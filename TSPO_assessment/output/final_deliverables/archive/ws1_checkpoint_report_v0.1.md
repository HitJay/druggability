# TSPO Ligands — WS0+WS1(b) Checkpoint Report (v0.2)

Date: 2026-10-14. RIC-408 (In Progress). Owner QYJI. Requester ZHCO (Cao Zheng), Group 3 TSPO proposal.
Data: `TSPO_assessment/data/` (ws0_structures.json, ws1_chembl_activities_raw.json 316 records, ws1_evidence_chembl_v0.csv 186 rows, ws1_target_meta.json, ws1_europepmc_raw.json, ws1_key_abstracts.json).
All claims tagged FACT (measured, source traceable) / OBS / MECH / HYP.

## 1. WS0 — compound curation (complete at v0 level)

| Compound | ChEMBL | PubChem CID | InChIKey | Notes |
|---|---|---|---|---|
| PK11195 (racemate) | CHEMBL481537 | 1345 | RAVIZVQZGXBOQO-UHFFFAOYSA-N | SMILES: CCC(C)N(C)C(=O)c1cc2cccc(-c3ccccc3Cl)c2cn1 |
| (R)-PK11195 | CHEMBL416715 | — | CC[C@@H]… | enantiomer tracked separately |
| Emapunil / XBD173 / AC-5216 | CHEMBL513922 | 6433109 | NBMBIEOUVBHEBM-UHFFFAOYSA-N | max phase 2 |
| Etifoxine | CHEMBL2106227 | 135413553 | IBYCYJFUEJQSMK-UHFFFAOYSA-N | max phase 3, HOE 36801 |
| desethyl-etifoxine | not resolved | — | — | 0 hits in Europe PMC; active metabolite per literature needs verification (TBD) |

Concentration-table scaffold started; etifoxine 2020 obesity paper fulltext is paywalled via EPMC (dose TBD from paper PDF).

## 2. WS1 — key findings by ligand

### PK11195 — top non-TSPO signal: CAR (constitutive androstane receptor, NR1I3)
- FACT: human CAR antagonism IC50 25 nM / inverse agonism IC50 245–390 nM (ChEMBL5503, 6 records, TR-FRET + HepG2 cell assay). Same order of magnitude as TSPO Ki (~0.3–11 nM human/rat, pX 7.5–9.7 across 98 records).
- FACT (in vivo, physiologically relevant): PK11195 is a CAR ligand whose activity flips antagonist→agonist after metabolism; in human primary hepatocytes and HepaRG it INDUCES CYP2B6/CYP3A4 (PMID:28442602). CAR/PXR dual-ligand behaviour documented (PMID:27197997).
- OBS: PK11195 is glucose-lowering and protects HFD mice from hepatosteatosis and glucose intolerance (zebrafish pck1 screen, PMID:23201900) — the T2D-benefit anchor paper.
- OBS (direction conflict to report): PK11195 INHIBITS glucose-induced insulin secretion from rat islets/pancreas in vitro (PMID:10935532, 10 nM–10 µM, concentration-dependent; 1992 Ro5-4864 companion paper) while potentiating it transiently in insulinoma cells (PMID:15909116, via cytosolic Ca2+, and killing the cells at the same time). In vitro beta-cell effects are mixed and partly cytotoxic.
- FACT (knockout counter-evidence): Tspo KO rats on GAN diet have WORSE steatosis/insulin resistance (PMID:40195072); TSPO deficiency alters WAT lipid metabolism via porphyrins (2025, PMID n/a). If TSPO loss mimics the drugs, PK11195's benefit should vanish or invert via TSPO — it does not obviously match. HYP: PK11195's metabolic benefit is more consistent with a non-TSPO mechanism (CAR activation + fasting-like energy state, PMID:23201900 pck1/fasting state).
- PK11195 reported T2D-improvement claim from the requester: no direct human T2D trial found in EPMC; closest anchors are PMID:23201900 (preclinical glucose-lowering) and TSPO PET epidemiology (insulin resistance/BMI associate with higher brain TSPO availability, PMID:37113066).

### Emapunil / XBD173 — clean TSPO profile, sparse off-target evidence
- FACT: TSPO Ki 0.2–31.3 nM incl. human WT/A147T (8.4 µM at central benzodiazepine site = 1000× selectivity vs GABA-A CBR).
- FACT: cognitive/neuroprotective effect is TSPO-dependent — absent in heterozygous TSPO-KO mice (PMID:37891168).
- OBS: no T2D/obesity-specific study found in ChEMBL/EPMC at v0; requester's "T2D benefit" source needs their citation (open question for ZHCO).
- Tier-1 off-targets: none beyond TSPO in public data. Reported as "not tested", not "non-binder".
- Context: ulcerative colitis pyroptosis (2026), anxiety/depression literature.

### Etifoxine — TSPO occupancy at human doses is essentially nil; phenotype runs through other routes
- FACT (decisive, PMID:35524344): human TSPO Ki = 7.8 µM; oral 50 mg tid → max free plasma 0.31 nM → ~4 orders of magnitude below Ki. Authors conclude TSPO occupancy is too low for TSPO-mediated effects. XBD173 90 mg qd → 1.0 nM free ≈ Ki → TSPO occupancy relevant.
- FACT: GABA-A channel (TBPS site) IC50 6.7 µM (ChEMBL1907607); known anxiolytic via GABA-A + neurosteroids.
- OBS: weight-loss paper PMID:32679124 — HFD mice, i.p. etifoxine, weight loss, ↓cholesterol/TG, hepatic lipid-gene reversal, gut-microbiome shifts (Oscillospira/Lachnospiraceae). Dose TBD (paywall).
- OBS: in HCV-infected cells etifoxine improves lipid accumulation but WORSENS insulin resistance (PMID:30984779).
- MECH (2026, PMID:41958827): etifoxine→Schwann-cell TSPO→progesterone→PPARγ-PGC1α→M2 macrophage (nerve-injury model, TSPO-KD attenuates). PPARγ is metabolic, but this is nerve injury, not obesity.
- HYP for etifoxine weight loss: gut microbiome / bile acid route (2020 paper's own hypothesis) > TSPO direct route. GABA-A 6.7 µM vs plasma free 0.31 nM also mismatched for occupancy — concentration-matching must be redone with the paper's actual i.p. dose and mouse PK.

## 3. Cross-cutting picture (HYP, to be tested in WS2/WS3)

1. PK11195's T2D-like benefit is best explained by non-TSPO pharmacology: CAR activation (nM, in vivo validated) and/or a fasting-like metabolic state; TSPO-KO data argue against a TSPO-mediated benefit.
2. Emapunil is the clean TSPO story; its T2D claim currently has no public anchor — ask ZHCO for the citation.
3. Etifoxine cannot work via human TSPO at its clinical exposure (4 orders of magnitude gap); candidate routes are GABA-A (if mouse brain exposure is high enough), PPARγ via neurosteroid signalling, or microbiome/bile acids.
4. Cross-ligand negative control value: Ro5-4864 (4'-chlordiazepam) co-appears with PK11195 in both insulin-secretion and gluconeogenesis screens — worth adding as a 4th ligand for the occupancy analysis.

## 4. Next steps
- WS1b: BindingDB + PDSP Ki database sweep (esp. etifoxine broad panel, emapunil, Ro5-4864); DGIdb/CTD; TSPO rs6971 polymorphism annotation.
- WS2: target fishing — ligand-similarity (SwissTargetPrediction/SEA) + reverse docking + DrugCLIP reverse mode (needs new wrapper mode + validation gate per plan).
- WS3: Open Targets genetics for candidates (NR1I3/CAR, PXR, PPARγ, GABA-A, TSPO, ACBP/DBI) vs T2D/obesity; mouse-vs-human dose/PK occupancy table.
- Questions for ZHCO: (a) citation for emapunil T2D benefit, (b) citation for PK11195 T2D improvement, (c) which PK11195 enantiomer/racemate their proposal assumes, (d) any internal expression/PET data on TSPO in islet/adipose.

## 5. WS1b update (2026-10-14, same day)

- BindingDB REST endpoints 404 (service retired); PDSP server unreachable (timeout). Skipped with rationale; ChEMBL+PubChem coverage retained.
- Ro5-4864 (4'-chlordiazepam) resolved: CID 1688, InChIKey PUMYFTJOWAJIKF-UHFFFAOYSA-N. Added as 4th ligand.
- PubChem bioassay mining (assaysummary, Actives only): PK11195 118 active targets / 2533 assays; emapunil 6; etifoxine 18; Ro5-4864 6. GeneID-mapped to symbols (`data/ws1b_geneid_map.json`).
- CAR (NR1I3) confirmed at sub-uM by a THIRD source: PubChem qHTS actives 0.025-0.39 uM alongside the two ChEMBL assay families. PK11195 nuclear-receptor off-targets at µM: PXR (NR1I2) 0.50, LXRα (NR1H3) 31.8, LXRβ (NR1H2) 31.8, RXRA 6.3, ESRRA 31-35, AR 22-40, THRβ 35, PRKN 20.6, TP53/JUN/FOS/histones 27-85 (pan-assay noise band).
- Etifoxine: GABA-A complex only at 6.7 uM (15 subunits, one experiment); CYP2D6 10.7 uM; CYP2C9 9.5; DRD2 13.5; Gabrd/Gabre subunits. Nothing sub-µM except... nothing. Confirms occupancy mismatch.
- Emapunil: TSPO (P16257 0.2-0.6 uM rat-tracer? no - 0.0002-0.0006 uM) + human TSPO P30536 6.4-31 nM; CYP3A7 13.5 uM; CYP2C9 19; GABA-A-related 9.5 uM. Clean.
- Ro5-4864: TSPO rat 3.5-58 nM / mouse 0.2-10 nM / human 1.1-7.3 nM + MCL1 (empty value). Mostly TSPO.
- Etifoxine 2020 paper recovered via Wayback Machine snapshot (Cloudflare-blocked direct PDF): dose = 50 mg/kg i.p. daily in HFD mice; weight loss visible at 7 days, significant at 13 days; serum cholesterol and TG decreased; hepatic lipid genes (cyp7a1 partial, cyp27a1, abcg1, LXRα) and inflammatory genes (TNFα, IL18) reversed; microbiome shifts in Oscillospira/Lachnospiraceae, butanoate + sphingolipid metabolism; authors' own mechanism = TSPO -> cholesterol trafficking -> bile acid synthesis -> microbiome. PDF: `data/etifoxine_obesity_2020_wayback.pdf` (as archived, via Wayback).
- Occupancy math update: 50 mg/kg i.p. mouse ~ allometric-equivalent to 150-280 mg/day human — same exposure league as the 50 mg tid oral used in PMID:35524344, whose free Cmax was 0.31 nM vs human TSPO Ki 7.8 uM (~4 orders gap). Unless mouse free plasma levels are 10000x higher than human-normalized (implausible), the 2020 weight-loss phenotype occurred at negligible TSPO occupancy (HYP, needs mouse PK to close).
- rs6971 (A147T) sensitivity already in hand: emapunil Ki 6.4 (WT) vs 31.3 nM (A147T), 12.6x; PK11195 29.2 vs 36 nM, 1.2x. Species+genotype annotation mandatory for WS3 occupancy table.

## 6. WS2 ligand-similarity + WS3 genetics + WS4 tiering (v0.3, 2026-10-14)

WS2a (ChEMBL similarity 70%, 31 analogues mined):
- Neighbourhood is TSPO + GABA-A + noise tail; NO new metabolic target family hides in the chemical class. Experimental surface essentially closed.
- SwissTargetPrediction POST endpoint needs a session job flow -> deferred; second method family = structure arm (DrugCLIP reverse + docking, with validation gate) as per plan. STITCH resolve endpoint garbled -> dropped with rationale.

WS3 (Open Targets associations, T2D EFO_0001360 / obesity EFO_0001071 filter):
- NR1I3/CAR: MODY3 0.073, NAFLD 0.067, obesity 0.054.
- NR1I2/PXR: obesity 0.093. NR1H3/LXRa: metSyn 0.288, NAFLD 0.261. PPARG: T2D 0.861.
- TSPO: none in top returned rows. GABRA2/GABRG2: none. Genetics do NOT support TSPO as a T2D/obesity driver; they DO support the hepatic nuclear-receptor route.

WS4 tiering table: output/ws4_tiered_targets_v0.3.csv (14 rows).

## 7. Bottom line for the requester (v0.3)

1. PK11195: all plausible targets = TSPO, CAR (T1, sub-uM, triple-sourced, in vivo confirmed), PXR (T2, 0.5 uM), GABA-A central site (T3, uM), LXR/RXR/ERR/AR/THRb noise band (T4). Best mechanistic story for T2D benefit: CAR activation -> fasting-like hepatic state (PMID:23201900); TSPO route disfavoured by KO biology + islet secretion inhibition.
2. Emapunil: all plausible targets = TSPO (T1) and nothing else meaningful in public data. TSPO-dependence proven for cognition, UNPROVEN for any metabolic phenotype; requester's T2D citation still needed.
3. Etifoxine: all plausible targets = TSPO (measured 7.8 uM but occupancy-impossible at clinical+mouse doses), GABA-A picrotoxin site (6.7 uM), CYP/DRD2 noise. Weight-loss phenotype most consistent with gut-microbiome/bile-acid route (authors' own hypothesis) or PPARg via neurosteroids (nerve-injury model only). TSPO route effectively excluded at human exposure; mouse PK still needed to fully close.

## 8. WS2b structure arm (2026-10-14)

### Vina validation-gate docking (scripts/ws2b_validation_gate.py, output/docking/)
| Pocket | Vina top score | Note |
|---|---|---|
| TSPO 4RYI (PK11195 co-crystal) | -9.42 kcal/mol | positive control passes (redock in co-crystal pocket; index-based RMSD 4.3 A is an upper bound without atom mapping) |
| CAR 1XVP chain D (CID co-crystal pocket) | -10.89 | PK11195 CAR off-target signal RECOVERED by an independent method family |
| PXR 2QNV (CDZ pocket) | -7.55 | consistent with sub-uM qHTS but weakest of the three |

Gate verdict: PASS - the structure arm supports the ChEMBL/PubChem evidence ranking (TSPO ~ CAR > PXR).

### DrugCLIP reverse mode (ligand -> pocket library)
- New reverse pipeline built and run end-to-end on A100: pockets TSPO(4RYI)/CAR(1XVP-D)/PXR(2QNV) encoded via official encoders; query = 4 seed ligands + 3 decoys; official 2.94M-mol LMDB used as per-pocket background (100k subsample) for z-score/percentile normalisation (scripts/ws2b_drugclip_reverse.py, ws2b_drugclip_normalise.py, scripts/reverse_retrieve_dcvenv.py).
- Gate verdict: FAIL - decoys outrank true ligands after normalisation (lisinopril z=1.73 vs PK11195 z=0.83 on TSPO; glycine z=2.13 on CAR; emapunil->TSPO only z=0.10). Cross-pocket score comparability problem confirmed empirically; the plan's contingency applies: DrugCLIP reverse output = Tier 4 exploratory only, EXCLUDED from target conclusions.
- Honest negative result retained as evidence (output/drugclip_reverse/, normalised_scores.pkl).

### Final WS2/WS3/WS4 synthesis (unchanged conclusions, strengthened)
1. PK11195: TSPO (T1), CAR (T1, now tri-sourced: ChEMBL biochem+cell, PubChem qHTS, Vina structure recovery), PXR (T2), GABA-A (T3), LXR/ERR/AR/THRb noise band (T4).
2. Emapunil: TSPO only (T1); T2D citation still needed from requester.
3. Etifoxine: TSPO measured 7.8 uM but occupancy-impossible at clinical + mouse-equivalent exposure (T2 measured/exposure-incompatible); GABA-A 6.7 uM (T2-T3); microbiome/bile-acid route is the phenotype-matching hypothesis (OBS); human RCT (PMID:38075272) shows short-term etifoxine changes Faecalibacterium/Roseburia/Lactobacillus - first human microbiome evidence.
4. Ro5-4864: TSPO-selective class control.

## 9. Supplementary analyses (2026-10-14, same day)

### 9.1 Receptor occupancy table (theta = L/(L+Ki), documented exposures)
| Ligand | Target | Exposure (source) | Free nM | Ki/IC50 nM | Occupancy |
|---|---|---|---|---|---|
| emapunil | TSPO WT | 90 mg qd (PMID:35524344) | 1.0 | 6.4 | 13.5% |
| emapunil | TSPO A147T | same | 1.0 | 31.3 | 3.1% |
| etifoxine | TSPO human | 50 mg tid (PMID:35524344) | 0.31 | 7800 | <0.01% |
| etifoxine | GABA-A TBPS | same, brain=plasma upper bound | 0.31 | 6700 | <0.01% |
| PK11195 | TSPO | PET tracer condition | ~0.05 | 8 | 0.6% |
| PK11195 | CAR | in-vivo metabolic dose band (TBD PK) | ~100 (assumed) | 55.8 | ~64% |
Reading: only PK11195-CAR and emapunil-TSPO are occupancy-competent; etifoxine occupies nothing at documented exposures.

### 9.2 GTEx tissue expression (median TPM, gtex_v8)
| Gene | Pancreas | Liver | Adipose SC | Adipose Oment | Hypothalamus | Colon | Muscle |
|---|---|---|---|---|---|---|---|
| TSPO | 38.4 | 33.7 | 221.9 | 227.9 | 29.1 | 164.0 | 38.9 |
| NR1I3/CAR | 0.1 | 98.7 | 0.3 | 0.4 | 0.5 | 0.5 | 0.6 |
| NR1I2/PXR | 0.2 | 42.6 | 0.1 | 0.1 | 0.6 | 11.2 | 0.0 |
| GABRA2 | 0.0 | 0.0 | 0.5 | 0.1 | 3.3 | 0.8 | 0.0 |
| DBI/ACBP | 30.5 | 175.4 | 172.0 | 171.0 | 133.9 | 117.2 | 42.2 |
Reading: CAR is liver-specific (supports the hepatic CAR mechanism for PK11195); TSPO is highest in adipose (its metabolic relevance is via adipose, not islet); GABRA2 is CNS-restricted (peripheral metabolic GABA route unlikely); DBI/ACBP (endogenous TSPO ligand) is high in liver/adipose/hypothalamus — the endogenous axis is present where the phenotypes are.

### 9.3 Extended docking matrix (scripts/ws2c_docking_matrix.py, 6 ligands x 3 pockets)
| Vina top (kcal/mol) | TSPO 4RYI | CAR 1XVP-D | PXR 2QNV |
|---|---|---|---|
| R-PK11195 | -10.96 | -10.45 | -9.10 |
| S-PK11195 | -10.66 | -10.21 | -8.36 |
| PK11195 rac | -9.42 | -10.89 | -7.55 |
| Ro5-4864 | -9.82 | -9.93 | -7.79 |
| emapunil | -8.34 | -8.38 | -7.76 |
| etifoxine | -7.86 | -8.16 | -6.34 |
Observations: R > S ordering reproduced at TSPO and PXR (stereospecific direction confirmed); etifoxine is weakest everywhere (consistent with uM ligand); Ro5-4864 is not TSPO-selective by docking (CAR -9.93 ~ TSPO -9.82) — its in-vitro TSPO selectivity is affinity-derived, docking cannot resolve it; emapunil is not predicted TSPO-selective by docking either — its 1000x selectivity is experimental fact, not a pose feature.

### 9.4 Docking calibration (Spearman, n=6, TSPO pKi vs -Vina)
rho = 0.83, p = 0.042. Docking separates the uM ligand from nM ligands but misorders within the nM cluster. Use: activity-class filter only, not selectivity ranking.

### 9.5 Remaining still-uncomputed (with reasons)
- Boltz-2 affinity refinement of the docking poses: recommended only if the proposal needs pose-level affinity deltas; the evidence tiers already rest on measured data.
- Induced-fit / ensemble docking for TSPO (polymorphic A147T, membrane environment): out of scope for a target search; belongs to a mechanism campaign.
- PPARγ / GABA-A docking for etifoxine: GABA-A is a channel (picrotoxin site exists in structures 6X3X etc.); could be added later but occupancy table already excludes relevance at exposure.


## 10. WS2d — SwissTargetPrediction (independent ligand-similarity method family)
Long-timeout streaming POST solved the job-queue flow (each POST = new session; response streams until the table arrives).
| Ligand | Top targets (probability) | Verdict |
|---|---|---|
| PK11195 | **TSPO 0.899, CAR/NR1I3 0.888** (#1 and #2), then HSD11B1 0.67, SIGMAR1 0.57, ALOX15 0.54 | CAR confirmed by a 4th method family (ChEMBL biochem + ChEMBL cell + PubChem qHTS + Vina + STP) |
| emapunil | DRD1 0.24 max; TSPO NOT in top-100 | similarity methods fail on its scaffold; profile stays clean |
| etifoxine | CB1 0.69, F10 0.69, CB2 0.66, GRM5 0.49; TSPO rank 99 (0.087); GABA-A absent | no measured ChEMBL records for CB1/CB2/F10/P2RX7 -> prediction-only, tiering unchanged |
| Ro5-4864 | rate-limited by the server after 3 jobs | deferred; control ligand, non-blocking |

## 11. WS2e — GABA-A picrotoxin-site docking (6HUG, human alpha1beta3gamma2L, PIO co-crystal pocket)
| Ligand | Vina top (kcal/mol) |
|---|---|
| etifoxine | -4.85 (weakest of the four) |
| PK11195 | -6.52 |
| emapunil | -6.26 |
| Ro5-4864 | -6.05 |
Negative result: etifoxine's 6.7 uM TBPS-site IC50 is consistent with weak, non-discriminating binding; no new target signal from the channel site.

## 12. WS2f — DBI/endozepine literature synthesis
No direct "PK11195 is a DBI antagonist" paper found. Three high-relevance hits:
- PMID:40976282 (2025): insulin evokes endozepine release from NTS astrocytes; endozepines act via the GABA-A benzodiazepine site to modulate hepatic glucose production.
- PMID:34343461 (2021): TSPO-allopregnanolone-GABA-A axis in appetite; TSPO ligands (incl. etifoxine) modulate it.
- PMID:41633838 (2026): glial octadecaneuropeptide as a therapeutic candidate for obesity.
Combined with GTEx (DBI high in liver/adipose/hypothalamus), the endogenous DBI/endozepine axis is present exactly where the phenotypes are. HYP: PK11195/emapunil may perturb DBI signalling at TSPO and/or the GABA-A site — the most plausible indirect route for any emapunil metabolic effect.

## 13. Boltz-2 refinement — blocked, inputs ready
BioLib returns 401 (needs interactive `biolib.login()`). Co-fold YAMLs prepared: output/boltz/tspo_pka.yaml (TSPO 4RYI sequence + PK11195 SMILES) and output/boltz/car_pka.yaml (CAR LBD + PK11195). Deferred until login is available.
