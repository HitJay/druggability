#!/usr/bin/env python3
"""
Generate comprehensive 300 DPI publication figure with 4 panels:
Panel A: 2D Structural Domain Architecture & Ligand Binding Sites (Completely Zero-Overlap Redesign)
Panel B: Ternary Co-Occupancy & Steric Exclusion (Lactate+Agonist1 Co-binding vs AZ1 Clash)
Panel C: HCAR1 vs HCAR2 Subtype Selectivity & Anti-Flushing Mechanism (Triple-Basic Wall)
Panel D: Full 45-Compound Series Landscape (Ortho vs Allo vs Bitopic / Dualsteric)

Optimized for ZERO edge truncation, ZERO text overlap, and generous bounding box margins.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
OUT_PNG = os.path.join(WORK_DIR, "gpr81_binding_domains_visualization.png")

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#CBD5E0"
plt.rcParams["axes.linewidth"] = 0.8

# Fixed canvas size 16x12 at 300 DPI
fig = plt.figure(figsize=(16, 12), dpi=300, facecolor="#FFFFFF")
gs = GridSpec(2, 2, figure=fig, hspace=0.30, wspace=0.24, 
              left=0.065, right=0.935, top=0.92, bottom=0.07)

NN_NAVY = "#001965"
NN_TEAL = "#00857C"
NN_CORAL = "#D9383A"
NN_AMBER = "#D97706"
NN_PURPLE = "#7C3AED"
NN_BG = "#F8FAFC"

# ----------------------------------------------------------------------
# Panel A: 2D Domain Architecture & Ligand Sites (ZERO OVERLAP REDESIGN)
# ----------------------------------------------------------------------
ax_a = fig.add_subplot(gs[0, 0], facecolor=NN_BG)
ax_a.set_title("A. GPR81 Structural Domains & Dual Pocket Organization", 
               fontsize=12, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

# Bilayer span
ax_a.axhspan(2.6, 5.4, color="#E2E8F0", alpha=0.65, zorder=1)
ax_a.text(0.35, 4.0, "LIPID\nBILAYER\n(POPC)", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#64748B", zorder=2)

# Helices
tm_names = ["TM1", "TM2", "TM3", "TM4", "TM5", "TM6", "TM7"]
tm_x = [1.2, 2.3, 3.4, 4.6, 5.8, 6.9, 8.0]
tm_ranges = ["22-42", "50-70", "90-110", "131-151", "183-203", "221-241", "262-281"]

for x, name, rng in zip(tm_x, tm_names, tm_ranges):
    rect = patches.FancyBboxPatch((x-0.34, 2.6), 0.68, 2.8, boxstyle="round,pad=0.04",
                                  facecolor="#CBD5E1", edgecolor=NN_NAVY, linewidth=1.2, zorder=3)
    ax_a.add_patch(rect)
    ax_a.text(x, 4.25, name, ha="center", va="center", fontsize=9.0, fontweight="bold", color=NN_NAVY, zorder=4)
    ax_a.text(x, 3.40, f"({rng})", ha="center", va="center", fontsize=6.8, color="#334155", zorder=4)

# Key Anchor residue markers (positioned outside helix center to prevent text collision)
# Arg71 on TM2 (annotated to the left)
ax_a.scatter([2.3], [5.05], s=70, color="#16A34A", edgecolors=NN_NAVY, lw=1.1, zorder=6)
ax_a.text(1.78, 5.05, "Arg71", ha="right", va="center", fontsize=7.2, fontweight="bold", color="#15803D",
          bbox=dict(boxstyle="round,pad=0.18", facecolor="#DCFCE7", edgecolor="#16A34A", lw=0.7), zorder=7)

# Glu153 on TM4/5 (annotated to the right)
ax_a.scatter([5.8], [5.05], s=70, color=NN_AMBER, edgecolors=NN_NAVY, lw=1.1, zorder=6)
ax_a.text(6.32, 5.05, "Glu153", ha="left", va="center", fontsize=7.2, fontweight="bold", color="#B45309",
          bbox=dict(boxstyle="round,pad=0.18", facecolor="#FEF3C7", edgecolor="#D97706", lw=0.7), zorder=7)

# Intracellular motifs
ax_a.scatter([3.4], [2.85], s=45, color=NN_PURPLE, edgecolors=NN_NAVY, lw=0.9, zorder=6)
ax_a.text(3.4, 2.98, "DRY", ha="center", va="bottom", fontsize=6.5, fontweight="bold", color="#6D28D9", zorder=7)

ax_a.scatter([8.0], [2.85], s=45, color=NN_PURPLE, edgecolors=NN_NAVY, lw=0.9, zorder=6)
ax_a.text(8.0, 2.98, "NPxxY", ha="center", va="bottom", fontsize=6.5, fontweight="bold", color="#6D28D9", zorder=7)

# Loops
# ECL1 (TM2 - TM3)
ax_a.add_patch(patches.Arc((2.85, 5.4), 1.1, 0.7, theta1=0, theta2=180, color=NN_NAVY, lw=1.5, zorder=3))
ax_a.text(2.85, 5.82, "ECL1", ha="center", fontsize=7.0, color="#475569", zorder=4)

# ECL2 (TM4 - TM5)
ax_a.add_patch(patches.Arc((5.2, 5.4), 1.2, 1.2, theta1=0, theta2=180, color=NN_CORAL, lw=2.0, ls="--", zorder=3))
ax_a.text(5.2, 6.08, "ECL2 Lid (Phe168/Ser167)", ha="center", fontsize=7.5, fontweight="bold", color=NN_CORAL, zorder=4)

# ECL3 (TM6 - TM7)
ax_a.add_patch(patches.Arc((7.45, 5.4), 1.1, 0.7, theta1=0, theta2=180, color=NN_NAVY, lw=1.5, zorder=3))
ax_a.text(7.45, 5.82, "ECL3", ha="center", fontsize=7.0, color="#475569", zorder=4)

# ICLs
ax_a.add_patch(patches.Arc((1.75, 2.6), 1.1, 0.6, theta1=180, theta2=360, color=NN_NAVY, lw=1.5, zorder=3))
ax_a.add_patch(patches.Arc((4.0, 2.6), 1.2, 0.6, theta1=180, theta2=360, color=NN_NAVY, lw=1.5, zorder=3))
ax_a.add_patch(patches.Arc((6.35, 2.6), 1.1, 0.7, theta1=180, theta2=360, color=NN_PURPLE, lw=2.0, zorder=3))
ax_a.text(6.35, 2.12, "ICL3 (Gi coupling)", ha="center", fontsize=7.0, fontweight="bold", color="#6D28D9", zorder=4)

# Pockets Cards in Extracellular space (cleanly separated at top with generous line gaps)
# Orthosteric Box (Top-Left)
box_ortho = patches.FancyBboxPatch((0.80, 6.20), 3.05, 1.75, boxstyle="round,pad=0.08",
                                   facecolor="#DCFCE7", edgecolor="#16A34A", lw=1.3, zorder=5)
ax_a.add_patch(box_ortho)
ax_a.text(2.32, 7.82, "ORTHOSTERIC CORE", ha="center", va="top", fontsize=8.6, fontweight="bold", color="#15803D", zorder=6)
ax_a.text(2.32, 7.46, "Lactate (Endogenous) · AZ1 (Ortho)", ha="center", va="top", fontsize=7.2, fontweight="bold", color="#166534", zorder=6)
ax_a.text(2.32, 7.10, "• TM2, TM3, TM7 Deep Cavity\n• Anchor: Arg71 Salt-Bridge\n• Covered by ECL2 Active Lid", 
          ha="center", va="top", linespacing=1.35, fontsize=6.6, color="#14532D", zorder=6)
# Guide arrow pointing into pocket mouth
ax_a.annotate("", xy=(2.7, 5.5), xytext=(2.32, 6.20),
              arrowprops=dict(arrowstyle="->", color="#16A34A", lw=1.4, mutation_scale=9), zorder=6)

# Allosteric Box (Top-Right)
box_allo = patches.FancyBboxPatch((5.35, 6.20), 3.65, 1.75, boxstyle="round,pad=0.08",
                                  facecolor="#FEF3C7", edgecolor="#D97706", lw=1.3, zorder=5)
ax_a.add_patch(box_allo)
ax_a.text(7.17, 7.82, "ALLOSTERIC CREVICE (ago-PAM)", ha="center", fontsize=8.6, fontweight="bold", color="#B45309", zorder=6)
ax_a.text(7.17, 7.46, "GPR81 Agonist 1 (Takeda Tool Compound)", ha="center", va="top", fontsize=7.2, fontweight="bold", color="#92400E", zorder=6)
ax_a.text(7.17, 7.10, "• TM5, TM6 Extracellular Cleft\n• Anchor: Glu153 H-bond + Met170\n• Independent Synergistic Site", 
          ha="center", va="top", linespacing=1.35, fontsize=6.6, color="#78350F", zorder=6)
# Guide arrow pointing into crevice mouth
ax_a.annotate("", xy=(6.5, 5.5), xytext=(6.5, 6.20),
              arrowprops=dict(arrowstyle="->", color="#D97706", lw=1.4, mutation_scale=9), zorder=6)

# Separation vector between pockets in upper center
ax_a.annotate("", xy=(5.30, 7.18), xytext=(3.90, 7.18),
              arrowprops=dict(arrowstyle="<->", color=NN_CORAL, lw=1.8, mutation_scale=10), zorder=8)
ax_a.text(4.60, 7.42, "17.7 Å Distance", ha="center", fontsize=7.5, fontweight="bold", color=NN_CORAL,
          bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor=NN_CORAL, lw=0.8), zorder=9)
ax_a.text(4.60, 6.85, "Independent\nSites", ha="center", fontsize=6.5, fontweight="bold", color="#991B1B", zorder=9)

# Bottom banner
ax_a.text(4.6, 1.45, "CYTOPLASM: Gi Coupling · Activation switches: DRY (TM3) & NPxxY (TM7) → 4.8 Å TM6 opening",
          ha="center", fontsize=7.2, fontweight="bold", color=NN_NAVY,
          bbox=dict(boxstyle="round,pad=0.28", facecolor="#EFF6FF", edgecolor="#BFDBFE", lw=0.9), zorder=5)

ax_a.set_xlim(0.0, 9.2)
ax_a.set_ylim(1.1, 8.2)
ax_a.axis("off")

# ----------------------------------------------------------------------
# Panel B: Ternary Co-Occupancy & Steric Exclusion (ENLARGED HIGH-LEGIBILITY FONTS)
# ----------------------------------------------------------------------
ax_b = fig.add_subplot(gs[0, 1], facecolor=NN_BG)
ax_b.set_title("B. Ternary Co-Occupancy (Lactate+Agonist 1) vs AZ1 Steric Clash", 
               fontsize=13.5, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

# Left box: Lactate + Agonist 1
box_left = patches.FancyBboxPatch((0.5, 0.7), 4.1, 5.7, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor="#16A34A", lw=1.5)
ax_b.add_patch(box_left)
ax_b.text(2.55, 6.05, "Lactate + Agonist 1 (ago-PAM)\n[Co-Occupancy Allowed]", ha="center", va="top", fontsize=11.5, fontweight="bold", color="#15803D", linespacing=1.2)

ax_b.scatter([1.6], [4.4], s=350, color="#16A34A", edgecolors=NN_NAVY, lw=1.5, zorder=5)
ax_b.text(1.6, 3.75, "Lactate\n(Ortho)", ha="center", va="top", fontsize=10.5, fontweight="bold", color="#15803D")

ax_b.scatter([3.5], [4.7], s=380, color=NN_AMBER, edgecolors=NN_NAVY, lw=1.5, zorder=5)
ax_b.text(3.5, 4.05, "Agonist 1\n(Allo)", ha="center", va="top", fontsize=10.5, fontweight="bold", color="#B45309")

ax_b.annotate("", xy=(3.3, 4.7), xytext=(1.8, 4.4),
              arrowprops=dict(arrowstyle="<->", color="#16A34A", lw=2.2, mutation_scale=12))
ax_b.text(2.55, 5.15, "d_min = 7.71 Å\n(Clean Gap)", ha="center", va="bottom", fontsize=10.0, fontweight="bold", color="#16A34A")

ax_b.text(2.55, 1.45, "• Zero Steric Clash · Both Sites Filled\n• Synergistic Functional Potentiation", 
          ha="center", va="bottom", fontsize=9.8, fontweight="bold", color="#15803D",
          bbox=dict(boxstyle="round,pad=0.35", facecolor="#DCFCE7", edgecolor="#86EFAC", lw=1.0))

# Right box: AZ1 + Agonist 1
box_right = patches.FancyBboxPatch((5.0, 0.7), 4.1, 5.7, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor=NN_CORAL, lw=1.5)
ax_b.add_patch(box_right)
ax_b.text(7.05, 6.05, "AZ1 (Ortho) + Agonist 1 (Allo)\n[Steric Exclusion]", ha="center", va="top", fontsize=11.5, fontweight="bold", color=NN_CORAL, linespacing=1.2)

ax_b.scatter([6.1], [4.3], s=400, color="#2563EB", edgecolors=NN_NAVY, lw=1.5, zorder=5)
ax_b.text(6.1, 3.65, "AZ1\n(MW 603)", ha="center", va="top", fontsize=10.5, fontweight="bold", color="#1D4ED8")

ax_b.scatter([8.0], [4.7], s=380, color=NN_AMBER, edgecolors=NN_NAVY, lw=1.5, zorder=5)
ax_b.text(8.0, 4.05, "Agonist 1\n(MW 446)", ha="center", va="top", fontsize=10.5, fontweight="bold", color="#B45309")

ax_b.annotate("", xy=(7.8, 4.6), xytext=(6.3, 4.4),
              arrowprops=dict(arrowstyle="<->", color=NN_CORAL, lw=2.2, mutation_scale=12))
ax_b.text(7.05, 5.15, "d_min = 2.60 Å\n(Steric Collision!)", ha="center", va="bottom", fontsize=10.0, fontweight="bold", color=NN_CORAL)

ax_b.text(7.05, 1.45, "• Severe Extracellular Vestibule Clash\n• Mutual Competitive Displacement", 
          ha="center", va="bottom", fontsize=9.8, fontweight="bold", color="#B91C1C",
          bbox=dict(boxstyle="round,pad=0.35", facecolor="#FEE2E2", edgecolor="#FCA5A5", lw=1.0))

ax_b.set_xlim(0, 9.6)
ax_b.set_ylim(0.4, 6.8)
ax_b.axis("off")

# ----------------------------------------------------------------------
# Panel C: HCAR1 vs HCAR2 Selectivity (ENLARGED HIGH-LEGIBILITY FONTS)
# ----------------------------------------------------------------------
ax_c = fig.add_subplot(gs[1, 0], facecolor=NN_BG)
ax_c.set_title("C. HCAR1 vs HCAR2: Anti-Flushing Selectivity Mechanism", 
               fontsize=13.0, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

box_h1 = patches.FancyBboxPatch((0.4, 3.2), 4.3, 3.3, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor="#0284C7", lw=1.5)
ax_c.add_patch(box_h1)
ax_c.text(2.55, 6.20, "HCAR1 (GPR81) — Agonist Tolerant", ha="center", va="top", fontsize=11.5, fontweight="bold", color="#0369A1")
ax_c.text(2.55, 5.45, "Allosteric Pocket Motif (TM5-ECL2):", ha="center", va="top", fontsize=9.8, color="#475569")
ax_c.text(2.55, 4.80, "Leu152 — Glu153 — Asn154", ha="center", va="top", fontsize=13.0, fontweight="bold", color="#15803D",
          bbox=dict(boxstyle="round,pad=0.3", facecolor="#DCFCE7", edgecolor="#86EFAC", lw=1.1))
ax_c.text(2.55, 3.75, "Glu153 (-1 charge): d = 2.50 Å\nStrong -6.2 kcal/mol H-bond Anchor", ha="center", va="top", fontsize=9.2, fontweight="bold", color="#15803D", linespacing=1.25)

box_h2 = patches.FancyBboxPatch((5.1, 3.2), 4.3, 3.3, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor=NN_CORAL, lw=1.5)
ax_c.add_patch(box_h2)
ax_c.text(7.25, 6.20, "HCAR2 (GPR109A) — Severe Flushing", ha="center", va="top", fontsize=11.5, fontweight="bold", color=NN_CORAL)
ax_c.text(7.25, 5.45, "Homologous Motif (Cryo-EM PDB 8J6P):", ha="center", va="top", fontsize=9.8, color="#475569")
ax_c.text(7.25, 4.80, "Lys164 — Lys165 — Lys166", ha="center", va="top", fontsize=13.0, fontweight="bold", color=NN_CORAL,
          bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEE2E2", edgecolor="#FCA5A5", lw=1.1))
ax_c.text(7.25, 3.75, "Triple Basic (+3 net charge):\nLys165 (3.29 Å) Repulsion & Clash", ha="center", va="top", fontsize=9.2, fontweight="bold", color="#B91C1C", linespacing=1.25)

ax_c.text(4.90, 1.65, 
          "MOLECULAR BASIS FOR FLUSHING AVOIDANCE:\n"
          "• HCAR2 features a +3 basic lysine wall (Lys164–Lys165–Lys166)\n"
          "  that forms a potent electrostatic and steric barrier.\n"
          "• GPR81 agonists with neutral/basic RHS vectors are repelled,\n"
          "  completely eliminating off-target cutaneous flushing.",
          ha="center", va="center", fontsize=9.2, fontweight="bold", linespacing=1.35,
          bbox=dict(boxstyle="round,pad=0.40", facecolor="#EFF6FF", edgecolor="#BFDBFE", lw=1.2))

ax_c.set_xlim(0, 10.0)
ax_c.set_ylim(0.6, 6.8)
ax_c.axis("off")

# ----------------------------------------------------------------------
# Panel D: Full 45-Compound Landscape (Ortho vs Allo vs Bitopic)
# ----------------------------------------------------------------------
ax_d = fig.add_subplot(gs[1, 1], facecolor=NN_BG)
ax_d.set_title("D. 45-Compound Series Landscape: Orthosteric vs Allosteric vs Bitopic", 
               fontsize=12, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

categories = ["Pure Orthosteric\n(4 acids: Lactate/CHBA)", 
              "Allosteric / ago-PAM\n(33 cpds: c28/c26/c30/Ag1)", 
              "Bitopic / Dualsteric\n(8 cpds: c32-c39 Amides)"]
counts = [4, 33, 8]
colors = ["#16A34A", NN_AMBER, "#2563EB"]

bars = ax_d.bar(categories, counts, color=colors, edgecolor=NN_NAVY, lw=0.9, width=0.52)
for b, c in zip(bars, counts):
    ax_d.text(b.get_x() + b.get_width()/2, b.get_height() + 0.9, f"N = {c} ({c/45*100:.1f}%)", 
              ha="center", fontsize=8.5, fontweight="bold", color=NN_NAVY)

ax_d.set_ylabel("Compound Count (N = 45)", fontsize=9, color="#475569")
ax_d.set_ylim(0, 42)
ax_d.set_xlim(-0.6, 2.6)
ax_d.grid(True, axis="y", ls="--", alpha=0.5, color="#CBD5E1")

# Clean annotation placed in the UPPER-LEFT/CENTER to avoid right-edge overflow
ax_d.annotate("Strategic Sweet Spot:\nAmide series (c38: 54 nM, 500x GHSR)\nbridges both Arg71 & Glu153!", 
             xy=(2, 8), xytext=(0.5, 26),
             arrowprops=dict(facecolor="#2563EB", shrink=0.08, width=1.3, headwidth=5),
             fontsize=8, fontweight="bold", color="#1D4ED8",
             bbox=dict(boxstyle="round,pad=0.25", facecolor="#DBEAFE", edgecolor="#93C5FD"))

plt.savefig(OUT_PNG, dpi=300)
plt.close()
print(f"Saved optimized 300 DPI figure: {OUT_PNG}")
