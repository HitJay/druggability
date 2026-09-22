#!/usr/bin/env python3
"""
Generate dedicated 3D pocket & domain visualization figures for the slide deck:
1. fig_slide_lactate_domain.png   (Lactate @ Orthosteric TM2/3/7 + ECL2)
2. fig_slide_az1_domain.png       (AZ1 @ Orthosteric TM2/3/7 + ECL2)
3. fig_slide_agonist1_domain.png  (Agonist 1 @ Allosteric TM5/6 + ECL2)
4. fig_slide_three_molecules_comparison.png (Side-by-side 3-pocket domain comparison)

Optimized for ZERO edge truncation, ZERO text overlap, and generous margins.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import MolDraw2DCairo
from PIL import Image

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
OUT_DIR = os.path.join(WORK_DIR, "slide_figures")
os.makedirs(OUT_DIR, exist_ok=True)

RECEPTOR_PDB = os.path.join(WORK_DIR, "8Z8A_HCAR1_clean.pdb")

COVALENT = {"C": 0.76, "N": 0.71, "O": 0.66, "S": 1.05, "P": 1.07, "Cl": 0.99, "H": 0.31}
ELEM_COLOR = {
    "C": "#94A3B8", "N": "#2563EB", "O": "#DC2626", "S": "#D97706",
    "Cl": "#0D9488", "H": "#E2E8F0"
}
LIG_COLORS = {
    "Lactate": "#16A34A",
    "AZ1": "#2563EB",
    "Agonist1": "#D97706"
}

DOMAIN_MAP = {
    range(22, 43): "TM1",
    range(50, 71): "TM2",
    range(71, 90): "ECL1",
    range(90, 111): "TM3",
    range(131, 152): "TM4",
    range(152, 183): "ECL2",
    range(183, 204): "TM5",
    range(221, 242): "TM6",
    range(242, 262): "ECL3",
    range(262, 282): "TM7",
}

def get_domain(resi):
    for r, name in DOMAIN_MAP.items():
        if resi in r:
            return name
    return "Loop"

def parse_pdb_atoms(pdb_path):
    atoms = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                try:
                    name = line[12:16].strip()
                    resn = line[17:20].strip()
                    resi = int(line[22:26].strip())
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    el = line[76:78].strip() if len(line) >= 78 and line[76:78].strip() else name[0]
                    el = (el[0] + el[1:].lower()) if len(el) > 1 else el.upper()
                    if el != "H":
                        atoms.append({"name": name, "resn": resn, "resi": resi, "x": x, "y": y, "z": z, "el": el})
                except Exception:
                    pass
    return atoms

def parse_sdf_atoms(sdf_path):
    m = Chem.SDMolSupplier(sdf_path, removeHs=False)[0]
    conf = m.GetConformer()
    atoms = []
    for i, a in enumerate(m.GetAtoms()):
        el = a.GetSymbol()
        if el != "H":
            pos = conf.GetAtomPosition(i)
            atoms.append({"el": el, "x": pos.x, "y": pos.y, "z": pos.z})
    return atoms, m

def infer_bonds(atoms, tol=0.45):
    bonds = []
    n = len(atoms)
    for i in range(n):
        for j in range(i + 1, n):
            e1 = atoms[i]["el"]
            e2 = atoms[j]["el"]
            r1 = COVALENT.get(e1, 0.77)
            r2 = COVALENT.get(e2, 0.77)
            d = ((atoms[i]["x"] - atoms[j]["x"])**2 + (atoms[i]["y"] - atoms[j]["y"])**2 + (atoms[i]["z"] - atoms[j]["z"])**2)**0.5
            if d < r1 + r2 + tol:
                bonds.append((i, j))
    return bonds

def render_2d_png(mol, out_path, size=(380, 300)):
    AllChem.Compute2DCoords(mol)
    d2d = MolDraw2DCairo(size[0], size[1])
    d2d.drawOptions().padding = 0.08
    d2d.drawOptions().bondLineWidth = 2.0
    d2d.DrawMolecule(mol)
    d2d.FinishDrawing()
    with open(out_path, "wb") as f:
        f.write(d2d.GetDrawingText())

def render_single_molecule_slide_figure(mol_name, sdf_file, title, pocket_type, domain_info, key_residue_configs, out_png):
    rec_atoms = parse_pdb_atoms(RECEPTOR_PDB)
    lig_atoms, rd_mol = parse_sdf_atoms(os.path.join(WORK_DIR, sdf_file))

    # Extract pocket atoms within 5.0 A of ligand
    pocket = []
    for ra in rec_atoms:
        d_min = min(((ra["x"] - la["x"])**2 + (ra["y"] - la["y"])**2 + (ra["z"] - la["z"])**2)**0.5 for la in lig_atoms)
        if d_min < 5.0:
            pocket.append(ra)

    # PCA projection over pocket + ligand
    all_xyz = np.array([[a["x"], a["y"], a["z"]] for a in lig_atoms + pocket])
    cen = all_xyz.mean(axis=0)
    u, s, vt = np.linalg.svd(all_xyz - cen, full_matrices=False)
    proj = lambda x, y, z: (vt[0] @ (np.array([x, y, z]) - cen), vt[1] @ (np.array([x, y, z]) - cen))

    fig = plt.figure(figsize=(10.5, 5.4), dpi=250, facecolor="#FFFFFF")

    # Left: 2D structure with generous margin
    temp_2d = f"/tmp/{mol_name}_2d.png"
    render_2d_png(rd_mol, temp_2d)
    img_2d = Image.open(temp_2d)

    ax_left = fig.add_axes([0.04, 0.16, 0.28, 0.70], facecolor="#F8FAFC")
    ax_left.imshow(img_2d)
    ax_left.axis("off")
    ax_left.set_title(f"Chemical Structure\n{mol_name}", fontsize=10.5, fontweight="bold", color="#001965", pad=6)

    # Right: 3D Pocket Visualization (width 0.58, leaving 0.07 right margin)
    ax_right = fig.add_axes([0.35, 0.14, 0.58, 0.74], facecolor="#F8FAFC")
    ax_right.set_title(f"3D Pocket Engagement & Domain Contact: {pocket_type}", fontsize=11, fontweight="bold", color="#001965", pad=8)

    # Draw pocket bonds
    p_bonds = infer_bonds(pocket)
    p_coords = [proj(a["x"], a["y"], a["z"]) for a in pocket]
    for i, j in p_bonds:
        ax_right.plot([p_coords[i][0], p_coords[j][0]], [p_coords[i][1], p_coords[j][1]],
                      color="#94A3B8", lw=1.1, alpha=0.65, solid_capstyle="round", zorder=2)
    for idx, (px, py) in enumerate(p_coords):
        el = pocket[idx]["el"]
        c = ELEM_COLOR.get(el, "#94A3B8") if el != "C" else "#CBD5E1"
        ax_right.scatter([px], [py], s=14, c=c, edgecolors="none", zorder=3)

    # Draw ligand bonds
    l_bonds = infer_bonds(lig_atoms)
    l_coords = [proj(a["x"], a["y"], a["z"]) for a in lig_atoms]
    lig_c = LIG_COLORS.get(mol_name, "#16A34A")
    for i, j in l_bonds:
        ax_right.plot([l_coords[i][0], l_coords[j][0]], [l_coords[i][1], l_coords[j][1]],
                      color=lig_c, lw=3.0, solid_capstyle="round", zorder=5)
    for idx, (lx, ly) in enumerate(l_coords):
        el = lig_atoms[idx]["el"]
        c = lig_c if el == "C" else ELEM_COLOR.get(el, lig_c)
        ax_right.scatter([lx], [ly], s=38, c=c, edgecolors="#001965", lw=0.6, zorder=6)

    # Draw smart curated key residue labels (custom offset dx, dy per residue to prevent collision!)
    all_px = [p[0] for p in p_coords]
    all_py = [p[1] for p in p_coords]
    x_min, x_max = min(all_px), max(all_px)
    y_min, y_max = min(all_py), max(all_py)

    for cfg in key_residue_configs:
        r_num = cfg["resi"]
        label_text = cfg["label"]
        dx = cfg.get("dx", 0.3)
        dy = cfg.get("dy", 0.3)
        ha = cfg.get("ha", "left")
        va = cfg.get("va", "bottom")
        color = cfg.get("color", "#166534")
        bg_col = cfg.get("bg", "#DCFCE7")
        edge_col = cfg.get("edge", "#16A34A")

        matching = [a for a in pocket if a["resi"] == r_num and a["name"] in ["CA", "CG", "OE1", "NH1", "NE", "OH"]]
        if matching:
            ma = matching[0]
            mx, my = proj(ma["x"], ma["y"], ma["z"])
            
            # Guide line from atom to label
            lx_target = mx + dx
            ly_target = my + dy
            ax_right.plot([mx, lx_target], [my, ly_target], color=edge_col, lw=1.0, ls=":", zorder=7)
            
            ax_right.text(lx_target, ly_target, label_text, fontsize=7.2, fontweight="bold", color=color,
                          ha=ha, va=va, bbox=dict(boxstyle="round,pad=0.22", facecolor=bg_col, edgecolor=edge_col, lw=0.8), zorder=8)

    # Expand limits to guarantee no label clips
    ax_right.set_xlim(x_min - 2.8, x_max + 2.8)
    ax_right.set_ylim(y_min - 2.2, y_max + 2.2)
    ax_right.axis("off")

    # Bottom badge centered comfortably
    fig.text(0.5, 0.04, f"Domain Mapping: {domain_info}", ha="center", fontsize=9, fontweight="bold", color="#001965",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF", edgecolor="#BFDBFE", lw=0.9))

    plt.savefig(out_png, dpi=250)
    plt.close()
    print(f"Saved: {out_png}")

def render_three_panel_comparison():
    im_lac = Image.open(os.path.join(OUT_DIR, "fig_slide_lactate_domain.png"))
    im_az1 = Image.open(os.path.join(OUT_DIR, "fig_slide_az1_domain.png"))
    im_ag1 = Image.open(os.path.join(OUT_DIR, "fig_slide_agonist1_domain.png"))

    w, h = im_lac.size
    comp = Image.new("RGB", (w * 3, h), "#FFFFFF")
    comp.paste(im_lac, (0, 0))
    comp.paste(im_az1, (w, 0))
    comp.paste(im_ag1, (w * 2, 0))

    out_comp = os.path.join(OUT_DIR, "fig_slide_three_molecules_comparison.png")
    comp.save(out_comp, dpi=(250, 250))
    print(f"Saved 3-panel comparison figure: {out_comp}")

def main():
    # 1. Lactate in Orthosteric Domain
    render_single_molecule_slide_figure(
        "Lactate", "lactate_ortho_8Z8A.sdf",
        "L-Lactate in Orthosteric Core", "Orthosteric Pocket (Deep Core)",
        "TM2 (Arg71 anchor) · TM3 (Leu92) · TM7 (Tyr268) · Cap: ECL2 (Phe168/Ser167)",
        [
            {"resi": 71, "label": "Arg71 (TM2/3 Anchor)\n-3.62 kcal/mol", "dx": -1.2, "dy": 1.2, "ha": "right", "va": "bottom", "color": "#166534", "bg": "#DCFCE7", "edge": "#16A34A"},
            {"resi": 168, "label": "Phe168 (ECL2 Lid)", "dx": 1.1, "dy": 1.1, "ha": "left", "va": "bottom", "color": "#991B1B", "bg": "#FEE2E2", "edge": "#DC2626"},
            {"resi": 268, "label": "Tyr268 (TM7)", "dx": 1.1, "dy": -1.0, "ha": "left", "va": "top", "color": "#1E3A8A", "bg": "#DBEAFE", "edge": "#2563EB"}
        ],
        os.path.join(OUT_DIR, "fig_slide_lactate_domain.png")
    )

    # 2. AZ1 in Orthosteric Domain
    render_single_molecule_slide_figure(
        "AZ1", "az1_ortho_boltz.sdf",
        "AZ1 in Orthosteric Core", "Orthosteric Pocket (Boltz-2 Pose)",
        "TM2 (Arg71: -11.0 kcal/mol) · ECL2 (Phe168: -12.7 kcal/mol) · ECL2 (Ser167: -12.4 kcal/mol)",
        [
            {"resi": 71, "label": "Arg71 (TM2/3 Anchor)\n-11.03 kcal/mol (R71A: +10.2)", "dx": -1.4, "dy": 1.2, "ha": "right", "va": "bottom", "color": "#166534", "bg": "#DCFCE7", "edge": "#16A34A"},
            {"resi": 168, "label": "Phe168 (ECL2 Lid)\n-12.73 kcal/mol", "dx": 1.2, "dy": 1.2, "ha": "left", "va": "bottom", "color": "#991B1B", "bg": "#FEE2E2", "edge": "#DC2626"},
            {"resi": 167, "label": "Ser167 (ECL2)\n-12.37 kcal/mol", "dx": 1.2, "dy": -1.2, "ha": "left", "va": "top", "color": "#991B1B", "bg": "#FEE2E2", "edge": "#DC2626"}
        ],
        os.path.join(OUT_DIR, "fig_slide_az1_domain.png")
    )

    # 3. Agonist 1 in Allosteric Domain
    render_single_molecule_slide_figure(
        "Agonist1", "agonist1_allo_vina.sdf",
        "GPR81 Agonist 1 in Allosteric Crevice", "TM5–TM6 Allosteric Crevice (ago-PAM)",
        "TM5 (Glu153: -6.2 kcal/mol) · ECL2 (Met170: -11.8 kcal/mol) · TM5 (His155: -6.3 kcal/mol)",
        [
            {"resi": 153, "label": "Glu153 (TM5 Anchor)\n-6.21 kcal/mol (E153A: +6.6)", "dx": -1.3, "dy": 1.2, "ha": "right", "va": "bottom", "color": "#92400E", "bg": "#FEF3C7", "edge": "#D97706"},
            {"resi": 170, "label": "Met170 (ECL2 Cleft)\n-11.84 kcal/mol", "dx": 1.2, "dy": 1.1, "ha": "left", "va": "bottom", "color": "#1E3A8A", "bg": "#DBEAFE", "edge": "#2563EB"},
            {"resi": 155, "label": "His155 (TM5)\n-6.27 kcal/mol", "dx": -1.2, "dy": -1.1, "ha": "right", "va": "top", "color": "#92400E", "bg": "#FEF3C7", "edge": "#D97706"}
        ],
        os.path.join(OUT_DIR, "fig_slide_agonist1_domain.png")
    )

    render_three_panel_comparison()

if __name__ == "__main__":
    main()
