#!/usr/bin/env python
"""Render the optimized 8-slide group meeting presentation (6 main + 2 Appendix: HTML -> PDF + @2x PNG per slide) via Playwright."""
import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path("/das/user/QYJI/druggability")
IMG_PATH = ROOT / "humanPPI_repro/results/repro_2panel_evidence.png"
BQ1_IMG_PATH = ROOT / "reports/bq1_99_triage/bq1_99_triage_and_fep_2panel.png"
AMY_IMG_PATH = ROOT / "reports/bq1_99_triage/amylin_mrap2_study/amylin_mrap2_competition_md_2panel.png"
OUT_HTML = ROOT / "reports/ppi_group_meeting_deck_2026-10-29.html"
OUT_PDF = ROOT / "reports/ppi_group_meeting_deck_2026-10-29.pdf"
SLIDE_DIR = ROOT / "reports/deck_slides_2026-10-29"
SLIDE_DIR.mkdir(parents=True, exist_ok=True)

b64_img = base64.b64encode(IMG_PATH.read_bytes()).decode("ascii")
b64_bq1 = base64.b64encode(BQ1_IMG_PATH.read_bytes()).decode("ascii")
b64_amy = base64.b64encode(AMY_IMG_PATH.read_bytes()).decode("ascii")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Druggability Pipeline Landscape &amp; Preliminary PPI Screening Plan — Group Meeting Deck (RIC-410)</title>
<style>
  @page {{
    size: 1920px 1080px;
    margin: 0;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{
    background: #CBD5E1;
    font-family: 'Segoe UI', Calibri, -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1A1A2E;
    -webkit-font-smoothing: antialiased;
  }}
  .slide {{
    width: 1920px;
    height: 1080px;
    background: #FFFFFF;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    page-break-after: always;
    break-after: page;
    margin: 0 auto;
  }}
  .slide.navy-bg {{
    background: #001965;
    color: #FFFFFF;
  }}

  /* Header & Footer for standard slides */
  .hdr {{
    height: 136px;
    background: #001965;
    padding: 18px 68px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }}
  .hdr-l h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 7px;
  }}
  .hdr-l .sub {{
    font-size: 15.5px;
    color: #E8EEF7;
  }}
  .hdr-l .sub strong {{ color: #FFFFFF; }}
  .hdr-l .sub em {{ color: #CADCFC; font-style: italic; }}
  .hdr-r {{
    text-align: right;
    color: #FFFFFF;
    flex-shrink: 0;
  }}
  .hdr-r .badge {{
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.32);
    padding: 5px 14px;
    border-radius: 4px;
    font-size: 14.5px;
    font-weight: 700;
    margin-bottom: 6px;
  }}
  .hdr-r .meta {{
    font-size: 13.5px;
    color: #E8EEF7;
  }}

  .body-area {{
    flex: 1;
    padding: 18px 68px 12px 68px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 0;
  }}

  .ftr {{
    height: 40px;
    padding: 0 0 8px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: #5A6070;
    border-top: 1px solid #D0D7E5;
    margin: 0 68px;
    flex-shrink: 0;
  }}

  /* Reusable components */
  .banner {{
    background: #F2F4F8;
    border: 1.5px solid #D0D7E5;
    border-left: 10px solid #D9383A;
    padding: 12px 20px;
    font-size: 14.2px;
    line-height: 1.42;
  }}
  .banner.navy {{ background: #E8EEF7; border-color: #001965; border-left-color: #001965; }}
  .banner.teal {{ background: #EBF7F5; border-color: #00857C; border-left-color: #00857C; }}
  .banner.amber {{ background: #FDF6E7; border-color: #B7791F; border-left-color: #B7791F; }}

  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
  }}
  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 22px;
  }}
  .card {{
    background: #FFFFFF;
    border: 1.5px solid #D0D7E5;
    display: flex;
    flex-direction: column;
  }}
  .card-hdr {{
    height: 44px;
    background: #001965;
    color: #FFFFFF;
    font-size: 16.5px;
    font-weight: 700;
    padding: 0 18px;
    display: flex;
    align-items: center;
  }}
  .card-hdr.teal {{ background: #00857C; }}
  .card-hdr.red  {{ background: #D9383A; }}
  .card-sub {{
    height: 36px;
    background: #E8EEF7;
    color: #001965;
    font-size: 14px;
    font-weight: 700;
    padding: 0 18px;
    display: flex;
    align-items: center;
  }}
  .card-sub.teal {{ color: #00857C; }}
  .card-sub.red  {{ color: #D9383A; }}
  .card-body {{
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    font-size: 13.8px;
    line-height: 1.40;
    flex: 1;
  }}

  /* Slide 2 Landscape styles */
  .chevron-bar {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 14px;
    flex-shrink: 0;
  }}
  .stage-pill {{
    background: #E8EEF7;
    border: 1.5px solid #001965;
    border-left: 8px solid #001965;
    padding: 8px 12px;
  }}
  .stage-pill.teal {{ border-color: #00857C; border-left-color: #00857C; }}
  .stage-pill.red  {{ border-color: #D9383A; border-left-color: #D9383A; }}
  .stage-pill .st-t {{ font-size: 13px; font-weight: 700; color: #001965; margin-bottom: 2px; }}
  .stage-pill.teal .st-t {{ color: #00857C; }}
  .stage-pill.red  .st-t {{ color: #D9383A; }}
  .stage-pill .st-s {{ font-size: 11.2px; color: #1A1A2E; }}

  .pillars-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 14px 20px;
    flex-shrink: 0;
  }}
  .cap-card {{
    background: #FFFFFF;
    border: 1.5px solid #D0D7E5;
    display: flex;
    flex-direction: column;
  }}
  .cap-hdr {{
    height: 34px;
    background: #001965;
    color: #FFFFFF;
    font-size: 13.8px;
    font-weight: 700;
    padding: 0 14px;
    display: flex;
    align-items: center;
  }}
  .cap-hdr.teal {{ background: #00857C; }}
  .cap-hdr.red  {{ background: #D9383A; }}
  .cap-tag {{
    height: 24px;
    background: #F2F4F8;
    color: #001965;
    font-family: Consolas, Menlo, monospace;
    font-size: 11.2px;
    font-weight: 700;
    padding: 0 14px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #E2E8F0;
  }}
  .cap-tag.teal {{ color: #00857C; }}
  .cap-tag.red  {{ color: #D9383A; }}
  .cap-body {{
    padding: 8px 14px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 11.8px;
    line-height: 1.33;
  }}

  table.std-tbl {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  table.std-tbl th {{
    background: #001965;
    color: #FFFFFF;
    font-weight: 700;
    text-align: left;
    padding: 8px 11px;
    border: 1px solid #D0D7E5;
  }}
  table.std-tbl td {{
    padding: 7px 11px;
    border: 1px solid #D0D7E5;
    color: #1A1A2E;
    line-height: 1.30;
  }}
  table.std-tbl tr:nth-child(even) td {{
    background: #E8EEF7;
  }}
  table.std-tbl tr:nth-child(odd) td {{
    background: #FFFFFF;
  }}
</style>
</head>
<body>

<!-- ==================== SLIDE 1: TITLE & EXECUTIVE FRAMING ==================== -->
<div class="slide navy-bg" id="slide-1">
  <div style="height: 16px; background: #00857C; width: 100%;"></div>
  <div style="padding: 46px 84px; flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
    <div>
      <div style="display: inline-block; background: #00857C; color: #FFFFFF; font-weight: 700; font-size: 14.5px; padding: 7px 18px; letter-spacing: 0.5px; margin-bottom: 20px;">
        SCIENTIFIC UPDATE (~10 MIN) &nbsp;|&nbsp; PLANNING STAGE &nbsp;|&nbsp; RIC-410
      </div>
      <h1 style="font-size: 42px; font-weight: 800; color: #FFFFFF; margin-bottom: 12px; letter-spacing: -0.4px;">
        Druggability Pipeline Landscape &amp; Preliminary PPI Screening Plan
      </h1>
      <div style="font-size: 20.5px; font-weight: 700; color: #E8EEF7; margin-bottom: 16px;">
        1. End-to-End Capability Landscape &nbsp;&nbsp;|&nbsp;&nbsp; 2. Proteome PPI Module &amp; Boundaries &nbsp;&nbsp;|&nbsp;&nbsp; 3. Assay-Gated Exploratory Plan
      </div>
      <div style="font-size: 15.5px; color: #CADCFC;">
        Presenter: Qiuye Jin (QYJI) &nbsp;&nbsp;|&nbsp;&nbsp; Cardiometabolic Data S6 Collaborator: Zheng Cao (ZHCO) &nbsp;&nbsp;|&nbsp;&nbsp; Research Insights China (RIC)
      </div>
    </div>

    <!-- Three Executive Summary Pillars -->
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; margin: 14px 0;">
      <div style="background: #FFFFFF; border: 2px solid #00857C; color: #1A1A2E; display: flex; flex-direction: column;">
        <div style="background: #00857C; color: #FFFFFF; font-size: 17px; font-weight: 700; padding: 12px 20px;">
          1. Pipeline Landscape (Slide 2)
        </div>
        <div style="background: #E8EEF7; color: #001965; font-size: 13.8px; font-weight: 700; padding: 8px 20px;">
          6 Integrated Modules Across Modalities
        </div>
        <div style="padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; font-size: 14px; line-height: 1.42;">
          <div>
            <strong style="color: #001965; font-size: 14.8px;">&bull; End-to-End Platform:</strong><br>
            Built a 6-stage computational pipeline under <code>druggability</code>: (1) Target Genetics &amp; Safety, (2) Proteome PPI &amp; SAVs, (3) Peptide &amp; BBB, (4) Pocket &amp; Virtual Screening, (5) Explicit MD &amp; FEP/TI, and (6) 3D Delivery.
          </div>
          <div>
            <strong style="color: #001965; font-size: 14.8px;">&bull; Battle-Tested on Internal Projects:</strong><br>
            Validated across OXTR peptide selectivity (RIC-403), GPR81 anti-flushing FEP (RIC-396), TSPO target fishing (RIC-408), GIGYF1 glue pocket (RIC-407), and peptide BBB / 3_safety (RIC-349/409).
          </div>
        </div>
      </div>

      <div style="background: #FFFFFF; border: 2px solid #00857C; color: #1A1A2E; display: flex; flex-direction: column;">
        <div style="background: #00857C; color: #FFFFFF; font-size: 17px; font-weight: 700; padding: 12px 20px;">
          2. New PPI Capability (Slides 3&ndash;4)
        </div>
        <div style="background: #E8EEF7; color: #001965; font-size: 13.8px; font-weight: 700; padding: 8px 20px;">
          Baker RF2-PPI Validation &amp; Boundaries
        </div>
        <div style="padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; font-size: 14px; line-height: 1.42;">
          <div>
            <strong style="color: #001965; font-size: 14.8px;">&bull; What Baker &amp; Cong Achieved:</strong><br>
            <em>Science</em> 2025 (7x omicMSAs + RF2-PPI &rarr; 17,849 PPIs @90% prec; 2,700 zero-prior in Data S6) + <em>Sci Rep</em> 2026 (clinical SAVs mapped to 3D interfaces).
          </div>
          <div>
            <strong style="color: #001965; font-size: 14.8px;">&bull; In-House Audit &amp; Scope Rules:</strong><br>
            Reproduced on 6x A100 GPUs (<strong>262x lift</strong> over random; r=0.919). High sensitivity on large/transmembrane complexes (<strong>43.2% recall &gt;1,500 &Aring;&sup2;</strong>), blind spot on transient SLiMs (4.5%) &rarr; positive generator only.
          </div>
        </div>
      </div>

      <div style="background: #FFFFFF; border: 2px solid #D9383A; color: #1A1A2E; display: flex; flex-direction: column;">
        <div style="background: #D9383A; color: #FFFFFF; font-size: 17px; font-weight: 700; padding: 12px 20px;">
          3. Exploratory Plan &amp; Gate (Slides 5&ndash;6)
        </div>
        <div style="background: #E8EEF7; color: #001965; font-size: 13.8px; font-weight: 700; padding: 8px 20px;">
          3 Business Options Gated on Wet-Lab Assay
        </div>
        <div style="padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; font-size: 14px; line-height: 1.42;">
          <div>
            <strong style="color: #D9383A; font-size: 14.8px;">&bull; 3 Candidate Business Questions:</strong><br>
            <strong>BQ-1</strong> (99 cardiometabolic Data S6 leads triage), <strong>BQ-2</strong> (on-demand 1-vs-20,260 bait screen in ~6 GPU-h), and <strong>BQ-3</strong> (6&Aring; disease-interface &amp; point-mutant control design).
          </div>
          <div>
            <strong style="color: #D9383A; font-size: 14.8px;">&bull; Dry-Run PoC &amp; Assay Readiness Gate:</strong><br>
            Completed dry-run triage (8/99 pass 4/4; #1 RAMP3&ndash;MRAP2 audited via Boltz-2, MD &amp; FEP). Next step is <strong>gated on checking wet-lab screening/validation assay readiness</strong> (co-IP / BRET / cAMP).
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Goal Strip -->
    <div style="background: #E8EEF7; padding: 16px 24px; color: #001965; font-size: 15.5px; font-weight: 700;">
      <span style="color: #D9383A;">Goal of Today&rsquo;s 10-Min Update (Planning Stage):</span> Share our systematic druggability pipeline landscape (Part 1), clarify what the new PPI module can/cannot do (Part 2), and align on how to check wet-lab assay readiness before committing to a campaign (Part 3).
    </div>
  </div>
</div>

<!-- ==================== SLIDE 2: SYSTEMATIC PIPELINE LANDSCAPE ==================== -->
<div class="slide" id="slide-2">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Druggability Agent Platform: Systematic Capability Landscape &amp; Benchmarks</h1>
      <div class="sub"><strong>PART 1: PIPELINE CAPABILITY LANDSCAPE</strong> &nbsp;|&nbsp; <em>6 Integrated Modules Across Target Genetics, PPI, Peptide/BBB, Virtual Screening, MD/FEP &amp; 3D Delivery</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 2 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <!-- Top 6-Stage Workflow Bar -->
    <div class="chevron-bar">
      <div class="stage-pill">
        <div class="st-t">Stage 1: Target &amp; Genetics</div>
        <div class="st-s">Open Targets / GWAS / Safety</div>
      </div>
      <div class="stage-pill teal">
        <div class="st-t">Stage 2: PPI &amp; Interfaces</div>
        <div class="st-s">RF2-PPI / Boltz-2 / SAVs</div>
      </div>
      <div class="stage-pill">
        <div class="st-t">Stage 3: Peptide &amp; BBB</div>
        <div class="st-s">PRODIGY / Lipidation / ESM-2</div>
      </div>
      <div class="stage-pill teal">
        <div class="st-t">Stage 4: Pocket &amp; VS</div>
        <div class="st-s">fpocket / DrugCLIP / Vina</div>
      </div>
      <div class="stage-pill red">
        <div class="st-t">Stage 5: Explicit MD &amp; FEP</div>
        <div class="st-s">A100 OpenMM / Alchemical TI</div>
      </div>
      <div class="stage-pill">
        <div class="st-t">Stage 6: 3D &amp; Assay Design</div>
        <div class="st-s">3Dmol HTML / Point-Mutants</div>
      </div>
    </div>

    <!-- 6 Core Capability Pillar Cards (2x3) -->
    <div class="pillars-grid">
      <div class="cap-card">
        <div class="cap-hdr">1. Target Tractability, Genetics &amp; Safety</div>
        <div class="cap-tag">druggability.tractability | ligandability | 3_safety</div>
        <div class="cap-body">
          <div>&bull; <strong style="color:#001965;">5-Axis Target Profiling:</strong> Open Targets GraphQL + ChEMBL ligandability + fpocket + clinical precedents + safety across SM / Antibody / Peptide / PROTAC.</div>
          <div>&bull; <strong style="color:#001965;">Human Genetics &amp; Safety Gate:</strong> GWAS / ClinVar / UKB WES variant mapping + bidirectional target safety evaluation (W40-W44 &amp; 25-gene T2D/obesity panels).</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr teal">2. Proteome PPI &amp; Interface Variants [NEW]</div>
        <div class="cap-tag teal">RF2-PPI (6x A100) | Boltz-2 | interface_variants</div>
        <div class="cap-body">
          <div>&bull; <strong style="color:#00857C;">Proteome Partner Screen:</strong> 20,260-protein coevolution + structure funnel (~6 GPU-h/bait; 262x enrichment over random; 43.2% recall on complexes &gt;1,500 &Aring;&sup2;).</div>
          <div>&bull; <strong style="color:#00857C;">3D Disease-Variant Triage:</strong> Maps UniProt + AlphaMissense pathogenic SAVs onto 6&Aring; contact surfaces to design surgical point-mutant negative controls.</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr">3. Peptide Engineering &amp; CNS/BBB Exposure</div>
        <div class="cap-tag">druggability.peptide (affinity | scan | chem_mod | bbb)</div>
        <div class="cap-body">
          <div>&bull; <strong style="color:#001965;">Peptide Structural Pharmacology:</strong> PRODIGY contact affinity (&Delta;G/K<sub>d</sub>), high-throughput Ala/20-AA mutational hotspot scan, and subtype selectivity counter-screens.</div>
          <div>&bull; <strong style="color:#001965;">Protraction &amp; BBB Platform:</strong> 3D cone steric audit for C16/C18/C20 lipidation exit vectors + ESM-2 multi-task heads (BBB AUC=0.89, hemolytic AUC=1.00).</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr teal">4. Pocket Detection, AI VS &amp; Target Fishing</div>
        <div class="cap-tag teal">druggability.pocket | drugclip | vina | image2smiles</div>
        <div class="cap-body">
          <div>&bull; <strong style="color:#00857C;">Multi-Tier Virtual Screening:</strong> Contrastive DrugCLIP (2.94M library in ~22s) &rarr; tight-box AutoDock Vina (redocking &lt;2.0 &Aring; QC gate) &rarr; Boltz-2 affinity &amp; Murcko clustering.</div>
          <div>&bull; <strong style="color:#00857C;">Off-Target Deconvolution &amp; OCR:</strong> 5-layer ligand target fishing + clinical C<sub>max,u</sub>/K<sub>i</sub> occupancy gating; DECIMER/MolScribe chemical structure recovery from literature.</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr red">5. Explicit-Solvent MD &amp; Alchemical FEP/TI</div>
        <div class="cap-tag red">OpenMM 8.3 CUDA | openmmtools.alchemy (A100)</div>
        <div class="cap-body">
          <div>&bull; <strong style="color:#D9383A;">High-Throughput Explicit MD:</strong> All-atom Amber14SB + TIP3P water + 0.15M NaCl on A100 (&gt;2,100 ns/day); resolves static MM/GBSA vacuum cavity artifacts &amp; steric ejection.</div>
          <div>&bull; <strong style="color:#D9383A;">Alchemical FEP &amp; Annihilation TI:</strong> Dual-topology relative FEP &amp; mutational hotspot free-energy scans to quantify residue/variant energetic contributions (&Delta;&Delta;G in kcal/mol).</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr">6. Automated 3D Dossiers &amp; Wet-Lab Governance</div>
        <div class="cap-tag">druggability.report | 3Dmol.js | Scientific Boundaries</div>
        <div class="cap-body">
          <div>&bull; <strong style="color:#001965;">Zero-Install 3D Deliverables:</strong> Self-contained 3Dmol.js WebGL HTML dossiers, editable NN-styled PPTX + vector PDF decks, and ranked Excel/CSV scorecards.</div>
          <div>&bull; <strong style="color:#001965;">Audit &amp; Boundary Governance:</strong> Strict [FACT]/[OBS]/[MECH]/[HYP] tagging; mandatory homolog negative controls (ipTM &ne; potency); positive hypothesis generator only.</div>
        </div>
      </div>
    </div>

    <!-- Bottom Benchmark Table -->
    <div style="display:flex; flex-direction:column;">
      <div style="height:32px; background:#001965; color:#FFFFFF; font-size:13.8px; font-weight:700; padding:0 14px; display:flex; align-items:center;">
        Production-Validated Portfolio Benchmarks Across Modalities (Real Executed Outputs &amp; Wet-Lab Handovers)
      </div>
      <table class="std-tbl" style="font-size:11.4px;">
        <thead>
          <tr>
            <th style="width:14%; background:#00857C;">Modality / Domain</th>
            <th style="width:16%; background:#00857C;">Project &amp; Ticket</th>
            <th style="width:20%; background:#00857C;">Computational Stack Executed</th>
            <th style="width:34%; background:#00857C;">Headline Verified Biophysical / Biological Finding</th>
            <th style="width:16%; background:#00857C;">Deliverable &amp; Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong style="color:#001965;">Peptide Selectivity &amp; Protraction</strong></td>
            <td><strong>OXTR vs V1a/V1b/V2R &amp; GLP-1R (RIC-403)</strong></td>
            <td>Cryo-EM 7QVM/7DW9 + PRODIGY + A100 Explicit MD + 3D Lipidation Cone</td>
            <td>Explained &gt;1,000x selectivity: Pro7Gly releases V2R TM1 clash (3.51&Aring;, 70.8&Aring; MD ejection); verified Leu8 C18-diacid exit vector (0 clashes, ~160h PK).</td>
            <td>3D HTML + 12-Slide Deck Delivered (Mingyue)</td>
          </tr>
          <tr>
            <td><strong style="color:#001965;">Small-Molecule GPCR &amp; FEP</strong></td>
            <td><strong>GPR81 (HCAR1) vs HCAR2/3 (RIC-396)</strong></td>
            <td>45-Cmpd Vina + Boltz-2 Affinity + Steric Contradiction + 3-Leg OpenFEP</td>
            <td>Eliminated flushing liability via HCAR2 basic clash wall (+45.2 kcal/mol); proved AZ1 vs lactate mutual exclusion; converged c30/c31 FEP.</td>
            <td>3D HTML + 45-Cmpd Scorecard Delivered (UHYG)</td>
          </tr>
          <tr>
            <td><strong style="color:#001965;">Ligand Target Fishing &amp; TI</strong></td>
            <td><strong>TSPO 5-Ligand Panel (PK11195, Emapunil) (RIC-408)</strong></td>
            <td>5-Source Curation + 17-Pocket Vina Gate + 250ps MD + 57-Anchor TI</td>
            <td>Proved CAR (NR1I3) is PK11195 #2 target (IC<sub>50</sub> 25-56 nM, 5 methods); discovered TSPO dimer pocket 4RYI_p26 (LEU58 +7.6 kJ/mol) &amp; C<sub>max</sub>/K<sub>i</sub> gate.</td>
            <td>6-Round Dossiers + 7-Slide Deck Delivered (ZHCO)</td>
          </tr>
          <tr>
            <td><strong style="color:#001965;">Molecular Glue &amp; Cryptic Pocket</strong></td>
            <td><strong>GIGYF1-GRB10/14 &amp; GHSR VS (RIC-407 / RIC-392)</strong></td>
            <td>Crystal 7RUQ/2AUH + UKB 454k WES Mutagenesis + 7,931-Cmpd Vina/Boltz-2</td>
            <td>Identified 445 &Aring;&sup3; cryptic glue pocket at GIGYF1 interface; UKB p.Tyr498Cys drops affinity &gt;80x (+2.74 kcal/mol, T2D OR=5.91); 20 GHSR chemotypes.</td>
            <td>3D Glue Dossier &amp; Ranked Hits (GO Decision)</td>
          </tr>
          <tr>
            <td><strong style="color:#001965;">Peptide CNS/BBB &amp; Safety Gate</strong></td>
            <td><strong>MC4R / RORA BBB &amp; 3_Safety (RIC-349 / RIC-409)</strong></td>
            <td>ESM-2 + Protraction Penaliser + Local vLLM Safety Gate + 175-Gene Dry/Wet</td>
            <td>BBB test AUC=0.89 (flagged protracted peptide CNS exclusion); 298 target-direction safety audits (0 gate errors); 175-gene HepG2 ATP/TMRM calibration.</td>
            <td>Production CLI / Service &amp; Weekly Panels</td>
          </tr>
          <tr style="background:#EBF7F5; font-weight:600;">
            <td><strong style="color:#00857C;">Proteome PPI &amp; Interface Triage</strong></td>
            <td><strong>Cardiometabolic Data S6 99-Lead Dry-Run (RIC-410)</strong></td>
            <td>RF2-PPI (6x A100) + 4-Criteria Triage + Boltz-2 omicMSA + A100 MD &amp; FEP</td>
            <td>8/99 leads pass all 4/4 criteria (#1 RAMP3-MRAP2 ipTM=0.868, MD RMSD 0.49&Aring;); obesity SAVs R125/L115 are top FEP hotspots (+6.25/+5.21 kcal/mol).</td>
            <td>Exploratory Dry-Run Ready for Assay Check</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="ftr">
    <div>Platform: <code>druggability</code> repo (hpccnrd001 A100 Cluster) &nbsp;|&nbsp; Validated tickets: RIC-349, RIC-392, RIC-396, RIC-403, RIC-407, RIC-408, RIC-410</div>
    <div>druggability repo &nbsp;|&nbsp; Page 2/6</div>
  </div>
</div>

<!-- ==================== SLIDE 3: MODULE 2 DEEP-DIVE (CONSOLIDATED BAKER + VALIDATION) ==================== -->
<div class="slide" id="slide-3">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Module 2 Deep-Dive: Baker Engine Summary, A100 Validation &amp; Reading Rules</h1>
      <div class="sub"><strong>PART 2A: PPI ENGINE &amp; IN-HOUSE VALIDATION</strong> &nbsp;|&nbsp; <em>Consolidated Summary of Science 2025 / Sci Rep 2026, 33,000-Pair In-House Audit, and 4 Rigorous Caveats</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 3 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div class="banner navy" style="padding:10px 18px; font-size:13.5px;">
      <strong style="color:#001965;">What Baker &amp; Cong Achieved (2025 Science vs 2026 Sci Rep Division of Labor &mdash; Details in Appendix S2):</strong>
      <strong>2025 Science</strong> built the engine (7x eukaryotic omicMSAs + 17x AFDB domain-contact training &rarr; RF2-PPI, 20x faster than AF2) and screened 19,528 human proteins (~191M pairs &rarr; <strong>17,849 PPIs @90% prec</strong>; 3,631 novel; 2,700 zero-prior in Data S6). <strong>2026 Sci Rep</strong> added no new screen; it mapped clinical disease SAVs onto 2025 3D interfaces &amp; AF3 assemblies.
    </div>

    <div class="grid-4">
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:6px solid #001965; padding:9px 12px; text-align:center;">
        <div style="font-size:22px; font-weight:800; color:#001965;">262x Enrichment</div>
        <div style="font-size:13px; font-weight:700; margin:2px 0;">Weighted AUCPR 0.262 vs 0.001</div>
        <div style="font-size:11.5px; color:#5A6070;">1:1,000 proteome prior (1:1 AUC = 0.813)</div>
      </div>
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:6px solid #00857C; padding:9px 12px; text-align:center;">
        <div style="font-size:22px; font-weight:800; color:#00857C;">r = 0.919 Parity</div>
        <div style="font-size:13px; font-weight:700; margin:2px 0;">8,977 Shared Benchmark Pairs</div>
        <div style="font-size:11.5px; color:#5A6070;">623 TPs &amp; 0 FPs at &ge;90% precision</div>
      </div>
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:6px solid #001965; padding:9px 12px; text-align:center;">
        <div style="font-size:22px; font-weight:800; color:#001965;">43.2% vs 4.5%</div>
        <div style="font-size:13px; font-weight:700; margin:2px 0;">Large vs Small Interface Recall</div>
        <div style="font-size:11.5px; color:#5A6070;">&gt;1,500 &Aring;&sup2; stable vs &lt;800 &Aring;&sup2; SLiMs</div>
      </div>
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:6px solid #D9383A; padding:9px 12px; text-align:center;">
        <div style="font-size:22px; font-weight:800; color:#D9383A;">~6 GPU-Hours</div>
        <div style="font-size:13px; font-weight:700; margin:2px 0;">Per Target Proteome Screen</div>
        <div style="font-size:11.5px; color:#5A6070;">1 bait vs 20,260 proteins on 6x A100</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 980px 780px; gap: 24px; flex: 1; margin: 10px 0;">
      <div style="background:#FFF; border:1.5px solid #D0D7E5; padding:8px; display:flex; align-items:center; justify-content:center;">
        <img src="data:image/png;base64,{b64_img}" style="width:100%; height:100%; object-fit:contain;">
      </div>
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column;">
        <div style="height:40px; background:#D9383A; color:#FFF; font-size:15px; font-weight:700; padding:0 18px; display:flex; align-items:center;">
          Physical Mechanism &amp; 4 Rigorous Reading Rules (Do Not Overclaim)
        </div>
        <div style="padding:12px 18px; display:flex; flex-direction:column; justify-content:space-between; flex:1; font-size:13px; line-height:1.36;">
          <div><strong style="color:#001965;">&bull; Why Overall Recall is 20.8% (Panel B Mechanism [MECH]):</strong> Coevolution scales with contact area: <strong>43.2% recall on large stable complexes (&gt;1,500 &Aring;&sup2;</strong>; 51.8% @0.50) vs <strong>4.5% on small transient SLiMs (&lt;800 &Aring;&sup2;)</strong>. 58% of Data S6 novel hits are transmembrane complexes.</div>
          <div><strong style="color:#D9383A;">&bull; Rule 1 (Not 17.8k Blind Hits):</strong> 14,218 of 17,849 PPIs combined prior evidence with lower cutoffs; <strong>3,631 are novel</strong> (2,700 zero-prior in Data S6).</div>
          <div><strong style="color:#D9383A;">&bull; Rule 2 (&lsquo;No PDB Template&rsquo; &ne; Unknown Fold):</strong> Data S6 pairs lack homologous <strong>complex</strong> templates in PDB, not monomer structures.</div>
          <div><strong style="color:#D9383A;">&bull; Rule 3 &amp; 4 (Interface SAV &amp; ipTM &ne; Proven In Vivo Effect):</strong> Interface SAVs (&lt;6&Aring;) and high pLDDT/ipTM propose testable structural hypotheses; they do not prove binding loss or tissue co-expression without wet-lab assays.</div>
        </div>
      </div>
    </div>

    <div class="banner teal" style="padding:10px 18px; font-size:13.2px;">
      <div style="color:#00857C; font-weight:700; font-size:14.2px; margin-bottom:2px;">In-House Disease-Interface Module (<code>druggability.interface_variants</code>, 22 Unit Tests) &mdash; Verified on CASR (P41180) [OBS]:</div>
      <div>&bull; <strong>Dual-Evidence Pathogenic Filter:</strong> Combines sequence alignment QC (&lt;5% mismatch), UniProt clinical disease variants + EBI AlphaMissense pathogenicity, and 6 &Aring; CB/CA contact geometry.<br>
      &bull; <strong>CASR Proof-of-Concept (Tier-A CKD target in Data S6):</strong> Mapped <strong>89 clinical pathogenic mutations</strong> (HHC1 / HYPOC1); <strong>64% cluster directly at the extracellular dimerization interface (residues &le;612)</strong>, enabling automated nomination of point-mutant negative controls.</div>
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 3/6</div>
  </div>
</div>

<!-- ==================== SLIDE 4: PROSPECTIVE VALIDATION & FIT MATRIX ==================== -->
<div class="slide" id="slide-4">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Prospective Time-Split Validation (2024&ndash;2026) &amp; Biological Fit Matrix</h1>
      <div class="sub"><strong>PART 2B: PROSPECTIVE PROOF &amp; OPERATING BOUNDARIES</strong> &nbsp;|&nbsp; <em>11 Data S6 &lsquo;Zero-Prior&rsquo; Predictions Confirmed by Independent Wet Labs Since Cutoff + Operating Rules</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 4 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div style="display: grid; grid-template-columns: 1055px 705px; gap: 24px; flex: 1;">
      <!-- Left: Prospective Table -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div style="height:44px; background:#00857C; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
            Prospective Audit: Data S6 &lsquo;Zero-Prior&rsquo; Pairs Confirmed in 2024&ndash;2026 (11 Cases)
          </div>
          <div style="padding:10px 18px 8px 18px; font-size:13.2px; color:#1A1A2E; line-height:1.35;">
            Data S6 defined 2,700 novel pairs with zero DB (Sep 2023) &amp; zero PDB complex template (Jan 2024) support. Over the subsequent two years, <strong>11 pairs were independently validated by structures or co-IP (&gt;50% are transmembrane/organelle complexes*)</strong>:
          </div>
          <div style="padding:0 18px;">
            <table class="std-tbl">
              <thead>
                <tr>
                  <th style="width:20%;">Data S6 Novel Pair</th>
                  <th style="width:16%; text-align:center;">RF / AF / AFM</th>
                  <th style="width:28%;">2024&ndash;2026 Independent Publication</th>
                  <th style="width:36%;">Wet-Lab Validation &amp; Biological Role</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong style="color:#001965;">DND1 &ndash; NANOS3</strong></td>
                  <td style="text-align:center;">0.52 / 0.97 / 1.00</td>
                  <td><em>Mol Cell</em> 2026 &amp; <em>Nat Commun</em> 2025</td>
                  <td>Cryo-EM/X-ray + co-IP: germ-granule RNA complex</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">GPATCH1 &ndash; DHX35</strong></td>
                  <td style="text-align:center;">0.73 / 1.00 / 1.00</td>
                  <td><em>Cell Research</em> 2025 (PMID 40016598)</td>
                  <td>Cryo-EM structure: spliceosomal quality-control B*Q</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">NUP210 &ndash; TMEM209*</strong></td>
                  <td style="text-align:center;">0.28 / 0.99 / 0.99</td>
                  <td><em>J Cell Sci</em> 2026 (PMID 41582553)</td>
                  <td>Endogenous co-IP + TMD rescue: 4th TM nucleoporin</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">MTR &ndash; MMADHC*</strong></td>
                  <td style="text-align:center;">0.38 / 0.99 / 1.00</td>
                  <td><em>PNAS</em> 2026 (PMID 42709793)</td>
                  <td>Co-IP + flux: B12 chaperone binds MTR in mitochondria</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">EFCAB10 &ndash; AK8</strong></td>
                  <td style="text-align:center;">1.00 / 0.98 / 0.99</td>
                  <td><em>PNAS</em> 2025 (PMID 41055978)</td>
                  <td>KO mice + co-IP: anchors AK8 to ciliary radial spoke</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">TOR1A &ndash; CLCC1*</strong></td>
                  <td style="text-align:center;">0.81 / 0.93 / 0.93</td>
                  <td><em>Mol Cells</em> 2026 (PMID 42551441)</td>
                  <td>Co-IP + rescue: ER Cl&minus; channel in DYT1 dystonia</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">GLMP &ndash; MFSD1* (+4)</strong></td>
                  <td style="text-align:center;">0.99 / 1.00 / 1.00</td>
                  <td><em>Nat Cell Biol</em> 2024 / <em>EMBO Rep</em> 2024</td>
                  <td>Lysosomal transporter + PPTC7-FBXL4, TMEM131, SPARK</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div style="margin:10px 18px 14px 18px; background:#FFF; border:1px solid #D0D7E5; border-left:8px solid #001965; padding:10px 16px; font-size:12.8px; line-height:1.36;">
          <strong style="color:#001965;">Category B &mdash; Resolving Direct 3D Mechanism for Known AP-MS Hits:</strong> Beyond de novo Data S6 pairs, 3D predictions resolved how <em>NUDT5</em> allosterically blocks <em>PPAT</em> in purine synthesis (<em>Science</em> 2025, PMID 41196949) and how <em>SMG5&ndash;SMG6</em> dimerizes in NMD (<em>Nat Commun</em> 2026) &mdash; turning noisy AP-MS hits into point-mutant-verified mechanisms. (* = Transmembrane / Organelle).
        </div>
      </div>

      <!-- Right: Fit Matrix & Governance -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="height:44px; background:#D9383A; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          Biological Fit Matrix &amp; Campaign Governance
        </div>
        <div style="padding:12px 18px; display:flex; flex-direction:column; justify-content:space-between; flex:1; gap:12px;">
          <div style="background:#EBF7F5; border:1.5px solid #00857C;">
            <div style="background:#00857C; color:#FFF; font-size:13.8px; font-weight:700; padding:6px 14px;">IDEAL TARGETS (HIGH SENSITIVITY &mdash; USE HERE)</div>
            <div style="padding:10px 16px; font-size:13px; line-height:1.36; display:flex; flex-direction:column; gap:7px;">
              <div><strong style="color:#00857C;">&bull; Transmembrane &amp; Organelle Complexes (58% of S6):</strong><br>Hard to solubilize in detergent AP-MS (e.g., GPCR accessory proteins RAMP1/2/3, ER/lysosomal channels).</div>
              <div><strong style="color:#00857C;">&bull; Large Constitutive / Obligate Assemblies (&gt;1,500 &Aring;&sup2;):</strong><br>43.2% recall at &ge;90% precision (51.8% at moderate cutoff).</div>
              <div><strong style="color:#00857C;">&bull; Disease-Mutated Interfaces (ClinVar / Human Genetics):</strong><br>Pinpoints exact contact residues to design disruptor controls.</div>
            </div>
          </div>

          <div style="background:#FDF2F2; border:1.5px solid #D9383A;">
            <div style="background:#D9383A; color:#FFF; font-size:13.8px; font-weight:700; padding:6px 14px;">KNOWN BLIND SPOTS (DO NOT USE TO EXCLUDE)</div>
            <div style="padding:10px 16px; font-size:13px; line-height:1.36; display:flex; flex-direction:column; gap:7px;">
              <div><strong style="color:#D9383A;">&bull; Transient / PTM-Triggered Signaling Complexes:</strong><br>Phosphorylation- or ligand-dependent recruitment (e.g., GPCR-arrestin, kinase-substrate) lacks static coevolution.</div>
              <div><strong style="color:#D9383A;">&bull; Disordered Short Linear Motifs (SLiMs, &lt;800 &Aring;&sup2;):</strong><br>Only 4.5% recall at high precision (underrepresented in training).</div>
              <div><strong style="color:#D9383A;">&bull; Fast-Evolving / Immune / Tissue-Restricted Paralogs:</strong><br>Coevolution reflects family conservation, not tissue specificity.</div>
            </div>
          </div>

          <div style="background:#FDF6E7; border:1.5px solid #B7791F; border-left:8px solid #B7791F; padding:10px 16px; font-size:13px; line-height:1.36;">
            <strong style="color:#B7791F; font-size:13.8px;">Golden Rule (Lambourne et al., Nat Commun 2026):</strong><br>
            <strong>1. Positive Hypothesis Generator Only:</strong> High score (@90% precision) + co-expression = strong wet-lab lead; low score NEVER disproves a biological hypothesis.<br>
            <strong>2. Mandatory Tissue Co-Expression Gate:</strong> Always filter predicted pairs by GTEx / single-cell co-expression in the disease tissue.
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 4/6</div>
  </div>
</div>

<!-- ==================== SLIDE 5: PRELIMINARY CAMPAIGN PLAN & ASSAY GATE ==================== -->
<div class="slide" id="slide-5">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Preliminary Campaign Plan: 3 Candidate Business Questions &amp; Assay Gate</h1>
      <div class="sub"><strong>PART 3A: EXPLORATORY PLAN &amp; ASSAY GATE</strong> &nbsp;|&nbsp; <em>Exploratory Planning Options &amp; Stepwise Decision Gated on Downstream Wet-Lab Assay Readiness</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 5 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div class="banner amber">
      <strong style="color:#B7791F;">Current Status &mdash; Exploratory Planning Stage (No Premature Scale-Up):</strong>
      While our computational pipeline (Modules 1&ndash;6) is ready, we are currently in the <strong>planning phase</strong>. Below are 3 candidate Business Questions (<strong>BQ-1 to BQ-3</strong>); actual campaign execution will be strictly gated on whether downstream wet-lab screening/validation assays are ready.
    </div>

    <div class="grid-3" style="flex: 1; margin: 14px 0;">
      <div class="card">
        <div class="card-hdr">BQ-1: Portfolio Partner Mining</div>
        <div class="card-sub">Triage 99 Cardiometabolic Data S6 Leads</div>
        <div class="card-body">
          <div><strong style="color:#001965;">&bull; Candidate Question:</strong><br>Among Baker&rsquo;s 2,700 zero-prior PPIs (Data S6), which novel interactors of our cardiometabolic targets pass strict 4-criteria triage (Genetics, Pathway, Perturbation, Co-expression)?</div>
          <div><strong style="color:#001965;">&bull; Dry-Run Status (Completed):</strong><br>Audited 99 unflagged leads via Module 1 + Module 2 &rarr; <strong>8 leads pass all 4/4 criteria</strong> (led by <strong>#1 RAMP3&ndash;MRAP2</strong> &amp; <strong>#2 RAMP1&ndash;MRAP2</strong>; 14 pass 3/4).</div>
          <div><strong style="color:#001965;">&bull; Required Wet-Lab Assay Gate:</strong><br>Requires ready <strong>co-IP / NanoBiT / BRET or surface receptor trafficking assay</strong> in the relevant target biology team before nominating any wet-lab validation.</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr teal">BQ-2: On-Demand Bait Screen</div>
        <div class="card-sub teal">1 Priority Target vs 20,260 Human Proteins</div>
        <div class="card-body">
          <div><strong style="color:#00857C;">&bull; Candidate Question:</strong><br>When an internal project has a priority receptor/transporter where detergent AP-MS fails, can we screen 20,260 proteins (~6 GPU-h/bait) to find missing co-receptors, chaperones, or E3 ligases?</div>
          <div><strong style="color:#00857C;">&bull; Dry-Run Status (Capability Ready):</strong><br>6x A100 pipeline operational (<strong>~6 GPU-h per target bait</strong>); automatically filters hits by @90% precision cutoff and GTEx target-organ co-expression.</div>
          <div><strong style="color:#00857C;">&bull; Required Wet-Lab Assay Gate:</strong><br>Only triggered on-demand when a project team has both a clear biological bottleneck and a <strong>ready functional/binding readout</strong> to test top 3&ndash;5 predicted partners.</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr red">BQ-3: 3D Interface &amp; Controls</div>
        <div class="card-sub red">Surgical Point-Mutant Negative Controls</div>
        <div class="card-body">
          <div><strong style="color:#D9383A;">&bull; Candidate Question:</strong><br>When biologists already have a candidate partner or disease variant, where is the 6&Aring; contact surface and which single-residue mutations selectively disrupt binding without misfolding?</div>
          <div><strong style="color:#D9383A;">&bull; Dry-Run Status (Verified on CASR &amp; MRAP2):</strong><br>Runs in ~15 min/pair (<code>interface-variants</code>) + optional Module 5 explicit MD &amp; FEP hotspot scan to rank energetic anchor residues (ddG in kcal/mol).</div>
          <div><strong style="color:#D9383A;">&bull; Required Wet-Lab Assay Gate:</strong><br>Directly supports teams already running mutagenesis / co-IP / BRET who need <strong>2&ndash;3 surgical point-mutant negative controls</strong> instead of crude domain truncations.</div>
        </div>
      </div>
    </div>

    <div class="banner teal" style="font-size:13.4px;">
      <div style="color:#00857C; font-weight:700; font-size:14.4px; margin-bottom:2px;">Proposed Stepwise Governance &amp; Assay Readiness Gate (How We Decide Next Steps):</div>
      <div>&bull; <strong>Step 1 (Computational Dry-Run &mdash; Done):</strong> Completed 4-criteria triage on 99 cardiometabolic S6 leads + cross-module MD/FEP proof-of-concept on #1 RAMP3&ndash;MRAP2 (Slide 6).<br>
      &bull; <strong>Step 2 (Biology &amp; Assay Readiness Check &mdash; Current Step):</strong> Review top candidates with biology leads to check (i) biological interest and (ii) whether screening/validation assays (co-IP, NanoBiT/BRET, cAMP, surface ELISA) are established and have capacity.<br>
      &bull; <strong>Step 3 (Go / No-Go Decision):</strong> Only launch focused wet-lab validation on 1&ndash;2 pairs where the assay is ready; hold broader proteome screens until assay bandwidth is confirmed.</div>
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 5/6</div>
  </div>
</div>

<!-- ==================== SLIDE 6: DRY-RUN POC — BQ-1 TRIAGE & RAMP3-MRAP2 AUDIT ==================== -->
<div class="slide" id="slide-6">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Dry-Run PoC: BQ-1 99-Lead Triage &amp; RAMP3&ndash;MRAP2 Cross-Module Audit</h1>
      <div class="sub"><strong>PART 3B: DRY-RUN EXAMPLE &amp; ASSAY DISCUSSION</strong> &nbsp;|&nbsp; <em>Illustrating How Modules 1&ndash;6 Work Together on a Candidate Pair Before Checking Wet-Lab Assay Readiness</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 6 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div style="display: grid; grid-template-columns: 1045px 715px; gap: 24px; flex: 1;">
      <!-- Left: 99 Leads 4-Criteria Funnel & Top 4/4 Table -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div style="height:44px; background:#001965; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
            BQ-1 Dry-Run: 4-Criteria Triage Across 99 Cardiometabolic Data S6 Leads
          </div>
          <div style="padding:10px 16px; display:grid; grid-template-columns:repeat(5, 1fr); gap:10px;">
            <div style="background:#FFF; border:1.5px solid #001965; padding:6px 4px; text-align:center;">
              <div style="font-size:15px; font-weight:800; color:#001965;">C1: Genetics</div>
              <div style="font-size:11.2px; font-weight:700;">60/99 (46 Human)</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #001965; padding:6px 4px; text-align:center;">
              <div style="font-size:15px; font-weight:800; color:#001965;">C2: Pathway</div>
              <div style="font-size:11.2px; font-weight:700;">43/99 Shared Path.</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #00857C; padding:6px 4px; text-align:center;">
              <div style="font-size:15px; font-weight:800; color:#00857C;">C3: Perturb.</div>
              <div style="font-size:11.2px; font-weight:700;">14/99 Direct Evid.</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #00857C; padding:6px 4px; text-align:center;">
              <div style="font-size:15px; font-weight:800; color:#00857C;">C4: Co-Prog.</div>
              <div style="font-size:11.2px; font-weight:700;">56/99 CM Co-Expr.</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #D9383A; padding:6px 4px; text-align:center;">
              <div style="font-size:15px; font-weight:800; color:#D9383A;">8 Pass 4/4</div>
              <div style="font-size:11.2px; font-weight:700;">#1 RAMP3&ndash;MRAP2</div>
            </div>
          </div>

          <div style="padding:0 16px;">
            <table class="std-tbl" style="font-size:11.8px;">
              <thead>
                <tr>
                  <th style="width:21%;">Rank &amp; Pair (Tier)</th>
                  <th style="width:13%; text-align:center;">Indications</th>
                  <th style="width:14%; text-align:center;">RF / AF / AFM</th>
                  <th style="width:25%;">C1 Both-Protein Genetics &amp; C2 Pathway</th>
                  <th style="width:27%;">C3 Direct Perturbation &amp; C4 CM Co-Expr</th>
                </tr>
              </thead>
              <tbody>
                <tr style="background:#EBF7F5;">
                  <td><strong style="color:#00857C;">#1 RAMP3&ndash;MRAP2 (Tier A, NN)</strong></td>
                  <td style="text-align:center;">Obesity; T2D; HF</td>
                  <td style="text-align:center;">0.75 / 0.96 / 0.76</td>
                  <td>RAMP3(T2D GWAS) + MRAP2(MC4R Obesity); GPCR path</td>
                  <td>Co-IP &amp; surface GPCR regulation (PMID 37085333); STRING coexpr=0.047</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">#2 RAMP1&ndash;MRAP2 (Tier A, NN)</strong></td>
                  <td style="text-align:center;">Obesity; T2D; HF</td>
                  <td style="text-align:center;">0.78 / 0.91 / 0.82</td>
                  <td>RAMP1(HCM GWAS) + MRAP2(MC4R Obesity); GPCR path</td>
                  <td>Reciprocal GPCR trafficking perturbation (PMID 37085333); co-expressed</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">#3 NR3C1&ndash;FOXO3 (Tier B)</strong></td>
                  <td style="text-align:center;">T2D; Obesity; CKD</td>
                  <td style="text-align:center;">0.31 / 0.93 / 0.95</td>
                  <td>NR3C1(AFib GWAS=0.84) + FOXO3(Obesity=0.42); FOXO path</td>
                  <td>Direct regulatory interaction (STRING exp=0.363); coexpr=0.102</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">#4 CD80&ndash;CSF3 (Tier C)</strong></td>
                  <td style="text-align:center;">MASH; CVD</td>
                  <td style="text-align:center;">0.52 / 0.96 / 0.98</td>
                  <td>CD80(Cirrhosis=0.28) + CSF3(AFib=0.14); Cytokine path</td>
                  <td>STRING exp=0.062; shared MI &amp; diabetes expression (coexpr=0.075)</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">#5 TLR4&ndash;LTBR (Tier C)</strong></td>
                  <td style="text-align:center;">T2D; MASH</td>
                  <td style="text-align:center;">0.26 / 0.86 / 0.72</td>
                  <td>TLR4(T2D GWAS=0.56) + LTBR(Cirrhosis=0.17); NF-&kappa;B path</td>
                  <td>Consistent hub mRNA perturbation (PMID 37414270); coexpr=0.086</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">#6 GP1BA&ndash;F2RL2 (Tier C)</strong></td>
                  <td style="text-align:center;">MASH; CKD; CVD</td>
                  <td style="text-align:center;">0.25 / 0.85 / 0.73</td>
                  <td>GP1BA(Liver=0.09) + F2RL2(GN=0.14); Hemostasis/GPCR</td>
                  <td>STRING exp=0.069; shared myocardial infarction expression (coexpr=0.088)</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">#7&ndash;#8 (KO Mouse): ITGA2B, IL18</strong></td>
                  <td style="text-align:center;">CVD; HF; T2D</td>
                  <td style="text-align:center;">0.56&ndash;0.59 (Mean)</td>
                  <td>ITGA2B&ndash;ACVRL1 (PAH GWAS=0.83) &amp; IL18&ndash;CCL17 (CM=0.28)</td>
                  <td>Plus 14 pairs passing 3/4 criteria (IL17A&ndash;FCN2, BRD3&ndash;KDM1A, TLR4&ndash;CTSS)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div style="margin:10px 16px 14px 16px; background:#FFF; border:1px solid #D0D7E5; border-left:8px solid #B7791F; padding:10px 15px; font-size:12.6px; line-height:1.35;">
          <strong style="color:#B7791F;">Next Step &mdash; Check Screening / Validation Assay Readiness with Biology Teams:</strong> Before scaling up, check with GPCR/Cardiometabolic biology teams whether co-IP / BRET / cAMP assays for RAMP1/3&ndash;MRAP2 (or NR3C1&ndash;FOXO3) are established and whether testing 2&ndash;3 point-mutant controls fits current assay bandwidth.
        </div>
      </div>

      <!-- Right: #1 Example RAMP3-MRAP2 Cross-Module Dry-Run -->
      <div style="background:#E8EEF7; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="height:44px; background:#D9383A; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          #1 Example (RAMP3&ndash;MRAP2): Cross-Module Pipeline Dry-Run
        </div>
        <div style="padding:12px 16px; display:flex; flex-direction:column; justify-content:space-between; flex:1; gap:12px;">
          <div style="background:#FFF; border:1px solid #D0D7E5; padding:6px; height:285px; display:flex; align-items:center; justify-content:center;">
            <img src="data:image/png;base64,{b64_bq1}" style="width:100%; height:100%; object-fit:contain;">
          </div>

          <div style="background:#FFF; border:1.5px solid #001965; flex:1; display:flex; flex-direction:column;">
            <div style="background:#001965; color:#FFF; font-size:13.2px; font-weight:700; padding:7px 14px;">HOW MODULES 2, 3, 4, 5 &amp; 6 CONVERGE ON ONE CANDIDATE</div>
            <div style="padding:10px 14px; font-size:12.4px; line-height:1.35; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
              <div><strong style="color:#001965;">&bull; Mod 2 (Boltz-2 + omicMSA Complex):</strong><br><strong>ipTM = 0.868, ptm = 0.834</strong> (180 inter-chain contacts &le;5&Aring;: 21 TM-TM + 159 ECD/juxtamembrane). RF2-PPI TM contact prob = 0.590 (RAMP3) / 0.865 (RAMP1).</div>
              <div><strong style="color:#D9383A;">&bull; Mod 5 (A100 Explicit-Solvent MD &amp; FEP Hotspots):</strong><br>Stable in A100 MD (<strong>backbone RMSD = 0.49 &Aring;</strong>). Human monogenic obesity SAVs MRAP2 <strong>R125C (ddG = +6.25 kcal/mol)</strong> &amp; <strong>L115V (+5.21 kcal/mol)</strong> rank as #1 &amp; #2 FEP hotspots.</div>
              <div><strong style="color:#001965;">&bull; Mod 3/5 (AMY1R/3R Subunit Competition &mdash; Appendix S1):</strong><br>Cryo-EM (7TYF/7TZF) + 8-system MD show MRAP2 occupies <strong>80% of RAMP3&rsquo;s CTR face</strong> (ddG = &minus;23.4 kcal/mol vs CTR) and blocks Amylin 7TM entry (96&rarr;0 contacts).</div>
              <div><strong style="color:#D9383A;">&bull; Mod 4 &amp; 6 (Groove Docking &amp; Assay-Ready Controls):</strong><br>Ubrogepant (&minus;7.81 kcal/mol) &amp; Rimegepant (ligand_ipTM=0.950) dock in ECD groove; <strong>MRAP2 L115A/R125A &amp; RAMP3 W56A</strong> controls ready if wet-lab assay is available.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 6/6</div>
  </div>
</div>

<!-- ==================== SLIDE 7 (APPENDIX S1): AMYLIN RECEPTOR COMPETITION & MD ==================== -->
<div class="slide" id="slide-7">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Appendix S1: Does MRAP2 Compete with Amylin or Destabilize AMY1R / AMY3R?</h1>
      <div class="sub"><strong>SUPPLEMENTARY DEEP-DIVE (ZHCO FOLLOW-UP)</strong> &nbsp;|&nbsp; <em>Cryo-EM Superposition (7TYF/7TZF), Quaternary Boltz-2 Co-Folding, and 8-System A100 Explicit-Solvent MD</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">APPENDIX S1 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div style="display: grid; grid-template-columns: 1045px 715px; gap: 24px; flex: 1;">
      <!-- Left: Quantitative Comparison Table -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div style="height:44px; background:#001965; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
            Quantitative Comparison: Cryo-EM Baselines vs Subunit &amp; Orthosteric Competition
          </div>
          <div style="padding:10px 16px; display:grid; grid-template-columns:repeat(3, 1fr); gap:12px;">
            <div style="background:#FFF; border:1.5px solid #001965; padding:6px 8px; text-align:center;">
              <div style="font-size:14px; font-weight:800; color:#001965;">Cryo-EM Fact (7TYF/7TZF)</div>
              <div style="font-size:11.2px; font-weight:700;">98.5% Amylin ICs on CTR; RAMP W84/P85 caps Tyr37</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #00857C; padding:6px 8px; text-align:center;">
              <div style="font-size:14px; font-weight:800; color:#00857C;">Mech 1: Subunit Competition</div>
              <div style="font-size:11.2px; font-weight:700;">80.0% RAMP3 &amp; 75.7% RAMP1 CTR-face shared w/ MRAP2</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #D9383A; padding:6px 8px; text-align:center;">
              <div style="font-size:14px; font-weight:800; color:#D9383A;">Mech 2: 7TM Pocket Block</div>
              <div style="font-size:11.2px; font-weight:700;">Amylin 7TM contacts drop 92&rarr;2 (AMY1R) &amp; 96&rarr;0 (AMY3R)</div>
            </div>
          </div>

          <div style="padding:0 16px;">
            <table class="std-tbl" style="font-size:11.8px;">
              <thead>
                <tr>
                  <th style="width:19%;">System / Condition</th>
                  <th style="width:17%;">Chains Evaluated</th>
                  <th style="width:22%;">3D Overlap / 7TM Contacts</th>
                  <th style="width:22%;">A100 MD &lt;dG_GBn2&gt; &amp; &lt;E_vdW&gt;</th>
                  <th style="width:20%;">Biophysical Conclusion</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong style="color:#001965;">Cryo-EM AMY1R (7TYF)</strong></td>
                  <td>CTR+RAMP1 : Amylin</td>
                  <td>87 7TM + 48 ECD + 2 RAMP1 (W84/P85)</td>
                  <td>&lt;dG&gt; = &minus;221.3 &plusmn; 5.1 | &lt;E_vdW&gt; = &minus;222.2</td>
                  <td>Native AMY1R reference (RMSD 0.41&Aring;)</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">Cryo-EM AMY3R (7TZF)</strong></td>
                  <td>CTR+RAMP3 : Amylin</td>
                  <td>91 7TM + 45 ECD + 3 RAMP3 (E74/W84/P85)</td>
                  <td>&lt;dG&gt; = &minus;197.5 &plusmn; 7.1 | &lt;E_vdW&gt; = &minus;227.7</td>
                  <td>Native AMY3R reference (RMSD 0.48&Aring;)</td>
                </tr>
                <tr style="background:#EBF7F5;">
                  <td><strong style="color:#00857C;">RAMP3 Subunit Comp.</strong></td>
                  <td>RAMP3:MRAP2 vs CTR</td>
                  <td>32/40 (80.0%) CTR face shared; 222 clashes</td>
                  <td><strong>&minus;212.9 (&minus;254.0 vdW) vs &minus;189.5 (&minus;217.5)</strong></td>
                  <td>MRAP2 outcompetes CTR (ddG = &minus;23.4)</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">RAMP1 Subunit Comp.</strong></td>
                  <td>RAMP1:MRAP2 vs CTR</td>
                  <td>28/37 (75.7%) CTR face shared; 172 clashes</td>
                  <td>&minus;156.8 (&minus;198.5 vdW) vs &minus;159.2 (&minus;202.7)</td>
                  <td>Comparable affinity; blocks AMY1R</td>
                </tr>
                <tr>
                  <td><strong style="color:#001965;">AMY1R Ternary (&minus;MRAP2)</strong></td>
                  <td>CTR+RAMP1 : Amylin</td>
                  <td>92 7TM + 73 ECD ICs (N-loop RMSD 1.27&Aring;)</td>
                  <td>&lt;dG&gt; = &minus;237.8 &plusmn; 6.7 | &lt;E_vdW&gt; = &minus;269.5</td>
                  <td>Deep 7TM orthosteric engagement</td>
                </tr>
                <tr style="background:#EBF7F5;">
                  <td><strong style="color:#D9383A;">AMY1R Quat. (+MRAP2)</strong></td>
                  <td>CTR+RAMP1+M : Amylin</td>
                  <td>2 7TM ICs (&minus;97.8%); displaced 21.7&Aring;</td>
                  <td><strong>&lt;dG&gt; = &minus;113.5 | &lt;E_vdW&gt; = &minus;149.6</strong></td>
                  <td>ddG = +124.3 | ddE_vdW = +119.9</td>
                </tr>
                <tr style="background:#EBF7F5;">
                  <td><strong style="color:#D9383A;">AMY3R &minus;/+ MRAP2</strong></td>
                  <td>CTR+RAMP3(&plusmn;M) : Amy</td>
                  <td>96 &rarr; 0 7TM ICs (&minus;100%); displaced 24.5&Aring;</td>
                  <td><strong>&minus;164.2 (&minus;223.6) &rarr; &minus;148.9 (&minus;163.1 vdW)</strong></td>
                  <td>ddG = +15.3 | ddE_vdW = +60.5</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div style="margin:10px 16px 14px 16px; background:#FFF; border:1px solid #D0D7E5; border-left:8px solid #D9383A; padding:10px 15px; font-size:12.6px; line-height:1.35;">
          <strong style="color:#D9383A;">Testable Wet-Lab Hypothesis (If Amylin cAMP / BRET Assay is Ready):</strong> Co-expressing WT MRAP2 will competitively sequester RAMP3/RAMP1 away from CTR and attenuate amylin/cagrilintide potency, whereas our FEP-designed obesity point-mutants (<strong>MRAP2 L115A/V, R125A/C</strong>) will lose RAMP binding and restore normal AMY1R/AMY3R signaling.
        </div>
      </div>

      <!-- Right: 2-Panel Competition & MD Plot + Summary -->
      <div style="background:#E8EEF7; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="height:44px; background:#00857C; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          Dual-Mechanism Competition &amp; A100 MD Energetics
        </div>
        <div style="padding:12px 16px; display:flex; flex-direction:column; justify-content:space-between; flex:1; gap:12px;">
          <div style="background:#FFF; border:1px solid #D0D7E5; padding:6px; height:285px; display:flex; align-items:center; justify-content:center;">
            <img src="data:image/png;base64,{b64_amy}" style="width:100%; height:100%; object-fit:contain;">
          </div>

          <div style="background:#FFF; border:1.5px solid #001965; flex:1; display:flex; flex-direction:column;">
            <div style="background:#001965; color:#FFF; font-size:13.2px; font-weight:700; padding:7px 14px;">ANSWERS TO ZHENG&rsquo;S TWO QUESTIONS (MECHANISM SUMMARY)</div>
            <div style="padding:10px 14px; font-size:12.4px; line-height:1.36; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
              <div>
                <strong style="color:#001965; font-size:13px;">1. Do Amylin and MRAP2 Compete in Binding to Amylin Receptors?</strong><br>
                <strong>YES &mdash; at two structural levels:</strong><br>
                &bull; <strong>Subunit Sequestration (MRAP2 vs CTR for RAMP1/3):</strong> MRAP2 occupies <strong>80.0% (32/40)</strong> of RAMP3&rsquo;s and <strong>75.7% (28/37)</strong> of RAMP1&rsquo;s CTR-binding residues, and binds RAMP3 more tightly than CTR in MD (<strong>ddG = &minus;23.43 kcal/mol</strong>).<br>
                &bull; <strong>Tyr37 Pocket Cap Occlusion:</strong> MRAP2 covers <strong>100%</strong> of the RAMP1/3 Trp84&ndash;Pro85 shelf that caps amylin&rsquo;s C-terminal Tyr37-NH2.
              </div>
              <div>
                <strong style="color:#D9383A; font-size:13px;">2. Does MRAP2 Affect the Stability of Amylin / Receptor Complexes?</strong><br>
                <strong>YES &mdash; severe destabilization &amp; 7TM ejection:</strong><br>
                &bull; In quaternary co-folding + MD, MRAP2 invades the CTR ECL2/ECL3/7TM entrance, reducing amylin&rsquo;s 7TM contacts by <strong>97.8% in AMY1R (ddG = +124.26, ddE_vdW = +119.92 kcal/mol)</strong> and <strong>100% in AMY3R (ddG = +15.26, ddE_vdW = +60.49 kcal/mol)</strong>.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Cao et al., <em>Science</em> 375, eabm9601 (2022)</div>
    <div>druggability repo &nbsp;|&nbsp; Appendix S1</div>
  </div>
</div>

<!-- ==================== SLIDE 8 (APPENDIX S2): DETAILED TWO-STUDY SYNTHESIS ==================== -->
<div class="slide" id="slide-8">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Appendix S2: Detailed Two-Study Comparison (2025 Science vs 2026 Sci Rep)</h1>
      <div class="sub"><strong>SUPPLEMENTARY LITERATURE SYNTHESIS (ZHCO)</strong> &nbsp;|&nbsp; <em>5-Stage Proteome Screening Cascade (2025), Curated Disease-Variant Case Studies (2026), and Reading Rules</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">APPENDIX S2 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Scientific Update &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div class="banner navy">
      <div style="color: #001965; font-weight: 700; font-size: 15.2px; margin-bottom: 3px;">How the Two Publications Connect (Figure 1&ndash;3 Synthesis):</div>
      <div><strong>&bull; 1st Study (Zhang et al., <em>Science</em> 2025):</strong> Built the computational engine (<code>omicMSAs</code> + <code>RF2-PPI</code>) and screened the human proteome (19,528 proteins &rarr; 17,849 PPIs @90% prec).<br>
      <strong>&bull; 2nd Study (Pei, Zhang &amp; Cong, <em>Sci Rep</em> 2026):</strong> Did <strong>NOT</strong> retrain a model or run a new proteome screen; used the 2025 resource as input for curated case studies (interface disease variants &amp; AlphaFold3 multi-subunit complexes).</div>
    </div>

    <div class="grid-3" style="flex: 1; margin: 14px 0;">
      <div class="card">
        <div class="card-hdr">1st Study: 2025 Science</div>
        <div class="card-sub">Proteome-Scale Engine &amp; Resource</div>
        <div class="card-body" style="gap: 10px; font-size: 13.4px;">
          <div><strong style="color:#001965;">&bull; Stage 1&ndash;2: 7x omicMSAs + RF2-PPI:</strong><br>Assembled <strong>21,415 eukaryotic species</strong> from 30 PB raw reads (7x deeper MSAs). Distilled <strong>223,440 AFDB domain-domain contacts</strong> (17x larger training set) + negative pairs &rarr; RF2-PPI (20x faster than AF2).</div>
          <div><strong style="color:#001965;">&bull; Stage 3&ndash;4: 4-Tier Cascade Funnel:</strong><br>20,296 proteins (19,528 screened; ~191M pairs) &rarr; Localization filter (<strong>111.2M</strong>) &rarr; DCA coevolution (<strong>43.6M</strong>) &rarr; RF2-PPI (<strong>~1.9M</strong>) &rarr; AF2 3D modeling.</div>
          <div><strong style="color:#001965;">&bull; Stage 5: Primary Resource Numbers:</strong><br><strong>29,256 PPIs (@80% prec) &amp; 17,849 (@90% prec)</strong>: 3,631 novel, 2,700 lacking complex templates (Data S6; 58% TM), <strong>1,413 with uncharacterized proteins</strong>, 4,950 with interface SAVs, 404 complexes (+139 new subunits).</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr teal">2nd Study: 2026 Sci Rep</div>
        <div class="card-sub teal">Curated Case Studies &amp; AF3 Assemblies</div>
        <div class="card-body" style="gap: 10px; font-size: 13.4px;">
          <div><strong style="color:#00857C;">&bull; Pathway Crosstalk &amp; Dark Proteins:</strong><br>1) <em>PMS1&ndash;FAAP24</em>: links DNA mismatch repair (MMR) to Fanconi anemia ICL repair.<br>2) <em>C12orf57&ndash;ANKRD50</em>: links dark protein C12orf57 to SNX27-retromer endocytic recycling.</div>
          <div><strong style="color:#00857C;">&bull; Interface Disease Variant Cases:</strong><br>1) <em>C12orf57 L51Q</em>: buried at ANKRD50 interface (Temtamy syndrome).<br>2) <em>BBS7&ndash;WDR19 (V80D)</em>: disrupts BBSome&ndash;IFT-A ciliary contact in Senior&ndash;L&oslash;ken ciliopathy.<br>3) <em>SCO1 (P174L) &ndash; COA6 (W59C)</em>: co-localizes across interface in complex IV deficiency.</div>
          <div><strong style="color:#00857C;">&bull; Higher-Order AF3 Complex Modeling:</strong><br>Superimposed binary models + AlphaFold3: identified <em>C19orf25</em> as a new NRZ tethering subunit, and modeled BLOC-1 / BORC / Sarcoglycan assemblies.</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr red">4 Rigorous Reading Rules</div>
        <div class="card-sub red">Critical Scientific Caveats (Do Not Overclaim)</div>
        <div class="card-body" style="gap: 9px; font-size: 13.2px;">
          <div><strong style="color:#D9383A;">&bull; 1. Not a Pure Blind Discovery Set:</strong><br>Of the 17,849 PPIs (@90% prec), 14,218 combined prior physical/genetic evidence with lower score cutoffs; only <strong>3,631 are novel</strong> (and 2,700 are zero-prior in Data S6).</div>
          <div><strong style="color:#D9383A;">&bull; 2. &lsquo;No PDB Template&rsquo; &ne; Unknown Fold:</strong><br>Data S6&rsquo;s 2,700 pairs lack homologous <strong>complex</strong> templates in PDB, NOT necessarily individual monomer structures.</div>
          <div><strong style="color:#D9383A;">&bull; 3. Interface SAV &ne; Proven Disruption:</strong><br>4,950 PPIs carry disease SAVs at &lt;6 &Aring; interfaces (and AFDB DDI training used predicted monomers). This proposes a testable hypothesis, not experimental proof that the variant abolishes binding.</div>
          <div><strong style="color:#D9383A;">&bull; 4. pLDDT / ipTM &ne; In Vivo Binding:</strong><br>High structural confidence reflects fold/packing geometry, not tissue co-expression or physiological stoichiometry.</div>
        </div>
      </div>
    </div>

    <div class="banner">
      <strong style="color: #001965;">Exact 2025 Screening Cascade &amp; Output Breakdown:</strong>
      20,296 human proteins &rarr; 19,528 screened (~191M pairs) &rarr; <strong>111.2M localization-filtered</strong> &rarr; <strong>43.6M DCA-filtered</strong> &rarr; <strong>~1.9M RF2-PPI hits</strong> &rarr; AF2 3D modeling &rarr; <strong>29,256 PPIs (@80% est. precision)</strong> &amp; <strong>17,849 PPIs (@90% est. precision)</strong> &rarr; 3,631 unreported &rarr; 2,700 lacking homologous complex templates (Data S6).
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Appendix S2</div>
  </div>
</div>

</body>
</html>
"""

OUT_HTML.write_text(html, encoding="utf-8")
print("Wrote 8-slide HTML:", OUT_HTML)


async def render_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto(f"file://{OUT_HTML}", wait_until="networkidle")
        await page.wait_for_timeout(400)

        # Print 8-page PDF
        await page.pdf(
            path=str(OUT_PDF),
            width="1920px",
            height="1080px",
            print_background=True,
            margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"},
        )
        print(f"Rendered PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")

        # Screenshot each slide element at 2x
        for i in range(1, 9):
            el = await page.query_selector(f"#slide-{i}")
            out_png = SLIDE_DIR / f"slide_{i:02d}@2x.png"
            await el.screenshot(path=str(out_png))
            print(f"Rendered slide {i} PNG: {out_png} ({out_png.stat().st_size:,} bytes)")

        await browser.close()


asyncio.run(render_all())
