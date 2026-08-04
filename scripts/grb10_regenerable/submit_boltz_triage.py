#!/usr/bin/env python
"""Submit Boltz-2 affinity triage for GRB10 SH2 top elite candidates."""
from __future__ import annotations

import json
import shutil
import traceback
from pathlib import Path

import pandas as pd

GRB10_SH2_SEQUENCE = (
    "IHRTQHWFHGRISREESHRIIKQQGLVDGLFLLRDSQSNPKAFVLTLCHHQKIKNFQILPCT"
    "FFSLDDGNTKFSDLIQLVDFYQLNKGVLPCKLKHHCIR"
)

OUTDIR = Path("output/2026-06-30/grb10_screening_expanded_chembl/boltz_full")
INPUT_DIR = OUTDIR / "inputs"
RUN_DIR = OUTDIR / "runs"
LOG_DIR = OUTDIR / "logs"
for d in (INPUT_DIR, RUN_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)


def safe_name(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_")[:80]


def write_yaml(path: Path, smiles: str) -> None:
    yaml_text = f"""version: 1
sequences:
  - protein:
      id: A
      sequence: {GRB10_SH2_SEQUENCE}
  - ligand:
      id: B
      smiles: '{smiles}'
properties:
  - affinity:
      binder: B
"""
    path.write_text(yaml_text, encoding="utf-8")


def main() -> None:
    # Read triage CSV - take elite + top 5 of tier1
    triage = pd.read_csv(
        "output/2026-06-30/grb10_screening_expanded_chembl/vina_full/grb10_vina_full_triage.csv"
    )
    elite = triage[triage["tier"] == "elite"].head(15)
    tier1_top = triage[triage["tier"] == "tier1"].head(5)
    subset = pd.concat([elite, tier1_top]).drop_duplicates(
        subset="compound_id"
    ).reset_index(drop=True)

    print(f"Total compounds for Boltz: {len(subset)}")
    print(subset[["compound_id", "name", "best_vina_kcal_mol", "tier"]].to_string(index=False))

    import biolib

    boltz = biolib.load("@nn/DCD/Boltz-2:0.0.37")
    output_csv = OUTDIR / "boltz_full_scores.csv"
    fieldnames = [
        "library",
        "compound_id",
        "name",
        "canonical_smiles",
        "best_vina_kcal_mol",
        "mw",
        "tpsa",
        "tier",
        "boltz_job_id",
        "boltz_result_url",
        "boltz_exit_code",
        "boltz_affinity_pred_value",
        "boltz_affinity_probability_binary",
        "boltz_confidence_score",
        "boltz_ligand_iptm",
        "boltz_complex_ipde",
        "boltz_run_dir",
        "error",
    ]

    # Check existing completed runs
    completed = set()
    if output_csv.exists():
        past = pd.read_csv(output_csv)
        completed = set(past["compound_id"].dropna().astype(str))

    results = []

    for _, row in subset.iterrows():
        cid = str(row["compound_id"])
        if cid in completed:
            print(f"[SKIP] {cid} {row['name']} already done")
            continue

        label = safe_name(f"{cid}_{row['name']}")
        yaml_path = INPUT_DIR / f"{label}.yaml"
        write_yaml(yaml_path, str(row["canonical_smiles"]))
        compound_run_dir = RUN_DIR / label

        result_row = {
            "library": "chembl_expanded_8490",
            "compound_id": cid,
            "name": row["name"],
            "canonical_smiles": row["canonical_smiles"],
            "best_vina_kcal_mol": row["best_vina_kcal_mol"],
            "mw": row["mw"],
            "tpsa": row["tpsa"],
            "tier": row["tier"],
            "boltz_job_id": "",
            "boltz_result_url": "",
            "boltz_exit_code": "",
            "boltz_affinity_pred_value": "",
            "boltz_affinity_probability_binary": "",
            "boltz_confidence_score": "",
            "boltz_ligand_iptm": "",
            "boltz_complex_ipde": "",
            "boltz_run_dir": str(compound_run_dir),
            "error": "",
        }

        try:
            print(f"\n=== BOLTZ {cid} {row['name']} ===")
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

            result_row.update(
                {
                    "boltz_job_id": str(job.id),
                    "boltz_result_url": f"https://biolib.corp.novocorp.net/results/{job.id}/",
                    "boltz_exit_code": exit_code,
                    "boltz_affinity_pred_value": affinity.get("affinity_pred_value"),
                    "boltz_affinity_probability_binary": affinity.get("affinity_probability_binary"),
                    "boltz_confidence_score": confidence.get("confidence_score"),
                    "boltz_ligand_iptm": confidence.get("ligand_iptm"),
                    "boltz_complex_ipde": confidence.get("complex_ipde"),
                }
            )
            print(f"  exit={exit_code} prob={affinity.get('affinity_probability_binary')}")

        except Exception as e:
            error_text = "".join(traceback.format_exception_only(type(e), e)).strip()
            result_row.update({"boltz_exit_code": "exception", "error": error_text})
            print(f"  EXCEPTION: {error_text}")

        results.append(result_row)

        # Incremental save after each run
        res_df = pd.DataFrame(results)
        res_df.to_csv(output_csv, index=False)
        print(f"  saved incremental to {output_csv}")

    # Final summary
    if results:
        final = pd.read_csv(output_csv)
        print(f"\n\n=== BOLTZ FINAL SUMMARY ===")
        cols = ["compound_id", "name", "tier", "best_vina_kcal_mol",
                "boltz_affinity_pred_value", "boltz_affinity_probability_binary",
                "boltz_confidence_score", "boltz_exit_code"]
        print(final[cols].to_string(index=False))


if __name__ == "__main__":
    main()
