#!/usr/bin/env python3
"""Matched-pair reverse validation of the Davidsson 2020 GPR81 optimization story.

Docks the key matched pairs from the recovered paper series under the validated
multi-seed protocol (8 seeds, exhaustiveness 32) and compares docking outcomes
against the paper's reported EC50 narrative. Pairs:
  - 15 -> 26  (acyclic acyl urea -> cyclic pyridone bioisostere; EC50 0.299 -> 0.021 uM)
  - 21/22 -> 28/30 (acyl urea -> constrained analogues)
  - 30 vs 31 (pyridone vs pyrimidinone; 0.005 vs 0.24 uM)
  - 35 -> 36/37/38 (morpholine -> methyl/dimethyl-morpholine amides)
Receptors: 8Z87 and 8Z8A only (9KT9 was shown to be the noisiest view).
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from meeko import MoleculePreparation
from rdkit import Chem
from rdkit.Chem import AllChem
from vina import Vina

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
OUT = PHASE1 / "phase4_matched_pairs"
(OUT / "ligands").mkdir(parents=True, exist_ok=True)
(OUT / "poses").mkdir(parents=True, exist_ok=True)

MATCHED_PAIRS = {
    "15->26": {"from": 15, "to": 26, "narrative": "acyl urea -> pyridone bioisostere (0.299 -> 0.021 uM)"},
    "22->30": {"from": 22, "to": 30, "narrative": "acyl urea -> pyridone w/ same RHS (0.166 -> 0.005 uM)"},
    "21->28": {"from": 21, "to": 28, "narrative": "acyl urea -> pyridone w/ hydroxyacetyl (0.895 -> 0.022 uM)"},
    "30 vs 31": {"from": 30, "to": 31, "narrative": "pyridone vs pyrimidinone (0.005 vs 0.24 uM)"},
    "35->36/37/38": {"from": 35, "to": 38, "narrative": "morpholine -> cis-2,6-diMe morpholine amide (0.60 -> 0.054 uM)"},
}
COMPOUNDS = {15, 21, 22, 26, 28, 30, 31, 35, 36, 37, 38}
RECEPTORS = ["8Z87", "8Z8A"]
SEEDS = [20260803, 1, 2, 3, 4, 5, 6, 7]
EXHAUSTIVENESS = 32
N_POSES = 5


def prepare_ligand(num: int) -> Path:
    sdf = PHASE1 / "paper_ligands" / f"compound_{num:02d}.sdf"
    out = OUT / "ligands" / f"compound_{num:02d}.pdbqt"
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
    # meeko 0.7.x: use PDBQTWriterLegacy to serialize the prepared setup
    from meeko import PDBQTWriterLegacy
    pdbqt_str, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        raise RuntimeError(f"PDBQTWriterLegacy failed for {num}: {err}")
    out.write_text(pdbqt_str)
    return out


def parse_poses(path: Path) -> list[dict]:
    rows = []
    cur = None
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            cur = int(line.split()[1])
        if line.startswith("REMARK VINA RESULT:"):
            rows.append({"pose_rank": cur, "score": float(line.split()[3])})
    return rows


def main():
    p2 = json.loads((PHASE1 / "phase2_prepared/phase2_manifest.json").read_text())
    receptors = {s["pdb_id"]: s for s in p2["structures"] if s["pdb_id"] in RECEPTORS}

    ligands = {}
    for num in COMPOUNDS:
        ligands[num] = prepare_ligand(num)
        print(f"[PREP] compound {num}: {ligands[num].name} ({ligands[num].stat().st_size} B)", flush=True)

    rows = []
    for rid in RECEPTORS:
        rec = receptors[rid]
        geom = rec["ligand_geometry"]
        for num in sorted(COMPOUNDS):
            all_scores = []
            for seed in SEEDS:
                v = Vina(sf_name="vina", seed=seed)
                v.set_receptor(rec["receptor_pdbqt"]["path"])
                v.compute_vina_maps(center=geom["center_A"], box_size=geom["box_size_A"])
                v.set_ligand_from_file(str(ligands[num]))
                v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
                pose_file = OUT / "poses" / f"c{num}_{rid}_seed{seed}.pdbqt"
                v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
                parsed = parse_poses(pose_file)
                for p in parsed:
                    all_scores.append(p["score"])
                    rows.append({"compound": num, "receptor": rid, "seed": seed,
                                 "pose_rank": p["pose_rank"], "score_kcal_mol": p["score"]})
            best = min(all_scores) if all_scores else None
            mean = float(np.mean(all_scores)) if all_scores else None
            print(f"[DONE] c{num} {rid}: best={best:.2f} mean={mean:.2f} n={len(all_scores)}", flush=True)

    with (OUT / "matched_pair_docking_results.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["compound", "receptor", "seed", "pose_rank", "score_kcal_mol"])
        w.writeheader()
        w.writerows(rows)

    # Summary per compound per receptor
    summary = {}
    for num in sorted(COMPOUNDS):
        summary[num] = {}
        for rid in RECEPTORS:
            scores = [r["score_kcal_mol"] for r in rows if r["compound"] == num and r["receptor"] == rid]
            if scores:
                summary[num][rid] = {"best": round(min(scores), 3), "mean": round(float(np.mean(scores)), 3),
                                     "n_poses": len(scores), "std": round(float(np.std(scores)), 3)}
    (OUT / "matched_pair_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print("\n=== SUMMARY ===")
    print(f"{'comp':>5} {'8Z87 best':>10} {'8Z87 mean':>10} {'8Z8A best':>10} {'8Z8A mean':>10}")
    for num in sorted(COMPOUNDS):
        s = summary[num]
        b87 = s.get("8Z87", {}).get("best", "-")
        m87 = s.get("8Z87", {}).get("mean", "-")
        b8a = s.get("8Z8A", {}).get("best", "-")
        m8a = s.get("8Z8A", {}).get("mean", "-")
        print(f"{num:>5} {b87:>10} {m87:>10} {b8a:>10} {m8a:>10}")


if __name__ == "__main__":
    main()
