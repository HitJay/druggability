#!/usr/bin/env python3
"""Full-series reverse-SAR analysis (Phase 6 results + EC50).

Reads phase6_full_series results for all 39 paper compounds on 8Z8A and 9KT9,
joins paper EC50 (from paper_structures_recovered.json) and reports:
  - global score-EC50 correlation per receptor
  - series-level trends (acyl_urea / constrained_cyclic / amide / linker_variant)
  - per-series docking direction consistency vs EC50
  - top-scoring compounds not in the original matched-pair set

Output: data/gpr81_phase1/phase6_full_series/full_series_reverse_sar.json
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from scipy import stats

PHASE1 = Path(__file__).resolve().parents[1] / "data/gpr81_phase1"
P6 = PHASE1 / "phase6_full_series"

# EC50 + series from recovered structures
rec = json.loads((PHASE1 / "paper_structures_recovered.json").read_text())
EC50 = {}
SERIES = {}
for c in rec["compounds"]:
    n = c["paper_compound_number"]
    ec = c.get("paper_reported_hGPR81_EC50_uM")
    if ec is None or (isinstance(ec, str)):
        continue
    if isinstance(ec, str) and ec.startswith(">"):
        continue  # censored values excluded from correlation
    EC50[n] = float(ec)
    SERIES[n] = c.get("series", "?")

# scores
scores = {}
with (P6 / "full_series_docking_results.csv").open() as fh:
    for r in csv.DictReader(fh):
        cid, rid = int(r["compound"]), r["receptor"]
        s = float(r["score_kcal_mol"])
        scores.setdefault((cid, rid), []).append(s)

best = {(c, r): min(v) for (c, r), v in scores.items()}

# correlation per receptor
print("=== global correlation (best score vs log10 EC50) ===")
for rid in ["8Z8A", "9KT9"]:
    xs, ecs = [], []
    for c in EC50:
        if (c, rid) in best:
            xs.append(best[(c, rid)])
            ecs.append(math.log10(EC50[c]))
    if len(xs) >= 5:
        r_p, p_p = stats.pearsonr(xs, ecs)
        r_s, p_s = stats.spearmanr(xs, ecs)
        print(f"{rid}: n={len(xs)} Pearson r={r_p:.3f} (p={p_p:.3f}) Spearman rho={r_s:.3f} (p={p_s:.3f})")
    else:
        print(f"{rid}: insufficient data ({len(xs)})")

# series-level
print("\n=== series-level (8Z8A best score vs EC50) ===")
for series in ["acyl_urea", "constrained_analogue_cyclic", "amide", "linker_variant"]:
    items = [(c, EC50[c], best.get((c, "8Z8A"))) for c in EC50 if SERIES.get(c) == series]
    items = [(c, ec, s) for c, ec, s in items if s is not None]
    if len(items) < 3:
        print(f"{series}: n={len(items)} (skip)")
        continue
    xs = [s for _, _, s in items]
    ecs = [math.log10(ec) for _, ec, _ in items]
    r_p, p_p = stats.pearsonr(xs, ecs)
    r_s, p_s = stats.spearmanr(xs, ecs)
    ec_range = (min(ec for _, ec, _ in items), max(ec for _, ec, _ in items))
    print(f"{series}: n={len(items)} EC50 range {ec_range[0]:.4f}-{ec_range[1]:.3f} uM | "
          f"Pearson r={r_p:.3f} (p={p_p:.3f}) Spearman rho={r_s:.3f} (p={p_s:.3f})")

# top 8Z8A scorers among compounds NOT in matched-pair set
matched = {15, 21, 22, 26, 28, 30, 31, 35, 36, 37, 38}
others = [(c, best.get((c, "8Z8A")), EC50[c], SERIES.get(c)) for c in EC50 if c not in matched and (c, "8Z8A") in best]
others.sort(key=lambda x: x[1] if x[1] is not None else 999)
print("\n=== best 8Z8A scorers outside matched-pair set ===")
for c, s, ec, series in others[:10]:
    print(f"  c{c:>2} {series:<18} score={s:>7.2f} EC50={ec} uM")

# worst 9KT9 outliers (positional QC candidates)
print("\n=== worst 9KT9 scores (candidates for positional QC) ===")
nine = [(c, best.get((c, "9KT9")), EC50[c]) for c in EC50 if (c, "9KT9") in best]
nine.sort(key=lambda x: x[1])
for c, s, ec in nine[:8]:
    print(f"  c{c:>2} 9KT9={s:>7.2f} (EC50={ec})")

# save
out = {
    "correlations": {},
    "series": {},
    "top_outside_matched": [{"compound": c, "score_8Z8A": s, "ec50_uM": ec, "series": se} for c, s, ec, se in others[:10]],
}
for rid in ["8Z8A", "9KT9"]:
    xs, ecs = [], []
    for c in EC50:
        if (c, rid) in best:
            xs.append(best[(c, rid)]); ecs.append(math.log10(EC50[c]))
    if len(xs) >= 5:
        r_p, p_p = stats.pearsonr(xs, ecs)
        r_s, p_s = stats.spearmanr(xs, ecs)
        out["correlations"][rid] = {"n": len(xs), "pearson_r": round(r_p, 3), "pearson_p": round(p_p, 3),
                                    "spearman_rho": round(r_s, 3), "spearman_p": round(p_s, 3)}
(P6 / "full_series_reverse_sar.json").write_text(json.dumps(out, indent=2) + "\n")
print("\nsaved ->", P6 / "full_series_reverse_sar.json")
