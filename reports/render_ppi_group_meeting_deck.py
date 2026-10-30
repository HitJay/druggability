#!/usr/bin/env python
"""Render the 6-slide group meeting presentation (HTML -> PDF + @2x PNG per slide) via Playwright."""
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
<title>Proteome-Wide PPI &amp; Disease-Interface Triage — Group Meeting Deck (RIC-410)</title>
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
    font-size: 29px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 7px;
  }}
  .hdr-l .sub {{
    font-size: 16px;
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
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 6px;
  }}
  .hdr-r .meta {{
    font-size: 14px;
    color: #E8EEF7;
  }}

  .body-area {{
    flex: 1;
    padding: 22px 68px 14px 68px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 0;
  }}

  .ftr {{
    height: 42px;
    padding: 0 68px 10px 68px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12.5px;
    color: #5A6070;
    border-top: 1px solid #D0D7E5;
    margin: 0 68px;
    padding-left: 0;
    padding-right: 0;
    flex-shrink: 0;
  }}

  /* Reusable components */
  .banner {{
    background: #F2F4F8;
    border: 1.5px solid #D0D7E5;
    border-left: 10px solid #D9383A;
    padding: 14px 22px;
    font-size: 15px;
    line-height: 1.45;
  }}
  .banner.navy {{ background: #E8EEF7; border-color: #001965; border-left-color: #001965; }}
  .banner.teal {{ background: #EBF7F5; border-color: #00857C; border-left-color: #00857C; }}

  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 28px;
  }}
  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
  }}
  .card {{
    background: #FFFFFF;
    border: 1.5px solid #D0D7E5;
    display: flex;
    flex-direction: column;
  }}
  .card-hdr {{
    height: 48px;
    background: #001965;
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 700;
    padding: 0 20px;
    display: flex;
    align-items: center;
  }}
  .card-hdr.teal {{ background: #00857C; }}
  .card-hdr.red  {{ background: #D9383A; }}
  .card-sub {{
    height: 40px;
    background: #E8EEF7;
    color: #001965;
    font-size: 15px;
    font-weight: 700;
    padding: 0 20px;
    display: flex;
    align-items: center;
  }}
  .card-sub.teal {{ color: #00857C; }}
  .card-sub.red  {{ color: #D9383A; }}
  .card-body {{
    padding: 18px 22px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    font-size: 14.5px;
    line-height: 1.42;
    flex: 1;
  }}

  table.std-tbl {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
  }}
  table.std-tbl th {{
    background: #001965;
    color: #FFFFFF;
    font-weight: 700;
    text-align: left;
    padding: 9px 12px;
    border: 1px solid #D0D7E5;
  }}
  table.std-tbl td {{
    padding: 8px 12px;
    border: 1px solid #D0D7E5;
    color: #1A1A2E;
    line-height: 1.32;
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

<!-- ==================== SLIDE 1: TITLE & EXEC SUMMARY ==================== -->
<div class="slide navy-bg" id="slide-1">
  <div style="height: 16px; background: #00857C; width: 100%;"></div>
  <div style="padding: 54px 92px; flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
    <div>
      <div style="display: inline-block; background: #00857C; color: #FFFFFF; font-weight: 700; font-size: 15px; padding: 8px 20px; letter-spacing: 0.5px; margin-bottom: 24px;">
        GROUP MEETING BRIEFING (5&ndash;10 MIN) &nbsp;|&nbsp; RIC-410
      </div>
      <h1 style="font-size: 46px; font-weight: 800; color: #FFFFFF; margin-bottom: 14px; letter-spacing: -0.5px;">
        Proteome-Wide PPI &amp; Disease-Interface Triage
      </h1>
      <div style="font-size: 23px; font-weight: 700; color: #E8EEF7; margin-bottom: 20px;">
        1. What David Baker &amp; Qian Cong&rsquo;s Team Achieved &nbsp;&nbsp;|&nbsp;&nbsp; 2. What Business Question Our Campaign Solves
      </div>
      <div style="font-size: 16.5px; color: #CADCFC;">
        Presenter: Qiuye Jin (QYJI) &nbsp;&nbsp;|&nbsp;&nbsp; Cardiometabolic Data S6 Partner: Zheng Cao (ZHCO) &nbsp;&nbsp;|&nbsp;&nbsp; October 2026
      </div>
    </div>

    <!-- Two Main Summary Cards -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 36px; my: 20px;">
      <div style="background: #FFFFFF; border: 2px solid #00857C; color: #1A1A2E; display: flex; flex-direction: column;">
        <div style="background: #00857C; color: #FFFFFF; font-size: 18.5px; font-weight: 700; padding: 14px 24px;">
          PART 1: What David Baker &amp; Qian Cong&rsquo;s Team Achieved (Slides 2&ndash;4)
        </div>
        <div style="padding: 22px 26px; display: flex; flex-direction: column; gap: 15px; font-size: 15.2px; line-height: 1.42;">
          <div>
            <strong style="color: #001965; font-size: 16px;">&bull; Solved the Human Interactome Scale &amp; Signal Bottleneck (Science 2025):</strong><br>
            Assembled <strong>7x deeper omicMSAs</strong> from 30 PB raw eukaryotic reads + distilled <strong>223k AFDB domain-domain pairs</strong> (17x larger training set) to train <strong>RF2-PPI</strong> (20x faster than AF2).
          </div>
          <div>
            <strong style="color: #001965; font-size: 16px;">&bull; Mapped 17,849 High-Precision Human PPIs (@90% Precision):</strong><br>
            Includes 3,631 novel interactions (<strong>2,700 zero-prior-evidence in Data S6; 58% transmembrane</strong>) + ~16,000 clinical disease mutations mapped to 3D interfaces (<em>Sci Rep</em> 2026).
          </div>
          <div>
            <strong style="color: #00857C; font-size: 16px;">&bull; Verified In-House on 6x A100 GPUs &amp; Prospectively Validated:</strong><br>
            <strong>262x enrichment</strong> over random proteome screening (r=0.919 parity; <strong>43.2% recall on large stable complexes &gt;1500 &Aring;&sup2;</strong>; <strong>11 Data S6 pairs proved by cryo-EM/co-IP</strong> in 2024&ndash;2026).
          </div>
        </div>
      </div>

      <div style="background: #FFFFFF; border: 2px solid #D9383A; color: #1A1A2E; display: flex; flex-direction: column;">
        <div style="background: #D9383A; color: #FFFFFF; font-size: 18.5px; font-weight: 700; padding: 14px 24px;">
          PART 2: Campaign Business Questions for Alignment (Slides 5&ndash;6)
        </div>
        <div style="padding: 22px 26px; display: flex; flex-direction: column; gap: 15px; font-size: 15.2px; line-height: 1.42;">
          <div>
            <strong style="color: #001965; font-size: 16px;">&bull; BQ-1 (Portfolio Partner Mining &mdash; Ready Now):</strong><br>
            Triage the <strong>99 unflagged novel PPI leads</strong> across 120 cardiometabolic targets in Data S6 (18 Tier A + 8 NN pipeline incl. <em>RAMP1/2/3, CASR, TTR</em>) &rarr; nominate <strong>Top-10 for co-IP</strong>.
          </div>
          <div>
            <strong style="color: #00857C; font-size: 16px;">&bull; BQ-2 (De Novo Target Screen &mdash; On-Demand Service):</strong><br>
            Screen any priority internal receptor/transporter bait against all <strong>20,260 human proteins in ~6 GPU-h</strong> to find missing co-receptors, chaperones, or E3 ligases missed by AP-MS.
          </div>
          <div>
            <strong style="color: #D9383A; font-size: 16px;">&bull; BQ-3 (Disease-Interface &amp; Assay Control Design):</strong><br>
            Deliver 3D complex coordinates (<strong>6&Aring; contact surface</strong>) + clinical pathogenic variants (ClinVar / AlphaMissense) to design exact <strong>point-mutant negative controls</strong> for co-IP/BRET.
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Goal Strip -->
    <div style="background: #E8EEF7; padding: 18px 28px; color: #001965; font-size: 16.5px; font-weight: 700;">
      <span style="color: #D9383A;">Goal of Today&rsquo;s 5&ndash;10 Min Discussion:</span> Review the technical capability and boundaries (Part 1), and decide which Business Question(s) and pilot targets to prioritize for Phase-1 wet-lab handoff (Part 2).
    </div>
  </div>
</div>

<!-- ==================== SLIDE 2: PART 1A — BAKER ACHIEVEMENT ==================== -->
<div class="slide" id="slide-2">
  <div class="hdr">
    <div class="hdr-l">
      <h1>What Baker &amp; Cong&rsquo;s Team Achieved: 2025 Science vs 2026 Sci Rep &amp; Critical Caveats</h1>
      <div class="sub"><strong>PART 1A: TWO-STUDY SYNTHESIS &amp; SCIENTIFIC CAVEATS</strong> &nbsp;|&nbsp; <em>Synthesizing the 5-Stage Proteome Engine (2025), Mechanistic Case Extension (2026), and Rigorous Reading Rules</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 2 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Group Meeting &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div class="banner navy">
      <div style="color: #001965; font-weight: 700; font-size: 15.8px; margin-bottom: 4px;">How the Two Publications Connect (Figure 1&ndash;3 Synthesis):</div>
      <div><strong>&bull; 1st Study (Zhang et al., <em>Science</em> 2025):</strong> Built the computational engine (<code>omicMSAs</code> + <code>RF2-PPI</code>) and screened the human proteome (19,528 proteins &rarr; 17,849 PPIs @90% prec).<br>
      <strong>&bull; 2nd Study (Pei, Zhang &amp; Cong, <em>Sci Rep</em> 2026):</strong> Did <strong>NOT</strong> retrain a model or run a new proteome screen; used the 2025 resource as input for curated case studies (interface disease variants &amp; AlphaFold3 multi-subunit complexes).</div>
    </div>

    <div class="grid-3" style="flex: 1; margin: 16px 0;">
      <div class="card">
        <div class="card-hdr">1st Study: 2025 Science</div>
        <div class="card-sub">Proteome-Scale Engine &amp; Resource</div>
        <div class="card-body" style="gap: 11px; font-size: 13.8px;">
          <div><strong style="color:#001965;">&bull; Stage 1&ndash;2: 7x omicMSAs + RF2-PPI:</strong><br>Assembled <strong>21,415 eukaryotic species</strong> from 30 PB raw reads (7x deeper MSAs). Distilled <strong>223,440 AFDB domain-domain contacts</strong> (17x larger training set) + negative pairs &rarr; RF2-PPI (20x faster than AF2).</div>
          <div><strong style="color:#001965;">&bull; Stage 3&ndash;4: 4-Tier Cascade Funnel:</strong><br>20,296 proteins (19,528 screened; ~191M pairs) &rarr; Localization filter (<strong>111.2M</strong>) &rarr; DCA coevolution (<strong>43.6M</strong>) &rarr; RF2-PPI (<strong>~1.9M</strong>) &rarr; AF2 3D modeling.</div>
          <div><strong style="color:#001965;">&bull; Stage 5: Primary Resource Numbers:</strong><br><strong>29,256 PPIs (@80% prec) &amp; 17,849 (@90% prec)</strong>: 3,631 novel, 2,700 lacking complex templates (Data S6; 58% TM), <strong>1,413 with uncharacterized proteins</strong>, 4,950 with interface SAVs, 404 complexes (+139 new subunits).</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr teal">2nd Study: 2026 Sci Rep</div>
        <div class="card-sub teal">Curated Case Studies &amp; AF3 Assemblies</div>
        <div class="card-body" style="gap: 11px; font-size: 13.8px;">
          <div><strong style="color:#00857C;">&bull; Pathway Crosstalk &amp; Dark Proteins:</strong><br>1) <em>PMS1&ndash;FAAP24</em>: links DNA mismatch repair (MMR) to Fanconi anemia ICL repair.<br>2) <em>C12orf57&ndash;ANKRD50</em>: links dark protein C12orf57 to SNX27-retromer endocytic recycling.</div>
          <div><strong style="color:#00857C;">&bull; Interface Disease Variant Cases:</strong><br>1) <em>C12orf57 L51Q</em>: buried at ANKRD50 interface (Temtamy syndrome).<br>2) <em>BBS7&ndash;WDR19 (V80D)</em>: disrupts BBSome&ndash;IFT-A ciliary contact in Senior&ndash;L&oslash;ken ciliopathy.<br>3) <em>SCO1 (P174L) &ndash; COA6 (W59C)</em>: co-localizes across interface in complex IV deficiency.</div>
          <div><strong style="color:#00857C;">&bull; Higher-Order AF3 Complex Modeling:</strong><br>Superimposed binary models + AlphaFold3: identified <em>C19orf25</em> as a new NRZ tethering subunit, and modeled BLOC-1 / BORC / Sarcoglycan assemblies.</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr red">4 Rigorous Reading Rules</div>
        <div class="card-sub red">Critical Scientific Caveats (Do Not Overclaim)</div>
        <div class="card-body" style="gap: 10px; font-size: 13.5px;">
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
    <div>druggability repo &nbsp;|&nbsp; Page 2/6</div>
  </div>
</div>

<!-- ==================== SLIDE 3: PART 1B — IN-HOUSE VALIDATION ==================== -->
<div class="slide" id="slide-3">
  <div class="hdr">
    <div class="hdr-l">
      <h1>In-House Benchmark Reproduction &amp; Physical Sensitivity Mechanism</h1>
      <div class="sub"><strong>PART 1B: IN-HOUSE VALIDATION &amp; MECHANISM</strong> &nbsp;|&nbsp; <em>Verified on 33,000 Benchmark Pairs (6x A100 GPUs): Why Recall is 43.2% on Large Complexes vs 4.5% on Small Motifs</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 3 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Group Meeting &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div class="grid-4">
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:7px solid #001965; padding:12px 14px; text-align:center;">
        <div style="font-size:25px; font-weight:800; color:#001965;">262x Enrichment</div>
        <div style="font-size:14px; font-weight:700; margin:4px 0 2px;">Weighted AUCPR 0.262 vs 0.001</div>
        <div style="font-size:12px; color:#5A6070;">At realistic 1:1,000 proteome S/N prior (1:1 balanced AUC = 0.813)</div>
      </div>
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:7px solid #00857C; padding:12px 14px; text-align:center;">
        <div style="font-size:25px; font-weight:800; color:#00857C;">r = 0.919 Parity</div>
        <div style="font-size:14px; font-weight:700; margin:4px 0 2px;">8,977 Shared Benchmark Pairs</div>
        <div style="font-size:12px; color:#5A6070;">Pearson r=0.919 (Spearman 0.901); 623 TPs &amp; 0 FPs at &ge;90% precision</div>
      </div>
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:7px solid #001965; padding:12px 14px; text-align:center;">
        <div style="font-size:25px; font-weight:800; color:#001965;">43.2% vs 4.5%</div>
        <div style="font-size:14px; font-weight:700; margin:4px 0 2px;">Large vs Small Interface Recall</div>
        <div style="font-size:12px; color:#5A6070;">&gt;1,500 &Aring;&sup2; stable complexes (43.2% @0.90) vs &lt;800 &Aring;&sup2; SLiMs (4.5%)</div>
      </div>
      <div style="background:#FFF; border:1.5px solid #D0D7E5; border-top:7px solid #D9383A; padding:12px 14px; text-align:center;">
        <div style="font-size:25px; font-weight:800; color:#D9383A;">~6 GPU-Hours</div>
        <div style="font-size:14px; font-weight:700; margin:4px 0 2px;">Per Target Proteome Screen</div>
        <div style="font-size:12px; color:#5A6070;">1 bait protein vs 20,260 human proteins on 6x A100 GPUs + 3D SAVs</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1045px 715px; gap: 24px; flex: 1; margin: 16px 0;">
      <div style="background:#FFF; border:1.5px solid #D0D7E5; padding:10px; display:flex; align-items:center; justify-content:center;">
        <img src="data:image/png;base64,{b64_img}" style="width:100%; height:100%; object-fit:contain;">
      </div>
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column;">
        <div style="height:46px; background:#001965; color:#FFF; font-size:16.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          How to Read These Two Plots (Biology First)
        </div>
        <div style="padding:18px 22px; display:flex; flex-direction:column; gap:16px; font-size:14.2px; line-height:1.44;">
          <div>
            <strong style="color:#001965; font-size:15px;">1. Panel A (Left) &mdash; Precision Under 1:1,000 Proteome Odds:</strong><br>
            In a blind proteome screen, 99.9% of pairs do not bind (random baseline AUC = 0.001). Our reproduced pipeline achieves <strong>AUC = 0.262 (262x enrichment)</strong> and <strong>20.8% recall at &ge;90% precision</strong> (623 true hits, zero false positives).
          </div>
          <div>
            <strong style="color:#00857C; font-size:15px;">2. Panel B (Right) &mdash; Why Average Recall is 20.8% (MECH):</strong><br>
            Coevolutionary signal scales directly with buried physical surface area:<br>
            &bull; <strong>Large / Stable (&gt;1,500 &Aring;&sup2;, &gt;50 contact residues):</strong> <strong>43.2% recall</strong> at &ge;90% precision (<strong>51.8%</strong> at moderate cutoff).<br>
            &bull; <strong>Medium (800&ndash;1,500 &Aring;&sup2;):</strong> <strong>19.4% recall</strong>.<br>
            &bull; <strong>Small / Transient (&lt;800 &Aring;&sup2;, &le;10 residues, SLiMs):</strong> <strong>4.5% recall</strong>.
          </div>
        </div>
      </div>
    </div>

    <div class="banner teal">
      <div style="color:#00857C; font-weight:700; font-size:16px; margin-bottom:4px;">In-House Reproduction of Pei et al. (Sci Rep 2026) Disease-Interface Module &mdash; Verified on CASR (P41180) [OBS]:</div>
      <div>&bull; <strong>Dual-Evidence Pathogenic Rule:</strong> Automated SAV quality control (&lt;5% sequence mismatch) + dual-source pathogenicity filter (UniProt disease variants + EBI AlphaMissense per-protein scores) + 6 &Aring; CB/CA interface geometry (<code>src/druggability/interface_variants.py</code>, 22 unit tests passing).<br>
      &bull; <strong>Biological Proof-of-Concept on Calcium-Sensing Receptor (CASR, Tier-A CKD target in Data S6):</strong> Identified <strong>89 clinical pathogenic mutations</strong> (HHC1 / HYPOC1); <strong>64% cluster directly at the extracellular dimerization interface (&le;612)</strong>, proving the module pinpoints functionally critical contact surfaces for wet-lab mutagenesis.</div>
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 3/6</div>
  </div>
</div>

<!-- ==================== SLIDE 4: PART 1C — PROSPECTIVE VALIDATION & FIT MATRIX ==================== -->
<div class="slide" id="slide-4">
  <div class="hdr">
    <div class="hdr-l">
      <h1>Prospective Time-Split Validation (2024&ndash;2026) &amp; Biological Fit Matrix</h1>
      <div class="sub"><strong>PART 1C: PROSPECTIVE AUDIT &amp; OPERATING BOUNDARIES</strong> &nbsp;|&nbsp; <em>11 &lsquo;Zero-Prior-Evidence&rsquo; Data S6 Predictions Independently Confirmed by Cryo-EM / Co-IP Since Cutoff</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 4 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Group Meeting &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div style="display: grid; grid-template-columns: 1055px 705px; gap: 24px; flex: 1;">
      <!-- Left: Prospective Table -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div style="height:46px; background:#00857C; color:#FFF; font-size:16px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
            Prospective Audit: Data S6 &lsquo;Zero-Prior&rsquo; Pairs Confirmed in 2024&ndash;2026 (11 Cases)
          </div>
          <div style="padding:12px 18px 8px 18px; font-size:13.5px; color:#1A1A2E; line-height:1.36;">
            Data S6 defined 2,700 novel pairs with zero DB (Sep 2023) &amp; zero PDB template (Jan 2024) support. Over the subsequent two years, <strong>11 pairs were independently validated by wet-lab structures or co-IP (&gt;50% are transmembrane/organelle complexes*)</strong>:
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
        <div style="margin:12px 18px 14px 18px; background:#FFF; border:1px solid #D0D7E5; border-left:8px solid #001965; padding:11px 16px; font-size:13px; line-height:1.38;">
          <strong style="color:#001965;">Category B &mdash; Resolving Direct 3D Mechanism for Known AP-MS Hits:</strong> Beyond de novo Data S6 pairs, 3D predictions resolved how <em>NUDT5</em> allosterically blocks <em>PPAT</em> in purine synthesis (<em>Science</em> 2025, PMID 41196949) and how <em>SMG5&ndash;SMG6</em> dimerizes in NMD (<em>Nat Commun</em> 2026) &mdash; turning noisy AP-MS hits into point-mutant-verified mechanisms.
        </div>
      </div>

      <!-- Right: Fit Matrix & Governance -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="height:46px; background:#D9383A; color:#FFF; font-size:16px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          Biological Fit Matrix &amp; Campaign Governance
        </div>
        <div style="padding:14px 18px; display:flex; flex-direction:column; justify-content:space-between; flex:1; gap:14px;">
          <div style="background:#EBF7F5; border:1.5px solid #00857C;">
            <div style="background:#00857C; color:#FFF; font-size:14px; font-weight:700; padding:7px 14px;">IDEAL TARGETS (HIGH SENSITIVITY &mdash; USE HERE)</div>
            <div style="padding:12px 16px; font-size:13.2px; line-height:1.38; display:flex; flex-direction:column; gap:8px;">
              <div><strong style="color:#00857C;">&bull; Transmembrane &amp; Organelle Complexes (58% of S6):</strong><br>Hard to solubilize in detergent AP-MS (e.g., GPCR accessory proteins RAMP1/2/3, ER/lysosomal channels).</div>
              <div><strong style="color:#00857C;">&bull; Large Constitutive / Obligate Assemblies (&gt;1,500 &Aring;&sup2;):</strong><br>43.2% recall at &ge;90% precision (51.8% at moderate cutoff).</div>
              <div><strong style="color:#00857C;">&bull; Disease-Mutated Interfaces (ClinVar / Human Genetics):</strong><br>Pinpoints exact contact residues to design disruptor controls.</div>
            </div>
          </div>

          <div style="background:#FDF2F2; border:1.5px solid #D9383A;">
            <div style="background:#D9383A; color:#FFF; font-size:14px; font-weight:700; padding:7px 14px;">KNOWN BLIND SPOTS (DO NOT USE TO EXCLUDE)</div>
            <div style="padding:12px 16px; font-size:13.2px; line-height:1.38; display:flex; flex-direction:column; gap:8px;">
              <div><strong style="color:#D9383A;">&bull; Transient / PTM-Triggered Signaling Complexes:</strong><br>Phosphorylation- or ligand-dependent recruitment (e.g., GPCR-arrestin, kinase-substrate) lacks static coevolution.</div>
              <div><strong style="color:#D9383A;">&bull; Disordered Short Linear Motifs (SLiMs, &lt;800 &Aring;&sup2;):</strong><br>Only 4.5% recall at high precision (underrepresented in training).</div>
              <div><strong style="color:#D9383A;">&bull; Fast-Evolving / Immune / Tissue-Restricted Paralogs:</strong><br>Coevolution reflects family conservation, not tissue specificity.</div>
            </div>
          </div>

          <div style="background:#FDF6E7; border:1.5px solid #B7791F; border-left:8px solid #B7791F; padding:12px 16px; font-size:13.2px; line-height:1.38;">
            <strong style="color:#B7791F; font-size:14px;">Golden Rule (Lambourne et al., Nat Commun 2026):</strong><br>
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

<!-- ==================== SLIDE 5: PART 2A — BUSINESS QUESTION MENU ==================== -->
<div class="slide" id="slide-5">
  <div class="hdr">
    <div class="hdr-l">
      <h1>What is the Business Question for Our Campaign? (3 Options for Alignment)</h1>
      <div class="sub"><strong>PART 2A: CAMPAIGN BUSINESS QUESTION MENU</strong> &nbsp;|&nbsp; <em>Translating Baker&rsquo;s Interactome Engine into Concrete Drug Discovery &amp; Assay Design Decisions</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 5 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Group Meeting &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div class="banner navy">
      <strong style="color:#001965;">Why Define the Business Question Now?</strong> Our pipeline and 6-GPU screening capability are fully operational. Rather than running unfocused screens, we propose three concrete Business Questions (<strong>BQ-1, BQ-2, BQ-3</strong>) tailored to different stages of our cardiometabolic and rare-disease portfolio.
    </div>

    <div class="grid-3" style="flex: 1; margin: 18px 0;">
      <div class="card">
        <div class="card-hdr">BQ-1: Portfolio Partner Mining</div>
        <div class="card-sub">99 Data S6 Leads &rarr; 8 Pass All 4/4 Criteria</div>
        <div class="card-body">
          <div><strong style="color:#001965;">&bull; The Business Question:</strong><br>Among Baker&rsquo;s 2,700 zero-prior-evidence human PPIs (Data S6), which novel interactors of our cardiometabolic targets pass strict 4-criteria triage (Genetics, Pathway, Perturbation, Co-progression)?</div>
          <div><strong style="color:#001965;">&bull; Preliminary Result on 99 Unflagged Leads:</strong><br>Strict 4-criteria audit across 99 leads: C1 Both-Genetics (60; 46 Human GWAS/ClinVar), C2 Pathway (43), C3 Direct Perturb. (14), C4 CM Co-expr (56) &rarr; <strong>8 leads pass all 4/4</strong> (led by <strong>#1 RAMP3&ndash;MRAP2</strong> &amp; <strong>#2 RAMP1&ndash;MRAP2</strong>).</div>
          <div><strong style="color:#001965;">&bull; Deep-Dive on #1 Winner (RAMP3&ndash;MRAP2):</strong><br>Boltz-2 + omicMSA complex (ipTM=0.868), A100 MD (RMSD 0.49&Aring;), FEP hotspot scan (obesity SAVs R125 +6.25 &amp; L115 +5.21 kcal/mol), and gepant groove docking (-7.81 kcal/mol) completed.</div>
          <div><strong style="color:#001965;">&bull; Wet-Lab Deliverable:</strong><br>8-pair 4/4 ranked dossier + RAMP3&ndash;MRAP2 3D coordinates &amp; <strong>L115A/R125A/W56A</strong> disruptor controls ready for co-IP / BRET.</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr teal">BQ-2: De Novo Proteome Screen</div>
        <div class="card-sub teal">Find Missing Partners for Priority Baits</div>
        <div class="card-body">
          <div><strong style="color:#00857C;">&bull; The Business Question:</strong><br>When an internal biology project has a high-priority target (especially a transmembrane receptor, transporter, or organelle protein where detergent AP-MS fails), what is its missing endogenous partner?</div>
          <div><strong style="color:#00857C;">&bull; Target Archetypes:</strong><br>1) Orphan / membrane receptors needing unknown accessory proteins or trafficking chaperones.<br>2) Intracellular targets needing tissue-specific endogenous E3 ligases or deubiquitinases.</div>
          <div><strong style="color:#00857C;">&bull; Compute &amp; Timeline:</strong><br><strong>~6 GPU-hours per target bait</strong> (1 bait protein vs all 20,260 human proteins on 6x A100 GPUs).</div>
          <div><strong style="color:#00857C;">&bull; Wet-Lab Deliverable:</strong><br>Calibrated partner shortlist (@90% / @80% precision) + 3D complex structures + GTEx co-expression matrix.</div>
        </div>
      </div>

      <div class="card">
        <div class="card-hdr red">BQ-3: 3D Interface &amp; Genetics Triage</div>
        <div class="card-sub red">De-Risk Mechanism &amp; Design Assay Controls</div>
        <div class="card-body">
          <div><strong style="color:#D9383A;">&bull; The Business Question:</strong><br>When biology teams already have a suspect binding partner (from AP-MS, literature, or genetics) or a human disease variant of unknown mechanism, where is the exact 3D contact surface and how do we test it?</div>
          <div><strong style="color:#D9383A;">&bull; Scientific Problem Solved:</strong><br>Standard AP-MS cannot distinguish direct vs indirect binding, and domain truncations often misfold the whole protein. Biologists need surgical single-residue disruptor mutations.</div>
          <div><strong style="color:#D9383A;">&bull; Compute &amp; Timeline:</strong><br>~15 minutes per pair via <code>bbbkit interface-variants</code> (UniProt + AlphaMissense + 6&Aring; CB/CA contact geometry).</div>
          <div><strong style="color:#D9383A;">&bull; Wet-Lab Deliverable:</strong><br>Atomic 3D interface coordinates + human pathogenic SAV enrichment + <strong>2&ndash;3 point-mutations to selectively abolish binding</strong>.</div>
        </div>
      </div>
    </div>

    <div class="banner teal">
      <strong style="color:#00857C;">How the 3 Business Questions Fit Together as One Modular Pipeline:</strong>
      <strong>BQ-1</strong> (99 Cardiometabolic Data S6 Leads) and <strong>BQ-2</strong> (1-Bait Proteome Screen) generate high-precision partner hypotheses; <strong>BQ-3</strong> (3D Interface + Pathogenic SAV Mapping) automatically runs on the top hits so every candidate handed to wet-lab biology arrives with an actionable 3D model and point-mutant negative control.
    </div>
  </div>

  <div class="ftr">
    <div>References: Zhang et al., <em>Science</em> 390, eadt1630 (2025) | Pei, Zhang &amp; Cong, <em>Sci Rep</em> 16:25590 (2026) | Lambourne et al., <em>Nat Commun</em> (2026)</div>
    <div>druggability repo &nbsp;|&nbsp; Page 5/6</div>
  </div>
</div>

<!-- ==================== SLIDE 6: PART 2B — BQ-1 PRELIMINARY RESULTS (4-CRITERIA + MD/FEP) ==================== -->
<div class="slide" id="slide-6">
  <div class="hdr">
    <div class="hdr-l">
      <h1>BQ-1 Preliminary Result: 4-Criteria Triage (99 Leads) &amp; RAMP3&ndash;MRAP2 MD/FEP</h1>
      <div class="sub"><strong>PART 2B: BQ-1 PRELIMINARY RESULTS</strong> &nbsp;|&nbsp; <em>8/99 Cardiometabolic Leads Pass All 4 Strict Criteria; #1 RAMP3&ndash;MRAP2 Characterized by Boltz-2, MD &amp; FEP</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">SLIDE 6 OF 6 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Group Meeting &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div style="display: grid; grid-template-columns: 1045px 715px; gap: 24px; flex: 1;">
      <!-- Left: 99 Leads 4-Criteria Funnel & Top 4/4 Table -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div style="height:46px; background:#001965; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
            BQ-1 Strict 4-Criteria Triage Across 99 Unflagged Cardiometabolic Leads
          </div>
          <div style="padding:12px 16px; display:grid; grid-template-columns:repeat(5, 1fr); gap:10px;">
            <div style="background:#FFF; border:1.5px solid #001965; padding:7px 4px; text-align:center;">
              <div style="font-size:15.5px; font-weight:800; color:#001965;">C1: Genetics</div>
              <div style="font-size:11.5px; font-weight:700;">60/99 (46 Human)</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #001965; padding:7px 4px; text-align:center;">
              <div style="font-size:15.5px; font-weight:800; color:#001965;">C2: Pathway</div>
              <div style="font-size:11.5px; font-weight:700;">43/99 Shared Path.</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #00857C; padding:7px 4px; text-align:center;">
              <div style="font-size:15.5px; font-weight:800; color:#00857C;">C3: Perturb.</div>
              <div style="font-size:11.5px; font-weight:700;">14/99 Direct Evid.</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #00857C; padding:7px 4px; text-align:center;">
              <div style="font-size:15.5px; font-weight:800; color:#00857C;">C4: Co-Prog.</div>
              <div style="font-size:11.5px; font-weight:700;">56/99 CM Co-Expr.</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #D9383A; padding:7px 4px; text-align:center;">
              <div style="font-size:15.5px; font-weight:800; color:#D9383A;">8 Pass 4/4</div>
              <div style="font-size:11.5px; font-weight:700;">#1 RAMP3&ndash;MRAP2</div>
            </div>
          </div>

          <div style="padding:0 16px;">
            <table class="std-tbl" style="font-size:12.0px;">
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

        <div style="margin:10px 16px 14px 16px; background:#FFF; border:1px solid #D0D7E5; border-left:8px solid #00857C; padding:10px 15px; font-size:12.8px; line-height:1.36;">
          <strong style="color:#00857C;">Why RAMP3&ndash;MRAP2 is the #1 Winner for Structural &amp; Energetic Deep-Dive:</strong> Passes all 4 criteria + Tier-A approved &amp; Novo Amylin/CagriSema co-receptor (RAMP3) paired with human monogenic obesity protein MRAP2. Two human obesity variants on MRAP2 (<strong>p.Leu115Val</strong>, <strong>p.Arg125Cys</strong>) sit directly inside the 3D interface.
        </div>
      </div>

      <!-- Right: #1 Winner RAMP3-MRAP2 Docking, MD & FEP -->
      <div style="background:#E8EEF7; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="height:46px; background:#D9383A; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          #1 Winner (RAMP3&ndash;MRAP2): 3D Complex, Docking, MD &amp; FEP
        </div>
        <div style="padding:12px 16px; display:flex; flex-direction:column; justify-content:space-between; flex:1; gap:12px;">
          <div style="background:#FFF; border:1px solid #D0D7E5; padding:6px; height:285px; display:flex; align-items:center; justify-content:center;">
            <img src="data:image/png;base64,{b64_bq1}" style="width:100%; height:100%; object-fit:contain;">
          </div>

          <div style="background:#FFF; border:1.5px solid #001965; flex:1; display:flex; flex-direction:column;">
            <div style="background:#001965; color:#FFF; font-size:13.5px; font-weight:700; padding:7px 14px;">QUANTITATIVE BIOPHYSICAL &amp; DRUGGABILITY SUMMARY</div>
            <div style="padding:10px 14px; font-size:12.5px; line-height:1.36; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
              <div><strong style="color:#001965;">&bull; 3D Complex &amp; Coevolution (RF2-PPI + Boltz-2 omicMSA):</strong><br><strong>ipTM = 0.868, ptm = 0.834</strong> (180 inter-chain contacts &le;5&Aring;: 21 TM-TM + 159 ECD/juxtamembrane). RF2-PPI TM helix contact prob = 0.590 (RAMP3) / 0.865 (RAMP1).</div>
              <div><strong style="color:#00857C;">&bull; Explicit-Solvent MD (A100, Amber14SB + TIP3P, 200 ps):</strong><br>Complex remains tightly bound with <strong>backbone RMSD = 0.49 &Aring;</strong> (2,558 ns/day).</div>
              <div><strong style="color:#D9383A;">&bull; FEP Mutational Hotspot Scan (Obesity Variants at Interface):</strong><br>Human obesity SAVs <strong>MRAP2 R125</strong> (d=3.33&Aring; to RAMP3 D113, <strong>ddG = +6.25 kcal/mol</strong>) &amp; <strong>L115</strong> (d=1.97&Aring; to D107, <strong>ddG = +5.21 kcal/mol</strong>) are top energetic hotspots alongside M87 (+3.29), F85 (+3.07) &amp; RAMP3 W56 (+2.51 kcal/mol).</div>
              <div><strong style="color:#001965;">&bull; Interface Groove Docking (AutoDock Vina + Boltz-2 Ternary):</strong><br>RAMP-antagonist scaffolds <strong>Ubrogepant (-7.81 vs -7.09 kcal/mol control)</strong> &amp; <strong>Rimegepant (-7.39 kcal/mol, ternary ligand_ipTM = 0.950)</strong> selectively bind the composite RAMP3&ndash;MRAP2 ECD groove &rarr; propose <strong>L115A / R125A / W56A</strong> co-IP disruptor controls.</div>
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
      <h1>Appendix: Does MRAP2 Compete with Amylin or Destabilize AMY1R / AMY3R?</h1>
      <div class="sub"><strong>SUPPLEMENTARY DEEP-DIVE (ZHCO FOLLOW-UP)</strong> &nbsp;|&nbsp; <em>Cryo-EM Superposition (7TYF/7TZF), Quaternary Boltz-2 Co-Folding, and 8-System A100 Explicit-Solvent MD</em></div>
    </div>
    <div class="hdr-r">
      <div class="badge">APPENDIX S1 &nbsp;|&nbsp; RIC-410</div>
      <div class="meta">Group Meeting &nbsp;|&nbsp; Novo Nordisk</div>
    </div>
  </div>

  <div class="body-area">
    <div style="display: grid; grid-template-columns: 1045px 715px; gap: 24px; flex: 1;">
      <!-- Left: Quantitative Comparison Table -->
      <div style="background:#F2F4F8; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div style="height:46px; background:#001965; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
            Quantitative Comparison: Cryo-EM Baselines vs Subunit &amp; Orthosteric Competition
          </div>
          <div style="padding:12px 16px; display:grid; grid-template-columns:repeat(3, 1fr); gap:12px;">
            <div style="background:#FFF; border:1.5px solid #001965; padding:7px 8px; text-align:center;">
              <div style="font-size:14.5px; font-weight:800; color:#001965;">Cryo-EM Fact (7TYF/7TZF)</div>
              <div style="font-size:11.5px; font-weight:700;">98.5% Amylin ICs on CTR; RAMP W84/P85 caps Tyr37</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #00857C; padding:7px 8px; text-align:center;">
              <div style="font-size:14.5px; font-weight:800; color:#00857C;">Mech 1: Subunit Competition</div>
              <div style="font-size:11.5px; font-weight:700;">80.0% RAMP3 &amp; 75.7% RAMP1 CTR-face shared w/ MRAP2</div>
            </div>
            <div style="background:#FFF; border:1.5px solid #D9383A; padding:7px 8px; text-align:center;">
              <div style="font-size:14.5px; font-weight:800; color:#D9383A;">Mech 2: 7TM Pocket Block</div>
              <div style="font-size:11.5px; font-weight:700;">Amylin 7TM contacts drop 92&rarr;2 (AMY1R) &amp; 96&rarr;0 (AMY3R)</div>
            </div>
          </div>

          <div style="padding:0 16px;">
            <table class="std-tbl" style="font-size:12.0px;">
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
                  <td><strong>&lt;dG&gt; = &minus;113.5 &plusmn; 4.1 (ddG = +124.3)</strong></td>
                  <td>MRAP2 ejects RAMP1 or cuts dG by 52%</td>
                </tr>
                <tr style="background:#EBF7F5;">
                  <td><strong style="color:#D9383A;">AMY3R &minus;/+ MRAP2</strong></td>
                  <td>CTR+RAMP3(&plusmn;M) : Amy</td>
                  <td>96 &rarr; 0 7TM ICs (&minus;100%); displaced 24.5&Aring;</td>
                  <td><strong>&minus;164.2 (&minus;223.6) &rarr; &minus;148.9 (&minus;163.1 vdW)</strong></td>
                  <td>MRAP2 68&ndash;88 plugs 7TM (ddE = +60.5)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div style="margin:10px 16px 14px 16px; background:#FFF; border:1px solid #D0D7E5; border-left:8px solid #D9383A; padding:10px 15px; font-size:12.6px; line-height:1.36;">
          <strong style="color:#D9383A;">Testable Wet-Lab Hypothesis (cAMP / BRET / Surface ELISA):</strong> Co-expressing WT MRAP2 will competitively sequester RAMP3/RAMP1 away from CTR and attenuate amylin/cagrilintide potency, whereas our FEP-designed obesity point-mutants (<strong>MRAP2 L115A/V, R125A/C</strong>) will lose RAMP binding and restore normal AMY1R/AMY3R signaling.
        </div>
      </div>

      <!-- Right: 2-Panel Competition & MD Plot + Summary -->
      <div style="background:#E8EEF7; border:1.5px solid #D0D7E5; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="height:46px; background:#00857C; color:#FFF; font-size:15.5px; font-weight:700; padding:0 20px; display:flex; align-items:center;">
          Dual-Mechanism Competition &amp; A100 MD Energetics
        </div>
        <div style="padding:12px 16px; display:flex; flex-direction:column; justify-content:space-between; flex:1; gap:12px;">
          <div style="background:#FFF; border:1px solid #D0D7E5; padding:6px; height:285px; display:flex; align-items:center; justify-content:center;">
            <img src="data:image/png;base64,{b64_amy}" style="width:100%; height:100%; object-fit:contain;">
          </div>

          <div style="background:#FFF; border:1.5px solid #001965; flex:1; display:flex; flex-direction:column;">
            <div style="background:#001965; color:#FFF; font-size:13.5px; font-weight:700; padding:7px 14px;">ANSWERS TO ZHENG&rsquo;S TWO QUESTIONS (MECHANISM SUMMARY)</div>
            <div style="padding:10px 14px; font-size:12.5px; line-height:1.38; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
              <div>
                <strong style="color:#001965; font-size:13.2px;">1. Do Amylin and MRAP2 Compete in Binding to Amylin Receptors?</strong><br>
                <strong>YES &mdash; at two structural levels:</strong><br>
                &bull; <strong>Subunit Sequestration (MRAP2 vs CTR for RAMP1/3):</strong> MRAP2 occupies <strong>80.0% (32/40)</strong> of RAMP3&rsquo;s and <strong>75.7% (28/37)</strong> of RAMP1&rsquo;s CTR-binding residues, and binds RAMP3 more tightly than CTR in MD (<strong>ddG = &minus;23.43 kcal/mol</strong>).<br>
                &bull; <strong>Tyr37 Pocket Cap Occlusion:</strong> MRAP2 covers <strong>100%</strong> of the RAMP1/3 Trp84&ndash;Pro85 shelf that caps amylin&rsquo;s C-terminal Tyr37-NH2.
              </div>
              <div>
                <strong style="color:#D9383A; font-size:13.2px;">2. Does MRAP2 Affect the Stability of Amylin / Receptor Complexes?</strong><br>
                <strong>YES &mdash; severe destabilization &amp; 7TM ejection:</strong><br>
                &bull; In quaternary co-folding + MD, MRAP2 invades the CTR ECL2/ECL3/7TM entrance, reducing amylin&rsquo;s 7TM contacts by <strong>97.8% in AMY1R (ddG = +124.26 kcal/mol)</strong> and <strong>100% in AMY3R (ddE_vdW = +60.49 kcal/mol)</strong>.
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

</body>
</html>
"""

OUT_HTML.write_text(html, encoding="utf-8")
print("Wrote 7-slide HTML:", OUT_HTML)


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

        # Print 7-page PDF
        await page.pdf(
            path=str(OUT_PDF),
            width="1920px",
            height="1080px",
            print_background=True,
            margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"},
        )
        print(f"Rendered PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")

        # Screenshot each slide element at 2x
        for i in range(1, 8):
            el = await page.query_selector(f"#slide-{i}")
            out_png = SLIDE_DIR / f"slide_{i:02d}@2x.png"
            await el.screenshot(path=str(out_png))
            print(f"Rendered slide {i} PNG: {out_png} ({out_png.stat().st_size:,} bytes)")

        await browser.close()


asyncio.run(render_all())
