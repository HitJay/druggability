#!/usr/bin/env python3
"""Prepare confirmed GPR81 tool compounds and run the Phase-3 docking campaign."""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

from meeko import MoleculePreparation
from rdkit import Chem
from rdkit.Chem import AllChem
from vina import Vina

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
OUT = PHASE1 / "phase3_docking"
LIGANDS = OUT / "ligands_pdbqt"
POSES = OUT / "poses"
RESULTS = OUT / "docking_results.csv"
CONFIG = PHASE1 / "phase2_prepared/phase2_manifest.json"

EXHAUSTIVENESS = 16
N_POSES = 5


def prepare_ligand(sdf_path: Path, output: Path) -> dict:
    suppl = Chem.SDMolSupplier(str(sdf_path), removeHs=False, sanitize=True)
    mol = next((m for m in suppl if m is not None), None)
    if mol is None:
        raise RuntimeError(f"RDKit could not parse {sdf_path}")
    mol = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol, randomSeed=20260803, useRandomCoords=True) != 0:
        raise RuntimeError(f"3D embedding failed for {sdf_path}")
    AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    # Meeko 0.7.x requires explicit hydrogens in the RDKit molecule.
    setup = MoleculePreparation()
    setups = setup.prepare(mol)
    if len(setups) != 1:
        raise RuntimeError(f"Expected one prepared molecule for {sdf_path}, got {len(setups)}")
    setup.write_pdbqt_file(str(output))
    return {"source": str(sdf_path), "output": str(output), "atoms": mol.GetNumAtoms(), "pdbqt_bytes": output.stat().st_size}


def parse_vina_results(path: Path) -> list[dict]:
    rows = []
    current_model = None
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            current_model = int(line.split()[1])
        match = re.match(r"REMARK VINA RESULT:\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)", line)
        if match and current_model is not None:
            rows.append({"pose_rank": current_model, "score_kcal_mol": float(match.group(1)), "rmsd_lb": float(match.group(2)), "rmsd_ub": float(match.group(3))})
    return rows


def write_header() -> None:
    if not RESULTS.exists():
        RESULTS.write_text("compound_id,receptor_id,pose_rank,score_kcal_mol,rmsd_lb,rmsd_ub,pose_file,error\n")


def append_row(row: dict) -> None:
    with RESULTS.open("a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["compound_id", "receptor_id", "pose_rank", "score_kcal_mol", "rmsd_lb", "rmsd_ub", "pose_file", "error"])
        writer.writerow(row)


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    LIGANDS.mkdir(parents=True, exist_ok=True)
    POSES.mkdir(parents=True, exist_ok=True)
    with CONFIG.open() as fh:
        phase2 = json.load(fh)
    compounds = []
    with (PHASE1 / "tool_compounds.csv").open() as fh:
        compounds = list(csv.DictReader(fh))
    prep_records = []
    for row in compounds:
        sdf = PHASE1 / "ligands" / f"{row['compound_id']}_CID{row['cid']}.sdf"
        pdbqt = LIGANDS / f"{row['compound_id']}.pdbqt"
        prep_records.append(prepare_ligand(sdf, pdbqt))
    (OUT / "ligand_preparation.json").write_text(json.dumps(prep_records, indent=2) + "\n")

    write_header()
    done = {(r["compound_id"], r["receptor_id"], r["pose_rank"])
            for r in csv.DictReader(RESULTS.open())} if RESULTS.exists() else set()
    for receptor in phase2["structures"]:
        rid = receptor["pdb_id"]
        v = Vina(sf_name="vina", seed=20260803)
        v.set_receptor(receptor["receptor_pdbqt"]["path"])
        geometry = receptor["ligand_geometry"]
        if geometry is None:
            # Apo has no ligand-derived absolute box; use the consensus active-pocket
            # center from 8Z87 transformed only in a future aligned-structure workflow.
            # It is intentionally excluded until receptor alignment is implemented.
            print(f"[SKIP] {rid}: no ligand-anchored box; not docking apo in this pass", flush=True)
            continue
        v.compute_vina_maps(center=geometry["center_A"], box_size=geometry["box_size_A"])
        for row in compounds:
            cid = row["compound_id"]
            ligand_path = LIGANDS / f"{cid}.pdbqt"
            v.set_ligand_from_file(str(ligand_path))
            try:
                v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
                energies = v.energies(n_poses=N_POSES)
                pose_dir = POSES / rid
                pose_dir.mkdir(exist_ok=True)
                pose_file = pose_dir / f"{cid}.pdbqt"
                v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
                parsed = parse_vina_results(pose_file)
                if not parsed:
                    raise RuntimeError("Vina produced no parseable poses")
                for pose in parsed:
                    rank = pose["pose_rank"]
                    key = (cid, rid, str(rank))
                    if key in done:
                        continue
                    append_row({"compound_id": cid, "receptor_id": rid, **pose,
                                "score_kcal_mol": round(pose["score_kcal_mol"], 4),
                                "rmsd_lb": round(pose["rmsd_lb"], 4), "rmsd_ub": round(pose["rmsd_ub"], 4),
                                "pose_file": str(pose_file), "error": ""})
                print(f"[OK] {cid} {rid}: {parsed[0]['score_kcal_mol']:.2f}", flush=True)
            except Exception as exc:
                append_row({"compound_id": cid, "receptor_id": rid, "pose_rank": "", "score_kcal_mol": "", "rmsd_lb": "", "rmsd_ub": "", "pose_file": "", "error": str(exc)[:300]})
                print(f"[ERROR] {cid} {rid}: {exc}", flush=True)


if __name__ == "__main__":
    run()
