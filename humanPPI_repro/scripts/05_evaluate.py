#!/usr/bin/env python3
"""Step 5: aggregate RF2-PPI scores, weighted PR curve (Fig 1F/2D), author-score cross-check.

Weighted PR (paper Fig 1 caption): positives weighted w=0.01 to model S/N=1:1000.
  precision(rank) = TP*w / (TP*w + FP),  recall(rank) = TP / P_total
Outputs:
  results/all_scores.tsv               pair, p_bind, label
  results/pr_curve.png                 our reproduction PR curve + operating points
  results/pr_metrics.json              AUCPR, recall@precision 0.8/0.9, counts
  results/author_crosscheck.tsv        pair, ours, authors (for pairs in both)
  results/author_crosscheck_stats.json correlation + agreement summary
"""
import glob, gzip, json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORING = os.path.join(ROOT, "work", "scoring")
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)

W_POS = 0.01
AUTHOR_SCORES = os.path.join(ROOT, "downloads", "RF2-PPI_scores.gz")

# ---------- 1. aggregate our scores ----------
# NOTE: official predict_list_PPI.py writes <list_fn>.log/.npz next to the list file,
# not in its own cwd.
scores = {}   # pair -> p_bind
for log_fn in glob.glob(os.path.join(ROOT, "work", "pair_lists", "*_input.log")):
    with open(log_fn) as f:
        next(f)  # header
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            a3m_path, p = parts[0], parts[1]
            pair = os.path.basename(a3m_path).replace(".i90.a3m", "")
            try:
                scores[pair] = float(p)
            except ValueError:
                continue
print(f"scored pairs: {len(scores)}")

labels = {}
with open(os.path.join(ROOT, "data", "benchmark_labels.tsv")) as f:
    for line in f:
        p, l = line.rstrip("\n").split("\t")
        labels[p] = l
print(f"benchmark pairs: {len(labels)}")

all_pairs = sorted(labels)
with open(os.path.join(RESULTS, "all_scores.tsv"), "w") as f:
    f.write("pair\tlabel\tp_bind\n")
    for p in all_pairs:
        f.write(f"{p}\t{labels[p]}\t{scores.get(p, float('nan')):.6f}\n")

scored = [(p, scores[p], labels[p]) for p in all_pairs if p in scores]
n_pos = sum(1 for _, _, l in scored if l == "positive")
n_neg = sum(1 for _, _, l in scored if l == "negative")
missing = len(all_pairs) - len(scored)
print(f"with scores: {len(scored)} (pos {n_pos} / neg {n_neg}); missing pMSA/score: {missing}")

# ---------- 2. weighted PR ----------
pairs_sorted = sorted(scored, key=lambda x: -x[1])
y = np.array([1.0 if l == "positive" else 0.0 for _, _, l in pairs_sorted])
P = y.sum()
tp = np.cumsum(y)
fp = np.cumsum(1 - y)
prec = tp * W_POS / (tp * W_POS + fp)
rec = tp / P
# prepend recall=0
rec_c = np.concatenate([[0.0], rec])
prec_c = np.concatenate([[prec[0] if len(prec) else 1.0], prec])
aucpr = float(np.sum(np.diff(rec_c) * prec_c[1:]))

def recall_at_precision(target):
    ok = np.where(prec >= target)[0]
    return float(rec[ok[0]]) if len(ok) else 0.0, (int(ok[0]) if len(ok) else None)

r90, i90 = recall_at_precision(0.90)
r80, i80 = recall_at_precision(0.80)
metrics = {
    "w_positive": W_POS,
    "scored_pairs": len(scored),
    "positives": int(n_pos),
    "negatives": int(n_neg),
    "pairs_without_score": missing,
    "AUCPR_weighted": aucpr,
    "recall_at_precision_0.90": r90,
    "rank_at_precision_0.90": i90,
    "recall_at_precision_0.80": r80,
    "rank_at_precision_0.80": i80,
}
with open(os.path.join(RESULTS, "pr_metrics.json"), "w") as f:
    json.dump(metrics, f, indent=1)
print(json.dumps(metrics, indent=1))

# ---------- 3. PR plot (NN corporate palette) ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAVY, TEAL, RED = "#001965", "#00857C", "#D9383A"
fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=200)
ax.step(rec_c * 100, prec_c * 100, where="post", color=NAVY, lw=2,
        label=f"RF2-PPI + omicMSA (this repro)\nAUCPR={aucpr:.3f} (w=0.01)")
if i90 is not None:
    ax.plot(rec[i90] * 100, prec[i90] * 100, "o", color=RED, ms=7,
            label=f"90% precision @ recall {r90*100:.1f}%")
if i80 is not None:
    ax.plot(rec[i80] * 100, prec[i80] * 100, "s", color=TEAL, ms=7,
            label=f"80% precision @ recall {r80*100:.1f}%")
ax.set_xlabel("Recall (%)")
ax.set_ylabel("Precision (%)")
ax.set_xlim(0, 100)
ax.set_ylim(0, 105)
ax.grid(alpha=0.3)
ax.legend(fontsize=8, loc="lower left")
ax.set_title("Human PPI benchmark reproduction\n(Zhang et al., Science 2025; 3,000 pos / 30,000 neg, S/N=1:1000)",
             fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(RESULTS, "pr_curve.png"))
print("wrote", os.path.join(RESULTS, "pr_curve.png"))

# ---------- 4. author cross-check ----------
author = {}
if os.path.exists(AUTHOR_SCORES):
    bench_set = set(all_pairs)
    with gzip.open(AUTHOR_SCORES, "rt") as f:
        for line in f:
            if line.startswith("#") or line.startswith("Pair"):
                continue
            parts = line.rstrip("\n").split("\t")
            if parts and parts[0] in bench_set:
                try:
                    author[parts[0]] = float(parts[1])
                except ValueError:
                    pass
    common = sorted(set(author) & set(scores))
    with open(os.path.join(RESULTS, "author_crosscheck.tsv"), "w") as f:
        f.write("pair\tlabel\tp_ours\tp_authors\n")
        for p in common:
            f.write(f"{p}\t{labels[p]}\t{scores[p]:.6f}\t{author[p]:.6f}\n")
    a = np.array([scores[p] for p in common])
    b = np.array([author[p] for p in common])
    stats = {
        "pairs_in_author_scores": len(author),
        "pairs_compared": len(common),
        "pearson_r": float(np.corrcoef(a, b)[0, 1]) if len(common) > 2 else None,
        "spearman_r": float(__import__("scipy.stats", fromlist=["spearmanr"]).spearmanr(a, b).statistic) if len(common) > 2 else None,
        "mean_abs_diff": float(np.mean(np.abs(a - b))) if common else None,
        "frac_abs_diff_le_0.1": float(np.mean(np.abs(a - b) <= 0.1)) if common else None,
    }
    with open(os.path.join(RESULTS, "author_crosscheck_stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    print(json.dumps(stats, indent=1))
else:
    print("author scores file not found; skip cross-check")
