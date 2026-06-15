# BRP Peptides – Blood-Brain Barrier Permeability Prediction Report

> **Analysis date**: 2026-06-15
> **Requestor**: EJNH (Jason; forwarded via Jay)
> **Jira**: RIC-388 (Phase 2 + Phase 3 — sequence-based peptide DL models + benchmarking)
> **Tool**: ESM-2 protein language model + 6 reference models, B3Pred benchmark
> **Analyst**: Qiuye Jin (Computational Sciences)
> **Deliverables**: `output/2026-06-15/brp_bbb_prediction/` (report HTML/PDF/PPTX, `results/consensus_predictions.csv`)

---

## 1. Background and Objective

**BRP** (BRINP2-related peptide) is a 12-mer, non-incretin, centrally-acting
anti-obesity peptide reported in *Nature* 2025 (Coassolo et al., PMID 40044869,
Svensson lab). EJNH provided four BRP-related peptides and asked whether the
native peptide is predicted to cross the BBB **from its amino-acid sequence**,
and whether the prediction is sequence-specific.

This analysis answers the RIC-388 Phase 2/3 objectives: deploy a sequence-based
deep-learning peptide model, build a multi-model consensus, expand the validation
set with known food-intake-regulating peptides, and benchmark with
sensitivity/specificity/MCC.

## 2. Target Peptides

| ID | Name | Sequence (C-term amide) | Length | MW (Da) | Net charge @7.4 |
|---|---|---|---|---|---|
| 0660-0000-0564 | BRP (native) | THRILRRLFNLC | 12 | 1540.9 | +4.1 |
| 0660-0000-0565 | BRP dimer | (THRILRRLFNLC)₂ | 24 | ~3079.8 | +8.2 |
| 0660-0000-0566 | Scrambled BRP | CRFIRNLHLLRT | 12 | 1540.9 | +4.1 |
| 0660-0000-0587 | Scrambled BRP | RFTCIRLNRLHL | 12 | 1540.9 | +4.1 |

> **Critical observation**: 0564 (native), 0566 and 0587 (the two scrambles) have
> **identical amino-acid composition** (C₁F₁H₁I₁L₃N₁R₃T₁); they differ **only in
> residue order**. Any composition/descriptor-based feature is therefore identical
> across the three.

## 3. Methods

### 3.1 Why a sequence-order model is required

Composition/descriptor models (BrainPepPass, AAC, BBPpred) see only "which amino
acids and how many" → they assign the three same-composition peptides **identical
scores** by construction and cannot answer the sequence-specificity question. Only
sequence-order-aware models (ESM-2 protein language model, dipeptide composition)
can separate native from scrambled.

### 3.2 Model matrix (7 predictors)

| Model | Type | Order-aware | Source |
|---|---|---|---|
| **ESM-2 (150M) + LR** ⭐ | PLM embedding + logistic regression | **Yes** | ESM-2 UR50; head on B3Pred |
| AAC+DPC+Phys (RF) | AA+dipeptide+physchem RF | Partial | B3Pred |
| DPC | Dipeptide composition + LR | Partial | B3Pred |
| AAC / AAC+Phys | Composition (+physchem) + LR | No | B3Pred |
| BBPpred | SVC (external) | No | Chen et al. 2021 |
| BrainPepPass v2 | mordred descriptors + XGBoost | No | deployed (RIC-384) |

### 3.3 Benchmark & evaluation

- **B3Pred Dataset-1** (Kumar et al., *Pharmaceutics* 2021): train 204(+)/201(−);
  validation 52(+)/50(−); plus 249 CPP negatives for a stricter test.
- 10×5 repeated stratified CV on train; held-out evaluation; 200-bootstrap
  uncertainty on the queries.
- ESM-2 weights pulled via the Facebook fair-esm CDN (HuggingFace is blocked in
  this environment); A100 GPU embeddings.

## 4. Results

| Model | 0564 native | 0565 dimer* | 0566 scram | 0587 scram | Separates? |
|---|---|---|---|---|---|
| **ESM-2** ⭐ | **87.5** | 87.5 | **10.6** | **10.8** | ✅ Clear |
| AAC+DPC+Phys (RF) | 47.0 | 47.0 | 44.8 | 52.2 | ⚠️ Weak |
| DPC | 99.2 | 99.2 | 99.0 | 100 | ⚠️ All BBB+ |
| AAC | 39.3 | 39.3 | 39.3 | 39.3 | ❌ Identical |
| AAC+Phys | 38.2 | 38.2 | 38.2 | 38.2 | ❌ Identical |
| BBPpred | 77.2 | 77.2 | 77.2 | 77.2 | ❌ Identical |
| BrainPepPass v2 | 10.2 | 10.2 | 10.2 | 10.1 | ❌ Identical |

- ESM-2 benchmark: validation AUC **0.90**, vs-CPP AUC **0.95**.
- Native − scrambled margin positive in **98%** of bootstrap resamples (mean +53 pts).

\* Dimer ~3080 Da out-of-domain; scored via its monomer, for reference only.

## 5. Reference benchmark (Phase 2 validation peptides)

Five known appetite regulators (UniProt-verified active forms) anchor the scale:

| Peptide | Form | Len | ESM-2 P(BBB+) | Known central route |
|---|---|---|---|---|
| **α-MSH** | Ac-(1-13)-NH₂ | 13 | **98.0%** BBB+ (in-domain) | Crosses BBB (saturable transport) |
| GLP-1 | (7-36)amide | 30 | 95.8% BBB+ | Area postrema / vagal |
| GIP | (1-42) | 42 | 19.3% BBB− | Median-eminence access |
| PYY | (3-36) | 34 | 99.7% BBB+ | Arcuate (median eminence) + vagal |
| AgRP | (83-132) | 50 | 100% BBB+ | Endogenous CNS peptide; cystine-knot |

The in-domain **α-MSH hit (98%)** matches its established saturable-transport BBB
crossing — an independent validation of the pipeline.

## 6. Conclusions

1. **Native BRP is predicted BBB-penetrant (~88%); both scrambled controls are
   non-penetrant (~11%).** Only the sequence model resolves this.
2. The result matches the *Nature* study design (scrambles are its negative
   controls), independently supporting credibility.
3. **Caveat**: the model predicts intrinsic, sequence-based penetration
   *propensity*. Several reference peptides act centrally via circumventricular
   organs / vagal pathways rather than crossing the intact BBB — penetration
   propensity ≠ in-vivo brain-entry route.

## 7. Limitations & recommendations

- Dimer 0565 (~3080 Da) and reference peptides (30–50 aa) are extrapolation;
  ESM-2 encodes only the 20 standard amino acids (no amidation/disulfide/
  cyclization/lipidation).
- **Recommended wet-lab validation**: PAMPA-BBB or in-vivo brain/plasma Kp,uu
  comparing 0564 vs 0566/0587 — the strong predicted separation (88% vs 11%) is a
  clean, falsifiable test.

## 8. Reproducibility

All scripts in `output/2026-06-15/brp_bbb_prediction/code/` (01→16), run in order.
Benchmark from `raghavagps/B3Pred`; reference sequences from UniProt
(P01275/P09681/P01189/O00253/P10082). This sequence-based capability was
generalized into a reusable platform — see
[peptide-esm-platform.md](peptide-esm-platform.md).
