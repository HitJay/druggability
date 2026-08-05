#!/usr/bin/env python3
"""Phase 5 - tight-box redocking on 9KT9 for orthosteric-pocket small molecules.

Scope (narrowed after REVIEW_2026-08-04 + positional analysis):
  The 24A box on 9KT9 lets Vina find a "deep-insert" global optimum for small
  acids (3,5-DHBA redock centroid 5.71 A). A 12A tight box centered on the
  co-crystal ligand recovers the experimental pose (best 1.66 A, see
  phase3_5_controls_restrained). Tight-box is ONLY valid for compounds whose
  binding site is the orthosteric pocket, i.e. the small tool acids
  (CHBA, 3,5-DHBA, 3-OBA). Large series molecules (AZ1, GPR81_agonist_1,
  paper compounds) bind the TM5-TM6 extracellular region 12-14 A away from
  the co-crystal center and MUST NOT be re-docked with a tight box -- their
  positional analysis is handled separately (analyze_gpr81_tightbox_summary.py).

Outputs:
  phase5_tightbox/9kt9_small_acid_redock.csv + .json  (audit trail)
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from vina import Vina

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
OUT = PHASE1 / "phase5_tightbox"
(OUT / "poses").mkdir(parents=True, exist_ok=True)

COMPOUNDS = ["CHBA", "3_5_DHBA", "3_OBA"]
SEEDS = [20260803, 1, 2]
EXHAUSTIVENESS = 32
N_POSES = 5


def heavy_atoms_pdb(path: Path) -> list[np.ndarray]:
    out = []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            # reference-ligand PDBs written by local scripts use non-standard
            # column widths (e.g. two-char chain id); whitespace split is robust.
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
    geom = rec["ligand_geometry"]
    exp_centroid = np.mean(np.array(heavy_atoms_pdb(PHASE1 / "phase2_prepared/reference_ligands/9KT9_34D.pdb")), axis=0)
    exp_span = np.array(geom["ligand_span_A"])
    # fixed 12A tight box centered on 34D (matches validated restrained control)
    box = [12.0, 12.0, 12.0]

    rows, controls = [], []
    for cid in COMPOUNDS:
        lig = PHASE1 / "phase3_docking/ligands_pdbqt" / f"{cid}.pdbqt"
        assert lig.exists(), lig
        for seed in SEEDS:
            v = Vina(sf_name="vina", seed=seed)
            v.set_receptor(rec["receptor_pdbqt"]["path"])
            v.compute_vina_maps(center=exp_centroid.tolist(), box_size=box)
            v.set_ligand_from_file(str(lig))
            v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
            pose_file = OUT / "poses" / f"{cid}_9KT9_tight_seed{seed}.pdbqt"
            v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
            for rank, score, patoms in parse_pose_models(pose_file):
                if not patoms:
                    continue
                d = float(np.linalg.norm(np.mean(np.array(patoms), axis=0) - exp_centroid))
                rows.append({"compound": cid, "receptor": "9KT9", "seed": seed, "pose_rank": rank,
                             "score_kcal_mol": score, "centroid_distance_A": round(d, 3),
                             "pose_file": str(pose_file)})
        scores = [r["score_kcal_mol"] for r in rows if r["compound"] == cid]
        dists = [r["centroid_distance_A"] for r in rows if r["compound"] == cid]
        print(f"[DONE] {cid} 9KT9 tight: best={min(scores):.3f}, best centroid recovery={min(dists):.2f} A", flush=True)

    # control: 3,5-DHBA (= co-crystal 34D) must recover < 2 A
    for seed in SEEDS:
        v = Vina(sf_name="vina", seed=seed)
        v.set_receptor(rec["receptor_pdbqt"]["path"])
        v.compute_vina_maps(center=exp_centroid.tolist(), box_size=box)
        v.set_ligand_from_file(str(PHASE1 / "phase3_docking/ligands_pdbqt/3_5_DHBA.pdbqt"))
        v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
        pose_file = OUT / "poses" / f"REDOCK_3_5_DHBA_9KT9_tight_seed{seed}.pdbqt"
        v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
        for rank, score, patoms in parse_pose_models(pose_file):
            if not patoms:
                continue
            d = float(np.linalg.norm(np.mean(np.array(patoms), axis=0) - exp_centroid))
            controls.append({"seed": seed, "pose_rank": rank, "score_kcal_mol": score,
                             "centroid_distance_A": round(d, 3)})
    best_ctrl = min(controls, key=lambda x: x["centroid_distance_A"])
    print(f"[REDOCK] 3_5_DHBA->9KT9 tight: best centroid recovery = {best_ctrl['centroid_distance_A']:.2f} A", flush=True)

    with (OUT / "9kt9_small_acid_redock.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["compound", "receptor", "seed", "pose_rank", "score_kcal_mol", "centroid_distance_A", "pose_file"])
        w.writeheader(); w.writerows(rows)
    summary = {
        "protocol": "tight-box (12A, centered on 34D co-crystal centroid), exhaustiveness 32, 3 seeds",
        "rationale": "9KT9 24A-box deep-insert artifact (see REVIEW_2026-08-04.md P0); tight box valid only for orthosteric-pocket small acids",
        "redock_control_3_5_DHBA": {"best_centroid_recovery_A": best_ctrl["centroid_distance_A"],
                                     "best_recovery_score": best_ctrl["score_kcal_mol"],
                                     "all_distances": [c["centroid_distance_A"] for c in controls]},
        "per_compound": {cid: {"best_score": round(min(r["score_kcal_mol"] for r in rows if r["compound"] == cid), 3),
                               "best_centroid_recovery_A": round(min(r["centroid_distance_A"] for r in rows if r["compound"] == cid), 3)}
                         for cid in COMPOUNDS},
        "note": "AZ1 / GPR81_agonist_1 / paper compounds deliberately excluded: they bind the TM5-TM6 extracellular region, not the orthosteric pocket.",
    }
    (OUT / "9kt9_small_acid_redock.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
