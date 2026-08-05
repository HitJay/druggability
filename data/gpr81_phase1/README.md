# GPR81 / HCAR1 Phase-1 input package

This directory contains the auditable input-normalization output for the HCAR1/GPR81 small-molecule agonist docking request.

## Target identity
- Human HCAR1/GPR81/HCA1/GPR104
- UniProt: Q9BXC0
- Reviewed sequence length: 346 aa

## Tool compounds
`tool_compounds.csv` contains the five requested PubChem records, including CID, formula, molecular weight, canonical/connectivity SMILES, isomeric SMILES, and source URLs. The corresponding 3-D PubChem SDF files are under `ligands/`.

## Receptor structures
The strongest Phase-2 starting points are experimental human HCAR1-Gi cryo-EM structures, not AlphaFold alone:
- `structures/8Z87.cif`: CHBA-bound
- `structures/9KT9.pdb`: 3,5-DHBA-bound
- `structures/8Z8A.pdb`: lactate-bound
- `structures/8Z8B.pdb`: apo

`structure_records.json` records the RCSB titles, methods, release dates, and URLs.

## Paper series
`paper_compound_inventory.csv` inventories compounds 1-39 from the supplied Davidsson et al. (2020) paper across acyl urea, constrained analogue, and amide series. Potency values are transcribed from Tables 1-8.

**Update (2026-08-04):** all 39 paper structures are now recovered and validated (`paper_structures_recovered.json`; 3 `authoritative` + 36 `reconstructed_and_MS_validated`, each with SI-reported [M+H]+ matched within HRMS tolerance, ChEMBL cross-check where available). SDFs are under `paper_ligands/compound_*.sdf`. The only compound that failed first-pass reconstruction (22, MS mismatch) was later resolved and is now `authoritative`.

## Phases
- Phase 1: input normalization (this package; `MANIFEST.json` + sha256)
- Phase 2: receptor prep (`phase2_prepared/`; chain R, ligands removed, pocket from co-crystal ligand)
- Phase 3: tool-compound docking (`phase3_docking/`; 8Z87/8Z8A/9KT9, 24A box) + multiseed (`phase3_multiseed/`)
- Phase 3.5: aligned pose comparison + redocking controls (`phase3_5_aligned/`, `phase3_5_controls/`, `phase3_5_controls_restrained/`)
- Phase 4: matched-pair reverse validation (`phase4_matched_pairs/`; 8Z87/8Z8A only)
- Phase 5: tight-box redocking remediation (`phase5_tightbox/`) — see `REVIEW_2026-08-04.md` for rationale
- Phase 6: full-series docking of all 39 paper compounds (`phase6_full_series/`; 8Z8A + 9KT9, DONE 2026-08-04, positional QC passed)
- Safety: HCAR1 activation-direction assessment (`safety/`; 3_safety-style companion)

## Pipeline state map (which data is trustworthy under which protocol)

```
                     protocol trust level
                     -------------------------------
 Phase 3/4 (24A box)  8Z87 small acids  OK
                      8Z87 large mols   CLASH (CHBA-state TM5-TM6 incompat; NOT non-binders)
                      8Z8A all          OK (large mols bind TM5-TM6 region; amides reach orthosteric pocket)
                      9KT9 small acids  INVALID -> use Phase 5 tight box
                      9KT9 large mols   INVALID under 24A (phase-4 never docked them; Phase 6 24A results need positional QC)
 Phase 5 (tight box)  9KT9 small acids  VALIDATED (redock 3,5-DHBA 1.67 A < 2 A gate)
                      large molecules   NOT APPLICABLE (they bind TM5-TM6, not the orthosteric pocket)
 Phase 6 (24A box)    8Z8A + 9KT9 all   new full-series scan; 9KT9 needs positional QC per compound
```

Key conclusions so far (2026-08-04):
- Large Davidsson-series agonists dock to the TM5-TM6 extracellular region on both
  receptors, NOT the small-acid orthosteric pocket (multi-seed consensus, 8 seeds x 5 poses).
- 8Z87 positive scores for large molecules = CHBA-state conformational clash, not non-binding.
- c30 (pyridone, 5 nM) vs c31 (pyrimidinone, 240 nM): pyrimidinone N3 sits 3.8 A from GLU153
  carboxylate (8/8 seeds) -> electrostatic repulsion, inter-energy penalty ~4 kcal/mol.
- HCAR1 activation carries mechanism-based tumor/cachexia + liver-fibrosis risk (see `safety/`).

## Review status
`REVIEW_2026-08-04.md` documents a full-chain audit: 9KT9 pose drift under the 24A box (fixed by tight-box protocol in Phase 5), systematic positive scores for large molecules on 8Z87 (clash-incompatible with the CHBA sub-pocket, not non-binders), and stale-doc issues.
