# GPR81 Phase 6 — full-series docking of all 39 paper compounds

> Generated 2026-08-04. Companion to `gpr81_phase5_tightbox_report.md` and
> `REVIEW_2026-08-04.md`. Protocol: 24A box, 2 seeds x exhaustiveness 16 x 5 poses,
> on 8Z8A (primary) and 9KT9 (fills the phase-4 gap). Matched pairs (11 compounds)
> additionally carry the 8-seed phase-4 data.

## 1. Positional QC — 9KT9 is usable for large molecules under 24A

Unlike the small tool acids (which deep-inserted under the 24A box on 9KT9),
all 39 large paper compounds dock to defined regions — **zero N-terminal drift**:

| Receptor | TM5-TM6 extracellular | Orthosteric pocket | Mixed |
|---|---|---|---|
| 8Z8A (pose 1, seed 20260803) | 27 | 9 | 3 |
| 9KT9 (pose 1, seed 20260803) | 23 | 15 | 1 |

[OBS] 9KT9 (3,5-DHBA-bound) accommodates more compounds in the orthosteric
pocket (15 vs 9) — a state-specific difference worth noting, not an error.
Per-compound region labels: `phase6_full_series/9kt9_positional_qc.json` (in
`full_series_positional_qc.json`).

## 2. Score vs potency — no global correlation (expected)

| Receptor | n | Pearson r | p | Spearman rho | p |
|---|---|---|---|---|---|
| 8Z8A | 39 | -0.114 | 0.49 | -0.128 | 0.44 |
| 9KT9 | 39 | -0.181 | 0.27 | -0.211 | 0.20 |

Vina absolute scores do not rank-order potency across the full series — confirms
the project convention: never use a single docking score as a conclusion.

Series-level (8Z8A): acyl_urea n=22 Spearman -0.356 (p=0.104, marginal);
constrained n=6, amide n=8, linker n=3 all non-significant. The only near-signal
is within the acyl_urea series, consistent with scaffold-consistent SAR being
partially captured while cross-series comparisons are not.

## 3. Concrete score-activity mismatches (why single-score ranking fails)

| Compound | 8Z8A best | EC50 (uM) | Note |
|---|---|---|---|
| c7 (acyl_urea, pyrazol-1-yl) | -8.46 | 0.0036 | best scorer; genuinely potent - consistent |
| c17 (acyl_urea, benzothiophene RHS) | -8.15 | 0.26 | strong score, 70x weaker than c7 |
| c23 (N-methylated urea) | -6.96 | 16.0 | good score, very weak activity |
| c24/25 (urea linker variants) | ~-5.8 | 33.0 | score says binder, paper says inactive |

The linker-variant series (c23-25, EC50 16-33 uM) still docks with decent scores
— rigid-docking cannot capture the loss of the intramolecular H-bond network that
the paper attributes to linker geometry. This is exactly the "rigid docking fails
to explain SAR" case the next-step plan predicted.

## 4. New high-value observations

- **c7 (-8.46, 3.6 nM)** and c4 (1.4 nM, Table 2 R1=CF3) are the most potent
  compounds in the paper; c7 is now the best-scoring compound overall on 8Z8A.
  The Table 2/3 R2/R3 SAR (Me/CF3/F/H at R2; morpholine vs pyrazol-1-yl at R3)
  is a rich unexplored docking panel for a follow-up focused analysis.
- Pyridone-vs-pyrimidinone penalty (c30 vs c31, ~4 kcal/mol inter, GLU153 clash)
  confirmed again in the full-series run (c30 8Z8A best -6.0, c31 -2.8).

## 5. Data files

- `full_series_docking_results.csv` — all poses (39 x 2 receptors x 2 seeds x 5)
- `full_series_summary.json` — best/mean/std per compound x receptor
- `full_series_reverse_sar.json` — correlations + top scorers (from analyze script)
- `full_series_positional_qc.json` — per-compound region labels on both receptors
- `poses/` — PDBQT poses (gitignored)

## 6. Caveats

- 2 seeds x 16 exhaustiveness (vs 8 seeds x 32 for matched pairs): scores are
  directional; matched-pair-level conclusions still rest on phase-4 data.
- Single pose-1 region label per compound for QC; multi-seed consensus only
  computed for the 11 matched pairs.
- 9KT9 orthosteric-pocket occupancy for large molecules is a single-conformation
  observation; no induced-fit.
