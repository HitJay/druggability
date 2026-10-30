#!/usr/bin/env python
"""Generate self-contained 1920x1080 HTML one-pager (Group Meeting Edition) and render @1x/@2x/@3x PNG via Playwright."""
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
<title>Proteome-Wide PPI &amp; Disease-Interface Triage: Baker Achievement &amp; Campaign Business Questions</title>
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
    height: 136px;
    background: #001965;
    padding: 18px 64px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }}
  .header-left h1 {{
    font-size: 28.5px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.3px;
    margin-bottom: 8px;
  }}
  .header-left .sub {{
    font-size: 16px;
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
    flex-shrink: 0;
  }}
  .header-right .badge {{
    display: inline-block;
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 5px 14px;
    border-radius: 4px;
    font-size: 15px;
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
    padding: 20px 64px 12px 64px;
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
    height: 48px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.1px;
    flex-shrink: 0;
  }}
  .hdr-teal {{ background: #00857C; }}
  .hdr-navy {{ background: #001965; }}
  .hdr-red  {{ background: #D9383A; }}

  .panel-body {{
    padding: 14px 18px;
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
    gap: 12px;
    flex-shrink: 0;
  }}
  .kpi-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-top: 6px solid #001965;
    padding: 9px 6px 8px 6px;
    text-align: center;
  }}
  .kpi-card.teal {{ border-top-color: #00857C; }}
  .kpi-card.red  {{ border-top-color: #D9383A; }}
  .kpi-val {{
    font-size: 23px;
    font-weight: 800;
    color: #001965;
    line-height: 1.18;
    margin-bottom: 4px;
  }}
  .kpi-card.teal .kpi-val {{ color: #00857C; }}
  .kpi-card.red  .kpi-val {{ color: #D9383A; }}
  .kpi-lbl {{
    font-size: 12.8px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 2px;
  }}
  .kpi-sub {{
    font-size: 11.2px;
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
    height: 358px;
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
    padding: 11px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
    flex-shrink: 0;
  }}
  .ev-row {{
    font-size: 13.0px;
    line-height: 1.35;
    color: #1A1A2E;
  }}
  .ev-row strong.teal {{ color: #00857C; font-size: 13.4px; }}
  .ev-row strong.navy {{ color: #001965; font-size: 13.4px; }}

  /* Right Column Stack */
  .right-col {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 16px;
    min-height: 0;
  }}

  /* 3 Business Question Cards */
  .bq-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }}
  .bq-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    display: flex;
    flex-direction: column;
  }}
  .bq-hdr {{
    height: 34px;
    background: #001965;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .bq-hdr.teal {{ background: #00857C; }}
  .bq-hdr.red  {{ background: #D9383A; }}
  .bq-sub {{
    font-size: 12.4px;
    font-weight: 700;
    color: #001965;
    text-align: center;
    padding: 6px 8px 3px 8px;
  }}
  .bq-sub.teal {{ color: #00857C; }}
  .bq-sub.red  {{ color: #D9383A; }}
  .bq-body {{
    font-size: 11.9px;
    line-height: 1.34;
    color: #1A1A2E;
    padding: 4px 10px 10px 10px;
  }}

  /* Handoff Callout */
  .layer-strip {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-left: 8px solid #001965;
    padding: 10px 15px;
    font-size: 12.9px;
    line-height: 1.35;
    margin-top: 10px;
  }}
  .layer-strip strong {{ color: #001965; font-size: 13.4px; }}

  /* Bottom Right Matrix + 2 Cards */
  .matrix-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 9px;
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
    height: 30px;
    background: #00857C;
    color: #FFFFFF;
    font-size: 12.2px;
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
    padding: 7px 11px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 11.9px;
    line-height: 1.32;
  }}
  .mat-body strong.teal {{ color: #00857C; }}
  .mat-body strong.red  {{ color: #D9383A; }}

  .pos-stack {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
    flex: 1;
  }}
  .pos-card {{
    background: #FFFFFF;
    border: 1px solid #D0D7E5;
    border-left: 8px solid #001965;
    padding: 8px 14px;
    font-size: 12.6px;
    line-height: 1.33;
    display: flex;
    align-items: center;
    flex: 1;
  }}
  .pos-card.teal {{ border-left-color: #00857C; }}
  .pos-card strong.navy {{ color: #001965; font-size: 13.1px; }}
  .pos-card strong.teal {{ color: #00857C; font-size: 13.1px; }}

  /* Footer */
  .footer {{
    height: 38px;
    padding: 0 64px 8px 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
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
      <h1>Proteome-Wide PPI &amp; Disease-Interface Triage: Baker Achievement &amp; Campaign Business Questions</h1>
      <div class="sub">
        <strong>What Baker &amp; Cong&rsquo;s Team Achieved + What Business Question Our Campaign Solves</strong> &nbsp;|&nbsp;
        <em>Zhang et al., Science 2025 + Pei et al., Sci Rep 2026</em>
      </div>
    </div>
    <div class="header-right">
      <div class="badge">GROUP MEETING &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">2026-10-29 &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <!-- Main Workspace -->
  <div class="main">
    <!-- Left Column: Section 1 -->
    <div class="panel">
      <div class="panel-hdr hdr-teal">1. What Baker &amp; Cong&rsquo;s Team Achieved (Science 2025) &amp; In-House Reproduction</div>
      <div class="panel-body">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-val">200M&rarr;17.8k</div>
            <div class="kpi-lbl">Baker Interactome</div>
            <div class="kpi-sub">3,631 novel @90% prec (2,700 S6)</div>
          </div>
          <div class="kpi-card teal">
            <div class="kpi-val">262x</div>
            <div class="kpi-lbl">In-House Enrichment</div>
            <div class="kpi-sub">AUCPR 0.262 vs 0.001 (1:1000)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val">43.2%</div>
            <div class="kpi-lbl">Large-Complex Recall</div>
            <div class="kpi-sub">Interfaces &gt;1500 &Aring;&sup2; (r=0.919)</div>
          </div>
          <div class="kpi-card red">
            <div class="kpi-val">~6 hrs</div>
            <div class="kpi-lbl">Per-Target Screen</div>
            <div class="kpi-sub">1 bait vs 20,260 human proteins</div>
          </div>
        </div>

        <div class="plot-box">
          <img src="data:image/png;base64,{b64_img}" alt="PR Curve and Biological Interface Sensitivity">
        </div>

        <div class="ev-box">
          <div class="ev-row">
            <strong class="teal">2025 Science vs 2026 Sci Rep Division (FACT):</strong>
            <strong>2025</strong> built the engine (7x omicMSAs, 17x AFDB DDI training &rarr; RF2-PPI; 191M&rarr;111.2M&rarr;43.6M&rarr;1.9M funnel; <strong>17,849 PPIs @90% prec</strong> [de novo + prior-guided], 3,631 novel, 2,700 Data S6 lacking complex templates, 1,413 uncharacterized). <strong>2026</strong> added no new screen; it mined 2025 models for disease SAVs &amp; AF3 assemblies.
          </div>
          <div class="ev-row">
            <strong class="navy">Why Recall is 20.8% Overall &amp; Where It Excels (MECH):</strong>
            At realistic 1:1000 proteome odds (balanced 1:1 AUC=0.813), recall is <strong>43.2% on large stable complexes (&gt;1500 &Aring;&sup2;)</strong> vs 4.5% on small transient SLiMs (&lt;800 &Aring;&sup2;). Over half of 2,700 Data S6 novel PPIs (<strong>1,556; 58%</strong>) are <strong>transmembrane complexes</strong> missed by AP-MS.
          </div>
          <div class="ev-row">
            <strong class="navy">Prospective Audit &amp; Variant Interpretation Caveat (OBS):</strong>
            <strong>11 Data S6 pairs</strong> (cutoff Sep 2023) are now proved by cryo-EM/co-IP (<em>DND1-NANOS3</em>, <em>DHX35-GPATCH1</em>, <em>TMEM209-NUP210</em>). On <strong>CASR</strong>, <strong>64% of 89 pathogenic SAVs</strong> map to the ECD dimer interface (<em>note: interface SAVs propose testable disruption hypotheses, not proof of loss-of-binding</em>).
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column: Section 2 & Section 3 -->
    <div class="right-col">
      <!-- Top-Right: 3 Business Questions -->
      <div class="panel panel-blue">
        <div class="panel-hdr hdr-navy">2. Campaign Business Question Menu (3 Candidate Questions for Alignment)</div>
        <div class="panel-body" style="padding: 12px 16px;">
          <div class="bq-row">
            <div class="bq-card">
              <div class="bq-hdr">BQ-1: Portfolio Partner Mining</div>
              <div class="bq-sub">99 Leads &rarr; 8 Pass All 4/4</div>
              <div class="bq-body">Strict 4-Criteria Triage on 99 Data S6 cardiometabolic leads (C1 Both-Genetics 60 [46 Human], C2 Pathway 43, C3 Direct Perturb. 14, C4 CM Co-expr 56) &rarr; <strong>8 pass all 4/4</strong> (<strong>#1 RAMP3&ndash;MRAP2</strong>, <strong>#2 RAMP1&ndash;MRAP2</strong>).</div>
            </div>
            <div class="bq-card">
              <div class="bq-hdr teal">BQ-2: De Novo Target Screen</div>
              <div class="bq-sub teal">1 Bait vs 20,260 Human Proteins</div>
              <div class="bq-body">For an internal priority receptor or enzyme (especially <strong>transmembrane or organelle targets</strong> where detergent AP-MS fails), what is its missing endogenous co-receptor, trafficking chaperone, or E3 ligase (<strong>~6 GPU-h/target</strong>)?</div>
            </div>
            <div class="bq-card">
              <div class="bq-hdr red">BQ-3: Disease-Interface Assay</div>
              <div class="bq-sub red">3D Pocket &amp; Disruptor Mutants</div>
              <div class="bq-body">Given a target complex or human genetics signal, where is the exact <strong>6&Aring; contact surface</strong> and which clinical pathogenic variants (ClinVar / AlphaMissense) sit at the interface to design <strong>point-mutant negative controls</strong>?</div>
            </div>
          </div>
          <div class="layer-strip">
            <strong>End-to-End Handoff to Wet-Lab (~6 GPU-h / Target):</strong>
            (1) Calibrated partner probability (@90% precision cutoff), (2) 3D complex coordinates (6&Aring; contact residues), and (3) Interface pathogenic variants (Pei et al. 2026) &rarr; exact point-mutant negative controls for co-IP / BioID / BRET.
          </div>
        </div>
      </div>

      <!-- Bottom-Right: Biological Fit Matrix + Immediate Pilot -->
      <div class="panel" style="flex: 1;">
        <div class="panel-hdr hdr-red">3. Biological Fit Matrix, Golden Rule &amp; Proposed Pilot Decision</div>
        <div class="panel-body" style="padding: 12px 16px;">
          <div class="matrix-grid">
            <div class="mat-box">
              <div class="mat-hdr">IDEAL TARGETS (HIGH SENSITIVITY)</div>
              <div class="mat-body">
                <div>&bull; <strong class="teal">Obligate &amp; constitutive complexes</strong> (43.2% recall on interfaces &gt;1500 &Aring;&sup2;)</div>
                <div>&bull; <strong class="teal">Transmembrane &amp; organelle complexes</strong> (58% of Data S6; missed by detergent AP-MS)</div>
                <div>&bull; <strong class="teal">Co-receptors, chaperones &amp; enzymes</strong> with human genetic variants at interface</div>
              </div>
            </div>
            <div class="mat-box red">
              <div class="mat-hdr">BLIND SPOTS (DO NOT EXCLUDE)</div>
              <div class="mat-body">
                <div>&bull; <strong class="red">Transient / PTM-triggered signaling</strong> (e.g., GPCR-arrestin, kinase-substrate)</div>
                <div>&bull; <strong class="red">Disordered short linear motifs (SLiMs)</strong> (4.5% recall on interfaces &lt;800 &Aring;&sup2;)</div>
                <div>&bull; <strong class="red">Immune receptors (TCR/BCR/MHC)</strong> &amp; lineage-specific / paralog swaps</div>
              </div>
            </div>
          </div>
          <div class="pos-stack">
            <div class="pos-card teal">
              <div><strong class="teal">Golden Rule for Campaign Governance:</strong> Use strictly as a <strong>POSITIVE hypothesis generator &amp; 3D assay design tool</strong> &mdash; never discard a biologically supported candidate due to a low score (confirmed by Lambourne et al., <em>Nat Commun</em> 2026).</div>
            </div>
            <div class="pos-card">
              <div><strong class="navy">Phase-1 Pilot Executed (BQ-1 4-Criteria Triage + Docking / MD / FEP):</strong> <strong>8/99 cardiometabolic leads pass all 4 strict criteria</strong> (6 with human GWAS/ClinVar on both proteins: <em>RAMP3&ndash;MRAP2</em> #1, <em>RAMP1&ndash;MRAP2</em> #2, <em>NR3C1&ndash;FOXO3</em> #3). #1 <strong>RAMP3&ndash;MRAP2</strong> verified by Boltz-2 (ipTM=0.868), MD (0.49&Aring;) &amp; FEP.</div>
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
