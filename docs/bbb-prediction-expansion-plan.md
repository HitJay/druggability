# BBB Permeability Prediction — Expansion Plan

> Response to: Jiansheng Huang (2026-05-28)  
> Author: Qiuye Jin (Jay)  
> Status: Draft Plan

---

## Summary of Requests

| # | Request | Scope |
|---|---------|-------|
| 1 | Validate BrainPepPass/BBiPP results with additional DL models; expand peptide MW coverage from 1200→2000+ Da | Peptide BBB prediction |
| 2 | Find robust analysis tools for **small molecule** BBB permeability | SM BBB prediction |
| 3 | Incorporate more CNS/food-intake-regulating peptides & validated SM as benchmark compounds | Validation dataset |

---

## 1. Deep Learning Models for Peptide BBB Prediction (MW up to 2000+ Da)

### Current Limitations
- **BrainPepPass v2**: Training set MW typically <1200 Da; produces false positives for peptides >1500 Da (afamelanotide 99.3%, NN9161 83.1%)
- **BBiPP**: Server permanently offline (Monash ERC domain decommissioned)

### Proposed Additional Models

| Model | Architecture | MW Range | Reference | Access |
|-------|-------------|----------|-----------|--------|
| **DeepB3P** | Transformer + Feedback GAN (data augmentation) | Sequence-based, no explicit MW limit; trained on all known BBBPs | Tang & Chen, *J Adv Res* 2025;73:459-468 (PMID 39111628) | Web: http://cbcb.cdutcm.edu.cn/deepb3p/ (status TBD); Code: request from authors |
| **DeepB3Pred** | Stacked BiGRU + novel sequence features | Sequence-based; supports longer peptides | Arif et al., *BMC Biol* 2025;23:325 (PMID 41162940) | Code: available with paper |
| **ESM-BBB-Pred** | Fine-tuned ESM-2 (protein language model) + DNN | **No MW cap** — uses PLM embeddings from amino acid sequences | Naseem et al., *Brief Bioinform* 2024;26(1):bbaf066 (PMID 39987496) | Code: with publication |
| **BBBpPred (Augur)** | Data augmentation + ensemble | Sequence-based, accommodates diverse peptide lengths | Gu et al., *BMC Biol* 2024;22:86 (PMID 38637801) | Web + code available |
| **Masked Peptide Transformer** | Transformer with dynamic routing | Sequence-based | Ma & Wolfinger, *Brief Bioinform* 2023;24(6):bbad399 (PMID 37985456) | Code available |

### Key Advantage of Sequence-Based (PLM) Models
- **ESM-BBB-Pred** uses ESM-2 embeddings — the representation is learned from ~250M protein sequences and captures structural/biophysical properties implicitly
- No hard MW cutoff because features are derived from amino acid sequence, not physicochemical descriptors with training-set bias
- Particularly suitable for cyclic peptides & lipidated peptides (NN9161 MW ~2200 Da) when combined with descriptor-based models for cross-validation

### Implementation Priority
1. **ESM-BBB-Pred** — Most promising for >1200 Da peptides; PLM embeddings handle diverse peptide architectures
2. **DeepB3P** — Transformer-based, best-performing on benchmarks (outperforms prior models by ~9% MCC)
3. **DeepB3Pred** — BiGRU complement for ensemble consensus

### Caveats for MW 1200–2000+ Da
- All models are trained primarily on peptides 2–50 amino acids (typical MW 200–5000+ Da depending on modifications)
- Lipidated peptides (NN9161) with non-natural moieties (PEG, C18 tetrazole fatty acid) are **not represented in any training set** — all predictions for heavily modified peptides should be flagged as extrapolation
- Consensus across ≥3 models provides more confidence than any single tool

---

## 2. Small Molecule BBB Permeability Prediction Tools

### Recommended Tools

| Tool | Method | Training Data | Features | Access |
|------|--------|---------------|----------|--------|
| **B3clf** | XGBoost + 6 resampling strategies | B3DB (7,807 SM, largest curated dataset) | PaDEL descriptors; CLI + Python API | `pip install b3clf`; GitHub: theochem/B3clf; HuggingFace: QCDevs/b3clf |
| **SwissADME** | Rule-based + BOILED-Egg (WLOGP/TPSA plot) | ChEMBL-derived | TPSA, LogP, MW, HBD, HBA, P-gp | http://www.swissadme.ch (free web) |
| **pkCSM** | Graph-based signatures | Multi-source curated | BBB logBB + P-gp substrate/inhibitor + CNS penetration | http://biosig.lab.uq.edu.au/pkcsm/ |
| **ADMETlab 3.0** | Multi-task DNN (GNN + descriptors) | Aggregated ADMET data | BBB, P-gp, CNS-MPO, HIA, Pgp efflux | https://admetlab3.scbdd.com/ |
| **CNS-MPO Score** | Multi-parameter optimization (6-dim) | Pfizer internal → published rules | LogP, LogD, MW, TPSA, HBD, pKa | Implementable locally (simple formula) |

### Implementation Plan for Bivamelagon (SM MC4R agonist)
```
Priority:  B3clf (local, reproducible) → SwissADME → pkCSM → ADMETlab 3.0
Outputs:   BBB+/- classification, P(BBB+), logBB estimate, P-gp efflux risk, CNS-MPO score
```

B3clf is the preferred primary tool because:
- Open-source, locally executable (reproducibility)
- Based on B3DB — the largest curated BBB dataset (7,807+ compounds)
- Supports multiple classifiers/resampling for robustness testing

---

## 3. Expanded Benchmark Compound Set

### 3.1 Additional CNS/Food-Intake Peptides

| Peptide | Type | MW (Da) | CNS/Food Intake Role | BBB Status (Literature) |
|---------|------|---------|---------------------|------------------------|
| α-MSH (α-melanocyte-stimulating hormone) | Linear peptide (13 aa) | 1665 | MC3R/MC4R agonist; appetite suppression | Partial CNS entry via circumventricular organs |
| ACTH(1-24) (cosyntropin) | Linear peptide (24 aa) | 2933 | MC2R; stress/feeding regulation | Does not cross BBB |
| Liraglutide | Lipidated peptide (GLP-1 analogue) | 3751 | GLP-1R; weight loss/CNS satiety | Crosses BBB (demonstrated in rodent studies) |
| Semaglutide | Lipidated peptide (GLP-1 analogue) | 4114 | GLP-1R; weight loss/CNS satiety | Evidence of CNS access (NTS/hypothalamus) |
| Tirzepatide | Lipidated peptide (GIP/GLP-1) | 4814 | GIP/GLP-1R dual agonist; weight loss | CNS access evidence emerging |
| Oxytocin | Cyclic peptide (9 aa) | 1007 | Feeding behavior, social bonding | Minimal passive BBB penetration; intranasal delivery |
| NPY (neuropeptide Y) | Linear peptide (36 aa) | 4272 | Potent orexigenic (stimulates food intake) | Endogenous CNS peptide; exogenous does not cross |
| AgRP(83-132) | Linear peptide (50 aa) | 5936 | MC3R/MC4R antagonist; orexigenic | Endogenous CNS; exogenous unlikely to cross |
| CCK-8 (cholecystokinin octapeptide) | Linear peptide (8 aa) | 1143 | Satiety signal; CCK1R/CCK2R | Limited BBB penetration |
| Ghrelin | Linear peptide (28 aa) | 3371 | GHS-R1a; orexigenic | Crosses BBB (saturable transport) |
| Leptin | Protein (167 aa) | 16,000 | LepR; appetite suppression | BBB transport via LepR (saturable) |
| Exendin-4 (exenatide) | Linear peptide (39 aa) | 4187 | GLP-1R; appetite/glucose | Partial BBB penetration |

### 3.2 Additional Validated Small Molecules

| Compound | MW (Da) | Target/MoA | BBB Status | Reference |
|----------|---------|-----------|------------|-----------|
| Lorcaserin | 196 | 5-HT2C agonist; appetite suppression (withdrawn) | BBB+ (CNS drug) | FDA label |
| Naltrexone | 341 | Opioid antagonist (in Contrave®) | BBB+ | FDA label |
| Bupropion | 240 | NDRI (in Contrave®) | BBB+ | FDA label |
| Topiramate | 339 | Multi-target (in Qsymia®) | BBB+ | FDA label |
| Phentermine | 149 | NE/DA releaser (in Qsymia®) | BBB+ | FDA label |
| Orlistat | 496 | Pancreatic lipase inhibitor (peripheral) | BBB− | FDA label |
| Diazoxide choline (DCCR) | 247 | KATP channel opener | BBB? (likely peripheral) | Phase 3 |
| Celastrol | 451 | Leptin sensitizer | BBB+ (in vitro/rodent) | Literature |
| MK-0493 | ~530 | MC4R agonist (Merck, discontinued) | BBB+ (oral CNS-active) | Merck publications |
| GSK-598809 | 397 | DRD3 antagonist (binge eating) | BBB+ (PET tracer data) | GSK publications |

### 3.3 Validation Strategy
1. Assemble SMILES + known BBB status for all compounds above
2. Run each peptide through: BrainPepPass v2, ESM-BBB-Pred, DeepB3P, DeepB3Pred
3. Run each SM through: B3clf, SwissADME BOILED-Egg, pkCSM, CNS-MPO
4. Compute confusion matrix for each tool vs. known literature BBB status
5. Report sensitivity, specificity, MCC, and identify MW/structural ranges where each tool is reliable

---

## 4. Implementation Timeline (Proposed)

| Phase | Tasks | Deliverable |
|-------|-------|-------------|
| **Phase 1** (1-2 weeks) | Set up B3clf locally; run Bivamelagon + validation SM set; compute CNS-MPO scores | SM BBB prediction report |
| **Phase 2** (2-3 weeks) | Deploy ESM-BBB-Pred + DeepB3P; run MC4R peptides + expanded peptide set | Peptide BBB consensus predictions |
| **Phase 3** (1 week) | Cross-model validation; confusion matrix; identify reliable MW ranges | Benchmarking report with recommendations |

---

## 5. Key Limitations & Honest Assessment

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| No peptide BBB model validated at MW >2000 Da | NN9161 predictions remain uncertain | Flag as extrapolation; prioritize experimental validation |
| Lipidated/PEGylated peptides absent from all training sets | All models likely unreliable for NN9161 | Explicit domain-of-applicability check; consensus approach |
| Active transport not modeled | May miss receptor-mediated transcytosis (e.g., ghrelin, leptin) | Note transport mechanism in report |
| BBiPP permanently offline | Cannot validate against 2nd established tool | Replaced by sequence-based DL models (better coverage) |

---

## 6. Action Items

- [ ] Obtain/deploy ESM-BBB-Pred code (from PMID 39987496 supplementary)
- [ ] Test DeepB3P webserver availability; if offline, request code from authors
- [ ] Install B3clf (`pip install b3clf`) and validate with known SM
- [ ] Curate expanded peptide SMILES/sequences (Table 3.1)
- [ ] Curate expanded SM SMILES (Table 3.2)
- [ ] Implement CNS-MPO scoring function locally
- [ ] Run Phase 1 predictions → share preliminary results with Jiansheng

---

## References

1. Tang Q, Chen W. *DeepB3P: A transformer-based model for identifying BBB penetrating peptides with data augmentation using feedback GAN.* J Adv Res. 2025;73:459-468. PMID 39111628
2. Arif M, Musleh S, Alam T. *DeepB3Pred: blood-brain barrier peptide predictor using stacked BiGRU model with novel features.* BMC Biol. 2025;23(1):325. PMID 41162940
3. Naseem A, et al. *ESM-BBB-Pred: a fine-tuned ESM 2.0 and deep neural networks for the identification of blood-brain barrier peptides.* Brief Bioinform. 2024;26(1):bbaf066. PMID 39987496
4. Gu ZF, et al. *Prediction of blood-brain barrier penetrating peptides based on data augmentation with Augur.* BMC Biol. 2024;22(1):86. PMID 38637801
5. Ma C, Wolfinger R. *A prediction model for blood-brain barrier penetrating peptides based on masked peptide transformers with dynamic routing.* Brief Bioinform. 2023;24(6):bbad399. PMID 37985456
6. Meng F, et al. *A curated diverse molecular database of blood-brain barrier permeability with chemical descriptors (B3DB).* Sci Data. 2021;8:289.
7. Meng F, et al. *B3clf: Predictors for Blood-Brain Barrier Permeability with resampling strategies.* GitHub: theochem/B3clf
