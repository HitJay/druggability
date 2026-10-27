#!/usr/bin/env python3
"""Step 2: split benchmark protein pairs into shards for parallel pMSA generation.

generate_protein_pair_MSA.py processes pairs serially (hhfilter is the bottleneck),
so we shard the pair list; each shard runs as an independent process in its own
output directory (the original script writes a shared tmplog -> must not share cwd).
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_LIST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "benchmark_pairs.tsv")
N_SHARDS = int(sys.argv[2]) if len(sys.argv) > 2 else 32
OUT_DIR = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "work", "pair_lists")
# optional: directory with single-protein MSAs; pairs missing either MSA are excluded
# (generate_protein_pair_MSA.py would crash the whole shard on a missing file)
MSA_DIR = sys.argv[4] if len(sys.argv) > 4 else None

os.makedirs(OUT_DIR, exist_ok=True)
with open(IN_LIST) as f:
    pairs = [ln.strip() for ln in f if ln.strip()]

excluded = []
if MSA_DIR:
    def has_msa(pair):
        a, b = pair.split("_")
        return (os.path.exists(os.path.join(MSA_DIR, a + ".a3m"))
                and os.path.exists(os.path.join(MSA_DIR, b + ".a3m")))
    kept = []
    for p in pairs:
        if has_msa(p):
            kept.append(p)
        else:
            excluded.append(p)
    pairs = kept
    with open(os.path.join(ROOT, "data", "excluded_pairs.tsv"), "w") as f:
        f.write("pair\treason\n")
        for p in excluded:
            f.write(f"{p}\tmissing_single_omicMSA\n")
    print(f"excluded {len(excluded)} pairs with missing single MSAs")

n = len(pairs)
per = (n + N_SHARDS - 1) // N_SHARDS
for i in range(N_SHARDS):
    shard = pairs[i * per:(i + 1) * per]
    if not shard:
        continue
    out = os.path.join(OUT_DIR, f"shard_{i:03d}.txt")
    with open(out, "w") as f:
        f.write("\n".join(shard) + "\n")
    print(f"{out}: {len(shard)} pairs")
print(f"total {n} pairs in {N_SHARDS} shards")
