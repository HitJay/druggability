import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

out_dir = Path("output/2026-09-18/oxtr_onepager_assets")
out_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

# ==============================================================================
# Visualization 1: Side-by-Side Structural Pocket & Steric Mechanism Schematic
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.4), dpi=300)
fig.patch.set_facecolor('#FFFFFF')

# Panel 1: OXTR
ax1.set_facecolor('#F8FAFC')
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis('off')

# OXTR Pocket boundary (Open, spacious)
oxtr_boundary = patches.Polygon([[1, 9], [2, 3], [5, 1], [8, 3], [9, 9]], closed=False, 
                                edgecolor='#001965', facecolor='#EFF6FF', linewidth=3, zorder=1)
ax1.add_patch(oxtr_boundary)

# TM1 (Far away, pos 1.5, 7.5)
ax1.add_patch(patches.FancyBboxPatch((0.6, 5.5), 1.4, 3.5, boxstyle="round,pad=0.2", 
                                     facecolor='#93C5FD', edgecolor='#1D4ED8', linewidth=1.5, zorder=2))
ax1.text(1.3, 7.2, "TM1 (Helix I)\nOpen State", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1E3A8A')

# ECL3 Lys306 (Flexible, swinging outward)
ax1.annotate('', xy=(9.2, 8.5), xytext=(8.0, 6.5),
            arrowprops=dict(arrowstyle="->", color='#00857C', lw=2.5, connectionstyle="arc3,rad=-0.2"))
ax1.text(8.5, 6.0, "ECL3 Lys306\n(Swings out freely)", ha='center', va='top', fontsize=9, fontweight='bold', color='#00857C')

# Peptide in OXTR
# Core deep pocket (Tyr2, Ile3)
ax1.add_patch(patches.Circle((5, 2.2), 0.7, facecolor='#D9383A', edgecolor='#991B1B', lw=1.5, zorder=4))
ax1.text(5, 2.2, "Tyr2\nCore", ha='center', va='center', fontsize=9, fontweight='bold', color='#FFFFFF')

# Position 7 Gly
ax1.add_patch(patches.Circle((6.8, 5.0), 0.6, facecolor='#10B981', edgecolor='#047857', lw=1.5, zorder=4))
ax1.text(6.8, 5.0, "Gly7", ha='center', va='center', fontsize=9, fontweight='bold', color='#FFFFFF')

# Connection line
ax1.plot([5, 6.8], [2.2, 5.0], color='#D9383A', lw=3, zorder=3)
ax1.plot([6.8, 7.8], [5.0, 7.5], color='#D9383A', lw=3, zorder=3)

# Exit vector arrow from Pos 8
ax1.annotate('', xy=(9.5, 9.2), xytext=(7.8, 7.5),
            arrowprops=dict(arrowstyle="->", color='#0284C7', lw=3.0, linestyle='--'))
ax1.text(8.8, 8.0, "Pos 8 Exit\n(To Solvent)", ha='left', va='center', fontsize=9, fontweight='bold', color='#0284C7')

ax1.set_title("A. Human OXTR: Spacious Plastic Vestibule\n(Gly7 Accommodated; Active & Stable)", 
              fontsize=11.5, fontweight='bold', color='#001965', pad=10)

# Panel 2: V2R
ax2.set_facecolor('#FEF2F2')
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.axis('off')

# V2R Pocket boundary (Constricted, narrow)
v2r_boundary = patches.Polygon([[2.5, 9], [3, 3], [5, 1], [7, 3], [7.5, 9]], closed=False, 
                               edgecolor='#991B1B', facecolor='#FFF1F2', linewidth=3, zorder=1)
ax2.add_patch(v2r_boundary)

# TM1 Inward Shift (Constricted by 3.51 Å!)
ax2.add_patch(patches.FancyBboxPatch((2.2, 5.5), 1.4, 3.5, boxstyle="round,pad=0.2", 
                                     facecolor='#FCA5A5', edgecolor='#B91C1C', linewidth=2, zorder=2))
ax2.text(2.9, 7.2, "TM1 Inward\nShift -3.51 Å!", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#7F1D1D')

# Inward shift arrow
ax2.annotate('', xy=(2.0, 7.2), xytext=(0.8, 7.2),
            arrowprops=dict(arrowstyle="->", color='#B91C1C', lw=2.5))
ax2.text(1.2, 7.7, "3.51 Å", fontsize=9, fontweight='bold', color='#B91C1C')

# Leu302 Rigid Hydrophobic Clamp
ax2.add_patch(patches.FancyBboxPatch((6.8, 5.5), 1.4, 2.5, boxstyle="round,pad=0.2", 
                                     facecolor='#FDE68A', edgecolor='#D97706', linewidth=1.5, zorder=2))
ax2.text(7.5, 6.7, "Leu302\n(Rigid Clamp)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#92400E')

# Peptide in V2R
ax2.add_patch(patches.Circle((5, 2.2), 0.7, facecolor='#94A3B8', edgecolor='#475569', lw=1.5, zorder=4))
ax2.text(5, 2.2, "Tyr2", ha='center', va='center', fontsize=9, fontweight='bold', color='#FFFFFF')

# Gly7 violently clashing with TM1
ax2.add_patch(patches.Circle((4.2, 5.8), 0.6, facecolor='#EF4444', edgecolor='#7F1D1D', lw=2, zorder=4))
ax2.text(4.2, 5.8, "Gly7", ha='center', va='center', fontsize=9, fontweight='bold', color='#FFFFFF')

# Clash explosion symbol
ax2.text(3.6, 6.6, "⚡ CLASH!", fontsize=12, fontweight='black', color='#DC2626', zorder=5)

# Expulsion ejection arrow
ax2.annotate('', xy=(5.0, 9.5), xytext=(4.2, 6.6),
            arrowprops=dict(arrowstyle="->", color='#DC2626', lw=3.5, linestyle='-'))
ax2.text(5.5, 8.8, "Trajectory Ejection\n(70.8 Å Drift in MD)", ha='left', va='center', fontsize=9.5, fontweight='black', color='#DC2626')

ax2.set_title("B. Vasopressin V2R: Severe 3.51 Å Constriction\n(Pro7 Missing -> Steric Collisions -> Complete Ejection)", 
              fontsize=11.5, fontweight='bold', color='#991B1B', pad=10)

plt.tight_layout()
fig_mech_path = out_dir / "fig_mech_comparison.png"
plt.savefig(fig_mech_path, dpi=300, bbox_inches='tight')
plt.close()
print("Saved:", fig_mech_path)

# ==============================================================================
# Visualization 2: Molecular Architecture & Exit Vector Scheme (CYIQNCGLG-C18)
# ==============================================================================
fig, ax = plt.subplots(figsize=(10.5, 2.3), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')
ax.set_xlim(0, 11)
ax.set_ylim(0, 3)
ax.axis('off')

# Sequence tiles
seq_data = [
    ("Cys1", "#001965", "Disulfide Anchor"),
    ("Tyr2", "#D9383A", "Activation Hotspot"),
    ("Ile3", "#001965", "Hydrophobic Core"),
    ("Gln4", "#001965", "H-Bond Donor"),
    ("Asn5", "#001965", "Backbone Turn"),
    ("Cys6", "#001965", "Disulfide Bridge"),
    ("Gly7", "#00857C", "★ 1000× Selectivity Switch"),
    ("Lys8", "#0284C7", "★ Exit Vector (C18-diacid)"),
    ("Gly9", "#64748B", "C-terminal Cap")
]

# Draw disulfide bridge arc between Cys1 and Cys6
arc = patches.Arc((3.5, 1.8), 5.0, 1.2, angle=0, theta1=0, theta2=180, color='#F59E0B', lw=2.5, ls='--')
ax.add_patch(arc)
ax.text(3.5, 2.5, "Intramolecular Disulfide Loop (Cys1 - Cys6)", ha='center', va='center', fontsize=9, fontweight='bold', color='#D97706')

for i, (res, col, role) in enumerate(seq_data):
    x_pos = 1.0 + i * 1.05
    y_pos = 1.1
    # Card
    rect = patches.FancyBboxPatch((x_pos - 0.45, y_pos - 0.45), 0.9, 0.9, boxstyle="round,pad=0.1",
                                  facecolor=col, edgecolor='none', zorder=3)
    ax.add_patch(rect)
    ax.text(x_pos, y_pos + 0.05, res, ha='center', va='center', fontsize=10, fontweight='bold', color='#FFFFFF', zorder=4)
    ax.text(x_pos, y_pos - 0.22, f"Pos {i+1}", ha='center', va='center', fontsize=8, color='#E2E8F0', zorder=4)
    
    # Sub role text
    ax.text(x_pos, y_pos - 0.72, role, ha='center', va='top', fontsize=8, fontweight='bold', color=col)

# Draw Lipidation chain hanging from Lys8
ax.annotate('', xy=(8.35, -0.05), xytext=(8.35, 0.55),
            arrowprops=dict(arrowstyle="->", color='#0284C7', lw=2.5))
ax.text(8.35, -0.15, "Octadecanedioic acid-γGlu (C18 Diacid Albumin Binder)\n[Plasma Exposure ~160h Once-Weekly]", 
        ha='center', va='top', fontsize=8.5, fontweight='bold', color='#0284C7')

plt.tight_layout()
fig_arch_path = out_dir / "fig_peptide_architecture.png"
plt.savefig(fig_arch_path, dpi=300, bbox_inches='tight')
plt.close()
print("Saved:", fig_arch_path)
