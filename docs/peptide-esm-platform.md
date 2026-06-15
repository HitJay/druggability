# Peptide-ESM Platform – One Base Model, Many Task Heads

> **Date**: 2026-06-15
> **Jira**: RIC-388 (generalization of the sequence-based peptide DL capability)
> **Analyst**: Qiuye Jin (Computational Sciences)
> **Package**: `bbbkit.peptide` (`src/bbbkit/peptide/`); install with `pip install 'bbbkit[peptide]'`
> **Reproducible scratch run**: `output/2026-06-15/peptide_esm_platform/`

---

## 1. Motivation

The BRP analysis ([brp-bbb-prediction.md](brp-bbb-prediction.md)) showed that a
frozen ESM-2 protein-language-model embedding + a lightweight classifier head
matches a purpose-built BBB tool. ESM-2 embeddings encode structural /
physicochemical / evolutionary signal, so **any "peptide sequence → property"
task can reuse the same frozen embedding**. This platform operationalizes that:
compute the embedding **once per peptide**, cache it, and train many cheap task
heads on top.

```text
            ESM-2 embedding service (GPU, computed once, cached on disk)
                                  │
        ┌──────────┬──────────────┼──────────────┬──────────┐
     BBB head   ACP head      Toxicity head    AMP head   …new head
   (logreg)    (logreg)        (logreg)       (logreg)
```

## 2. Architecture

| Component | File | Role |
|---|---|---|
| Weight config | `bbbkit/peptide/config.py` | ESM-2 ckpt resolution (arg > `ESM2_CKPT` > bbbkit model dir > torch hub) + fair-esm CDN auto-download |
| Embedding service | `bbbkit/peptide/embed.py` | ESM-2 (fair-esm 150M) + on-disk cache keyed by `sha1(model:sequence)` |
| Task heads | `bbbkit/peptide/heads.py` | linear / MLP head + 5-fold CV + train-only hyperparameter selection + held-out eval |
| Dataset onboarding | `bbbkit/peptide/datasets.py` | published-benchmark download/parse into canonical `{train,test}.csv` (official splits) |
| Task registry | `bbbkit/peptide/tasks.py` | dataset source, official-split flag, published SOTA refs |
| Orchestrator | `bbbkit/peptide/benchmark.py` | `run_benchmark` / `run_task`: embed → CV-select head → held-out eval |

The on-disk cache is the key idea: a peptide that appears in two tasks is embedded
**only once**, so the expensive GPU step is amortized. Re-embedding cached
sequences is ~1 ms (a `.npy` read, no model load). Cache lives at
`~/.cache/bbbkit/esm_emb` (override via `BBBKIT_ESM_CACHE`).

## 3. Benchmark integrity

- Every task uses a **published benchmark dataset**; **official train/test splits
  are used verbatim** and the test set is never seen during training/selection.
- Standard 20 amino acids only, peptide length 5–50, cross-split deduplication
  (no leakage).
- Metrics: ROC-AUC, Accuracy, MCC, Sensitivity, Specificity (held-out) + 5-fold
  stratified CV on train. Published SOTA cited per task (approximate, from papers).

## 4. Results (held-out official test sets)

Best head per task selected by **train-CV only** (the test set is never used for
selection). AUC is on the held-out official test split.

| Task | Dataset | n tr/te | Head | **Test AUC** | Test MCC | Published SOTA | Verdict |
|---|---|---|---|---|---|---|---|
| BBB penetration | B3Pred (Kumar 2021) | 405/99 | linear | **0.893** | 0.635 | ~0.87 | matches/exceeds |
| Anticancer (alternate) | AntiCP 2.0 (Agrawal 2021) | 1548/388 | linear | **0.975** | 0.846 | ~0.98 / 0.85 | matches |
| Anticancer (main, hard) | AntiCP 2.0 main | 1375/341 | mlp | **0.817** | 0.455 | ~0.82 | close |
| Toxicity | ToxinPred v1 (Gupta 2013) | 5380/596 | mlp | **0.845** | 0.512 | ~0.94 | honest gap |
| Antimicrobial (AMP) | LMPred / DRAMP 2.0 (Dee 2021) | 2143/2158 | mlp | **0.927** | 0.734 | ~0.98 | below specialized CNN |
| Hemolytic | HemoPI-1 (Chaudhary 2016) | 867/217 | linear | **0.998** | 0.963 | ~0.95 / 0.73 | exceeds |

**Reading**: a generic frozen ESM-2 + lightweight head matches purpose-built tools
on BBB, ACP-alternate and hemolytic (HemoPI MCC 0.96 ≫ SOTA 0.73); is close on the
hard ACP-main split; is competitive but below a task-trained CNN on AMP (0.93 vs
~0.98); and **under-performs** the specialized SVM on ToxinPred's independent set
(distribution shift — CV 0.97 but independent test 0.85). Reported plainly — not
every task is won by ESM.

### 4.1 Performance improvement — linear vs tuned-MLP head

A non-linear MLP head (hyperparameters selected by train-CV) lifts the harder
tasks most, while easy/small tasks keep the linear head:

| Task | Linear AUC | MLP AUC | ΔAUC | Best (by CV) |
|---|---|---|---|---|
| Anticancer (main) | 0.785 | 0.817 | **+0.033** | mlp |
| Toxicity | 0.824 | 0.845 | **+0.021** (MCC +0.045) | mlp |
| AMP | 0.926 | 0.927 | +0.001 | mlp |
| BBB | 0.875 | 0.838 | −0.036 | linear (small set → MLP overfits) |

Same frozen embeddings, no re-embedding — only the head changes.

## 5. Honest limitations

- Mean-pooled embedding + linear head is a strong **baseline, not a ceiling**; an
  MLP head or attention pooling would likely lift the harder tasks.
- ESM-2 sees only the 20 standard amino acids — no modifications, D-amino acids,
  cyclization, or lipidation (the modification blind spot from the BRP work).
- This is a **protein/peptide** base. Small-molecule ADMET and protein-ligand
  interaction tasks need other bases (ChemBERTa / MolFormer / Uni-Mol).

## 6. How to use

```bash
pip install 'bbbkit[peptide]'          # torch + fair-esm + scikit-learn
bbbkit peptide download-weights        # ESM-2 150M via fair-esm CDN (or set ESM2_CKPT)
bbbkit peptide tasks                    # list built-in benchmark tasks
bbbkit peptide download --tasks amp,hemolytic --data-dir data/peptide
bbbkit peptide benchmark --tasks amp,hemolytic --data-dir data/peptide
```

```python
from bbbkit.peptide import embed, run_benchmark
X = embed(["THRILRRLFNLC"])                 # cached ESM-2 embedding (1, 640)
results = run_benchmark("data/peptide", keys=["amp", "hemolytic"])
```

## 7. How to extend

```bash
# 1. add data/<newtask>/{train,test}.csv   (columns: sequence,label)
#    (or add an onboarding fn in bbbkit/peptide/datasets.py for auto-download)
# 2. register the task in bbbkit/peptide/tasks.py (REGISTRY)
# 3. bbbkit peptide benchmark --tasks <newtask>   # reuses the shared ESM cache
```

Candidate next tasks (datasets verified downloadable from raghavagps GitHub):
antiviral (AVP), cell-penetrating peptides (CPP).
