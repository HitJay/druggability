#!/usr/bin/env python
"""Two-page proposal deck: Druggability Agent Platform Landscape & PPI Screening Campaign Proposal.

Re-balanced from the Baker-heavy single slide into a concise, systematic 2-page proposal:
  - Slide 1: End-to-End Druggability Agent Capability Landscape & Validated Benchmarks
             (6 core capability modules across target profiling, PPI interactome, peptide/BBB,
              virtual screening/target fishing, explicit MD/FEP, and 3D delivery + 6 real internal case studies)
  - Slide 2: Proteome-Wide PPI & Disease-Interface Screening Campaign Proposal
             (Streamlined Baker RF2-PPI/Sci Rep in-house validation & boundaries + 3 Campaign Business
              Questions & completed BQ-1 99-lead / RAMP3-MRAP2 pilot)

NN corporate palette (#001965 / #00857C / #D9383A). 16:9 widescreen (13.333 x 7.5 in).
100% pure English on slide canvas; biology-first Chinese oral script in speaker notes.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY = RGBColor(0x00, 0x19, 0x65)
TEAL = RGBColor(0x00, 0x85, 0x7C)
RED = RGBColor(0xD9, 0x38, 0x3A)
AMBER = RGBColor(0xB4, 0x53, 0x09)
INK = RGBColor(0x1A, 0x1A, 0x2E)
GREY = RGBColor(0x5A, 0x60, 0x70)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xE8, 0xEE, 0xF7)
BORDER = RGBColor(0xD0, 0xD7, 0xE5)
GREEN_BG = RGBColor(0xEB, 0xF7, 0xF5)
RED_BG = RGBColor(0xFD, 0xF2, 0xF2)
AMBER_BG = RGBColor(0xFE, 0xF3, 0xC7)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = 13.333, 7.5


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


def text(slide, x, y, w, h, runs, size=11, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=2, font="Calibri"):
    """runs: str, or list of paragraphs; each paragraph: str or list of (txt, {opts})."""
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


def add_header_footer(slide, page_num, total_pages, title, subtitle_left, subtitle_right, footer_text):
    rect(slide, 0, 0, W, H, WHITE)
    rect(slide, 0, 0, W, 0.96, NAVY)
    text(slide, 0.45, 0.14, 10.10, 0.36, title, size=17.2, bold=True, color=WHITE)
    text(slide, 0.45, 0.54, 10.10, 0.28, [
        [(subtitle_left + "  |  ", {"size": 10.2, "bold": True, "color": ICE}),
         (subtitle_right, {"size": 10.2, "color": ICE, "italic": True})]
    ])
    text(slide, 10.60, 0.18, 2.28, 0.54, [
        [(f"PAGE {page_num} OF {total_pages}  |  PROPOSAL", {"size": 10.2, "bold": True, "color": WHITE})],
        [("RIC-410  |  Novo Nordisk", {"size": 9.2, "color": ICE})]
    ], align=PP_ALIGN.RIGHT, space_after=2)
    rect(slide, 0.45, 7.08, W - 0.90, 0.01, BORDER)
    text(slide, 0.45, 7.12, 9.80, 0.26, footer_text, size=8.0, color=GREY)
    text(slide, 10.30, 7.12, 2.58, 0.26,
         f"druggability repo  |  Page {page_num}/{total_pages}",
         size=8.0, color=GREY, align=PP_ALIGN.RIGHT)


# ==============================================================================
# SLIDE 1: Druggability Agent Platform — Systematic Capability Landscape
# ==============================================================================
s1 = prs.slides.add_slide(prs.slide_layouts[6])
add_header_footer(
    s1, 1, 2,
    "Druggability Agent Platform: Systematic Capability Landscape & Benchmarks",
    "PART 1: END-TO-END COMPUTATIONAL PIPELINE",
    "From Target Genetics & PPI Interactome to Peptide/Small-Molecule Pharmacology, MD/FEP & 3D Delivery",
    "Platform: druggability repo (hpccnrd001 A100 Cluster)  |  Validated tickets: RIC-349, RIC-392, RIC-396, RIC-403, RIC-407, RIC-408, RIC-410"
)

# 1A. Top Workflow Pipeline Chevron Bar (6 End-to-End Stages) (y=1.08, h=0.50)
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
    rect(s1, sx, 1.08, sw, 0.48, ICE, line=st_col, line_w=1.1)
    rect(s1, sx, 1.08, 0.06, 0.48, st_col)
    text(s1, sx + 0.10, 1.12, sw - 0.14, 0.40, [
        [(st_hdr, {"size": 8.4, "bold": True, "color": st_col})],
        [(st_sub, {"size": 7.3, "color": INK})],
    ], space_after=1)
    if idx < len(stages) - 1:
        text(s1, sx + sw, 1.18, sgap, 0.26, "▸", size=10.5, bold=True, color=GREY, align=PP_ALIGN.CENTER)
    sx += sw + sgap

# 1B. Six Core Capability Pillar Cards (2 rows x 3 cols) (y=1.66, h=2.66 total)
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
        ("Alchemical FEP & Annihilation TI", "Dual-topology relative FEP & 8-lambda annihilation alanine-scanning TI to quantify residue/variant energetic hotspots (ddG in kcal/mol)."),
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
    rect(s1, cx, cy, cw, ch, WHITE, line=BORDER)
    rect(s1, cx, cy, cw, 0.24, c_col)
    text(s1, cx + 0.10, cy + 0.03, cw - 0.20, 0.18, c_title, size=8.6, bold=True, color=WHITE)
    rect(s1, cx, cy + 0.24, cw, 0.17, LIGHT)
    text(s1, cx + 0.10, cy + 0.25, cw - 0.20, 0.15, c_tag, size=7.1, bold=True, color=c_col, font="Consolas")
    paras = []
    for b_hdr, b_desc in c_bullets:
        paras.append([
            ("• " + b_hdr + ": ", {"size": 7.6, "bold": True, "color": c_col}),
            (b_desc, {"size": 7.3, "color": INK})
        ])
    text(s1, cx + 0.10, cy + 0.44, cw - 0.20, ch - 0.47, paras, space_after=1.5)

# 1C. Bottom Table: Production-Validated Internal Case Studies Across Modalities (y=4.42, h=2.58)
rect(s1, 0.45, 4.42, 12.43, 0.28, NAVY)
text(s1, 0.57, 4.46, 12.15, 0.20,
     "Production-Validated Portfolio Benchmarks Across Modalities (Real Executed Outputs & Wet-Lab Handovers)",
     size=9.2, bold=True, color=WHITE)

bench_rows = [
    ("Modality / Domain", "Project & Ticket", "Computational Stack Executed", "Headline Verified Biophysical / Biological Finding", "Deliverable & Status"),
    ("Peptide Selectivity & Protraction", "OXTR vs V1a/V1b/V2R & GLP-1R (RIC-403)", "Cryo-EM 7QVM/7DW9 + PRODIGY + A100 Explicit MD + 3D Lipidation Cone", "Explained >1,000x selectivity: Pro7Gly releases V2R TM1 clash (3.51A, 70.8A MD ejection); verified Leu8 C18-diacid exit vector (0 clashes, ~160h PK).", "3D HTML + 12-Slide Deck Delivered (Mingyue)"),
    ("Small-Molecule GPCR & FEP", "GPR81 (HCAR1) vs HCAR2/3 (RIC-396)", "45-Cmpd Vina + Boltz-2 Affinity + Steric Contradiction + 3-Leg OpenFEP", "Eliminated flushing liability via HCAR2 basic clash wall (+45.2 kcal/mol); proved AZ1 vs lactate mutual exclusion; converged c30/c31 FEP.", "3D HTML + 45-Cmpd Scorecard Delivered (UHYG)"),
    ("Ligand Target Fishing & TI", "TSPO 5-Ligand Panel (PK11195, Emapunil) (RIC-408)", "5-Source Curation + 17-Pocket Vina Gate + 250ps MD + 57-Anchor TI", "Proved CAR (NR1I3) is PK11195 #2 target (IC50 25-56 nM, 5 methods); discovered TSPO dimer pocket 4RYI_p26 (LEU58 +7.6 kJ/mol) & Cmax/Ki gate.", "6-Round Dossiers + 7-Slide Deck Delivered (ZHCO)"),
    ("Molecular Glue & Cryptic Pocket", "GIGYF1-GRB10/14 & GHSR VS (RIC-407 / RIC-392)", "Crystal 7RUQ/2AUH + UKB 454k WES Mutagenesis + 7,931-Cmpd Vina/Boltz-2", "Identified 445 A3 cryptic glue pocket at GIGYF1 interface; UKB p.Tyr498Cys drops affinity >80x (+2.74 kcal/mol, T2D OR=5.91); 20 GHSR chemotypes.", "3D Glue Dossier & Ranked Hits (GO Decision)"),
    ("Peptide CNS/BBB & Safety Gate", "MC4R / RORA BBB & 3_Safety (RIC-349 / RIC-409)", "ESM-2 + Protraction Penaliser + Local vLLM Safety Gate + 175-Gene Dry/Wet", "BBB test AUC=0.89 (flagged protracted peptide CNS exclusion); 298 target-direction safety audits (0 gate errors); 175-gene HepG2 ATP/TMRM calibration.", "Production CLI / Service & Weekly Panels"),
    ("Proteome PPI & Interface Triage", "Cardiometabolic Data S6 99-Lead Pilot (RIC-410)", "RF2-PPI (6x A100) + 4-Criteria Triage + Boltz-2 omicMSA + A100 MD & FEP", "8/99 leads pass all 4/4 criteria (#1 RAMP3-MRAP2 ipTM=0.868, MD RMSD 0.49A); obesity SAVs R125/L115 are top FEP hotspots (+6.25/+5.21 kcal/mol).", "Page 2 Proposal + 99-Pair Workbook (ZHCO)"),
]

tbl1_shape = s1.shapes.add_table(len(bench_rows), 5, Inches(0.45), Inches(4.70), Inches(12.43), Inches(2.30))
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

s1.notes_slide.notes_text_frame.text = """【Page 1 口播讲稿：Druggability Agent 全管线能力全景与已验证项目（约 2–3 分钟）】

1. 为什么要把 PPI 筛查放进整个 Druggability Agent 的系统版图里看？（顶部六步工作流横幅）
   - 过去几个月，我们围绕心代（Obesity/T2D/MASH/CKD/HF）与罕见病管线，已经把 `druggability` 仓库建设成了一套覆盖 6 个阶段的端到端计算药理学平台：
     Stage 1（靶点遗传学与安全门禁）→ Stage 2（全蛋白组 PPI 与致病界面映射）→ Stage 3（多肽工程与 BBB 穿透）→ Stage 4（隐性口袋、AI 超大库虚筛与靶点钓钩）→ Stage 5（A100 显式水 MD 与炼金术 FEP/TI）→ Stage 6（自包含 3D WebGL 报告与湿实验点突变设计）。
   - Baker 团队的 RF2-PPI 全蛋白组互作筛查不是一个孤立脚本，而是补齐了我们在 Stage 2（发现未知内源调控伙伴/辅助亚基）的关键拼图，并且它的输出可以直接无缝喂给下游的 Stage 4（界面凹槽对接）和 Stage 5（A100 显式水 MD 与 FEP 能量热点计算）。

2. 六大核心能力模块（中间 2×3 矩阵）：
   - 模块 1（靶点可药性、人类遗传学与安全画像）：整合 Open Targets GraphQL、ChEMBL 配体覆盖度、UKB 454k 外显子组罕见突变，以及本地 vLLM 驱动的 3_safety 双门禁安全评估（已完成 W40–W44 周度批次及 25 基因双向心代面板）。
   - 模块 2（全蛋白组 PPI 筛查与界面致病突变映射 [本次新增]）：6 张 A100 本地部署 RF2-PPI（单靶点扫 20,260 蛋白仅需 ~6 小时，浓缩富集 262 倍）+ Boltz-2 复合物共折叠 + 6 Å 界面临床突变映射（UniProt + AlphaMissense 双证据）。
   - 模块 3（多肽结构药理学与长效化/BBB 平台）：PRODIGY 接触亲和力、全序列丙氨酸/20 氨基酸突变扫描、C16/C18/C20 脂化长效化 3D 生长锥空间位阻审计，以及冻结 ESM-2 多任务轻量头（BBB 穿透 AUC=0.89，溶血毒性 AUC=1.00）。
   - 模块 4（口袋探测、AI 虚拟筛选与配体脱靶钓钩）：fpocket 全组装隐性口袋扫描 + DrugCLIP 对比学习毫秒级初筛（294 万分子库 ~22 秒）+ 紧盒子 AutoDock Vina（重对接 <2.0 Å 质控门禁）+ 结合临床游离暴露量 Cmax,u/Ki 的靶点去卷积。
   - 模块 5（A100 显式水分子动力学与炼金术 FEP/TI）：OpenMM 8.3 全原子显式水 MD（>2,100 ns/day）消除静态单构象真空腔伪影，叠加双拓扑相对 FEP 与 8-lambda 湮灭式丙氨酸扫描 TI，精准定量突变或残基的能量贡献（ddG）。
   - 模块 6（自包含 3D 交互交付与科学治理铁律）：零安装 3Dmol.js HTML + NN 规范 PPTX/PDF 双产物；严格区分 [FACT]/[OBS]/[MECH]/[HYP]，强制执行同源阴性对照（警惕 ipTM ≠ 结合效力）与“仅作阳性假设生成”治理原则。

3. 底部表格：六个模块均已在内部真实靶点项目上跑通并完成交付（OXTR 催产素选择性 RIC-403、GPR81 抗潮红选择性 RIC-396、TSPO 五配体靶点去卷积 RIC-408、GIGYF1-GRB10 分子胶隐性口袋 RIC-407、多肽 BBB 与安全门禁 RIC-349/409，以及本次的心代 Data S6 99 对 PPI 初筛 RIC-410）。
"""


# ==============================================================================
# SLIDE 2: Proteome-Wide PPI & Disease-Interface Campaign Proposal (Streamlined)
# ==============================================================================
s2 = prs.slides.add_slide(prs.slide_layouts[6])
add_header_footer(
    s2, 2, 2,
    "PPI & Disease-Interface Screening Campaign: Validation & Business Questions",
    "PART 2: MODULE 2 DEEP-DIVE & CAMPAIGN ALIGNMENT",
    "Concise Baker/Cong Summary, In-House A100 Validation, 3 Candidate Business Questions & BQ-1 Pilot",
    "References: Zhang et al., Science 390, eadt1630 (2025) | Pei, Zhang & Cong, Sci Rep 16:25590 (2026) | Lambourne et al., Nat Commun (2026)"
)

# ------------------------------------------------------------------------------
# 2A. Left Column: Concise Baker Summary, In-House Validation & Boundaries (x=0.45, w=5.85, y=1.10, h=5.88)
# ------------------------------------------------------------------------------
LP_X, LP_W = 0.45, 5.85
rect(s2, LP_X, 1.10, LP_W, 5.88, LIGHT, line=BORDER)
rect(s2, LP_X, 1.10, LP_W, 0.34, TEAL)
text(s2, LP_X + 0.14, 1.15, LP_W - 0.28, 0.24,
     "1. Baker Engine Summary, In-House Validation & Scope Boundaries",
     size=10.6, bold=True, color=WHITE)

# 4 Compact KPI Callout Cards (y=1.52, h=0.74)
kpis = [
    ("200M->17.8k", "Baker Interactome", "2,700 S6 novel (58% TM)", NAVY),
    ("262x Lift", "In-House 33k Audit", "AUCPR 0.262 (r=0.919)", TEAL),
    ("43.2% vs 4.5%", "Large vs SLiM Recall", ">1,500 A2 vs <800 A2", NAVY),
    ("~6 GPU-h", "Per-Bait Screen", "1 vs 20,260 on 6x A100", RED),
]
kw = 1.32
kgap = 0.10
kx = LP_X + 0.14
for val, lbl, sub, col in kpis:
    rect(s2, kx, 1.52, kw, 0.74, WHITE, line=BORDER)
    rect(s2, kx, 1.52, kw, 0.05, col)
    text(s2, kx + 0.03, 1.59, kw - 0.06, 0.64, [
        [(val, {"size": 12.2, "bold": True, "color": col})],
        [(lbl, {"size": 7.9, "bold": True, "color": INK})],
        [(sub, {"size": 6.8, "color": GREY})],
    ], align=PP_ALIGN.CENTER, space_after=1)
    kx += kw + kgap

# 2-Panel Evidence Plot (PR curve + Biological Interface Size Recall) (y=2.34, h=2.12)
IMG = "/das/user/QYJI/druggability/humanPPI_repro/results/repro_2panel_evidence.png"
img_w = LP_W - 0.28  # 5.57 in
rect(s2, LP_X + 0.14, 2.34, img_w, 2.12, WHITE, line=BORDER)
s2.shapes.add_picture(IMG, Inches(LP_X + 0.16), Inches(2.36), Inches(img_w - 0.04), Inches(2.08))

# Concise Summary Card (y=4.54, h=1.08)
rect(s2, LP_X + 0.14, 4.54, LP_W - 0.28, 1.08, WHITE, line=BORDER)
rect(s2, LP_X + 0.14, 4.54, 0.07, 1.08, NAVY)
text(s2, LP_X + 0.26, 4.58, LP_W - 0.44, 1.00, [
    [("• 2025 Science vs 2026 Sci Rep (FACT): ", {"size": 8.0, "bold": True, "color": NAVY}),
     ("2025 built omicMSAs (7x) + RF2-PPI (20x faster) -> 17,849 PPIs @90% prec (3,631 novel; 2,700 Data S6 lacking complex templates). 2026 mapped clinical SAVs onto 2025 3D interfaces.",
      {"size": 7.6, "color": INK})],
    [("• Prospective Proof & Caveats (OBS): ", {"size": 8.0, "bold": True, "color": TEAL}),
     ("11 Data S6 zero-prior pairs confirmed by cryo-EM/co-IP in 2024-2026 (e.g., TMEM209-NUP210, DND1-NANOS3). On CASR, 64% of 89 pathogenic SAVs map to the dimer interface (note: interface SAVs & ipTM require tissue co-expression + wet-lab validation).",
      {"size": 7.6, "color": INK})],
], space_after=2)

# Compact Green/Red Scope Matrix (y=5.70, h=1.18)
col_w2 = (LP_W - 0.38) / 2  # 2.735 in
rect(s2, LP_X + 0.14, 5.70, col_w2, 1.18, GREEN_BG, line=TEAL, line_w=1.0)
rect(s2, LP_X + 0.14, 5.70, col_w2, 0.21, TEAL)
text(s2, LP_X + 0.20, 5.72, col_w2 - 0.12, 0.17, "IDEAL TARGETS (HIGH SENSITIVITY)", size=7.8, bold=True, color=WHITE)
text(s2, LP_X + 0.20, 5.94, col_w2 - 0.12, 0.90, [
    [("• Large obligate complexes ", {"size": 7.4, "bold": True, "color": TEAL}),
     ("(43.2% recall >1,500 A2)", {"size": 7.2, "color": INK})],
    [("• Transmembrane / organelle PPIs ", {"size": 7.4, "bold": True, "color": TEAL}),
     ("(58% of S6; missed by AP-MS)", {"size": 7.2, "color": INK})],
    [("• Disease-mutated interfaces ", {"size": 7.4, "bold": True, "color": TEAL}),
     ("for disruptor control design", {"size": 7.2, "color": INK})],
    [("• Rule: Positive generator only ", {"size": 7.4, "bold": True, "color": NAVY}),
     ("(never exclude by low score)", {"size": 7.2, "color": INK})],
], space_after=1)

rx_left2 = LP_X + 0.14 + col_w2 + 0.10
rect(s2, rx_left2, 5.70, col_w2, 1.18, RED_BG, line=RED, line_w=1.0)
rect(s2, rx_left2, 5.70, col_w2, 0.21, RED)
text(s2, rx_left2 + 0.06, 5.72, col_w2 - 0.12, 0.17, "BLIND SPOTS (DO NOT EXCLUDE)", size=7.8, bold=True, color=WHITE)
text(s2, rx_left2 + 0.06, 5.94, col_w2 - 0.12, 0.90, [
    [("• Transient / PTM signaling ", {"size": 7.4, "bold": True, "color": RED}),
     ("(GPCR-arrestin, kinase-substrate)", {"size": 7.2, "color": INK})],
    [("• Disordered SLiMs (<800 A2) ", {"size": 7.4, "bold": True, "color": RED}),
     ("(only 4.5% recall at @90% prec)", {"size": 7.2, "color": INK})],
    [("• Immune / TCR-MHC & paralogs ", {"size": 7.4, "bold": True, "color": RED}),
     ("(needs GTEx co-expression gate)", {"size": 7.2, "color": INK})],
    [("• Multi-Platform Synergy: ", {"size": 7.4, "bold": True, "color": NAVY}),
     ("Route hits -> Module 4/5 MD & FEP", {"size": 7.2, "color": INK})],
], space_after=1)

# ------------------------------------------------------------------------------
# 2B. Right Column Top: 3 Candidate Business Questions (x=6.48, w=6.40, y=1.10, h=2.46)
# ------------------------------------------------------------------------------
RP_X, RP_W = 6.48, 6.40
rect(s2, RP_X, 1.10, RP_W, 2.46, ICE, line=BORDER)
rect(s2, RP_X, 1.10, RP_W, 0.34, NAVY)
text(s2, RP_X + 0.14, 1.15, RP_W - 0.28, 0.24,
     "2. Campaign Business Question Menu (Connecting Module 2 -> Modules 1, 4, 5 & 6)",
     size=10.6, bold=True, color=WHITE)

bq_cards = [
    ("BQ-1: Portfolio Partner Mining", "99 Data S6 Leads -> 8 Pass 4/4",
     "Triage 99 unflagged cardiometabolic Data S6 leads via Module 1 genetics/co-expression + Module 2 3D SAVs + Module 5 MD/FEP -> nominate top pairs for co-IP/BRET.",
     NAVY),
    ("BQ-2: De Novo Target Screen", "1 Priority Bait vs 20,260 Proteins",
     "For orphan/transmembrane receptors or intracellular targets where AP-MS fails, screen 20,260 proteins (~6 GPU-h/bait) for missing co-receptors, chaperones, or E3 ligases.",
     TEAL),
    ("BQ-3: 3D Interface & Controls", "Disruptor Mutants & Groove VS",
     "Map 6A contact surfaces & clinical pathogenic SAVs (`interface-variants`, ~15 min/pair) to design surgical point-mutant negative controls and dock modulators (Module 4).",
     RED),
]
bw_box = 1.96
bgap = 0.12
bx = RP_X + 0.14
for bq_hdr, bq_sub, bq_body, bq_col in bq_cards:
    rect(s2, bx, 1.50, bw_box, 1.50, WHITE, line=BORDER)
    rect(s2, bx, 1.50, bw_box, 0.24, bq_col)
    text(s2, bx + 0.04, 1.53, bw_box - 0.08, 0.18, bq_hdr, size=7.9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    rect(s2, bx, 1.74, bw_box, 0.20, LIGHT)
    text(s2, bx + 0.04, 1.76, bw_box - 0.08, 0.16, bq_sub, size=7.4, bold=True, color=bq_col, align=PP_ALIGN.CENTER)
    text(s2, bx + 0.06, 1.97, bw_box - 0.12, 1.00, bq_body, size=7.2, color=INK, align=PP_ALIGN.LEFT)
    bx += bw_box + bgap

# End-to-End Handoff Strip inside Section 2 (y=3.06, h=0.44)
rect(s2, RP_X + 0.14, 3.06, RP_W - 0.28, 0.44, WHITE, line=BORDER)
rect(s2, RP_X + 0.14, 3.06, 0.07, 0.44, NAVY)
text(s2, RP_X + 0.26, 3.10, RP_W - 0.44, 0.36, [
    [("End-to-End Wet-Lab Handoff Package (~6 GPU-h / Bait): ", {"size": 7.6, "bold": True, "color": NAVY}),
     ("(1) Calibrated partner probability (@90% precision) + GTEx co-expression, (2) 3D complex coordinates & 6A contact residues, and (3) FEP-verified interface SAV point-mutant negative controls for co-IP / BioID / BRET.",
      {"size": 7.2, "color": INK})]
])

# ------------------------------------------------------------------------------
# 2C. Right Column Bottom: Completed Phase-1 Pilot (BQ-1 99-Lead Triage + RAMP3-MRAP2 Multi-Module Deep-Dive) (y=3.66, h=3.32)
# ------------------------------------------------------------------------------
rect(s2, RP_X, 3.66, RP_W, 3.32, LIGHT, line=BORDER)
rect(s2, RP_X, 3.66, RP_W, 0.34, RED)
text(s2, RP_X + 0.14, 3.71, RP_W - 0.28, 0.24,
     "3. Executed Phase-1 Pilot: BQ-1 99-Pair Triage + RAMP3-MRAP2 Full-Pipeline Audit",
     size=10.6, bold=True, color=WHITE)

# Left sub-box inside 2C:BQ1_IMG (x=RP_X+0.14, y=4.08, w=3.05, h=1.42) + 8 Winners List below (y=5.56, h=1.32)
BQ1_IMG = "/das/user/QYJI/druggability/reports/bq1_99_triage/bq1_99_triage_and_fep_2panel.png"
rect(s2, RP_X + 0.14, 4.08, 3.05, 1.42, WHITE, line=BORDER)
s2.shapes.add_picture(BQ1_IMG, Inches(RP_X + 0.16), Inches(4.10), Inches(3.01), Inches(1.38))

rect(s2, RP_X + 0.14, 5.56, 3.05, 1.32, WHITE, line=NAVY, line_w=1.0)
rect(s2, RP_X + 0.14, 5.56, 3.05, 0.21, NAVY)
text(s2, RP_X + 0.20, 5.58, 2.93, 0.17, "BQ-1 4-CRITERIA TRIAGE (99 LEADS -> 8 PASS 4/4)", size=7.4, bold=True, color=WHITE)
text(s2, RP_X + 0.20, 5.80, 2.93, 1.04, [
    [("• Funnel: ", {"size": 7.3, "bold": True, "color": NAVY}),
     ("C1 Both-Genetics 60 (46 Human), C2 Pathway 43, C3 Direct Perturb 14, C4 CM Co-expr 56 -> 8 pass 4/4 (+14 pass 3/4).", {"size": 7.1, "color": INK})],
    [("• Top 6 Pure-Human 4/4 Winners: ", {"size": 7.3, "bold": True, "color": TEAL}),
     ("#1 RAMP3-MRAP2, #2 RAMP1-MRAP2 (Amylin/CagriSema axis), #3 NR3C1-FOXO3, #4 CD80-CSF3, #5 TLR4-LTBR, #6 GP1BA-F2RL2.", {"size": 7.1, "color": INK})],
], space_after=1.5)

# Right sub-box inside 2C: How All 6 Modules Converged on #1 RAMP3-MRAP2 (x=RP_X+3.27, y=4.08, w=2.99, h=2.80)
rx_pilot = RP_X + 3.27
rw_pilot = 2.99
rect(s2, rx_pilot, 4.08, rw_pilot, 2.80, WHITE, line=TEAL, line_w=1.1)
rect(s2, rx_pilot, 4.08, rw_pilot, 0.22, TEAL)
text(s2, rx_pilot + 0.08, 4.10, rw_pilot - 0.16, 0.18, "#1 RAMP3-MRAP2: CROSS-MODULE PROOF", size=7.6, bold=True, color=WHITE)
text(s2, rx_pilot + 0.08, 4.34, rw_pilot - 0.16, 2.50, [
    [("• Mod 2 (Boltz-2 + omicMSA): ", {"size": 7.4, "bold": True, "color": NAVY}),
     ("Tightly packed TM+ECD complex (ipTM=0.868, 180 contacts <=5A; TM contact prob=0.590/0.865).", {"size": 7.1, "color": INK})],
    [("• Mod 5 (A100 MD & FEP Hotspots): ", {"size": 7.4, "bold": True, "color": RED}),
     ("Stable in explicit-solvent MD (RMSD 0.49A). Human monogenic obesity SAVs MRAP2 R125C (+6.25 kcal/mol) & L115V (+5.21 kcal/mol) are #1/#2 FEP hotspots.", {"size": 7.1, "color": INK})],
    [("• Mod 3/5 (AMY1R/3R Competition): ", {"size": 7.4, "bold": True, "color": NAVY}),
     ("Cryo-EM (7TYF/7TZF) + 8-system MD show MRAP2 shares 80% of RAMP3's CTR face (ddG=-23.4 kcal/mol vs CTR) & blocks Amylin 7TM entry (96->0 contacts).", {"size": 7.1, "color": INK})],
    [("• Mod 4 (Groove Virtual Screen): ", {"size": 7.4, "bold": True, "color": RED}),
     ("Ubrogepant (-7.81 kcal/mol) & Rimegepant (ternary ligand_ipTM=0.950) selectively bind the composite RAMP3-MRAP2 ECD groove.", {"size": 7.1, "color": INK})],
    [("• Mod 6 (Wet-Lab Assay Controls): ", {"size": 7.4, "bold": True, "color": NAVY}),
     ("Delivered MRAP2 L115A/V, R125A/C & RAMP3 W56A point-mutant controls to test AMY1R/3R rescue in co-IP / BRET / cAMP.", {"size": 7.1, "color": INK})],
], space_after=1.5)

s2.notes_slide.notes_text_frame.text = """【Page 2 口播讲稿：全蛋白组 PPI 与疾病界面筛查专项 Proposal 及跨模块联动实例（约 2.5 分钟）】

1. 左栏：精炼总结 Baker & Cong 团队突破、内部复现与能力边界（回应领导问题 1）
   - 2025 Science 造出了全蛋白组引擎（7 倍深真核 omicMSA + 17 倍大 AFDB 训练集训出 RF2-PPI，比 AF2 快 20 倍），从 1.91 亿对人类蛋白中筛出 17,849 个 >=90% 精度的 PPI（含 2,700 个无复合物模板的 Data S6 新互作，58% 为跨膜蛋白）；2026 Sci Rep 在此结构基础上映射临床致病突变（SAVs）。
   - 我们在 6 张 A100 上完整复现了 33,000 对基准集：在 1:1000 真实极低信噪比下浓缩富集 262 倍（AUCPR=0.262，与作者打分相关性 r=0.919）；物理机制上，大界面稳定复合物（>1500 Å²）召回率达 43.2%，而小界面短基序（SLiMs <800 Å²）仅 4.5%。此外，Data S6 发布两年来已有 11 个零先验预测对被独立实验室用 Cryo-EM 或 co-IP 证实。
   - 左下红绿矩阵明确了治理边界：专攻跨膜与大界面稳定复合物，绝不用低分排除瞬时信号或短基序假设；所有高分命中直接联动本管线 Module 4（对接）和 Module 5（A100 显式水 MD / FEP）做动力学验证。

2. 右上：三项候选 Business Questions（回应领导问题 2，并与全管线各模块打通）
   - BQ-1（存量管线靶点新伙伴挖掘）：对 Data S6 中 99 个未标记心代候选对，串联 Module 1（双蛋白遗传学/共表达）+ Module 2（3D 界面突变）+ Module 5（MD/FEP）筛出 Top 候选交湿实验。
   - BQ-2（疑难/跨膜靶点全蛋白组从头筛查）：生物团队给 1 个靶点 UniProt ID，~6 GPU 小时扫完 20,260 个人类蛋白，寻找去垢剂 AP-MS 漏掉的辅助受体、伴侣或组织特异 E3 连接酶。
   - BQ-3（3D 致病界面映射与点突变负对照设计）：15 分钟内给出 6 Å 接触面与 ClinVar/AlphaMissense 致病突变，直接设计不破坏整体折叠的 co-IP/BRET 点突变负对照。

3. 右下：BQ-1 首期 Pilot 执行结果（展示第 1 页六大模块如何在一个真实项目上闭环发力）
   - 左下：99 个心代 Data S6 候选对经严格 4 维标准（C1 双蛋白遗传 60 对[46 纯人类]、C2 共同通路 43 对、C3 直接扰动 14 对、C4 共表达 56 对）筛选，8 对全部通过 4/4 标准（#1 RAMP3–MRAP2、#2 RAMP1–MRAP2 领衔）。
   - 右下（#1 RAMP3–MRAP2 全管线六模块协同验证）：
     • Module 2（结构共折叠）：Boltz-2 + omicMSA 给出高置信跨膜+胞外复合物（ipTM=0.868，180 对接触）；
     • Module 5（A100 显式水 MD + FEP 突变扫描）：主链 RMSD 0.49 Å 极稳定；人类单基因肥胖突变 MRAP2 R125C（+6.25 kcal/mol）与 L115V（+5.21 kcal/mol）恰好是结合面 #1 和 #2 能量热点；
     • Module 3/5（受体亚基竞争与稳定性）：叠合 Cryo-EM（7TYF/7TZF）与 8 体系显式水 MD 证实，MRAP2 占据 RAMP3 上 80% 的 CTR 结合面（比 CTR 结合更强，ddG=-23.4 kcal/mol），并在四元复合物中阻断 Amylin 插入 7TM 正构口袋（跨膜接触从 96 降至 0）；
     • Module 4 & 6（凹槽对接与湿实验交付）：Ubrogepant（-7.81 kcal/mol）与 Rimegepant（三元 ligand_ipTM=0.950）选择性结合复合凹槽；已交付 MRAP2 L115A/R125A 与 RAMP3 W56A 点突变负对照供湿实验测试。
"""

out_pptx = "/das/user/QYJI/druggability/reports/ppi_screening_proposal_2026-10-28.pptx"
prs.save(out_pptx)
print("Saved 2-page systematic capability & PPI proposal PPTX:", out_pptx)
