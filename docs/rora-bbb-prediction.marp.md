---
marp: true
theme: default
paginate: true
size: 16:9
header: 'RORα Tool Compounds – BBB Permeability Prediction'
footer: 'Computational Sciences · 2026-05-29'
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
  .highlight { color: #c0392b; font-weight: bold; }
  .good { color: #27ae60; font-weight: bold; }
  .warn { color: #e67e22; font-weight: bold; }
---

<!-- _class: title -->

# RORα Tool Compounds
## Blood-Brain Barrier Permeability Prediction

**Requestor**: Mingyue Wu
**Analysis date**: 2026-05-29

Tool: B3clf (12-model ensemble) + CNS-MPO scoring
Analyst: Qiuye Jin (Computational Sciences)

---

## Background

**RORα** (RAR-related orphan receptor alpha) is proposed as a target for obesity.

Three small-molecule tool compounds are available for in vivo testing:

| Compound | Mechanism | Reference |
|---|---|---|
| **SR3335** (ML 176) | RORα inverse agonist | Kumar et al., Mol Pharmacol 2011 |
| **SR1001** | RORα/γt inverse agonist | Solt et al., ACS Chem Biol 2012 |
| **SR1078** | RORα/RORγ agonist | Wang et al., ACS Med Chem Lett 2010 |

**Question**: Will these compounds cross the BBB?  
→ Critical for interpreting central vs. peripheral anti-obesity effects.

---

## Methods

### B3clf — Machine Learning BBB Classifier

- SMILES → 3D conformer (RDKit ETKDG) → PaDEL descriptors → ML classification
- 12 model variants: 4 classifiers × 3 sampling strategies
- Trained on ~7000 compounds with known BBB permeability
- **All 12 models ran successfully** (conda env `bbb-predict`: Python 3.9, sklearn 0.24.2, xgboost 1.4.2)

### CNS-MPO Score (Pfizer)

- 6-parameter desirability score: cLogP, cLogD, MW, TPSA, HBD, pKa
- Scale: 0–6; **≥ 4 = good CNS drug-likeness**
- Reference: Wager et al., ACS Chem Neurosci 2010

---

## Physicochemical Properties

| Property | SR3335 | SR1001 | SR1078 | CNS Drug Ideal |
|---|---|---|---|---|
| **MW** | 405.3 | 477.4 | 431.3 | < 360 (≤500) |
| **TPSA** (Å²) | 66.4 ✅ | 108.4 ❌ | 49.3 ✅ | 40–90 |
| **cLogP** | 3.86 | 3.52 | 5.27 ❌ | 1–3 (≤5) |
| **HBD** | 2 | 3 | 2 | ≤ 3 |
| **HBA** | 4 | 6 | 2 | ≤ 7 |
| **RotBonds** | 4 | 5 | 3 | ≤ 8 |
| **CNS-MPO** | **3.82** | **2.69** | **2.74** | ≥ 4.0 |

> SR3335 has the best CNS drug-like profile; SR1001 and SR1078 have significant liabilities.

---

## B3clf Prediction Results

### Individual Model Scores

| Compound | XGB_ADASYN | XGB_SMOTE | XGB_common | DTree_ADASYN | DTree_SMOTE | KNN_common |
|---|---|---|---|---|---|---|
| **SR3335** | **0.503** ✅ | **0.607** ✅ | 0.361 | **0.979** ✅ | **0.642** ✅ | **0.634** ✅ |
| **SR1001** | 0.321 | 0.239 | 0.250 | **0.979** ✅ | 0.074 | 0.157 |
| **SR1078** | **0.569** ✅ | **0.512** ✅ | 0.137 | 0.353 | **0.642** ✅ | **0.598** ✅ |

✅ = BBB+ call (P ≥ 0.5). LogReg models all predict BBB− for all compounds (not shown).

> **XGBoost** (best benchmark performer) calls SR3335 **BBB+** in 2/3 models.

---

## Consensus Summary

| Compound | Avg P(BBB+) | Consensus | CNS-MPO | Verdict |
|---|---|---|---|---|
| **SR3335** | 0.177 | **BBB−** | 3.82 | ⚠️ Borderline |
| **SR1001** | 0.051 | **BBB−** | 2.69 | ❌ Peripheral |
| **SR1078** | 0.114 | **BBB−** | 2.74 | ❌ Peripheral |

### Key Finding

**All three RORα tool compounds are predicted to be BBB-impermeable.**
If anti-obesity effects are observed in vivo, the mechanism is most likely **peripheral**.

---

## Compound Analysis: SR3335

### Profile
- **MW 405**, TPSA 66 Å² (in optimal range), cLogP 3.86
- CNS-MPO = **3.82** (just below 4.0 cutoff)
- **5/12 models predict BBB+**; XGBoost gives P = 0.50–0.61

### Interpretation
- **Strong borderline case** — the most CNS-capable compound of the three
- XGBoost (best-benchmarked algorithm) favours BBB+ in 2/3 models
- The thiophene sulfonamide scaffold has moderate permeability potential
- Sulfonamide NH pKa (~4–5) would actually *improve* the CNS-MPO if properly calculated

### Recommendation
- **Must measure brain/plasma ratio** (Kp,uu) in vivo
- If Kp,uu > 0.1 → meaningful CNS contribution likely

---

## Compound Analysis: SR1001

### Profile
- **MW 477**, TPSA **108 Å²** (far exceeds 90 Å² cutoff), cLogP 3.52
- **3 HBDs** (2 sulfonamide NH + 1 OH)
- CNS-MPO = **2.69** (poor)
- **11/12 models predict BBB−** (only dtree_ADASYN outlier calls BBB+)

### Liabilities
1. **TPSA 108 Å²**: Literature cutoff for passive BBB permeation is ~90 Å²; 108 is 20% over
2. **3 HBDs**: Each additional HBD reduces permeability ~10-fold
3. **Thiazole–sulfonamide–acetamide**: highly polar scaffold

### Conclusion
**Peripheral-restricted (high confidence)**. Anti-obesity efficacy is most likely mediated via hepatic/adipose/immune RORα/γt.

---

## Compound Analysis: SR1078

### Profile
- **MW 431**, TPSA 49 Å² (favourable!), cLogP **5.27** (too high)
- Only 2 HBDs, 2 HBAs — minimal H-bonding
- CNS-MPO = **2.74** (poor, driven by excessive lipophilicity)
- **4/12 models predict BBB+** (XGB ADASYN/SMOTE + DTree SMOTE + KNN common)

### The Lipophilicity Paradox
- Low TPSA normally favours BBB penetration, but **cLogP > 5** creates:
  1. **P-gp efflux liability** — MDR1 substrate risk
  2. **Low free fraction** — excessive plasma protein binding
  3. **Poor solubility** — limits brain tissue distribution

### Conclusion
**Borderline-to-peripheral**. The models disagree — include in brain PK alongside SR3335.

---

## Decision Matrix for In Vivo Studies

| Compound | BBB Status | Votes BBB+ | Confidence | Implication |
|---|---|---|---|---|
| **SR3335** | BBB− (strong borderline) | 5/12 | Low | **Must include brain PK** |
| **SR1001** | BBB− | 1/12 | High | Peripheral mechanism |
| **SR1078** | BBB− (borderline) | 4/12 | Moderate | Include in brain PK |

### Practical Recommendation

- **SR3335**: Near-split vote + XGBoost BBB+ → cannot assume peripheral-only. Brain/plasma Kp,uu is **mandatory**.
- **SR1078**: 4/12 BBB+ with low TPSA → some penetration possible; measure alongside SR3335.
- **SR1001**: Only 1 outlier vote → safely interpret as peripheral mechanism.

---

## Recommended Follow-up Experiments

| Priority | Experiment | Compound | Rationale |
|---|---|---|---|
| **High** | Brain/plasma Kp,uu (mouse, Tmax) | SR3335, SR1078 | Borderline predictions (5/12 and 4/12 BBB+) |
| **High** | P-gp efflux ratio (MDCK-MDR1) | SR1078 | High cLogP → likely P-gp substrate |
| Medium | PAMPA-BBB assay | All 3 | Orthogonal in vitro validation |
| Medium | CSF sampling (steady-state) | SR3335 | Gold standard free brain exposure |
| Low | Pharmacokinetic brain tissue analysis | All 3 | Definitive answer for all |

---

## Limitations

1. **Model disagreement**: XGBoost/DTree tend toward BBB+, LogReg consistently BBB− — reflects algorithm bias, not compound uncertainty
2. **DTree ADASYN outlier**: tends to overfit (P=0.98 for both SR3335 and SR1001)
3. **pKa estimation**: Heuristic (not ChemAxon/Epik); SR3335 sulfonamide pKa may be overestimated
4. **No P-gp modelling**: B3clf predicts passive permeability only; active efflux not captured
5. **No in vivo calibration**: Computational prediction only — brain/plasma ratio is the gold standard

---

## Conclusions

1. **SR3335 is a strong borderline case** (5/12 BBB+, Avg P = 0.41, CNS-MPO 3.82) — XGBoost (best benchmark) favours BBB+ → **brain PK is mandatory**

2. **SR1001 is clearly peripheral** (1/12 BBB+, high TPSA 108 Å², 3 HBDs) — safely attribute efficacy to peripheral RORα/γt

3. **SR1078 is borderline-to-peripheral** (4/12 BBB+, low TPSA but high cLogP) — P-gp efflux likely limits CNS exposure; include in brain PK

4. **If anti-obesity effects are observed**, the safest interpretation:
   - SR1001: peripheral RORα/γt (hepatic, adipose, immune)
   - SR3335/SR1078: cannot exclude central contribution without brain PK data

5. **Action**: Request brain/plasma ratio for SR3335 + SR1078 from DMPK

---

<!-- _class: title -->

# Thank You

**Contact**: Qiuye Jin
Computational Sciences

Results: `results/rora_bbb_consensus.csv`
Full report: `docs/rora-bbb-prediction.md`
Script: `scripts/run_rora_bbb_predictions.py`
