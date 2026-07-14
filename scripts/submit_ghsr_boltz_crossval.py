#!/usr/bin/env python3
"""Submit top 20 GHSR inverse agonist candidates for Boltz-2 cross-validation."""
from __future__ import annotations

import csv, json, shutil, traceback
from pathlib import Path

# GHSR mature sequence (UniProt P34986, without signal peptide 1-24)
# This is the 7TM receptor used in docking
GHSR_SEQUENCE = (
    "WNQTGSSGIFTSNCPQNVICIDEDWPPTNLRFPTPSDVYGMGSHVTVTVNCSEN"
    "GLNIVGLLLPGLEKSSQPVQKLLPKCGADLLVSEAGQRVVALVVFVVFGVGNLL"
    "TVLVSRSREKLRTPTNAFLINLAVADGLLMTLVLPLLVTDYLYHPSWAFGNLSA"
    "CRFSVMVTSVVTLSVTALSVERYFAICFPLRAKVVVTKGRVKLVIVVVLVFVSFV"
    "LSLLESLGLGLGESQRNRESRGEDTATSTTRGSSQAGPSLAGPQEGPGERGQAP"
    "RALSLQPMGVGQKTSASGKKEGTSASTQVTSPGEEAPPETLVRVWNGPAPGEAP"
    "KALAAAAGALAESESGEGARAGGRPRRGEAEGSQAPGEARGEEERPGLGARGGR"
    "GGSERGEKGDRVLPLRLPPSAAGPGAKVPPATPPPLPALPFPLLSPPSPFLPEP"
    "GGGEVKEEEAGQAPSGRRVSTKKRGAAAAGGSHRAGPGRQELVRSAGPALGPRG"
    "QRAERRAPAGAAEADQQTVETGEGSGESEAERPTNMAVMANGLERKPLGGGGGP"
    "GQVPGAA"
)

OUTDIR = Path("output/2026-07-10/ghsr_inverse_agonist_docking/boltz_crossval")
INPUT_DIR = OUTDIR / "inputs"
RUN_DIR = OUTDIR / "runs"
LOG_DIR = OUTDIR / "logs"
for d in (INPUT_DIR, RUN_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Screening library for SMILES lookup
LIBRARY = "output/2026-07-10/ghsr_inverse_agonist_docking/ghsr_screening_library.csv"
RANKED = "output/2026-07-10/ghsr_inverse_agonist_docking/ranked_hits.csv"

def safe_name(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_")[:80]

def write_yaml(path: Path, smiles: str) -> None:
    yaml_text = f"""version: 1
sequences:
  - protein:
      id: A
      sequence: {GHSR_SEQUENCE}
  - ligand:
      id: B
      smiles: '{smiles}'
properties:
  - affinity:
      binder: B
"""
    path.write_text(yaml_text, encoding="utf-8")

def main() -> None:
    # Load screening library for SMILES
    lib = {}
    with open(LIBRARY) as f:
        reader = csv.DictReader(f)
        for row in reader:
            lib[row["compound_id"]] = row

    # Get top 20 strong inverse agonists from ranked hits
    top20 = []
    with open(RANKED) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["class"] == "strong_inverse_agonist":
                top20.append(row)
                if len(top20) == 20:
                    break

    print(f"Top 20 inverse agonists for Boltz cross-validation:")
    print(f"{'Rank':>5s} {'Compound':20s} {'Delta':>8s} {'Priority':>8s}")
    for i, row in enumerate(top20, 1):
        print(f"{i:5d} {row['compound_id']:20s} {row['delta_score']:>8s} {row['priority']:>8s}")

    import biolib

    boltz = biolib.load("@nn/DCD/Boltz-2:0.0.37")
    output_csv = OUTDIR / "boltz_crossval_scores.csv"
    fieldnames = [
        "rank", "compound_id", "vina_score_7F83", "vina_score_8JSR", "vina_delta",
        "vina_priority", "name", "smiles",
        "boltz_job_id", "boltz_result_url", "boltz_exit_code",
        "boltz_affinity_pred_value", "boltz_affinity_probability_binary",
        "boltz_confidence_score", "boltz_ligand_iptm", "boltz_complex_ipde",
        "error",
    ]

    completed = set()
    if output_csv.exists():
        past = list(csv.DictReader(open(output_csv)))
        completed = set(r.get("compound_id", "") for r in past)
        print(f"\nAlready completed: {len(completed)}")

    results = []
    for i, row in enumerate(top20, 1):
        cid = row["compound_id"]
        if cid in completed:
            print(f"[SKIP] {cid} already done")
            continue

        lib_row = lib.get(cid, {})
        smi = lib_row.get("canonical_smiles", "")
        name = lib_row.get("name", cid)
        if not smi:
            print(f"[SKIP] {cid}: no SMILES found")
            continue

        label = safe_name(f"{cid}_{name}")
        yaml_path = INPUT_DIR / f"{label}.yaml"
        write_yaml(yaml_path, smi)
        compound_run_dir = RUN_DIR / label

        result_row = {
            "rank": i,
            "compound_id": cid,
            "vina_score_7F83": row["score_7F83"],
            "vina_score_8JSR": row["score_8JSR"],
            "vina_delta": row["delta_score"],
            "vina_priority": row["priority"],
            "name": name,
            "smiles": smi,
            "boltz_job_id": "",
            "boltz_result_url": "",
            "boltz_exit_code": "",
            "boltz_affinity_pred_value": "",
            "boltz_affinity_probability_binary": "",
            "boltz_confidence_score": "",
            "boltz_ligand_iptm": "",
            "boltz_complex_ipde": "",
            "error": "",
        }

        try:
            print(f"\n=== [{i}/20] BOLTZ {cid} {name} ===", flush=True)
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

            affinity = {}
            confidence = {}
            aff_path = compound_run_dir / "predictions/boltz/affinity_boltz.json"
            conf_path = compound_run_dir / "predictions/boltz/confidence_boltz_model_0.json"
            if aff_path.exists():
                affinity = json.loads(aff_path.read_text(encoding="utf-8"))
            if conf_path.exists():
                confidence = json.loads(conf_path.read_text(encoding="utf-8"))

            result_row.update({
                "boltz_job_id": str(job.id),
                "boltz_result_url": f"https://biolib.corp.novocorp.net/results/{job.id}/",
                "boltz_exit_code": exit_code,
                "boltz_affinity_pred_value": affinity.get("affinity_pred_value"),
                "boltz_affinity_probability_binary": affinity.get("affinity_probability_binary"),
                "boltz_confidence_score": confidence.get("confidence_score"),
                "boltz_ligand_iptm": confidence.get("ligand_iptm"),
                "boltz_complex_ipde": confidence.get("complex_ipde"),
            })
            print(f"  exit={exit_code} prob={affinity.get('affinity_probability_binary')}", flush=True)

        except Exception as e:
            error_text = "".join(traceback.format_exception_only(type(e), e)).strip()
            result_row.update({"boltz_exit_code": "exception", "error": error_text})
            print(f"  EXCEPTION: {error_text}", flush=True)

        results.append(result_row)

        # Incremental save
        with open(output_csv, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(results)
        print(f"  saved -> {output_csv}", flush=True)

    # Final summary
    if results:
        print(f"\n\n=== BOLTZ CROSS-VALIDATION SUMMARY ===")
        with open(output_csv) as f:
            reader = csv.DictReader(f)
            for r in reader:
                print(f"  {r['compound_id']:20s} vina_delta={r['vina_delta']:>6s}  "
                      f"boltz_prob={r['boltz_affinity_probability_binary']:>6s}  "
                      f"boltz_conf={r['boltz_confidence_score']:>6s}")

if __name__ == "__main__":
    main()
