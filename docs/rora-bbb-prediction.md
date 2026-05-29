# RORα Tool Compounds – Blood-Brain Barrier Permeability Prediction Report

> **Analysis date**: 2026-05-29  
> **Requestor**: Mingyue Wu  
> **Target**: RORα (RAR-related orphan receptor alpha), proposed for obesity  
> **Tool**: B3clf (12-model ensemble) + CNS-MPO scoring  
> **Result files**: `results/rora_bbb_predictions.csv`, `results/rora_bbb_consensus.csv`

---

## 1. Background and Objective

**RORα** (RAR-related orphan receptor alpha) has been proposed as a therapeutic target for obesity. Three small-molecule tool compounds are available for in vivo testing. Understanding their BBB penetration profiles is critical for interpreting whether observed effects are centrally or peripherally mediated.

This analysis predicts BBB permeability for three RORα modulators using:
- **B3clf**: a validated machine learning classifier trained on ~7000 compounds with 12 model variants (4 algorithms × 3 sampling strategies)
- **CNS-MPO** (CNS Multi-Parameter Optimization): a Pfizer-developed desirability score (0–6, ≥4 desirable for CNS drugs)

---

## 2. Target Compounds

| Compound | Type | Mechanism | Source |
|---|---|---|---|
| **SR3335** (ML 176) | Small molecule | RORα inverse agonist | [MedChemExpress](https://www.medchemexpress.com/SR3335.html) |
| **SR1001** | Small molecule | RORα/γt inverse agonist | [MedChemExpress](https://www.medchemexpress.com/SR1001.html) |
| **SR1078** | Small molecule | RORα/RORγ agonist | [MedChemExpress](https://www.medchemexpress.com/SR1078.html) |

### SMILES

| Compound | SMILES |
|---|---|
| SR3335 | `O=S(C1=CC=CS1)(NC2=CC=C(C(C(F)(F)F)(C(F)(F)F)O)C=C2)=O` |
| SR1001 | `CC(NC1=NC(C)=C(S(=O)(NC2=CC=C(C(C(F)(F)F)(O)C(F)(F)F)C=C2)=O)S1)=O` |
| SR1078 | `O=C(NC1=CC=C(C(C(F)(F)F)(C(F)(F)F)O)C=C1)C2=CC=C(C(F)(F)F)C=C2` |

---

## 3. Methods

### 3.1 B3clf

- **Reference**: Fadel M et al. *J Chem Inf Model* 2024
- **Principle**: SMILES → 3D conformer (RDKit ETKDG) → PaDEL descriptors → ML classification
- **Model variants**: 4 classifiers (XGBoost, LogReg, DecisionTree, KNN) × 3 sampling strategies (ADASYN, SMOTE, common) = **12 models**
- **Output**: Binary label (BBB+/BBB−) with probability
- **Environment**: `bbb-predict` conda env (Python 3.9.23, sklearn 0.24.2, xgboost 1.4.2) — all 12 models loaded successfully

### 3.2 CNS-MPO Score

- **Reference**: Wager TT et al. *ACS Chem Neurosci* 2010;1(6):420-434
- **Components** (6 parameters, each scored 0–1):
  - cLogP (desirable ≤ 3)
  - cLogD (desirable ≤ 2)
  - MW (desirable ≤ 360)
  - TPSA (desirable 40–90 Å²)
  - HBD (desirable ≤ 0.5)
  - pKa (desirable ≤ 8)
- **Interpretation**: ≥ 4.0 = good CNS drug-likeness; < 3.0 = poor CNS drug-likeness

---

## 4. Physicochemical Properties

| Compound | MW | TPSA (Å²) | cLogP | HBD | HBA | RotBonds | cLogD (est) | pKa (est) | CNS-MPO |
|---|---|---|---|---|---|---|---|---|---|
| **SR3335** | 405.3 | 66.4 | 3.86 | 2 | 4 | 4 | 3.36 | 8.5 | **3.82** |
| **SR1001** | 477.4 | 108.4 | 3.52 | 3 | 6 | 5 | 3.02 | 8.5 | **2.69** |
| **SR1078** | 431.3 | 49.3 | 5.27 | 2 | 2 | 3 | 4.77 | 8.5 | **2.74** |

### Key observations:
- **SR3335**: MW slightly above 360, TPSA in optimal range (66 Å²), moderate lipophilicity → best CNS-MPO of the three
- **SR1001**: TPSA far exceeds 90 Å² cutoff (108 Å²), 3 HBDs, MW close to 500 → poor CNS penetration expected
- **SR1078**: Highly lipophilic (cLogP 5.27), low TPSA but likely P-gp efflux substrate → poor BBB penetration despite favourable TPSA

---

## 5. B3clf Prediction Results

### 5.1 Individual Model Predictions

| Compound | Model | P(BBB+) | Label |
|---|---|---|---|
| SR3335 | xgb_classic_ADASYN | 0.5030 | **BBB+** |
| SR3335 | xgb_classic_SMOTE | 0.6065 | **BBB+** |
| SR3335 | xgb_common | 0.3607 | BBB- |
| SR3335 | logreg_classic_ADASYN | 0.2032 | BBB- |
| SR3335 | logreg_classic_SMOTE | 0.0029 | BBB- |
| SR3335 | logreg_common | 0.0684 | BBB- |
| SR3335 | dtree_classic_ADASYN | 0.9787 | **BBB+** |
| SR3335 | dtree_classic_SMOTE | 0.6417 | **BBB+** |
| SR3335 | dtree_common | 0.1639 | BBB- |
| SR3335 | knn_classic_ADASYN | 0.3375 | BBB- |
| SR3335 | knn_classic_SMOTE | 0.4332 | BBB- |
| SR3335 | knn_common | 0.6343 | **BBB+** |
| SR1001 | xgb_classic_ADASYN | 0.3207 | BBB- |
| SR1001 | xgb_classic_SMOTE | 0.2386 | BBB- |
| SR1001 | xgb_common | 0.2496 | BBB- |
| SR1001 | logreg_classic_ADASYN | 0.1333 | BBB- |
| SR1001 | logreg_classic_SMOTE | 0.0008 | BBB- |
| SR1001 | logreg_common | 0.0306 | BBB- |
| SR1001 | dtree_classic_ADASYN | 0.9787 | **BBB+** |
| SR1001 | dtree_classic_SMOTE | 0.0741 | BBB- |
| SR1001 | dtree_common | 0.1639 | BBB- |
| SR1001 | knn_classic_ADASYN | 0.0497 | BBB- |
| SR1001 | knn_classic_SMOTE | 0.0395 | BBB- |
| SR1001 | knn_common | 0.1570 | BBB- |
| SR1078 | xgb_classic_ADASYN | 0.5693 | **BBB+** |
| SR1078 | xgb_classic_SMOTE | 0.5120 | **BBB+** |
| SR1078 | xgb_common | 0.1370 | BBB- |
| SR1078 | logreg_classic_ADASYN | 0.0171 | BBB- |
| SR1078 | logreg_classic_SMOTE | 0.0010 | BBB- |
| SR1078 | logreg_common | 0.0104 | BBB- |
| SR1078 | dtree_classic_ADASYN | 0.3529 | BBB- |
| SR1078 | dtree_classic_SMOTE | 0.6417 | **BBB+** |
| SR1078 | dtree_common | 0.1639 | BBB- |
| SR1078 | knn_classic_ADASYN | 0.3002 | BBB- |
| SR1078 | knn_classic_SMOTE | 0.4384 | BBB- |
| SR1078 | knn_common | 0.5976 | **BBB+** |

### 5.2 Consensus Results (12-model vote)

| Compound | Avg P(BBB+) | Votes BBB+ | Consensus | CNS-MPO | Interpretation |
|---|---|---|---|---|---|
| **SR3335** | **0.411** | **5/12** | **BBB−** (borderline) | 3.82 | Strong borderline — in vivo PK confirmation essential |
| **SR1001** | 0.203 | 1/12 | **BBB−** | 2.69 | Likely peripheral-restricted |
| **SR1078** | 0.312 | 4/12 | **BBB−** | 2.74 | Borderline-to-peripheral |

---

## 6. Interpretation and Recommendations

### 6.1 SR3335 (ML 176) — Strong Borderline

- **B3clf consensus**: BBB− by narrow margin (5/12 BBB+, Avg P = **0.411**)
- XGBoost (best-benchmarked algorithm): 2/3 models predict **BBB+** (P = 0.50, 0.61)
- DTree ADASYN: P = 0.98 (BBB+); KNN_common: P = 0.63 (BBB+)
- **CNS-MPO 3.82**: just below the 4.0 threshold — the compound has reasonable MW, good TPSA, moderate lipophilicity
- **Recommendation**: **Cannot rule out CNS exposure**. Given XGBoost's superior benchmark accuracy and the near-split vote, SR3335 may well cross the BBB. **Brain PK measurement is essential** before interpreting in vivo efficacy as purely peripheral.

### 6.2 SR1001 — Likely Peripheral

- **B3clf consensus**: BBB− (11/12 models, Avg P = 0.203)
- Only dtree_ADASYN calls BBB+ (P = 0.98, likely an outlier — this model tends to overfit)
- **Key liabilities**: TPSA = 108.4 Å² (far above 90 Å² cutoff), 3 HBDs, MW = 477
- **Recommendation**: **Peripheral-restricted with high confidence**. Any anti-obesity effect observed with SR1001 is most likely mediated through peripheral RORα/γt modulation (e.g., hepatic, adipose, immune).

### 6.3 SR1078 — Borderline-to-Peripheral

- **B3clf consensus**: BBB− (8/12 models, Avg P = 0.312), but 4/12 call BBB+
- XGBoost ADASYN/SMOTE both predict BBB+ (P = 0.57, 0.51); DTree SMOTE and KNN_common also BBB+
- **Key liabilities**: cLogP = 5.27 → high lipophilicity paradox (increases P-gp efflux liability, reduces free fraction)
- **Recommendation**: **Borderline-to-peripheral**. Low TPSA (49 Å²) favours passive permeation, but excessive lipophilicity likely triggers P-gp efflux. If brain PK is measured for SR3335, include SR1078 as well.

### 6.4 Summary Decision Table

| Compound | BBB Prediction | Votes BBB+ | Confidence | Action for In Vivo Studies |
|---|---|---|---|---|
| SR3335 | BBB− (strong borderline) | 5/12 | Low (near-split) | **Must measure Kp,uu brain/plasma** |
| SR1001 | BBB− | 1/12 | High | Interpret as peripheral mechanism |
| SR1078 | BBB− (borderline) | 4/12 | Moderate | Measure brain PK alongside SR3335 |

---

## 7. Experimental Follow-up Suggestions

| Priority | Experiment | Rationale |
|---|---|---|
| **High** | Brain/plasma ratio for SR3335 (mouse, LC-MS/MS, Tmax) | Borderline prediction; confirm CNS exposure |
| Medium | P-gp efflux assay (Caco-2 or MDCK-MDR1) for SR1078 | High cLogP suggests P-gp liability |
| Medium | PAMPA-BBB assay (all 3 compounds) | Orthogonal in vitro confirmation |
| Low | CSF sampling after SR3335 dosing | Gold standard CNS exposure measurement |

---

## 8. Limitations

1. **pKa estimation**: Basic pKa was estimated heuristically (not calculated with Epik/ChemAxon). For SR3335 (sulfonamide NH), the actual pKa may be lower (~4–5 for sulfonamide), which would improve CNS-MPO.
2. **P-gp efflux not modelled**: B3clf predicts passive permeability; active efflux by P-gp (MDR1) is not captured. SR1078's high lipophilicity is a known P-gp substrate flag.
3. **DTree ADASYN outlier tendency**: dtree_classic_ADASYN tends to produce high-probability outlier calls (e.g., P = 0.98 for both SR3335 and SR1001); this model may overfit.
4. **No in vivo calibration**: Predictions are purely computational. In vivo brain/plasma ratios are the gold standard.

---

## 9. References

1. Fadel M et al. *B3clf: A machine learning tool for blood-brain barrier permeability prediction.* J Chem Inf Model. 2024.
2. Wager TT et al. *Moving beyond rules: The development of a central nervous system multiparameter optimization (CNS MPO) approach to enable alignment of druglike properties.* ACS Chem Neurosci. 2010;1(6):420-434.
3. Pajouhesh H, Lenz GR. *Medicinal chemical properties of successful central nervous system drugs.* NeuroRx. 2005;2(4):541-553.
4. Kumar TRS et al. *SR3335 (ML 176): an RORα inverse agonist.* Mol Pharmacol. 2011.
5. Solt LA et al. *Identification of a selective RORα/γt dual inverse agonist (SR1001).* ACS Chem Biol. 2012.

---

*Report generated: 2026-05-29 | Analyst: Qiuye Jin (Computational Sciences)*
