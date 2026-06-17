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
| Predictor | `bbbkit/peptide/predict.py` | `predict_bbb`: sequence → ESM-2 → B3Pred-trained head → P(BBB+) + bootstrap CI |
| Auto-report | `bbbkit/peptide/report.py` | applicability domain + Opus interpretation + self-contained HTML / PPTX |

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

## 6b. BBB auto-report pipeline (NEW · 2026-06-16)

End-to-end: **peptide sequences → ESM-2 BBB prediction → applicability-domain
flagging → LLM (Claude Opus 4.7) interpretation → self-contained HTML / PPTX**.
Built on the same frozen-ESM-2 base; reuses `bbbkit.report.llm.LLMClient` (the
OpenAI-compatible client wired to the internal Opus gateway).

### What it adds

| Piece | Role |
|---|---|
| `predict_bbb` (`predict.py`) | seq → ESM-2 (GPU) → B3Pred-trained linear head → P(BBB+) + bootstrap 90% CI |
| `applicability_domain` (`report.py`) | rule flags from the B3Pred training distribution (405 peptides, median 13 aa, 80 % ≤ 20 aa, max 30): `in-domain` / `edge-extrapolation` / `out-of-domain-length` / `out-of-domain-modification` |
| `build_bbb_report` (`report.py`) | per-peptide Opus narrative + executive summary → HTML (+ optional PPTX) + matrix CSV |

### Honest-by-construction interpretation ("组合拳")

The model is non-deterministic, so the report layer enforces quality structurally
rather than trusting one free-form generation:

1. **Numbers are code-owned** — the LLM writes prose only; every score / CI is
   injected by code in `_assemble_peptide_narrative`. The model cannot hallucinate
   a number into the report.
2. **Structured JSON output** — `response_format={"type":"json_object"}` (verified
   supported by the gateway; `temperature`/`seed` are rejected by Bedrock). The LLM
   fills fixed fields (`reading` / `domain` / `caveat` / `literature`).
3. **Deterministic validation** — `_validate_peptide_fields` rejects any prose that
   contains a `%`/CI, omits "propensity", or (for out-of-domain inputs) fails to
   flag the score as an upper bound.
4. **Retry with self-correction** — on validation failure the reason is fed back
   to the model; this drove the fallback rate from 20 % → **0 %** on the 10-peptide
   panel.
5. **Graceful fallback** — exhausted retries fall back to a deterministic English
   template, so a report is always produced (works with no API / offline).
6. **Few-shot golden examples** — anchor tone/depth (in-domain + out-of-domain).

Reports are **English-only** by design (verified 0 Chinese chars in HTML / CSV /
PPTX, including the PPTX theme fonts).

### CLI

```bash
# A) input CSV has a `sequence` column → end-to-end GPU predict, then report
bbbkit peptide report -i seqs.csv -o outdir --pptx --ckpt <abs path to esm2_t30_150M_UR50D.pt>

# B) input CSV already has a `p_bbb` column → skip prediction, just write the report
bbbkit peptide report -i predictions.csv -o outdir --pptx

# --no-llm = templates only (no API); --bootstrap N = CI resamples (default 200)
```

### Two-stage wrapper (`scripts/run_e2e.sh`)

No single environment has both the GPU stack and the LLM SDK, so the wrapper
splits the run:

- **Stage 1** — `/data/user/QYJI/miniforge3/bin/python` (torch + fair-esm + A100)
  runs the ESM-2 prediction and writes the prediction CSV.
- **Stage 2** — the repo `.venv` (openai SDK) reads that CSV and calls Opus to
  render HTML / PPTX.

```bash
bash scripts/run_e2e.sh <sequences.csv> <outdir> [--pptx] [--no-llm] [--bootstrap N]
```

Verified end-to-end (2026-06-16): predictions reproduce the BRP reference exactly
(native 87.5 %, scrambled 10.5 %, α-MSH 98.0 %, GLP-1 95.9 %); Opus narratives
0 fallbacks; HTML + 4-slide PPTX, 0 Chinese. Tests: `tests/test_report.py`
(28, all green; full peptide+report suite 44 pass).

### ⚠️ Out-of-domain is flagged, not silently scored

A lipidated / PEGylated / cyclized peptide (e.g. **NN9161**, C18+PEG ~2200 Da) is
correctly returned **unscored** and badged `out-of-domain-modification` — ESM-2
encodes only the 20 standard amino acids. Extending the tool to *score* such
protracted analogs is the subject of the
[protracted-peptide improvement plan](../output/2026-06-16/bbb_protracted_improvement_plan/improvement_plan.md).

## 7. How to extend

```bash
# 1. add data/<newtask>/{train,test}.csv   (columns: sequence,label)
#    (or add an onboarding fn in bbbkit/peptide/datasets.py for auto-download)
# 2. register the task in bbbkit/peptide/tasks.py (REGISTRY)
# 3. bbbkit peptide benchmark --tasks <newtask>   # reuses the shared ESM cache
```

Candidate next tasks (datasets verified downloadable from raghavagps GitHub):
antiviral (AVP), cell-penetrating peptides (CPP).
