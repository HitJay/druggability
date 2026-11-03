#!/usr/bin/env python
"""Generate self-contained 2-page 1920x1080 HTML proposal and render PDF + @1x/@2x/@3x PNGs via Playwright."""
import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path("/das/user/QYJI/druggability")
IMG_PATH = ROOT / "humanPPI_repro/results/repro_2panel_evidence.png"
BQ1_IMG_PATH = ROOT / "reports/bq1_99_triage/bq1_99_triage_and_fep_2panel.png"

OUT_HTML = ROOT / "reports/ppi_screening_proposal_2026-10-28.html"
OUT_PDF = ROOT / "reports/ppi_screening_proposal_2026-10-28.pdf"
OUT_P1_2X = ROOT / "reports/ppi_screening_proposal_2026-10-28_p1@2x.png"
OUT_P2_2X = ROOT / "reports/ppi_screening_proposal_2026-10-28_p2@2x.png"
OUT_1X = ROOT / "reports/ppi_screening_proposal_2026-10-28.png"
OUT_2X = ROOT / "reports/ppi_screening_proposal_2026-10-28@2x.png"
OUT_3X = ROOT / "reports/ppi_screening_proposal_2026-10-28@3x.png"

b64_img = base64.b64encode(IMG_PATH.read_bytes()).decode("ascii")
b64_bq1 = base64.b64encode(BQ1_IMG_PATH.read_bytes()).decode("ascii")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Druggability Agent Platform Landscape &amp; PPI Screening Campaign Proposal (2-Page Deck)</title>
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

  /* Top Header Banner */
  .header {{
    height: 136px;
    background: #001965;
    padding: 18px 64px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }}
  .header-left h1 {{
    font-size: 27.5px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.2px;
    margin-bottom: 8px;
  }}
  .header-left .sub {{
    font-size: 15.5px;
    color: #E8EEF7;
  }}
  .header-left .sub strong {{ color: #FFFFFF; }}
  .header-left .sub em {{ font-style: italic; color: #CADCFC; }}
  .header-right {{
    text-align: right;
    color: #FFFFFF;
    flex-shrink: 0;
  }}
  .header-right .badge {{
    display: inline-block;
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 5px 14px;
    border-radius: 4px;
    font-size: 14.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }}
  .header-right .meta {{
    font-size: 13.5px;
    color: #E8EEF7;
  }}

  /* Footer */
  .footer {{
    height: 40px;
    margin: 0 64px;
    padding-bottom: 6px;
    border-top: 1px solid #D0D7E5;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: #5A6070;
    flex-shrink: 0;
  }}

  /* ==========================================================================
     SLIDE 1 STYLES: Capability Landscape + Benchmarks Table
     ========================================================================== */
  .s1-body {{
    flex: 1;
    padding: 16px 64px 10px 64px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 0;
  }}
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
  .cap-body strong.navy {{ color: #001965; }}
  .cap-body strong.teal {{ color: #00857C; }}
  .cap-body strong.red  {{ color: #D9383A; }}

  .bench-wrap {{
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }}
  .bench-hdr {{
    height: 34px;
    background: #001965;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
    padding: 0 16px;
    display: flex;
    align-items: center;
  }}
  table.bench-tbl {{
    width: 100%;
    border-collapse: collapse;
    border: 1.5px solid #D0D7E5;
    font-size: 11.4px;
    line-height: 1.28;
  }}
  table.bench-tbl th {{
    background: #00857C;
    color: #FFFFFF;
    text-align: left;
    padding: 6px 10px;
    font-size: 11.8px;
    font-weight: 700;
    border: 1px solid #D0D7E5;
  }}
  table.bench-tbl td {{
    padding: 5.5px 10px;
    border: 1px solid #D0D7E5;
    vertical-align: middle;
  }}
  table.bench-tbl tr:nth-child(even) td {{ background: #E8EEF7; }}
  table.bench-tbl tr:nth-child(odd) td {{ background: #FFFFFF; }}
  table.bench-tbl tr.hl-row td {{ background: #EBF7F5; font-weight: 600; }}

  /* ==========================================================================
     SLIDE 2 STYLES: PPI Campaign Validation & Business Questions
     ========================================================================== */
  .s2-main {{
    flex: 1;
    padding: 16px 64px 10px 64px;
    display: grid;
    grid-template-columns: 845px 923px;
    gap: 24px;
    min-height: 0;
  }}
  .panel {{
    background: #F2F4F8;
    border: 1.5px solid #D0D7E5;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .panel-blue {{ background: #E8EEF7; }}
  .panel-hdr {{
    height: 44px;
    padding: 0 18px;
    display: flex;
    align-items: center;
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
    flex-shrink: 0;
  }}
  .hdr-teal {{ background: #00857C; }}
  .hdr-navy {{ background: #001965; }}
  .hdr-red  {{ background: #D9383A; }}
  .panel-body {{
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    flex: 1;
    min-height: 0;
  }}

  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    flex-shrink: 0;
  }}
  .kpi-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-top: 5px solid #001965;
    padding: 7px 6px;
    text-align: center;
  }}
  .kpi-card.teal {{ border-top-color: #00857C; }}
  .kpi-card.red  {{ border-top-color: #D9383A; }}
  .kpi-val {{ font-size: 19.5px; font-weight: 800; color: #001965; line-height: 1.15; margin-bottom: 2px; }}
  .kpi-card.teal .kpi-val {{ color: #00857C; }}
  .kpi-card.red  .kpi-val {{ color: #D9383A; }}
  .kpi-lbl {{ font-size: 11.8px; font-weight: 700; color: #1A1A2E; }}
  .kpi-sub {{ font-size: 10.4px; color: #5A6070; }}

  .plot-box {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    padding: 4px;
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .plot-box img {{ width: 100%; height: 100%; object-fit: contain; }}

  .ev-box {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-left: 7px solid #001965;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 11.8px;
    line-height: 1.32;
  }}

  .matrix-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }}
  .mat-box {{
    border: 1.5px solid #00857C;
    background: #EBF7F5;
    display: flex;
    flex-direction: column;
  }}
  .mat-box.red {{ border-color: #D9383A; background: #FDF2F2; }}
  .mat-hdr {{
    height: 26px;
    background: #00857C;
    color: #FFFFFF;
    font-size: 11.4px;
    font-weight: 700;
    padding: 0 10px;
    display: flex;
    align-items: center;
  }}
  .mat-box.red .mat-hdr {{ background: #D9383A; }}
  .mat-body {{
    padding: 6px 10px;
    font-size: 11.1px;
    line-height: 1.30;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}

  .right-col {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 14px;
    min-height: 0;
  }}
  .bq-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    flex: 1;
  }}
  .bq-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    display: flex;
    flex-direction: column;
  }}
  .bq-hdr {{
    height: 32px;
    background: #001965;
    color: #FFFFFF;
    font-size: 12.2px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .bq-hdr.teal {{ background: #00857C; }}
  .bq-hdr.red  {{ background: #D9383A; }}
  .bq-sub {{
    background: #F2F4F8;
    font-size: 11.4px;
    font-weight: 700;
    color: #001965;
    text-align: center;
    padding: 4px 6px;
    border-bottom: 1px solid #E2E8F0;
  }}
  .bq-sub.teal {{ color: #00857C; }}
  .bq-sub.red  {{ color: #D9383A; }}
  .bq-body {{
    font-size: 11.4px;
    line-height: 1.33;
    padding: 7px 10px;
  }}

  .pilot-grid {{
    display: grid;
    grid-template-columns: 440px 435px;
    gap: 14px;
    flex: 1;
    min-height: 0;
  }}
  .pilot-left {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
  }}
  .bq1-img-box {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    padding: 4px;
    height: 205px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .bq1-img-box img {{ width: 100%; height: 100%; object-fit: contain; }}
  .sub-card {{
    background: #FFFFFF;
    border: 1.5px solid #001965;
    display: flex;
    flex-direction: column;
    flex: 1;
  }}
  .sub-card.teal {{ border-color: #00857C; }}
  .sub-hdr {{
    height: 28px;
    background: #001965;
    color: #FFFFFF;
    font-size: 11.4px;
    font-weight: 700;
    padding: 0 10px;
    display: flex;
    align-items: center;
  }}
  .sub-card.teal .sub-hdr {{ background: #00857C; }}
  .sub-body {{
    padding: 7px 10px;
    font-size: 11.2px;
    line-height: 1.32;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }}
</style>
</head>
<body>

<!-- ==========================================================================
     PAGE 1: Systematic Capability Landscape & Benchmarks
     ========================================================================== -->
<div class="slide" id="slide-1">
  <div class="header">
    <div class="header-left">
      <h1>Druggability Agent Platform: Systematic Capability Landscape &amp; Benchmarks</h1>
      <div class="sub">
        <strong>PART 1: END-TO-END COMPUTATIONAL PIPELINE</strong> &nbsp;|&nbsp;
        <em>From Target Genetics &amp; PPI Interactome to Peptide/Small-Molecule Pharmacology, MD/FEP &amp; 3D Delivery</em>
      </div>
    </div>
    <div class="header-right">
      <div class="badge">PAGE 1 OF 2 &nbsp;|&nbsp; PROPOSAL</div>
      <div class="meta">RIC-410 &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="s1-body">
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
          <div>&bull; <strong class="navy">5-Axis Target Profiling:</strong> Open Targets GraphQL + ChEMBL ligandability + fpocket + clinical precedents + safety across SM / Antibody / Peptide / PROTAC.</div>
          <div>&bull; <strong class="navy">Human Genetics &amp; Safety Gate:</strong> GWAS / ClinVar / UKB WES variant mapping + bidirectional target safety evaluation (W40-W44 &amp; 25-gene T2D/obesity panels).</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr teal">2. Proteome PPI &amp; Interface Variants [NEW]</div>
        <div class="cap-tag teal">RF2-PPI (6x A100) | Boltz-2 | interface_variants</div>
        <div class="cap-body">
          <div>&bull; <strong class="teal">Proteome Partner Screen:</strong> 20,260-protein coevolution + structure funnel (~6 GPU-h/bait; 262x enrichment over random; 43.2% recall on complexes &gt;1,500 &Aring;&sup2;).</div>
          <div>&bull; <strong class="teal">3D Disease-Variant Triage:</strong> Maps UniProt + AlphaMissense pathogenic SAVs onto 6&Aring; contact surfaces to design surgical point-mutant negative controls.</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr">3. Peptide Engineering &amp; CNS/BBB Exposure</div>
        <div class="cap-tag">druggability.peptide (affinity | scan | chem_mod | bbb)</div>
        <div class="cap-body">
          <div>&bull; <strong class="navy">Peptide Structural Pharmacology:</strong> PRODIGY contact affinity (&Delta;G/K<sub>d</sub>), high-throughput Ala/20-AA mutational hotspot scan, and subtype selectivity counter-screens.</div>
          <div>&bull; <strong class="navy">Protraction &amp; BBB Platform:</strong> 3D cone steric audit for C16/C18/C20 lipidation exit vectors + ESM-2 multi-task heads (BBB AUC=0.89, hemolytic AUC=1.00).</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr teal">4. Pocket Detection, AI VS &amp; Target Fishing</div>
        <div class="cap-tag teal">druggability.pocket | drugclip | vina | image2smiles</div>
        <div class="cap-body">
          <div>&bull; <strong class="teal">Multi-Tier Virtual Screening:</strong> Contrastive DrugCLIP (2.94M library in ~22s) &rarr; tight-box AutoDock Vina (redocking &lt;2.0 &Aring; QC gate) &rarr; Boltz-2 affinity &amp; Murcko clustering.</div>
          <div>&bull; <strong class="teal">Off-Target Deconvolution &amp; OCR:</strong> 5-layer ligand target fishing + clinical C<sub>max,u</sub>/K<sub>i</sub> occupancy gating; DECIMER/MolScribe chemical structure recovery from literature.</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr red">5. Explicit-Solvent MD &amp; Alchemical FEP/TI</div>
        <div class="cap-tag red">OpenMM 8.3 CUDA | openmmtools.alchemy (A100)</div>
        <div class="cap-body">
          <div>&bull; <strong class="red">High-Throughput Explicit MD:</strong> All-atom Amber14SB + TIP3P water + 0.15M NaCl on A100 (&gt;2,100 ns/day); resolves static MM/GBSA vacuum cavity artifacts &amp; steric ejection.</div>
          <div>&bull; <strong class="red">Alchemical FEP &amp; Annihilation TI:</strong> Dual-topology relative FEP &amp; 8-lambda annihilation alanine-scanning TI to quantify residue/variant energetic hotspots (&Delta;&Delta;G in kcal/mol).</div>
        </div>
      </div>

      <div class="cap-card">
        <div class="cap-hdr">6. Automated 3D Dossiers &amp; Wet-Lab Governance</div>
        <div class="cap-tag">druggability.report | 3Dmol.js | Scientific Boundaries</div>
        <div class="cap-body">
          <div>&bull; <strong class="navy">Zero-Install 3D Deliverables:</strong> Self-contained 3Dmol.js WebGL HTML dossiers, editable NN-styled PPTX + vector PDF decks, and ranked Excel/CSV scorecards.</div>
          <div>&bull; <strong class="navy">Audit &amp; Boundary Governance:</strong> Strict [FACT]/[OBS]/[MECH]/[HYP] tagging; mandatory homolog negative controls (ipTM &ne; potency); positive hypothesis generator only.</div>
        </div>
      </div>
    </div>

    <!-- Bottom Benchmark Table -->
    <div class="bench-wrap">
      <div class="bench-hdr">Production-Validated Portfolio Benchmarks Across Modalities (Real Executed Outputs &amp; Wet-Lab Handovers)</div>
      <table class="bench-tbl">
        <tr>
          <th style="width:14%;">Modality / Domain</th>
          <th style="width:16%;">Project &amp; Ticket</th>
          <th style="width:20%;">Computational Stack Executed</th>
          <th style="width:34%;">Headline Verified Biophysical / Biological Finding</th>
          <th style="width:16%;">Deliverable &amp; Status</th>
        </tr>
        <tr>
          <td><strong>Peptide Selectivity &amp; Protraction</strong></td>
          <td><strong>OXTR vs V1a/V1b/V2R &amp; GLP-1R (RIC-403)</strong></td>
          <td>Cryo-EM 7QVM/7DW9 + PRODIGY + A100 Explicit MD + 3D Lipidation Cone</td>
          <td>Explained &gt;1,000x selectivity: Pro7Gly releases V2R TM1 clash (3.51&Aring;, 70.8&Aring; MD ejection); verified Leu8 C18-diacid exit vector (0 clashes, ~160h PK).</td>
          <td>3D HTML + 12-Slide Deck Delivered (Mingyue)</td>
        </tr>
        <tr>
          <td><strong>Small-Molecule GPCR &amp; FEP</strong></td>
          <td><strong>GPR81 (HCAR1) vs HCAR2/3 (RIC-396)</strong></td>
          <td>45-Cmpd Vina + Boltz-2 Affinity + Steric Contradiction + 3-Leg OpenFEP</td>
          <td>Eliminated flushing liability via HCAR2 basic clash wall (+45.2 kcal/mol); proved AZ1 vs lactate mutual exclusion; converged c30/c31 FEP.</td>
          <td>3D HTML + 45-Cmpd Scorecard Delivered (UHYG)</td>
        </tr>
        <tr>
          <td><strong>Ligand Target Fishing &amp; TI</strong></td>
          <td><strong>TSPO 5-Ligand Panel (PK11195, Emapunil) (RIC-408)</strong></td>
          <td>5-Source Curation + 17-Pocket Vina Gate + 250ps MD + 57-Anchor TI</td>
          <td>Proved CAR (NR1I3) is PK11195 #2 target (IC<sub>50</sub> 25-56 nM, 5 methods); discovered TSPO dimer pocket 4RYI_p26 (LEU58 +7.6 kJ/mol) &amp; C<sub>max</sub>/K<sub>i</sub> gate.</td>
          <td>6-Round Dossiers + 7-Slide Deck Delivered (ZHCO)</td>
        </tr>
        <tr>
          <td><strong>Molecular Glue &amp; Cryptic Pocket</strong></td>
          <td><strong>GIGYF1-GRB10/14 &amp; GHSR VS (RIC-407 / RIC-392)</strong></td>
          <td>Crystal 7RUQ/2AUH + UKB 454k WES Mutagenesis + 7,931-Cmpd Vina/Boltz-2</td>
          <td>Identified 445 &Aring;&sup3; cryptic glue pocket at GIGYF1 interface; UKB p.Tyr498Cys drops affinity &gt;80x (+2.74 kcal/mol, T2D OR=5.91); 20 GHSR chemotypes.</td>
          <td>3D Glue Dossier &amp; Ranked Hits (GO Decision)</td>
        </tr>
        <tr>
          <td><strong>Peptide CNS/BBB &amp; Safety Gate</strong></td>
          <td><strong>MC4R / RORA BBB &amp; 3_Safety (RIC-349 / RIC-409)</strong></td>
          <td>ESM-2 + Protraction Penaliser + Local vLLM Safety Gate + 175-Gene Dry/Wet</td>
          <td>BBB test AUC=0.89 (flagged protracted peptide CNS exclusion); 298 target-direction safety audits (0 gate errors); 175-gene HepG2 ATP/TMRM calibration.</td>
          <td>Production CLI / Service &amp; Weekly Panels</td>
        </tr>
        <tr class="hl-row">
          <td><strong style="color:#00857C;">Proteome PPI &amp; Interface Triage</strong></td>
          <td><strong>Cardiometabolic Data S6 99-Lead Pilot (RIC-410)</strong></td>
          <td>RF2-PPI (6x A100) + 4-Criteria Triage + Boltz-2 omicMSA + A100 MD &amp; FEP</td>
          <td>8/99 leads pass all 4/4 criteria (#1 RAMP3-MRAP2 ipTM=0.868, MD RMSD 0.49&Aring;); obesity SAVs R125/L115 are top FEP hotspots (+6.25/+5.21 kcal/mol).</td>
          <td>Page 2 Proposal + 99-Pair Workbook (ZHCO)</td>
        </tr>
      </table>
    </div>
  </div>

  <div class="footer">
    <div>Platform: <code>druggability</code> repo (hpccnrd001 A100 Cluster) &nbsp;|&nbsp; Validated tickets: RIC-349, RIC-392, RIC-396, RIC-403, RIC-407, RIC-408, RIC-410</div>
    <div>druggability repo &nbsp;|&nbsp; Page 1/2</div>
  </div>
</div>

<!-- ==========================================================================
     PAGE 2: PPI & Disease-Interface Screening Campaign Proposal
     ========================================================================== -->
<div class="slide" id="slide-2">
  <div class="header">
    <div class="header-left">
      <h1>PPI &amp; Disease-Interface Screening Campaign: Validation &amp; Business Questions</h1>
      <div class="sub">
        <strong>PART 2: MODULE 2 DEEP-DIVE &amp; CAMPAIGN ALIGNMENT</strong> &nbsp;|&nbsp;
        <em>Concise Baker/Cong Summary, In-House A100 Validation, 3 Candidate Business Questions &amp; BQ-1 Pilot</em>
      </div>
    </div>
    <div class="header-right">
      <div class="badge">PAGE 2 OF 2 &nbsp;|&nbsp; PROPOSAL</div>
      <div class="meta">RIC-410 &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="s2-main">
    <!-- Left Column: Streamlined Baker Summary, In-House Validation & Boundaries -->
    <div class="panel">
      <div class="panel-hdr hdr-teal">1. Baker Engine Summary, In-House Validation &amp; Scope Boundaries</div>
      <div class="panel-body">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-val">200M&rarr;17.8k</div>
            <div class="kpi-lbl">Baker Interactome</div>
            <div class="kpi-sub">2,700 S6 novel (58% TM)</div>
          </div>
          <div class="kpi-card teal">
            <div class="kpi-val">262x Lift</div>
            <div class="kpi-lbl">In-House 33k Audit</div>
            <div class="kpi-sub">AUCPR 0.262 (r=0.919)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val">43.2% vs 4.5%</div>
            <div class="kpi-lbl">Large vs SLiM Recall</div>
            <div class="kpi-sub">&gt;1,500 &Aring;&sup2; vs &lt;800 &Aring;&sup2;</div>
          </div>
          <div class="kpi-card red">
            <div class="kpi-val">~6 GPU-h</div>
            <div class="kpi-lbl">Per-Bait Screen</div>
            <div class="kpi-sub">1 vs 20,260 on 6x A100</div>
          </div>
        </div>

        <div class="plot-box">
          <img src="data:image/png;base64,{b64_img}" alt="PR Curve and Biological Interface Sensitivity">
        </div>

        <div class="ev-box">
          <div><strong style="color:#001965;">&bull; 2025 Science vs 2026 Sci Rep (FACT):</strong> 2025 built omicMSAs (7x) + RF2-PPI (20x faster) &rarr; <strong>17,849 PPIs @90% prec</strong> (3,631 novel; 2,700 Data S6 lacking complex templates). 2026 mapped clinical SAVs onto 2025 3D interfaces.</div>
          <div><strong style="color:#00857C;">&bull; Prospective Proof &amp; Caveats (OBS):</strong> <strong>11 Data S6 zero-prior pairs</strong> confirmed by cryo-EM/co-IP in 2024-2026 (e.g., <em>TMEM209-NUP210</em>, <em>DND1-NANOS3</em>). On <strong>CASR</strong>, <strong>64% of 89 pathogenic SAVs</strong> map to the dimer interface (<em>note: interface SAVs &amp; ipTM require tissue co-expression + wet-lab validation</em>).</div>
        </div>

        <div class="matrix-grid">
          <div class="mat-box">
            <div class="mat-hdr">IDEAL TARGETS (HIGH SENSITIVITY)</div>
            <div class="mat-body">
              <div>&bull; <strong style="color:#00857C;">Large obligate complexes</strong> (43.2% recall &gt;1,500 &Aring;&sup2;)</div>
              <div>&bull; <strong style="color:#00857C;">Transmembrane / organelle PPIs</strong> (58% of S6; missed by AP-MS)</div>
              <div>&bull; <strong style="color:#00857C;">Disease-mutated interfaces</strong> for disruptor control design</div>
              <div>&bull; <strong style="color:#001965;">Rule: Positive generator only</strong> (never exclude by low score)</div>
            </div>
          </div>
          <div class="mat-box red">
            <div class="mat-hdr">BLIND SPOTS (DO NOT EXCLUDE)</div>
            <div class="mat-body">
              <div>&bull; <strong style="color:#D9383A;">Transient / PTM signaling</strong> (GPCR-arrestin, kinase-substrate)</div>
              <div>&bull; <strong style="color:#D9383A;">Disordered SLiMs (&lt;800 &Aring;&sup2;)</strong> (only 4.5% recall at @90% prec)</div>
              <div>&bull; <strong style="color:#D9383A;">Immune / TCR-MHC &amp; paralogs</strong> (needs GTEx co-expression gate)</div>
              <div>&bull; <strong style="color:#001965;">Multi-Platform Synergy:</strong> Route hits &rarr; Module 4/5 MD &amp; FEP</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column: 3 Candidate Business Questions + Completed Phase-1 Pilot -->
    <div class="right-col">
      <!-- Top Right: 3 Candidate Business Questions -->
      <div class="panel panel-blue" style="height: 350px;">
        <div class="panel-hdr hdr-navy">2. Campaign Business Question Menu (Connecting Module 2 &rarr; Modules 1, 4, 5 &amp; 6)</div>
        <div class="panel-body" style="gap: 8px;">
          <div class="bq-row">
            <div class="bq-card">
              <div class="bq-hdr">BQ-1: Portfolio Partner Mining</div>
              <div class="bq-sub">99 Data S6 Leads &rarr; 8 Pass 4/4</div>
              <div class="bq-body">Triage 99 unflagged cardiometabolic Data S6 leads via <strong>Module 1</strong> genetics/co-expression + <strong>Module 2</strong> 3D SAVs + <strong>Module 5</strong> MD/FEP &rarr; nominate top pairs for co-IP/BRET.</div>
            </div>
            <div class="bq-card">
              <div class="bq-hdr teal">BQ-2: De Novo Target Screen</div>
              <div class="bq-sub teal">1 Priority Bait vs 20,260 Proteins</div>
              <div class="bq-body">For orphan/transmembrane receptors or intracellular targets where AP-MS fails, screen 20,260 proteins (<strong>~6 GPU-h/bait</strong>) for missing co-receptors, chaperones, or E3 ligases.</div>
            </div>
            <div class="bq-card">
              <div class="bq-hdr red">BQ-3: 3D Interface &amp; Controls</div>
              <div class="bq-sub red">Disruptor Mutants &amp; Groove VS</div>
              <div class="bq-body">Map 6&Aring; contact surfaces &amp; clinical pathogenic SAVs (<code>interface-variants</code>, ~15 min/pair) to design surgical <strong>point-mutant negative controls</strong> and dock modulators (<strong>Module 4</strong>).</div>
            </div>
          </div>
          <div style="background:#FFFFFF;border:1px solid #D0D7E5;border-left:7px solid #001965;padding:7px 12px;font-size:11.2px;line-height:1.30;">
            <strong style="color:#001965;">End-to-End Wet-Lab Handoff Package (~6 GPU-h / Bait):</strong>
            (1) Calibrated partner probability (@90% precision) + GTEx co-expression, (2) 3D complex coordinates &amp; 6&Aring; contact residues, and (3) FEP-verified interface SAV point-mutant negative controls for co-IP / BioID / BRET.
          </div>
        </div>
      </div>

      <!-- Bottom Right: Executed Phase-1 Pilot -->
      <div class="panel" style="flex: 1;">
        <div class="panel-hdr hdr-red">3. Executed Phase-1 Pilot: BQ-1 99-Pair Triage + RAMP3-MRAP2 Full-Pipeline Audit</div>
        <div class="panel-body">
          <div class="pilot-grid">
            <div class="pilot-left">
              <div class="bq1-img-box">
                <img src="data:image/png;base64,{b64_bq1}" alt="BQ-1 99-Pair Triage and RAMP3-MRAP2 FEP">
              </div>
              <div class="sub-card">
                <div class="sub-hdr">BQ-1 4-CRITERIA TRIAGE (99 LEADS &rarr; 8 PASS 4/4)</div>
                <div class="sub-body">
                  <div>&bull; <strong style="color:#001965;">Funnel:</strong> C1 Both-Genetics 60 (46 Human), C2 Pathway 43, C3 Direct Perturb 14, C4 CM Co-expr 56 &rarr; <strong>8 pass 4/4</strong> (+14 pass 3/4).</div>
                  <div>&bull; <strong style="color:#001965;">Top 6 Pure-Human 4/4 Winners:</strong> <strong>#1 RAMP3-MRAP2</strong>, <strong>#2 RAMP1-MRAP2</strong> (Amylin/CagriSema axis), #3 NR3C1-FOXO3, #4 CD80-CSF3, #5 TLR4-LTBR, #6 GP1BA-F2RL2.</div>
                </div>
              </div>
            </div>

            <div class="sub-card teal">
              <div class="sub-hdr">#1 RAMP3-MRAP2: CROSS-MODULE PROOF</div>
              <div class="sub-body" style="justify-content: space-between; flex: 1;">
                <div>&bull; <strong style="color:#001965;">Mod 2 (Boltz-2 + omicMSA):</strong> Tightly packed TM+ECD complex (<strong>ipTM=0.868</strong>, 180 contacts &le;5&Aring;; TM contact prob=0.590/0.865).</div>
                <div>&bull; <strong style="color:#D9383A;">Mod 5 (A100 MD &amp; FEP Hotspots):</strong> Stable in explicit-solvent MD (<strong>RMSD 0.49&Aring;</strong>). Human monogenic obesity SAVs MRAP2 <strong>R125C (+6.25 kcal/mol)</strong> &amp; <strong>L115V (+5.21 kcal/mol)</strong> are #1/#2 FEP hotspots.</div>
                <div>&bull; <strong style="color:#001965;">Mod 3/5 (AMY1R/3R Competition):</strong> Cryo-EM (7TYF/7TZF) + 8-system MD show MRAP2 shares <strong>80% of RAMP3&rsquo;s CTR face</strong> (&Delta;&Delta;G=&minus;23.4 kcal/mol vs CTR) &amp; blocks Amylin 7TM entry (96&rarr;0 contacts).</div>
                <div>&bull; <strong style="color:#D9383A;">Mod 4 (Groove Virtual Screen):</strong> Ubrogepant (&minus;7.81 kcal/mol) &amp; Rimegepant (ternary ligand_ipTM=0.950) selectively bind the composite RAMP3-MRAP2 ECD groove.</div>
                <div>&bull; <strong style="color:#001965;">Mod 6 (Wet-Lab Assay Controls):</strong> Delivered <strong>MRAP2 L115A/V, R125A/C &amp; RAMP3 W56A</strong> point-mutant controls to test AMY1R/3R rescue in co-IP / BRET / cAMP.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="footer">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) &nbsp;|&nbsp; Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) &nbsp;|&nbsp; Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 2/2</div>
  </div>
</div>

</body>
</html>
"""

OUT_HTML.write_text(html, encoding="utf-8")
print("Wrote 2-page HTML:", OUT_HTML)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])

        # 1) Export 2-page vector PDF
        ctx_pdf = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page_pdf = await ctx_pdf.new_page()
        await page_pdf.goto(f"file://{OUT_HTML}", wait_until="networkidle")
        await page_pdf.wait_for_timeout(400)
        await page_pdf.pdf(
            path=str(OUT_PDF),
            width="1920px",
            height="1080px",
            print_background=True,
            margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},
        )
        print(f"Rendered 2-page PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")
        await ctx_pdf.close()

        # 2) Render individual slide PNGs (@2x) + stacked 2-page composite PNGs (@1x, @2x, @3x)
        for scale, out_stack in [(1, OUT_1X), (2, OUT_2X), (3, OUT_3X)]:
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 2160},
                device_scale_factor=scale,
            )
            page = await ctx.new_page()
            await page.goto(f"file://{OUT_HTML}", wait_until="networkidle")
            await page.wait_for_timeout(300)
            if scale == 2:
                el1 = await page.query_selector("#slide-1")
                el2 = await page.query_selector("#slide-2")
                await el1.screenshot(path=str(OUT_P1_2X))
                await el2.screenshot(path=str(OUT_P2_2X))
                print(f"Rendered Page 1 @2x: {OUT_P1_2X} ({OUT_P1_2X.stat().st_size:,} bytes)")
                print(f"Rendered Page 2 @2x: {OUT_P2_2X} ({OUT_P2_2X.stat().st_size:,} bytes)")
            await page.screenshot(path=str(out_stack), full_page=True, omit_background=False)
            print(f"Rendered 2-page stacked {scale}x PNG: {out_stack} ({out_stack.stat().st_size:,} bytes)")
            await ctx.close()

        await browser.close()


asyncio.run(main())
