# GPR81 (HCAR1) Agonist Optimization & Development Recommendations

*Follow-up deliverable 3 — synthesized from the full GPR81 campaign: structure
recovery and identity resolution (Davidsson et al. 2020, BMCL 30:126953; 39/39
compounds), multi-receptor docking (8Z8A lactate-bound / 9KT9 3,5-DHBA-bound /
8Z87 CHBA-bound active-state structures), redocking controls, multi-seed
pose-consensus, pocket region analysis, reverse-SAR matched pairs, and HCAR2/
GHS-R1a cross-reactivity mapping.*

> Evidence-level convention (as in all campaign deliverables):
> [FACT] experimental/database-verified · [OBS] direct computation ·
> [MECH] mechanistic interpretation · [HYP] unresolved hypothesis.

---

## 1. Where the series stands (lead perspective)

**Best-balanced lead today: compound 28** (constrained pyridone, EC50 22 nM,
41× vs GPR109A, 82× vs GHS-R1a, LLE 5.3). [FACT] It is the only compound that
is simultaneously potent, full-efficacy, and selective against both known
cross-reactivity liabilities, and it is the paper's own "very interesting
compound for further evaluation".

**Close challengers:**

| Compound | EC50 (nM) | GPR109A × | GHS-R1a × | LLE | Position |
|---|---|---|---|---|---|
| c28 | 22 | 41 | 82 | 5.3 | constrained pyridone — best balance [FACT] |
| c26 | 21 | 29 | 62 | 3.9 | constrained pyridone, benzothiazole RHS [FACT] |
| c29 | 75 | 25 | 667 | 4.5 | constrained pyridone, CH2OH-sulfone RHS [FACT] |
| c38 | 54 | 10 | 500 | — | amide, cis-2,6-dimethylmorpholine; sol 95 µM [FACT] |
| c30 | 5 | 7.4 | n.d. | — | most potent, but GPR109A selectivity collapses [FACT] |
| c7 | 3.6 | n.d. | n.d. | — | acyl-urea, pyrazol-1-yl; Emax 70% (partial) [FACT] |
| c4 | 1.4 | n.d. | n.d. | — | acyl-urea, R2=CF3; Emax n.d. [FACT] |
| c5 | 0.74 | n.d. | n.d. | — | **partial agonist, Emax 47%** — potent ≠ lead [FACT] |

Three recurring patterns drive the ranking:

1. **The most potent compound is the least selective** (c30, 5 nM / 7.4×), the
   same trap as the HTS hit c1 (23 nM but 0.3× vs GHS-R1a — 3× more potent at
   GHS-R1a than at GPR81). Potency alone must never nominate a lead. [FACT]
2. **Partial agonists concentrate in the Table 2/3 acyl-urea panel** (c5–c8,
   Emax 47–74%). Their low EC50 values rank them top by potency but they are
   not full-agonist leads. [FACT] — this may, however, be a *feature* for a
   safety-conscious profile (see §4).
3. **Selectivity and LLE were improved by the constrained pyridone and amide
   series**, not by the acyclic acyl ureas. [FACT]

---

## 2. Structure-based optimization strategies

### 2.1 Two distinct binding modes — design accordingly [OBS]+[MECH]

The docking campaign established that GPR81 ligands occupy two separate sites:

- **Orthosteric pocket (small acids):** lactate, 3,5-DHBA, CHBA anchor via a
  conserved carboxylate–Arg71 salt bridge (with Tyr75, Ser167, His261, Phe168
  lining the pocket). Redocking controls recover the experimental pose
  (centroid 0.88–2.9 Å). Potency of this chemotype is inherently low (mM–µM).
  [FACT][OBS]
- **TM5–TM6 extracellular site (large agonists):** essentially all nM-potent
  paper compounds (30/39 on 8Z8A) dock into an extended crevice formed by
  TM5/TM6 (residues ~149–181: Tyr149, Glu153, His155, Ser164, Glu166, Ile169,
  Asn174, His177), 9–14 Å from the orthosteric center. [OBS] The amide series
  (c33, c35–c38) additionally reaches into the orthosteric pocket — a dual-site
  engagement. [OBS]

**Consequence:** optimization should be planned per site. The nM SAR lives in
the TM5–TM6 site; the Arg71 carboxylate anchor is the address for fragment
grafting (prodrugs, PET tracers, tool acids), not for potency gains.

### 2.2 The pyridone–pyrimidinone rule (single-atom potency cliff) [FACT]+[OBS]+[MECH]

c30 (pyridone, 5 nM) vs c31 (pyrimidinone, 240 nM) is a **47× potency loss**
from one atom change. The docked poses explain it: the pyrimidinone N3 sits
3.75–3.83 Å from the Glu153 carboxylate in 8/8 seeds — negative-lone-pair /
negative-carboxylate electrostatic repulsion (Vina inter-term penalty ≈ 4
kcal/mol). The pyridone C–H at the same position has no lone pair. [OBS]

**Rule: keep the pyridone (or a C–H lactam bioisostere) in any constrained
template; avoid pyrimidinone at that ring position.** The same logic applies to
c26/c27 (21 vs 490 nM). [MECH]

### 2.3 Exploit the Glu153 contact for HCAR2 selectivity [FACT]+[MECH]

HCAR2 (GPR109A) differs at 9/10 TM5–TM6 residues, including the charge flip
**Glu153 (HCAR1) → Lys165 (HCAR2)**. A substituent that makes a favorable
contact with the negative Glu153 carboxylate will become repulsive at the
positive Lys165 — a built-in selectivity handle. The orthosteric pocket is even
more divergent (Arg71→Leu83), which is why the small acids are intrinsically
HCAR1-preferring. [MECH]

**Actionable:** dock RHS variants carrying basic/neutral H-bond donors into the
HCAR2 AlphaFold model (already built in this project) and select vectors that
clash/repel at Lys165 while contacting Glu153. This is a testable docking
target, not yet validated experimentally. [HYP]

### 2.4 Linker pre-organization beats linker flexibility [FACT]+[MECH]

The acyclic acyl-urea linker requires an intramolecular H-bond network for
activity: when it is broken (N-methylation c23, CH2 insertion c24, NH inversion
c25 → EC50 16–33 µM), activity collapses even though the compounds still dock
with good scores — rigid docking cannot see this penalty. The paper's winning
move (Table 7) was to constrain the urea into a pyridone ring, pre-organizing
the geometry. **Future designs should keep the constrained template and treat
the acyl-urea series as a scaffold to escape from, not to extend.** [FACT][MECH]

### 2.5 RHS/SAR handles that worked [FACT]

- **R2 substituent:** CF3 > CH3 (c4 1.4 nM vs c3 3.7 nM); Cl is the workhorse.
- **R3:** morpholine vs pyrazol-1-yl swap changes potency 3–10× (c10 vs c11)
  and modulates Emax (partial agonism).
- **RHS:** SO2-N-methylpiperidine reaches the extended site and gives the
  tightest poses; CH2-4-methylpiperazine is the polar, solubility-friendly
  alternative; the cyclic-amide RHS (c28/c29, CH2OH) is the selectivity sweet
  spot. [OBS]
- **Amide series stereochemistry:** cis-2,6-dimethylmorpholine (c38, 54 nM,
  500× GHS-R1a, sol 95 µM) vs trans (c37, 350 nM, no selectivity gain) — a
  6.5× potency + selectivity + solubility win from one stereocentre. [FACT]

---

## 3. Development directions

1. **Nominate c28 as the primary lead**; run c26 and c29 as backups; keep c38
   as the amide-series/physchem lead (best solubility of the nM set). [FACT]
2. **Fill the profiling gap on the Table 2/3 panel**: c3–c8 are potent
   (0.7–7 nM) but have no selectivity or Emax data for c3/c4. Before any
   acyl-urea follow-up, measure GPR109A + GHS-R1a counterscreens — the HTS
   hits c1/c2 warn that this scaffold class carries GHS-R1a liability. [FACT]
3. **Second-generation design brief** (chemistry): constrained pyridone core
   (c28 template) + RHS vectors aimed at Glu153/Asn174/His155 (TM5–TM6),
   retaining a carboxylate-free polar anchor; hard caps MW ≤ 550, clogP ≤ 4,
   LLE ≥ 5 (c28 = 5.3 is the bar); keep an eye on the 47%–70% Emax window —
   a tuned partial agonist may be the safest GPR81 profile (mechanism-based
   oncology/cachexia/fibrosis risk, see below). [MECH]
4. **Selectivity panel for every analog**: hGPR81 / hGPR109A / hGHS-R1a (both
   liabilities are assayed in the Davidsson paper — replicate that triplex) +
   HCA3 (GPR109B) where feasible. Target ≥ 25× vs GPR109A and ≥ 50× vs
   GHS-R1a (the tier-A rule used in the ranking). [FACT]
5. **Structure-based workflow** (this campaign's validated configuration):
   use 8Z8A (lactate-bound) as the primary docking model; 9KT9 orthosteric
   labels require the deep-insert gate; treat 8Z87 (CHBA-bound) as
   clash-incompatible for large ligands (conformational-state artifact, not
   non-binding). Extend with induced-fit/MD (Boltz-2 available in this repo)
   before committing to a TM5–TM6 interaction. [OBS]
6. **Pharmacology**: distinguish Gαi vs β-arrestin bias; the endogenous tone
   is mM lactate, so functional assays must control ambient lactate; partial
   agonism and allosteric/biased profiles deserve explicit testing. [HYP]
7. **Safety gates** (ties to the drug-target safety landscape work): HCAR1
   agonism carries mechanism-based tumor/cachexia + liver-fibrosis signals
   (Open Targets/OT Platform evidence pulled 2026-08-04). Factor this into
   indication choice; a tissue-selective or partial agonist may mitigate.
   [FACT][HYP]

---

## 4. Honest limitations of the computational layer

- Vina scores are **not** affinity/potency predictions: global score–EC50
  correlation is absent (n=39, r≈−0.11), and several score–activity mismatches
  are documented (c17 scores −8.15 but is 70× weaker than c7; c23–c25 score
  well yet are 16–33 µM). [OBS]
- Docking does not prove agonism, affinity, or selectivity — it provides
  binding-mode hypotheses. [FACT]
- All pose-level conclusions rest on rigid-receptor docking; the TM5–TM6 site
  occupancy is single-conformation evidence until MD/induced-fit confirms it.
  [HYP]

---

*Prepared as part of the GPR81 druggability follow-up. Companion files:
gpr81_compound_scorecard.csv (45-compound ranking), gpr81_pocket_analysis_pairs.csv
(46 ligand–receptor pairs), figures/pocket_*.png (per-pair illustrations),
gpr81_followup_report.html (consolidated report).*
