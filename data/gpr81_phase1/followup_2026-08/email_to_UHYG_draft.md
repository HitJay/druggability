Subject: GPR81 (HCAR1) druggability follow-up — ranking, pocket analyses, and wet-lab benchmark proposal

Hi Huan,

Following up on the GPR81/HCAR1 druggability request: the three follow-up
deliverables are complete, plus a computational cross-validation layer and a
proposed wet-lab benchmark panel. Summary below; full detail in the
self-contained reports (links at the end).

1. Overall ranking of all 45 compounds
   - Ranking basis: reported experimental hGPR81 EC50 (ascending), stratified
     into Tier A/B/C by EC50 + Emax + GPR109A/GHS-R1a selectivity.
   - Best-balanced lead: compound 28 (22 nM, 41x GPR109A, 82x GHSR, LLE 5.3).
   - Watch-outs: compound 30 is most potent (5 nM) but only 7.4x GPR109A-
     selective; compound 5 (0.74 nM) is a partial agonist (Emax 47%).
   - Reference ligands (CHBA, 3,5-DHBA, 3-OBA, lactate) listed separately.

2. Binding-pocket analyses, all 46 ligand-receptor pairs
   - Per pair: multi-seed Vina score, binding region, polar/hydrophobic
     contact residues, pose position vs co-crystal ligand, EC50 context —
     with a structural illustration for each pair (46 figures embedded in the
     HTML report).
   - New control run: lactate x 9KT9 tight-box (12 A box, ex32, 3 seeds):
     best -3.78 kcal/mol, 2.79 A centroid recovery (vs 2.89 A on cognate
     8Z8A) — the endogenous ligand recovers the orthosteric pocket on both
     active-state structures.

3. Optimization & development recommendations
   - Keep the constrained pyridone template; avoid pyrimidinone (N3-Glu153
     clash, 47x potency cliff); exploit the Glu153(HCAR1)->Lys165(HCAR2)
     charge flip as a selectivity handle; retain the cis-2,6-dimethylmorpholine
     stereochemistry (c38: 54 nM, 500x GHSR, sol 95 uM).
   - Counterscreen every analog at GPR109A + GHS-R1a; design caps MW <= 550,
     clogP <= 4, LLE >= 5.
   - Safety: mechanism-based tumor/cachexia + liver-fibrosis risk (as in the
     ticket description) — tuned partial agonism + bias profiling as
     mitigation.

4. Computational cross-validation (new)
   - Boltz-2 (BioLib) run on all 45 compounds: 45/45 completed. Finding:
     Boltz affinity probability shows no correlation with EC50 (r = -0.044),
     same null result as Vina (r = -0.114) — neither layer ranks potency;
     both are structural evidence, not affinity predictors.
   - Binding-site disagreement: Boltz predicts the orthosteric pocket
     (Arg71 anchor) for 29/45, Vina (8Z8A) predicts TM5-TM6 for the large
     series. Reference acids validate the orthosteric call. The true site for
     nM agonists is experimentally undecided — Arg71/Glu153 mutagenesis or
     co-crystallization would settle it.

5. Wet-lab benchmark proposal (next step, needs your input)
   - Stratified 20-compound panel: 9 leads + 2 partial-agonist probes +
     3 mechanism pairs + 2 Boltz controls + 4 reference acids; every analog
     counterscreened at GPR109A + GHS-R1a. Designed to calibrate the two
     computational layers against real EC50/Emax (Spearman + tier-confusion
     matrix). The panel CSV is ready to hand to the assay team.

Deliverables
   Shared drive (accessible to you):
     /TDE_TV/shared_folder/QYJI/druggability/output/2026-08-05/followup_2026_08/
       gpr81_followup_report.html      (self-contained, all 46 figures embedded)
       gpr81_boltz_wetlab_report.html  (three-layer report, 7 sections)
   Local audit trail:
     /das/user/QYJI/druggability/data/gpr81_phase1/followup_2026_08/
       gpr81_compound_scorecard.csv/.json · gpr81_pocket_analysis_pairs.csv/.json
       gpr81_optimization_recommendations.md · wetlab_benchmark_subset.csv
       data/boltz_results.csv/.json · audit_data_integrity.py (20/20 checks pass)

Happy to walk through anything, or adjust the benchmark panel before it goes
to the assay team.

Best,
Jay
