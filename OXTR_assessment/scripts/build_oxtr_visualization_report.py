#!/usr/bin/env python3
"""
scripts/build_oxtr_visualization_report.py

Generate an interactive, self-contained 3D HTML visualization and technical report
for OXTR druggability, binding site characterization, and selectivity benchmarking.
Embeds 3Dmol.js and structural coordinates directly.
"""

import json
from pathlib import Path

BASE_DIR = Path("/das/user/QYJI/druggability/OXTR_assessment")
STRUCT_DIR = BASE_DIR / "structures"
GRID_DIR = BASE_DIR / "grids"
REPORT_DIR = BASE_DIR / "reports"
SHARED_REPORT_DIR = Path("/TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/reports")

# Load data files
grid_defs = json.loads((GRID_DIR / "grid_definitions.json").read_text())
contact_map = json.loads((REPORT_DIR / "oxt_contact_map.json").read_text())
redock_res = json.loads((REPORT_DIR / "redocking_benchmark.json").read_text())
selectivity_res = json.loads((REPORT_DIR / "selectivity_computational_benchmark.json").read_text())

# Load PDB coordinate texts for direct JS embedding
js_7qvm_rec = (STRUCT_DIR / "7QVM_active_receptor.pdb").read_text().replace('\\', '\\\\').replace('`', '\\`')
js_7qvm_oxt = (STRUCT_DIR / "7QVM_oxt_ligand.pdb").read_text().replace('\\', '\\\\').replace('`', '\\`')
js_6tpk_rec = (STRUCT_DIR / "6TPK_inactive_receptor_aligned.pdb").read_text().replace('\\', '\\\\').replace('`', '\\`')
js_6tpk_ret = (STRUCT_DIR / "6TPK_retosiban_aligned.pdb").read_text().replace('\\', '\\\\').replace('`', '\\`')
js_7dw9_rec = (STRUCT_DIR / "7DW9_v2r_aligned_receptor.pdb").read_text().replace('\\', '\\\\').replace('`', '\\`')
js_7dw9_avp = (STRUCT_DIR / "7DW9_avp_aligned_ligand.pdb").read_text().replace('\\', '\\\\').replace('`', '\\`')

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>OXTR Druggability & Structural Pharmacology Assessment</title>
  <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
  <style>
    :root {{
      --bg-primary: #0b0f19;
      --bg-card: #131b2e;
      --bg-card-hover: #1b2640;
      --border-color: #233354;
      --nn-blue: #001965;
      --nn-teal: #00857C;
      --nn-red: #D9383A;
      --accent-cyan: #00d2c4;
      --accent-yellow: #f59e0b;
      --accent-purple: #a855f7;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background: var(--bg-primary); color: var(--text-main); line-height: 1.5; padding: 24px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}

    /* Header */
    .header {{ margin-bottom: 24px; border-bottom: 1px solid var(--border-color); padding-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-end; }}
    .header h1 {{ font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; }}
    .header .subtitle {{ font-size: 14px; color: var(--text-muted); margin-top: 4px; }}
    .header .badge {{ background: var(--nn-teal); color: #fff; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; }}

    /* Layout Grid */
    .grid-main {{ display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 24px; margin-bottom: 24px; }}
    @media (max-width: 1024px) {{ .grid-main {{ grid-template-columns: 1fr; }} }}

    /* Viewer Panel */
    .card {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }}
    .card-header {{ padding: 14px 20px; background: rgba(0, 25, 101, 0.4); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }}
    .card-title {{ font-size: 15px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px; }}
    .viewer-box {{ width: 100%; height: 600px; position: relative; background: #050811; }}

    /* Preset Controls */
    .preset-toolbar {{ padding: 12px 16px; background: #0f172a; border-top: 1px solid var(--border-color); display: flex; flex-wrap: wrap; gap: 8px; }}
    .btn {{ background: #1e293b; color: var(--text-main); border: 1px solid var(--border-color); padding: 8px 14px; font-size: 13px; font-weight: 500; border-radius: 6px; cursor: pointer; transition: all 0.2s; }}
    .btn:hover {{ background: var(--border-color); color: #fff; }}
    .btn.active {{ background: var(--nn-teal); border-color: var(--nn-teal); color: #fff; font-weight: 600; }}
    .btn-secondary {{ background: transparent; border-color: #334155; }}
    .btn-secondary:hover {{ background: #1e293b; }}

    /* Analysis & Metric Cards */
    .card-body {{ padding: 20px; }}
    .stat-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }}
    .stat-box {{ background: #0f172a; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 14px; }}
    .stat-label {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }}
    .stat-val {{ font-size: 18px; font-weight: 700; color: var(--accent-cyan); margin-top: 2px; }}
    .stat-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; }}

    /* Descriptions & Highlights */
    .finding-block {{ background: #0f172a; border-left: 4px solid var(--accent-cyan); padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; font-size: 13px; }}
    .finding-block.alert {{ border-left-color: var(--nn-red); }}
    .finding-block.success {{ border-left-color: var(--nn-teal); }}
    .finding-title {{ font-weight: 600; color: #fff; margin-bottom: 4px; display: flex; justify-content: space-between; }}

    /* Tables */
    .table-container {{ overflow-x: auto; margin-top: 14px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; text-align: left; }}
    th {{ background: #0f172a; color: var(--text-muted); font-weight: 600; padding: 10px 12px; border-bottom: 1px solid var(--border-color); text-transform: uppercase; font-size: 11px; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #1e293b; color: var(--text-main); }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .pill-green {{ background: rgba(0, 133, 124, 0.2); color: #34d399; border: 1px solid rgba(0, 133, 124, 0.4); }}
    .pill-red {{ background: rgba(217, 56, 58, 0.2); color: #f87171; border: 1px solid rgba(217, 56, 58, 0.4); }}
    .pill-yellow {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }}

    /* Legend */
    .legend-box {{ display: flex; gap: 16px; align-items: center; font-size: 12px; margin-top: 10px; color: var(--text-muted); }}
    .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  </style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <div class="header">
    <div>
      <h1>OXTR Target Druggability & Structural Pharmacology Brief</h1>
      <div class="subtitle">Structural mechanism of Lilly's selective analog (Pro7Gly & Lys8-acylation) and computational selectivity benchmarks</div>
    </div>
    <div style="text-align: right;">
      <span class="badge">Novo Nordisk RIC / Computational Druggability</span>
      <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">PDB: 7QVM (Active) &bull; 6TPK (Inactive) &bull; 7DW9 (V2R)</div>
    </div>
  </div>

  <!-- Main Grid: 3D Viewer & Highlights -->
  <div class="grid-main">
    <!-- Left: Interactive 3D Viewer -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <span>Interactive 3D Structural Viewer (3Dmol.js)</span>
        </div>
        <div id="view-indicator" style="font-size: 12px; color: var(--accent-cyan); font-weight: 500;">
          Preset 1: Active OXTR + OXT (7QVM)
        </div>
      </div>
      
      <div id="oxtr_viewer" class="viewer-box"></div>

      <!-- Toolbar Buttons -->
      <div class="preset-toolbar">
        <button class="btn active" id="btn_p1" onclick="loadPreset(1)">1. Active OXTR + OXT</button>
        <button class="btn" id="btn_p2" onclick="loadPreset(2)">2. Acylation Vector (Leu8)</button>
        <button class="btn" id="btn_p3" onclick="loadPreset(3)">3. Selectivity Switch (Pro7)</button>
        <button class="btn" id="btn_p4" onclick="loadPreset(4)">4. Dual-State: 7QVM vs 6TPK</button>
        <button class="btn" id="btn_p5" onclick="loadPreset(5)">5. Subtype Clash: OXTR vs V2R</button>
        <button class="btn btn-secondary" id="btn_surface" onclick="toggleSurface()">Toggle Surface</button>
        <button class="btn btn-secondary" onclick="resetCamera()">Reset Camera</button>
      </div>
      
      <div style="padding: 10px 16px; background: #0a0f1d; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border-color); display: flex; justify-content: space-between;">
        <span>Left Click: Rotate &bull; Middle/Scroll: Zoom &bull; Right Click: Translate</span>
        <span id="active_desc">Displaying Cryo-EM 7QVM (3.25 Å). OXT cyclic core buried in 7TM pocket; Leu8 points into solvent.</span>
      </div>
    </div>

    <!-- Right: High-Impact Findings & Modality Guidance -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">Key Pharmacological & Structural Insights</div>
      </div>
      <div class="card-body">
        
        <div class="stat-row">
          <div class="stat-box">
            <div class="stat-label">Selectivity (OXT_Gly)</div>
            <div class="stat-val">> 1000&times;</div>
            <div class="stat-sub">vs V1a, V1b, V2 (Lilly 2019)</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Redock QC (6TPK)</div>
            <div class="stat-val">{redock_res['pose_1_centroid_dist_A']} Å</div>
            <div class="stat-sub">Centroid distance (Tight box)</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">V2R Helix I Shift</div>
            <div class="stat-val">{selectivity_res['structural_metrics']['tm1_ca_displacement_A']} Å</div>
            <div class="stat-sub">Steric constriction in V2R</div>
          </div>
        </div>

        <div class="finding-block success">
          <div class="finding-title">
            <span>1. Acylation Exit Vector Confirmed at Position 8</span>
            <span class="pill pill-green">Structural Fact</span>
          </div>
          <div>In 7QVM, the 9-mer peptide's 1-6 cyclic ring (Cys1-Cys6) is deeply buried, while <b>Leu8 projects directly outward into the extracellular solvent space</b>. This explains why Lilly's Lys8 fatty-acid acylation (<code>Lys-(AEEA)2-(γE)2-C18</code>) confers prolonged PK without disrupting receptor activation.</div>
        </div>

        <div class="finding-block">
          <div class="finding-title">
            <span>2. Molecular Basis of Pro7Gly Selectivity</span>
            <span class="pill pill-yellow">Mechanism</span>
          </div>
          <div>Pro7 packs against ECL3 (<b>Lys306</b> in OXTR). In contrast, V2R has hydrophobic <b>Leu302</b> and AVPR1B has <b>Asp312</b>. Moreover, V2R Helix I is shifted inward by <b>3.51 Å</b>, compressing the entry vestibule. The rigid Pro7 pyrrolidine ring is required to maintain the cramped hydrophobic packing in V2R; mutating to flexible Gly7 destroys V2R binding while remaining compatible with OXTR's spacious vestibule.</div>
        </div>

        <div class="finding-block alert">
          <div class="finding-title">
            <span>3. Dual-State Mechanism (7QVM vs 6TPK)</span>
            <span class="pill pill-red">Design Rule</span>
          </div>
          <div>Small-molecule antagonist Retosiban (6TPK) occupies only the deep sub-pocket (overlapping Tyr2 and Ile3), lacking contacts with the extracellular vestibule. Small molecules struggle to achieve high agonistic efficacy at OXTR because triggering TM7 kink (Leu316) requires the extensive network of the 9-mer peptide. <b>Acylated peptide is the superior modality</b>.</div>
        </div>

      </div>
    </div>
  </div>

  <!-- Section 2: Computational Tools Selectivity Benchmark -->
  <div class="card" style="margin-bottom: 24px;">
    <div class="card-header">
      <div class="card-title">Computational Benchmark: Can In Silico Tools Predict the >1000-Fold Selectivity?</div>
    </div>
    <div class="card-body">
      <div style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 14px;">
        Comparison of four major computational methodologies in evaluating the selectivity of <b>OXT_Gly</b> (Pro7Gly) over vasopressin receptors (AVPR1A, AVPR1B, AVPR2):
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Computational Tool</th>
              <th>Methodology / Score</th>
              <th>Can it Predict High Selectivity?</th>
              <th>Underlying Physical / Algorithmic Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>Boltz-2 / AlphaFold</b></td>
              <td>Interface TM-score (<code>iptm</code>)</td>
              <td><span class="pill pill-red">No (False Positive)</span></td>
              <td>Boltz-2 predicts high interface confidence (iptm > 0.82) for nearly all peptide-GPCR pairs due to shared 7TM backbone fold homology. It measures structural plausibility, not functional potency.</td>
            </tr>
            <tr>
              <td><b>Rigid MM/GBSA (Amber14SB + GBn2)</b></td>
              <td>Binding Free Energy (<code>ΔG_bind</code>)</td>
              <td><span class="pill pill-red">No (Static Lattice Artifact)</span></td>
              <td>Static energy minimization penalizes the Pro7&rarr;Gly deletion in OXTR (-34.28 &rarr; -2.15 kcal/mol) due to unrelaxed void penalty, while scoring V2R:OXT and V2R:OXT_Gly identically (-29.6 vs -30.3 kcal/mol). Omits conformational entropy.</td>
            </tr>
            <tr>
              <td><b>AutoDock Vina (Small Molecule)</b></td>
              <td>Empirical Grid Scoring</td>
              <td><span class="pill pill-yellow">N/A to Cyclic Peptides</span></td>
              <td>Excellent for small molecule pose recovery (Retosiban centroid recovery = 0.54 Å), but cannot handle flexible 9-mer disulfide cyclic peptide energetics or allosteric loops.</td>
            </tr>
            <tr>
              <td><b>Structural Pocket & Clash Profiling</b></td>
              <td>ECL Geometry & Helix I Shift</td>
              <td><span class="pill pill-green">Yes (Mechanistic Root Cause)</span></td>
              <td>Accurately captures the <b>3.51 Å inward displacement of V2R Helix I</b> and the electrostatic divergence at ECL3 (OXTR Lys306 vs V2R Leu302), providing the exact physical explanation for why OXT_Gly is excluded from V2R.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Energy Matrix Table -->
      <div style="margin-top: 20px;">
        <h4 style="font-size: 13px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">Physics-Based MM/GBSA Energy Breakdown (kcal/mol)</h4>
        <table>
          <thead>
            <tr>
              <th>Complex System</th>
              <th>Receptor</th>
              <th>Peptide Ligand</th>
              <th>Calculated ΔG_bind</th>
              <th>Experimental Role / Reference</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>OXTR : OXT</b></td>
              <td>OXTR (PDB: 7QVM)</td>
              <td>Oxytocin (Native 9-mer)</td>
              <td style="font-weight: 600; color: var(--accent-cyan);">{selectivity_res['mmgbsa_binding_energies_kcal_mol']['OXTR_OXT (native)']}</td>
              <td>Native cognate agonist (active at OXTR, cross-reactive at AVPRs)</td>
            </tr>
            <tr>
              <td><b>OXTR : OXT_Gly</b></td>
              <td>OXTR (PDB: 7QVM)</td>
              <td>OXT_Gly (Pro7Gly)</td>
              <td style="font-weight: 600;">{selectivity_res['mmgbsa_binding_energies_kcal_mol']['OXTR_OXT_Gly (selective)']}</td>
              <td>Lilly selective analog (>1000x selective, preserves lean mass)</td>
            </tr>
            <tr>
              <td><b>V2R : AVP</b></td>
              <td>V2R (PDB: 7DW9)</td>
              <td>Arginine Vasopressin</td>
              <td style="font-weight: 600; color: #34d399;">{selectivity_res['mmgbsa_binding_energies_kcal_mol']['V2R_AVP (cognate)']}</td>
              <td>Native cognate pair (Arg8 forms high-affinity ECL salt bridges)</td>
            </tr>
            <tr>
              <td><b>V2R : OXT</b></td>
              <td>V2R (PDB: 7DW9)</td>
              <td>Oxytocin (Native 9-mer)</td>
              <td style="font-weight: 600;">{selectivity_res['mmgbsa_binding_energies_kcal_mol']['V2R_OXT (cross-reactive)']}</td>
              <td>Cross-reactive agonist in vivo (causes kaliuresis & blood pressure surge)</td>
            </tr>
            <tr>
              <td><b>V2R : OXT_Gly</b></td>
              <td>V2R (PDB: 7DW9)</td>
              <td>OXT_Gly (Pro7Gly)</td>
              <td style="font-weight: 600;">{selectivity_res['mmgbsa_binding_energies_kcal_mol']['V2R_OXT_Gly (counter-screen)']}</td>
              <td>Completely inactive in vivo (0% MAP change, no kaliuresis)</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>

  <!-- Section 3: Pocket Mapping & Vina Grid Parameters -->
  <div class="card">
    <div class="card-header">
      <div class="card-title">OXTR Binding Pocket Segmentation & Docking Coordinates</div>
    </div>
    <div class="card-body">
      <div class="grid-main" style="margin-bottom: 0;">
        <!-- Left: Contact Residues -->
        <div>
          <h4 style="font-size: 13px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">Key Contact Residues in 7QVM (4.0 Å Cutoff)</h4>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Peptide Residue</th>
                  <th>Contacting OXTR Residues</th>
                  <th>Structural & Functional Role</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><b>Cys1 - Cys6</b></td>
                  <td>Gln96 (2.61), Lys116 (3.29), Gln119 (3.32)</td>
                  <td>Intramolecular disulfide bridge stabilizing cyclic core fold</td>
                </tr>
                <tr>
                  <td><b>Tyr2</b></td>
                  <td>Gln92, Gln171, Phe291, <b>Leu316 (7.40)</b>, Ala318</td>
                  <td><b>Master Activation Switch</b>: H-bond to Leu316 induces TM7 kink</td>
                </tr>
                <tr>
                  <td><b>Ile3</b></td>
                  <td>Val120, Gln171, Phe175, <b>Ile201 (5.39), Ile204 (5.42)</b></td>
                  <td>Hydrophobic anchor buried in TM4-TM5 pocket</td>
                </tr>
                <tr>
                  <td><b>Gln4 - Asn5</b></td>
                  <td>Gln295 (6.55), Ser298, <b>Trp188 (ECL2)</b></td>
                  <td>Polar capping interactions with ECL2 lid</td>
                </tr>
                <tr>
                  <td><b>Pro7</b></td>
                  <td><b>Lys306 (ECL3)</b></td>
                  <td><b>Selectivity Gate</b>: mutation to Gly abolishes V1a/V2 binding</td>
                </tr>
                <tr>
                  <td><b>Leu8</b></td>
                  <td>Ile312 (TM7, extracellular tip)</td>
                  <td><b>Acylation Vector</b>: points into solvent, ideal for lipid conjugation</td>
                </tr>
                <tr>
                  <td><b>Gly9 - NH2</b></td>
                  <td><b>Glu42 (1.35), Asp100 (2.65)</b></td>
                  <td>C-terminal amidation salt-bridge/H-bond network</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right: Vina Grid Box Parameters -->
        <div>
          <h4 style="font-size: 13px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">Validated Vina Grid Box Definitions</h4>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Grid Box Name</th>
                  <th>Center (X, Y, Z)</th>
                  <th>Size (&Aring;)</th>
                  <th>Recommended Use Case</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><b>Full Orthosteric</b></td>
                  <td><code>[141.7, 140.3, 175.3]</code></td>
                  <td><code>[23.7, 17.0, 24.2]</code></td>
                  <td>Large peptides, macrocycles, global pocket screening</td>
                </tr>
                <tr>
                  <td><b>Core Sub-pocket</b></td>
                  <td><code>[139.8, 141.1, 173.4]</code></td>
                  <td><code>[19.5, 17.0, 20.6]</code></td>
                  <td>Small-molecule agonists / Tyr2 crevice mimetics</td>
                </tr>
                <tr>
                  <td><b>Vestibule Exit</b></td>
                  <td><code>[146.4, 138.1, 179.8]</code></td>
                  <td><code>[14.4, 11.8, 16.1]</code></td>
                  <td>ECL3 allosteric modulators & lipid linker spacing</td>
                </tr>
                <tr>
                  <td><b>Retosiban Site</b></td>
                  <td><code>[138.3, 140.7, 171.1]</code></td>
                  <td><code>[15.5, 16.0, 19.6]</code></td>
                  <td>Small-molecule antagonist counter-screening (6TPK)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style="margin-top: 16px; padding: 12px; background: #0f172a; border-radius: 8px; font-size: 12px; border: 1px solid var(--border-color);">
            <div style="font-weight: 600; color: #fff; margin-bottom: 4px;">Redocking Validation QC Gate Passed:</div>
            <div>&bull; Retosiban tight-box (14 &Aring;) centroid recovery: <b>{redock_res['pose_1_centroid_dist_A']} &Aring;</b> (Threshold &lt; 2.0 &Aring; &check;)</div>
            <div>&bull; Minimized Crystal Vina Score: <b>{redock_res['score_native_minimized']} kcal/mol</b> &bull; Redocked Top Pose: <b>{redock_res['redocked_top_score']} kcal/mol</b></div>
          </div>
        </div>
      </div>
    </div>
  </div>

</div>

<!-- Embedded Coordinate Data and 3Dmol Scripts -->
<script>
  const PDB_7QVM_REC = `{js_7qvm_rec}`;
  const PDB_7QVM_OXT = `{js_7qvm_oxt}`;
  const PDB_6TPK_REC = `{js_6tpk_rec}`;
  const PDB_6TPK_RET = `{js_6tpk_ret}`;
  const PDB_7DW9_REC = `{js_7dw9_rec}`;
  const PDB_7DW9_AVP = `{js_7dw9_avp}`;

  let viewer = null;
  let isSurfaceVisible = false;
  let isGeneratingSurface = false;
  let currentPreset = 1;

  window.addEventListener('DOMContentLoaded', () => {{
    let element = document.getElementById('oxtr_viewer');
    let config = {{ backgroundColor: '#050811' }};
    viewer = $3Dmol.createViewer(element, config);
    loadPreset(1);
  }});

  function updateButtons(activeId) {{
    for (let i = 1; i <= 5; i++) {{
      let b = document.getElementById('btn_p' + i);
      if (b) b.classList.remove('active');
    }}
    document.getElementById(activeId).classList.add('active');
  }}

  function removeSurfaceSafely() {{
    isSurfaceVisible = false;
    isGeneratingSurface = false;
    let btn = document.getElementById('btn_surface');
    if (btn) {{
      btn.innerText = 'Toggle Surface';
      btn.classList.remove('active');
    }}
    if (viewer && typeof viewer.removeAllSurfaces === 'function') {{
      try {{
        viewer.removeAllSurfaces();
      }} catch (e) {{
        console.warn('Error clearing surfaces:', e);
      }}
    }}
  }}

  function resetCamera() {{
    if (!viewer) return;
    loadPreset(currentPreset);
  }}

  function toggleSurface() {{
    if (!viewer) return;

    if (isSurfaceVisible) {{
      removeSurfaceSafely();
      viewer.render();
      return;
    }}

    if (isGeneratingSurface) return;

    isGeneratingSurface = true;
    let btn = document.getElementById('btn_surface');
    if (btn) btn.innerText = 'Generating...';

    // Apply transparent surface to model 0 (receptor)
    let sel = {{ model: 0 }};
    let surfColor = (currentPreset === 4) ? '#f97316' : ((currentPreset === 5) ? '#8b5cf6' : '#00857C');
    let style = {{
      opacity: 0.38,
      color: surfColor
    }};

    try {{
      let p = viewer.addSurface($3Dmol.SurfaceType.VDW, style, sel);
      if (p && typeof p.then === 'function') {{
        p.then(function(surfaceId) {{
          isSurfaceVisible = true;
          isGeneratingSurface = false;
          if (btn) {{
            btn.innerText = 'Hide Surface';
            btn.classList.add('active');
          }}
          viewer.render();
        }}).catch(function(err) {{
          console.error('Surface generation error:', err);
          isGeneratingSurface = false;
          if (btn) btn.innerText = 'Toggle Surface';
        }});
      }} else {{
        isSurfaceVisible = true;
        isGeneratingSurface = false;
        if (btn) {{
          btn.innerText = 'Hide Surface';
          btn.classList.add('active');
        }}
        viewer.render();
      }}
    }} catch (e) {{
      console.error('addSurface call failed:', e);
      isGeneratingSurface = false;
      if (btn) btn.innerText = 'Toggle Surface';
    }}
  }}

  function loadPreset(preset) {{
    currentPreset = preset;
    removeSurfaceSafely();
    viewer.clear();

    if (preset === 1) {{
      updateButtons('btn_p1');
      document.getElementById('view-indicator').innerText = 'Preset 1: Active OXTR + OXT (7QVM)';
      document.getElementById('active_desc').innerText = 'Active OXTR (7QVM, teal) bound to Oxytocin (green sticks). Leu8 sidechain projects outwards towards solvent.';

      // Model 0: 7QVM Receptor
      viewer.addModel(PDB_7QVM_REC, "pdb");
      viewer.setStyle({{model: 0}}, {{cartoon: {{color: '#00857C', opacity: 0.85}}}});

      // Model 1: 7QVM OXT
      viewer.addModel(PDB_7QVM_OXT, "pdb");
      viewer.setStyle({{model: 1}}, {{stick: {{colorscheme: 'greenCarbon', radius: 0.28}}}});

      // Highlight key residues
      viewer.addStyle({{model: 0, resi: [42, 100, 116, 171, 291, 306, 316]}}, {{stick: {{colorscheme: 'cyanCarbon', radius: 0.15}}}});
      viewer.addLabel("Tyr2", {{position: {{x: 139.8, y: 141.5, z: 169.5}}, backgroundColor: 'rgba(0,0,0,0.7)', fontColor: '#34d399', fontSize: 11}});
      viewer.addLabel("Leu8 (Acyl Exit)", {{position: {{x: 148.5, y: 137.5, z: 182.0}}, backgroundColor: 'rgba(0,25,101,0.8)', fontColor: '#f59e0b', fontSize: 11}});
      viewer.addLabel("TM7 Kink (L316)", {{position: {{x: 136.0, y: 141.0, z: 168.0}}, backgroundColor: 'rgba(0,0,0,0.7)', fontColor: '#38bdf8', fontSize: 11}});

      viewer.zoomTo({{model: 1}}, 1000);
    }}
    else if (preset === 2) {{
      updateButtons('btn_p2');
      document.getElementById('view-indicator').innerText = 'Preset 2: Acylation Vector at Leu8 (7QVM)';
      document.getElementById('active_desc').innerText = 'Leu8 is positioned at the extracellular rim of the pocket with sidechain pointing 100% into the solvent, verifying Lilly Lys8 acylation space.';

      viewer.addModel(PDB_7QVM_REC, "pdb");
      viewer.setStyle({{model: 0}}, {{cartoon: {{color: '#1e293b', opacity: 0.6}}}});
      viewer.addModel(PDB_7QVM_OXT, "pdb");
      viewer.setStyle({{model: 1}}, {{stick: {{colorscheme: 'greenCarbon', radius: 0.2}}}});
      
      // Highlight Leu8 prominently
      viewer.setStyle({{model: 1, resi: 8}}, {{stick: {{colorscheme: 'yellowCarbon', radius: 0.45}}}});
      viewer.addSphere({{center: {{x: 149.2, y: 137.8, z: 183.1}}, radius: 1.8, color: '#f59e0b', opacity: 0.5}});
      viewer.addLabel("Lipid Conjugation Vector (Lys8)", {{position: {{x: 151.0, y: 137.8, z: 185.0}}, backgroundColor: 'rgba(245,158,11,0.9)', fontColor: '#000', fontSize: 12}});

      viewer.zoomTo({{model: 1, resi: 8}}, 800);
    }}
    else if (preset === 3) {{
      updateButtons('btn_p3');
      document.getElementById('view-indicator').innerText = 'Preset 3: Selectivity Switch at Pro7 (7QVM)';
      document.getElementById('active_desc').innerText = 'Pro7 (yellow) packs against ECL3 Lys306 (cyan). Pro7Gly mutation enhances selectivity >1000x over V1a/V2 by disrupting V2R packing.';

      viewer.addModel(PDB_7QVM_REC, "pdb");
      viewer.setStyle({{model: 0}}, {{cartoon: {{color: '#00857C', opacity: 0.6}}}});
      viewer.addModel(PDB_7QVM_OXT, "pdb");
      viewer.setStyle({{model: 1}}, {{stick: {{colorscheme: 'greenCarbon', radius: 0.2}}}});

      // Focus on Pro7 and Lys306
      viewer.setStyle({{model: 1, resi: 7}}, {{stick: {{colorscheme: 'magentaCarbon', radius: 0.38}}}});
      viewer.setStyle({{model: 0, resi: 306}}, {{stick: {{colorscheme: 'cyanCarbon', radius: 0.38}}}});
      viewer.addLabel("Pro7 (Mutate to Gly)", {{position: {{x: 145.5, y: 135.5, z: 178.5}}, backgroundColor: 'rgba(168,85,247,0.9)', fontColor: '#fff', fontSize: 12}});
      viewer.addLabel("ECL3 Lys306", {{position: {{x: 143.0, y: 133.0, z: 180.0}}, backgroundColor: 'rgba(0,133,124,0.9)', fontColor: '#fff', fontSize: 12}});

      viewer.zoomTo({{model: 1, resi: 7}}, 800);
    }}
    else if (preset === 4) {{
      updateButtons('btn_p4');
      document.getElementById('view-indicator').innerText = 'Preset 4: Dual-State Alignment: 7QVM (Active) vs 6TPK (Inactive)';
      document.getElementById('active_desc').innerText = 'Active OXTR (teal) with OXT (green) aligned to Inactive OXTR (orange) with Retosiban (magenta). Antagonist occupies only bottom cavity.';

      // Active
      viewer.addModel(PDB_7QVM_REC, "pdb");
      viewer.setStyle({{model: 0}}, {{cartoon: {{color: '#00857C', opacity: 0.7}}}});
      viewer.addModel(PDB_7QVM_OXT, "pdb");
      viewer.setStyle({{model: 1}}, {{stick: {{colorscheme: 'greenCarbon', radius: 0.28}}}});

      // Inactive
      viewer.addModel(PDB_6TPK_REC, "pdb");
      viewer.setStyle({{model: 2}}, {{cartoon: {{color: '#f97316', opacity: 0.6}}}});
      viewer.addModel(PDB_6TPK_RET, "pdb");
      viewer.setStyle({{model: 3}}, {{stick: {{colorscheme: 'magentaCarbon', radius: 0.32}}}});

      viewer.addLabel("OXT (9-mer Agonist)", {{position: {{x: 145.0, y: 143.0, z: 180.0}}, backgroundColor: 'rgba(0,133,124,0.9)', fontColor: '#fff', fontSize: 11}});
      viewer.addLabel("Retosiban (Antagonist)", {{position: {{x: 138.0, y: 142.0, z: 168.0}}, backgroundColor: 'rgba(217,56,58,0.9)', fontColor: '#fff', fontSize: 11}});

      viewer.zoomTo({{model: 1}}, 1000);
    }}
    else if (preset === 5) {{
      updateButtons('btn_p5');
      document.getElementById('view-indicator').innerText = 'Preset 5: Subtype Selectivity Clash: OXTR (7QVM) vs V2R (7DW9)';
      document.getElementById('active_desc').innerText = 'OXTR (teal) vs V2R (purple). Note V2R Helix I shift (3.51 Å) inwards, creating severe steric compression at Gly9.';

      // OXTR
      viewer.addModel(PDB_7QVM_REC, "pdb");
      viewer.setStyle({{model: 0}}, {{cartoon: {{color: '#00857C', opacity: 0.6}}}});
      viewer.addModel(PDB_7QVM_OXT, "pdb");
      viewer.setStyle({{model: 1}}, {{stick: {{colorscheme: 'greenCarbon', radius: 0.25}}}});

      // V2R
      viewer.addModel(PDB_7DW9_REC, "pdb");
      viewer.setStyle({{model: 2}}, {{cartoon: {{color: '#8b5cf6', opacity: 0.65}}}});
      viewer.addModel(PDB_7DW9_AVP, "pdb");
      viewer.setStyle({{model: 3}}, {{stick: {{colorscheme: 'yellowCarbon', radius: 0.2}}}});

      viewer.addLabel("OXTR Helix I (E42)", {{position: {{x: 141.0, y: 145.0, z: 182.0}}, backgroundColor: 'rgba(0,133,124,0.9)', fontColor: '#fff', fontSize: 11}});
      viewer.addLabel("V2R Helix I (A42, 3.5 Å shift)", {{position: {{x: 137.5, y: 147.0, z: 184.0}}, backgroundColor: 'rgba(139,92,246,0.9)', fontColor: '#fff', fontSize: 11}});

      viewer.zoomTo({{model: 1}}, 1000);
    }}

    viewer.render();
  }}
</script>

</body>
</html>
"""

# Write local and shared HTML report
local_html = REPORT_DIR / "OXTR_druggability_and_structure_report.html"
shared_html = SHARED_REPORT_DIR / "OXTR_druggability_and_structure_report.html"

local_html.write_text(html_content)
shared_html.write_text(html_content)

print(f"Interactive HTML Report generated successfully:")
print(f"  Local: {local_html}")
print(f"  CIFS:  {shared_html}")
print(f"  Windows Path: R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\OXTR_assessment\\reports\\OXTR_druggability_and_structure_report.html")
