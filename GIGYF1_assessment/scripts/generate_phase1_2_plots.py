import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path

out_dir = Path("output/2026-09-18/gigyf1_grb10_case")
out_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

# Load data
with open(out_dir / "gigyf1_phase1_2_summary.json") as f:
    data = json.load(f)

# -------------------------------------------------------------
# Figure 1: GRB10 Pro-Rich Motif Interface Contact Breakdown
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.8), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax1.set_facecolor('#F8FAFC')
ax2.set_facecolor('#F8FAFC')

# Panel A: Contacts per residue on GRB10
grb10_res = ["Pro1", "Pro2", "Val3", "Leu4", "Thr5", "Pro6", "Gly7", "Ser8"]
contacts = [2, 2, 4, 5, 4, 7, 1, 0]
colors = ['#00857C' if c >= 4 else '#001965' for c in contacts]

bars = ax1.bar(range(len(grb10_res)), contacts, color=colors, width=0.58, zorder=3)
ax1.set_xticks(range(len(grb10_res)))
ax1.set_xticklabels(grb10_res, fontsize=8.5, fontweight='bold')
ax1.set_ylabel('Interface Contacts Count (< 4.5 Å)', fontsize=9, fontweight='bold', color='#1E293B')
ax1.set_title('A. GRB10 Pro-Rich Motif Interface Contact Density', fontsize=10, fontweight='bold', color='#001965', loc='left', pad=8)
ax1.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)
ax1.set_ylim(0, 9)

for b, v in zip(bars, contacts):
    if v > 0:
        ax1.text(b.get_x() + b.get_width()/2., v + 0.2, str(v), ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1E293B')

ax1.annotate('Core PPII Hydrophobic Lock\n(Val3 - Leu4 - Thr5 - Pro6)', xy=(3.5, 6), xytext=(2.0, 7.8),
             arrowprops=dict(facecolor='#00857C', arrowstyle='->', lw=1.2),
             fontsize=7.5, fontweight='bold', color='#00857C')

# Panel B: Human Genetics Variant Distance to GRB10 Epitope
variants = ["Tyr498Cys\n(Aromatic)", "Gly485Arg\n(Turn Loop)", "Phe495Leu\n(Core Helix)", "Trp494Arg\n(Core Helix)", "Ser474Ter\n(LoF Cut)"]
distances = [1.87, 5.22, 6.15, 6.24, 0.0] # 0 represents complete structural loss
v_colors = ['#D9383A', '#F59E0B', '#F59E0B', '#F59E0B', '#7F1D1D']

bars2 = ax2.barh(range(len(variants)), distances, color=v_colors, height=0.55, zorder=3)
ax2.set_yticks(range(len(variants)))
ax2.set_yticklabels(variants, fontsize=8, fontweight='bold')
ax2.set_xlabel('Min Distance to GRB10 Epitope (Å)', fontsize=9, fontweight='bold', color='#1E293B')
ax2.set_title('B. UK Biobank T2D Rare Coding Variants on GIGYF1', fontsize=10, fontweight='bold', color='#001965', loc='left', pad=8)
ax2.grid(axis='x', linestyle='--', alpha=0.35, zorder=0)
ax2.set_xlim(0, 8.5)

for b, d, name in zip(bars2, distances, variants):
    if d > 0:
        ax2.text(d + 0.2, b.get_y() + b.get_height()/2., f"{d:.2f} Å", ha='left', va='center', fontsize=7.5, fontweight='bold', color='#1E293B')
    else:
        ax2.text(0.3, b.get_y() + b.get_height()/2., "Catastrophic Truncation (LoF)", ha='left', va='center', fontsize=7.5, fontweight='bold', color='#FFFFFF')

plt.tight_layout()
out_plot = out_dir / "fig_gigyf1_grb10_phase1_2_summary.png"
plt.savefig(out_plot, dpi=300, bbox_inches='tight')
plt.close()
print("Saved summary plot to:", out_plot)
