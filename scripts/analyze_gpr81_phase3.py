#!/usr/bin/env python3
"""Analyze GPR81 Phase-3 Vina poses without over-interpreting scores."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
P3 = PHASE1 / "phase3_docking"
PHASE2 = PHASE1 / "phase2_prepared/phase2_manifest.json"
RESULTS = P3 / "docking_results.csv"
OUT_SUMMARY = P3 / "tool_compound_binding_mode_comparison.csv"
OUT_CONTACTS = P3 / "tool_compound_residue_interactions.csv"
OUT_REPORT = P3 / "gpr81_tool_compound_binding_mode_report.md"

CORE_RESIDUES = {71, 75, 92, 95, 96, 99, 165, 167, 168, 261, 264, 268}
POCKET_CUTOFF = 4.0


def pdb_atoms(path: Path, ligand: bool = False) -> list[dict]:
    atoms = []
    for line in path.read_text().splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            element = line[76:78].strip() or line[12:16].strip()[0]
            if element.upper() == "H":
                continue
            atoms.append({
                "name": line[12:16].strip(),
                "resname": line[17:20].strip(),
                "chain": line[21:22].strip(),
                "resnum": int(line[22:26]),
                "x": float(line[30:38]), "y": float(line[38:46]), "z": float(line[46:54]),
                "element": element.upper(),
            })
        except (ValueError, IndexError):
            continue
    return atoms


def distance(a: dict, b: dict) -> float:
    return math.sqrt((a["x"]-b["x"])**2 + (a["y"]-b["y"])**2 + (a["z"]-b["z"])**2)


def interaction_type(resname: str, ligand_atoms: list[dict], residue_atoms: list[dict], min_d: float) -> str:
    polar_res = {"ARG", "LYS", "ASP", "GLU", "HIS", "SER", "THR", "ASN", "GLN", "TYR", "CYS"}
    aromatic = {"PHE", "TYR", "TRP", "HIS"}
    lig_hetero = any(a["element"] in {"N", "O", "S"} for a in ligand_atoms)
    if min_d <= 3.5 and resname in polar_res and lig_hetero:
        return "polar_or_hbond_candidate"
    if resname in aromatic:
        return "aromatic_or_hydrophobic_contact"
    return "hydrophobic_contact"


def main() -> None:
    phase2 = json.loads(PHASE2.read_text())
    receptor_atoms = {r["pdb_id"]: pdb_atoms(Path(r["receptor_pdb"])) for r in phase2["structures"]}
    rows = list(csv.DictReader(RESULTS.open()))
    compounds = sorted({r["compound_id"] for r in rows})
    receptors = sorted({r["receptor_id"] for r in rows})
    contacts = []
    summary = []
    for cid in compounds:
        for rid in receptors:
            sub = [r for r in rows if r["compound_id"] == cid and r["receptor_id"] == rid and not r["error"]]
            if not sub:
                continue
            sub.sort(key=lambda r: int(r["pose_rank"]))
            pose_file = Path(sub[0]["pose_file"])
            # Vina PDBQT contains MODEL blocks; split and analyze each model separately.
            blocks = []
            current = []
            for line in pose_file.read_text().splitlines():
                if line.startswith("MODEL") and current:
                    blocks.append(current); current = []
                if line.startswith(("ATOM", "HETATM")):
                    current.append(line)
            if current: blocks.append(current)
            ensemble_contact_sets = []
            for rank, block in enumerate(blocks, start=1):
                ligand_path = pose_file.parent / f"_{cid}_{rid}_{rank}.tmp.pdb"
                ligand_path.write_text("\n".join(block)+"\n")
                lig_atoms = pdb_atoms(ligand_path, ligand=True)
                ligand_path.unlink()
                grouped = defaultdict(list)
                for atom in receptor_atoms[rid]:
                    grouped[(atom["resname"], atom["resnum"])].append(atom)
                pose_contacts = []
                for (resname, resnum), ratoms in grouped.items():
                    min_d = min(distance(la, ra) for la in lig_atoms for ra in ratoms)
                    if min_d <= POCKET_CUTOFF:
                        kind = interaction_type(resname, lig_atoms, ratoms, min_d)
                        pose_contacts.append((resname, resnum, round(min_d, 3), kind))
                        contacts.append({"compound_id": cid, "receptor_id": rid, "pose_rank": rank, "residue": resname, "residue_number": resnum, "min_distance_A": round(min_d, 3), "interaction_class": kind, "core_residue": resnum in CORE_RESIDUES})
                ensemble_contact_sets.append({(x[0], x[1]) for x in pose_contacts})
            pose1 = [c for c in contacts if c["compound_id"] == cid and c["receptor_id"] == rid and c["pose_rank"] == 1]
            core = sorted({c["residue_number"] for c in pose1 if c["core_residue"]})
            all_res = sorted({c["residue_number"] for c in pose1})
            scores = [float(r["score_kcal_mol"]) for r in sub]
            ensemble_union = set().union(*ensemble_contact_sets) if ensemble_contact_sets else set()
            ensemble_intersection = set.intersection(*ensemble_contact_sets) if ensemble_contact_sets else set()
            summary.append({
                "compound_id": cid, "receptor_id": rid, "n_poses": len(sub),
                "best_score_kcal_mol": min(scores), "pose1_score_kcal_mol": scores[0],
                "score_span_kcal_mol": max(scores)-min(scores),
                "pose1_core_residues": ";".join(map(str, core)),
                "pose1_contact_residues": ";".join(f"{r}{n}" for r,n in [(c["residue"],c["residue_number"]) for c in pose1]),
                "pose_ensemble_union_n_residues": len(ensemble_union),
                "pose_ensemble_intersection_n_residues": len(ensemble_intersection),
                "pose1_core_contact_fraction": round(len(core)/len(CORE_RESIDUES), 3),
                "warning": "positive_or_weak_score" if min(scores) > -2 else ("broad_pose_ensemble" if max(scores)-min(scores) > 1.5 else ""),
            })
    with OUT_CONTACTS.open("w", newline="") as fh:
        fields=list(contacts[0].keys()) if contacts else []
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(contacts)
    with OUT_SUMMARY.open("w", newline="") as fh:
        fields=list(summary[0].keys())
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(summary)
    # Cross-receptor aggregate, keeping the result descriptive rather than inferential.
    lines=["# GPR81 tool-compound binding-mode analysis (Phase 3)","","> This is a computational pose comparison. It does not prove agonism, affinity, or selectivity.","",f"Docking receptors: {', '.join(receptors)}. Apo 8Z8B was excluded because its pocket box was not transferred without structural alignment.","", "## Pose summary", ""]
    for cid in compounds:
        ss=[x for x in summary if x["compound_id"]==cid]
        lines.append(f"### {cid}")
        for x in ss:
            lines.append(f"- {x['receptor_id']}: pose1={x['pose1_score_kcal_mol']:.3f} kcal/mol; score span={x['score_span_kcal_mol']:.3f}; core contact fraction={x['pose1_core_contact_fraction']:.3f}; core residues={x['pose1_core_residues'] or 'none'}; warning={x['warning'] or 'none'}")
        lines.append("")
    lines += ["## Interpretation rules", "", "- More negative Vina score is only a local computational ranking signal.", "- A credible comparison requires compatible pocket occupancy, reproducible contacts across receptor conformations, and agreement with experimental biology.", "- AZ1 and GPR81 agonist 1 should be treated cautiously if pose scores are weak/positive or if the pose ensemble is broad.", "- The next report should overlay aligned receptor structures and compare ligand poses in a common coordinate frame.", ""]
    OUT_REPORT.write_text("\n".join(lines))
    print(json.dumps({"summary_rows":len(summary),"contact_rows":len(contacts),"summary":str(OUT_SUMMARY),"contacts":str(OUT_CONTACTS),"report":str(OUT_REPORT)},indent=2))

if __name__ == "__main__": main()
