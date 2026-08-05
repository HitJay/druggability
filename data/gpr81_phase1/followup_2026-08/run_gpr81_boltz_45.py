#!/usr/bin/env python3
"""
GPR81 follow-up: Boltz-2 cross-validation of all 45 compounds (BioLib cloud).

Runs Boltz-2 (BioLib @nn/DCD/Boltz-2:0.0.37) on HCAR1 + each compound SMILES
with the affinity property, extracting the same metrics as the GHSR campaign:
  affinity_pred_value, affinity_probability_binary (from affinity_boltz.json)
  confidence_score, ligand_iptm, complex_ipde      (from confidence_boltz_model_0.json)

Input : gpr81_compound_scorecard.json (entry_id, smiles, ec50_nM context)
Output: data/boltz_results.csv + .json (incremental, resumable; per-compound YAML + logs)

Usage:
  # requires a working BioLib login (~/.cache/pybiolib/user-state.json refresh token)
  python run_gpr81_boltz_45.py [--parallel N] [--limit K]

Boltz affinity/iptm are structural-model estimates, not measured affinities:
they are a second, independent computational layer to be benchmarked against
wet-lab EC50 later (see gpr81_boltz_wetlab_report.html).
"""
from __future__ import annotations
import argparse, csv, json, shutil, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parent
P1 = BASE.parent
DATA = BASE / "data"
OUT_CSV = DATA / "boltz_results.csv"
OUT_JSON = DATA / "boltz_results.json"
INPUT_DIR = DATA / "boltz_inputs"
RUN_DIR = DATA / "boltz_runs"
LOG_DIR = DATA / "boltz_logs"
for d in (INPUT_DIR, RUN_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

# HCAR1 full-length sequence, UniProt Q9BXC0 (346 aa, no signal peptide).
# Retrieved 2026-08-05 from rest.uniprot.org/uniprotkb/Q9BXC0.json (sequence.value).
HCAR1_SEQUENCE = (
    "MYNGSCCRIEGDTISQVMPPLLIVAFVLGALGNGVALCGFCFHMKTWKPSTVYLFNLAVA"
    "DFLLMICLPFRTDYYLRRRHWAFGDIPCRVGLFTLAMNRAGSIVFLTVVAADRYFKVVHP"
    "HHAVNTISTRVAAGIVCTLWALVILGTVYLLLENHLCVQETAVSCESFIMESANGWHDIM"
    "FQLEFFMPLGIILFCSFKIVWSLRRRQQLARQARMKKATRFIMVVAIVFITCYLPSVSAR"
    "LYFLWTVPSSACDPSVHGALHITLSFTYMNSMLDPLVYYFSSPSFPKFYNKLKICSLKPK"
    "QPGHSKTQRPEEMPISNLGRRSCISVANSFQSQSDGQWDPHIVEWH"
)


def safe_name(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_")[:80]


def write_yaml(path: Path, smiles: str) -> None:
    yaml_text = f"""version: 1
sequences:
  - protein:
      id: A
      sequence: {HCAR1_SEQUENCE}
  - ligand:
      id: B
      smiles: '{smiles}'
properties:
  - affinity:
      binder: B
"""
    path.write_text(yaml_text, encoding="utf-8")


FIELD_NAMES = ["entry_id", "name", "smiles", "ec50_nM", "emax_pct",
               "boltz_job_id", "boltz_result_url", "boltz_exit_code",
               "boltz_affinity_pred_value", "boltz_affinity_probability_binary",
               "boltz_confidence_score", "boltz_ligand_iptm", "boltz_complex_ipde",
               "error"]


def run_one(boltz, row: dict, retries: int = 2) -> dict:
    entry = row["entry_id"]
    label = safe_name(entry)
    yaml_path = INPUT_DIR / f"{label}.yaml"
    write_yaml(yaml_path, row["smiles"])
    compound_run_dir = RUN_DIR / label
    result = dict(row)
    result.update({k: "" for k in FIELD_NAMES if k not in result})
    result["entry_id"] = entry

    for attempt in range(1, retries + 2):
        try:
            job = boltz.run(
                input=str(yaml_path.resolve()),
                recycling_steps="1",
                diffusion_samples="1",
                sampling_steps="50",
                sampling_steps_affinity="50",
                diffusion_samples_affinity="2",
                biolib_check=False,
                biolib_stream_logs=False,
            )
            stdout = job.get_stdout().decode("utf-8", errors="replace")
            stderr = job.get_stderr().decode("utf-8", errors="replace")
            (LOG_DIR / f"{label}_stdout.log").write_text(stdout, encoding="utf-8")
            (LOG_DIR / f"{label}_stderr.log").write_text(stderr, encoding="utf-8")
            exit_code = job.get_exit_code()

            if exit_code == 0:
                if compound_run_dir.exists():
                    shutil.rmtree(compound_run_dir)
                compound_run_dir.mkdir(parents=True, exist_ok=True)
                job.save_files(str(compound_run_dir), overwrite=True)

            affinity, confidence = {}, {}
            aff_path = compound_run_dir / "predictions/boltz/affinity_boltz.json"
            conf_path = compound_run_dir / "predictions/boltz/confidence_boltz_model_0.json"
            if aff_path.exists():
                affinity = json.loads(aff_path.read_text(encoding="utf-8"))
            if conf_path.exists():
                confidence = json.loads(conf_path.read_text(encoding="utf-8"))

            result.update({
                "boltz_job_id": str(job.id),
                "boltz_result_url": f"https://biolib.corp.novocorp.net/results/{job.id}/",
                "boltz_exit_code": exit_code,
                "boltz_affinity_pred_value": affinity.get("affinity_pred_value"),
                "boltz_affinity_probability_binary": affinity.get("affinity_probability_binary"),
                "boltz_confidence_score": confidence.get("confidence_score"),
                "boltz_ligand_iptm": confidence.get("ligand_iptm"),
                "boltz_complex_ipde": confidence.get("complex_ipde"),
                "error": "",
            })
            print(f"[OK] {entry} exit={exit_code} prob={result['boltz_affinity_probability_binary']}", flush=True)
            return result
        except Exception as e:
            err = "".join(traceback.format_exception_only(type(e), e)).strip()
            print(f"[RETRY {attempt}] {entry}: {err[:160]}", flush=True)
            time.sleep(10 * attempt)
            result["error"] = err
    result["boltz_exit_code"] = "exception"
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parallel", type=int, default=1, help="concurrent BioLib jobs")
    ap.add_argument("--limit", type=int, default=0, help="only first K compounds (0 = all)")
    args = ap.parse_args()

    sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
    rows = []
    for c in sc["compounds"]:
        if not c.get("smiles"):
            continue
        rows.append({
            "entry_id": c["entry_id"],
            "name": c.get("name", ""),
            "smiles": c["smiles"],
            "ec50_nM": c.get("ec50_nM"),
            "emax_pct": c.get("emax_pct"),
        })
    if args.limit:
        rows = rows[: args.limit]
    print(f"compounds to run: {len(rows)}")

    done = {}
    if OUT_CSV.exists():
        with open(OUT_CSV) as f:
            for r in csv.DictReader(f):
                if r.get("boltz_job_id") or r.get("error") == "exception":
                    done[r["entry_id"]] = r
    todo = [r for r in rows if r["entry_id"] not in done]
    print(f"already done: {len(done)} | todo: {len(todo)}")
    if not todo:
        print("nothing to do")
        return

    import biolib
    boltz = biolib.load("@nn/DCD/Boltz-2:0.0.37")

    results = list(done.values())
    if args.parallel > 1:
        with ThreadPoolExecutor(max_workers=args.parallel) as ex:
            futs = {ex.submit(run_one, boltz, r): r for r in todo}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                _save(results)
    else:
        for i, r in enumerate(todo, 1):
            print(f"\n=== [{i}/{len(todo)}] {r['entry_id']} ===", flush=True)
            results.append(run_one(boltz, r))
            _save(results)

    print("\n=== BOLTZ SUMMARY ===")
    for r in sorted(results, key=lambda x: str(x.get("entry_id"))):
        print(f"  {r['entry_id']:8s} prob={str(r.get('boltz_affinity_probability_binary'))[:8]:8s} "
              f"conf={str(r.get('boltz_confidence_score'))[:8]:8s} exit={r.get('boltz_exit_code')}")


def _save(results: list[dict]) -> None:
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELD_NAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    with open(OUT_JSON, "w") as f:
        json.dump({
            "target": "HCAR1 (Q9BXC0, full length 346 aa)",
            "protocol": "BioLib Boltz-2:0.0.37, recycling 1, sampling 50, affinity 50/2; "
                        "metrics = affinity_pred_value / affinity_probability_binary / confidence_score / ligand_iptm / complex_ipde",
            "caveat": "Boltz affinity/iptm are structural-model estimates, not measured affinities; "
                      "benchmark against wet-lab EC50 before use",
            "results": results,
        }, f, indent=1)


if __name__ == "__main__":
    main()
