# TSPO Ligand Target Search (PK11195 / Emapunil-XBD173 / Etifoxine) — Plan

Status: PLAN ONLY (no analysis run yet). Date: 2026-10-14. Owner: QYJI. Requester: ZHCO (Cao Zheng), Group 3 TSPO proposal.

## 1. Question

For three TSPO-reported ligands, enumerate ALL plausible protein targets (on-target TSPO and off-target / polypharmacology), and rank them by how likely each explains the reported metabolic phenotype.

| Ligand | Known TSPO link | Phenotype claim | Core doubt |
|---|---|---|---|
| PK11195 | NMR structure (pocket), Ki ~10 nM | improves T2D conditions | TSPO-dependence unproven; effective doses are often micromolar |
| Emapunil (XBD173 / AC-5216) | TSPO ligand; TSPO-dependent effect shown only for cognition/neuropathology | some T2D benefit | no direct evidence of TSPO route in T2D |
| Etifoxine | weak TSPO affinity | weight loss at low concentration | potency of phenotype does not match TSPO affinity (known GABA-A modulator, to be verified) |

Key principle: a target is only "plausible" if (a) there is binding/activity evidence at a concentration compatible with the concentration that produces the phenotype, and (b) the target has biological relevance to T2D / obesity. Every conclusion is tagged FACT / OBS / MECH / HYP.

## 2. Definition of "all potential targets" (scope control)

- Direct binders / functional modulators of proteins (receptors, channels, enzymes, transporters, nuclear receptors).
- Include metabolizing enzymes and transporters only as a separate annotated class (PK/DDI, not efficacy).
- Out of scope: phenotypic mechanism beyond protein targets, and wet-lab experimental design (to be defined by the biology team).
- Evidence unit = (ligand, protein, assay type, potency, species, source). Nothing enters the target list without a traceable source.

## 3. Workstreams

### WS0. Compound curation (day 1)
- Resolve identities and structures: PK11195 (racemate vs R-/S- enantiomer; note R-PK11195 is the usual TSPO ligand), emapunil/XBD173/AC-5216, etifoxine (and its active metabolite, desethyl-etifoxine).
- Cross-check SMILES in ChEMBL, PubChem, DrugBank, IUPHAR; record InChIKeys, salts, stereo.
- Collect concentration context from the T2D/obesity papers (in vitro uM, in vivo mg/kg, plasma/brain exposure) into a table; this is used later for occupancy filtering.
- Gate: structure + concentration table reviewed before downstream steps.

### WS1. Known-evidence mining (days 1-3)
Sources (query by InChIKey/name, record potency and assay):
- Bioactivity: ChEMBL, BindingDB, PubChem BioAssay, IUPHAR/BPS GtoPdb, DrugBank, PDSP Ki database (broad receptor panels), DGIdb, CTD, STITCH.
- Large profiling sets: Tox21/ToxCast, Eurofins/CEREP-type panels if published, LINCS L1000.
- Literature: PubMed/Europe PMC + Paperclip (existing paperclip integration in this repo) with NER (bbbkit/druggability `ner.py`) to harvest "ligand X inhibits/activates/binds Y" statements; manual curation of top hits.
- Specific question: do published TSPO-knockout / knockdown studies show that the ligand effect persists without TSPO? (strongest FACT about TSPO-dependence).
- Output: evidence table v1 (ligand x protein x potency x source).

### WS2. Computational target fishing (days 3-8)
Orthogonal methods so no single predictor drives conclusions:
1. Ligand-based: SwissTargetPrediction, SEA, ChEMBL similarity (multiple fingerprints), PPB2; nearest-neighbour analysis around known TSPO and GABA-A ligands.
2. Structure-based reverse docking: reuse existing druggability pipeline (Vina coarse screen -> DrugCLIP pocket retrieval -> Boltz-2 affinity via BioLib -> MM-GBSA filter only -> FEP+ for top few). Pocket library = PDB/AlphaFold pockets of the candidate set from WS1 + T2D/obesity-relevant proteome subset (GPCRs, ion channels, nuclear receptors, kinases, metabolic enzymes, mitochondrial proteins such as VDAC/ANT).
3. DrugCLIP reverse retrieval (ligand -> pocket library), a dedicated arm:
   - Existing tool `src/druggability/drugclip.py` (+ `drugclip_worker.py`) runs pocket -> molecule-library retrieval. Target fishing needs the opposite direction. DrugCLIP is a dual-encoder (pocket encoder + molecule encoder, cosine similarity), so the idea is to embed the 3 ligands (+ TSPO-ligand and GABA-A/other reference ligands) and a pocket library, then rank pockets per ligand.
   - New work: build a pocket LMDB library (PDB co-crystal pockets + AlphaFold/fpocket pockets of the WS1/WS3 candidate set and a metabolic/CNS-relevant proteome subset); add a `ligand -> pockets` mode to the wrapper, with an independent unit test (mock worker).
   - Known caveat (HYP, must be validated): DrugCLIP scores are trained for ranking molecules within one pocket; cross-pocket score scales are not guaranteed comparable. Mitigation: per-pocket normalisation (z-score of the ligand score against the background distribution of the existing mols.lmdb for that pocket) and report rank/percentile, not raw cosine.
   - Validation gate before use: (a) TSPO pocket (PK11195 NMR structure) must rank high for PK11195; (b) known off-target pockets from WS1 must be recovered; (c) report enrichment (EF/AUC) on a known ligand-pocket set. If the gate fails, DrugCLIP output is reported as exploratory (Tier 4 only).
   - Its hits feed Vina/Boltz-2 confirmation; DrugCLIP alone never reaches Tier 3.
4. Mandatory controls before trusting any score:
   - Positive control: TSPO + PK11195 (NMR structure; re-dock RMSD and score rank).
   - Known off-targets from WS1 as recovery test (are they recovered in the top X%?).
   - Decoys / cross-pocket negative controls for enrichment (EF / AUC).
5. Consensus: a target needs support from >= 2 independent method families to reach "predicted" tier.

### WS3. Phenotype relevance and exposure filter (days 6-9)
- Open Targets: genetic association of each candidate with T2D / obesity / BMI (GWAS, cis-pQTL via OTv4; cis = chr +-1Mb), tractability, safety flags.
- Tissue expression of candidates in relevant tissues (islet, liver, adipose, muscle, hypothalamus, immune cells) vs TSPO expression.
- Occupancy filter: compare potency (Ki/IC50/EC50) with the effective concentration from WS0. Example logic: etifoxine at low concentration should engage targets with sub-uM potency, not TSPO if its Ki is higher than the active dose.
- Optional transcriptional connectivity (LINCS signature vs T2D/obesity signatures) as supporting MECH evidence only.

### WS4. Integration and tiering (days 9-11)
Tier each ligand x target pair:
- Tier 1: experimentally measured, potency compatible with phenotype concentration, T2D/obesity relevance.
- Tier 2: experimentally measured but concentration mismatch, or relevance unclear.
- Tier 3: predicted only (>= 2 methods concur).
- Tier 4: single-method prediction / low confidence (listed for completeness).
Also report a per-ligand TSPO-dependence verdict (supported / unresolved / disfavoured) with the evidence and its limits. Computational limits (docking is not affinity, no species-specific structure for some targets, selectivity pockets) are stated explicitly.

### WS5. Deliverables (days 11-14)
- Target tables per ligand (CSV/XLSX) with evidence, tier and sources.
- Self-contained HTML report (English; no external resources) plus one-page summary.
- Reproducible scripts and run log in the repo (campaign-style, with unit tests for new parsing / scoring code per project rule).
- Short list of orthogonal-evidence questions for the biology team to decide whether wet-lab follow-up is warranted (no experimental designs proposed by us).

## 4. Timeline (target ~3 weeks incl. review)

| Week | Content | Human checkpoint |
|---|---|---|
| 1 | WS0 + WS1 | review structure/concentration table and evidence v1 |
| 2 | WS2 + WS3 | review control results (TSPO re-dock, off-target recovery) before ranking |
| 3 | WS4 + WS5 | review tiering and report with requester |

## 5. Code / repo implications
- Reuse `src/druggability` (fetch.py, search.py, ner.py, pocket.py, batch.py, biolib_apps.py) and existing docking/FEP scripts; new campaign folder `TSPO_assessment/` following OXTR/GLP1R/GPR81 layout.
- Any new module (e.g. ChEMBL/BindingDB/PDSP fetchers, target-fishing wrappers) gets an independent unit test under `tests/`.
- Respect the roadmap rule: pay down touched technical debt first, do not add new one-off scripts at repo root.

## 6. Risks and open questions
1. Exact deadline not given.
1b. DrugCLIP reverse mode is new code (existing wrapper is pocket->molecule) and its cross-pocket scoring is unvalidated; covered by the validation gate in WS2.3.
2. Doses/concentrations used in the cited T2D / obesity studies are needed (WS0); if unavailable the occupancy filter becomes qualitative.
3. Species: human vs rodent TSPO and targets differ (e.g. rodent vs human affinity of TSPO ligands is polymorphism-sensitive, rs6971); data are species-annotated.
4. Racemic vs enantiomeric PK11195 changes interpretation; confirm which form was used in each study.
5. Docking scores cannot establish binding; only measured data reach Tier 1.
6. Etifoxine's known GABA-A modulation and other pharmacology listed in memory/prior knowledge are HYP until confirmed from WS1 sources.
7. Public data may be sparse for emapunil; absence of data is reported as "not tested", not "not a binder".
