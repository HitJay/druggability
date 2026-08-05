# HCAR1 vs HCAR2 — pocket comparison (selectivity structural basis)

> Generated 2026-08-04. Companion to `davidsson2020_selectivity_transcription.json`
> and `HCAR1_activation_safety_2026-08-04.md` (Appendix).
> Inputs: HCAR1 sequence Q9BXC0 + cryo-EM 8Z8A/8Z87/9KT9; HCAR2 sequence Q8TDS4
> + AlphaFold AF-Q8TDS4-F1-model_v6.pdb (downloaded 2026-08-04).
> Pairwise global alignment identity: **56.5%** (paper states ~52% for the closest homologue).

## 1. Orthosteric pocket (small-acid site, lactate/CHBA/3,5-DHBA anchor)

| HCAR1 | HCAR2 | Change | Significance |
|---|---|---|---|
| **ARG71** | **Leu83** | R→L | **KEY**: HCAR1's carboxylate anchor (positive charge) is GONE in HCAR2 — explains why lactate/CHBA/3,5-DHBA are HCAR1-preferring and niacin (different anchor chemistry) is HCAR2-selective |
| GLU166 | Ser178 | E→S | charge/H-bond donor lost |
| HIS261 | Phe277 | H→F | H-bond/imidazole → hydrophobic |
| TYR75, LEU92, LEU95, ALA96, ARG99, SER167, PHE168, LEU264, TYR268 | conserved | = | scaffold conserved |

## 2. TM5-TM6 extracellular region (large-molecule site from this project)

| HCAR1 | HCAR2 | Change |
|---|---|---|
| GLU153 | Lys165 | E→K (charge flip) |
| HIS155 | Met167 | H→M |
| CYS157 | Ile169 | C→I |
| SER164 | Leu176 | S→L |
| GLU166 | Ser178 | E→S |
| ILE169 | Ser181 | I→S |
| MET170 | Ile182 | M→I |
| GLU171 | Cys183 | E→C |
| ASN174 | Phe186 | N→F |
| HIS177 | His189 | conserved |

9 of 10 residues differ — this region is the least conserved part of the binding
surface, yet still accommodates the large agonists on both receptors (c30 GPR109A
EC50 0.037 uM = only 7.4x selective).

## 3. Interpretation for the campaign

- **Small-acid site**: HCAR2 lost the ARG71 anchor ⇒ orthosteric-pocket ligands are
  intrinsically hard to make HCAR2-selective *against* (they simply don't fit HCAR2),
  and HCAR2-selective chemotypes use their own anchor (niacin). [MECH]
- **Large-molecule site**: divergent sequence yet cross-activity ⇒ the TM5-TM6 site
  tolerates the Davidsson scaffolds on both receptors; the 7.4x (c30) to >45x (c27)
  GPR109A selectivity spread must come from specific RHS/LHS contacts that exploit the
  HCAR1-vs-HCAR2 differences (e.g. GLU153 vs Lys165). This is a testable docking target:
  dock c27/c30 RHS variants into HCAR2 and look for a clash/repulsion that HCAR1 lacks. [HYP]
- **Pyrimidinone selectivity effect (c27 >45x vs c31 6x)**: same ring change, opposite
  selectivity outcome depending on RHS — consistent with our finding that the pyrimidinone
  N3 penalty is contact-specific (GLU153 in HCAR1; the HCAR2 counterpart Lys165 is a
  charge flip that would *favour* the N) — needs per-pose analysis, not a global rule. [HYP]

## 4. Caveats

- AlphaFold HCAR2 is an apo model (pLDDT-based); pocket geometry is predicted, not
  experimentally determined — treat residue-level comparison as primary, geometry as secondary.
- No HCAR2 co-crystal structure exists yet for these chemotypes (as of 2026-08).
- Sequence alignment is pairwise-global; TM bundle register is reliable for GPCRs of
  this identity level, but insertion/deletion regions (ICL/ECL) should not be over-read.

## Files
- `AF-Q8TDS4-F1-model_v6.pdb` — AlphaFold HCAR2 structure (downloaded)
- `hcar1_hcar2_pocket_mapping.json` — residue mapping (orthosteric + TM5-TM6)
