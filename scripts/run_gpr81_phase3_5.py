#!/usr/bin/env python3
"""Phase 3.5: align HCAR1 structures and compare docked poses in one frame."""
from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from Bio.PDB import PDBParser

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
P2 = PHASE1 / "phase2_prepared"
P3 = PHASE1 / "phase3_docking"
OUT = PHASE1 / "phase3_5_aligned"
ALIGNED_RECEPTORS = OUT / "receptors"
ALIGNED_POSES = OUT / "poses"
ALIGNED_REFERENCES = OUT / "reference_ligands"

RECEPTORS = ["8Z87", "9KT9", "8Z8A"]
FIXED = "8Z87"
POSE_RE = re.compile(r"REMARK VINA RESULT:\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)")


def pdb_atom(line: str) -> tuple[float, float, float] | None:
    try:
        return float(line[30:38]), float(line[38:46]), float(line[46:54])
    except (ValueError, IndexError):
        return None


def transform_point(point: np.ndarray, rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    return rotation @ point + translation


def kabsch(fixed: np.ndarray, moving: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    fixed_center = fixed.mean(axis=0)
    moving_center = moving.mean(axis=0)
    x = moving - moving_center
    y = fixed - fixed_center
    covariance = x.T @ y
    u, _, vt = np.linalg.svd(covariance)
    d = np.eye(3)
    d[2, 2] = np.sign(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ d @ u.T
    translation = fixed_center - rotation @ moving_center
    fitted = (rotation @ moving.T).T + translation
    rmsd = float(np.sqrt(np.mean(np.sum((fitted - fixed) ** 2, axis=1))))
    return rotation, translation, rmsd


def receptor_ca(path: Path) -> dict[int, np.ndarray]:
    structure = PDBParser(QUIET=True).get_structure(path.stem, str(path))
    chain = structure[0]["R"]
    return {res.id[1]: np.array(res["CA"].coord, dtype=float) for res in chain if "CA" in res}


def format_transformed_atom(line: str, xyz: np.ndarray) -> str:
    return f"{line[:30]}{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}{line[54:]}"


def transform_pdb_lines(lines: list[str], rotation: np.ndarray, translation: np.ndarray) -> list[str]:
    output = []
    for line in lines:
        if line.startswith(("ATOM", "HETATM")):
            p = pdb_atom(line)
            if p is not None:
                line = format_transformed_atom(line, transform_point(np.array(p), rotation, translation))
        output.append(line)
    return output


def split_pose_models(path: Path) -> list[list[str]]:
    models, current = [], []
    for line in path.read_text().splitlines():
        if line.startswith("MODEL") and current:
            models.append(current); current = []
        current.append(line)
    if current: models.append(current)
    return models


def pose_atoms(model_lines: list[str]) -> np.ndarray:
    points = [pdb_atom(line) for line in model_lines if line.startswith(("ATOM", "HETATM"))]
    return np.array([p for p in points if p is not None], dtype=float)


def model_score(model_lines: list[str]) -> float | None:
    for line in model_lines:
        m = POSE_RE.match(line)
        if m: return float(m.group(1))
    return None


def atom_count(path: Path) -> int:
    return len(pose_atoms(split_pose_models(path)[0]))


def write_pdbqt_models(path: Path, models: list[list[str]]) -> None:
    path.write_text("\n".join("\n".join(m) for m in models) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for d in [ALIGNED_RECEPTORS, ALIGNED_POSES, ALIGNED_REFERENCES]: d.mkdir(exist_ok=True)
    source_receptors = {rid: P2 / "receptors" / f"{rid}_chainR_protein.pdb" for rid in RECEPTORS}
    ca = {rid: receptor_ca(path) for rid, path in source_receptors.items()}
    common = sorted(set(ca[FIXED]).intersection(*(set(ca[r]) for r in RECEPTORS)))
    fixed_coords = np.array([ca[FIXED][n] for n in common])
    transforms = {}
    for rid in RECEPTORS:
        moving = np.array([ca[rid][n] for n in common])
        rotation, translation, rmsd = kabsch(fixed_coords, moving)
        transforms[rid] = {"rotation": rotation, "translation": translation, "alignment_rmsd_A": rmsd, "n_common_CA": len(common)}
        lines = source_receptors[rid].read_text().splitlines()
        (ALIGNED_RECEPTORS / f"{rid}_aligned_to_{FIXED}.pdb").write_text("\n".join(transform_pdb_lines(lines, rotation, translation)) + "\n")
        ref = next(P2.joinpath("reference_ligands").glob(f"{rid}_*.pdb"))
        (ALIGNED_REFERENCES / f"{ref.name[:-4]}_aligned_to_{FIXED}.pdb").write_text("\n".join(transform_pdb_lines(ref.read_text().splitlines(), rotation, translation)) + "\n")

    result_rows = list(csv.DictReader((P3 / "docking_results.csv").open()))
    compounds = sorted({r["compound_id"] for r in result_rows})
    rmsd_rows, pose_rows = [], []
    aligned_pose_paths = {}
    for cid in compounds:
        pose_arrays = {}
        for rid in RECEPTORS:
            src = P3 / "poses" / rid / f"{cid}.pdbqt"
            models = split_pose_models(src)
            transformed = []
            for model in models:
                transformed.append(transform_pdb_lines(model, transforms[rid]["rotation"], transforms[rid]["translation"]))
            dest = ALIGNED_POSES / f"{cid}_{rid}_aligned_to_{FIXED}.pdbqt"
            write_pdbqt_models(dest, transformed)
            aligned_pose_paths[rid] = dest
            pose_arrays[rid] = pose_atoms(transformed[0])
            pose_rows.append({"compound_id":cid,"receptor_id":rid,"pose_rank":1,"score_kcal_mol":model_score(transformed[0]),"aligned_pose":str(dest)})
        base = pose_arrays[FIXED]
        for rid, arr in pose_arrays.items():
            rmsd = float(np.sqrt(np.mean(np.sum((arr - base) ** 2, axis=1)))) if arr.shape == base.shape else None
            rmsd_rows.append({"compound_id":cid,"reference_receptor":FIXED,"moving_receptor":rid,"pose_rank":1,"ligand_heavy_atom_count":len(arr),"ligand_rmsd_A":None if rmsd is None else round(rmsd,3),"alignment_rmsd_A":round(transforms[rid]["alignment_rmsd_A"],3),"status":"ok" if rmsd is not None else "atom_count_mismatch"})

    with (OUT / "receptor_alignment_manifest.json").open("w") as fh:
        json.dump({"fixed_receptor":FIXED,"common_CA_residues":common,"transforms":{k:{kk:(vv.tolist() if isinstance(vv,np.ndarray) else vv) for kk,vv in v.items()} for k,v in transforms.items()}},fh,indent=2)
    for name, rows in [("ligand_pose_rmsd.csv",rmsd_rows),("aligned_pose_manifest.csv",pose_rows)]:
        with (OUT / name).open("w",newline="") as fh:
            w=csv.DictWriter(fh,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

    # Lightweight, self-contained gallery using 3Dmol.js. Files are relative to gallery location.
    cards=[]
    for cid in compounds:
        cards.append(f"<section><h2>{html.escape(cid)}</h2><div class='viewer' id='v_{html.escape(cid)}'></div><script>addViewer('v_{html.escape(cid)}', '{html.escape(cid)}');</script></section>")
    pose_json={cid:{rid:str((Path("poses") / f"{cid}_{rid}_aligned_to_{FIXED}.pdbqt")) for rid in RECEPTORS} for cid in compounds}
    receptor_json={rid:str(Path("receptors") / f"{rid}_aligned_to_{FIXED}.pdb") for rid in RECEPTORS}
    gallery=f'''<!doctype html><html><head><meta charset="utf-8"><title>HCAR1 GPR81 Phase 3.5 aligned poses</title><script src="https://3Dmol.org/build/3Dmol-min.js"></script><style>body{{font-family:Arial;background:#111;color:#eee}}section{{margin:20px auto;max-width:1100px}}.viewer{{height:520px;border:1px solid #555}}</style></head><body><h1>HCAR1/GPR81 aligned docking poses</h1><p>Fixed frame: {FIXED}. Receptor chain R aligned by common Cα residues. Computational hypotheses only.</p>{''.join(cards)}<script>const rec={json.dumps(receptor_json)};const poses={json.dumps(pose_json)};function addViewer(id,cid){{let e=document.getElementById(id),v=$3Dmol.createViewer(e,{{backgroundColor:'#111'}});Object.entries(rec).forEach(([rid,p])=>fetch(p).then(r=>r.text()).then(t=>{{v.addModel(t,'pdb');v.setStyle({{model:-1}},{{cartoon:{{color:rid==='8Z87'?'white':rid==='9KT9'?'cyan':'magenta',opacity:0.35}}}});return fetch(poses[cid][rid]);}}).then(r=>r.text()).then(t=>{{v.addModel(t,'pdbqt');v.setStyle({{model:-1}},{{stick:{{colorscheme:'greenCarbon'}}}});v.zoomTo();v.render();}}));}}</script></body></html>'''
    (OUT / "gpr81_aligned_pose_gallery.html").write_text(gallery)
    report=["# GPR81 Phase 3.5 aligned pose comparison","",f"Fixed frame: {FIXED}; common Cα residues: {len(common)}.","","## Receptor alignment"]
    for rid in RECEPTORS: report.append(f"- {rid}: backbone alignment RMSD {transforms[rid]['alignment_rmsd_A']:.3f} Å")
    report += ["","## Pose RMSD (pose 1, after receptor alignment)"]
    for r in rmsd_rows: report.append(f"- {r['compound_id']} {r['moving_receptor']} vs {FIXED}: ligand RMSD={r['ligand_rmsd_A']} Å; status={r['status']}")
    report += ["","## Caveat","","Ligand RMSD compares the same prepared atom ordering across receptor conformations. It measures pose consistency, not binding affinity or agonism. The gallery is a visual aid; interaction claims must be read with the Phase-3 contact table.",""]
    (OUT / "gpr81_phase3_5_report.md").write_text("\n".join(report))
    print(json.dumps({"common_CA":len(common),"alignment":{rid:round(transforms[rid]['alignment_rmsd_A'],3) for rid in RECEPTORS},"rmsd_rows":len(rmsd_rows),"gallery":str(OUT/'gpr81_aligned_pose_gallery.html')},indent=2))

if __name__ == "__main__": main()
