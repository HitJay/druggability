#!/usr/bin/env python3
"""
Parallel 8-GPU Orchestrator on loong (hpccnrd002, 8x NVIDIA L20 GPUs)
Runs Stage 1 (Boltz-2 + omicMSA Docking) -> Stage 2 (Explicit-Solvent NPT MD + GBn2 MM/GBSA) -> Stage 3 (8-Lambda Alchemical TI FEP)
for all 10 complex-template-free prioritized PPI frontrunners across the Top 5 Axes.
"""
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path("/work/user/QYJI/frontrunners_md_fep")
BOLTZ_PYTHON = "/work/user/QYJI/venvs/boltz-2/bin/python"
OPENMM_PYTHON = "/data/user/QYJI/micromamba/envs/openfe-md/bin/python"
BOLTZ_CACHE = "/work/user/QYJI/boltz_cache"

manifest = json.loads((BASE_DIR / "manifest_10complexes.json").read_text())
RESULTS_DIR = BASE_DIR / "results"
BOLTZ_OUT = BASE_DIR / "boltz_runs"
SPECS_DIR = BASE_DIR / "specs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BOLTZ_OUT.mkdir(parents=True, exist_ok=True)
SPECS_DIR.mkdir(parents=True, exist_ok=True)


def run_one_complex(spec: dict, gpu_id: int) -> dict:
    cid = spec["id"]
    out_json = RESULTS_DIR / f"{cid}_full_audit.json"
    if out_json.exists() and out_json.stat().st_size > 500:
        print(f"[GPU {gpu_id}] {cid} already completed -> skipping!", flush=True)
        return json.loads(out_json.read_text())

    t0 = time.time()
    work_dir = RESULTS_DIR / cid
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_file = SPECS_DIR / f"{cid}.json"
    spec_file.write_text(json.dumps(spec, indent=2))

    yaml_file = BASE_DIR / "boltz_inputs" / f"{cid}.yaml"
    pred_dir = BOLTZ_OUT / f"boltz_results_{cid}" / "predictions" / cid
    raw_pdb = pred_dir / f"{cid}_model_0.pdb"
    conf_json = pred_dir / f"confidence_{cid}_model_0.json"

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    env["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
    env["BOLTZ_CACHE"] = BOLTZ_CACHE

    # Stage 1: Boltz-2 + omicMSA Co-Folding / Docking
    if not (raw_pdb.exists() and conf_json.exists()):
        print(f"[GPU {gpu_id}] Stage 1: Running Boltz-2 + omicMSA for {cid} ({spec['total_len']} aa)...", flush=True)
        boltz_cmd = [
            BOLTZ_PYTHON, "-m", "boltz.main", "predict",
            str(yaml_file),
            "--out_dir", str(BOLTZ_OUT),
            "--cache", BOLTZ_CACHE,
            "--devices", "1",
            "--num_workers", "0",
            "--recycling_steps", "3",
            "--sampling_steps", "100",
            "--output_format", "pdb",
            "--override",
        ]
        log_boltz = work_dir / "boltz.log"
        with open(log_boltz, "w") as lf:
            r_b = subprocess.run(boltz_cmd, env=env, stdout=lf, stderr=subprocess.STDOUT)
        if r_b.returncode != 0 or not raw_pdb.exists():
            raise RuntimeError(f"[GPU {gpu_id}] Boltz-2 failed for {cid} (exit={r_b.returncode}). Check {log_boltz}")
        print(f"[GPU {gpu_id}] Stage 1 finished for {cid} in {time.time()-t0:.1f}s", flush=True)

    # Stage 2 & 3: Explicit-Solvent NPT MD + GBn2 MM/GBSA + 8-Lambda Alchemical TI FEP
    print(f"[GPU {gpu_id}] Stage 2+3: Running Explicit-Solvent MD + MM/GBSA + 8-Lambda FEP for {cid}...", flush=True)
    md_cmd = [
        OPENMM_PYTHON, str(BASE_DIR / "md_fep_worker.py"),
        "--spec-json", str(spec_file),
        "--raw-pdb", str(raw_pdb),
        "--conf-json", str(conf_json),
        "--work-dir", str(work_dir),
        "--out-json", str(out_json),
        "--length-ns", "0.2",
        "--n-snapshots", "15",
    ]
    log_md = work_dir / "md_fep.log"
    with open(log_md, "w") as lf:
        r_m = subprocess.run(md_cmd, env=env, stdout=lf, stderr=subprocess.STDOUT)
    if r_m.returncode != 0 or not out_json.exists():
        raise RuntimeError(f"[GPU {gpu_id}] MD+FEP failed for {cid} (exit={r_m.returncode}). Check {log_md}")

    res = json.loads(out_json.read_text())
    print(
        f"[GPU {gpu_id}] DONE {cid} ({time.time()-t0:.1f}s): ipTM={res['boltz_confidence']['iptm']:.3f}, "
        f"<dG_GBn2>={res['explicit_md']['mean_delta_g_gbn2_kcal']:.1f} kcal/mol, "
        f"RMSD={res['explicit_md']['mean_partner_rmsd_A']:.2f} A",
        flush=True,
    )
    return res


def main():
    # Use a GPU pool of 8 workers (GPUs 0..7)
    import queue
    gpu_q = queue.Queue()
    for g in range(8):
        gpu_q.put(g)

    def worker(spec):
        g = gpu_q.get()
        try:
            return run_one_complex(spec, g)
        finally:
            gpu_q.put(g)

    t_all = time.time()
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(worker, sp): sp["id"] for sp in manifest}
        for fut in concurrent.futures.as_completed(futs):
            cid = futs[fut]
            try:
                all_results.append(fut.result())
            except Exception as e:
                print(f"ERROR on {cid}: {e}", flush=True)

    all_results.sort(key=lambda x: x["id"])
    (BASE_DIR / "all_10complexes_md_fep_summary.json").write_text(json.dumps(all_results, indent=2))
    print(f"ALL {len(all_results)}/10 COMPLEXES COMPLETED in {time.time()-t_all:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
