#!/usr/bin/env python3
"""Step 1: prepare benchmark pair lists for pMSA generation.

Inputs : data/benchmarks/positives_and_negatives.tsv (3000 pos / 30000 neg)
Outputs: data/benchmark_pairs.tsv   (all 33k pairs, tab: pair, label)
         data/benchmark_labels.tsv  (pair -> label map for evaluation)
"""
import csv, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "data", "benchmarks", "positives_and_negatives.tsv")
OUT_PAIRS = os.path.join(ROOT, "data", "benchmark_pairs.tsv")
OUT_LABELS = os.path.join(ROOT, "data", "benchmark_labels.tsv")

pairs = []
with open(BENCH) as f:
    r = csv.reader(f, delimiter="\t")
    header = next(r)
    assert header[0] == "Protein pairs", header
    for row in r:
        if not row or not row[0].strip():
            continue
        pairs.append((row[0].strip(), row[1].strip()))

n_pos = sum(1 for _, l in pairs if l == "positive")
n_neg = sum(1 for _, l in pairs if l == "negative")
print(f"pairs: {len(pairs)} (pos {n_pos} / neg {n_neg})")

with open(OUT_PAIRS, "w") as f:
    for p, _ in pairs:
        f.write(p + "\n")
with open(OUT_LABELS, "w") as f:
    for p, l in pairs:
        f.write(f"{p}\t{l}\n")
print("wrote", OUT_PAIRS, "and", OUT_LABELS)
