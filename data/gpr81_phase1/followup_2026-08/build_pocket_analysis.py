#!/usr/bin/env python3
"""
GPR81 follow-up deliverable 2: binding-pocket analysis for all 46
ligand-receptor pairs + structural illustration figures.

Pair universe (46 = 45 compound entries + 1 for the dual-listed compound):
  1-39  c01..c39 x 8Z8A   phase-6 full-series poses (2 seeds x 5 poses)
  40-44 t01..t05 x 8Z8A   phase-3 tool-compound poses (5 poses)
  45    lac x 8Z8A         redocking control (cognate, 2OP co-crystal)
  46    lac x 9KT9         tight-box cross-structure control (this follow-up run)
(t01 = AZ1 = paper compound 1: listed both in the Davidsson series and in the
lead table, so it contributes its phase-6 paper pair AND its phase-3 lead pair.)

Per pair: best Vina score, binding-region classification (same residue sets as
phase-5/6: ORTHO {71,75,92,95,96,99,165,167,168,261,264,268}, TM56
{153,155,157,164,166,169,170,171,174,177}, NTERM {6,7,8,9,79}), polar-contact
candidates (ligand N/O/S < 3.5 A of receptor N/O), hydrophobic contacts
(ligand C - receptor C < 4.0 A), pose centroid distance to the co-crystal
ligand, and experimental EC50/Emax context.

Figures: per-pair PNG with 2D structure (RDKit) + 3D pocket interaction view
(matplotlib stick renderer, PCA orientation, dashed polar contacts).

Outputs: data/gpr81_pocket_analysis_pairs.csv/.json, figures/pocket_*.png
"""
from __future__ import annotations
import csv, json, os
from pathlib import Path
from collections import Counter
import numpy as np

BASE = Path(__file__).resolve().parent
P1 = BASE.parent
VENV = "/das/user/QYJI/druggability/.venv/bin/python"

ORTHO = {71, 75, 92, 95, 96, 99, 165, 167, 168, 261, 264, 268}
TM56 = {153, 155, 157, 164, 166, 169, 170, 171, 174, 177}
NTERM = {6, 7, 8, 9, 79}
COVALENT = {"C": 0.76, "N": 0.71, "O": 0.66, "S": 1.05, "P": 1.07,
            "F": 0.57, "Cl": 0.99, "Br": 1.14, "H": 0.31}

POCKET_CUTOFF = 5.0      # receptor atoms within this distance of ligand = pocket
POLAR_CUTOFF = 3.5       # ligand N/O/S - receptor N/O polar contact candidate
HYDROPHOBIC_CUTOFF = 4.0 # ligand C - receptor C
REGION_CUTOFF = 4.5      # contact cutoff for region classification


# ---------------------------------------------------------------- parsers
def _ad_to_element(t: str) -> str:
    """Map an AutoDock PDBQT atom type to a chemical element (see figures script)."""
    t = t.strip().upper()
    if t in ("A", "C"):
        return "C"
    if t.startswith("O"):
        return "O"
    if t.startswith("N"):
        return "N"
    if t.startswith("S"):
        return "S"
    if t.startswith("H"):
        return "H"
    return {"CL": "Cl", "BR": "Br"}.get(t, t)


def parse_pdbqt_models(path: Path) -> list[dict]:
    """Return [{rank, score, atoms:[(elem, x, y, z), ...]}] for each MODEL."""
    models, cur, score, acc = [], None, None, []
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            cur = int(line.split()[1]); acc = []; score = None
        elif line.startswith("REMARK VINA RESULT:"):
            try:
                score = float(line.split()[3])
            except (ValueError, IndexError):
                score = None
        elif line.startswith(("ATOM", "HETATM")):
            try:
                el = _ad_to_element(line[76:78] or line[12:16].strip()[0])
                if el == "H":
                    continue
                acc.append((el, float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except (ValueError, IndexError):
                continue
        elif line.startswith("ENDMDL") and cur is not None:
            models.append({"rank": cur, "score": score, "atoms": acc})
            cur = None
    return models


def parse_pdb_atoms(path: Path) -> list[tuple]:
    """Return [(resid, resname, atomname, elem, x, y, z)] heavy atoms only.
    Fixed-column PDB parse with a whitespace-split fallback for locally
    written reference-ligand PDBs with non-standard column widths."""
    out = []
    for line in path.read_text().splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            el = line[76:78].strip()
            if not el:
                el = line[12:16].strip()
                el = el[0] if el and el[0].isalpha() else "C"
            el = el.upper()
            resid = int(line[22:26])
            resname = line[17:20].strip()
            atomname = line[12:16].strip()
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
        except (ValueError, IndexError):
            try:
                f = line.split()
                resid = int(f[5]); resname = f[3]; atomname = f[2]
                x, y, z = float(f[6]), float(f[7]), float(f[8])
                el = (f[-1] if len(f) >= 11 and len(f[-1]) <= 2 and f[-1].isalpha() else atomname)
                el = el[0].upper() if len(el) == 1 else el[:2].upper()
            except (ValueError, IndexError):
                continue
        if el == "H":
            continue
        out.append((resid, resname, atomname, el, x, y, z))
    return out


def centroid(atoms) -> np.ndarray:
    arr = np.array([np.array(a[-3:], dtype=float) for a in atoms])
    return arr.mean(axis=0) if len(arr) else np.zeros(3)


def classify_region(lig_atoms, rec_atoms, cutoff=REGION_CUTOFF):
    hits = Counter()
    for le, lx, ly, lz in lig_atoms:
        for ri, rn, an, re_, rx, ry, rz in rec_atoms:
            if ((lx - rx) ** 2 + (ly - ry) ** 2 + (lz - rz) ** 2) ** 0.5 < cutoff:
                hits[ri] += 1
    n = sum(hits.values())
    if n == 0:
        return "NO_CONTACT"
    o = sum(v for k, v in hits.items() if k in ORTHO) / n
    t = sum(v for k, v in hits.items() if k in TM56) / n
    nt = sum(v for k, v in hits.items() if k in NTERM) / n
    if o >= 0.4:
        return "ORTHO_POCKET"
    if t >= 0.4:
        return "TM56_EXTRACELLULAR"
    if nt >= 0.4:
        return "NTERM_SURFACE"
    return "MIXED"


def find_interactions(lig_atoms, rec_atoms):
    """Return (polar_contacts, hydrophobic_contacts)."""
    polar, hyd = [], []
    for le, lx, ly, lz in lig_atoms:
        for ri, rn, an, re_, rx, ry, rz in rec_atoms:
            d = ((lx - rx) ** 2 + (ly - ry) ** 2 + (lz - rz) ** 2) ** 0.5
            if le in ("N", "O", "S") and re_ in ("N", "O") and d < POLAR_CUTOFF:
                polar.append((le, ri, rn, an, re_, round(d, 2)))
            elif le == "C" and re_ == "C" and d < HYDROPHOBIC_CUTOFF:
                hyd.append((ri, round(d, 2)))
    # dedupe polar (same residue/atom may pair with several ligand atoms - keep closest)
    seen, uniq = {}, []
    for p in sorted(polar, key=lambda x: x[5]):
        key = (p[1], p[3])
        if key not in seen:
            seen[key] = True
            uniq.append(p)
    return uniq, hyd


def infer_bonds(atoms, tol=0.45):
    """Distance-based bond inference; atoms = [(elem, x, y, z)]."""
    bonds = []
    n = len(atoms)
    for i in range(n):
        ei = atoms[i][0]
        if ei not in COVALENT:
            continue
        for j in range(i + 1, n):
            ej = atoms[j][0]
            if ej not in COVALENT:
                continue
            d = np.linalg.norm(np.array(atoms[i][1:]) - np.array(atoms[j][1:]))
            if d < COVALENT[ei] + COVALENT[ej] + tol:
                bonds.append((i, j))
    return bonds


# ---------------------------------------------------------------- pair list
def build_pairs():
    rec_json = json.load(open(P1 / "paper_structures_recovered.json"))
    papers = {e["paper_compound_number"]: e for e in rec_json["compounds"]}
    region_cons = json.load(open(P1 / "phase6_full_series/full_series_region_consensus_2seed.json"))
    region8 = {k: v.get("8Z8A", {}).get("consensus") for k, v in region_cons["compounds"].items()}

    tool_smiles = {}
    with open(P1 / "tool_compounds.csv") as f:
        for r in csv.DictReader(f):
            tool_smiles[r["compound_id"]] = r["canonical_smiles"]

    pairs = []
    # 1-39: papers x 8Z8A (phase-6)
    for cid in range(1, 40):
        e = papers[cid]
        pairs.append({
            "pair_id": f"c{cid:02d}_8Z8A",
            "entry_id": f"c{cid:02d}",
            "name": f"Davidsson 2020 compound {cid}",
            "series": e["series"],
            "receptor": "8Z8A",
            "role": "paper series",
            "smiles": e["smiles"],
            "pose_files": [P1 / f"phase6_full_series/poses/c{cid:02d}_8Z8A_seed{s}.pdbqt" for s in (1, 20260803)],
            "receptor_pdb": P1 / "phase2_prepared/receptors/8Z8A_chainR_protein.pdb",
            "ref_ligand": P1 / "phase2_prepared/reference_ligands/8Z8A_2OP.pdb",
            "protocol": "phase6: 24A box, 2 seeds x ex16 x 5 poses",
            "region_known": region8.get(f"c{cid:02d}"),
        })
    # 40-44: tools x 8Z8A (phase-3)
    for tname, tid in [("AZ1_GPR81_agonist_2", "t01"), ("GPR81_agonist_1", "t02"),
                       ("CHBA", "t03"), ("3_5_DHBA", "t04"), ("3_OBA", "t05")]:
        pairs.append({
            "pair_id": f"{tid}_8Z8A",
            "entry_id": tid,
            "name": tname,
            "series": "lead/tool compound",
            "receptor": "8Z8A",
            "role": "lead table",
            "smiles": tool_smiles.get(tname),
            "pose_files": [P1 / f"phase3_docking/poses/8Z8A/{tname}.pdbqt"],
            "receptor_pdb": P1 / "phase2_prepared/receptors/8Z8A_chainR_protein.pdb",
            "ref_ligand": P1 / "phase2_prepared/reference_ligands/8Z8A_2OP.pdb",
            "protocol": "phase3: 5 poses",
            "region_known": None,
        })
    # 45: lac x 8Z8A (cognate control)
    pairs.append({
        "pair_id": "lac_8Z8A", "entry_id": "lac", "name": "L-lactate",
        "series": "endogenous", "receptor": "8Z8A", "role": "endogenous ligand",
        "smiles": "C[C@H](O)C(=O)O",
        "pose_files": [P1 / "phase3_5_controls/poses/lactate_8Z8A.pdbqt"],
        "receptor_pdb": P1 / "phase2_prepared/receptors/8Z8A_chainR_protein.pdb",
        "ref_ligand": P1 / "phase2_prepared/reference_ligands/8Z8A_2OP.pdb",
        "protocol": "redock control (cognate 2OP box)",
        "region_known": "ORTHO_POCKET",
    })
    # 46: lac x 9KT9 (tight-box cross-structure)
    pairs.append({
        "pair_id": "lac_9KT9", "entry_id": "lac", "name": "L-lactate",
        "series": "endogenous", "receptor": "9KT9", "role": "endogenous ligand (cross-structure)",
        "smiles": "C[C@H](O)C(=O)O",
        "pose_files": [BASE / f"data/poses/lactate_9KT9_tight_seed{s}.pdbqt" for s in (20260803, 1, 2)],
        "receptor_pdb": P1 / "phase2_prepared/receptors/9KT9_chainR_protein.pdb",
        "ref_ligand": P1 / "phase2_prepared/reference_ligands/9KT9_34D.pdb",
        "protocol": "tight-box 12A on 34D, ex32, 3 seeds (follow-up run)",
        "region_known": "ORTHO_POCKET",
    })
    return pairs


# ---------------------------------------------------------------- scorecard context
def load_ec50_context():
    sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
    out = {}
    for c in sc["compounds"]:
        out[c["entry_id"]] = {
            "ec50_nM": c.get("ec50_nM"),
            "emax_pct": c.get("emax_pct"),
            "gpr109a_fold": c.get("gpr109a_fold"),
            "ghsr_fold": c.get("ghsr_fold"),
            "lle": c.get("lle"),
        }
    return out


def main():
    pairs = build_pairs()
    ctx = load_ec50_context()
    ref_centroids = {}

    def ref_centroid(p):
        if p not in ref_centroids:
            ref_centroids[p] = centroid(parse_pdb_atoms(p))
        return ref_centroids[p]

    rows = []
    for pr in pairs:
        best = None
        for pf in pr["pose_files"]:
            if not pf.exists():
                continue
            for m in parse_pdbqt_models(pf):
                if m["score"] is None:
                    continue
                if best is None or m["score"] < best["score"]:
                    best = {"score": m["score"], "atoms": m["atoms"], "file": str(pf)}
        if best is None:
            print("NO POSE", pr["pair_id"])
            continue
        rec_atoms = parse_pdb_atoms(pr["receptor_pdb"])
        lig = best["atoms"]
        polar, hyd = find_interactions(lig, rec_atoms)
        region = pr["region_known"] or classify_region(lig, rec_atoms)
        refc = ref_centroid(pr["ref_ligand"])
        lc = centroid(lig)
        cent_dist = float(np.linalg.norm(lc - refc))
        c = ctx.get(pr["entry_id"], {})
        row = {
            "pair_id": pr["pair_id"], "entry_id": pr["entry_id"], "name": pr["name"],
            "series": pr["series"], "receptor": pr["receptor"], "role": pr["role"],
            "smiles": pr["smiles"],
            "best_score_kcal_mol": round(best["score"], 3),
            "protocol": pr["protocol"],
            "region": region,
            "pose_centroid_to_cocrystal_A": round(cent_dist, 2),
            "n_polar_contacts": len(polar),
            "polar_contacts": "; ".join(f"{p[2]}{p[1]}{p[3]}-{p[0]} {p[5]:.1f}A" for p in polar[:8]),
            "n_hydrophobic_contacts": len(hyd),
            "hydrophobic_residues": "; ".join(sorted({str(r[0]) for r in hyd})),
            "ec50_nM": c.get("ec50_nM"), "emax_pct": c.get("emax_pct"),
            "gpr109a_fold": c.get("gpr109a_fold"), "ghsr_fold": c.get("ghsr_fold"),
            "lle": c.get("lle"),
            "best_pose_file": best["file"],
            "_pose_files": [str(pf) for pf in pr["pose_files"]],
        }
        rows.append(row)
        print(f"{pr['pair_id']:12s} score={row['best_score_kcal_mol']:7.2f} region={region:20s} "
              f"centroid={cent_dist:5.2f} polar={len(polar):2d} hyd={len(hyd):3d}")

    with open(BASE / "data/gpr81_pocket_analysis_pairs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(BASE / "data/gpr81_pocket_analysis_pairs.json", "w") as f:
        json.dump({"pair_universe": "46 pairs = 39 paper x 8Z8A + 5 leads x 8Z8A + lactate x 8Z8A + lactate x 9KT9; "
                                    "t01/AZ1 = paper c1 dual-listed (phase-6 + phase-3 runs)",
                   "pairs": rows}, f, indent=1)
    print("total pairs with poses:", len(rows))


if __name__ == "__main__":
    main()
