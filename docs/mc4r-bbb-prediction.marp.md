---
marp: true
theme: default
paginate: true
size: 16:9
header: 'MC4R Agonists – BBB Permeability Prediction'
footer: 'Analysis 2026-05-21 · BrainPepPass v2'
style: |
  section { font-size: 22px; padding: 40px 60px; }
  section.title { font-size: 30px; text-align: center; }
  section.title h1 { font-size: 44px; }
  h1 { font-size: 32px; margin-bottom: 8px; color: #003a70; }
  h2 { font-size: 26px; color: #003a70; border-bottom: 2px solid #003a70; padding-bottom: 4px; }
  h3 { font-size: 22px; color: #00518a; }
  table { font-size: 16px; border-collapse: collapse; margin: 8px 0; }
  th { background: #003a70; color: #fff; padding: 4px 8px; }
  td { padding: 3px 8px; border: 1px solid #ccc; }
  blockquote { font-size: 18px; color: #555; border-left: 4px solid #003a70; }
  code { background: #f0f0f0; padding: 1px 4px; }
  ul, ol { margin: 4px 0; }
  li { margin: 2px 0; }
  .small table { font-size: 14px; }
---

<!-- _class: title -->

# MC4R Agonists
## Blood-Brain Barrier Permeability Prediction Report

Analysis date: **2026-05-21**
NN9161 structure update: 2026-05-21

Tool: BrainPepPass v2 (local reproduction, xgboost 3.2.0 + NumPy 2.4)
Source: *BrainPepPass: A framework based on supervised dimensionality reduction for predicting BBB-penetrating peptides*
Result file: `results/mc4r_bbb_predictions.csv`

---

## 1. Background and Objective

**MC4R** (melanocortin-4 receptor) is a key GPCR regulating:

- Energy homeostasis
- Sexual function
- Pain

Whether an MC4R-targeting peptide / small molecule **crosses the BBB** directly determines:

- Central vs. peripheral action
- Choice of administration route

**This analysis** evaluates BBB permeability for **six MC4R-related compounds** using **BrainPepPass** and **BBiPP**.

---

## 2. Target Compounds

<div class="small">

| Compound | Alias | Type | MoA | Status |
|---|---|---|---|---|
| **Setmelanotide** | RM-493, Imcivree | Cyclic peptide (disulfide) | MC4R agonist | ✅ Marketed (POMC/LEPR-deficiency obesity) |
| **Bremelanotide** | PT-141, Vyleesi | Cyclic peptide (lactam) | MC4R agonist | ✅ Marketed (HSDD) |
| **Afamelanotide** | Scenesse, CUV1647 | Linear peptide (13-mer) | MC1R/MC4R agonist | ✅ Marketed (erythropoietic protoporphyria) |
| **Bivamelagon** | LB54640 | Oral small molecule | MC4R agonist | 🔬 Investigational (Eli Lilly) |
| **TCMCB07** | — | Cyclic peptide | **MC4R antagonist** | 🔬 Investigational (Endevica Bio, cachexia) |
| **NN9161** | LAMA2 (NN code, *not* laminin α2 gene), 0070-0002-0453 | Lipidated peptide | MC4R agonist | 🔬 Investigational (Novo Nordisk) |

</div>

> ⚠️ **TCMCB07 note**: PMID 32544087, 35592439 confirm TCMCB07 as MC4R **antagonist** for cachexia, deliberately designed as a peripheral agent that **does not cross the BBB**.

---

## 3.1 Tools — BrainPepPass v2

- **Principle**: RDKit + mordred descriptors → supervised dimensionality reduction (3 XGBRegressor pattern-learning models) → XGBClassifier
- **Output**: BBB+ / BBB− with probability
- **Training data**: natural and chemically modified peptides, including cyclic structures, typical MW range **100–1200 Da**

**Feature set (FC-4, 19 dimensions)**

| Group | Features |
|---|---|
| FC-1 (9 dims) | MW, TPSA, SLogP, nHBAcc, nHBDon, nN, nO, nN+nO, LogD (sub-model) |
| FC-3 (10 dims) | JGI9, nAcid, JGI5, RotRatio, JGI6, JGI7, Lipinski, EState_VSA5, GhoseFilter, GATS3d |

**Local reproduction**: GitHub model files cloned; original `.xgb` binary migrated to `.json` (xgboost ≥ 3.1 requirement); Python 3.12 + xgboost 3.2.0 + mordred 1.2.0 + NumPy 2.4.6.

---

## 3.2 Tools — BBiPP (Monash ERC)

**Status**: ❌ **Permanently offline** (verified)

**Verification**

- DNS lookup `bbipp.erc.monash.edu` → **NXDOMAIN** (domain does not exist)
- DNS lookup of parent `erc.monash.edu` → **NXDOMAIN** (entire ERC subdomain withdrawn)
- `monash.edu` and `github.com` resolve normally → rules out local network block
- No snapshots in the Wayback Machine

**Conclusion**: the Monash ERC subdomain has been removed from DNS; the server is **permanently offline**, not transiently unreachable.

**Handling**: no BBiPP results in this analysis.

---

## 4.1 BrainPepPass v2 Predictions

<div class="small">

| Compound | BBB call | P(BBB+) | MW | TPSA | SLogP | LogD (pred) | HBD | HBA | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| Setmelanotide | **BBB−** | 2.8% | 1116 | 494.8 | −2.76 | −7.14 | 17 | 14 | ✅ Reliable |
| Bremelanotide | **BBB−** | 18.3% | 1025 | 376.5 | −0.44 | −4.46 | 14 | 11 | ⚠️ Possible false negative |
| Afamelanotide | **BBB+** | 99.3% | 1646 | 643.0 | −4.10 | −10.79 | 23 | 21 | ❌ Out-of-domain false positive |
| Bivamelagon | **BBB−** | 10.2% | 628 | 73.4 | +5.39 | +3.96 | 0 | 5 | ❌ Out-of-domain (non-peptide) |
| TCMCB07 | N/A | — | structure undisclosed | — | — | — | — | — | — |
| **NN9161** | **BBB+** | **83.1%** | **2091** | **811.5** | **−4.92** | **−13.74** | **26** | **29** | **❌ Out-of-domain false positive** |

</div>

---

## 4.2 Classical Physicochemical Rule Comparison

| Compound | MW<500 | TPSA<90 Å² | HBD≤3 | cLogP 1–5 | Rule-based call |
|---|---|---|---|---|---|
| Setmelanotide | ❌ | ❌ | ❌ | ❌ | **Cannot cross (passive diffusion)** |
| Bremelanotide | ❌ | ❌ | ❌ | ✅ | **Cannot cross (passive diffusion)** |
| Afamelanotide | ❌ | ❌ | ❌ | ❌ | **Cannot cross (passive diffusion)** |
| Bivamelagon | ❌ (628) | ✅ | ✅ | ✅ | **Likely crosses** (slightly oversized but otherwise compliant) |
| **NN9161** | ❌ (2091) | ❌ (811) | ❌ (26) | ❌ | **Definitely cannot cross (passive diffusion)** |

> Classical rules and BrainPepPass agree on Setmelanotide; disagree on Afamelanotide and NN9161 (both flagged as out-of-domain false positives).

---

## 5.1 Afamelanotide false positive (BBB+ 99.3%)

**Anomaly**: Subcutaneous implant (Scenesse) acting on cutaneous MC1R, **no central indication** — yet model returns **99.3% BBB+**.

**Root cause**

- MW = 1646, TPSA = 643, HBD = 23 → physicochemical properties make passive BBB penetration **impossible**
- BrainPepPass training: predominantly small-to-medium peptides (typical MW < 1200 Da)
- Generalisation **fails** for ultra-large linear peptides above 1500 Da

**Conclusion**: model false positive; the prediction should be **ignored**.

---

## 5.2 Bremelanotide possible false negative (BBB− 18.3%)

**Anomaly**: Bremelanotide (Vyleesi) produces central pro-sexual effects after intranasal or subcutaneous dosing → indicates CNS exposure.

**Possible explanations**

1. **Receptor-mediated or active transport** across the BBB (non-passive); the model cannot capture active transport.
2. **Intranasal delivery** routes a fraction of drug through the olfactory bulb directly into the CNS, bypassing the BBB.
3. The **hypothalamic-pituitary region** has higher intrinsic BBB permeability (circumventricular organs such as the area postrema lack a tight BBB).

---

## 5.3 Bivamelagon possible false negative (BBB− 10.2%)

**Anomaly**: Oral small molecule with TPSA = 73.4, HBD = 0, LogP = 5.4 → classical rules predict ready BBB penetration.

**Root cause**

- BrainPepPass is trained **only on peptides**
- Bivamelagon as a non-peptide small molecule is **out of domain**
- The prediction is **unreliable**

**Recommendation**: use dedicated small-molecule BBB predictors instead — **B3clf, SwissADME, pkCSM**.

---

## 5.4 Setmelanotide (most reliable result)

**BBB− (2.8%)** is consistent with reality:

- Setmelanotide acts mainly through **peripheral MC4R**
- Although CNS exposure has been reported in some settings,
  - high MW (1116 Da)
  - strong polarity (TPSA = 495, HBD = 17)
  - make passive crossing **unfavourable**

**Bottom line**: the model's call here is **trustworthy**.

---

## 5.5 NN9161 false positive (BBB+ 83.1%)

**Anomaly**: SC-injected lipidated peptide (MW = 2091, TPSA = 811, HBD = 26), built with semaglutide-style C18 fatty-acid sidechain to extend half-life. Designed for **peripheral action**, yet model returns **83.1% BBB+**.

**Failure modes**

1. **MW out of training domain**: typical training MW < 1200 Da; NN9161 at 2091 Da is an extreme extrapolation.
2. **No precedent for lipidation**: C18 tetrazole fatty-acid + PEG linker absent from training; model may misread high lipophilicity as a BBB-permeation signature.
3. **Same failure pattern as Afamelanotide** (MW = 1646, BBB+ 99.3%): oversize peptides systematically called BBB+.
4. **TPSA = 811 physically incompatible**: literature BBB-permeation TPSA cutoff is ~90 Å²; 811 Å² is roughly **9× the cutoff**.

**Conclusion**: the BrainPepPass call on NN9161 has **no predictive value** and should be ignored.

---

## 6. Compounds with Undisclosed / Special Structure (1/2)

### TCMCB07

- **Type**: MC4R antagonist for cancer / chronic kidney disease cachexia
- **Structure**: not deposited in ChEMBL or PubChem
  - Design paper: Gruber et al., *ACS Pharmacol Transl Sci* 2022, PMID 35592439 — drug-like cyclic peptide
- **BBB design intent**: deliberately engineered for **peripheral action**
  - Hu et al., *J Cachexia Sarcopenia Muscle* 2020, PMID 32725770 — confirmed intestinal absorption via OATP1A2 with **no BBB crossing**

---

## 6. Compounds with Undisclosed / Special Structure (2/2)

### NN9161 (LAMA2, 0070-0002-0453)

- **Type**: Novo Nordisk MC4R agonist; lipidated peptide (~13 residues)
  - C18 fatty acid (tetrazole bioisostere) + PEG linker
- **Structure**: obtained — PubChem CID 70686774 / CAS 1228015-10-8; data file `data/nn9161.csv`
- **Measured properties** (mordred / RDKit):
  - MW = 2091 Da, TPSA = 811 Å², SLogP = −4.92
  - LogD(pred) = −13.74, HBD = 26, HBA = 29
- **BrainPepPass call**: BBB+ 83.1% — **❌ out-of-domain false positive** (see §5.5)
- **BBB design intent**: C18 fatty-acid strategy mirrors **semaglutide**, intended to prolong plasma half-life via albumin binding — **not** for CNS penetration; subcutaneous dosing acts on peripheral MC4R.

---

## 7. Recommended Follow-up

| Analysis | Tool | Target | Priority |
|---|---|---|---|
| Small-molecule BBB prediction | B3clf / SwissADME / pkCSM | Bivamelagon | **High** |
| Active-transport assessment | P-gp efflux prediction (pkCSM) | Bremelanotide | Medium |
| CNS-MPO multi-parameter score | CNS-MPO (LogP, LogD, MW, TPSA, HBD, pKa) | Setmelanotide, Bremelanotide, Bivamelagon | Medium |
| Lipidated-peptide BBB assessment | No mature *in silico* tool — rely on experiments (in situ brain perfusion, PAMPA-BBB) | NN9161 | Low (experimental) |
| Structure retrieval for TCMCB07 | Patent databases (USPTO/EPO) / Endevica Bio filings | TCMCB07 | Low |

---

## 8. References

1. Oliveira EC et al. *BrainPepPass: A framework based on supervised dimensionality reduction for predicting blood-brain barrier-penetrating peptides.* 2022.
   GitHub: [ewerton-cristhian/BrainPepPass](https://github.com/ewerton-cristhian/BrainPepPass)

2. Gruber KA et al. *Development of a Therapeutic Peptide for Cachexia Suggests a Platform Approach for Drug-like Peptides.*
   ACS Pharmacol Transl Sci 2022;5(5):344–361. **PMID 35592439**

3. Hu Y et al. *Characterization of the cellular transport mechanisms for the anti-cachexia candidate compound TCMCB07.*
   J Cachexia Sarcopenia Muscle 2020;11(6):1677–1687. **PMID 32725770**

4. Zhu X et al. *Melanocortin-4 receptor antagonist TCMCB07 ameliorates cancer- and chronic kidney disease-associated cachexia.*
   J Clin Invest 2020;130(9):4921–4934. **PMID 32544087**

---

<!-- _class: title -->

# Thank You

Questions / Discussion

`results/mc4r_bbb_predictions.csv`
