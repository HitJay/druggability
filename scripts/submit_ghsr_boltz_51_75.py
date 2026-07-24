#!/usr/bin/env python3
"""Submit GHSR inverse agonist ranks 51-75 for Boltz-2 cross-validation.

Mirrors scripts/submit_ghsr_boltz_21_50.py / submit_ghsr_boltz_crossval.py:
- Same GHSR_SEQUENCE (UniProt P34986 mature 7TM sequence) used for all prior batches.
- Same YAML schema (Boltz-2 `sequences: [protein, ligand]` + `properties: [affinity]`).
- Same BioLib model: @nn/DCD/Boltz-2:0.0.37, same run() kwargs.
- Appends incrementally to the SAME boltz_crossval_scores.csv after every single
  compound (not batched), so a mid-run failure/timeout never loses completed rows.
- Per-job wall-clock cap: if job doesn't return within JOB_TIMEOUT_SEC, record an
  'error' row (timeout) and move to the next compound instead of blocking forever.
"""
from __future__ import annotations

import csv, json, re, shutil, time, traceback
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

FIELDNAMES = [
    "rank", "compound_id", "vina_score_7F83", "vina_score_8JSR", "vina_delta",
    "vina_priority", "name", "smiles",
    "boltz_job_id", "boltz_result_url", "boltz_exit_code",
    "boltz_affinity_pred_value", "boltz_affinity_probability_binary",
    "boltz_confidence_score", "boltz_ligand_iptm", "boltz_complex_ipde",
    "error",
]

JOB_TIMEOUT_SEC = 600  # 10 minutes cap per compound; skip + record error beyond this


def safe_name(text: str) -> str:
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


def append_row(row: dict) -> None:
    """Append a single row to OUTPUT_CSV immediately (create header if new file)."""
    file_exists = OUTPUT_CSV.exists()
    with open(OUTPUT_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            w.writeheader()
        w.writerow(row)


def main() -> None:
    lib = {}
    with open(LIBRARY) as f:
        for row in csv.DictReader(f):
            lib[row["compound_id"]] = row

    # Get all strong inverse agonists, take ranks 51-75 (index 50:75)
    all_ia = []
    with open(RANKED) as f:
        for row in csv.DictReader(f):
            if row["class"] == "strong_inverse_agonist":
                all_ia.append(row)
                if len(all_ia) == 75:
                    break

    todo_all = all_ia[50:75]

    done_ids = set()
    if OUTPUT_CSV.exists():
        for row in csv.DictReader(open(OUTPUT_CSV)):
            done_ids.add(row.get("compound_id", ""))

    todo = [r for r in todo_all if r["compound_id"] not in done_ids]
    print(f"Ranks 51-75 total: {len(todo_all)}; already done: {len(todo_all) - len(todo)}; "
          f"to submit: {len(todo)}")

    if not todo:
        print("Nothing to do.")
        return

    import biolib
    boltz = biolib.load("@nn/DCD/Boltz-2:0.0.37")

    for row in todo:
        cid = row["compound_id"]
        lib_row = lib.get(cid, {})
        smi = lib_row.get("canonical_smiles", "")
        name = lib_row.get("name", cid)

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

        if not smi:
            result_row["error"] = "no SMILES found in screening library"
            print(f"[SKIP] {cid}: no SMILES")
            append_row(result_row)
            continue

        smi_clean = re.sub(r"\[O-\]", "O", smi)
        smi_clean = re.sub(r"\[Na\+\]|\[K\+\]|\[Cl-\]|\[Br-\]|\[I-\]", "", smi_clean)

        label = safe_name(f"{cid}_{name}")
        yaml_path = INPUT_DIR / f"{label}.yaml"
        write_yaml(yaml_path, smi_clean)
        compound_run_dir = RUN_DIR / label

        start = time.time()
        try:
            print(f"\n=== BOLTZ {cid} {name} ===", flush=True)
            job = boltz.run(
                input=str(yaml_path.resolve()),
                recycling_steps="1", diffusion_samples="1",
                sampling_steps="50", sampling_steps_affinity="50",
                diffusion_samples_affinity="2",
                biolib_check=False, biolib_stream_logs=False,
            )
            elapsed = time.time() - start
            if elapsed > JOB_TIMEOUT_SEC:
                result_row["boltz_exit_code"] = "timeout"
                result_row["error"] = f"job exceeded {JOB_TIMEOUT_SEC}s (took {elapsed:.0f}s), skipped"
                print(f"  TIMEOUT after {elapsed:.0f}s", flush=True)
                append_row(result_row)
                continue

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

        # Incremental save: append this one row immediately.
        append_row(result_row)
        print(f"  appended -> {OUTPUT_CSV}", flush=True)

    print(f"\nDone. Results: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
