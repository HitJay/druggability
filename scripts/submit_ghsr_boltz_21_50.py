#!/usr/bin/env python3
"""Submit GHSR inverse agonist ranks 21-50 for Boltz-2 cross-validation."""
from __future__ import annotations

import csv, json, shutil, traceback
from pathlib import Path

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

LIBRARY = "output/2026-07-10/ghsr_inverse_agonist_docking/ghsr_screening_library.csv"
RANKED = "output/2026-07-10/ghsr_inverse_agonist_docking/ranked_hits.csv"
OUTPUT_CSV = OUTDIR / "boltz_crossval_scores.csv"

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
    lib = {}
    with open(LIBRARY) as f:
        for row in csv.DictReader(f):
            lib[row["compound_id"]] = row

    # Get all strong inverse agonists (top 50)
    all_ia = []
    with open(RANKED) as f:
        for row in csv.DictReader(f):
            if row["class"] == "strong_inverse_agonist":
                all_ia.append(row)
                if len(all_ia) == 50:
                    break

    # Check which ones are already done
    done_ids = set()
    if OUTPUT_CSV.exists():
        for row in csv.DictReader(open(OUTPUT_CSV)):
            done_ids.add(row.get("compound_id", ""))

    # Take ranks 21-50 (already done 1-20)
    todo = [r for r in all_ia[20:] if r["compound_id"] not in done_ids]
    if not todo:
        print("Ranks 21-50 already all submitted. Checking for failed ones...")
        todo = [r for r in all_ia[20:] if r["compound_id"] in done_ids]
        # Re-check for failures
        with open(OUTPUT_CSV) as f:
            existing = {r["compound_id"]: r for r in csv.DictReader(f)}
        todo = [r for r in todo if existing.get(r["compound_id"], {}).get("boltz_exit_code", "") != "0"]
        if not todo:
            print("All ranks 21-50 completed successfully.")
            return

    print(f"Submitting {len(todo)} compounds (ranks 21-50) to Boltz-2")

    import biolib
    boltz = biolib.load("@nn/DCD/Boltz-2:0.0.37")

    # Read existing results
    existing_rows = []
    fieldnames = [
        "rank", "compound_id", "vina_score_7F83", "vina_score_8JSR", "vina_delta",
        "vina_priority", "name", "smiles",
        "boltz_job_id", "boltz_result_url", "boltz_exit_code",
        "boltz_affinity_pred_value", "boltz_affinity_probability_binary",
        "boltz_confidence_score", "boltz_ligand_iptm", "boltz_complex_ipde",
        "error",
    ]
    if OUTPUT_CSV.exists():
        with open(OUTPUT_CSV) as f:
            for r in csv.DictReader(f):
                existing_rows.append(r)

    new_results = []
    for row in todo:
        cid = row["compound_id"]
        lib_row = lib.get(cid, {})
        smi = lib_row.get("canonical_smiles", "")
        name = lib_row.get("name", cid)
        if not smi:
            print(f"[SKIP] {cid}: no SMILES")
            continue

        # Skip charged SMILES (replace [O-] with O, remove [Na+] etc.)
        import re
        smi_clean = re.sub(r'\[O-\]', 'O', smi)
        smi_clean = re.sub(r'\[Na\+\]|\[K\+\]|\[Cl-\]|\[Br-\]|\[I-\]', '', smi_clean)

        label = safe_name(f"{cid}_{name}")
        yaml_path = INPUT_DIR / f"{label}.yaml"
        write_yaml(yaml_path, smi_clean)
        compound_run_dir = RUN_DIR / label

        result_row = {
            "rank": row.get("rank", ""),
            "compound_id": cid,
            "vina_score_7F83": row["score_7F83"],
            "vina_score_8JSR": row["score_8JSR"],
            "vina_delta": row["delta_score"],
            "vina_priority": row["priority"],
            "name": name,
            "smiles": smi,
            "boltz_job_id": "", "boltz_result_url": "", "boltz_exit_code": "",
            "boltz_affinity_pred_value": "", "boltz_affinity_probability_binary": "",
            "boltz_confidence_score": "", "boltz_ligand_iptm": "", "boltz_complex_ipde": "",
            "error": "",
        }

        try:
            print(f"\n=== BOLTZ {cid} {name} ===", flush=True)
            job = boltz.run(
                input=str(yaml_path.resolve()),
                recycling_steps="1", diffusion_samples="1",
                sampling_steps="50", sampling_steps_affinity="50",
                diffusion_samples_affinity="2",
                biolib_check=False, biolib_stream_logs=False,
            )
            stdout = job.get_stdout().decode("utf-8", errors="replace")
            stderr = job.get_stderr().decode("utf-8", errors="replace")
            (LOG_DIR / f"{label}_stdout.log").write_text(stdout)
            (LOG_DIR / f"{label}_stderr.log").write_text(stderr)
            exit_code = job.get_exit_code()

            if exit_code == 0:
                if compound_run_dir.exists():
                    shutil.rmtree(compound_run_dir)
                compound_run_dir.mkdir(parents=True, exist_ok=True)
                job.save_files(str(compound_run_dir), overwrite=True)

            aff_path = compound_run_dir / "predictions/boltz/affinity_boltz.json"
            conf_path = compound_run_dir / "predictions/boltz/confidence_boltz_model_0.json"
            affinity = json.loads(aff_path.read_text()) if aff_path.exists() else {}
            confidence = json.loads(conf_path.read_text()) if conf_path.exists() else {}

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

        new_results.append(result_row)

        # Incremental save: merge with existing
        all_rows = existing_rows + new_results
        with open(OUTPUT_CSV, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_rows)
        print(f"  saved", flush=True)

    print(f"\nDone. Results: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
