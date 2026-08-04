#!/usr/bin/env python
"""Run a resumable full ChEMBL AutoDock-Vina screen for GRB10 SH2."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import traceback
from pathlib import Path

import pandas as pd


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_")[:80]


def parse_best_vina(stdout: str) -> float | None:
    for line in stdout.splitlines():
        match = re.match(r"\s*1\s+(-?\d+\.\d+)\s+", line)
        if match:
            return float(match.group(1))
    return None


def read_completed(output_csv: Path) -> set[str]:
    if not output_csv.exists():
        return set()
    with output_csv.open(newline="", encoding="utf-8") as handle:
        return {row["compound_id"] for row in csv.DictReader(handle) if row.get("compound_id")}


def append_row(output_csv: Path, row: dict[str, object], fieldnames: list[str]) -> None:
    file_exists = output_csv.exists()
    with output_csv.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", default="output/2026-06-30/grb10_screening_expanded_chembl/chembl_seed_library.csv")
    parser.add_argument("--outdir", default="output/2026-06-30/grb10_screening_expanded_chembl/vina_full")
    parser.add_argument("--receptor", default="output/2026-06-29/grb10_inhibition_cmpd_research/structures/1NRV.pdb")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0, help="0 means run to the end of the library")
    parser.add_argument("--exhaustiveness", default="8")
    parser.add_argument("--box-size", default="22")
    parser.add_argument("--receptor-selection", default="protein and chain A")
    parser.add_argument("--ligand-selection", default="chain A and resnum 431 439 462 477 480 515")
    args = parser.parse_args()

    import biolib

    workspace = Path.cwd()
    outdir = Path(args.outdir)
    run_dir = outdir / "runs"
    log_dir = outdir / "logs"
    for directory in (run_dir, log_dir):
        directory.mkdir(parents=True, exist_ok=True)

    library = pd.read_csv(args.library)
    if args.limit and args.limit > 0:
        subset = library.iloc[args.start : args.start + args.limit].copy()
    else:
        subset = library.iloc[args.start :].copy()

    output_csv = outdir / "vina_full_scores.csv"
    completed = read_completed(output_csv)
    app = biolib.load("@nn/SmallMolecules/AutoDock-Vina")
    fieldnames = [
        "library",
        "compound_id",
        "name",
        "canonical_smiles",
        "max_phase",
        "mw",
        "clogp",
        "tpsa",
        "heavy_atoms",
        "job_id",
        "result_url",
        "exit_code",
        "best_vina_kcal_mol",
        "run_dir",
        "error",
    ]

    total = len(subset)
    for position, row in enumerate(subset.itertuples(index=False), start=1):
        row_data = row._asdict()
        compound_id = str(row_data.get("compound_id") or row_data.get("name"))
        name = str(row_data.get("name") or compound_id)
        if compound_id in completed:
            print(f"[{position}/{total}] skip completed {compound_id} {name}", flush=True)
            continue

        label = safe_name(f"{compound_id}_{name}")
        compound_run_dir = run_dir / label
        stdout_path = log_dir / f"{label}_stdout.log"
        stderr_path = log_dir / f"{label}_stderr.log"
        print(f"[{position}/{total}] docking {compound_id} {name}", flush=True)

        result_row = {
            "library": "chembl_expanded_8490",
            "compound_id": compound_id,
            "name": name,
            "canonical_smiles": row_data.get("canonical_smiles"),
            "max_phase": row_data.get("max_phase"),
            "mw": row_data.get("mw"),
            "clogp": row_data.get("clogp"),
            "tpsa": row_data.get("tpsa"),
            "heavy_atoms": row_data.get("heavy_atoms"),
            "job_id": "",
            "result_url": "",
            "exit_code": "",
            "best_vina_kcal_mol": "",
            "run_dir": str(compound_run_dir),
            "error": "",
        }

        try:
            job = app.run(
                LIGAND_SMILES=str(row_data["canonical_smiles"]),
                INPUT_RECEPTOR_PDB=str(workspace / args.receptor),
                PRODY_RECEPTOR_SELECTION=args.receptor_selection,
                PRODY_LIGAND_SELECTION=args.ligand_selection,
                EXHAUSTIVENESS=args.exhaustiveness,
                PH="7.4",
                SKIP_TAUTOMER="True",
                SKIP_ACIDBASE="True",
                BOX_SIZE=args.box_size,
                verbose="False",
                biolib_check=False,
                biolib_stream_logs=False,
            )
            stdout = job.get_stdout().decode("utf-8", errors="replace")
            stderr = job.get_stderr().decode("utf-8", errors="replace")
            stdout_path.write_text(stdout, encoding="utf-8")
            stderr_path.write_text(stderr, encoding="utf-8")
            exit_code = job.get_exit_code()
            best_vina = parse_best_vina(stdout)

            if exit_code == 0:
                if compound_run_dir.exists():
                    shutil.rmtree(compound_run_dir)
                compound_run_dir.mkdir(parents=True, exist_ok=True)
                job.save_files(str(compound_run_dir), overwrite=True)

            result_row.update(
                {
                    "job_id": str(job.id),
                    "result_url": f"https://biolib.corp.novocorp.net/results/{job.id}/",
                    "exit_code": exit_code,
                    "best_vina_kcal_mol": best_vina if best_vina is not None else "",
                }
            )
            print(f"[{position}/{total}] done {compound_id} exit={exit_code} best={best_vina}", flush=True)
        except Exception as error:  # noqa: BLE001 - keep full screen resumable.
            error_text = "".join(traceback.format_exception_only(type(error), error)).strip()
            stderr_path.write_text(traceback.format_exc(), encoding="utf-8")
            result_row.update({"exit_code": "exception", "error": error_text})
            print(f"[{position}/{total}] exception {compound_id}: {error_text}", flush=True)

        append_row(output_csv, result_row, fieldnames)
        completed.add(compound_id)

    if output_csv.exists():
        results = pd.read_csv(output_csv)
        ranked = results[results["exit_code"].astype(str) == "0"].copy()
        ranked["best_vina_kcal_mol"] = pd.to_numeric(ranked["best_vina_kcal_mol"], errors="coerce")
        ranked = ranked.sort_values("best_vina_kcal_mol", na_position="last")
        ranked.to_csv(outdir / "vina_full_scores_ranked_success.csv", index=False)
        print(f"wrote {output_csv}")
        print(f"wrote {outdir / 'vina_full_scores_ranked_success.csv'}")


if __name__ == "__main__":
    main()