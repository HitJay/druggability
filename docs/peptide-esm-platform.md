# Peptide-ESM Platform – One Base Model, Many Task Heads

> **Date**: 2026-06-15
> **Jira**: RIC-388 (generalization of the sequence-based peptide DL capability)
> **Analyst**: Qiuye Jin (Computational Sciences)
> **Code**: `output/2026-06-15/peptide_esm_platform/`

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
| Embedding service | `esm_platform/embed.py` | ESM-2 (fair-esm 150M) + on-disk cache keyed by `sha1(model:sequence)` |
| Task registry | `esm_platform/tasks.py` | dataset source, official-split flag, published SOTA refs |
| Task head | `esm_platform/heads.py` | standardized logistic-regression + 5-fold CV + held-out eval |
| Orchestrator | `run_benchmark.py` | embed → CV → test per task |
| Report | `make_report.py` | benchmark figure + report |

The on-disk cache is the key idea: a peptide that appears in two tasks is embedded
**only once**, so the expensive GPU step is amortized. Re-embedding cached
sequences is ~1 ms (a `.npy` read, no model load).

## 3. Benchmark integrity

- Every task uses a **published benchmark dataset**; **official train/test splits
  are used verbatim** and the test set is never seen during training/selection.
- Standard 20 amino acids only, peptide length 5–50, cross-split deduplication
  (no leakage).
- Metrics: ROC-AUC, Accuracy, MCC, Sensitivity, Specificity (held-out) + 5-fold
  stratified CV on train. Published SOTA cited per task (approximate, from papers).

## 4. Results (held-out official test sets)

| Task | Dataset | n tr/te | **Test AUC** | Test MCC | Published SOTA | Verdict |
|---|---|---|---|---|---|---|
| BBB penetration | B3Pred (Kumar 2021) | 405/99 | **0.893** | 0.635 | ~0.87 | matches/exceeds |
| Anticancer (alternate) | AntiCP 2.0 (Agrawal 2021) | 1548/388 | **0.975** | 0.846 | ~0.98 / 0.85 | matches |
| Anticancer (main, hard) | AntiCP 2.0 main | 1375/341 | **0.769** | 0.425 | ~0.82 | close, below |
| Toxicity | ToxinPred v1 (Gupta 2013) | 5380/596 | **0.816** | 0.496 | ~0.94 | honest gap |

**Reading**: a generic frozen ESM-2 + linear head matches purpose-built tools on
BBB and ACP-alternate, is close on the hard ACP-main split, and **under-performs**
the specialized dipeptide+motif SVM on ToxinPred's independent set (distribution
shift; CV is 0.97 but independent test 0.82). Reported plainly — not every task is
won by ESM.

## 5. Honest limitations

- Mean-pooled embedding + linear head is a strong **baseline, not a ceiling**; an
  MLP head or attention pooling would likely lift the harder tasks.
- ESM-2 sees only the 20 standard amino acids — no modifications, D-amino acids,
  cyclization, or lipidation (the modification blind spot from the BRP work).
- This is a **protein/peptide** base. Small-molecule ADMET and protein-ligand
  interaction tasks need other bases (ChemBERTa / MolFormer / Uni-Mol).

## 6. How to extend

```bash
# 1. add data/<newtask>/{train,test}.csv   (columns: sequence,label)
# 2. register the task in esm_platform/tasks.py
# 3. python run_benchmark.py <newtask>      # reuses the shared ESM cache
```

Candidate next tasks (datasets verified downloadable from raghavagps GitHub):
antimicrobial (AMP), hemolytic, antiviral, cell-penetrating peptides.
