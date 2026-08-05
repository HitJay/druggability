#!/usr/bin/env python3
"""
GPR81 follow-up deliverable 2b: per-pair structural illustration figures.

For each of the 46 ligand-receptor pairs, render a single PNG containing:
  left  panel - 2D ligand structure (RDKit MolDraw2DCairo)
  right panel - 3D pocket interaction view (matplotlib stick renderer):
                 receptor pocket atoms within 5 A of the ligand as thin gray
                 sticks, ligand as thick colored sticks, polar-contact
                 candidates as dashed yellow lines with residue labels,
                 hydrophobic contacts counted but not drawn (avoid clutter).
  bottom strip - key binding parameters (score, region, centroid distance to
                 co-crystal ligand, n polar / n hydrophobic, EC50 context).

Orientation: PCA projection of the drawn atoms (deterministic, no manual
viewing angles). Bond connectivity: distance-based inference from covalent
radii (validated against PDBQT ROOT/BRANCH for ligands).

Outputs: figures/pocket_<pair_id>.png
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Draw import MolDraw2DCairo

BASE = Path(__file__).resolve().parent
P1 = BASE.parent
FIGDIR = BASE / "figures"
FIGDIR.mkdir(exist_ok=True)

COVALENT = {"C": 0.76, "N": 0.71, "O": 0.66, "S": 1.05, "P": 1.07,
            "F": 0.57, "Cl": 0.99, "Br": 1.14, "H": 0.31}
POCKET_CUTOFF = 5.0
POLAR_CUTOFF = 3.5
HYDROPHOBIC_CUTOFF = 4.0

ELEM_COLOR = {
    "C": "#A0A0A0",   # receptor carbon (gray)
    "N": "#3B78E0", "O": "#E04B4B", "S": "#E8B800",
    "P": "#C97A11", "F": "#58C458", "Cl": "#2BB8B8", "BR": "#8B3AB8",
    "H": "#FFFFFF",
}
LIG_C = "#1FAE4C"  # ligand carbon (green)

THREE_TO_ONE = {"ARG": "R", "TYR": "Y", "LEU": "L", "GLU": "E", "SER": "S",
                "PHE": "F", "HIS": "H", "ILE": "I", "MET": "M", "ASN": "N",
                "GLN": "Q", "TRP": "W", "ALA": "A", "CYS": "C", "VAL": "V",
                "THR": "T", "GLY": "G", "ASP": "D", "LYS": "K", "PRO": "P"}


# ---------------------------------------------------------------- parsers
def _ad_to_element(t: str) -> str:
    """Map an AutoDock PDBQT atom type to a chemical element.
    PDBQT column 78-79 holds AutoDock types, not elements:
    A=aromatic C, C=C, OA=acceptor O, NA=acceptor N, SA=S, HD=donor H..."""
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


def _norm_pdb_el(el: str) -> str:
    """Normalize a PDB element-column symbol (real elements, e.g. ' C', 'Cl')."""
    el = el.strip()
    return (el[0] + el[1:].lower()) if len(el) > 1 else el.upper()


def parse_pdbqt_models(path: Path) -> list[dict]:
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
    out = []
    for line in path.read_text().splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            el = line[76:78].strip()
            if not el:
                el = line[12:16].strip()
                el = el[0] if el and el[0].isalpha() else "C"
            el = _norm_pdb_el(el)
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
                el = _norm_pdb_el(el)
            except (ValueError, IndexError):
                continue
        if el == "H":
            continue
        out.append((resid, resname, atomname, el, x, y, z))
    return out


def infer_bonds(atoms, tol=0.45):
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


def find_interactions(lig_atoms, rec_atoms):
    polar, hyd = [], []
    for le, lx, ly, lz in lig_atoms:
        for ri, rn, an, re_, rx, ry, rz in rec_atoms:
            d = ((lx - rx) ** 2 + (ly - ry) ** 2 + (lz - rz) ** 2) ** 0.5
            if le in ("N", "O", "S") and re_ in ("N", "O") and d < POLAR_CUTOFF:
                polar.append((le, ri, rn, an, re_, round(d, 2)))
            elif le == "C" and re_ == "C" and d < HYDROPHOBIC_CUTOFF:
                hyd.append((ri, round(d, 2)))
    seen, uniq = {}, []
    for p in sorted(polar, key=lambda x: x[5]):
        key = (p[1], p[3])
        if key not in seen:
            seen[key] = True
            uniq.append(p)
    # hydrophobic: unique residues
    hyd_res = sorted({r[0] for r in hyd})
    return uniq, hyd_res


# ---------------------------------------------------------------- 2D
def render_2d(smiles: str, path: Path, label: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    AllChem.Compute2DCoords(mol)
    d2d = MolDraw2DCairo(520, 420)
    d2d.drawOptions().padding = 0.06
    d2d.drawOptions().bondLineWidth = 2
    d2d.DrawMolecule(mol)
    d2d.FinishDrawing()
    path.write_bytes(d2d.GetDrawingText())
    return True


# ---------------------------------------------------------------- 3D
def render_3d(ax, lig_atoms, rec_atoms, polar, hyd_res):
    # pocket selection (receptor atoms within POCKET_CUTOFF of any ligand atom)
    pocket = []
    for ri, rn, an, re_, rx, ry, rz in rec_atoms:
        rc = np.array((rx, ry, rz))
        if any(np.linalg.norm(rc - np.array(la[1:])) < POCKET_CUTOFF for la in lig_atoms):
            pocket.append((ri, rn, an, re_, rx, ry, rz))
    if not pocket:
        pocket = rec_atoms[:80]
    # normalize receptor atoms to (elem, x, y, z) for bond inference / drawing
    pdraw = [(re_, rx, ry, rz) for (ri, rn, an, re_, rx, ry, rz) in pocket]

    # PCA orientation over all drawn atoms
    all_xyz = np.array([a[-3:] for a in lig_atoms] + [a[-3:] for a in pdraw])
    cen = all_xyz.mean(axis=0)
    u, s, vt = np.linalg.svd(all_xyz - cen, full_matrices=False)
    proj = lambda a: (vt[0] @ (a - cen), vt[1] @ (a - cen))

    def draw_sticks(atoms, bonds, color_fn, lw, dot_s, alpha=1.0):
        coords = [proj(np.array(a[-3:])) for a in atoms]
        for i, j in bonds:
            (x1, y1), (x2, y2) = coords[i], coords[j]
            ax.plot([x1, x2], [y1, y2], color=color_fn(atoms[i], atoms[j]),
                    lw=lw, alpha=alpha, solid_capstyle="round", zorder=3)
        for idx, (x, y) in enumerate(coords):
            el = atoms[idx][0]
            ax.scatter([x], [y], s=dot_s, c=ELEM_COLOR.get(el, "#888888"),
                       edgecolors="none", zorder=4)

    def lig_color(ai, aj):
        e = ai[0]
        return LIG_C if e == "C" else ELEM_COLOR.get(e, "#888888")

    def rec_color(ai, aj):
        e = ai[0]
        return ELEM_COLOR.get(e, "#888888")

    # receptor sticks first (thin)
    pbonds = infer_bonds(pdraw)
    draw_sticks(pdraw, pbonds, rec_color, lw=1.3, dot_s=4, alpha=0.9)
    # polar contacts (dashed)
    for le, ri, rn, an, re_, d in polar:
        rxyz = min((ra for ra in rec_atoms if ra[0] == ri and ra[1] == rn and ra[2] == an),
                   key=lambda ra: np.linalg.norm(np.array(ra[-3:]) - np.array(lig_atoms[0][-3:])), default=None)
        if rxyz is None:
            continue
        rc = np.array(rxyz[-3:])
        lxyz = min((a for a in lig_atoms if a[0] == le),
                   key=lambda a: np.linalg.norm(np.array(a[-3:]) - rc), default=None)
        if lxyz is None:
            continue
        (lx, ly) = proj(np.array(lxyz[-3:])); (rx, ry) = proj(rc)
        ax.plot([lx, rx], [ly, ry], color="#F5C518", lw=1.6, ls=(0, (4, 2)),
                alpha=0.95, zorder=5)
        label = f"{THREE_TO_ONE.get(rn, rn)}{ri}"
        ax.text(rx, ry, label, fontsize=7.5, color="#B8860B", zorder=6,
                ha="center", va="bottom")
    # ligand sticks on top
    lbonds = infer_bonds(lig_atoms)
    draw_sticks(lig_atoms, lbonds, lig_color, lw=3.2, dot_s=10)

    ax.set_axis_off()
    ax.set_aspect("equal")
    # equalize axis limits; generous pad so edge labels/sticks are never clipped
    xs = [proj(np.array(a[-3:]))[0] for a in lig_atoms + pdraw]
    ys = [proj(np.array(a[-3:]))[1] for a in lig_atoms + pdraw]
    pad = 3.0
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


# ---------------------------------------------------------------- main
def main():
    data = json.load(open(BASE / "data/gpr81_pocket_analysis_pairs.json"))
    pairs = data["pairs"]

    for pr in pairs:
        pair_id = pr["pair_id"]
        # reload best pose from file
        best = None
        for pf in [Path(f) for f in pr.get("_pose_files", [])]:
            if pf.exists():
                for m in parse_pdbqt_models(pf):
                    if m["score"] is None:
                        continue
                    if best is None or m["score"] < best["score"]:
                        best = {"score": m["score"], "atoms": m["atoms"]}
        if best is None:
            print("skip (no pose):", pair_id)
            continue
        # locate pose files dynamically (same logic as build_pocket_analysis)
        rec_atoms = parse_pdb_atoms(P1 / f"phase2_prepared/receptors/{pr['receptor']}_chainR_protein.pdb")

        fig = plt.figure(figsize=(12.5, 6.2), dpi=115)
        gs = fig.add_gridspec(1, 2, width_ratios=[0.42, 0.58], wspace=0.02)
        ax2d = fig.add_subplot(gs[0])
        ax3d = fig.add_subplot(gs[1])  # PCA-projected pocket view (2D axes)

        # 2D panel
        mol = Chem.MolFromSmiles(pr["smiles"])
        if mol is not None:
            AllChem.Compute2DCoords(mol)
            d2d = MolDraw2DCairo(560, 440)
            d2d.drawOptions().padding = 0.05
            d2d.drawOptions().bondLineWidth = 2
            d2d.DrawMolecule(mol)
            d2d.FinishDrawing()
            import io
            from PIL import Image
            img = Image.open(io.BytesIO(d2d.GetDrawingText()))
            ax2d.imshow(np.asarray(img))
        ax2d.set_axis_off()
        ax2d.set_title(f"{pr['entry_id']} · {pr['name']}", fontsize=11, fontweight="bold", pad=6)

        # 3D panel
        polar, hyd_res = find_interactions(best["atoms"], rec_atoms)
        render_3d(ax3d, best["atoms"], rec_atoms, polar, hyd_res)
        ax3d.set_title(f"{pr['receptor']} pocket · best {pr['best_score_kcal_mol']:.2f} kcal/mol",
                       fontsize=11, fontweight="bold", pad=4)

        # caption strip
        ec = f"EC50 {pr['ec50_nM']:g} nM" if pr.get("ec50_nM") is not None else "no EC50 assay"
        if pr.get("emax_pct") is not None:
            ec += f" (Emax {pr['emax_pct']}%)"
        cap = (f"region {pr['region']}  ·  centroid vs co-crystal {pr['pose_centroid_to_cocrystal_A']} Å"
               f"  ·  {pr['n_polar_contacts']} polar / {pr['n_hydrophobic_contacts']} hydrophobic contacts"
               f"  ·  {ec}  ·  {pr['protocol']}")
        fig.text(0.02, 0.015, cap, fontsize=8.2, color="#333333",
                 bbox=dict(boxstyle="round,pad=0.35", fc="#F4F6F7", ec="#CCCCCC"))

        out = FIGDIR / f"pocket_{pair_id}.png"
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print("wrote", out.name)

    print("figures done:", len(list(FIGDIR.glob("pocket_*.png"))))


if __name__ == "__main__":
    main()
