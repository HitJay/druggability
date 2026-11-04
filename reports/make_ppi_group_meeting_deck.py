#!/usr/bin/env python
"""Generate the optimized 8-slide editable PPTX deck (6 main slides + 2 Appendix slides) for the ~10 min group meeting scientific update (RIC-410).

Structure aligned with Lingling's feedback & group meeting plan:
  - Slide 1: Title & Executive Framing (3 pillars: Pipeline Landscape, New PPI Module & Boundaries, Assay-Gated Exploratory Plan)
  - Slide 2: Druggability Agent Platform: Systematic 6-Module Capability Landscape & Validated Benchmarks
  - Slide 3: Module 2 Deep-Dive: Baker Engine Summary, In-House A100 Validation & 4 Reading Rules (Consolidated from old Slides 2+3)
  - Slide 4: Prospective Time-Split Validation (2024-2026) & Biological Fit Matrix
  - Slide 5: Preliminary Campaign Plan: 3 Candidate Business Questions & Wet-Lab Assay Readiness Gate
  - Slide 6: Dry-Run Proof-of-Concept: BQ-1 99-Lead Triage & RAMP3-MRAP2 Cross-Module Audit
  - Appendix S1 (Slide 7): Does MRAP2 Compete with Amylin or Destabilize AMY1R / AMY3R? (Cryo-EM + 8-System MD)
  - Appendix S2 (Slide 8): Detailed Two-Study Comparison (2025 Science vs 2026 Sci Rep) & Cascade Numbers

Every slide has full Chinese oral speaker notes + Q&A defense in slide.notes_slide.
Slide canvas is 100% pure English (0 CJK characters).
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY = RGBColor(0x00, 0x19, 0x65)
TEAL = RGBColor(0x00, 0x85, 0x7C)
RED = RGBColor(0xD9, 0x38, 0x3A)
AMBER = RGBColor(0xB7, 0x79, 0x1F)
INK = RGBColor(0x1A, 0x1A, 0x2E)
GREY = RGBColor(0x5A, 0x60, 0x70)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xE8, 0xEE, 0xF7)
BORDER = RGBColor(0xD0, 0xD7, 0xE5)
GREEN_BG = RGBColor(0xEB, 0xF7, 0xF5)
RED_BG = RGBColor(0xFD, 0xF2, 0xF2)
AMBER_BG = RGBColor(0xFD, 0xF6, 0xE7)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = 13.333, 7.5


def add_blank_slide():
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(slide, x, y, w, h, fill, line=None, line_w=0.75, shape_type=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, runs, size: float = 11.0, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after: float = 3.0, font="Calibri"):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(runs, str):
        runs = [runs]
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if isinstance(para, str):
            para = [(para, {})]
        for txt, o in para:
            r = p.add_run()
            r.text = txt
            r.font.name = o.get("font", font)
            r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", bold)
            r.font.italic = o.get("italic", False)
            r.font.color.rgb = o.get("color", color)
    return tb


def add_header_footer(slide, page_num, total_pages, title, subtitle, section_tag,
                      footer_left="References: Zhang et al., Science 390, eadt1630 (2025) | Pei, Zhang & Cong, Sci Rep 16:25590 (2026) | Lambourne et al., Nat Commun (2026)"):
    rect(slide, 0, 0, W, H, WHITE)
    rect(slide, 0, 0, W, 0.96, NAVY)
    text(slide, 0.45, 0.14, 10.10, 0.36, title, size=17.2, bold=True, color=WHITE)
    text(slide, 0.45, 0.55, 10.10, 0.28, [
        [(section_tag + "  |  ", {"size": 10.0, "bold": True, "color": ICE}),
         (subtitle, {"size": 10.0, "color": ICE, "italic": True})]
    ])
    badge_str = f"SLIDE {page_num} OF {total_pages}  |  RIC-410" if isinstance(page_num, int) else f"{page_num}  |  RIC-410"
    text(slide, 10.60, 0.18, 2.28, 0.54, [
        [(badge_str, {"size": 10.0, "bold": True, "color": WHITE})],
        [("Scientific Update  |  Novo Nordisk", {"size": 9.0, "color": ICE})]
    ], align=PP_ALIGN.RIGHT, space_after=2)
    rect(slide, 0.45, 7.08, W - 0.90, 0.01, BORDER)
    text(slide, 0.45, 7.12, 9.50, 0.25, footer_left, size=8.2, color=GREY)
    page_str = f"druggability repo  |  Page {page_num}/{total_pages}" if isinstance(page_num, int) else f"druggability repo  |  {page_num}"
    text(slide, 10.00, 7.12, 2.88, 0.25, page_str, size=8.2, color=GREY, align=PP_ALIGN.RIGHT)


def set_notes(slide, notes_str):
    ns = slide.notes_slide
    ns.notes_text_frame.text = notes_str.strip()


# ==============================================================================
# SLIDE 1: Title & Executive Framing (~1 min)
# ==============================================================================
s1 = add_blank_slide()
rect(s1, 0, 0, W, H, NAVY)
rect(s1, 0, 0, W, 0.12, TEAL)

rect(s1, 0.60, 0.45, 4.40, 0.36, TEAL)
text(s1, 0.60, 0.50, 4.40, 0.26, "SCIENTIFIC UPDATE (~10 MIN)  |  PLANNING STAGE  |  RIC-410",
     size=10.0, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

text(s1, 0.60, 0.96, 12.10, 0.52,
     "Druggability Pipeline Landscape & Preliminary PPI Screening Plan",
     size=27.5, bold=True, color=WHITE)

text(s1, 0.60, 1.54, 12.10, 0.34,
     "1. End-to-End Capability Landscape   |   2. Proteome PPI Module & Boundaries   |   3. Assay-Gated Exploratory Plan",
     size=13.8, bold=True, color=ICE)

text(s1, 0.60, 1.98, 12.10, 0.28,
     "Presenter: Qiuye Jin (QYJI)   |   Cardiometabolic Data S6 Collaborator: Zheng Cao (ZHCO)   |   Research Insights China (RIC)",
     size=10.8, color=ICE)

# 3 Executive Summary Pillars on Slide 1 (y=2.42, h=3.82)
cw1 = 3.88
gap1 = 0.24
s1_cards = [
    ("1. Pipeline Landscape (Slide 2)", "6 Integrated Modules Across Modalities", TEAL, [
        ("End-to-End Platform",
         "Built a 6-stage computational pipeline under `druggability`: (1) Target Genetics & Safety, (2) Proteome PPI & SAVs, (3) Peptide & BBB, (4) Pocket & Virtual Screening, (5) Explicit MD & FEP/TI, and (6) 3D Delivery."),
        ("Battle-Tested on Internal Projects",
         "Validated across OXTR peptide selectivity (RIC-403), GPR81 anti-flushing FEP (RIC-396), TSPO target fishing (RIC-408), GIGYF1 glue pocket (RIC-407), and peptide BBB / 3_safety (RIC-349/409)."),
    ]),
    ("2. New PPI Capability (Slides 3-4)", "Baker RF2-PPI Validation & Boundaries", WHITE, [
        ("What Baker & Cong Achieved",
         "Science 2025 (7x omicMSAs + RF2-PPI -> 17,849 PPIs @90% prec; 2,700 zero-prior in Data S6) + Sci Rep 2026 (clinical SAVs mapped to 3D interfaces)."),
        ("In-House Audit & Scope Rules",
         "Reproduced on 6x A100 GPUs (262x lift over random; r=0.919). High sensitivity on large/transmembrane complexes (43.2% recall >1,500 A2), blind spot on transient SLiMs (4.5%) -> positive generator only."),
    ]),
    ("3. Exploratory Plan & Gate (Slides 5-6)", "3 Business Options Gated on Wet-Lab Assay", RED, [
        ("3 Candidate Business Questions",
         "BQ-1 (99 cardiometabolic Data S6 leads triage), BQ-2 (on-demand 1-vs-20,260 bait screen in ~6 GPU-h), and BQ-3 (6A disease-interface & point-mutant control design)."),
        ("Dry-Run PoC & Assay Readiness Gate",
         "Completed dry-run triage (8/99 pass 4/4; #1 RAMP3-MRAP2 audited via Boltz-2, MD & FEP). Next step is gated on checking wet-lab screening/validation assay readiness (co-IP / BRET / cAMP)."),
    ]),
]

x1 = 0.60
for c_hdr, c_sub, c_col, c_items in s1_cards:
    hdr_bg = TEAL if c_col != RED else RED
    rect(s1, x1, 2.42, cw1, 3.82, WHITE, line=hdr_bg, line_w=1.5)
    rect(s1, x1, 2.42, cw1, 0.40, hdr_bg)
    text(s1, x1 + 0.14, 2.50, cw1 - 0.28, 0.26, c_hdr, size=11.2, bold=True, color=WHITE)
    rect(s1, x1, 2.82, cw1, 0.28, ICE)
    text(s1, x1 + 0.14, 2.86, cw1 - 0.28, 0.20, c_sub, size=9.2, bold=True, color=NAVY)
    paras = []
    for it_t, it_b in c_items:
        paras.append([
            ("• " + it_t + ":\n", {"size": 9.8, "bold": True, "color": NAVY if hdr_bg == TEAL else RED}),
            (it_b, {"size": 9.1, "color": INK}),
        ])
    text(s1, x1 + 0.14, 3.20, cw1 - 0.28, 2.94, paras, space_after=6.0)
    x1 += cw1 + gap1

rect(s1, 0.60, 6.42, 12.12, 0.58, ICE)
text(s1, 0.80, 6.50, 11.72, 0.44, [
    [("Goal of Today's 10-Min Update (Planning Stage): ", {"size": 10.5, "bold": True, "color": RED}),
     ("Share our systematic druggability pipeline landscape (Part 1), clarify what the new PPI module can/cannot do (Part 2), and align on how to check wet-lab assay readiness before committing to a campaign (Part 3).",
      {"size": 10.0, "bold": True, "color": NAVY})]
])

set_notes(s1, """【Slide 1 口播讲稿（约 1 分钟）】
大家好！非常感谢 Lingling 安排今天这 10 分钟的 Scientific Update。
在之前跟大家聊 Baker 团队全蛋白组 PPI 预测的时候，我们意识到如果只单独讲一篇文章，大家很容易觉得它是一个孤立的计算脚本；同时我们目前还处于早期的探索与规划阶段（Planning Stage）。
因此今天的汇报分为三个部分：
1. 第一部分（Slide 2）：先把我们过去几个月在 `druggability` 管线里已经建成的 6 大核心计算模块和真实交付案例做个全景盘点，说明新引入的 PPI 模块在整个管线里处于什么位置；
2. 第二部分（Slide 3–4）：用最精炼的篇幅总结 Baker & Cong 团队（Science 2025 / Sci Rep 2026）做成了什么、我们在 6 张 A100 上的实测表现，以及它的适用边界（什么靶点好用、什么情况是盲区）；
3. 第三部分（Slide 5–6）：汇报我们初步梳理的 3 个业务问题选项（BQ-1/2/3）和在 99 对心代候选上的 Dry-Run 概念验证（如 RAMP3–MRAP2）。最关键的是，我们目前还在 Plan 阶段，后续到底推不推、怎么推，完全取决于先跟生物团队核对下游湿实验 Screening / Validation Assay（如 co-IP、BRET、cAMP）是否 Ready。""")


# ==============================================================================
# SLIDE 2: Systematic Druggability Pipeline Landscape & Validated Benchmarks (~2 min)
# ==============================================================================
s2 = add_blank_slide()
add_header_footer(
    s2, 2, 6,
    "Druggability Agent Platform: Systematic Capability Landscape & Benchmarks",
    "6 Integrated Modules Across Target Genetics, PPI, Peptide/BBB, Virtual Screening, MD/FEP & 3D Delivery",
    "PART 1: PIPELINE CAPABILITY LANDSCAPE",
    footer_left="Platform: druggability repo (hpccnrd001 A100 Cluster)  |  Validated tickets: RIC-349, RIC-392, RIC-396, RIC-403, RIC-407, RIC-408, RIC-410"
)

# 2A. Top Workflow Pipeline Chevron Bar (6 End-to-End Stages) (y=1.08, h=0.48)
stages = [
    ("Stage 1: Target & Genetics", "Open Targets / GWAS / Safety", NAVY),
    ("Stage 2: PPI & Interfaces", "RF2-PPI / Boltz-2 / SAVs", TEAL),
    ("Stage 3: Peptide & BBB", "PRODIGY / Lipidation / ESM-2", NAVY),
    ("Stage 4: Pocket & VS", "fpocket / DrugCLIP / Vina", TEAL),
    ("Stage 5: Explicit MD & FEP", "A100 OpenMM / Alchemical TI", RED),
    ("Stage 6: 3D & Assay Design", "3Dmol HTML / Point-Mutants", NAVY),
]
sw = 1.98
sgap = 0.11
sx = 0.45
for idx, (st_hdr, st_sub, st_col) in enumerate(stages):
    rect(s2, sx, 1.08, sw, 0.48, ICE, line=st_col, line_w=1.1)
    rect(s2, sx, 1.08, 0.06, 0.48, st_col)
    text(s2, sx + 0.10, 1.12, sw - 0.14, 0.40, [
        [(st_hdr, {"size": 8.4, "bold": True, "color": st_col})],
        [(st_sub, {"size": 7.3, "color": INK})],
    ], space_after=1)
    if idx < len(stages) - 1:
        text(s2, sx + sw, 1.18, sgap, 0.26, "▸", size=10.5, bold=True, color=GREY, align=PP_ALIGN.CENTER)
    sx += sw + sgap

# 2B. Six Core Capability Pillar Cards (2 rows x 3 cols) (y=1.66, h=2.66 total)
cards = [
    ("1. Target Tractability, Genetics & Safety", "druggability.tractability | ligandability | 3_safety", NAVY, [
        ("5-Axis Target Profiling", "Open Targets GraphQL + ChEMBL ligandability + fpocket + clinical precedents + safety across SM / Antibody / Peptide / PROTAC."),
        ("Human Genetics & Safety Gate", "GWAS / ClinVar / UKB WES variant mapping + bidirectional target safety evaluation (W40-W44 & 25-gene T2D/obesity panels)."),
    ]),
    ("2. Proteome PPI & Interface Variants [NEW]", "RF2-PPI (6x A100) | Boltz-2 | interface_variants", TEAL, [
        ("Proteome Partner Screen", "20,260-protein coevolution + structure funnel (~6 GPU-h/bait; 262x enrichment over random; 43.2% recall on complexes >1,500 A2)."),
        ("3D Disease-Variant Triage", "Maps UniProt + AlphaMissense pathogenic SAVs onto 6A contact surfaces to design surgical point-mutant negative controls."),
    ]),
    ("3. Peptide Engineering & CNS/BBB Exposure", "druggability.peptide (affinity | scan | chem_mod | bbb)", NAVY, [
        ("Peptide Structural Pharmacology", "PRODIGY contact affinity (dG/Kd), high-throughput Ala/20-AA mutational hotspot scan, and subtype selectivity counter-screens."),
        ("Protraction & BBB Platform", "3D cone steric audit for C16/C18/C20 lipidation exit vectors + ESM-2 multi-task heads (BBB AUC=0.89, hemolytic AUC=1.00)."),
    ]),
    ("4. Pocket Detection, AI VS & Target Fishing", "druggability.pocket | drugclip | vina | image2smiles", TEAL, [
        ("Multi-Tier Virtual Screening", "Contrastive DrugCLIP (2.94M library in ~22s) -> tight-box AutoDock Vina (redocking <2.0 A QC gate) -> Boltz-2 affinity & Murcko clustering."),
        ("Off-Target Deconvolution & OCR", "5-layer ligand target fishing + clinical Cmax,u/Ki occupancy gating; DECIMER/MolScribe chemical structure recovery from literature."),
    ]),
    ("5. Explicit-Solvent MD & Alchemical FEP/TI", "OpenMM 8.3 CUDA | openmmtools.alchemy (A100)", RED, [
        ("High-Throughput Explicit MD", "All-atom Amber14SB + TIP3P water + 0.15M NaCl on A100 (>2,100 ns/day); resolves static MM/GBSA vacuum cavity artifacts & steric ejection."),
        ("Alchemical FEP & Annihilation TI", "Dual-topology relative FEP & mutational hotspot free-energy scans to quantify residue/variant energetic contributions (ddG in kcal/mol)."),
    ]),
    ("6. Automated 3D Dossiers & Wet-Lab Governance", "druggability.report | 3Dmol.js | Scientific Boundaries", NAVY, [
        ("Zero-Install 3D Deliverables", "Self-contained 3Dmol.js WebGL HTML dossiers, editable NN-styled PPTX + vector PDF decks, and ranked Excel/CSV scorecards."),
        ("Audit & Boundary Governance", "Strict [FACT]/[OBS]/[MECH]/[HYP] tagging; mandatory homolog negative controls (ipTM != potency); positive hypothesis generator only."),
    ]),
]

cw = 3.98
cgap_x = 0.245
cgap_y = 0.12
ch = 1.27
for idx, (c_title, c_tag, c_col, c_bullets) in enumerate(cards):
    row = idx // 3
    col = idx % 3
    cx = 0.45 + col * (cw + cgap_x)
    cy = 1.66 + row * (ch + cgap_y)
    rect(s2, cx, cy, cw, ch, WHITE, line=BORDER)
    rect(s2, cx, cy, cw, 0.24, c_col)
    text(s2, cx + 0.10, cy + 0.03, cw - 0.20, 0.18, c_title, size=8.6, bold=True, color=WHITE)
    rect(s2, cx, cy + 0.24, cw, 0.17, LIGHT)
    text(s2, cx + 0.10, cy + 0.25, cw - 0.20, 0.15, c_tag, size=7.1, bold=True, color=c_col, font="Consolas")
    paras = []
    for b_hdr, b_desc in c_bullets:
        paras.append([
            ("• " + b_hdr + ": ", {"size": 7.6, "bold": True, "color": c_col}),
            (b_desc, {"size": 7.3, "color": INK})
        ])
    text(s2, cx + 0.10, cy + 0.44, cw - 0.20, ch - 0.47, paras, space_after=1.5)

# 2C. Bottom Table: Production-Validated Internal Case Studies Across Modalities (y=4.42, h=2.58)
rect(s2, 0.45, 4.42, 12.43, 0.28, NAVY)
text(s2, 0.57, 4.46, 12.15, 0.20,
     "Production-Validated Portfolio Benchmarks Across Modalities (Real Executed Outputs & Wet-Lab Handovers)",
     size=9.2, bold=True, color=WHITE)

bench_rows = [
    ("Modality / Domain", "Project & Ticket", "Computational Stack Executed", "Headline Verified Biophysical / Biological Finding", "Deliverable & Status"),
    ("Peptide Selectivity & Protraction", "OXTR vs V1a/V1b/V2R & GLP-1R (RIC-403)", "Cryo-EM 7QVM/7DW9 + PRODIGY + A100 Explicit MD + 3D Lipidation Cone", "Explained >1,000x selectivity: Pro7Gly releases V2R TM1 clash (3.51A, 70.8A MD ejection); verified Leu8 C18-diacid exit vector (0 clashes, ~160h PK).", "3D HTML + 12-Slide Deck Delivered (Mingyue)"),
    ("Small-Molecule GPCR & FEP", "GPR81 (HCAR1) vs HCAR2/3 (RIC-396)", "45-Cmpd Vina + Boltz-2 Affinity + Steric Contradiction + 3-Leg OpenFEP", "Eliminated flushing liability via HCAR2 basic clash wall (+45.2 kcal/mol); proved AZ1 vs lactate mutual exclusion; converged c30/c31 FEP.", "3D HTML + 45-Cmpd Scorecard Delivered (UHYG)"),
    ("Ligand Target Fishing & TI", "TSPO 5-Ligand Panel (PK11195, Emapunil) (RIC-408)", "5-Source Curation + 17-Pocket Vina Gate + 250ps MD + 57-Anchor TI", "Proved CAR (NR1I3) is PK11195 #2 target (IC50 25-56 nM, 5 methods); discovered TSPO dimer pocket 4RYI_p26 (LEU58 +7.6 kJ/mol) & Cmax/Ki gate.", "6-Round Dossiers + 7-Slide Deck Delivered (ZHCO)"),
    ("Molecular Glue & Cryptic Pocket", "GIGYF1-GRB10/14 & GHSR VS (RIC-407 / RIC-392)", "Crystal 7RUQ/2AUH + UKB 454k WES Mutagenesis + 7,931-Cmpd Vina/Boltz-2", "Identified 445 A3 cryptic glue pocket at GIGYF1 interface; UKB p.Tyr498Cys drops affinity >80x (+2.74 kcal/mol, T2D OR=5.91); 20 GHSR chemotypes.", "3D Glue Dossier & Ranked Hits (GO Decision)"),
    ("Peptide CNS/BBB & Safety Gate", "MC4R / RORA BBB & 3_Safety (RIC-349 / RIC-409)", "ESM-2 + Protraction Penaliser + Local vLLM Safety Gate + 175-Gene Dry/Wet", "BBB test AUC=0.89 (flagged protracted peptide CNS exclusion); 298 target-direction safety audits (0 gate errors); 175-gene HepG2 ATP/TMRM calibration.", "Production CLI / Service & Weekly Panels"),
    ("Proteome PPI & Interface Triage", "Cardiometabolic Data S6 99-Lead Dry-Run (RIC-410)", "RF2-PPI (6x A100) + 4-Criteria Triage + Boltz-2 omicMSA + A100 MD & FEP", "8/99 leads pass all 4/4 criteria (#1 RAMP3-MRAP2 ipTM=0.868, MD RMSD 0.49A); obesity SAVs R125/L115 are top FEP hotspots (+6.25/+5.21 kcal/mol).", "Exploratory Dry-Run Ready for Assay Check"),
]

tbl1_shape = s2.shapes.add_table(len(bench_rows), 5, Inches(0.45), Inches(4.70), Inches(12.43), Inches(2.30))
tbl1 = tbl1_shape.table
t1_widths = [1.75, 1.95, 2.55, 4.18, 2.00]
for ci, w_in in enumerate(t1_widths):
    tbl1.columns[ci].width = Inches(w_in)

for ri, rvals in enumerate(bench_rows):
    for ci, val in enumerate(rvals):
        cell = tbl1.cell(ri, ci)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.05)
        cell.margin_top = cell.margin_bottom = Inches(0.02)
        cell.fill.solid()
        if ri == 0:
            cell.fill.fore_color.rgb = TEAL
        elif ri == len(bench_rows) - 1:
            cell.fill.fore_color.rgb = GREEN_BG
        elif ri % 2 == 1:
            cell.fill.fore_color.rgb = WHITE
        else:
            cell.fill.fore_color.rgb = ICE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = val
        run.font.name = "Calibri"
        run.font.size = Pt(7.8 if ri == 0 else 7.1)
        run.font.bold = (ri == 0 or ci in (0, 1) or ri == len(bench_rows) - 1)
        run.font.color.rgb = WHITE if ri == 0 else (TEAL if ri == len(bench_rows) - 1 and ci == 0 else (NAVY if ci == 0 else INK))

set_notes(s2, """【Slide 2 口播讲稿：Druggability Agent 全管线系统能力全景与已验证项目（约 2 分钟）】
1. 为什么先看这张全景图？（顶部 Stage 1–6 工作流横幅）
   - 过去几个月，我们围绕心代与罕见病管线，已经把 `druggability` 建设成了一套覆盖 6 个阶段的端到端计算药理学平台：
     Stage 1（靶点遗传学与 3_safety 安全门禁）→ Stage 2（全蛋白组 PPI 与致病界面映射）→ Stage 3（多肽药理、脂化长效化与 BBB 穿透）→ Stage 4（隐性口袋、DrugCLIP 毫秒级初筛与靶点去卷积）→ Stage 5（A100 显式水 MD 与 FEP/TI 能量热点计算）→ Stage 6（自包含 3D WebGL 报告与湿实验突变设计）。
   - Baker 团队的 RF2-PPI 全蛋白组互作筛查补齐了我们在 Stage 2（发现未知内源调控伙伴/辅助受体）的拼图，而且它筛出的复合物可以直接无缝调用下游已经成熟的 Stage 4（界面对接）和 Stage 5（显式水 MD 与 FEP）。
2. 中间 6 张卡片与底部 6 个真实交付案例：
   - 底部表格列出了这套管线近期已经交付给生物团队的真实项目：包括交给 Mingyue 的 OXTR 催产素 >1,000 倍选择性与脂化出射角审计（RIC-403）、交给杨欢的 GPR81 抗潮红选择性与 FEP（RIC-396）、交给曹峥的 TSPO 五配体靶点钓钩与 CAR 核受体去卷积（RIC-408）、GIGYF1–GRB10 分子胶隐性口袋（RIC-407）、多肽 BBB 与 298 个靶点方向安全门禁（RIC-349/409），以及今天重点讨论的 PPI 模块（RIC-410）。""")


# ==============================================================================
# SLIDE 3: Module 2 Deep-Dive — Baker Engine Summary, In-House Validation & Caveats (~2 min)
# ==============================================================================
s3 = add_blank_slide()
add_header_footer(
    s3, 3, 6,
    "Module 2 Deep-Dive: Baker Engine Summary, A100 Validation & Reading Rules",
    "Consolidated Summary of Science 2025 / Sci Rep 2026, 33,000-Pair In-House Audit, and 4 Rigorous Caveats",
    "PART 2A: PPI ENGINE & IN-HOUSE VALIDATION"
)

# Top Two-Study Synthesis Banner (y=1.08, h=0.68)
rect(s3, 0.45, 1.08, 12.43, 0.68, LIGHT, line=BORDER)
rect(s3, 0.45, 1.08, 0.08, 0.68, NAVY)
text(s3, 0.65, 1.13, 12.10, 0.58, [
    [("What Baker & Cong Achieved (2025 Science vs 2026 Sci Rep Division of Labor — Details in Appendix S2): ", {"size": 9.6, "bold": True, "color": NAVY}),
     ("2025 Science built the engine (7x eukaryotic omicMSAs + 17x AFDB domain-contact training -> RF2-PPI, 20x faster than AF2) and screened 19,528 human proteins (~191M pairs -> 17,849 PPIs @90% prec; 3,631 novel; 2,700 zero-prior in Data S6). 2026 Sci Rep added no new screen; it mapped clinical disease SAVs onto 2025 3D interfaces & AF3 assemblies.",
      {"size": 8.8, "color": INK})]
])

# 4 KPI Cards (y=1.84, h=0.76)
kpis_s3 = [
    ("262x Enrichment", "Weighted AUCPR 0.262 vs 0.001", "1:1,000 proteome prior (1:1 AUC = 0.813)", NAVY),
    ("r = 0.919 Parity", "8,977 Shared Benchmark Pairs", "623 TPs & 0 FPs at >=90% precision", TEAL),
    ("43.2% vs 4.5%", "Large vs Small Interface Recall", ">1,500 A2 stable vs <800 A2 SLiMs", NAVY),
    ("~6 GPU-Hours", "Per Target Proteome Screen", "1 bait vs 20,260 proteins on 6x A100", RED),
]
kw3 = 2.92
kg3 = 0.25
kx3 = 0.45
for val, lbl, sub, col in kpis_s3:
    rect(s3, kx3, 1.84, kw3, 0.76, WHITE, line=BORDER)
    rect(s3, kx3, 1.84, kw3, 0.05, col)
    text(s3, kx3 + 0.06, 1.91, kw3 - 0.12, 0.65, [
        [(val, {"size": 14.0, "bold": True, "color": col})],
        [(lbl, {"size": 8.8, "bold": True, "color": INK})],
        [(sub, {"size": 7.6, "color": GREY})],
    ], align=PP_ALIGN.CENTER, space_after=1.5)
    kx3 += kw3 + kg3

# Left: High-DPI 2-Panel Evidence Plot (x=0.45, y=2.70, w=6.80, h=2.92)
IMG = "/das/user/QYJI/druggability/humanPPI_repro/results/repro_2panel_evidence.png"
rect(s3, 0.45, 2.70, 6.80, 2.92, WHITE, line=BORDER)
s3.shapes.add_picture(IMG, Inches(0.50), Inches(2.75), Inches(6.70), Inches(2.82))

# Right: Physical Mechanism + 4 Rigorous Reading Rules (x=7.42, y=2.70, w=5.46, h=2.92)
rect(s3, 7.42, 2.70, 5.46, 2.92, LIGHT, line=BORDER)
rect(s3, 7.42, 2.70, 5.46, 0.34, RED)
text(s3, 7.56, 2.75, 5.20, 0.24, "Physical Mechanism & 4 Rigorous Reading Rules (Do Not Overclaim)", size=10.2, bold=True, color=WHITE)

text(s3, 7.56, 3.10, 5.20, 2.46, [
    [("• Why Overall Recall is 20.8% (Panel B Mechanism [MECH]): ", {"size": 8.6, "bold": True, "color": NAVY}),
     ("Coevolution scales with contact area: 43.2% recall on large stable complexes (>1,500 A2; 51.8% @0.50) vs 4.5% on small transient SLiMs (<800 A2). 58% of Data S6 novel hits are transmembrane complexes.", {"size": 8.1, "color": INK})],
    [("• Rule 1 (Not 17.8k Blind Hits): ", {"size": 8.5, "bold": True, "color": RED}),
     ("14,218 of 17,849 PPIs combined prior evidence with lower cutoffs; 3,631 are novel (2,700 zero-prior in Data S6).", {"size": 8.0, "color": INK})],
    [("• Rule 2 ('No PDB Template' != Unknown Fold): ", {"size": 8.5, "bold": True, "color": RED}),
     ("Data S6 pairs lack homologous COMPLEX templates in PDB, not monomer structures.", {"size": 8.0, "color": INK})],
    [("• Rule 3 & 4 (Interface SAV & ipTM != Proven In Vivo Effect): ", {"size": 8.5, "bold": True, "color": RED}),
     ("Interface SAVs (<6A) and high pLDDT/ipTM propose testable structural hypotheses; they do not prove binding loss or tissue co-expression without wet-lab assays.", {"size": 8.0, "color": INK})],
], space_after=2.5)

# Bottom: Disease-Interface Module Verification on CASR (y=5.72, h=1.24)
rect(s3, 0.45, 5.72, 12.43, 1.24, GREEN_BG, line=TEAL, line_w=1.2)
rect(s3, 0.45, 5.72, 0.08, 1.24, TEAL)
text(s3, 0.65, 5.78, 12.10, 1.12, [
    [("In-House Disease-Interface Module (`druggability.interface_variants`, 22 Unit Tests) — Verified on CASR (P41180) [OBS]:",
      {"size": 9.8, "bold": True, "color": TEAL})],
    [("• Dual-Evidence Pathogenic Filter: Combines sequence alignment QC (<5% mismatch), UniProt clinical disease variants + EBI AlphaMissense pathogenicity, and 6 A CB/CA contact geometry.\n"
      "• CASR Proof-of-Concept (Tier-A CKD target in Data S6): Mapped 89 clinical pathogenic mutations (HHC1 / HYPOC1); 64% cluster directly at the extracellular dimerization interface (residues <=612), enabling automated nomination of point-mutant negative controls.",
      {"size": 8.8, "color": INK})]
], space_after=2)

set_notes(s3, """【Slide 3 口播讲稿（约 2 分钟，合并原 Slide 2+3，精简 Baker 文献背景并突出物理机制与 4 条科学红线）】
1. 顶部横幅（一句话讲清 Baker 两篇论文的关系，细节放 Appendix S2）：
   - 2025 Science 造出了计算引擎（7 倍深真核 omicMSA + 17 倍大 AFDB 结构域接触训练集 → 比 AF2 快 20 倍的 RF2-PPI），从 1.91 亿对人类蛋白中筛出 17,849 个 >=90% 精度的互作（含 2,700 个无同源复合物模板的 Data S6 新互作）；2026 Sci Rep 没有重训模型或重跑筛查，而是把临床致病突变（SAVs）映射到 2025 预测的 3D 界面上。
2. 左栏双图（我们在 6 张 A100 上的 33,000 对基准复现与物理机制）：
   - Panel A：在全蛋白组 1:1,000 极低信噪比下，随机盲筛 AUC 仅 0.001，我们本地复现达到 0.262（浓缩富集 262 倍，与原作者打分相关性 r=0.919）。
   - Panel B（核心物理机制）：为什么总体召回率是 20.8%？因为共进化信号取决于接触面积——对 >1,500 Å² 的大界面稳定复合物召回率达 43.2%（中等阈值 51.8%），而对 <800 Å² 的瞬时短基序（SLiMs）仅 4.5%。同时 Data S6 中 58% 是传统去垢剂 AP-MS 容易漏掉的跨膜蛋白复合物。
3. 右栏 4 条科学红线（曹峥梳理的防夸大界定）与底部 CASR 实测：
   - 明确 17,849 不全是盲筛新发现（3,631 个为新互作）、Data S6 无复合物模板不等于单体结构未知、界面突变和 ipTM 只提供可检验假设而非湿实验定论。底部展示我们在钙敏感受体 CASR 上实测，89 个临床致病突变中 64% 聚簇在二聚体界面。""")


# ==============================================================================
# SLIDE 4: Prospective Time-Split Validation (2024-2026) & Biological Fit Matrix (~1.5 min)
# ==============================================================================
s4 = add_blank_slide()
add_header_footer(
    s4, 4, 6,
    "Prospective Time-Split Validation (2024-2026) & Biological Fit Matrix",
    "11 Data S6 'Zero-Prior' Predictions Confirmed by Independent Wet Labs Since Cutoff + Operating Rules",
    "PART 2B: PROSPECTIVE PROOF & OPERATING BOUNDARIES"
)

# Left Panel: Prospective Time-Split Table (x=0.45, y=1.12, w=7.38, h=5.82)
rect(s4, 0.45, 1.12, 7.38, 5.82, LIGHT, line=BORDER)
rect(s4, 0.45, 1.12, 7.38, 0.36, TEAL)
text(s4, 0.61, 1.18, 7.05, 0.24,
     "Prospective Audit: Data S6 'Zero-Prior' Pairs Confirmed in 2024-2026 (11 Cases)",
     size=10.8, bold=True, color=WHITE)

text(s4, 0.61, 1.54, 7.05, 0.40,
     "Data S6 defined 2,700 novel pairs with zero DB (Sep 2023) & zero PDB complex template (Jan 2024) support. Over the subsequent two years, 11 pairs were independently validated by structures or co-IP (>50% are transmembrane/organelle complexes*):",
     size=8.6, color=INK)

rows_data = [
    ("Data S6 Novel Pair", "RF / AF / AFM", "2024-2026 Independent Publication", "Wet-Lab Validation & Biological Role"),
    ("DND1 - NANOS3", "0.52 / 0.97 / 1.00", "Mol Cell 2026 & Nat Commun 2025", "Cryo-EM/X-ray + co-IP: germ-granule RNA complex"),
    ("GPATCH1 - DHX35", "0.73 / 1.00 / 1.00", "Cell Research 2025 (PMID 40016598)", "Cryo-EM structure: spliceosomal quality-control B*Q"),
    ("NUP210 - TMEM209*", "0.28 / 0.99 / 0.99", "J Cell Sci 2026 (PMID 41582553)", "Endogenous co-IP + TMD rescue: 4th TM nucleoporin"),
    ("MTR - MMADHC*", "0.38 / 0.99 / 1.00", "PNAS 2026 (PMID 42709793)", "Co-IP + flux: B12 chaperone binds MTR in mitochondria"),
    ("EFCAB10 - AK8", "1.00 / 0.98 / 0.99", "PNAS 2025 (PMID 41055978)", "KO mice + co-IP: anchors AK8 to ciliary radial spoke"),
    ("TOR1A - CLCC1*", "0.81 / 0.93 / 0.93", "Mol Cells 2026 (PMID 42551441)", "Co-IP + rescue: ER Cl- channel in DYT1 dystonia"),
    ("GLMP - MFSD1* (+4 more)", "0.99 / 1.00 / 1.00", "Nat Cell Biol 2024 / EMBO Rep 2024", "Lysosomal transporter + PPTC7-FBXL4, TMEM131, SPARK"),
]

tbl_shape = s4.shapes.add_table(len(rows_data), 4, Inches(0.59), Inches(2.00), Inches(7.10), Inches(3.82))
tbl = tbl_shape.table
col_widths = [1.45, 1.15, 1.95, 2.55]
for ci, w_in in enumerate(col_widths):
    tbl.columns[ci].width = Inches(w_in)

for ri, rvals in enumerate(rows_data):
    for ci, val in enumerate(rvals):
        cell = tbl.cell(ri, ci)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.06)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        cell.fill.solid()
        if ri == 0:
            cell.fill.fore_color.rgb = NAVY
        elif ri % 2 == 1:
            cell.fill.fore_color.rgb = WHITE
        else:
            cell.fill.fore_color.rgb = ICE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if ci != 1 else PP_ALIGN.CENTER
        run = p.add_run()
        run.text = val
        run.font.name = "Calibri"
        run.font.size = Pt(8.5 if ri == 0 else 8.2)
        run.font.bold = (ri == 0 or ci == 0)
        run.font.color.rgb = WHITE if ri == 0 else (NAVY if ci == 0 else INK)

rect(s4, 0.59, 5.94, 7.10, 0.88, WHITE, line=BORDER)
rect(s4, 0.59, 5.94, 0.07, 0.88, NAVY)
text(s4, 0.75, 6.00, 6.84, 0.76, [
    [("Category B — Resolving Direct 3D Mechanism for Known AP-MS Hits: ", {"size": 8.8, "bold": True, "color": NAVY}),
     ("Beyond de novo Data S6 pairs, the 3D complex predictions resolved how NUDT5 allosterically blocks PPAT in purine synthesis (Science 2025, PMID 41196949) and how SMG5-SMG6 dimerizes in NMD (Nat Commun 2026) — turning noisy AP-MS hits into point-mutant-verified mechanisms. (* = Transmembrane / Organelle).",
      {"size": 8.1, "color": INK})]
])

# Right Panel: Biological Fit Matrix & Governance Rule (x=8.00, y=1.12, w=4.88, h=5.82)
rect(s4, 8.00, 1.12, 4.88, 5.82, LIGHT, line=BORDER)
rect(s4, 8.00, 1.12, 4.88, 0.36, RED)
text(s4, 8.16, 1.18, 4.55, 0.24,
     "Biological Fit Matrix & Campaign Governance",
     size=10.8, bold=True, color=WHITE)

rect(s4, 8.14, 1.60, 4.60, 1.88, GREEN_BG, line=TEAL, line_w=1.2)
rect(s4, 8.14, 1.60, 4.60, 0.28, TEAL)
text(s4, 8.26, 1.65, 4.35, 0.20, "IDEAL TARGETS (HIGH SENSITIVITY — USE HERE)", size=9.0, bold=True, color=WHITE)
text(s4, 8.26, 1.95, 4.35, 1.46, [
    [("• Transmembrane & Organelle Complexes (58% of S6):", {"size": 8.8, "bold": True, "color": TEAL})],
    [("  Hard to solubilize in detergent AP-MS (e.g., GPCR accessory proteins RAMP1/2/3, ER/lysosomal channels).", {"size": 8.2, "color": INK})],
    [("• Large Constitutive / Obligate Assemblies (>1,500 A2):", {"size": 8.8, "bold": True, "color": TEAL})],
    [("  43.2% recall at >=90% precision (51.8% at moderate cutoff).", {"size": 8.2, "color": INK})],
    [("• Disease-Mutated Interfaces (ClinVar / Human Genetics):", {"size": 8.8, "bold": True, "color": TEAL})],
    [("  Pinpoints exact contact residues to design disruptor controls.", {"size": 8.2, "color": INK})],
], space_after=1.5)

rect(s4, 8.14, 3.60, 4.60, 1.88, RED_BG, line=RED, line_w=1.2)
rect(s4, 8.14, 3.60, 4.60, 0.28, RED)
text(s4, 8.26, 3.65, 4.35, 0.20, "KNOWN BLIND SPOTS (DO NOT USE TO EXCLUDE)", size=9.0, bold=True, color=WHITE)
text(s4, 8.26, 3.95, 4.35, 1.46, [
    [("• Transient / PTM-Triggered Signaling Complexes:", {"size": 8.8, "bold": True, "color": RED})],
    [("  Phosphorylation- or ligand-dependent recruitment (e.g., GPCR-arrestin, kinase-substrate) lacks static coevolution.", {"size": 8.2, "color": INK})],
    [("• Disordered Short Linear Motifs (SLiMs, <800 A2):", {"size": 8.8, "bold": True, "color": RED})],
    [("  Only 4.5% recall at high precision (underrepresented in training).", {"size": 8.2, "color": INK})],
    [("• Fast-Evolving / Immune / Tissue-Restricted Paralogs:", {"size": 8.8, "bold": True, "color": RED})],
    [("  Coevolution reflects family conservation, not tissue specificity.", {"size": 8.2, "color": INK})],
], space_after=1.5)

rect(s4, 8.14, 5.60, 4.60, 1.22, AMBER_BG, line=AMBER, line_w=1.2)
rect(s4, 8.14, 5.60, 0.08, 1.22, AMBER)
text(s4, 8.32, 5.66, 4.32, 1.10, [
    [("Golden Rule (Lambourne et al., Nat Commun 2026):", {"size": 9.2, "bold": True, "color": AMBER})],
    [("1. Positive Hypothesis Generator Only: High score (@90% precision) + co-expression = strong wet-lab lead; low score NEVER disproves a biological hypothesis.\n"
      "2. Mandatory Tissue Co-Expression Gate: Always filter predicted pairs by GTEx / single-cell co-expression in the disease tissue.",
      {"size": 8.1, "color": INK})]
], space_after=2)

set_notes(s4, """【Slide 4 口播讲稿（约 1.5 分钟）】
1. 左栏（2024–2026 前瞻性时间切片盲测验证）：
   - Data S6 锁库截点是 2023 年 9 月。过去两年里，已有 11 个当年完全“零先验证据”的预测对被独立实验室用 Cryo-EM 或内源 co-IP 证实（如 DND1–NANOS3、GPATCH1–DHX35、核孔第 4 跨膜蛋白 NUP210–TMEM209、线粒体伴侣 MTR–MMADHC），且超过一半是传统去垢剂 AP-MS 容易漏掉的跨膜或细胞器膜蛋白。
2. 右栏（红绿适用边界与黄金治理法则）：
   - 绿色（高灵敏度适用区）：跨膜/细胞器复合物、大界面稳定复合物（>1,500 Å²）、带临床致病突变的结合界面。
   - 红色（盲区，绝不用作阴性排除）：磷酸化/配体诱导的瞬时招募（如 GPCR-arrestin）、无序短基序（SLiMs）、免疫受体与同源亚型。
   - 黄金法则：只作阳性假设生成与 3D 突变辅助设计，绝不用低分枪毙生物团队已有假设；进入湿实验前必须过靶器官共表达门禁。""")


# ==============================================================================
# SLIDE 5: Preliminary Campaign Plan — 3 Candidate Business Questions & Assay Gate (~1.5 min)
# ==============================================================================
s5 = add_blank_slide()
add_header_footer(
    s5, 5, 6,
    "Preliminary Campaign Plan: 3 Candidate Business Questions & Assay Gate",
    "Exploratory Planning Options & Stepwise Decision Gated on Downstream Wet-Lab Assay Readiness",
    "PART 3A: EXPLORATORY PLAN & ASSAY GATE"
)

# Top Planning-Stage Framing Banner (y=1.10, h=0.72)
rect(s5, 0.45, 1.10, 12.43, 0.72, AMBER_BG, line=AMBER, line_w=1.2)
rect(s5, 0.45, 1.10, 0.09, 0.72, AMBER)
text(s5, 0.68, 1.16, 12.05, 0.60, [
    [("Current Status — Exploratory Planning Stage (No Premature Scale-Up): ", {"size": 10.2, "bold": True, "color": AMBER}),
     ("While our computational pipeline (Modules 1-6) is ready, we are currently in the planning phase. Below are 3 candidate Business Questions (BQ-1 to BQ-3); actual campaign execution will be strictly gated on whether downstream wet-lab screening/validation assays are ready.",
      {"size": 9.2, "color": INK})]
])

# 3 Candidate Business Question Cards (y=1.94, h=3.68)
col_w5 = 3.98
gap5 = 0.245
bqs = [
    ("BQ-1: Portfolio Partner Mining",
     "Triage 99 Cardiometabolic Data S6 Leads",
     NAVY,
     [
         ("Candidate Question",
          "Among Baker's 2,700 zero-prior PPIs (Data S6), which novel interactors of our cardiometabolic targets pass strict 4-criteria triage (Genetics, Pathway, Perturbation, Co-expression)?"),
         ("Dry-Run Status (Completed)",
          "Audited 99 unflagged leads via Module 1 + Module 2 -> 8 leads pass all 4/4 criteria (led by #1 RAMP3-MRAP2 & #2 RAMP1-MRAP2; 14 pass 3/4)."),
         ("Required Wet-Lab Assay Gate",
          "Requires ready co-IP / NanoBiT / BRET or surface receptor trafficking assay in the relevant target biology team before nominating any wet-lab validation."),
     ]),
    ("BQ-2: On-Demand Bait Screen",
     "1 Priority Target vs 20,260 Human Proteins",
     TEAL,
     [
         ("Candidate Question",
          "When an internal project has a priority receptor/transporter where detergent AP-MS fails, can we screen 20,260 proteins (~6 GPU-h/bait) to find missing co-receptors, chaperones, or E3 ligases?"),
         ("Dry-Run Status (Capability Ready)",
          "6x A100 pipeline operational (~6 GPU-h per target bait); automatically filters hits by @90% precision cutoff and GTEx target-organ co-expression."),
         ("Required Wet-Lab Assay Gate",
          "Only triggered on-demand when a project team has both a clear biological bottleneck and a ready functional/binding readout to test top 3-5 predicted partners."),
     ]),
    ("BQ-3: 3D Interface & Controls",
     "Surgical Point-Mutant Negative Controls",
     RED,
     [
         ("Candidate Question",
          "When biologists already have a candidate partner or disease variant, where is the 6A contact surface and which single-residue mutations selectively disrupt binding without misfolding?"),
         ("Dry-Run Status (Verified on CASR & MRAP2)",
          "Runs in ~15 min/pair (`interface-variants`) + optional Module 5 explicit MD & FEP hotspot scan to rank energetic anchor residues (ddG in kcal/mol)."),
         ("Required Wet-Lab Assay Gate",
          "Directly supports teams already running mutagenesis / co-IP / BRET who need 2-3 surgical point-mutant negative controls instead of crude domain truncations."),
     ]),
]

bx5 = 0.45
for b_hdr, b_sub, b_col, b_rows in bqs:
    rect(s5, bx5, 1.94, col_w5, 3.68, WHITE, line=BORDER)
    rect(s5, bx5, 1.94, col_w5, 0.34, b_col)
    text(s5, bx5 + 0.12, 1.99, col_w5 - 0.24, 0.24, b_hdr, size=10.6, bold=True, color=WHITE)
    rect(s5, bx5, 2.28, col_w5, 0.28, LIGHT)
    text(s5, bx5 + 0.12, 2.32, col_w5 - 0.24, 0.20, b_sub, size=8.8, bold=True, color=b_col)
    paras = []
    for r_title, r_body in b_rows:
        paras.append([
            ("• " + r_title + ": ", {"size": 8.6, "bold": True, "color": b_col}),
            (r_body, {"size": 8.2, "color": INK})
        ])
    text(s5, bx5 + 0.12, 2.62, col_w5 - 0.24, 2.92, paras, space_after=4.5)
    bx5 += col_w5 + gap5

# Bottom Stepwise Assay-Readiness Decision Gate (y=5.74, h=1.22)
rect(s5, 0.45, 5.74, 12.43, 1.22, GREEN_BG, line=TEAL, line_w=1.2)
rect(s5, 0.45, 5.74, 0.09, 1.22, TEAL)
text(s5, 0.68, 5.80, 12.05, 1.10, [
    [("Proposed Stepwise Governance & Assay Readiness Gate (How We Decide Next Steps):", {"size": 9.8, "bold": True, "color": TEAL})],
    [("• Step 1 (Computational Dry-Run — Done): Completed 4-criteria triage on 99 cardiometabolic S6 leads + cross-module MD/FEP proof-of-concept on #1 RAMP3-MRAP2 (Slide 6).\n"
      "• Step 2 (Biology & Assay Readiness Check — Current Step): Review top candidates with biology leads to check (i) biological interest and (ii) whether screening/validation assays (co-IP, NanoBiT/BRET, cAMP, surface ELISA) are established and have capacity.\n"
      "• Step 3 (Go / No-Go Decision): Only launch focused wet-lab validation on 1-2 pairs where the assay is ready; hold broader proteome screens until assay bandwidth is confirmed.",
      {"size": 8.5, "color": INK})]
], space_after=1.5)

set_notes(s5, """【Slide 5 口播讲稿（约 1.5 分钟，重点突出“还在 Plan 阶段，一切以湿实验 Screening Assay 是否 Ready 为决策前提”）】
1. 顶部黄框（定调：克制、务实、不盲目铺摊子）：
   - 虽然我们第 2 页展示的计算管线（Module 1–6）已经全部就绪，但对于 PPI 这条线，我们目前明确处在**探索与规划阶段（Exploratory Planning Stage）**。
2. 中间三列（3 个候选的 Business Questions 及各自对应的湿实验门禁）：
   - **BQ-1（存量 99 对心代新伙伴挖掘）**：我们已经跑完了计算 Dry-Run（筛出 8 对全过 4/4 标准，见下一页 Slide 6），但下一步推不推，取决于对应靶点的生物团队手里有没有现成的 co-IP / BRET 或膜表面表达 Assay。
   - **BQ-2（按需 1-vs-20,260 全蛋白组筛查）**：单靶点只需 ~6 GPU 小时，但我们绝不盲目批量扫靶点，只有当某个重点项目（如难溶跨膜受体）遇到明确痛点、且下游已经准备好验证 Assay 时，才按需触发。
   - **BQ-3（3D 界面映射与点突变负对照设计）**：服务于已经在做 co-IP / 突变实验的生物学家，15 分钟加短轨迹 FEP 帮他们挑出 2–3 个不破坏整体折叠的精准点突变负对照。
3. 底部绿框（三步走决策门禁）：
   - Step 1（计算 Dry-Run 已完成）→ Step 2（当前阶段：跟生物团队核对哪些靶点的湿实验 Screening/Validation Assay 已经 Ready、通量如何）→ Step 3（仅针对 Assay 就绪的 1–2 个候选做小规模试水，再决定是否扩展）。""")


# ==============================================================================
# SLIDE 6: Dry-Run Proof-of-Concept — BQ-1 99-Lead Triage & RAMP3-MRAP2 Audit (~2 min)
# ==============================================================================
s6 = add_blank_slide()
add_header_footer(
    s6, 6, 6,
    "Dry-Run PoC: BQ-1 99-Lead Triage & RAMP3-MRAP2 Cross-Module Audit",
    "Illustrating How Modules 1-6 Work Together on a Candidate Pair Before Checking Wet-Lab Assay Readiness",
    "PART 3B: DRY-RUN EXAMPLE & ASSAY DISCUSSION"
)

# Left Column: 4-Criteria Funnel & Top 4/4 Ranked Leads Table (x=0.45, y=1.12, w=7.28, h=5.82)
rect(s6, 0.45, 1.12, 7.28, 5.82, LIGHT, line=BORDER)
rect(s6, 0.45, 1.12, 7.28, 0.36, NAVY)
text(s6, 0.61, 1.18, 6.95, 0.24,
     "BQ-1 Dry-Run: 4-Criteria Triage Across 99 Cardiometabolic Data S6 Leads",
     size=10.5, bold=True, color=WHITE)

f_pills = [
    ("C1: Genetics", "60/99 (46 Human)", NAVY),
    ("C2: Pathway", "43/99 Shared Path.", NAVY),
    ("C3: Perturb.", "14/99 Direct Evid.", TEAL),
    ("C4: Co-Prog.", "56/99 CM Co-Expr.", TEAL),
    ("8 Pass 4/4", "#1 RAMP3-MRAP2", RED),
]
pw = 1.29
pg = 0.12
px6 = 0.59
for p_val, p_sub, p_col in f_pills:
    rect(s6, px6, 1.55, pw, 0.58, WHITE, line=p_col, line_w=1.2)
    text(s6, px6 + 0.03, 1.60, pw - 0.06, 0.48, [
        [(p_val, {"size": 9.8, "bold": True, "color": p_col})],
        [(p_sub, {"size": 7.4, "bold": True, "color": INK})],
    ], align=PP_ALIGN.CENTER, space_after=1)
    px6 += pw + pg

lead_rows = [
    ("Rank & Pair (Tier)", "Indications", "RF / AF / AFM", "C1 Both-Protein Genetics & C2 Pathway", "C3 Direct Perturbation & C4 CM Co-Expr"),
    ("#1 RAMP3 - MRAP2 (Tier A, NN)", "Obesity; T2D; HF", "0.75 / 0.96 / 0.76", "RAMP3(T2D GWAS) + MRAP2(MC4R Obesity); GPCR path", "Co-IP & surface GPCR regulation (PMID 37085333); STRING coexpr=0.047"),
    ("#2 RAMP1 - MRAP2 (Tier A, NN)", "Obesity; T2D; HF", "0.78 / 0.91 / 0.82", "RAMP1(HCM GWAS) + MRAP2(MC4R Obesity); GPCR path", "Reciprocal GPCR trafficking perturbation (PMID 37085333); co-expressed"),
    ("#3 NR3C1 - FOXO3 (Tier B)", "T2D; Obesity; CKD", "0.31 / 0.93 / 0.95", "NR3C1(AFib GWAS=0.84) + FOXO3(Obesity=0.42); FOXO path", "Direct regulatory interaction (STRING exp=0.363); coexpr=0.102"),
    ("#4 CD80 - CSF3 (Tier C)", "MASH; CVD", "0.52 / 0.96 / 0.98", "CD80(Cirrhosis=0.28) + CSF3(AFib=0.14); Cytokine path", "STRING exp=0.062; shared MI & diabetes expression (coexpr=0.075)"),
    ("#5 TLR4 - LTBR (Tier C)", "T2D; MASH", "0.26 / 0.86 / 0.72", "TLR4(T2D GWAS=0.56) + LTBR(Cirrhosis=0.17); NF-kB path", "Consistent hub mRNA perturbation (PMID 37414270); coexpr=0.086"),
    ("#6 GP1BA - F2RL2 (Tier C)", "MASH; CKD; CVD", "0.25 / 0.85 / 0.73", "GP1BA(Liver=0.09) + F2RL2(GN=0.14); Hemostasis/GPCR", "STRING exp=0.069; shared myocardial infarction expression (coexpr=0.088)"),
    ("#7-#8 (KO Mouse): ITGA2B, IL18", "CVD; HF; T2D", "0.56 - 0.59 (Mean)", "ITGA2B-ACVRL1 (PAH GWAS=0.83) & IL18-CCL17 (CM=0.28)", "Plus 14 pairs passing 3/4 criteria (IL17A-FCN2, BRD3-KDM1A, TLR4-CTSS)"),
]

t2_shape = s6.shapes.add_table(len(lead_rows), 5, Inches(0.59), Inches(2.22), Inches(7.00), Inches(3.68))
t2 = t2_shape.table
t2_widths = [1.45, 0.92, 0.95, 1.78, 1.90]
for ci, w_in in enumerate(t2_widths):
    t2.columns[ci].width = Inches(w_in)

for ri, rvals in enumerate(lead_rows):
    for ci, val in enumerate(rvals):
        cell = t2.cell(ri, ci)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.04)
        cell.margin_top = cell.margin_bottom = Inches(0.02)
        cell.fill.solid()
        if ri == 0:
            cell.fill.fore_color.rgb = NAVY
        elif ri == 1:
            cell.fill.fore_color.rgb = GREEN_BG
        elif ri % 2 == 1:
            cell.fill.fore_color.rgb = WHITE
        else:
            cell.fill.fore_color.rgb = ICE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if ci not in (1, 2) else PP_ALIGN.CENTER
        run = p.add_run()
        run.text = val
        run.font.name = "Calibri"
        run.font.size = Pt(8.0 if ri == 0 else 7.4)
        run.font.bold = (ri in (0, 1) or ci == 0)
        run.font.color.rgb = WHITE if ri == 0 else (TEAL if ri == 1 and ci == 0 else (NAVY if ci == 0 else INK))

rect(s6, 0.59, 5.98, 7.00, 0.84, WHITE, line=BORDER)
rect(s6, 0.59, 5.98, 0.07, 0.84, AMBER)
text(s6, 0.75, 6.03, 6.75, 0.74, [
    [("Next Step — Check Screening / Validation Assay Readiness with Biology Teams: ", {"size": 8.6, "bold": True, "color": AMBER}),
     ("Before scaling up, check with GPCR/Cardiometabolic biology teams whether co-IP / BRET / cAMP assays for RAMP1/3-MRAP2 (or NR3C1-FOXO3) are established and whether testing 2-3 point-mutant controls fits current assay bandwidth.",
      {"size": 7.9, "color": INK})]
])

# Right Column: #1 Winner (RAMP3-MRAP2) Cross-Module Proof-of-Concept (x=7.90, y=1.12, w=4.98, h=5.82)
rect(s6, 7.90, 1.12, 4.98, 5.82, ICE, line=BORDER)
rect(s6, 7.90, 1.12, 4.98, 0.36, RED)
text(s6, 8.06, 1.18, 4.68, 0.24,
     "#1 Example (RAMP3-MRAP2): Cross-Module Pipeline Dry-Run",
     size=10.5, bold=True, color=WHITE)

BQ1_IMG = "/das/user/QYJI/druggability/reports/bq1_99_triage/bq1_99_triage_and_fep_2panel.png"
rect(s6, 8.04, 1.55, 4.70, 2.02, WHITE, line=BORDER)
s6.shapes.add_picture(BQ1_IMG, Inches(8.06), Inches(1.57), Inches(4.66), Inches(1.98))

rect(s6, 8.04, 3.65, 4.70, 3.17, WHITE, line=NAVY, line_w=1.2)
rect(s6, 8.04, 3.65, 4.70, 0.26, NAVY)
text(s6, 8.16, 3.69, 4.48, 0.20, "HOW MODULES 2, 3, 4, 5 & 6 CONVERGE ON ONE CANDIDATE", size=8.5, bold=True, color=WHITE)
text(s6, 8.16, 3.97, 4.48, 2.78, [
    [("• Mod 2 (Boltz-2 + omicMSA Complex):", {"size": 8.4, "bold": True, "color": NAVY})],
    [("  ipTM = 0.868, ptm = 0.834 (180 inter-chain contacts <=5A: 21 TM-TM + 159 ECD/juxtamembrane). RF2-PPI TM contact prob = 0.590 (RAMP3) / 0.865 (RAMP1).", {"size": 7.7, "color": INK})],
    [("• Mod 5 (A100 Explicit-Solvent MD & FEP Hotspots):", {"size": 8.4, "bold": True, "color": RED})],
    [("  Stable in A100 MD (backbone RMSD = 0.49 A). Human monogenic obesity SAVs MRAP2 R125C (ddG = +6.25 kcal/mol) & L115V (+5.21 kcal/mol) rank as #1 & #2 FEP hotspots.", {"size": 7.7, "color": INK})],
    [("• Mod 3/5 (AMY1R/3R Subunit Competition — Appendix S1):", {"size": 8.4, "bold": True, "color": NAVY})],
    [("  Cryo-EM (7TYF/7TZF) + 8-system MD show MRAP2 occupies 80% of RAMP3's CTR face (ddG = -23.4 kcal/mol vs CTR) and blocks Amylin 7TM entry (96->0 contacts).", {"size": 7.7, "color": INK})],
    [("• Mod 4 & 6 (Groove Docking & Assay-Ready Controls):", {"size": 8.4, "bold": True, "color": RED})],
    [("  Ubrogepant (-7.81 kcal/mol) & Rimegepant (ligand_ipTM=0.950) dock in ECD groove; MRAP2 L115A/R125A & RAMP3 W56A controls ready if wet-lab assay is available.", {"size": 7.7, "color": INK})],
], space_after=1.6)

set_notes(s6, """【Slide 6 口播讲稿（约 2 分钟，作为全管线协同的 Dry-Run 样板，并落脚到向生物团队征求 Assay 就绪度反馈）】
1. 左栏（BQ-1 99 对心代候选 4 维漏斗初筛）：
   - 按照曹峥设计的 4 条标准（C1 双蛋白心代遗传学 60 对[46 纯人类]、C2 共同通路 43 对、C3 直接扰动 14 对、C4 共表达 56 对），共有 8 对全部通过 4/4 标准（#1 RAMP3–MRAP2、#2 RAMP1–MRAP2、#3 NR3C1–FOXO3 等）。
2. 右栏（以 #1 RAMP3–MRAP2 展示我们 Slide 2 的六大模块如何在一个靶点对上协同发力）：
   - Module 2（共折叠）：Boltz-2 + omicMSA 给出高置信度复合物（ipTM=0.868，180 对残基接触）；
   - Module 5（A100 显式水 MD 与 FEP 突变热点）：复合物在显式水 MD 中极稳定（RMSD 0.49 Å）；更重要的是，人类单基因重度肥胖突变 MRAP2 R125C（+6.25 kcal/mol）和 L115V（+5.21 kcal/mol）恰好是结合面上最强的 #1 和 #2 能量热点；
   - Module 3/5（Amylin 受体竞争审计，详见 Appendix S1）：叠合 Cryo-EM 结构（7TYF/7TZF）与 8 体系 MD 显示，MRAP2 占据了 RAMP3 上 80% 的 CTR 结合面，并在四元复合物中阻断 Amylin 插入 7TM 口袋；
   - Module 4 & 6（凹槽对接与点突变负对照）：Ubrogepant/Rimegepant 选择性结合复合凹槽，并给出了 L115A/R125A/W56A 点突变负对照。
3. 左下黄框（开放性收尾，呼应领导要求）：
   - 以上是我们计算侧跑通的 Dry-Run 样板。下一步我们不急于扩大计算规模，而是想先请教组里做 GPCR / 心代生物学的同事：目前针对 RAMP1/3–MRAP2（或表里的其他候选），我们的湿实验 Screening / Validation Assay（比如 co-IP、BRET 或 cAMP 功能实验）是否 Ready？如果 Assay 现成，我们可以优先拿 1 个靶点对试水验证。感谢大家，欢迎讨论！""")


# ==============================================================================
# SLIDE 7 (APPENDIX S1): In Silico Test of MRAP2 Competition & Stability on Amylin Receptors
# ==============================================================================
s7 = add_blank_slide()
add_header_footer(
    s7, "APPENDIX S1", 6,
    "Appendix S1: Does MRAP2 Compete with Amylin or Destabilize AMY1R / AMY3R?",
    "Cryo-EM Superposition (7TYF/7TZF), Quaternary Boltz-2 Co-Folding, and 8-System A100 Explicit-Solvent MD",
    "SUPPLEMENTARY DEEP-DIVE (ZHCO FOLLOW-UP)",
    footer_left="References: Zhang et al., Science 390, eadt1630 (2025) | Pei, Zhang & Cong, Sci Rep 16:25590 (2026) | Cao et al., Science 375, eabm9601 (2022)"
)

rect(s7, 0.45, 1.12, 7.28, 5.82, LIGHT, line=BORDER)
rect(s7, 0.45, 1.12, 7.28, 0.36, NAVY)
text(s7, 0.61, 1.18, 6.95, 0.24,
     "Quantitative Comparison: Cryo-EM Baselines vs Subunit & Orthosteric Competition",
     size=10.3, bold=True, color=WHITE)

m_pills = [
    ("Cryo-EM Fact (7TYF/7TZF)", "98.5% Amylin ICs on CTR; RAMP W84/P85 caps Tyr37", NAVY),
    ("Mech 1: Subunit Competition", "80.0% RAMP3 & 75.7% RAMP1 CTR-face shared w/ MRAP2", TEAL),
    ("Mech 2: 7TM Pocket Block", "Amylin 7TM contacts drop 92->2 (AMY1R) & 96->0 (AMY3R)", RED),
]
mpw = 2.24
mpg = 0.14
mpx = 0.59
for m_val, m_sub, m_col in m_pills:
    rect(s7, mpx, 1.55, mpw, 0.56, WHITE, line=m_col, line_w=1.2)
    text(s7, mpx + 0.04, 1.60, mpw - 0.08, 0.46, [
        [(m_val, {"size": 8.6, "bold": True, "color": m_col})],
        [(m_sub, {"size": 6.9, "bold": True, "color": INK})],
    ], align=PP_ALIGN.CENTER, space_after=1)
    mpx += mpw + mpg

s7_rows = [
    ("System / Condition", "Chains Evaluated", "3D Overlap / 7TM Contacts", "A100 MD <dG_GBn2> & <E_vdW> (kcal/mol)", "Biophysical Conclusion"),
    ("Cryo-EM AMY1R (7TYF)", "CTR+RAMP1 : Amylin", "87 7TM + 48 ECD + 2 RAMP1 (W84/P85)", "<dG> = -221.3 ± 5.1 | <E_vdW> = -222.2", "Native AMY1R reference (RMSD 0.41A)"),
    ("Cryo-EM AMY3R (7TZF)", "CTR+RAMP3 : Amylin", "91 7TM + 45 ECD + 3 RAMP3 (E74/W84/P85)", "<dG> = -197.5 ± 7.1 | <E_vdW> = -227.7", "Native AMY3R reference (RMSD 0.48A)"),
    ("RAMP3 Subunit Comp.", "RAMP3:MRAP2 vs CTR", "32/40 (80.0%) CTR face shared; 222 clashes", "-212.9 (-254.0 vdW) vs -189.5 (-217.5)", "MRAP2 outcompetes CTR (ddG = -23.4)"),
    ("RAMP1 Subunit Comp.", "RAMP1:MRAP2 vs CTR", "28/37 (75.7%) CTR face shared; 172 clashes", "-156.8 (-198.5 vdW) vs -159.2 (-202.7)", "Comparable affinity; blocks AMY1R"),
    ("AMY1R Ternary (-MRAP2)", "CTR+RAMP1 : Amylin", "92 7TM + 73 ECD ICs (N-loop RMSD 1.27A)", "<dG> = -237.8 ± 6.7 | <E_vdW> = -269.5", "Deep 7TM orthosteric engagement"),
    ("AMY1R Quat. (+MRAP2)", "CTR+RAMP1+M : Amylin", "2 7TM ICs (-97.8%); displaced 21.7A", "<dG> = -113.5 | <E_vdW> = -149.6", "ddG = +124.3 | ddE_vdW = +119.9"),
    ("AMY3R -/+ MRAP2", "CTR+RAMP3(±M) : Amy", "96 -> 0 7TM ICs (-100%); displaced 24.5A", "-164.2 (-223.6) -> -148.9 (-163.1 vdW)", "ddG = +15.3 | ddE_vdW = +60.5"),
]

t7_shape = s7.shapes.add_table(len(s7_rows), 5, Inches(0.59), Inches(2.20), Inches(7.00), Inches(3.70))
t7 = t7_shape.table
t7_widths = [1.35, 1.15, 1.55, 1.55, 1.40]
for ci, w_in in enumerate(t7_widths):
    t7.columns[ci].width = Inches(w_in)

for ri, rvals in enumerate(s7_rows):
    for ci, val in enumerate(rvals):
        cell = t7.cell(ri, ci)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.04)
        cell.margin_top = cell.margin_bottom = Inches(0.02)
        cell.fill.solid()
        if ri == 0:
            cell.fill.fore_color.rgb = NAVY
        elif ri in (3, 6, 7):
            cell.fill.fore_color.rgb = GREEN_BG
        elif ri % 2 == 1:
            cell.fill.fore_color.rgb = WHITE
        else:
            cell.fill.fore_color.rgb = ICE
        p_cell = cell.text_frame.paragraphs[0]
        p_cell.alignment = PP_ALIGN.LEFT
        run = p_cell.add_run()
        run.text = val
        run.font.name = "Calibri"
        run.font.size = Pt(7.8 if ri == 0 else 7.2)
        run.font.bold = (ri == 0 or ci == 0 or (ri in (3, 6, 7) and ci == 3))
        run.font.color.rgb = WHITE if ri == 0 else (RED if ri in (6, 7) and ci == 0 else (NAVY if ci == 0 else INK))

rect(s7, 0.59, 5.98, 7.00, 0.84, WHITE, line=BORDER)
rect(s7, 0.59, 5.98, 0.07, 0.84, RED)
text(s7, 0.75, 6.03, 6.75, 0.74, [
    [("Testable Wet-Lab Hypothesis (If Amylin cAMP / BRET Assay is Ready): ", {"size": 8.6, "bold": True, "color": RED}),
     ("Co-expressing WT MRAP2 will competitively sequester RAMP3/RAMP1 away from CTR and attenuate amylin/cagrilintide potency, whereas our FEP-designed obesity point-mutants (MRAP2 L115A/V, R125A/C) will lose RAMP binding and restore normal AMY1R/AMY3R signaling.",
      {"size": 7.9, "color": INK})]
])

rect(s7, 7.90, 1.12, 4.98, 5.82, ICE, line=BORDER)
rect(s7, 7.90, 1.12, 4.98, 0.36, TEAL)
text(s7, 8.06, 1.18, 4.68, 0.24,
     "Dual-Mechanism Competition & A100 MD Energetics",
     size=10.5, bold=True, color=WHITE)

AMY_IMG = "/das/user/QYJI/druggability/reports/bq1_99_triage/amylin_mrap2_study/amylin_mrap2_competition_md_2panel.png"
rect(s7, 8.04, 1.55, 4.70, 2.02, WHITE, line=BORDER)
s7.shapes.add_picture(AMY_IMG, Inches(8.06), Inches(1.57), Inches(4.66), Inches(1.98))

rect(s7, 8.04, 3.65, 4.70, 3.17, WHITE, line=NAVY, line_w=1.2)
rect(s7, 8.04, 3.65, 4.70, 0.26, NAVY)
text(s7, 8.16, 3.69, 4.48, 0.20, "ANSWERS TO ZHENG'S TWO QUESTIONS (MECHANISM SUMMARY)", size=8.5, bold=True, color=WHITE)
text(s7, 8.16, 3.97, 4.48, 2.78, [
    [("1. Do Amylin and MRAP2 Compete in Binding to Amylin Receptors?", {"size": 8.5, "bold": True, "color": NAVY})],
    [("   YES — at two structural levels:\n"
      "   • Subunit Sequestration (MRAP2 vs CTR for RAMP1/3): MRAP2 occupies 80.0% (32/40) of RAMP3's and 75.7% (28/37) of RAMP1's CTR-binding residues, and binds RAMP3 more tightly than CTR in MD (ddG = -23.43 kcal/mol).\n"
      "   • Tyr37 Pocket Cap Occlusion: MRAP2 covers 100% of the RAMP1/3 Trp84-Pro85 shelf that caps amylin's C-terminal Tyr37-NH2.", {"size": 7.7, "color": INK})],
    [("2. Does MRAP2 Affect the Stability of Amylin / Receptor Complexes?", {"size": 8.5, "bold": True, "color": RED})],
    [("   YES — severe destabilization & 7TM ejection:\n"
      "   • In quaternary co-folding + MD, MRAP2 invades the CTR ECL2/ECL3/7TM entrance, reducing amylin's 7TM contacts by 97.8% in AMY1R (ddG = +124.26, ddE_vdW = +119.92 kcal/mol) and 100% in AMY3R (ddG = +15.26, ddE_vdW = +60.49 kcal/mol).", {"size": 7.7, "color": INK})],
], space_after=2.0)

set_notes(s7, """【Appendix S1（备查页 Slide 7）口播讲稿 — 回答关于 Amylin 受体竞争与稳定性的追问】
如果会上问到 RAMP1/3–MRAP2 是否会影响 Amylin 受体（AMY1R/AMY3R）组装或信号，翻出本页：
1. 亚基级直接竞争：MRAP2 占据了 RAMP3 上 80.0%（32/40）和 RAMP1 上 75.7%（28/37）原本结合 CTR 的残基，且 100% 盖住封盖 Amylin Tyr37 的 Trp84-Pro85 位点；显式水 MD 中 MRAP2 与 RAMP3 结合能（-212.9 kcal/mol）强于天然 CTR:RAMP3（-189.5 kcal/mol，ddG = -23.4 kcal/mol）。
2. 四元复合物正构口袋阻断：强行共折叠 + MD 时，MRAP2 堵住 CTR 正构口袋入口，使 Amylin 的 7TM 接触在 AMY1R 中丢失 97.8%（92→2，ddG = +124.3 kcal/mol），在 AMY3R 中 100% 归零（96→0，ddE_vdW = +60.5 kcal/mol）。""")


# ==============================================================================
# SLIDE 8 (APPENDIX S2): Detailed Two-Study Synthesis (2025 Science vs 2026 Sci Rep)
# ==============================================================================
s8 = add_blank_slide()
add_header_footer(
    s8, "APPENDIX S2", 6,
    "Appendix S2: Detailed Two-Study Comparison (2025 Science vs 2026 Sci Rep)",
    "5-Stage Proteome Screening Cascade (2025), Curated Disease-Variant Case Studies (2026), and Reading Rules",
    "SUPPLEMENTARY LITERATURE SYNTHESIS (ZHCO)"
)

rect(s8, 0.45, 1.10, 12.43, 0.84, LIGHT, line=BORDER)
rect(s8, 0.45, 1.10, 0.09, 0.84, NAVY)
text(s8, 0.68, 1.15, 12.05, 0.74, [
    [("How the Two Publications Connect (Figure 1-3 Synthesis):", {"size": 10.6, "bold": True, "color": NAVY})],
    [("• 1st Study (Zhang et al., Science 2025): Built the computational engine (`omicMSAs` + `RF2-PPI`) and screened the human proteome (19,528 proteins -> 17,849 PPIs @90% prec).\n"
      "• 2nd Study (Pei, Zhang & Cong, Sci Rep 2026): Did NOT retrain a model or run a new proteome screen; used the 2025 resource as input for curated case studies (interface disease variants & AlphaFold3 multi-subunit complexes).",
      {"size": 9.4, "color": INK})]
], space_after=1.5)

col_w8 = 3.98
gap8 = 0.245
pillars8 = [
    ("1st Study: 2025 Science", "Proteome-Scale Engine & Resource", NAVY, [
        ("Stage 1-2: 7x omicMSAs + RF2-PPI",
         "Assembled 21,415 eukaryotic species from 30 PB raw reads (7x deeper MSAs). Distilled 223,440 AFDB domain-domain contacts (17x larger training set) + negative pairs -> RF2-PPI (20x faster than AF2)."),
        ("Stage 3-4: 4-Tier Cascade Funnel",
         "20,296 proteins (19,528 screened; ~191M pairs) -> Localization filter (111.2M) -> DCA coevolution (43.6M) -> RF2-PPI (~1.9M) -> AF2 3D modeling."),
        ("Stage 5: Primary Resource Numbers",
         "29,256 PPIs (@80% prec) & 17,849 (@90% prec): 3,631 novel, 2,700 lacking complex templates (Data S6; 58% TM), 1,413 with uncharacterized proteins, 4,950 with interface SAVs, 404 complexes (+139 new subunits)."),
    ]),
    ("2nd Study: 2026 Sci Rep", "Curated Case Studies & AF3 Assemblies", TEAL, [
        ("Pathway Crosstalk & Dark Proteins",
         "1) PMS1-FAAP24: links DNA mismatch repair (MMR) to Fanconi anemia ICL repair. 2) C12orf57-ANKRD50: links dark protein C12orf57 to SNX27-retromer endocytic recycling."),
        ("Interface Disease Variant Cases",
         "1) C12orf57 L51Q: buried at ANKRD50 interface (Temtamy syndrome). 2) BBS7-WDR19 (V80D): disrupts BBSome-IFT-A ciliary contact in Senior-Loken ciliopathy. 3) SCO1 (P174L) - COA6 (W59C): co-localizes across interface in complex IV deficiency."),
        ("Higher-Order AF3 Complex Modeling",
         "Superimposed binary models + AlphaFold3: identified C19orf25 as a new NRZ tethering subunit, and modeled BLOC-1 / BORC / Sarcoglycan assemblies."),
    ]),
    ("4 Rigorous Reading Rules", "Critical Scientific Caveats (Do Not Overclaim)", RED, [
        ("1. Not a Pure Blind Discovery Set",
         "Of 17,849 PPIs (@90% prec), 14,218 combined prior physical/genetic evidence with lower cutoffs; 3,631 are novel (2,700 zero-prior in Data S6)."),
        ("2. 'No PDB Template' != Unknown Fold",
         "Data S6's 2,700 pairs lack homologous COMPLEX templates in PDB, NOT necessarily individual monomer structures."),
        ("3. Interface SAV != Proven Disruption",
         "4,950 PPIs carry disease SAVs at <6 A interfaces (and AFDB DDI training used predicted monomers). Proposes a testable hypothesis, not proof of binding loss."),
        ("4. pLDDT / ipTM != In Vivo Binding",
         "High structural confidence reflects fold/packing geometry, not tissue co-expression or physiological stoichiometry."),
    ]),
]

px8 = 0.45
for hdr_top, hdr_sub, col, items in pillars8:
    rect(s8, px8, 2.04, col_w8, 3.84, WHITE, line=BORDER)
    rect(s8, px8, 2.04, col_w8, 0.36, col)
    text(s8, px8 + 0.14, 2.09, col_w8 - 0.28, 0.25, hdr_top, size=11.0, bold=True, color=WHITE)
    rect(s8, px8, 2.40, col_w8, 0.30, ICE)
    text(s8, px8 + 0.14, 2.44, col_w8 - 0.28, 0.22, hdr_sub, size=9.6, bold=True, color=col)
    paras = []
    for it_title, it_desc in items:
        paras.append([
            ("• " + it_title + ": ", {"size": 8.9, "bold": True, "color": col}),
            (it_desc, {"size": 8.4, "color": INK})
        ])
    text(s8, px8 + 0.14, 2.76, col_w8 - 0.28, 3.04, paras, space_after=4.0)
    px8 += col_w8 + gap8

rect(s8, 0.45, 5.98, 12.43, 0.96, ICE, line=NAVY, line_w=1.0)
rect(s8, 0.45, 5.98, 0.09, 0.96, NAVY)
text(s8, 0.68, 6.06, 12.05, 0.80, [
    [("Exact 2025 Screening Cascade & Output Breakdown: ", {"size": 10.2, "bold": True, "color": NAVY}),
     ("20,296 human proteins -> 19,528 screened (~191M pairs) -> 111.2M localization-filtered -> 43.6M DCA-filtered -> ~1.9M RF2-PPI hits -> AF2 3D modeling -> 29,256 PPIs (@80% est. precision) & 17,849 PPIs (@90% est. precision) -> 3,631 unreported -> 2,700 lacking homologous complex templates (Data S6).",
      {"size": 9.4, "color": INK})]
])

set_notes(s8, """【Appendix S2（备查页 Slide 8）口播讲稿 — 供追问 Baker 2025 vs 2026 文献漏斗数字与案例细节时翻出】
保留完整的五级筛选漏斗数字（20,296 人类蛋白 → 19,528 入筛 [~1.91 亿对] → 1.112 亿共定位 → 4360 万 DCA → ~190 万 RF2-PPI → AF2 建模 → 29,256 [@80%] / 17,849 [@90%]）以及 2026 Sci Rep 的具体生物学案例（PMS1-FAAP24、C12orf57 L51Q、BBS7-WDR19 V80D、SCO1-COA6、C19orf25-NRZ），方便会中随时备查。""")

out_deck = "/das/user/QYJI/druggability/reports/ppi_group_meeting_deck_2026-10-29.pptx"
prs.save(out_deck)
print("Saved optimized 8-slide group meeting PPTX (6 main + 2 Appendix):", out_deck)
