Subject: GPR81 (HCAR1) druggability follow-up — complete deliverable package + wet-lab proposal

Hi Huan,

The three follow-up deliverables you requested are complete, together with an
extra computational cross-validation layer and a proposed wet-lab benchmark
panel. Full details are in the self-contained reports; everything is on the
shared drive (links at the end).

1. Overall ranking of all 45 compounds
   - Ranked by reported experimental hGPR81 EC50, stratified into Tier A/B/C
     (EC50 + Emax + GPR109A/GHS-R1a selectivity).
   - Best-balanced lead: compound 28 (22 nM, 41x GPR109A, 82x GHSR, LLE 5.3).
   - Watch-outs: compound 30 is the most potent (5 nM) but only 7.4x
     GPR109A-selective; compound 5 (0.74 nM) is a partial agonist (Emax 47%).
   - Reference ligands (CHBA, 3,5-DHBA, 3-OBA, lactate) listed separately.

2. Binding-pocket analyses, all 46 ligand-receptor pairs
   - Per pair: multi-seed Vina score, binding region, polar/hydrophobic
     contact residues, pose position vs co-crystal ligand, EC50 context,
     with a structural illustration (46 figures embedded in the main report;
     also available as individual PNGs).
   - New control: lactate x 9KT9 tight-box run (12 A box, ex32, 3 seeds) —
     best -3.78 kcal/mol, 2.79 A centroid recovery (vs 2.89 A on cognate
     8Z8A): the endogenous ligand recovers the orthosteric pocket on both
     active-state structures.

3. Optimization & development recommendations
   - Keep the constrained pyridone template; avoid pyrimidinone (N3-Glu153
     clash, 47x potency cliff); exploit the Glu153(HCAR1)->Lys165(HCAR2)
     charge flip as a selectivity handle; retain the cis-2,6-dimethylmorpholine
     stereochemistry (c38: 54 nM, 500x GHSR, sol 95 uM).
   - Counterscreen every analog at GPR109A + GHS-R1a; design caps MW <= 550,
     clogP <= 4, LLE >= 5.
   - Safety: mechanism-based tumor/cachexia + liver-fibrosis risk (as flagged
     in the ticket) — tuned partial agonism + bias profiling as mitigation.

4. Computational cross-validation (new)
   - Boltz-2 (BioLib) on all 45 compounds: 45/45 completed. Finding: Boltz
     affinity probability shows no correlation with EC50 (r = -0.044), the
     same null result as Vina (r = -0.114) — neither layer ranks potency;
     both are structural evidence only.
   - Binding-site disagreement: Boltz predicts the orthosteric pocket (Arg71
     anchor) for 29/45 compounds, while Vina (8Z8A) places the large series
     in the TM5-TM6 extracellular region (12-14 A away; only 2/40 agree).
     Reference acids are orthosteric in both models (consistent with the
     co-crystals). The true site for the nM agonists is experimentally
     undecided — Arg71/Glu153 mutagenesis or co-crystallization would settle
     it.
   - HCAR2/HCAR3 AlphaFold models (BioLib) also completed and validated
     against AlphaFold DB v6 (TM-core Cα RMSD 2.92 A / 0.53 A) — available
     for the selectivity-handle design work.

5. Wet-lab benchmark proposal (needs your input)
   - Stratified 20-compound panel: 9 leads + 2 partial-agonist probes +
     3 mechanism pairs + 2 Boltz controls + 4 reference acids; every analog
     counterscreened at GPR109A + GHS-R1a. Designed to calibrate the two
     computational layers against real EC50/Emax (Spearman + tier confusion
     matrix). The panel CSV is ready to hand to the assay team — happy to
     adjust the composition before it goes.

Deliverables
   Shared drive (readout folder, accessible to you):
     /TDE_TV/shared_folder/QYJI/druggability/GPR81/readout/
       gpr81_onepager_summary.html (one-pager, EN version alongside) — quick overview
       gpr81_followup_report.html (main report, self-contained, 46 figures)
       gpr81_boltz_wetlab_report.html (three-layer report, 7 sections)
       figures/ (46 pocket-analysis PNGs) · data/ (all machine-readable CSVs/JSONs)
   Local audit trail:
     /das/user/QYJI/druggability/data/gpr81_phase1/followup_2026_08/
       (build scripts + audit script, 20/20 data-integrity checks pass)
   Ticket: RIC-396 (attachments + comments).

Happy to walk through anything — and let me know if the wet-lab panel should
be adjusted before it reaches the assay team.

Best,
Jay
