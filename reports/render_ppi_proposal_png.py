#!/usr/bin/env python
"""Generate self-contained 1920x1080 HTML one-pager (Biology-friendly edition) and render @1x/@2x/@3x PNG via Playwright."""
import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path("/das/user/QYJI/druggability")
IMG_PATH = ROOT / "humanPPI_repro/results/repro_2panel_evidence.png"
OUT_HTML = ROOT / "reports/ppi_screening_proposal_2026-10-28.html"
OUT_1X = ROOT / "reports/ppi_screening_proposal_2026-10-28.png"
OUT_2X = ROOT / "reports/ppi_screening_proposal_2026-10-28@2x.png"
OUT_3X = ROOT / "reports/ppi_screening_proposal_2026-10-28@3x.png"

b64_img = base64.b64encode(IMG_PATH.read_bytes()).decode("ascii")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Proteome-Wide Binding Partner &amp; Disease-Interface Triage</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    background: #FFFFFF;
    font-family: 'Segoe UI', Calibri, -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1A1A2E;
    -webkit-font-smoothing: antialiased;
  }}
  .slide {{
    width: 1920px;
    height: 1080px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  /* Top Header Banner */
  .header {{
    height: 138px;
    background: #001965;
    padding: 20px 64px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }}
  .header-left h1 {{
    font-size: 31px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.3px;
    margin-bottom: 8px;
  }}
  .header-left .sub {{
    font-size: 16.5px;
    color: #E8EEF7;
  }}
  .header-left .sub strong {{
    color: #FFFFFF;
  }}
  .header-left .sub em {{
    font-style: italic;
    color: #CADCFC;
  }}
  .header-right {{
    text-align: right;
    color: #FFFFFF;
  }}
  .header-right .badge {{
    display: inline-block;
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 5px 14px;
    border-radius: 4px;
    font-size: 15.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }}
  .header-right .meta {{
    font-size: 14px;
    color: #E8EEF7;
  }}

  /* Main 2-Column Workspace */
  .main {{
    flex: 1;
    padding: 22px 64px 14px 64px;
    display: grid;
    grid-template-columns: 880px 884px;
    gap: 28px;
    min-height: 0;
  }}

  /* Panel container */
  .panel {{
    background: #F2F4F8;
    border: 1.5px solid #D0D7E5;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .panel-blue {{
    background: #E8EEF7;
  }}
  .panel-hdr {{
    height: 50px;
    padding: 0 22px;
    display: flex;
    align-items: center;
    font-size: 17.5px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.1px;
    flex-shrink: 0;
  }}
  .hdr-teal {{ background: #00857C; }}
  .hdr-navy {{ background: #001965; }}
  .hdr-red  {{ background: #D9383A; }}

  .panel-body {{
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    flex: 1;
    min-height: 0;
  }}

  /* Left Column: 4 KPI Cards */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    flex-shrink: 0;
  }}
  .kpi-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-top: 6px solid #001965;
    padding: 10px 8px 9px 8px;
    text-align: center;
  }}
  .kpi-card.teal {{ border-top-color: #00857C; }}
  .kpi-card.red  {{ border-top-color: #D9383A; }}
  .kpi-val {{
    font-size: 27px;
    font-weight: 800;
    color: #001965;
    line-height: 1.15;
    margin-bottom: 4px;
  }}
  .kpi-card.teal .kpi-val {{ color: #00857C; }}
  .kpi-card.red  .kpi-val {{ color: #D9383A; }}
  .kpi-lbl {{
    font-size: 13px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 3px;
  }}
  .kpi-sub {{
    font-size: 11.5px;
    color: #5A6070;
  }}

  /* Left Column: 2-Panel Plot Image */
  .plot-box {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 365px;
    flex-shrink: 0;
  }}
  .plot-box img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
  }}

  /* Left Column: Bottom 3 Evidence Rows */
  .ev-box {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-left: 8px solid #00857C;
    padding: 12px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 9px;
    flex-shrink: 0;
  }}
  .ev-row {{
    font-size: 13.3px;
    line-height: 1.37;
    color: #1A1A2E;
  }}
  .ev-row strong.teal {{ color: #00857C; font-size: 13.8px; }}
  .ev-row strong.navy {{ color: #001965; font-size: 13.8px; }}

  /* Right Column Stack */
  .right-col {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 20px;
    min-height: 0;
  }}

  /* 4-Step Funnel */
  .steps-row {{
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    gap: 6px;
  }}
  .step-card {{
    flex: 1;
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    display: flex;
    flex-direction: column;
  }}
  .step-hdr {{
    height: 36px;
    background: #001965;
    color: #FFFFFF;
    font-size: 13.2px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .step-hdr.teal {{ background: #00857C; }}
  .step-hdr.red  {{ background: #D9383A; }}
  .step-sub {{
    font-size: 13.2px;
    font-weight: 700;
    color: #001965;
    text-align: center;
    padding: 7px 6px 4px 6px;
  }}
  .step-sub.teal {{ color: #00857C; }}
  .step-sub.red  {{ color: #D9383A; }}
  .step-body {{
    font-size: 12.0px;
    line-height: 1.35;
    color: #1A1A2E;
    padding: 4px 10px 10px 10px;
  }}
  .chevron {{
    display: flex;
    align-items: center;
    justify-content: center;
    color: #00857C;
    font-size: 22px;
    font-weight: 900;
    padding: 0 1px;
  }}

  /* Three Orthogonal Layers Callout */
  .layer-strip {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-left: 8px solid #001965;
    padding: 11px 16px;
    font-size: 13.3px;
    line-height: 1.37;
    margin-top: 12px;
  }}
  .layer-strip strong {{ color: #001965; font-size: 13.8px; }}

  /* Bottom Right Matrix + 2 Cards */
  .matrix-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 10px;
  }}
  .mat-box {{
    border: 1.5px solid #00857C;
    background: #EBF7F5;
    display: flex;
    flex-direction: column;
  }}
  .mat-box.red {{
    border-color: #D9383A;
    background: #FDF2F2;
  }}
  .mat-hdr {{
    height: 32px;
    background: #00857C;
    color: #FFFFFF;
    font-size: 12.5px;
    font-weight: 700;
    padding: 0 12px;
    display: flex;
    align-items: center;
    letter-spacing: 0.3px;
  }}
  .mat-box.red .mat-hdr {{
    background: #D9383A;
  }}
  .mat-body {{
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 12.2px;
    line-height: 1.34;
  }}
  .mat-body strong.teal {{ color: #00857C; }}
  .mat-body strong.red  {{ color: #D9383A; }}

  .pos-stack {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 10px;
    flex: 1;
  }}
  .pos-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-left: 8px solid #001965;
    padding: 10px 16px;
    font-size: 13.1px;
    line-height: 1.35;
    display: flex;
    align-items: center;
    flex: 1;
  }}
  .pos-card.teal {{ border-left-color: #00857C; }}
  .pos-card strong.navy {{ color: #001965; font-size: 13.6px; }}
  .pos-card strong.teal {{ color: #00857C; font-size: 13.6px; }}

  /* Footer */
  .footer {{
    height: 40px;
    padding: 0 64px 10px 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12.2px;
    color: #5A6070;
    flex-shrink: 0;
  }}
</style>
</head>
<body>
<div class="slide">
  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <h1>Proteome-Wide Binding Partner &amp; Disease-Interface Triage</h1>
      <div class="sub">
        <strong>Pre-Screening Target Complexes Before Wet-Lab Assays</strong> &nbsp;|&nbsp;
        <em>Zhang et al., Science 2025 + Pei et al., Sci Rep 2026</em>
      </div>
    </div>
    <div class="header-right">
      <div class="badge">PROPOSAL &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">2026-10-28 &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <!-- Main Workspace -->
  <div class="main">
    <!-- Left Column: Section 1 -->
    <div class="panel">
      <div class="panel-hdr hdr-teal">1. Why It Matters &amp; In-House Validation (33,000 Benchmark Pairs)</div>
      <div class="panel-body">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-val">262x</div>
            <div class="kpi-lbl">vs Random Screening</div>
            <div class="kpi-sub">AUC 0.262 vs 0.001 (1:1000)</div>
          </div>
          <div class="kpi-card teal">
            <div class="kpi-val">43.2%</div>
            <div class="kpi-lbl">Large-Complex Recall</div>
            <div class="kpi-sub">At &ge;90% precision (51.8% @0.5)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val">0.919</div>
            <div class="kpi-lbl">Author Score Parity</div>
            <div class="kpi-sub">Pearson r across 8,977 pairs</div>
          </div>
          <div class="kpi-card red">
            <div class="kpi-val">~6 hrs</div>
            <div class="kpi-lbl">Per Target Screen</div>
            <div class="kpi-sub">1 bait vs 20,260 human proteins</div>
          </div>
        </div>

        <div class="plot-box">
          <img src="data:image/png;base64,{b64_img}" alt="PR Curve and Biological Interface Sensitivity">
        </div>

        <div class="ev-box">
          <div class="ev-row">
            <strong class="teal">Biological Bottleneck (FACT):</strong>
            Affinity purification (AP-MS / co-IP) often misses low-abundance or membrane complexes. Zhang et al. (<em>Science</em> 2025) identified <strong>17,849 high-precision human PPIs</strong> (3,631 novel) with <strong>29,246 3D structures</strong>.
          </div>
          <div class="ev-row">
            <strong class="navy">Why Recall is 20.8% Overall (MECH):</strong>
            At realistic 1:1000 proteome odds, sensitivity depends on contact area: <strong>43.2% recall on large stable complexes (&gt;1500 &Aring;&sup2;)</strong> vs 4.5% on small transient motifs (&lt;800 &Aring;&sup2;). Balanced 1:1 AUC = <strong>0.813</strong>.
          </div>
          <div class="ev-row">
            <strong class="navy">Human Genetics Proof-of-Concept (OBS):</strong>
            On Calcium-Sensing Receptor (<strong>CASR</strong>), our module mapped <strong>89 clinical pathogenic mutations</strong> (HHC1/HYPOC1); <strong>64% cluster directly at the ECD dimerization interface (&le;612)</strong>, confirming biological validity.
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column: Section 2 & Section 3 -->
    <div class="right-col">
      <!-- Top-Right: Funnel -->
      <div class="panel panel-blue">
        <div class="panel-hdr hdr-navy">2. From Target of Interest to Wet-Lab Assay Design (~6 Hours / Target)</div>
        <div class="panel-body" style="padding: 14px 18px;">
          <div class="steps-row">
            <div class="step-card">
              <div class="step-hdr">Step 1: Target Input</div>
              <div class="step-sub">1 Bait Protein</div>
              <div class="step-body">Provide any target UniProt ID; screened against 20,260 human proteins with deep evolutionary alignments</div>
            </div>
            <div class="chevron">&#10095;</div>
            <div class="step-card">
              <div class="step-hdr">Step 2: Partner Screen</div>
              <div class="step-sub">Binding Probability</div>
              <div class="step-body">Rapid coevolutionary &amp; structural scoring (~6h on 6 GPUs); calibrated against our local 90% precision cutoff</div>
            </div>
            <div class="chevron">&#10095;</div>
            <div class="step-card">
              <div class="step-hdr teal">Step 3: 3D &amp; Genetics</div>
              <div class="step-sub teal">Interface Mapping</div>
              <div class="step-body">3D complex model (6&Aring; contact residues) + clinical disease-mutation enrichment (ClinVar / UniProt / AlphaMissense)</div>
            </div>
            <div class="chevron">&#10095;</div>
            <div class="step-card">
              <div class="step-hdr red">Step 4: Assay Design</div>
              <div class="step-sub red">Wet-Lab Handoff</div>
              <div class="step-body">Top-N partner list + exact interface point-mutations to design negative controls for co-IP / BioID / BRET</div>
            </div>
          </div>
          <div class="layer-strip">
            <strong>What Biology Teams Receive per Candidate:</strong>
            (1) Calibrated binding confidence, (2) 3D complex structure with pocket/interface coordinates, and (3) Human genetic disease variants at the contact surface &mdash; directly guiding mutational validation.
          </div>
        </div>
      </div>

      <!-- Bottom-Right: Biological Fit Matrix + Immediate Pilot -->
      <div class="panel" style="flex: 1;">
        <div class="panel-hdr hdr-red">3. Biological Fit Matrix, Golden Rule &amp; Cardiometabolic Pilot</div>
        <div class="panel-body" style="padding: 14px 18px;">
          <div class="matrix-grid">
            <div class="mat-box">
              <div class="mat-hdr">IDEAL TARGETS (HIGH SENSITIVITY)</div>
              <div class="mat-body">
                <div>&bull; <strong class="teal">Obligate &amp; constitutive complexes</strong> (43.2% recall on interfaces &gt;1500 &Aring;&sup2;)</div>
                <div>&bull; <strong class="teal">Transmembrane &amp; organelle complexes</strong> hard to solubilize in standard AP-MS</div>
                <div>&bull; <strong class="teal">Endogenous receptor / enzyme complexes</strong> &amp; genetic disease-linked interfaces</div>
              </div>
            </div>
            <div class="mat-box red">
              <div class="mat-hdr">BLIND SPOTS (DO NOT EXCLUDE)</div>
              <div class="mat-body">
                <div>&bull; <strong class="red">Transient / PTM-triggered signaling</strong> (e.g., GPCR-arrestin, kinase-substrate)</div>
                <div>&bull; <strong class="red">Disordered short linear motifs (SLiMs)</strong> (4.5% recall on interfaces &lt;800 &Aring;&sup2;)</div>
                <div>&bull; <strong class="red">Immune receptors (TCR/BCR/MHC)</strong> &amp; fast-evolving / lineage-specific pairs</div>
              </div>
            </div>
          </div>
          <div class="pos-stack">
            <div class="pos-card teal">
              <div><strong class="teal">Golden Rule &amp; External Validation:</strong> Use strictly as a <strong>POSITIVE hypothesis generator</strong> (never discard a biological candidate due to a low score). Confirmed by Lambourne et al. (<em>Nat Commun</em> 2026) and Kutay lab TMEM209-Nup210 co-IP (<em>J Cell Sci</em> 2026).</div>
            </div>
            <div class="pos-card">
              <div><strong class="navy">Immediate Pilot &mdash; 99 Cardiometabolic Novel PPI Leads (Data S6):</strong> Prioritize our <strong>99 unflagged novel PPI leads across 5 indications</strong> (Obesity, T2D, CKD, MASH, CVD; Tier A/B/C targets) by integrating local PR precision, GTEx co-expression, and interface pathogenic SAV burden &rarr; nominate <strong>Top-10 for co-IP</strong>.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) &nbsp;|&nbsp; Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) &nbsp;|&nbsp; Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>Pipeline: <code>druggability</code> repo &nbsp;|&nbsp; Tracker: Jira <strong>RIC-410</strong></div>
  </div>
</div>
</body>
</html>
"""

OUT_HTML.write_text(html, encoding="utf-8")
print("Wrote HTML:", OUT_HTML)


async def render(scale: int, out: Path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=scale,
        )
        page = await ctx.new_page()
        await page.goto(f"file://{OUT_HTML}", wait_until="networkidle")
        await page.wait_for_timeout(400)
        await page.screenshot(path=str(out), full_page=False, omit_background=False)
        await browser.close()
    print(f"Rendered {scale}x PNG: {out} ({out.stat().st_size:,} bytes)")


async def main():
    await render(1, OUT_1X)
    await render(2, OUT_2X)
    await render(3, OUT_3X)


asyncio.run(main())
