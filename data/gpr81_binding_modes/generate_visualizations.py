#!/usr/bin/env python3
"""
Generate comprehensive 300 DPI publication figure with 4 panels:
Panel A: 2D Structural Domain Architecture & Ligand Binding Sites
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
# Set explicit margins: left=0.07, right=0.93, top=0.92, bottom=0.08
gs = GridSpec(2, 2, figure=fig, hspace=0.30, wspace=0.24, 
              left=0.065, right=0.935, top=0.92, bottom=0.07)

NN_NAVY = "#001965"
NN_TEAL = "#00857C"
NN_CORAL = "#D9383A"
NN_AMBER = "#D97706"
NN_PURPLE = "#7C3AED"
NN_BG = "#F8FAFC"

# ----------------------------------------------------------------------
# Panel A: 2D Domain Architecture & Ligand Sites
# ----------------------------------------------------------------------
ax_a = fig.add_subplot(gs[0, 0], facecolor=NN_BG)
ax_a.set_title("A. GPR81 Structural Domains & Dual Pocket Organization", 
               fontsize=12, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

ax_a.axhspan(2.5, 5.5, color="#E2E8F0", alpha=0.7, zorder=1)
ax_a.text(0.3, 5.2, "EXTRACELLULAR SPACE (Aqueous)", fontsize=8, fontweight="bold", color="#475569")
ax_a.text(0.3, 4.0, "MEMBRANE (POPC Bilayer)", fontsize=8, fontweight="bold", color="#64748B")
ax_a.text(0.3, 2.2, "CYTOPLASM (Gi Coupling)", fontsize=8, fontweight="bold", color="#475569")

tm_names = ["TM1", "TM2", "TM3", "TM4", "TM5", "TM6", "TM7"]
tm_x = [1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2]
tm_ranges = ["22-42", "50-70", "90-110", "131-151", "183-203", "221-241", "262-281"]

for x, name, rng in zip(tm_x, tm_names, tm_ranges):
    rect = patches.FancyBboxPatch((x-0.28, 2.5), 0.56, 3.0, boxstyle="round,pad=0.04",
                                  facecolor="#CBD5E1", edgecolor=NN_NAVY, linewidth=1.1, zorder=2)
    ax_a.add_patch(rect)
    ax_a.text(x, 4.0, f"{name}\n({rng})", ha="center", va="center", fontsize=7.5, fontweight="bold", color=NN_NAVY, zorder=3)

# Loops
ax_a.add_patch(patches.Arc((2.7, 5.5), 1.0, 1.2, theta1=0, theta2=180, color=NN_NAVY, lw=1.5, zorder=2))
ax_a.add_patch(patches.Arc((4.7, 5.5), 1.0, 2.0, theta1=0, theta2=180, color=NN_CORAL, lw=2.0, ls="--", zorder=2))
ax_a.text(4.7, 6.6, "ECL2 (Active Gate: Phe168/Ser167)", ha="center", fontsize=8, fontweight="bold", color=NN_CORAL)
ax_a.add_patch(patches.Arc((6.7, 5.5), 1.0, 1.0, theta1=0, theta2=180, color=NN_NAVY, lw=1.5, zorder=2))

ax_a.add_patch(patches.Arc((1.7, 2.5), 1.0, 0.8, theta1=180, theta2=360, color=NN_NAVY, lw=1.5, zorder=2))
ax_a.add_patch(patches.Arc((3.7, 2.5), 1.0, 0.8, theta1=180, theta2=360, color=NN_NAVY, lw=1.5, zorder=2))
ax_a.add_patch(patches.Arc((5.7, 2.5), 1.0, 0.8, theta1=180, theta2=360, color=NN_NAVY, lw=1.5, zorder=2))

# Pockets
ortho_bubble = patches.FancyBboxPatch((1.65, 4.4), 1.6, 1.3, boxstyle="round,pad=0.08",
                                      facecolor="#DCFCE7", edgecolor="#16A34A", lw=1.3, alpha=0.9, zorder=4)
ax_a.add_patch(ortho_bubble)
ax_a.text(2.45, 5.15, "ORTHOSTERIC CORE\nAnchor: Arg71 (TM2/3)\nLactate & AZ1 (Ortho)", 
          ha="center", va="center", fontsize=7.5, fontweight="bold", color="#15803D", zorder=5)

allo_bubble = patches.FancyBboxPatch((4.75, 4.75), 2.1, 1.4, boxstyle="round,pad=0.08",
                                     facecolor="#FEF3C7", edgecolor="#D97706", lw=1.3, alpha=0.9, zorder=4)
ax_a.add_patch(allo_bubble)
ax_a.text(5.80, 5.60, "ALLOSTERIC CREVICE (ago-PAM)\nAnchor: Glu153 / Met170 / His177\nAgonist 1 (Takeda)", 
          ha="center", va="center", fontsize=7.5, fontweight="bold", color="#B45309", zorder=5)

ax_a.annotate("", xy=(4.75, 5.15), xytext=(3.3, 4.8),
              arrowprops=dict(arrowstyle="<->", color=NN_CORAL, lw=1.8, mutation_scale=10), zorder=6)
ax_a.text(3.95, 5.25, "17.7 Å\nVector", ha="center", fontsize=8, fontweight="bold", color=NN_CORAL,
          bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFF", edgecolor=NN_CORAL, lw=0.8), zorder=7)

ax_a.set_xlim(0, 8.2)
ax_a.set_ylim(1.5, 7.2)
ax_a.axis("off")

# ----------------------------------------------------------------------
# Panel B: Ternary Co-Occupancy & Steric Exclusion
# ----------------------------------------------------------------------
ax_b = fig.add_subplot(gs[0, 1], facecolor=NN_BG)
ax_b.set_title("B. Ternary Co-Occupancy (Lactate+Agonist 1) vs AZ1 Steric Clash", 
               fontsize=12, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

# Left box: Lactate + Agonist 1
box_left = patches.FancyBboxPatch((0.6, 1.0), 3.9, 5.4, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor="#16A34A", lw=1.3)
ax_b.add_patch(box_left)
ax_b.text(2.55, 6.05, "Lactate + Agonist 1 (ago-PAM)\n[Co-Occupancy Allowed]", ha="center", fontsize=8.5, fontweight="bold", color="#15803D")

ax_b.scatter([1.7], [4.5], s=220, color="#16A34A", edgecolors=NN_NAVY, lw=1.3, zorder=5)
ax_b.text(1.7, 3.85, "Lactate\n(Ortho)", ha="center", fontsize=8, fontweight="bold", color="#15803D")

ax_b.scatter([3.4], [4.8], s=240, color=NN_AMBER, edgecolors=NN_NAVY, lw=1.3, zorder=5)
ax_b.text(3.4, 4.05, "Agonist 1\n(Allo)", ha="center", fontsize=8, fontweight="bold", color="#B45309")

ax_b.annotate("", xy=(3.2, 4.8), xytext=(1.9, 4.5),
              arrowprops=dict(arrowstyle="<->", color="#16A34A", lw=1.8, mutation_scale=9))
ax_b.text(2.55, 5.1, "d_min = 7.71 Å\n(Clean Gap)", ha="center", fontsize=7.5, fontweight="bold", color="#16A34A")

ax_b.text(2.55, 1.8, "• Zero Steric Clash\n• Independent Pockets\n• Synergistic Activation", 
          ha="center", fontsize=7.5, color="#15803D", bbox=dict(boxstyle="round,pad=0.25", facecolor="#DCFCE7", edgecolor="#86EFAC"))

# Right box: AZ1 + Agonist 1
box_right = patches.FancyBboxPatch((5.1, 1.0), 4.1, 5.4, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor=NN_CORAL, lw=1.3)
ax_b.add_patch(box_right)
ax_b.text(7.15, 6.05, "AZ1 (Ortho) + Agonist 1 (Allo)\n[Steric Exclusion]", ha="center", fontsize=8.5, fontweight="bold", color=NN_CORAL)

ax_b.scatter([6.3], [4.4], s=260, color="#2563EB", edgecolors=NN_NAVY, lw=1.3, zorder=5)
ax_b.text(6.1, 3.75, "AZ1\n(MW 603)", ha="center", fontsize=8, fontweight="bold", color="#1D4ED8")

ax_b.scatter([7.8], [4.8], s=240, color=NN_AMBER, edgecolors=NN_NAVY, lw=1.3, zorder=5)
ax_b.text(8.0, 4.05, "Agonist 1\n(MW 446)", ha="center", fontsize=8, fontweight="bold", color="#B45309")

ax_b.annotate("", xy=(7.6, 4.7), xytext=(6.5, 4.5),
              arrowprops=dict(arrowstyle="<->", color=NN_CORAL, lw=1.8, mutation_scale=9))
ax_b.text(7.1, 5.1, "d_min = 2.60 Å\n(Steric Clash!)", ha="center", fontsize=7.5, fontweight="bold", color=NN_CORAL)

ax_b.text(7.15, 1.8, "• Severe Steric Collision\n• Vestibule Exclusion\n• Mutual Displacement", 
          ha="center", fontsize=7.5, color=NN_CORAL, bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEE2E2", edgecolor="#FCA5A5"))

ax_b.set_xlim(0, 9.6)
ax_b.set_ylim(0.5, 6.8)
ax_b.axis("off")

# ----------------------------------------------------------------------
# Panel C: HCAR1 vs HCAR2 Selectivity (Triple-Lysine Positive Wall)
# ----------------------------------------------------------------------
ax_c = fig.add_subplot(gs[1, 0], facecolor=NN_BG)
ax_c.set_title("C. HCAR1 vs HCAR2 Selectivity: Anti-Flushing Charge-Flip Mechanism", 
               fontsize=12, fontweight="bold", color=NN_NAVY, pad=10, loc="left")

box_h1 = patches.FancyBboxPatch((0.5, 3.5), 4.0, 2.9, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor="#0284C7", lw=1.3)
ax_c.add_patch(box_h1)
ax_c.text(2.5, 6.0, "HCAR1 (GPR81) — Agonist Tolerant", ha="center", fontsize=8.5, fontweight="bold", color="#0369A1")
ax_c.text(2.5, 5.3, "Allosteric Pocket Motif (TM5-ECL2):", ha="center", fontsize=8, color="#475569")
ax_c.text(2.5, 4.4, "Leu152 — Glu153 — Asn154", ha="center", fontsize=10, fontweight="bold", color="#15803D",
          bbox=dict(boxstyle="round,pad=0.25", facecolor="#DCFCE7", edgecolor="#86EFAC"))
ax_c.text(2.5, 3.75, "Glu153 (-1): d=2.50 Å (Strong -6.2 kcal/mol anchor)", ha="center", fontsize=7.5, color="#15803D")

box_h2 = patches.FancyBboxPatch((4.9, 3.5), 4.2, 2.9, boxstyle="round,pad=0.08", facecolor="#FFFFFF", edgecolor=NN_CORAL, lw=1.3)
ax_c.add_patch(box_h2)
ax_c.text(7.0, 6.0, "HCAR2 (GPR109A) — Severe Flushing", ha="center", fontsize=8.5, fontweight="bold", color=NN_CORAL)
ax_c.text(7.0, 5.3, "Homologous Motif (PDB 8J6P):", ha="center", fontsize=8, color="#475569")
ax_c.text(7.0, 4.4, "Lys164 — Lys165 — Lys166", ha="center", fontsize=10, fontweight="bold", color=NN_CORAL,
          bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEE2E2", edgecolor="#FCA5A5"))
ax_c.text(7.0, 3.75, "Triple Basic (+3): Lys165 at 3.29 Å (Repulsion & Clash)", ha="center", fontsize=7.5, color=NN_CORAL)

ax_c.text(4.7, 1.8, 
          "MOLECULAR MECHANISM FOR FLUSHING AVOIDANCE:\n"
          "The +3 positive lysine wall (Lys164-Lys165-Lys166) in HCAR2 acts as an electrostatic barrier.\n"
          "GPR81 agonists carrying neutral/basic RHS elements are repelled by HCAR2, eliminating flushing.",
          ha="center", fontsize=7.8, color=NN_NAVY, bbox=dict(boxstyle="round,pad=0.35", facecolor="#EFF6FF", edgecolor="#BFDBFE"))

ax_c.set_xlim(0, 9.5)
ax_c.set_ylim(0.8, 6.8)
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
ax_d.set_xlim(-0.6, 2.6) # explicit xlim to guarantee margins
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
