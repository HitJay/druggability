import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path

out_dir = Path("output/2026-09-18/gigyf1_grb10_case")
out_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

# -------------------------------------------------------------
# Figure: Clinical Genetics Delta-Delta-G & MD Energy Decomposition
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.8), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax1.set_facecolor('#F8FAFC')
ax2.set_facecolor('#F8FAFC')

# Panel A: UK Biobank Variant Delta-Delta-G (Binding Disruption)
variants = ["Ser474Ter\n(LoF Truncation)", "Tyr498Cys\n(Epitope Core)", "Trp494Arg\n(Helix Core)", "Phe495Leu\n(Hydrophobic)", "Gly485Arg\n(Entrance Loop)"]
ddg_vals = [5.88, 2.74, 1.80, 0.81, 0.60]
bar_colors = ['#7F1D1D', '#DC2626', '#EF4444', '#F59E0B', '#FBBF24']

bars1 = ax1.bar(range(len(variants)), ddg_vals, color=bar_colors, width=0.55, zorder=3)
ax1.set_xticks(range(len(variants)))
ax1.set_xticklabels(variants, fontsize=7.5, fontweight='bold')
ax1.set_ylabel(r'$\Delta\Delta G_\mathrm{binding}\ \mathrm{(kcal/mol)}$ [Disruption]', fontsize=9, fontweight='bold', color='#1E293B')
ax1.set_title('A. Human Genetics T2D Variants In Silico Perturbation (ΔΔG)', fontsize=10, fontweight='bold', color='#001965', loc='left', pad=8)
ax1.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)
ax1.set_ylim(0, 7.0)

for b, v in zip(bars1, ddg_vals):
    ax1.text(b.get_x() + b.get_width()/2., v + 0.15, f"+{v:.2f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1E293B')

ax1.annotate('Severe Epitope Collapse\n(Y498C: Kd -> 3.85 mM)', xy=(1, 2.74), xytext=(1.8, 4.2),
             arrowprops=dict(facecolor='#DC2626', arrowstyle='->', lw=1.2),
             fontsize=7.5, fontweight='bold', color='#DC2626')

# Panel B: A100 GPU Explicit-Solvent MD Energy Breakdown (vdW + Coulomb)
pep_res = ["Pro1", "Pro2", "Val3", "Leu4", "Thr5", "Pro6", "Gly7", "Ser8"]
e_decomp = [-50.4, -6.7, -41.3, -40.0, -25.2, -16.5, -9.7, -1.2]
e_colors = ['#001965' if e < -30 else '#00857C' if e < -15 else '#64748B' for e in e_decomp]

bars2 = ax2.barh(range(len(pep_res)), e_decomp, color=e_colors, height=0.58, zorder=3)
ax2.set_yticks(range(len(pep_res)))
ax2.set_yticklabels(pep_res, fontsize=8.5, fontweight='bold')
ax2.set_xlabel('Mean Nonbonded Interaction Energy (kcal/mol)', fontsize=9, fontweight='bold', color='#1E293B')
ax2.set_title('B. A100 GPU Explicit-Solvent MD Energy Decomposition', fontsize=10, fontweight='bold', color='#001965', loc='left', pad=8)
ax2.grid(axis='x', linestyle='--', alpha=0.35, zorder=0)

for b, v in zip(bars2, e_decomp):
    ax2.text(v - 1.5, b.get_y() + b.get_height()/2., f"{v:.1f}", ha='right', va='center', fontsize=7.5, fontweight='bold', 
             color='#FFFFFF' if v < -20 else '#1E293B')

plt.tight_layout()
fig_path = out_dir / "fig_gigyf1_phase3_4_mechanics.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
plt.close()
print("Saved:", fig_path)
