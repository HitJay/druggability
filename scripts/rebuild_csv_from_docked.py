#!/usr/bin/env python3
"""Rebuild docking_results.csv from docked PDBQT output files."""
import os, csv, re, time

OUTDIR = "/das/user/QYJI/druggability/output/2026-07-10/ghsr_inverse_agonist_docking"
D7 = f"{OUTDIR}/docked_7F83"
D8 = f"{OUTDIR}/docked_8JSR"
CSV = f"{OUTDIR}/docking_results.csv"

FN = ['compound_id', 'score_7F83', 'score_8JSR', 'delta_score',
      'time_7F83', 'time_8JSR', 'error']

def extract_score(pdbqt_path):
    with open(pdbqt_path) as f:
        for line in f:
            if line.startswith("REMARK VINA RESULT:"):
                parts = line.strip().split()
                return float(parts[3])
    return None

# Get all compound IDs from docked_7F83
compounds = sorted(set(
    f.replace('_out.pdbqt', '')
    for f in os.listdir(D7) if f.endswith('_out.pdbqt')
))

rows = []
for cid in compounds:
    p7 = os.path.join(D7, f"{cid}_out.pdbqt")
    p8 = os.path.join(D8, f"{cid}_out.pdbqt")
    if not os.path.exists(p7) or not os.path.exists(p8):
        continue
    s7 = extract_score(p7)
    s8 = extract_score(p8)
    if s7 is None or s8 is None:
        continue
    rows.append({
        'compound_id': cid,
        'score_7F83': round(s7, 2),
        'score_8JSR': round(s8, 2),
        'delta_score': round(s7 - s8, 2),
        'time_7F83': '',
        'time_8JSR': '',
        'error': '',
    })

with open(CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FN)
    w.writeheader()
    w.writerows(rows)

total = len(rows)
ligands = [f for f in os.listdir(f"{OUTDIR}/ligands") if f.endswith('.pdbqt')]
print(f"CSV rebuilt: {total} compounds")
print(f"Total ligands: {len(ligands)}")
print(f"Missing PDBQT output: {len(ligands) - total}")
