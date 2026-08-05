#!/usr/bin/env python3
"""
GPR81 follow-up: dock L-lactate (endogenous ligand) into 9KT9 with the
validated tight-box protocol (12A box centered on the 34D co-crystal
centroid, exhaustiveness 32, 3 seeds) - the 46th ligand-receptor pair of
the follow-up deliverable.

Rationale: lactate's cognate structure is 8Z8A (2OP co-crystal). Docking it
into 9KT9's orthosteric pocket (3,5-DHBA-bound) tests whether the endogenous
agonist recovers the same pocket on a second active-state structure. Lactate
is a small acid of the co-crystal chemotype class, so the tight box is valid
(same rationale as the phase-5 small-acid redocks). This is a
cross-structure control, not a screening hit.

Outputs: followup_2026-08/data/lactate_9kt9_tightbox.csv + .json
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from vina import Vina

ROOT = Path(__file__).resolve().parents[3]
PHASE1 = ROOT / "data/gpr81_phase1"
OUT = Path(__file__).resolve().parent / "data"
(OUT / "poses").mkdir(parents=True, exist_ok=True)

SEEDS = [20260803, 1, 2]
EXHAUSTIVENESS = 32
N_POSES = 5
BOX = [12.0, 12.0, 12.0]


def heavy_atoms_pdb(path: Path) -> list[np.ndarray]:
    out = []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            fields = line.split()
            if len(fields) < 9:
                continue
            el = fields[2].rstrip("0123456789").upper()
            if el == "H":
                continue
            try:
                out.append(np.array([float(fields[6]), float(fields[7]), float(fields[8])]))
            except (ValueError, IndexError):
                continue
    return out


def parse_pose_models(path: Path) -> list[tuple[int, float, list[np.ndarray]]]:
    models, cur, score, acc = [], None, None, []
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            cur = int(line.split()[1]); acc = []; score = None
        elif line.startswith("REMARK VINA RESULT:"):
            score = float(line.split()[3])
        elif line.startswith(("ATOM", "HETATM")):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el != "H":
                    acc.append(np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]))
            except (ValueError, IndexError):
                continue
        elif line.startswith("ENDMDL") and cur is not None:
            models.append((cur, score, acc)); cur = None
    return models


def main() -> None:
    p2 = json.loads((PHASE1 / "phase2_prepared/phase2_manifest.json").read_text())
    rec = next(s for s in p2["structures"] if s["pdb_id"] == "9KT9")
    exp_centroid = np.mean(np.array(heavy_atoms_pdb(PHASE1 / "phase2_prepared/reference_ligands/9KT9_34D.pdb")), axis=0)
    lig = PHASE1 / "phase3_5_controls/ligands/lactate.pdbqt"
    assert lig.exists(), lig

    rows = []
    for seed in SEEDS:
        v = Vina(sf_name="vina", seed=seed)
        v.set_receptor(rec["receptor_pdbqt"]["path"])
        v.compute_vina_maps(center=exp_centroid.tolist(), box_size=BOX)
        v.set_ligand_from_file(str(lig))
        v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
        pose_file = OUT / "poses" / f"lactate_9KT9_tight_seed{seed}.pdbqt"
        v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
        for rank, score, patoms in parse_pose_models(pose_file):
            if not patoms:
                continue
            d = float(np.linalg.norm(np.mean(np.array(patoms), axis=0) - exp_centroid))
            rows.append({"compound": "lactate", "receptor": "9KT9", "seed": seed, "pose_rank": rank,
                         "score_kcal_mol": score, "centroid_distance_A": round(d, 3),
                         "pose_file": str(pose_file)})
    best = min(rows, key=lambda r: r["score_kcal_mol"])
    best_rec = min(rows, key=lambda r: r["centroid_distance_A"])
    print(f"[DONE] lactate->9KT9 tight: best score {best['score_kcal_mol']:.3f} (centroid {best['centroid_distance_A']:.2f} A); "
          f"best centroid recovery {best_rec['centroid_distance_A']:.2f} A (score {best_rec['score_kcal_mol']:.3f})", flush=True)

    with (OUT / "lactate_9kt9_tightbox.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["compound", "receptor", "seed", "pose_rank", "score_kcal_mol", "centroid_distance_A", "pose_file"])
        w.writeheader(); w.writerows(rows)
    summary = {
        "protocol": "tight-box (12A centered on 34D co-crystal centroid), exhaustiveness 32, 3 seeds",
        "compound": "L-lactate (endogenous HCAR1 agonist; cognate co-crystal 2OP in 8Z8A)",
        "receptor": "9KT9 (3,5-DHBA-bound HCAR1-Gi, 34D orthosteric pocket)",
        "note": "cross-structure control: does the endogenous ligand recover the orthosteric pocket on a second active-state structure?",
        "best_score_kcal_mol": round(best["score_kcal_mol"], 3),
        "best_centroid_recovery_A": round(best_rec["centroid_distance_A"], 3),
        "all_centroid_A": [r["centroid_distance_A"] for r in rows],
        "comparison_8Z8A_cognate": {"score": -4.361, "centroid_recovery_A": 2.886},
    }
    (OUT / "lactate_9kt9_tightbox.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
