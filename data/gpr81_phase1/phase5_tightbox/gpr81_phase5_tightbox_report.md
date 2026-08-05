# GPR81 Phase 5 — tight-box remediation & reverse-SAR analysis

> Generated 2026-08-04. Companion to `REVIEW_2026-08-04.md` (P0-P2 items).
> Evidence levels: [FACT] file/db-verified; [OBS] direct computation; [MECH] interpretation; [HYP] hypothesis.

## P0 — 9KT9 root cause and fix

**Root cause [FACT+OBS]:** 9KT9 receptor prep is CORRECT — chain R frame matches the
co-crystal ligand 34D (min distance 2.45 A), all pocket residues present, no clash at
the experimental pose. The failure was the **24A search box**: Vina found a deep-insert
global optimum 5.4 A beyond the experimental 34D position, scoring only 0.08 kcal/mol
better than the true pose (unconstrained redock centroid 5.71 A; every compound's
pose drifted to N-terminal residues, core-contact fraction 0.0).

**Fix [OBS]:** 12A tight box centered on the 34D co-crystal centroid + exhaustiveness 32:

| Ligand (9KT9) | best score | best centroid recovery |
|---|---|---|
| 3,5-DHBA (co-crystal control) | -5.574 | **1.67 A** (was 5.71 A) |
| CHBA | -5.579 | 1.05 A |
| 3-OBA | -3.950 | 0.97 A |

All three small acids now recover < 2 A. Verdict: 9KT9 is usable with the tight-box
protocol for orthosteric-pocket ligands. (Recorded in
`phase5_tightbox/9kt9_small_acid_redock.json` + updated `phase3_5_controls/redocking_controls.json`.)

**Scope limit [OBS]:** tight box is only valid for ligands whose site IS the orthosteric
pocket. Large series molecules bind 12-14 A away (see P1) and must not be re-docked with
the small-molecule-centered tight box.

## P1 — 8Z87 large-molecule positive scores reinterpreted

**Positional analysis of all 11 matched-pair compounds [OBS]:**

| Region | 8Z87 | 8Z8A |
|---|---|---|
| TM5-TM6 extracellular | 11/11 compounds | 8/11 (c15-c31) |
| Orthosteric pocket | 0/11 | 3/11 (amide series c35-c38) |

- ALL paper compounds on 8Z87 dock to the TM5-TM6 extracellular region (GLU153/ASN174/
  HIS155/SER164/GLU166 cluster), 12-14 A from the co-crystal center — they never enter
  the CHBA/lactate orthosteric pocket.
- The 7/9 positive scores on 8Z87 (c22/c30/c31/c35-38, +1.5..+12.7) are **conformational
  clashes in the CHBA-bound state's TM5-TM6 region**, NOT non-binding: the same compounds
  score -2.8..-7.5 on 8Z8A's equivalent region. AZ1 (23 nM agonist) is +10 on 8Z87 and
  -4.4..-7.7 on 8Z8A — a known potent agonist cannot be a "non-binder".
- [MECH] The 8Z87 (CHBA) vs 8Z8A (lactate) difference reflects state-specific TM5-TM6
  geometry; 8Z8A accommodates the large agonists, 8Z87 does not.

Deliverable: `phase5_tightbox/annotated_matched_pairs.csv/.json` — per-(compound,receptor)
validity + binding region + verdict, so the phase-4 table can no longer be misread.

**Contact-stat fix [OBS]:** any contact/union/intersection metric computed on
positive-score (clash) poses is invalid; Phase-3 binding-mode table entries for
AZ1/8Z87 ("core contact fraction 0.833") must be read as clash contacts, not binding.

## P2 — reverse-SAR (Davidsson 2020, 11 matched-pair compounds on 8Z8A)

**Global correlation: absent [OBS]:** 8Z8A best score vs log10(EC50): Pearson r=0.250
(p=0.46), Spearman 0.218 (p=0.52), n=11. Vina scores do NOT predict cross-series potency —
consistent with project convention (no single docking score as conclusion).

**Matched-pair direction analysis (8Z8A):**

| Pair | EC50 change | Score delta | Direction |
|---|---|---|---|
| 15->26 (acyl urea -> pyridone) | 0.299 -> 0.021 uM (14x) | -0.17 | MATCH (weak) |
| 22->30 (acyl urea -> pyridone) | 0.166 -> 0.005 uM (33x) | -1.09 | MATCH (weak) |
| 21->28 (acyl urea -> pyridone) | 0.895 -> 0.022 uM (41x) | -0.52 | MATCH (weak) |
| **30 vs 31 (pyridone vs pyrimidinone)** | **0.005 vs 0.24 uM (47x)** | **+3.17** | **MATCH (strong)** |
| 35->38 (amide morpholine -> diMe) | 0.6 -> 0.054 uM (11x) | +0.66 | MISMATCH |

- **30 vs 31 is the strongest docking-SAR agreement**: replacing the pyridone O with
  pyrimidinone N costs 3.2 kcal/mol in Vina and 47x in EC50. The pyrimidinone N insertion
  disrupts the binding mode — a concrete, testable structural hypothesis [OBS+MECH].
- Pyridone bioisostere conversions (15->26, 22->30, 21->28) improve EC50 14-41x while
  docking only improves 0.2-1.1 kcal/mol: direction consistent, magnitude far smaller
  than the affinity gain suggests. Cross-series Vina magnitudes are not quantitative.
- **Amide series (35->38) is a MISMATCH**: EC50 improves 11x while Vina worsens. Notably
  c35-38 dock to the orthosteric pocket on 8Z8A while the acyl-urea/constrained series
  stay in TM5-TM6 — the amide series likely reaches the orthosteric site and its
  optimization may be driven by ligand efficiency / physicochemical properties rather
  than deeper binding [OBS+HYP]. This is exactly the "solubility/exposure vs receptor
  binding" separation the next-step plan called for.

## Limitations

- Single-layer Vina scoring throughout; no MM/GBSA second layer yet.
- Region classification is per-best-pose (seed 20260803); multi-seed cluster consensus
  would harden it.
- 9KT9 was not used for large-molecule docking (phase-4 scope); its TM5-TM6 geometry
  remains unassessed for the series.
- Cryo-EM structures are single rigid conformations; no induced-fit or MD.

## Recommended next actions

1. MM/GBSA (OpenMM GBn2) on the 8Z8A top poses of c30/c31 to test the pyridone vs
   pyrimidinone hypothesis quantitatively (expected: c30 clearly preferred).
2. Multi-seed pose-cluster consensus for the region classification (harden P1).
3. If the amide series really binds the orthosteric pocket, dock c35-38 into 9KT9
   (tight box) to cross-validate on a second orthosteric-state structure.
4. Update the 3D gallery with region labels.
