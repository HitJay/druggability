#!/usr/bin/env python3
"""Phase 7+8: ΔScore analysis, hit classification, and prioritization."""
import csv, os, json
from collections import defaultdict

OUTDIR = "/das/user/QYJI/druggability/output/2026-07-10/ghsr_inverse_agonist_docking"
CSV = f"{OUTDIR}/docking_results.csv"
RANKED = f"{OUTDIR}/ranked_hits.csv"
SUMMARY = f"{OUTDIR}/GHSR_docking_summary.md"

with open(CSV) as f:
    reader = csv.DictReader(f)
    compounds = []
    for row in reader:
        compounds.append({
            'cid': row['compound_id'],
            's7': float(row['score_7F83']),
            's8': float(row['score_8JSR']),
            'delta': float(row['delta_score']),
        })

# Classification (fixed sign)
classification_counts = defaultdict(int)
classified = []
for c in compounds:
    d = c['delta']
    s7 = c['s7']
    if d < -1.0:
        cls = 'strong_inverse_agonist'
    elif d < -0.5:
        cls = 'moderate_inverse_agonist'
    elif d > 1.0:
        cls = 'agonist_like'
    elif d > 0.5:
        cls = 'active_state_preferring'
    elif s7 < -7.0 and c['s8'] < -7.0 and abs(d) < 0.3:
        cls = 'pan_binder'
    elif abs(d) <= 0.5 and s7 >= -7.0:
        cls = 'weak_binder'
    else:
        cls = 'other'
    classification_counts[cls] += 1
    classified.append({**c, 'class': cls})

# Priority score: -delta * 0.6 + (-s7) * 0.4
for c in classified:
    c['priority'] = -c['delta'] * 0.6 + (-c['s7']) * 0.4

# Rank by priority descending
classified.sort(key=lambda c: -c['priority'])

# Positive controls (known GHSR ligands)
controls = ['CHEMBL1201869', 'CHEMBL1201870', 'CHEMBL4297452', 'CHEMBL2106884',
            'CHEMBL1201203', 'CHEMBL1201878', 'CHEMBL2106913']
ctrl_results = [c for c in classified if c['cid'] in controls]
ctrl_names = {
    'CHEMBL1201869': 'Anamorelin', 'CHEMBL1201870': 'Macimorelin',
    'CHEMBL4297452': 'Ibutamoren', 'CHEMBL2106884': 'GHRP-6',
    'CHEMBL1201203': '1KQ', 'CHEMBL1201878': 'MK-0677',
    'CHEMBL2106913': 'Ghrelin(1-3)amide'}

# Write ranked hits
FN = ['rank', 'compound_id', 'class', 'score_7F83', 'score_8JSR', 'delta_score', 'priority']
with open(RANKED, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FN)
    w.writeheader()
    for i, c in enumerate(classified, 1):
        w.writerow({'rank': i, 'compound_id': c['cid'], 'class': c['class'],
                     'score_7F83': round(c['s7'], 2), 'score_8JSR': round(c['s8'], 2),
                     'delta_score': round(c['delta'], 2), 'priority': round(c['priority'], 2)})

# Print summary
print("=" * 60)
print("GHSR DOCKING CAMPAIGN — PHASE 7+8 RESULTS")
print("=" * 60)
print(f"\nTotal compounds docked: {len(compounds)}")
print(f"\n--- Classification ---")
for cls in ['strong_inverse_agonist', 'moderate_inverse_agonist', 'pan_binder',
            'active_state_preferring', 'agonist_like', 'weak_binder', 'other']:
    if classification_counts[cls]:
        print(f"  {cls:30s}: {classification_counts[cls]:>5d}")

# Top 20 inverse agonists
top_ia = [c for c in classified if c['class'] == 'strong_inverse_agonist'][:20]
print(f"\n--- Top 20 Strong Inverse Agonists ---")
print(f"{'Rank':>5s} {'Compound':20s} {'7F83':>8s} {'8JSR':>8s} {'Delta':>8s} {'Priority':>8s}")
for i, c in enumerate(top_ia, 1):
    print(f"{i:5d} {c['cid']:20s} {c['s7']:8.2f} {c['s8']:8.2f} {c['delta']:8.2f} {c['priority']:8.2f}")

print(f"\n--- Positive Controls ---")
print(f"{'Compound':20s} {'7F83':>8s} {'8JSR':>8s} {'Delta':>8s} {'Expected':>15s} {'Pass?':>6s}")
for c in ctrl_results:
    name = ctrl_names.get(c['cid'], c['cid'])
    if c['cid'] == 'CHEMBL1201203':  # 1KQ = co-crystallized inverse agonist
        expected = 'inv_agonist'
        pass_ = '✓' if c['delta'] < -0.5 else '✗'
    else:  # agonists should prefer active state (delta > 0)
        expected = 'agonist'
        pass_ = '✓' if c['delta'] > 0.3 else '✗'
    print(f"{name:20s} {c['s7']:8.2f} {c['s8']:8.2f} {c['delta']:8.2f} {expected:>15s} {pass_:>6s}")

# Write summary markdown
with open(SUMMARY, 'w') as f:
    f.write(f"""# GHSR Inverse Agonist Docking — Summary

**Date**: 2026-07-14
**Library**: {len(compounds)} compounds
**Receptors**: 7F83 (inactive) + 8JSR (active)
**Software**: AutoDock Vina (exhaustiveness=8)

## Classification

| Class | Count | Description |
|-------|------:|-------------|
""")
    for cls, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
        f.write(f"| {cls} | {count} | |\n")
    
    f.write(f"""
## Top 20 Inverse Agonists (by priority)

| Rank | Compound | 7F83 (kcal/mol) | 8JSR (kcal/mol) | ΔScore | Priority |
|-----:|----------|----------------:|----------------:|------:|--------:|
""")
    for i, c in enumerate(top_ia, 1):
        f.write(f"| {i} | {c['cid']} | {c['s7']:.2f} | {c['s8']:.2f} | {c['delta']:.2f} | {c['priority']:.2f} |\n")
    
    f.write(f"""
## Positive Controls

| Name | 7F83 | 8JSR | ΔScore | Expected | Pass? |
|------|-----:|-----:|------:|----------|:-----:|
""")
    for c in ctrl_results:
        name = ctrl_names.get(c['cid'], c['cid'])
        if c['cid'] == 'CHEMBL1201203':
            expected = 'inv_agonist'
            pass_ = '✓' if c['delta'] < -0.5 else '✗'
        else:
            expected = 'agonist'
            pass_ = '✓' if c['delta'] > 0.3 else '✗'
        f.write(f"| {name} | {c['s7']:.2f} | {c['s8']:.2f} | {c['delta']:.2f} | {expected} | {pass_} |\n")

print(f"\n\nRanked hits: {RANKED}")
print(f"Summary: {SUMMARY}")
