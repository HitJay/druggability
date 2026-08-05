#!/usr/bin/env python3
"""Phase 5 - tight-box redocking across all receptors (P0/P1 remediation).

!!! SUPERSEDED 2026-08-04 - DO NOT RUN FULL SCOPE !!!

This script's full-scope design (tight box for EVERY compound incl. large
Davidsson-series molecules) was proven wrong mid-run: large molecules bind the
TM5-TM6 extracellular region 12-14 A from the co-crystal center, so a tight box
centered on the co-crystal ligand forces them into steric clash (positive
scores) instead of measuring compatibility. The correct scope is
`run_gpr81_9kt9_tightbox.py` (orthosteric-pocket small acids only) plus the
positional analysis in `analyze_gpr81_tightbox_summary.py`. Kept for audit
trail only; see gpr81_phase5_tightbox_report.md.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from vina import Vina
from meeko import PDBQTWriterLegacy, MoleculePreparation
from rdkit import Chem
from rdkit.Chem import AllChem

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
OUT = PHASE1 / "phase5_tightbox"
(OUT / "poses").mkdir(parents=True, exist_ok=True)

RECEPTORS = ["8Z87", "8Z8A", "9KT9"]          # 8Z8B apo has no ligand-anchored box
TOOL_COMPOUNDS = ["CHBA", "3_5_DHBA", "3_OBA", "AZ1_GPR81_agonist_2", "GPR81_agonist_1"]
PAPER_COMPOUNDS = [15, 21, 22, 26, 28, 30, 31, 35, 36, 37, 38]
SEEDS = [20260803, 1]
EXHAUSTIVENESS = 16
N_POSES = 5
MIN_BOX = 12.0

# co-crystal pair for redock control validation
COCRYSTAL = {"8Z87": ("CHBA", "A1D71"), "8Z8A": ("lactate", "2OP"), "9KT9": ("3_5_DHBA", "34D")}


def heavy_atoms_pdbqt(path: Path) -> list[np.ndarray]:
    out = []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el != "H":
                    out.append(np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]))
            except (ValueError, IndexError):
                continue
    return out


def heavy_atoms_pdb(path: Path) -> list[np.ndarray]:
    out = []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el != "H":
                    out.append(np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]))
            except (ValueError, IndexError):
                fields = line.split()
                try:
                    if fields[2].upper() != "H":
                        out.append(np.array([float(fields[6]), float(fields[7]), float(fields[8])]))
                except (ValueError, IndexError):
                    continue
    return out


def ligand_span(pdbqt: Path) -> np.ndarray:
    a = heavy_atoms_pdbqt(pdbqt)
    a = np.array(a)
    return a.max(axis=0) - a.min(axis=0)


def prepare_ligand(sdf: Path, out: Path) -> None:
    if out.exists():
        return
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
        raise RuntimeError(f"expected 1 prep for {sdf.name}, got {len(setups)}")
    pdbqt_str, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        raise RuntimeError(f"PDBQTWriterLegacy failed for {sdf.name}: {err}")
    out.write_text(pdbqt_str)


def parse_pose_models(path: Path) -> list[tuple[int, float, list[np.ndarray]]]:
    """Return [(pose_rank, score, heavy_atom_coords)] per MODEL."""
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
    receptors = {s["pdb_id"]: s for s in p2["structures"] if s["pdb_id"] in RECEPTORS}

    # ---- gather ligand pdbqts ----
    ligands: dict[str, Path] = {}
    for cid in TOOL_COMPOUNDS:
        p = PHASE1 / "phase3_docking/ligands_pdbqt" / f"{cid}.pdbqt"
        if not p.exists():
            raise RuntimeError(f"missing tool ligand pdbqt {p}")
        ligands[cid] = p
    for num in PAPER_COMPOUNDS:
        sdf = PHASE1 / "paper_ligands" / f"compound_{num:02d}.sdf"
        out = PHASE1 / "phase4_matched_pairs/ligands" / f"compound_{num:02d}.pdbqt"
        prepare_ligand(sdf, out)
        ligands[f"c{num}"] = out

    # ---- build manifest + run ----
    manifest = {"receptors": {}, "compounds": sorted(ligands), "seeds": SEEDS,
                "exhaustiveness": EXHAUSTIVENESS, "n_poses": N_POSES,
                "box_rule": "ceil(max(ligand_span+3, cocrystal_span+5, 12))"}
    rows, summary = [], {}
    controls = []

    for rid in RECEPTORS:
        rec = receptors[rid]
        cocrystal_cid, cocrystal_resn = COCRYSTAL[rid]
        ref_lig_pdb = PHASE1 / "phase2_prepared/reference_ligands" / f"{rid}_{cocrystal_resn}.pdb"
        exp_centroid = np.mean(np.array(heavy_atoms_pdb(ref_lig_pdb)), axis=0)
        exp_span = np.array(rec["ligand_geometry"]["ligand_span_A"])
        receptor_pdbqt = rec["receptor_pdbqt"]["path"]
        manifest["receptors"][rid] = {"state": rec["state"], "exp_centroid": exp_centroid.tolist(),
                                      "exp_span": exp_span.tolist()}

        for cid in sorted(ligands):
            lig_path = ligands[cid]
            lig_span = ligand_span(lig_path)
            box = [max(ls + 3.0, es + 5.0, MIN_BOX) for ls, es in zip(lig_span, exp_span)]
            box = [round(b) for b in box]
            manifest.setdefault("boxes", {})[f"{cid}|{rid}"] = {"ligand_span": lig_span.tolist(),
                                                                "box_size_A": box}
            all_scores = []
            for seed in SEEDS:
                v = Vina(sf_name="vina", seed=seed)
                v.set_receptor(receptor_pdbqt)
                v.compute_vina_maps(center=exp_centroid.tolist(), box_size=box)
                v.set_ligand_from_file(str(lig_path))
                v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
                pose_file = OUT / "poses" / f"{cid}_{rid}_seed{seed}.pdbqt"
                v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
                for rank, score, _ in parse_pose_models(pose_file):
                    all_scores.append(score)
                    rows.append({"compound": cid, "receptor": rid, "seed": seed,
                                 "pose_rank": rank, "score_kcal_mol": score,
                                 "pose_file": str(pose_file)})
            if all_scores:
                summary.setdefault(cid, {})[rid] = {"best": round(min(all_scores), 3),
                                                    "mean": round(float(np.mean(all_scores)), 3),
                                                    "n_poses": len(all_scores),
                                                    "std": round(float(np.std(all_scores)), 3)}
            print(f"[DONE] {cid} {rid}: best={min(all_scores):.2f}", flush=True)

        # redock control: co-crystal ligand on its own receptor
        lig_path = ligands[cocrystal_cid]
        box = [round(max(ls + 3.0, es + 5.0, MIN_BOX)) for ls, es in zip(ligand_span(lig_path), exp_span)]
        all_dists = []
        for seed in SEEDS:
            v = Vina(sf_name="vina", seed=seed)
            v.set_receptor(receptor_pdbqt)
            v.compute_vina_maps(center=exp_centroid.tolist(), box_size=box)
            v.set_ligand_from_file(str(lig_path))
            v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
            pose_file = OUT / "poses" / f"REDOCK_{cocrystal_cid}_{rid}_seed{seed}.pdbqt"
            v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
            for rank, score, patoms in parse_pose_models(pose_file):
                if not patoms:
                    continue
                d = float(np.linalg.norm(np.mean(np.array(patoms), axis=0) - exp_centroid))
                all_dists.append({"seed": seed, "pose_rank": rank, "score_kcal_mol": score,
                                  "centroid_distance_A": round(d, 3)})
        best_dist = min(all_dists, key=lambda x: x["centroid_distance_A"])
        controls.append({"receptor_id": rid, "cocrystal_ligand": cocrystal_cid,
                         "exp_centroid": exp_centroid.tolist(), "box_size_A": box,
                         "best_centroid_recovery_A": best_dist["centroid_distance_A"],
                         "best_recovery_score_kcal_mol": best_dist["score_kcal_mol"],
                         "all_pose_distances": [d["centroid_distance_A"] for d in all_dists]})
        print(f"[REDOCK] {rid} {cocrystal_cid}: best centroid recovery = {best_dist['centroid_distance_A']:.2f} A", flush=True)

    with (OUT / "tightbox_docking_results.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["compound", "receptor", "seed", "pose_rank", "score_kcal_mol", "pose_file"])
        w.writeheader(); w.writerows(rows)
    (OUT / "tightbox_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT / "tightbox_redock_controls.json").write_text(json.dumps(controls, indent=2) + "\n")
    (OUT / "tightbox_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("\n=== SUMMARY ===")
    for cid in sorted(summary):
        line = f"{cid:>22} " + " ".join(f"{rid}:{summary[cid].get(rid, {}).get('best', '-'):>7}" for rid in RECEPTORS)
        print(line)


if __name__ == "__main__":
    main()
