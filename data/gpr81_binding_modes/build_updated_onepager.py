#!/usr/bin/env python3
"""
Build updated executive one-pager HTML for GPR81:
Incorporates:
1. Orthosteric vs Allosteric resolution (Br J Pharmacol 2026, PMID 41435849)
2. HCAR2 (8J6P) allosteric structural homology (17.7 A crevice)
3. OpenMM + OpenFF Sage atomistic energetics (R71A +10.2 kcal/mol, E153A +6.6 kcal/mol)
4. In vitro validation roadmap
5. 100% English, strict 1920x1080 fixed-viewport compliance
"""

import os
import shutil

ONEPAGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GPR81 (HCAR1) Druggability — Executive Project Summary</title>
<style>
  html, body { width: 1920px; height: 1080px; margin: 0; padding: 0; overflow: hidden;
               font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; background: #eef1f6; color: #222; }
  .page { width: 1920px; height: 1080px; display: grid;
          grid-template-rows: 100px 100px 800px; gap: 12px;
          padding: 16px 20px; box-sizing: border-box; }

  header { background: linear-gradient(100deg, #001965, #14537e); color: #fff;
           border-radius: 10px; padding: 12px 24px; display: flex; align-items: center;
           justify-content: space-between; box-shadow: 0 2px 8px rgba(0,25,101,.15); }
  header h1 { margin: 0; font-size: 25px; letter-spacing: 0.3px; }
  header .sub { margin-top: 4px; font-size: 13px; color: #cfe0ef; }
  header .attr { text-align: right; font-size: 12px; line-height: 1.6; color: #dbe7f2; }

  .metrics { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
  .metric { background: #fff; border-radius: 10px; padding: 10px 16px; box-shadow: 0 1px 4px rgba(0,25,101,.10);
            display: flex; flex-direction: column; justify-content: center; border-top: 4px solid #14537e; }
  .metric .v { font-size: 26px; font-weight: 700; color: #001965; line-height: 1.05; }
  .metric .l { font-size: 11.5px; color: #556; margin-top: 4px; }

  main { display: grid; grid-template-columns: 1.05fr 1.25fr 1.0fr; gap: 12px; min-height: 0; }
  .card { background: #fff; border-radius: 10px; padding: 12px 16px; box-shadow: 0 1px 4px rgba(0,25,101,.08);
          display: flex; flex-direction: column; overflow: hidden; }
  .col1-stack { grid-column: 1/2; grid-row: 1/3; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
  .col1-stack > .card:first-child { flex: 0 0 auto; }
  .col1-stack > .card:last-child  { flex: 1 1 0; min-height: 0; }
  .col2 { grid-column: 2/3; grid-row: 1/3; }
  .col3-stack { grid-column: 3/4; grid-row: 1/3; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
  .col3-stack > .card { flex: 1 1 0; min-height: 0; }

  h2 { margin: 0 0 6px; font-size: 14.5px; color: #001965; border-bottom: 2px solid #14537e;
       padding-bottom: 3px; display: flex; justify-content: space-between; align-items: baseline; }
  h3 { margin: 7px 0 3px; font-size: 12.5px; color: #14537e; }
  ul { margin: 3px 0 5px; padding-left: 17px; font-size: 12px; line-height: 1.45; }
  li { margin: 2px 0; }
  .tag { display: inline-block; font-size: 9px; font-weight: 700; color: #fff; border-radius: 3px;
         padding: 0 4px; margin-right: 4px; vertical-align: 1px; }
  .tag.FACT { background: #1e7e34; } .tag.OBS { background: #b06d00; }
  .tag.MECH { background: #14537e; } .tag.HYP { background: #7b3fa0; }
  table { border-collapse: collapse; width: 100%; font-size: 11.5px; margin: 4px 0 5px; }
  th, td { border: 1px solid #d5dbe1; padding: 3px 5px; text-align: left; }
  th { background: #001965; color: #fff; font-weight: 600; font-size: 11px; }
  tr:nth-child(even) { background: #f0f4f7; }
  .callout { background: #fff8e1; border-left: 4px solid #f0ad4e; padding: 6px 10px; border-radius: 4px;
             font-size: 11.5px; line-height: 1.45; margin: 3px 0; }
  .callout.green { background: #f0fff4; border-left-color: #38a169; }
  .callout.blue { background: #e8f4fd; border-left-color: #2e86c1; }
  .callout.purple { background: #f3ecfa; border-left-color: #7b3fa0; }
  .muted { color: #666; font-size: 10.5px; line-height: 1.35; margin: 3px 0; }
  .kpi { display: flex; gap: 8px; margin: 4px 0; }
  .kpi .box { flex: 1; background: #f0f4f7; border-radius: 6px; padding: 4px 6px; text-align: center; }
  .kpi .box .b { font-size: 18px; font-weight: 700; color: #001965; }
  .kpi .box .bl { font-size: 9.5px; color: #556; }
  .flex-spacer { flex: 1 1 auto; min-height: 0; }
</style>
</head>
<body>
<div class="page">
  <header>
    <div>
      <h1>GPR81 / HCAR1 Druggability — Executive Platform Summary</h1>
      <div class="sub">Binding-Mode Resolution (Orthosteric vs Ago-PAM) · OpenMM Atomistic Energetics · 45-Compound SAR &amp; Wet-Lab Roadmap</div>
    </div>
    <div class="attr">RIC-396 (Comment 101684) · Requester UHYG (Target Discovery)<br>Analyst QYJI · Research Insights China (RIC) · Updated September 2026</div>
  </header>

  <div class="metrics">
    <div class="metric"><div class="v">45</div><div class="l">Compounds ranked &amp; stratified</div></div>
    <div class="metric"><div class="v">4 / 33 / 8</div><div class="l">Pure Ortho / Allo ago-PAM / Bitopic</div></div>
    <div class="metric"><div class="v">17.7 Å</div><div class="l">Ortho–Allo Crevice Distance (8J6P)</div></div>
    <div class="metric"><div class="v">7.71 Å</div><div class="l">Ternary Co-Occupancy (Lactate+Ag1)</div></div>
    <div class="metric"><div class="v">KKK Wall</div><div class="l">HCAR2 Anti-Flushing Barrier (K164-166)</div></div>
    <div class="metric"><div class="v">c28 / c38</div><div class="l">Best Leads (Pyridone / Bitopic Amide)</div></div>
  </div>

  <main>
    <!-- ============ Column 1 ============ -->
    <div class="col1-stack">
      <div class="card">
        <h2>Key findings &amp; platform context</h2>
        <ul>
          <li><span class="tag FACT">FACT</span><b>c28 is the best-balanced lead</b>: EC50 22 nM, 41x GPR109A, 82x GHSR, LLE 5.3; constrained pyridone core.</li>
          <li><span class="tag FACT">FACT</span>c30 most potent (5 nM) but only 7.4x GPR109A-selective; c5 (0.74 nM) is a partial agonist (Emax 47%).</li>
          <li><span class="tag OBS">OBS</span><b>Docking/Boltz scores do not rank potency</b> (r = −0.114 &amp; −0.044) — structural pose hypothesis only.</li>
          <li><span class="tag OBS">OBS</span>SAR cliff: pyridone ≫ pyrimidinone (N3–Glu153 clash, 47x potency drop between c30 and c31).</li>
          <li><span class="tag MECH">MECH</span><b>OpenFEP Suitability</b>: Ligand RBFE is inapplicable across non-congeneric scaffolds (lactate/AZ1/agonist 1); residue mutation FEP (R71A/E153A) and GPU MD are the rigorous physical tools.</li>
        </ul>
      </div>
      <div class="card">
        <h2>Binding-site resolution: Orthosteric vs Ago-PAM</h2>
        <div class="callout green">
          <span class="tag FACT">FACT</span><b>Literature Benchmark (Br J Pharmacol 2026, PMID 41435849):</b> ebBRET biosensor profiling formally established <b>GPR81 agonist 1 as an ago-PAM</b>, while AZ series are <b>orthosteric agonists</b>. Corroborates Target Discovery in vitro data.
        </div>
        <div class="callout blue">
          <span class="tag OBS">OBS</span><b>Ternary Co-Occupancy vs Steric Clash:</b> Lactate &amp; Agonist 1 cleanly co-occupy the receptor (d_min = 7.71 Å) without collision. Conversely, AZ1 and Agonist 1 collide sterically (d_min = 2.60 Å) at the vestibule, confirming mutual exclusion.
        </div>
        <div class="callout purple">
          <span class="tag MECH">MECH</span><b>Anti-Flushing Mechanism (HCAR1 vs HCAR2):</b> HCAR1 Leu152-Glu153-Asn154 becomes a triple-lysine basic wall (Lys164-Lys165-Lys166, +3 charge) in HCAR2, creating an electrostatic/steric barrier that prevents off-target flushing.
        </div>
        <h3>OpenMM + OpenFF Sage atomistic energetics &amp; in silico mutagenesis</h3>
        <ul>
          <li><span class="tag OBS">OBS</span><b>AZ1 (Orthosteric, Boltz-2)</b>: Deep Arg71 salt-bridge (-11.0 kcal/mol); in silico <b>R71A penalty +10.2 kcal/mol</b>. Trajectory RMSD 1.54 Å (tightly locked).</li>
          <li><span class="tag OBS">OBS</span><b>Agonist 1 (Allosteric, Vina)</b>: TM5-TM6 Glu153 anchor (-6.2 kcal/mol); in silico <b>E153A penalty +6.6 kcal/mol</b>. In orthosteric site, Arg71 interaction is repulsive (+2.7 kcal/mol).</li>
          <li><span class="tag FACT">FACT</span><b>Lactate Ground Truth</b>: Arg71 salt-bridge -3.6 kcal/mol (R71A penalty +3.7 kcal/mol); Glu153 electrostatic repulsion (+3.2 kcal/mol); weak mM Kd.</li>
        </ul>
        <div class="flex-spacer"></div>
        <p class="muted">Orthogonal in silico mutation fingerprints: R71A knocks out orthosteric AZ1; E153A knocks out allosteric agonist 1.</p>
      </div>
    </div>

    <!-- ============ Column 2 ============ -->
    <div class="card col2">
      <h2>Compound ranking &amp; leads (Tier A/B/C)</h2>
      <table>
        <tr><th>ID</th><th>EC50 (nM)</th><th>Emax</th><th>GPR109A ×</th><th>GHSR ×</th><th>Tier</th><th>Comment</th></tr>
        <tr><td><b>c05</b></td><td>0.74</td><td>47%</td><td>—</td><td>—</td><td>B</td><td>Partial agonist (most potent, low Emax)</td></tr>
        <tr><td><b>c04</b></td><td>1.4</td><td>—</td><td>—</td><td>—</td><td>A</td><td>Potent acyl-urea (selectivity unknown)</td></tr>
        <tr><td><b>c30</b></td><td>5.0</td><td>—</td><td>7.4</td><td>—</td><td>B</td><td>Most potent, insufficient selectivity</td></tr>
        <tr><td><b>c28</b></td><td>22</td><td>—</td><td>41</td><td>82</td><td><b>A</b></td><td><b>Best-balanced lead (LLE 5.3)</b></td></tr>
        <tr><td><b>c26</b></td><td>21</td><td>—</td><td>29</td><td>62</td><td>A</td><td>Candidate lead (benzothiazole RHS)</td></tr>
        <tr><td><b>c38</b></td><td>54</td><td>—</td><td>10</td><td>500</td><td>B</td><td>Amide series + cis-morpholine (sol 95 µM)</td></tr>
        <tr><td><b>c29</b></td><td>75</td><td>—</td><td>25</td><td>667</td><td>B</td><td>High GHSR selectivity (CH2OH-sulfone)</td></tr>
        <tr><td><b>c31</b></td><td>240</td><td>—</td><td>—</td><td>—</td><td>C</td><td>Pyrimidinone control (47x loss vs c30)</td></tr>
      </table>
      <p class="muted">Ranking basis: paper hGPR81 EC50; Tier A = EC50 ≤ 50 nM, Emax ≥ 80%, selectivity ≥ 25x/50x; B = ≤ 100 nM with liability; C = rest. Reference acids listed separately. LLE = pEC50 - logD.</p>

      <h3>Structure-based design &amp; optimization rules</h3>
      <ul>
        <li><span class="tag FACT">FACT</span><b>Template Pre-organization</b>: Retain constrained pyridone ring; acyclic acyl-ureas depend on fragile intramolecular H-bonds (N-Me / CH2 insertion drops EC50 to 16–33 µM).</li>
        <li><span class="tag MECH">MECH</span><b>Selectivity Handle (HCAR2 Counter-screen)</b>: Exploit Glu153(HCAR1) → Lys165(HCAR2) charge flip. Basic/neutral RHS vectors attract Glu153 while clashing with Lys165.</li>
        <li><span class="tag FACT">FACT</span><b>RHS Stereochemistry</b>: cis-2,6-dimethylmorpholine (c38: 54 nM, 500x GHSR, sol 95 µM) outperforms trans (c37: 350 nM) by 6.5x in potency and solubility.</li>
        <li><span class="tag OBS">OBS</span><b>Property Boundaries</b>: MW ≤ 550, clogP ≤ 4.0, LLE ≥ 5.0; counter-screen every analogue at GPR109A + GHS-R1a.</li>
      </ul>
      <h3>Mechanism strategic implications</h3>
      <div class="callout blue">
        <b>Orthosteric (AZ1/c28) vs Ago-PAM (Agonist 1):</b> Orthosteric agonists drive rapid acute suppression of lipolysis but risk desensitization and cachexia pathway exposure. An ago-PAM preserves endogenous lactate physiological pacing and offers an intrinsic ceiling effect — ideal for T2D durability.
      </div>
    </div>

    <!-- ============ Column 3 ============ -->
    <div class="col3-stack">
      <div class="card">
        <h2>Validation roadmap (In vitro &amp; structural)</h2>
        <div class="kpi">
          <div class="box"><div class="b">9</div><div class="bl">Leads</div></div>
          <div class="box"><div class="b">2</div><div class="bl">Probes</div></div>
          <div class="box"><div class="b">3</div><div class="bl">Mech Pairs</div></div>
          <div class="box"><div class="b">2</div><div class="bl">Boltz Ctrls</div></div>
          <div class="box"><div class="b">4</div><div class="bl">Ref Acids</div></div>
        </div>
        <ul>
          <li><b>Step 1: Functional Schild Shift (cAMP)</b>: Titrate lactate curves with fixed agonist 1. Saturable leftward EC50 shift (cooperativity α &gt; 1) and/or baseline elevation confirms ago-PAM mode.</li>
          <li><b>Step 2: Dual-Residue Alanine Knockout</b>: Construct <b>R71A</b> (orthosteric) vs <b>E153A</b> (allosteric) mutants. AZ1 collapses on R71A; agonist 1 collapses on E153A.</li>
          <li><b>Step 3: Cryo-EM Complex (Ground Truth)</b>: 8Z8A/8Z87/8Z8B protocols (2.8 Å) enable reconstitution of HCAR1-Gi1-scFv16 with AZ1 or agonist 1 for atomic-level IP.</li>
        </ul>
        <h3>Safety &amp; translation (preclinical gate)</h3>
        <div class="callout" style="background:#fff5f5; border-left:4px solid #d9383a; margin-top:2px;">
          Mechanism-based <b>tumor/cachexia</b> + <b>liver-fibrosis</b> liability (HCAR1 axis). Mitigation: partial agonism or ago-PAM profile; monitor preclinical oncogenic markers.
        </div>
      </div>
      <div class="card">
        <h2>Deliverables &amp; shared access</h2>
        <table>
          <tr><th>Deliverable Artifact</th><th>Format / Location</th></tr>
          <tr><td><b>gpr81_binding_mode_evaluation.html</b></td><td>Interactive HTML: Ortho vs Allo &amp; FEP Study</td></tr>
          <tr><td><b>email_draft_to_huan.txt</b></td><td>Plain-text colleague email (paste-ready)</td></tr>
          <tr><td><b>gpr81_onepager_summary_en.html</b></td><td>Executive 1920×1080 dashboard (this file)</td></tr>
          <tr><td><b>gpr81_followup_report.html</b></td><td>46-pair pocket report (46 figures embedded)</td></tr>
          <tr><td><b>gpr81_boltz_wetlab_report.html</b></td><td>Vina × Boltz-2 cross-validation report</td></tr>
          <tr><td><b>openmm_pilot_results.json</b></td><td>Atomistic simulation &amp; mutation energy data</td></tr>
          <tr><td><b>wetlab_benchmark_subset.csv</b></td><td>Stratified 20-compound wet-lab panel</td></tr>
        </table>
        <p class="muted">
          Shared Drive: <code>R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\</code><br>
          Jira Ticket: <b>RIC-396</b> (Logged in Comment 101684) · NNRCC Research Insights China
        </p>
      </div>
    </div>
  </main>
</div>
</body>
</html>
"""

def main():
    paths = [
        "/das/user/QYJI/druggability/data/gpr81_phase1/followup_2026-08/gpr81_onepager_summary_en.html",
        "/TDE_TV/shared_folder/QYJI/druggability/GPR81/readout/gpr81_onepager_summary_en.html",
        "/das/user/QYJI/druggability/data/gpr81_binding_modes/gpr81_onepager_summary_en.html",
    ]
    
    # Assert 100% English: no Chinese characters
    for line_idx, line in enumerate(ONEPAGER_HTML.splitlines(), 1):
        for ch in line:
            if '\u4e00' <= ch <= '\u9fff':
                raise ValueError(f"Found Chinese character '{ch}' on line {line_idx}!")
                
    for p in paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(ONEPAGER_HTML.strip() + "\n")
        print(f"Successfully written: {p} ({len(ONEPAGER_HTML)} bytes)")

if __name__ == "__main__":
    main()
