#!/usr/bin/env python3
"""Phase 6 - full-series docking of all 39 recovered paper compounds.

Scope (per REVIEW_2026-08-04 + phase-5 analysis):
  - All 39 Davidsson 2020 compounds (paper_ligands/compound_XX.sdf).
  - Receptors: 8Z8A (primary, lactate-bound, accommodates large molecules in
    TM5-TM6 extracellular region) and 9KT9 (second orthosteric-state structure;
    fills the phase-4 gap - matched pairs were never docked there).
  - 24A box protocol (large molecules do NOT bind the orthosteric small-acid
    pocket; the tight-box protocol is only valid for orthosteric ligands).
  - 2 seeds x exhaustiveness 16 x 5 poses (phase-4 protocol was 8 seeds x 32;
    this is a full-series scan, matched pairs already have the 8-seed data).

Outputs (data/gpr81_phase1/phase6_full_series/):
  full_series_docking_results.csv, full_series_summary.json,
  full_series_manifest.json, poses/<cXX>_<receptor>_seed<N>.pdbqt
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from vina import Vina
from meeko import MoleculePreparation, PDBQTWriterLegacy
from rdkit import Chem
from rdkit.Chem import AllChem

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
OUT = PHASE1 / "phase6_full_series"
(OUT / "poses").mkdir(parents=True, exist_ok=True)

RECEPTORS = ["8Z8A", "9KT9"]
SEEDS = [20260803, 1]
EXHAUSTIVENESS = 16
N_POSES = 5


def prepare_ligand(num: int) -> Path:
    sdf = PHASE1 / "paper_ligands" / f"compound_{num:02d}.sdf"
    out = OUT / "ligands" / f"compound_{num:02d}.pdbqt"
    (OUT / "ligands").mkdir(exist_ok=True)
    if out.exists():
        return out
    suppl = Chem.SDMolSupplier(str(sdf), removeHs=False, sanitize=True)
    mol = next((m for m in suppl if m is not None), None)
    if mol is None:
        raise RuntimeError(f"cannot parse {sdf}")
    mol = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol, randomSeed=20260803, useRandomCoords=True) != 0:
        raise RuntimeError(f"embedding failed {sdf}")
    AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    setup = MoleculePreparation()
    setups = setup.prepare(mol)
    if len(setups) != 1:
        raise RuntimeError(f"expected 1 prep for {num}, got {len(setups)}")
    pdbqt_str, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        raise RuntimeError(f"PDBQTWriterLegacy failed for {num}: {err}")
    out.write_text(pdbqt_str)
    return out


def parse_pose_models(path: Path) -> list[tuple[int, float]]:
    rows, cur = [], None
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            cur = int(line.split()[1])
        if line.startswith("REMARK VINA RESULT:"):
            rows.append((cur, float(line.split()[3])))
    return rows


def main() -> None:
    p2 = json.loads((PHASE1 / "phase2_prepared/phase2_manifest.json").read_text())
    receptors = {s["pdb_id"]: s for s in p2["structures"] if s["pdb_id"] in RECEPTORS}

    ligands = {}
    for num in range(1, 40):
        ligands[num] = prepare_ligand(num)
        print(f"[PREP] compound {num:02d}: {ligands[num].stat().st_size} B", flush=True)

    rows, summary = [], {}
    for rid in RECEPTORS:
        rec = receptors[rid]
        geom = rec["ligand_geometry"]
        for num in range(1, 40):
            scores = []
            for seed in SEEDS:
                v = Vina(sf_name="vina", seed=seed)
                v.set_receptor(rec["receptor_pdbqt"]["path"])
                v.compute_vina_maps(center=geom["center_A"], box_size=geom["box_size_A"])
                v.set_ligand_from_file(str(ligands[num]))
                v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
                pose_file = OUT / "poses" / f"c{num:02d}_{rid}_seed{seed}.pdbqt"
                v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
                for rank, score in parse_pose_models(pose_file):
                    scores.append(score)
                    rows.append({"compound": num, "receptor": rid, "seed": seed,
                                 "pose_rank": rank, "score_kcal_mol": score,
                                 "pose_file": str(pose_file)})
            summary.setdefault(str(num), {})[rid] = {
                "best": round(min(scores), 3), "mean": round(float(np.mean(scores)), 3),
                "n_poses": len(scores), "std": round(float(np.std(scores)), 3)}
            print(f"[DONE] c{num:02d} {rid}: best={min(scores):.2f}", flush=True)

    with (OUT / "full_series_docking_results.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["compound", "receptor", "seed", "pose_rank", "score_kcal_mol", "pose_file"])
        w.writeheader()
        w.writerows(rows)
    (OUT / "full_series_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {"protocol": "24A box, vina sf, 2 seeds x exhaustiveness 16 x 5 poses",
                "receptors": RECEPTORS, "compounds": list(range(1, 40)),
                "rationale": "full-series scan; matched pairs already have 8-seed phase-4 data; "
                             "tight-box protocol not applicable (large molecules bind TM5-TM6, not orthosteric pocket)",
                "generated_utc": "2026-08-04"}
    (OUT / "full_series_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("\n=== SUMMARY ===")
    for num in range(1, 40):
        s = summary[str(num)]
        print(f"c{num:02d}: 8Z8A best={s.get('8Z8A', {}).get('best', '-'):>8}  9KT9 best={s.get('9KT9', {}).get('best', '-'):>8}")


if __name__ == "__main__":
    main()
