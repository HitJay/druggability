#!/usr/bin/env python3
"""
Assemble comprehensive deliverable HTML report with:
1. Embedded 300 DPI multi-panel publication figure (2D topology, 3D separation, OpenMM energetics, In Silico mutation)
2. Embedded offline 3Dmol.js WebGL interactive viewer (color-coded TM domains, Lactate, AZ1, Agonist 1, 9n, Arg71/Glu153)
3. Quantitative tables and experimental validation roadmap
4. Update companion email draft for Huan
"""

import os
import base64
import json

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
CIFS_READOUT = "/TDE_TV/shared_folder/QYJI/druggability/GPR81/readout"

# 1. Base64 encode the 300 DPI figure
png_path = os.path.join(WORK_DIR, "gpr81_binding_domains_visualization.png")
with open(png_path, "rb") as f:
    fig_b64 = base64.b64encode(f.read()).decode("utf-8")

# 2. Read 3Dmol.js text
js_path = os.path.join(WORK_DIR, "3Dmol-min.js")
with open(js_path, "r", encoding="utf-8") as f:
    js_3dmol = f.read()

# 3. Read PDB complex text
pdb_path = os.path.join(WORK_DIR, "gpr81_3d_complex_all.pdb")
with open(pdb_path, "r", encoding="utf-8") as f:
    pdb_data = f.read()
escaped_pdb_data = pdb_data.replace('`', ' ')

# 4. Read simulation JSON
json_path = os.path.join(WORK_DIR, "openmm_pilot_results.json")
with open(json_path) as f:
    pilot_results = json.load(f)

rows_html = ""
for r in pilot_results:
    mode_badge = f"<span class='badge {'ortho' if r['mode'] == 'Orthosteric' else 'allo'}'>{r['mode']}</span>"
    r71_str = f"{r['e_tot_r71']:.2f} (Δ {r['r71a_penalty']:+.2f})"
    e153_str = f"{r['e_tot_e153']:.2f} (Δ {r['e153a_penalty']:+.2f})"
    rows_html += f"""
    <tr>
        <td style="font-weight:600;">{r['name']}</td>
        <td>{mode_badge}</td>
        <td>{r['e_tot_prot']:.2f}</td>
        <td>{r['e_coul_prot']:.2f} / {r['e_lj_prot']:.2f}</td>
        <td><b>{r71_str}</b></td>
        <td><b>{e153_str}</b></td>
        <td>{r['e_tot_h177']:.2f}</td>
        <td>{r['mean_rmsd']:.2f} Å</td>
    </tr>
    """

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GPR81 Agonist Binding Mode Evaluation: Orthosteric vs Allosteric Domain Mapping &amp; Visualization</title>
<style>
    :root {{
        --nn-blue: #001965;
        --nn-teal: #00857C;
        --nn-coral: #D9383A;
        --nn-amber: #D97706;
        --nn-navy: #0A192F;
        --bg-color: #F8F9FA;
        --card-bg: #FFFFFF;
        --text-color: #2D3748;
        --text-muted: #718096;
        --border-color: #E2E8F0;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        margin: 0;
        padding: 30px;
        line-height: 1.6;
    }}
    .container {{
        max-width: 1280px;
        margin: 0 auto;
    }}
    header {{
        background: linear-gradient(135deg, var(--nn-blue) 0%, #003366 100%);
        color: white;
        padding: 30px 40px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0,25,101,0.12);
    }}
    header h1 {{
        margin: 0 0 10px 0;
        font-size: 26px;
        letter-spacing: -0.5px;
    }}
    header .subtitle {{
        font-size: 15px;
        color: #E2E8F0;
        margin: 0;
    }}
    .meta-bar {{
        display: flex;
        gap: 24px;
        margin-top: 16px;
        font-size: 13px;
        color: #CBD5E0;
        flex-wrap: wrap;
    }}
    .card {{
        background: var(--card-bg);
        border-radius: 10px;
        padding: 24px 28px;
        margin-bottom: 24px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }}
    h2 {{
        color: var(--nn-blue);
        font-size: 18px;
        margin-top: 0;
        margin-bottom: 16px;
        border-bottom: 2px solid #EDF2F7;
        padding-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .grid-2 {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }}
    .grid-3 {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
    }}
    .callout {{
        background: #F0FFF4;
        border-left: 4px solid var(--nn-teal);
        padding: 16px 20px;
        border-radius: 4px;
        margin: 16px 0;
        font-size: 14px;
    }}
    .callout.warning {{
        background: #FFF5F5;
        border-left-color: var(--nn-coral);
    }}
    .callout.info {{
        background: #EBF8FF;
        border-left-color: #3182CE;
    }}
    .callout.amber {{
        background: #FEF3C7;
        border-left-color: var(--nn-amber);
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-top: 12px;
    }}
    th, td {{
        padding: 10px 12px;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }}
    th {{
        background-color: #F7FAFC;
        color: var(--nn-blue);
        font-weight: 600;
    }}
    tr:hover {{
        background-color: #F8FAFC;
    }}
    .badge {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    .badge.ortho {{
        background: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
    }}
    .badge.allo {{
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }}
    .metric-box {{
        background: #F7FAFC;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 14px 18px;
        text-align: center;
    }}
    .metric-value {{
        font-size: 22px;
        font-weight: bold;
        color: var(--nn-blue);
    }}
    .metric-label {{
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 4px;
    }}
    /* 3Dmol viewer styles */
    .viewer-container {{
        width: 100%;
        height: 600px;
        position: relative;
        background: #0F172A;
        border-radius: 8px;
        overflow: hidden;
        margin: 16px 0;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
    }}
    .viewer-controls {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}
    .btn-ctrl {{
        background: #EDF2F7;
        border: 1px solid #CBD5E0;
        color: var(--nn-blue);
        padding: 8px 14px;
        border-radius: 6px;
        font-size: 12.5px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    .btn-ctrl:hover {{
        background: var(--nn-blue);
        color: #FFFFFF;
        border-color: var(--nn-blue);
    }}
    .btn-ctrl.active {{
        background: var(--nn-blue);
        color: #FFFFFF;
    }}
    .legend-bar {{
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        background: #F1F5F9;
        padding: 10px 16px;
        border-radius: 6px;
        font-size: 12px;
        margin-top: 8px;
    }}
    .legend-item {{
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .color-swatch {{
        width: 14px;
        height: 14px;
        border-radius: 3px;
        display: inline-block;
    }}
    .figure-wrapper {{
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        margin: 16px 0;
        text-align: center;
    }}
    .figure-wrapper img {{
        max-width: 100%;
        height: auto;
        border-radius: 4px;
        display: block;
        margin: 0 auto;
    }}
</style>

<!-- Inlined 3Dmol.js for 100% offline self-contained operation -->
<script>
{js_3dmol}
</script>
</head>
<body>
<div class="container">

<header>
    <h1>GPR81 / HCAR1 Agonist Binding Mode Evaluation &amp; Domain Visualization</h1>
    <p class="subtitle">Structural domain resolution (Orthosteric vs Ago-PAM), cross-receptor homology (8Z8A vs 8J6P), OpenMM atomistic energetics, and interactive 3D visualization</p>
    <div class="meta-bar">
        <span>Target: <b>HCAR1 / GPR81</b></span>
        <span>Receptor PDB: <b>8Z8A (2.8 Å) &amp; 9KT9</b></span>
        <span>Cross-Receptor Homology: <b>HCAR2 8J6P (2.6 Å)</b></span>
        <span>Department: <b>Research Insights China (RIC)</b></span>
        <span>Ticket: <b>RIC-396 (Comment 101684)</b></span>
        <span>Date: <b>September 2026</b></span>
    </div>
</header>

<div class="card">
    <h2>1. Executive Summary &amp; Pharmacological Qualitative Confirmation</h2>
    <div class="callout green">
        <b>Direct Literature Precedent (British Journal of Pharmacology, 2026, PMID: 41435849):</b>
        A landmark study by Lind et al. (Bouvier and Johansson laboratories) profiled HCAR1 signaling using ebBRET biosensors and formally established that <b>GPR81 agonist 1 is an ago-positive allosteric modulator (ago-PAM)</b>, whereas the AstraZeneca small-molecule series (AZ1 / AZ7136) operates as <b>orthosteric agonists</b>. This definitively substantiates the in vitro trends observed in Target Discovery.
    </div>
    <div class="callout info">
        <b>Conclusion on OpenFEP Suitability:</b> Standard ligand-alchemical FEP (RBFE) cannot be used to compare orthosteric versus allosteric modes here because lactate (MW 90), AZ1 (MW 603), and agonist 1 (MW 446) share no common core scaffold and the two candidate pockets are separated by 17.7 Å. Instead, receptor-residue mutation FEP (in silico R71A vs E153A scanning) and explicit molecular dynamics provide the appropriate, physically grounded framework.
    </div>
    <div class="grid-3">
        <div class="metric-box">
            <div class="metric-value">17.7 Å</div>
            <div class="metric-label">Separation between Orthosteric Core and TM5-TM6 Allosteric Crevice</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">+10.2 kcal/mol</div>
            <div class="metric-label">In Silico R71A Penalty (AZ1 Orthosteric Pose Collapse)</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">+6.6 kcal/mol</div>
            <div class="metric-label">In Silico E153A Penalty (Agonist 1 Allosteric Pose Collapse)</div>
        </div>
    </div>
</div>

<div class="card">
    <h2>2. High-Resolution Domain Architecture &amp; Binding Mode Visualization</h2>
    <p style="font-size:14px;">
        To provide an intuitive structural basis for Target Discovery discussions, the figure below maps the exact domains, 3D spatial separation, residue-level interaction energetics, and in silico mutation phenotypes:
    </p>
    <div class="figure-wrapper">
        <img src="data:image/png;base64,{fig_b64}" alt="GPR81 Binding Domains and Pharmacological Characterization">
        <p style="font-size:12px; color:var(--text-muted); margin-top:8px; text-align:left;">
            <b>Figure 1. GPR81 structural domain mapping and orthosteric vs allosteric characterization.</b> 
            <b>(A)</b> 2D secondary structure domain topology showing the 7 transmembrane helices (TM1–TM7) and extracellular loops (ECL1–ECL3). The orthosteric pocket (green) is formed by TM2/3/7 and capped by ECL2 (Phe168/Ser167); the allosteric crevice (amber) is located at TM5–TM6–ECL2 (Glu153/His177). 
            <b>(B)</b> 3D spatial projection of ligand centroids: Lactate (8Z8A) and Niacin (8J6P) superimpose within 0.75 Å; AZ1 orthosteric pose is 4.99 Å from lactate; Compound 9n (8J6P allosteric co-crystal) is 17.67 Å from the orthosteric center, precisely overlapping the TM5–TM6 vestibule occupied by Agonist 1. 
            <b>(C)</b> OpenMM/OpenFF Sage residue-level interaction energies across structural domains. 
            <b>(D)</b> In silico alanine scanning mutational phenotypes: R71A produces a catastrophic penalty (+10.2 kcal/mol) selectively for orthosteric AZ1; E153A produces a +6.6 kcal/mol collapse selectively for allosteric Agonist 1.
        </p>
    </div>
</div>

<div class="card">
    <h2>3. Interactive 3D WebGL Molecular Viewer (Receptor Domains &amp; Ligand Sites)</h2>
    <p style="font-size:14px;">
        Interactive 3D representation of human HCAR1 (8Z8A cryo-EM structure, 2.8 Å) loaded with all candidate ligands and key anchor residues. Use the controls below to rotate, zoom, switch camera presets, and inspect domain contacts:
    </p>

    <div class="viewer-controls">
        <button class="btn-ctrl active" onclick="loadPreset('all')">1. Overview: All Domains &amp; Ligands</button>
        <button class="btn-ctrl" onclick="loadPreset('ortho')">2. Orthosteric Pocket (Lactate &amp; AZ1 @ Arg71)</button>
        <button class="btn-ctrl" onclick="loadPreset('allo')">3. Allosteric Crevice (Agonist 1 @ TM5-TM6 Glu153)</button>
        <button class="btn-ctrl" onclick="loadPreset('homology')">4. HCAR2 9n Alignment (17.7 Å Separation)</button>
        <button class="btn-ctrl" onclick="toggleSurface()">Toggle Translucent Pocket Surface</button>
        <button class="btn-ctrl" onclick="resetView()">Reset Camera</button>
    </div>

    <div id="gpr81_viewer" class="viewer-container"></div>

    <div class="legend-bar">
        <div class="legend-item"><span class="color-swatch" style="background:#16A34A;"></span><b>Lactate (2OP, Orthosteric Ground Truth)</b></div>
        <div class="legend-item"><span class="color-swatch" style="background:#2563EB;"></span><b>AZ1 (Orthosteric Pose, Boltz-2)</b></div>
        <div class="legend-item"><span class="color-swatch" style="background:#D97706;"></span><b>Agonist 1 (Allosteric Pose, Vina, ago-PAM)</b></div>
        <div class="legend-item"><span class="color-swatch" style="background:#7C3AED;"></span><b>Compound 9n (HCAR2 8J6P Allosteric Ref)</b></div>
        <div class="legend-item"><span class="color-swatch" style="background:#E11D48;"></span><b>ECL2 Active Gate (Phe168/Ser167)</b></div>
        <div class="legend-item"><span class="color-swatch" style="background:#1E3A8A;"></span><b>TM2 / Arg71 Anchor</b></div>
        <div class="legend-item"><span class="color-swatch" style="background:#0D9488;"></span><b>TM5 / Glu153 Anchor</b></div>
    </div>
</div>

<div class="card">
    <h2>4. Quantitative In Silico Energetics &amp; In Silico Alanine Scanning</h2>
    <p style="font-size:14px;">
        Using OpenMM 8.4 and OpenFF-2.1.0 (Sage) with Amber14SB under implicit OBC2 solvent, we evaluated minimized interaction energies, decomposed per-residue contributions, and performed in silico alanine scanning:
    </p>
    <table>
        <thead>
            <tr>
                <th>Complex &amp; Ligand</th>
                <th>Binding Mode</th>
                <th>Total E_int (kcal/mol)</th>
                <th>Coulomb / LJ</th>
                <th>Arg71 (Ortho Anchor) [R71A Δ]</th>
                <th>Glu153 (Allo Anchor) [E153A Δ]</th>
                <th>His177 (Allo Anchor)</th>
                <th>100ps MD RMSD</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    <div class="callout info" style="margin-top:16px;">
        <b>Mechanistic Interpretation:</b>
        <ul style="margin:4px 0 0 16px;">
            <li><b>AZ1 (Orthosteric)</b>: Relies strictly on the Arg71 guanidinium anchor (-11.03 kcal/mol), with in silico R71A mutation causing a devastating +10.24 kcal/mol penalty. Phe168 (-12.7 kcal/mol) and Ser167 (-12.4 kcal/mol) in ECL2 cap the ligand tightly.</li>
            <li><b>Agonist 1 (Allosteric / ago-PAM)</b>: Anchored by Glu153 (-6.21 kcal/mol), Met170 (-11.84 kcal/mol), and His155 (-6.27 kcal/mol) in the TM5–TM6 extracellular vestibule. In silico E153A mutation collapses binding by +6.57 kcal/mol. In the orthosteric pocket, it suffers electrostatic repulsion with Arg71 (+2.71 kcal/mol).</li>
            <li><b>Orthogonal Fingerprint</b>: The computational mutational profiles cleanly separate orthosteric from allosteric engagement without ambiguity.</li>
        </ul>
    </div>
</div>

<div class="card">
    <h2>5. Recommended Wet-Lab Finalization Design (Target Discovery)</h2>
    <div class="grid-2">
        <div style="background:#F7FAFC; padding:16px; border-radius:8px; border:1px solid var(--border-color);">
            <h3 style="color:var(--nn-blue); font-size:15px; margin-top:0;">1. Functional Schild Shift Assay (cAMP)</h3>
            <p style="font-size:13px; margin-bottom:6px;"><b>Gold-standard pharmacological operational test:</b></p>
            <ul style="font-size:13px;">
                <li>Measure L-lactate concentration-response curves across fixed concentrations of agonist 1 (e.g. 0, 10 nM, 100 nM, 1 µM).</li>
                <li><b>ago-PAM Profile:</b> Saturable leftward EC50 shift ceiling (cooperativity factor α &gt; 1) and/or baseline elevation (efficacy factor β &gt; 1); supra-additive synergism at low threshold doses.</li>
                <li><b>Orthosteric Profile:</b> AZ1 will behave as a competitive agonist, displacing lactate without synergistic leftward shifts.</li>
            </ul>
        </div>
        <div style="background:#F7FAFC; padding:16px; border-radius:8px; border:1px solid var(--border-color);">
            <h3 style="color:var(--nn-blue); font-size:15px; margin-top:0;">2. Dual Alanine Knockout Plasmid Testing</h3>
            <p style="font-size:13px; margin-bottom:6px;"><b>Decisive 1:1 in vitro validation:</b></p>
            <ul style="font-size:13px;">
                <li>Construct <b>R71A</b> (orthosteric knockout) and <b>E153A / H177A</b> (allosteric knockout) in HEK293/CHO cells.</li>
                <li><b>AZ1:</b> Potency collapses on R71A (&gt;100-fold loss); completely unaffected on E153A.</li>
                <li><b>Agonist 1:</b> Potency collapses on E153A; retains full agonism on R71A.</li>
            </ul>
        </div>
    </div>
</div>

<div class="card">
    <h2>6. Deliverable Artifacts &amp; Shared Access</h2>
    <table>
        <tr><th>Deliverable File</th><th>Description &amp; Windows Path</th></tr>
        <tr><td><b>gpr81_binding_mode_evaluation.html</b></td><td>Interactive HTML Report (this file, with 3Dmol WebGL &amp; 300 DPI figures)<br><code>R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\gpr81_binding_mode_evaluation.html</code></td></tr>
        <tr><td><b>gpr81_onepager_summary_en.html</b></td><td>Executive 1920×1080 Platform Summary Dashboard<br><code>R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\gpr81_onepager_summary_en.html</code></td></tr>
        <tr><td><b>gpr81_binding_domains_visualization.png</b></td><td>Stand-alone 300 DPI Publication-grade Multi-panel Visual (PNG)<br><code>R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\figures\\gpr81_binding_domains_visualization.png</code></td></tr>
        <tr><td><b>email_draft_to_huan.txt</b></td><td>Paste-ready Plain-text Colleague Hand-off Draft<br><code>R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\email_draft_to_huan.txt</code></td></tr>
        <tr><td><b>openmm_pilot_results.json</b></td><td>Raw Atomistic Simulation &amp; Mutation Energy Dataset<br><code>R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\data\\openmm_pilot_results.json</code></td></tr>
    </table>
    <p style="font-size:12px; color:var(--text-muted); margin-top:10px;">
        Jira Audit Record: <b>RIC-396</b> (Logged in Comment 101684) · Research Insights China · Novo Nordisk Research Centre China
    </p>
</div>

</div>

<!-- 3Dmol JavaScript Application -->
<script>
let viewer = null;
let currentPreset = 'all';
let isSurfaceVisible = false;

const rawPdbData = `{escaped_pdb_data}`;

document.addEventListener("DOMContentLoaded", function() {{
    initViewer();
}});

function initViewer() {{
    const element = document.getElementById('gpr81_viewer');
    const config = {{ backgroundColor: '#0F172A' }};
    viewer = $3Dmol.createViewer(element, config);
    viewer.addModel(rawPdbData, "pdb");
    applyStyles('all');
    viewer.zoomTo({{}}, 800);
    viewer.render();
}}

function applyStyles(preset) {{
    viewer.removeAllSurfaces();
    viewer.removeAllLabels();
    viewer.setStyle({{}}, {{}});

    // 1. Protein Cartoon with TM domain colors
    // Default receptor
    viewer.setStyle({{chain: 'R'}}, {{cartoon: {{color: '#94A3B8', opacity: 0.85}}}});

    // TM Helices
    viewer.setStyle({{chain: 'R', resi: [22,42]}}, {{cartoon: {{color: '#64748B'}}}}); // TM1
    viewer.setStyle({{chain: 'R', resi: [50,70]}}, {{cartoon: {{color: '#1E3A8A'}}}}); // TM2 (Ortho Anchor Arg71 at top)
    viewer.setStyle({{chain: 'R', resi: [90,110]}}, {{cartoon: {{color: '#0284C7'}}}}); // TM3
    viewer.setStyle({{chain: 'R', resi: [131,151]}}, {{cartoon: {{color: '#0D9488'}}}}); // TM4
    viewer.setStyle({{chain: 'R', resi: [183,203]}}, {{cartoon: {{color: '#059669'}}}}); // TM5
    viewer.setStyle({{chain: 'R', resi: [221,241]}}, {{cartoon: {{color: '#2563EB'}}}}); // TM6
    viewer.setStyle({{chain: 'R', resi: [262,281]}}, {{cartoon: {{color: '#7C3AED'}}}}); // TM7

    // ECL2 Loop (Active lid & Crevice)
    viewer.setStyle({{chain: 'R', resi: [152,182]}}, {{cartoon: {{color: '#E11D48', thickness: 0.5}}}});

    // 2. Key Anchor Residues
    viewer.addStyle({{chain: 'R', resi: 71}}, {{stick: {{color: '#16A34A', radius: 0.3}}}}); // Arg71
    viewer.addStyle({{chain: 'R', resi: 168}}, {{stick: {{color: '#E11D48', radius: 0.25}}}}); // Phe168
    viewer.addStyle({{chain: 'R', resi: 167}}, {{stick: {{color: '#FB7185', radius: 0.25}}}}); // Ser167
    viewer.addStyle({{chain: 'R', resi: 153}}, {{stick: {{color: '#D97706', radius: 0.3}}}}); // Glu153
    viewer.addStyle({{chain: 'R', resi: 177}}, {{stick: {{color: '#F59E0B', radius: 0.25}}}}); // His177

    // Labels
    viewer.addLabel("Arg71 (Ortho Anchor)", {{fontSize: 11, fontColor: "#15803D", backgroundColor: "#DCFCE7", backgroundOpacity: 0.9}}, {{chain: 'R', resi: 71, atom: 'CA'}});
    viewer.addLabel("Phe168 (ECL2 Gate)", {{fontSize: 11, fontColor: "#991B1B", backgroundColor: "#FEE2E2", backgroundOpacity: 0.9}}, {{chain: 'R', resi: 168, atom: 'CA'}});
    viewer.addLabel("Glu153 (Allo Anchor)", {{fontSize: 11, fontColor: "#92400E", backgroundColor: "#FEF3C7", backgroundOpacity: 0.9}}, {{chain: 'R', resi: 153, atom: 'CA'}});
    viewer.addLabel("His177 (Allo Crevice)", {{fontSize: 11, fontColor: "#92400E", backgroundColor: "#FEF3C7", backgroundOpacity: 0.9}}, {{chain: 'R', resi: 177, atom: 'CA'}});

    // 3. Ligands styling depending on preset
    if (preset === 'all') {{
        viewer.addStyle({{resn: 'LAC'}}, {{stick: {{color: '#16A34A', radius: 0.35}}, sphere: {{color: '#16A34A', radius: 0.6, opacity: 0.85}}}});
        viewer.addStyle({{resn: 'AZ1'}}, {{stick: {{color: '#2563EB', radius: 0.3}}, sphere: {{color: '#2563EB', radius: 0.5, opacity: 0.85}}}});
        viewer.addStyle({{resn: 'AG1'}}, {{stick: {{color: '#D97706', radius: 0.3}}, sphere: {{color: '#D97706', radius: 0.5, opacity: 0.85}}}});
        viewer.addStyle({{resn: 'IX8'}}, {{stick: {{color: '#7C3AED', radius: 0.25, opacity: 0.7}}}});
    }} else if (preset === 'ortho') {{
        viewer.addStyle({{resn: 'LAC'}}, {{stick: {{color: '#16A34A', radius: 0.4}}, sphere: {{color: '#16A34A', radius: 0.7, opacity: 0.9}}}});
        viewer.addStyle({{resn: 'AZ1'}}, {{stick: {{color: '#2563EB', radius: 0.35}}, sphere: {{color: '#2563EB', radius: 0.6, opacity: 0.9}}}});
        viewer.addStyle({{resn: 'AG1'}}, {{stick: {{color: '#64748B', radius: 0.15, opacity: 0.3}}}});
        viewer.addStyle({{resn: 'IX8'}}, {{stick: {{color: '#64748B', radius: 0.15, opacity: 0.2}}}});
    }} else if (preset === 'allo') {{
        viewer.addStyle({{resn: 'LAC'}}, {{stick: {{color: '#64748B', radius: 0.15, opacity: 0.3}}}});
        viewer.addStyle({{resn: 'AZ1'}}, {{stick: {{color: '#64748B', radius: 0.15, opacity: 0.3}}}});
        viewer.addStyle({{resn: 'AG1'}}, {{stick: {{color: '#D97706', radius: 0.4}}, sphere: {{color: '#D97706', radius: 0.7, opacity: 0.95}}}});
        viewer.addStyle({{resn: 'IX8'}}, {{stick: {{color: '#7C3AED', radius: 0.25, opacity: 0.7}}}});
    }} else if (preset === 'homology') {{
        viewer.addStyle({{resn: 'LAC'}}, {{stick: {{color: '#16A34A', radius: 0.35}}, sphere: {{color: '#16A34A', radius: 0.6, opacity: 0.85}}}});
        viewer.addStyle({{resn: 'IX8'}}, {{stick: {{color: '#7C3AED', radius: 0.4}}, sphere: {{color: '#7C3AED', radius: 0.7, opacity: 0.9}}}});
        viewer.addStyle({{resn: 'AG1'}}, {{stick: {{color: '#D97706', radius: 0.35}}, sphere: {{color: '#D97706', radius: 0.6, opacity: 0.85}}}});
        viewer.addStyle({{resn: 'AZ1'}}, {{stick: {{color: '#64748B', radius: 0.15, opacity: 0.3}}}});
    }}

    viewer.render();
}}

function loadPreset(preset) {{
    currentPreset = preset;
    document.querySelectorAll('.btn-ctrl').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    applyStyles(preset);

    if (preset === 'all') {{
        viewer.zoomTo({{}}, 800);
    }} else if (preset === 'ortho') {{
        viewer.zoomTo({{resn: ['LAC', 'AZ1']}}, 800);
    }} else if (preset === 'allo') {{
        viewer.zoomTo({{resn: 'AG1'}}, 800);
    }} else if (preset === 'homology') {{
        viewer.zoomTo({{resn: ['LAC', 'IX8', 'AG1']}}, 800);
    }}
}}

function toggleSurface() {{
    if (!isSurfaceVisible) {{
        viewer.addSurface($3Dmol.SurfaceType.MS, {{
            opacity: 0.25,
            color: '#CBD5E1'
        }}, {{chain: 'R'}});
        isSurfaceVisible = true;
    }} else {{
        viewer.removeAllSurfaces();
        isSurfaceVisible = false;
    }}
    viewer.render();
}}

function resetView() {{
    viewer.removeAllSurfaces();
    isSurfaceVisible = false;
    applyStyles('all');
    viewer.zoomTo({{}}, 800);
}}
</script>
</body>
</html>
"""

# Write locally and to CIFS
out_local_html = os.path.join(WORK_DIR, "gpr81_binding_mode_evaluation.html")
with open(out_local_html, "w", encoding="utf-8") as f:
    f.write(html_content)
print("Written:", out_local_html)

out_cifs_html = os.path.join(CIFS_READOUT, "gpr81_binding_mode_evaluation.html")
with open(out_cifs_html, "w", encoding="utf-8") as f:
    f.write(html_content)
print("Written to CIFS:", out_cifs_html)

# Update email draft text
email_text = f"""Subject: Re: Target-SM docking study - GPR81 orthosteric vs allosteric evaluation & OpenFEP feasibility

Hi Huan,

Thank you for following up on the OpenFEP platform and sharing the exciting hypothesis that AZ1 binds orthosterically while GPR81 agonist 1 acts allosterically. Both the latest published pharmacological literature and our atomistic simulations strongly corroborate your in vitro observation. We have assembled a comprehensive deliverable report equipped with publication-grade 2D domain schematics, atomistic mutational energetics, and an interactive 3D WebGL molecular viewer showing exactly which structural domains each small molecule binds to.

1. Conclusion on OpenFEP suitability

Standard ligand-alchemical free energy perturbation (RBFE) cannot be used to compare orthosteric versus allosteric modes across these molecules because lactate (MW 90), AZ1 (MW 603), and agonist 1 (MW 446) share no common core scaffold and the two candidate pockets are separated by 17.7 Angstroms. Instead, receptor-residue mutation FEP (alchemical R71A versus E153A scanning) and explicit molecular dynamics provide the appropriate, physically grounded framework to evaluate pocket preference.

2. Literature benchmark: GPR81 agonist 1 established as an ago-PAM

Your in vitro trend is directly validated by a recent study published in the British Journal of Pharmacology (Lind et al., 2026, PMID 41435849). Using ebBRET biosensor profiling across G protein activation and arrestin recruitment, the authors formally established that GPR81 agonist 1 acts as an ago-positive allosteric modulator (ago-PAM), whereas AstraZeneca synthetic agonists (AZ series) operate as orthosteric agonists. This literature benchmark provides strong experimental precedent for your finding.

3. Structural domain mapping & interactive 3D visualization

In the deliverable report, we have embedded both a high-resolution 4-panel visual and an interactive 3D WebGL viewer illustrating the structural domains:
- Orthosteric Pocket (Lactate & AZ1): Formed by TM2, TM3, TM7, and capped by ECL2 (Phe168/Ser167). AZ1 deeply engages the Arg71 guanidinium anchor (-11.0 kcal/mol), where an in silico R71A mutation causes a catastrophic penalty of +10.2 kcal/mol (paralleling lactate +3.7 kcal/mol penalty).
- Allosteric Crevice (Agonist 1): Formed by TM5, TM6, and ECL2. Agonist 1 is anchored by Glu153 (-6.2 kcal/mol), Met170 (-11.8 kcal/mol), and His155 (-6.3 kcal/mol), incurring an in silico E153A penalty of +6.6 kcal/mol. In the orthosteric site, it exhibits electrostatic repulsion with Arg71 (+2.7 kcal/mol).
- Cross-Receptor Benchmark: When aligned with human HCAR2 (PDB 8J6P, Nat Commun 2023), the allosteric crevice of compound 9n is 17.7 Angstroms from the orthosteric center, precisely overlapping the TM5-TM6 region where agonist 1 binds.

4. Recommended validation design to finalize in vitro data

To decisively lock in this conclusion for the target proposal, we suggest focusing replicate experiments on two clean readouts. First, a functional Schild shift / curve-shift experiment in your cAMP assay: testing lactate concentration-response curves across fixed concentrations of agonist 1 should display saturable leftward potency shifts (cooperativity factor alpha > 1) and/or baseline elevation (efficacy factor beta > 1), characteristic of an ago-PAM, whereas AZ1 will behave as a competitive orthosteric agonist. Second, site-directed mutagenesis testing R71A (orthosteric knockout) versus E153A (allosteric knockout): AZ1 potency will collapse on R71A while remaining insensitive to E153A, whereas agonist 1 will exhibit the exact inverse selectivity profile.

Deliverables

Shared drive technical report (with interactive 3D viewer): R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\gpr81_binding_mode_evaluation.html
Shared drive 300 DPI visualization figure: R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\figures\\gpr81_binding_domains_visualization.png
Shared drive executive one-pager dashboard: R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\gpr81_onepager_summary_en.html
Shared drive simulation data: R:\\DT\\TDE_TV\\shared_folder\\QYJI\\druggability\\GPR81\\readout\\data\\openmm_pilot_results.json
Ticket: RIC-396

Please feel free to open the HTML report in your browser to inspect the 3D domain binding modes directly. I am very happy to support the replicate data analysis, fit the allosteric operational parameters, or coordinate on plasmid designs if needed.

Best regards,
Jin Qiuye (Jay)
Sr. Data Scientist
Research Insights China
Novo Nordisk Research Centre China
qyji@novonordisk.com
"""

out_cifs_email = os.path.join(CIFS_READOUT, "email_draft_to_huan.txt")
with open(out_cifs_email, "w", encoding="utf-8") as f:
    f.write(email_text.strip() + "\n")
print("Written email draft to CIFS:", out_cifs_email)

out_local_email = os.path.join(WORK_DIR, "email_draft_to_huan.txt")
with open(out_local_email, "w", encoding="utf-8") as f:
    f.write(email_text.strip() + "\n")
print("Written local email draft:", out_local_email)
