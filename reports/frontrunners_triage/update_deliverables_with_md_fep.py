#!/usr/bin/env python3
"""Add Sheet 5 (5_TemplateFree_Dock_MD_FEP) to PPI_Frontrunners_39Pairs_7Criteria_Triage.xlsx,
generate a 2-panel high-DPI figure, update the Top-5 Dossier, and write the final email reply to ZHCO & JXDL."""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT_DIR = Path("/das/user/QYJI/druggability/reports/frontrunners_triage")
SHARED_DIR = Path("/TDE_TV/shared_folder/QYJI/druggability/BnG4K")
MD_FEP_DIR = OUT_DIR / "md_fep_study"
all_md_fep = json.loads((MD_FEP_DIR / "all_10complexes_md_fep_summary.json").read_text())

xlsx_path = OUT_DIR / "PPI_Frontrunners_39Pairs_7Criteria_Triage.xlsx"
wb = openpyxl.load_workbook(xlsx_path)
if "5_TemplateFree_Dock_MD_FEP" in wb.sheetnames:
    del wb["5_TemplateFree_Dock_MD_FEP"]

ws5 = wb.create_sheet("5_TemplateFree_Dock_MD_FEP")
ws5.views.sheetView[0].showGridLines = True

NAVY_HEX = "001965"
TEAL_HEX = "00857C"
RED_HEX = "D9383A"
ICE_HEX = "E8EEF7"
GREEN_HEX = "EBF7F5"

font_title = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
font_sec = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
font_hdr = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
font_cell = Font(name="Calibri", size=9.5, bold=False, color="1A1A2E")
font_bold = Font(name="Calibri", size=9.5, bold=True, color="001965")
font_green = Font(name="Calibri", size=9.5, bold=True, color="00857C")
font_red = Font(name="Calibri", size=9.5, bold=True, color="D9383A")

fill_navy = PatternFill(start_color=NAVY_HEX, end_color=NAVY_HEX, fill_type="solid")
fill_teal = PatternFill(start_color=TEAL_HEX, end_color=TEAL_HEX, fill_type="solid")
fill_ice = PatternFill(start_color=ICE_HEX, end_color=ICE_HEX, fill_type="solid")
fill_green = PatternFill(start_color=GREEN_HEX, end_color=GREEN_HEX, fill_type="solid")
fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

thin_border = Border(
    left=Side(style="thin", color="D0D7E5"),
    right=Side(style="thin", color="D0D7E5"),
    top=Side(style="thin", color="D0D7E5"),
    bottom=Side(style="thin", color="D0D7E5"),
)

ws5.merge_cells("A1:N1")
ws5["A1"] = "Template-Free Prioritized PPI Frontrunners (10 Complexes Across Top 5 Axes) — Boltz-2 + omicMSA Docking, Explicit-Solvent NPT MD, MM/GBSA & 8-Lambda Alchemical TI FEP Audit"
ws5["A1"].font = font_title
ws5["A1"].fill = fill_navy
ws5["A1"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
ws5.row_dimensions[1].height = 28

# Part A: 10-Complex Summary Table
ws5.merge_cells("A2:N2")
ws5["A2"] = "Part A: 3D Complex Co-Folding/Docking (Boltz-2 + omicMSA) & Explicit-Solvent NPT MD + Ensemble GBn2 MM/GBSA Summary (Amber14SB + TIP3P, 0.15 M NaCl, 310 K, Precision=double)"
ws5["A2"].font = font_sec
ws5["A2"].fill = fill_teal
ws5["A2"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
ws5.row_dimensions[2].height = 22

part_a_headers = [
    ("Complex ID", 18), ("Campaign Axis", 24), ("PPI Pair", 16),
    ("Chain A Construct", 22), ("Chain B Construct", 22),
    ("Boltz Conf", 11), ("Boltz pTM", 11), ("Boltz ipTM", 11), ("Complex pLDDT", 13), ("<=5A Contacts", 14),
    ("MD Partner RMSD (A)", 18), ("<dG_GBn2> (kcal/mol)", 22), ("<E_vdW> (kcal/mol)", 18),
    ("Key Validated FEP Hotspots (ddG_screened, kcal/mol)", 65)
]
ws5.row_dimensions[3].height = 24
for ci, (h_text, w) in enumerate(part_a_headers, 1):
    c = ws5.cell(row=3, column=ci, value=h_text)
    c.font = font_hdr
    c.fill = fill_navy
    c.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
    c.border = thin_border
    ws5.column_dimensions[get_column_letter(ci)].width = w

for ri, d in enumerate(all_md_fep, 4):
    ws5.row_dimensions[ri].height = 36
    cA, cB = d["chainA"], d["chainB"]
    bc = d["boltz_confidence"]
    md = d["explicit_md"]
    # Format top positive FEP hotspots with d_min <= 5.0 A
    hot_fep = [
        f"{fp['mutation_label']} ({fp['ddG_screened_kcal_mol']:+.2f} kcal/mol, d={fp['d_min_partner_A']:.1f}A)"
        for fp in sorted(d["fep_hotspot_scan"], key=lambda x: -x["ddG_screened_kcal_mol"])
        if fp["ddG_screened_kcal_mol"] >= 0.8 and fp["d_min_partner_A"] <= 5.0
    ]
    vals = [
        d["id"], d["axis"], d["pair_label"],
        f"{cA['gene']} ({cA['start']}-{cA['end']})",
        f"{cB['gene']} ({cB['start']}-{cB['end']})",
        bc["confidence_score"], bc["ptm"], bc["iptm"], bc["complex_plddt"], bc["n_interchain_contacts_5A"],
        f"{md['mean_partner_rmsd_A']:.2f} (final {md['final_partner_rmsd_A']:.2f})",
        f"{md['mean_delta_g_gbn2_kcal']:.1f} +/- {md['std_delta_g_gbn2_kcal']:.1f}",
        f"{md['mean_vdw_ie_kcal']:.1f}",
        "; ".join(hot_fep[:5]),
    ]
    for ci, v in enumerate(vals, 1):
        cell = ws5.cell(row=ri, column=ci, value=v)
        cell.border = thin_border
        cell.fill = fill_green if ri % 2 == 0 else fill_white
        cell.font = font_bold if ci in (1, 3, 12) else font_cell
        cell.alignment = Alignment(vertical="center", horizontal="center" if ci in range(6, 14) else "left", wrap_text=True)

# Part B: Full 100-Row 8-Lambda Alchemical TI FEP Mutational Hotspot Scan Table
start_b = 16
ws5.merge_cells(f"A{start_b}:N{start_b}")
ws5[f"A{start_b}"] = "Part B: 8-Lambda Alchemical TI FEP Mutational Hotspot Scan Across All 10 Template-Free Complexes (100 Mutations Audited, Precision=double)"
ws5[f"A{start_b}"].font = font_sec
ws5[f"A{start_b}"].fill = fill_teal
ws5[f"A{start_b}"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
ws5.row_dimensions[start_b].height = 22

part_b_headers = [
    "Complex ID", "PPI Pair", "Chain", "Gene", "Canonical Pos", "WT Residue",
    "Alchemical Mutation", "d_min to Partner (A)", "ddG_screened (kcal/mol)", "ddG_raw (kcal/mol)",
    "ddG_screened (kJ/mol)", "Hotspot Class", "8-Lambda Window Profile (-dU/dlam, kJ/mol)", "Variant / Mutagen / Anchor Annotation"
]
hdr_row_b = start_b + 1
ws5.row_dimensions[hdr_row_b].height = 24
for ci, h_text in enumerate(part_b_headers, 1):
    c = ws5.cell(row=hdr_row_b, column=ci, value=h_text)
    c.font = font_hdr
    c.fill = fill_navy
    c.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
    c.border = thin_border

curr_r = hdr_row_b + 1
for d in all_md_fep:
    for fp in d["fep_hotspot_scan"]:
        ws5.row_dimensions[curr_r].height = 24
        ddg_s = fp["ddG_screened_kcal_mol"]
        d_min = fp["d_min_partner_A"]
        if ddg_s >= 3.0 and d_min <= 5.0:
            h_class = "CRITICAL HOTSPOT (ddG >= +3.0 kcal/mol)"
        elif ddg_s >= 1.0 and d_min <= 5.0:
            h_class = "MODERATE HOTSPOT (+1.0 to +3.0 kcal/mol)"
        elif d_min > 6.0:
            h_class = "DISTAL / ALLOSTERIC SITE (d_min > 6 A)"
        else:
            h_class = "NEUTRAL / PERIPHERAL RIM"
        win_str = ", ".join([f"{w['lambda']:.2f}:{w['minus_dUdlam_screened_kJmol']:+.1f}" for w in fp["windows"]])
        vals = [
            d["id"], d["pair_label"], fp["chain"], fp["gene"], fp["res_seq"], fp["res_name"],
            fp["mutation_label"], d_min, ddg_s, fp["ddG_raw_kcal_mol"],
            fp["ddG_screened_kJ_mol"], h_class, win_str, fp["description"]
        ]
        for ci, v in enumerate(vals, 1):
            cell = ws5.cell(row=curr_r, column=ci, value=v)
            cell.border = thin_border
            cell.fill = fill_white if curr_r % 2 == 1 else fill_ice
            if ci in (7, 9):
                cell.font = font_red if (ddg_s >= 3.0 and d_min <= 5.0) else (font_green if ddg_s >= 1.0 and d_min <= 5.0 else font_bold)
            else:
                cell.font = font_cell
            cell.alignment = Alignment(vertical="center", horizontal="center" if ci in (3, 4, 5, 6, 8, 9, 10, 11) else "left", wrap_text=True)
        curr_r += 1

wb.save(xlsx_path)
print("Updated Excel workbook with Sheet 5 (5_TemplateFree_Dock_MD_FEP):", xlsx_path)

# ==============================================================================
# Generate 2-Panel High-DPI Summary Figure for Template-Free MD + FEP
# ==============================================================================
NAVY, TEAL, RED, AMBER, GREY = "#001965", "#00857C", "#D9383A", "#B7791F", "#5A6070"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.6), dpi=300)
fig.patch.set_facecolor("#FFFFFF")

# Panel A: 10 Template-Free Frontrunner Complexes — Explicit-Solvent MD <dG_GBn2> & Backbone Stability
labels_a = [
    f"{d['pair_label']}\n(RMSD={d['explicit_md']['mean_partner_rmsd_A']:.2f}A, ipTM={d['boltz_confidence']['iptm']:.2f})"
    for d in all_md_fep
]
dg_vals = [abs(d["explicit_md"]["mean_delta_g_gbn2_kcal"]) for d in all_md_fep]
y_a = np.arange(len(labels_a))[::-1]
colors_a = [TEAL if d["boltz_confidence"]["iptm"] >= 0.25 else NAVY for d in all_md_fep]
bars1 = ax1.barh(y_a, dg_vals, height=0.62, color=colors_a, edgecolor="#1A1A2E", linewidth=0.6)
ax1.set_yticks(y_a)
ax1.set_yticklabels(labels_a, fontsize=8.0, fontweight="bold", color="#1A1A2E")
ax1.set_xlabel("Explicit-Solvent Ensemble |-dG_GBn2| (kcal/mol)", fontsize=8.8, fontweight="bold", color="#1A1A2E")
ax1.set_title("A. 10 Template-Free Frontrunners: MD Stability & MM/GBSA", fontsize=9.5, fontweight="bold", color=NAVY, pad=8)
ax1.set_xlim(0, 620)
ax1.grid(axis="x", linestyle="--", alpha=0.35)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
for bar, d in zip(bars1, all_md_fep):
    dg = d["explicit_md"]["mean_delta_g_gbn2_kcal"]
    w = bar.get_width()
    ax1.text(w + 8, bar.get_y() + bar.get_height()/2, f"{dg:.1f} kcal/mol",
             va="center", ha="left", fontsize=7.8, fontweight="bold", color="#1A1A2E")

# Panel B: Key Validated Interface SAVs & Experimental Mutagens — 8-Lambda Alchemical TI FEP ddG (kcal/mol)
fep_highlights = [
    ("FBXW11 R363W (SAV)", 19.28, RED),
    ("FBXW11 R447Q (SAV)", 15.47, RED),
    ("PDE3B R12A (Mutagen)", 11.01, TEAL),
    ("PDE3B K9A (Mutagen)", 10.14, TEAL),
    ("LGR4 R156 (Core Anchor)", 10.08, NAVY),
    ("GRB14 Q363 (BPS Contact)", 6.98, NAVY),
    ("FNIP1 D253 (BTRC Degron)", 6.63, TEAL),
    ("PRMT6 E244 (STARD10 Core)", 6.40, NAVY),
    ("PDE3B R6A (Mutagen)", 5.65, TEAL),
    ("BTRC R510A (Mutagen)", 5.49, TEAL),
    ("GRB14 Q348A (Mutagen)", 4.16, TEAL),
    ("PRKAG1 P134 (FNIP1 Core)", 4.08, NAVY),
    ("FNIP1 K495 (PRKAG1 Core)", 3.71, NAVY),
    ("BTRC Y307A (Mutagen)", 3.26, TEAL),
]
fep_names = [x[0] for x in fep_highlights]
fep_ddg = [x[1] for x in fep_highlights]
fep_cols = [x[2] for x in fep_highlights]
y_b = np.arange(len(fep_names))[::-1]
bars2 = ax2.barh(y_b, fep_ddg, height=0.64, color=fep_cols, edgecolor="#1A1A2E", linewidth=0.6)
ax2.axvline(2.0, color=RED, linestyle="--", linewidth=0.9, alpha=0.75)
ax2.set_yticks(y_b)
ax2.set_yticklabels(fep_names, fontsize=7.8, fontweight="bold", color="#1A1A2E")
ax2.set_xlabel("FEP Binding Free Energy ddG (kcal/mol)", fontsize=8.8, fontweight="bold", color="#1A1A2E")
ax2.set_title("B. Interface SAVs & Mutagens: FEP Hotspots", fontsize=9.5, fontweight="bold", color=NAVY, pad=8)
ax2.set_xlim(0, 23.0)
ax2.grid(axis="x", linestyle="--", alpha=0.35)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
for bar, v in zip(bars2, fep_ddg):
    ax2.text(v + 0.3, bar.get_y() + bar.get_height()/2, f"+{v:.2f}",
             va="center", ha="left", fontsize=7.8, fontweight="bold", color=RED if v >= 10 else "#1A1A2E")

fig.tight_layout(pad=1.2)
fig_path = OUT_DIR / "frontrunners_template_free_md_fep_2panel.png"
fig.savefig(fig_path, dpi=300, bbox_inches="tight", pad_inches=0.18)
print("Saved 2-panel MD+FEP figure:", fig_path)

# Sync updated workbook, figure, and PDBs to shared folder
if SHARED_DIR.exists():
    shutil.copyfile(xlsx_path, SHARED_DIR / xlsx_path.name)
    shutil.copyfile(fig_path, SHARED_DIR / fig_path.name)
    pdb_shared = SHARED_DIR / "02_TemplateFree_Docked_PDBs"
    pdb_shared.mkdir(parents=True, exist_ok=True)
    for pdb_f in sorted((MD_FEP_DIR / "pdbs").glob("*.pdb")):
        shutil.copyfile(pdb_f, pdb_shared / pdb_f.name)
    print("Synced updated Excel, figure, and 10 canonical PDBs to:", SHARED_DIR)
