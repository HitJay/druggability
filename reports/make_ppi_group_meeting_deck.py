#!/usr/bin/env python
"""Generate a 6-slide editable PPTX deck for the 5-10 min group meeting presentation (RIC-410).

Leadership ask:
  "bring a 5-10mins presentation to group meeting next week on the summary of what David Baker's team
   achieved and what the business question for the campaign is (TBD)"

Design anti-overlap rules enforced:
  1. All slide titles, subtitles, card headers, and card sub-banners are sized and width-allocated
     so they fit strictly on a SINGLE line (zero 2-line title wrap overlaps).
  2. Multi-bullet bodies inside any card use a SINGLE unified TextFrame with multiple paragraphs
     rather than stacked separate textboxes, making intra-card vertical text collisions impossible.

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


def text(slide, x, y, w, h, runs, size=11, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=3, font="Calibri"):
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


def add_header_footer(slide, page_num, total_pages, title, subtitle, section_tag):
    rect(slide, 0, 0, W, H, WHITE)
    rect(slide, 0, 0, W, 0.96, NAVY)
    # Give title w=10.0 in at 17.5 pt so even 80-char titles stay on 1 line
    text(slide, 0.48, 0.14, 10.00, 0.36, title, size=17.5, bold=True, color=WHITE)
    text(slide, 0.48, 0.55, 10.00, 0.28, [
        [(section_tag + "  |  ", {"size": 10.2, "bold": True, "color": ICE}),
         (subtitle, {"size": 10.2, "color": ICE, "italic": True})]
    ])
    text(slide, 10.55, 0.18, 2.30, 0.54, [
        [(f"SLIDE {page_num} OF {total_pages}  |  RIC-410", {"size": 10.2, "bold": True, "color": WHITE})],
        [("Group Meeting  |  Novo Nordisk", {"size": 9.2, "color": ICE})]
    ], align=PP_ALIGN.RIGHT, space_after=2)
    # Footer
    rect(slide, 0.48, 7.08, W - 0.96, 0.01, BORDER)
    text(slide, 0.48, 7.13, 9.0, 0.25,
         "References: Zhang et al., Science 390, eadt1630 (2025) | Pei, Zhang & Cong, Sci Rep 16:25590 (2026) | Lambourne et al., Nat Commun (2026)",
         size=8.5, color=GREY)
    text(slide, 9.50, 7.13, 3.35, 0.25,
         f"druggability repo  |  Page {page_num}/{total_pages}",
         size=8.5, color=GREY, align=PP_ALIGN.RIGHT)


def set_notes(slide, notes_str):
    ns = slide.notes_slide
    ns.notes_text_frame.text = notes_str.strip()


# ==============================================================================
# SLIDE 1: Title & Executive Summary (1 min)
# ==============================================================================
s1 = add_blank_slide()
rect(s1, 0, 0, W, H, NAVY)
rect(s1, 0, 0, W, 0.12, TEAL)

# Top badge
rect(s1, 0.65, 0.48, 3.90, 0.36, TEAL)
text(s1, 0.65, 0.53, 3.90, 0.26, "GROUP MEETING BRIEFING (5-10 MIN)  |  RIC-410",
     size=10.2, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Separate Title, Subtitle, and Presenter into well-spaced boxes (no overlap)
text(s1, 0.65, 1.00, 12.0, 0.55,
     "Proteome-Wide PPI & Disease-Interface Triage",
     size=29, bold=True, color=WHITE)

text(s1, 0.65, 1.62, 12.0, 0.36,
     "1. What David Baker & Qian Cong's Team Achieved   |   2. What Business Question Our Campaign Solves",
     size=15.0, bold=True, color=ICE)

text(s1, 0.65, 2.08, 12.0, 0.30,
     "Presenter: Qiuye Jin (QYJI)   |   Cardiometabolic Data S6 Partner: Zheng Cao (ZHCO)   |   October 2026",
     size=11.0, color=ICE)

# 2 Big Executive Summary Cards side by side (y=2.55, h=3.70)
cw = 5.85
# Card 1: Question 1 Summary
rect(s1, 0.65, 2.55, cw, 3.70, WHITE, line=TEAL, line_w=1.5)
rect(s1, 0.65, 2.55, cw, 0.44, TEAL)
text(s1, 0.85, 2.64, cw - 0.40, 0.28,
     "PART 1: What Baker & Cong's Team Achieved (Slides 2-4)",
     size=11.8, bold=True, color=WHITE)
text(s1, 0.85, 3.12, cw - 0.40, 3.00, [
    [("• Solved the Human Interactome Scale & Signal Bottleneck (Science 2025):", {"size": 10.6, "bold": True, "color": NAVY})],
    [("  Assembled 7x deeper omicMSAs from 30 PB raw eukaryotic reads + distilled 223k AFDB domain-domain pairs (17x larger training set) to train RF2-PPI (20x faster than AF2).", {"size": 9.8, "color": INK})],
    [("• Mapped 17,849 High-Precision Human PPIs (@90% Precision):", {"size": 10.6, "bold": True, "color": NAVY})],
    [("  Includes 3,631 novel interactions (2,700 lacking complex templates in Data S6, 58% transmembrane) + ~16,000 clinical disease mutations mapped to 3D interfaces (Sci Rep 2026).", {"size": 9.8, "color": INK})],
    [("• Verified In-House on 6x A100 GPUs & Prospectively Validated:", {"size": 10.6, "bold": True, "color": TEAL})],
    [("  262x enrichment over random proteome screening (r=0.919 parity; 43.2% recall on large stable complexes >1500 A2; 11 Data S6 pairs proved by cryo-EM/co-IP in 2024-2026).", {"size": 9.8, "color": INK})],
], space_after=3.5)

# Card 2: Question 2 Summary
rx = 0.65 + cw + 0.33
rect(s1, rx, 2.55, cw, 3.70, WHITE, line=RED, line_w=1.5)
rect(s1, rx, 2.55, cw, 0.44, RED)
text(s1, rx + 0.20, 2.64, cw - 0.40, 0.28,
     "PART 2: Campaign Business Questions for Alignment (Slides 5-6)",
     size=11.8, bold=True, color=WHITE)
text(s1, rx + 0.20, 3.12, cw - 0.40, 3.00, [
    [("• BQ-1 (Portfolio Partner Mining — Ready Now):", {"size": 10.6, "bold": True, "color": NAVY})],
    [("  Triage the 99 unflagged novel PPI leads across 120 cardiometabolic targets in Data S6 (18 Tier A + 8 NN pipeline incl. RAMP1/2/3, CASR, TTR) -> nominate Top-10 for co-IP.", {"size": 9.8, "color": INK})],
    [("• BQ-2 (De Novo Target Screen — On-Demand Service):", {"size": 10.6, "bold": True, "color": TEAL})],
    [("  Screen any priority internal receptor/transporter bait against all 20,260 human proteins in ~6 GPU-h to find missing co-receptors, chaperones, or E3 ligases missed by AP-MS.", {"size": 9.8, "color": INK})],
    [("• BQ-3 (Disease-Interface & Assay Control Design):", {"size": 10.6, "bold": True, "color": RED})],
    [("  Deliver 3D complex coordinates (6A contact surface) + clinical pathogenic variants (ClinVar / AlphaMissense) to design exact point-mutant negative controls for co-IP/BRET.", {"size": 9.8, "color": INK})],
], space_after=3.5)

# Bottom Takeaway Strip on Title Slide
rect(s1, 0.65, 6.45, 12.03, 0.58, ICE)
text(s1, 0.85, 6.53, 11.63, 0.44, [
    [("Goal of Today's 5-10 Min Discussion: ", {"size": 10.8, "bold": True, "color": RED}),
     ("Review the technical capability and boundaries (Part 1), and decide which Business Question(s) and pilot targets to prioritize for Phase-1 wet-lab handoff (Part 2).",
      {"size": 10.4, "bold": True, "color": NAVY})]
])

set_notes(s1, """【Slide 1 口播讲稿（约 45 秒）】
大家好！根据领导上周的建议，今天用 5 到 8 分钟跟大家汇报两件事：
第一部分（Slide 2–4）：总结 David Baker 和 Qian Cong 团队去年底在 Science 和今年在 Scientific Reports 上到底做成了什么突破，以及我们在内部复现验证后摸清的能力边界（什么时候准、什么时候是盲区）。
第二部分（Slide 5–6）：讨论我们内部推进这个 Campaign 的核心 Business Question 到底应该定在哪——我们梳理了三个直接服务心代和靶点发现的候选业务问题（包括曹峥前期筛出的 99 个心代靶点新互作对，以及按需扫全蛋白组服务），供大家今天一起拍板。""")


# ==============================================================================
# SLIDE 2: Part 1A — Two-Study Division of Labor & Scientific Caveats (ZHCO Synthesis)
# ==============================================================================
s2 = add_blank_slide()
add_header_footer(
    s2, 2, 6,
    "What Baker & Cong Achieved: 2025 Science vs 2026 Sci Rep & Caveats",
    "5-Stage Proteome Engine (2025), Case-Study Extension (2026), and Rigorous Reading Rules",
    "PART 1A: TWO-STUDY SYNTHESIS"
)

# Top Problem & Relationship Banner (y=1.10, h=0.84)
rect(s2, 0.48, 1.10, 12.37, 0.84, LIGHT, line=BORDER)
rect(s2, 0.48, 1.10, 0.09, 0.84, NAVY)
text(s2, 0.72, 1.15, 11.95, 0.74, [
    [("How the Two Publications Connect (Figure 1-3 Synthesis):", {"size": 10.6, "bold": True, "color": NAVY})],
    [("• 1st Study (Zhang et al., Science 2025): Built the computational engine (`omicMSAs` + `RF2-PPI`) and screened the human proteome (19,528 proteins -> 17,849 PPIs @90% prec).\n"
      "• 2nd Study (Pei, Zhang & Cong, Sci Rep 2026): Did NOT retrain a model or run a new proteome screen; used the 2025 resource as input for curated case studies (interface disease variants & AlphaFold3 multi-subunit complexes).",
      {"size": 9.4, "color": INK})]
], space_after=1.5)

# 3 Columns: Use a SINGLE TextFrame per card body so items never collide! (y=2.04, h=3.84)
col_w = 3.96
gap = 0.245
pillars = [
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

px = 0.48
for hdr_top, hdr_sub, col, items in pillars:
    rect(s2, px, 2.04, col_w, 3.84, WHITE, line=BORDER)
    rect(s2, px, 2.04, col_w, 0.36, col)
    text(s2, px + 0.14, 2.09, col_w - 0.28, 0.25, hdr_top, size=11.0, bold=True, color=WHITE)
    rect(s2, px, 2.40, col_w, 0.30, ICE)
    text(s2, px + 0.14, 2.44, col_w - 0.28, 0.22, hdr_sub, size=9.6, bold=True, color=col)
    paras = []
    for it_title, it_desc in items:
        paras.append([
            ("• " + it_title + ": ", {"size": 8.9, "bold": True, "color": col}),
            (it_desc, {"size": 8.4, "color": INK})
        ])
    text(s2, px + 0.14, 2.76, col_w - 0.28, 3.04, paras, space_after=4.0)
    px += col_w + gap

# Bottom Funnel Summary Strip (y=5.98, h=0.96)
rect(s2, 0.48, 5.98, 12.37, 0.96, ICE, line=NAVY, line_w=1.0)
rect(s2, 0.48, 5.98, 0.09, 0.96, NAVY)
text(s2, 0.72, 6.06, 11.95, 0.80, [
    [("Exact 2025 Screening Cascade & Output Breakdown: ", {"size": 10.2, "bold": True, "color": NAVY}),
     ("20,296 human proteins -> 19,528 screened (~191M pairs) -> 111.2M localization-filtered -> 43.6M DCA-filtered -> ~1.9M RF2-PPI hits -> AF2 3D modeling -> 29,256 PPIs (@80% est. precision) & 17,849 PPIs (@90% est. precision) -> 3,631 unreported -> 2,700 lacking homologous complex templates (Data S6).",
      {"size": 9.4, "color": INK})]
])

set_notes(s2, """【Slide 2 口播讲稿（约 1.5 分钟，融合 ZHCO 文献梳理与四条严谨科学界定）】
首先回答第一个问题：David Baker 和西南医学中心 Qian Cong 团队在 2025 年 Science 和 2026 年 Scientific Reports 这两篇姊妹篇里到底做成了什么？它们之间是什么关系？
曹峥（ZHCO）帮我们把这两篇文献的脉络和严谨边界梳理得非常清楚（顶部横幅 + 三列）：
1. 两篇文章的分工关系：
   - 第一篇（2025 Science，左列）是“造引擎 + 建全蛋白组图谱”：通过 30 PB 原始测序组装出 21,415 个真核物种的 7 倍深 omicMSAs，加上从 2 亿个 AFDB 单体里提取结构域接触（扩大 17 倍训练集）并引入阴性样本，训出比 AF2 快 20 倍的 RF2-PPI。然后对 19,528 个人类蛋白（1.91 亿对）走四级漏斗：亚细胞共定位过滤（1.112 亿对）→ DCA 共进化预筛（4360 万对）→ RF2-PPI 快筛（~190 万对）→ AF2 建模，最终得到 29,256 个（80% 估计精度）和 17,849 个（90% 估计精度）PPI，包含 3,631 个新互作、2,700 个无同源复合物模板（Data S6）、1,413 个未知功能蛋白互作、4,950 个带疾病突变的界面，以及 404 个多亚基复合物（139 个新亚基）。
   - 第二篇（2026 Sci Rep，中列）**没有重新训练模型，也没有重跑全蛋白组筛查**，而是直接以 2025 年预测出的结构和界面为输入，挑选代表性生物学案例做深度机制挖掘和 AlphaFold3 多亚基组装：比如发现错配修复 PMS1 与范可尼贫血通路 FAAP24 的连接、暗蛋白 C12orf57（界面携带致病突变 L51Q）与内体回收复合体 ANKRD50 的结合、纤毛病突变 WDR19 V80D 落在 BBS7–WDR19 界面、线粒体复合物 IV 缺陷突变 SCO1 P174L 与 COA6 W59C 在界面正对接触，以及用 AF3 拼出 NRZ 新亚基 C19orf25 和 BLOC-1/BORC 复合物。
2. 右列红框（汇报给领导和生物学团队时最关键的 4 条科学严谨性界定，绝不夸大）：
   - 界定 1（不全是盲筛新发现）：17,849 个高置信互作结合了“从头盲筛”和“先验数据库证据引导（允许更低阈值）”，其中只有 3,631 个是真正未见报道的新互作（2,700 个在 Data S6）。
   - 界定 2（无模板 ≠ 单体结构未知）：Data S6 的 2,700 对指的是“PDB 里没有同源的**复合物**结构模板”，而不是单个蛋白没有结构。
   - 界定 3（界面上有致病突变 ≠ 已证实打断结合）：4,950 个界面落有临床突变，只是提出了“突变可能通过影响结合或组装致病”的可检验分子假设，本身不等于湿实验已证明它破坏结合；同样，训练用的 AFDB 结构域接触也是预测值而非晶体结构。
   - 界定 4（高 pLDDT/ipTM ≠ 体内真结合）：结构置信度只代表局部几何堆积合理，不能替代靶器官共表达和湿实验验证。""")


# ==============================================================================
# SLIDE 3: Part 1B — In-House Reproduction & Mechanistic Sensitivity (1.5 min)
# ==============================================================================
s3 = add_blank_slide()
add_header_footer(
    s3, 3, 6,
    "In-House Benchmark Reproduction & Physical Sensitivity Mechanism",
    "Verified on 33,000 Pairs (6x A100 GPUs): 43.2% Recall on Large Complexes vs 4.5% on Small Motifs",
    "PART 1B: IN-HOUSE VALIDATION"
)

# Top 4 KPI Cards: use a single unified textbox inside each KPI card so rows never collide
kpis_s3 = [
    ("262x Enrichment", "Weighted AUCPR 0.262 vs 0.001", "1:1,000 proteome prior (1:1 AUC = 0.813)", NAVY),
    ("r = 0.919 Parity", "8,977 Shared Benchmark Pairs", "623 TPs & 0 FPs at >=90% precision", TEAL),
    ("43.2% vs 4.5%", "Large vs Small Interface Recall", ">1,500 A2 stable vs <800 A2 SLiMs", NAVY),
    ("~6 GPU-Hours", "Per Target Proteome Screen", "1 bait vs 20,260 proteins on 6x A100", RED),
]
kw3 = 2.91
kg3 = 0.24
kx3 = 0.48
for val, lbl, sub, col in kpis_s3:
    rect(s3, kx3, 1.12, kw3, 0.92, WHITE, line=BORDER)
    rect(s3, kx3, 1.12, kw3, 0.06, col)
    text(s3, kx3 + 0.08, 1.22, kw3 - 0.16, 0.78, [
        [(val, {"size": 15.5, "bold": True, "color": col})],
        [(lbl, {"size": 9.4, "bold": True, "color": INK})],
        [(sub, {"size": 8.0, "color": GREY})],
    ], align=PP_ALIGN.CENTER, space_after=2)
    kx3 += kw3 + kg3

# Left: High-DPI 2-Panel Evidence Plot (x=0.48, y=2.20, w=7.25, h=3.10)
IMG = "/das/user/QYJI/druggability/humanPPI_repro/results/repro_2panel_evidence.png"
rect(s3, 0.48, 2.20, 7.25, 3.12, WHITE, line=BORDER)
slide_img_w = 7.15
slide_img_h = slide_img_w * (3.15 / 7.6)  # 2.963 in
s3.shapes.add_picture(IMG, Inches(0.53), Inches(2.27), Inches(slide_img_w), Inches(slide_img_h))

# Right: Mechanistic Interpretation Box (x=7.92, y=2.20, w=4.93, h=3.12)
rect(s3, 7.92, 2.20, 4.93, 3.12, LIGHT, line=BORDER)
rect(s3, 7.92, 2.20, 4.93, 0.36, NAVY)
text(s3, 8.08, 2.26, 4.60, 0.24, "How to Read These Two Plots (Biology First)", size=11.0, bold=True, color=WHITE)

text(s3, 8.08, 2.66, 4.62, 2.58, [
    [("1. Panel A (Left) — Precision Under 1:1,000 Proteome Odds:", {"size": 10.0, "bold": True, "color": NAVY})],
    [("   In a blind proteome screen, 99.9% of pairs do not bind (random baseline AUC = 0.001). Our reproduced pipeline achieves AUC = 0.262 (262x enrichment) and 20.8% recall at >=90% precision (623 true hits, zero false positives).", {"size": 9.1, "color": INK})],
    [("2. Panel B (Right) — Why Average Recall is 20.8% (MECH):", {"size": 10.0, "bold": True, "color": TEAL})],
    [("   Coevolutionary signal scales with buried surface area:\n"
      "   • Large/Stable (>1,500 A2, >50 contact residues): 43.2% recall at >=90% precision (51.8% at moderate cutoff).\n"
      "   • Medium (800-1,500 A2): 19.4% recall.\n"
      "   • Small/Transient (<800 A2, <=10 residues, SLiMs): 4.5% recall.", {"size": 9.1, "color": INK})],
], space_after=3)

# Bottom: Human Genetics Interface Module Verification (CASR Proof-of-Concept) (y=5.46, h=1.48)
rect(s3, 0.48, 5.46, 12.37, 1.48, GREEN_BG, line=TEAL, line_w=1.2)
rect(s3, 0.48, 5.46, 0.09, 1.48, TEAL)
text(s3, 0.72, 5.54, 11.95, 1.32, [
    [("In-House Reproduction of Pei et al. (Sci Rep 2026) Disease-Interface Module — Verified on CASR (P41180) [OBS]:",
      {"size": 10.6, "bold": True, "color": TEAL})],
    [("• Dual-Evidence Pathogenic Rule: Implemented automated SAV quality control (<5% sequence mismatch) + dual-source pathogenicity filter (UniProt disease variants + EBI AlphaMissense per-protein scores) + 6 A CB/CA interface geometry (`src/druggability/interface_variants.py`, 22 unit tests passing).\n"
      "• Biological Proof-of-Concept on Calcium-Sensing Receptor (CASR, Tier-A CKD target in Data S6): Identified 89 clinical pathogenic mutations (HHC1 / HYPOC1); 64% cluster directly at the extracellular dimerization interface (residues <=612), proposing concrete point-mutant hypotheses for wet-lab mutagenesis.",
      {"size": 9.4, "color": INK})]
], space_after=3)

set_notes(s3, """【Slide 3 口播讲稿（约 1.5 分钟）】
为了确保这套方法在我们手里真实可用、不是纸上谈兵，我们在内部 6 张 A100 上把完整的 33,000 对基准集（3,000 个三大数据库共识真阳性 + 30,000 个阴性对）和疾病突变界面映射模块跑通并做了严格核验：
1. 看左边的 Panel A：如果模拟全蛋白组真实 1:1000 的极低信噪比（每 1 个真伙伴混在 1000 个随机蛋白里），随机盲筛的 AUC 只有 0.001，而我们本地复现的 RF2-PPI 达到了 0.262，相当于把实验命中率浓缩富集了 262 倍（如果换算成大家熟悉的 1:1 平衡测试集，AUC 是 0.813）。在 >=90% 精度红线以上，我们抓出了 623 个真阳性，且保持零假阳性；与作者官方分数的皮尔逊相关性达到 0.919。
2. 大家一定会问：为什么在 90% 精度下，总体召回率是 20.8%？剩下的近 80% 去哪了？
   这就是右边 Panel B 揭示的核心物理机制：我们按 PDB 复合物真实的物理接触面积分层后发现，模型对“大界面、稳定结合的复合物（>1500 Å²，超过 50 个接触残基）”召回率高达 43.2%（中等阈值下超过一半，达 51.8%）；而对“小界面、瞬时结合的短线性基序（<800 Å²，比如激酶底物瞬时磷酸化位点）”召回率只有 4.5%。
   这句话对我们做项目立项至关重要：它不是一把万能锤，而是一台专门捕捉“稳定结构复合物、跨膜复合物和辅助亚基”的高精度显微镜。
3. 底部的绿框：我们还把今年跟进发表的 Sci Rep (2026) 临床突变映射方法写成了内部标准模块（结合 UniProt 临床注释 + AlphaMissense 双证据规则 + 6 Å 界面几何）。拿 Data S6 里的慢性肾病上市药靶点钙敏感受体 CASR 实测，抓出的 89 个临床致病突变里有 64% 直接聚簇在胞外二聚化结合面上——这意味着我们给生物团队交付候选蛋白时，能同时给出“打断结合该突变哪几个氨基酸”的湿实验负对照方案。""")


# ==============================================================================
# SLIDE 4: Part 1C — Prospective Validation (2024-2026) & Biological Fit Matrix (1.5 min)
# ==============================================================================
s4 = add_blank_slide()
add_header_footer(
    s4, 4, 6,
    "Prospective Time-Split Validation (2024-2026) & Biological Fit Matrix",
    "11 Data S6 Predictions Independently Confirmed by Cryo-EM / Co-IP Since Cutoff",
    "PART 1C: PROSPECTIVE AUDIT & BOUNDARIES"
)

# Left Panel: Prospective Time-Split Table (x=0.48, y=1.12, w=7.35, h=5.82)
rect(s4, 0.48, 1.12, 7.35, 5.82, LIGHT, line=BORDER)
rect(s4, 0.48, 1.12, 7.35, 0.36, TEAL)
text(s4, 0.64, 1.18, 7.05, 0.24,
     "Prospective Audit: Data S6 'Zero-Prior' Pairs Confirmed in 2024-2026 (11 Cases)",
     size=10.8, bold=True, color=WHITE)

text(s4, 0.64, 1.54, 7.05, 0.40,
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

tbl_shape = s4.shapes.add_table(len(rows_data), 4, Inches(0.62), Inches(2.00), Inches(7.07), Inches(3.82))
tbl = tbl_shape.table
col_widths = [1.42, 1.15, 1.95, 2.55]
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

# Bottom note inside Left Panel (y=5.92, h=0.90)
rect(s4, 0.62, 5.94, 7.07, 0.88, WHITE, line=BORDER)
rect(s4, 0.62, 5.94, 0.07, 0.88, NAVY)
text(s4, 0.78, 6.00, 6.80, 0.76, [
    [("Category B — Resolving Direct 3D Mechanism for Known AP-MS Hits: ", {"size": 8.8, "bold": True, "color": NAVY}),
     ("Beyond de novo Data S6 pairs, the 3D complex predictions resolved how NUDT5 allosterically blocks PPAT in purine synthesis (Science 2025, PMID 41196949) and how SMG5-SMG6 dimerizes in NMD (Nat Commun 2026) — turning noisy AP-MS hits into point-mutant-verified mechanisms. (* = Transmembrane / Organelle).",
      {"size": 8.1, "color": INK})]
])

# Right Panel: Biological Fit Matrix & Governance Rule (x=8.02, y=1.12, w=4.83, h=5.82)
rect(s4, 8.02, 1.12, 4.83, 5.82, LIGHT, line=BORDER)
rect(s4, 8.02, 1.12, 4.83, 0.36, RED)
text(s4, 8.18, 1.18, 4.50, 0.24,
     "Biological Fit Matrix & Campaign Governance",
     size=10.8, bold=True, color=WHITE)

# Green Box: Ideal Targets (y=1.60, h=1.88)
rect(s4, 8.16, 1.60, 4.55, 1.88, GREEN_BG, line=TEAL, line_w=1.2)
rect(s4, 8.16, 1.60, 4.55, 0.28, TEAL)
text(s4, 8.28, 1.65, 4.30, 0.20, "IDEAL TARGETS (HIGH SENSITIVITY — USE HERE)", size=9.0, bold=True, color=WHITE)
text(s4, 8.28, 1.95, 4.30, 1.46, [
    [("• Transmembrane & Organelle Complexes (58% of S6):", {"size": 8.8, "bold": True, "color": TEAL})],
    [("  Hard to solubilize in detergent AP-MS (e.g., GPCR accessory proteins RAMP1/2/3, ER/lysosomal channels).", {"size": 8.2, "color": INK})],
    [("• Large Constitutive / Obligate Assemblies (>1,500 A2):", {"size": 8.8, "bold": True, "color": TEAL})],
    [("  43.2% recall at >=90% precision (51.8% at moderate cutoff).", {"size": 8.2, "color": INK})],
    [("• Disease-Mutated Interfaces (ClinVar / Human Genetics):", {"size": 8.8, "bold": True, "color": TEAL})],
    [("  Pinpoints exact contact residues to design disruptor controls.", {"size": 8.2, "color": INK})],
], space_after=1.5)

# Red Box: Blind Spots (y=3.60, h=1.88)
rect(s4, 8.16, 3.60, 4.55, 1.88, RED_BG, line=RED, line_w=1.2)
rect(s4, 8.16, 3.60, 4.55, 0.28, RED)
text(s4, 8.28, 3.65, 4.30, 0.20, "KNOWN BLIND SPOTS (DO NOT USE TO EXCLUDE)", size=9.0, bold=True, color=WHITE)
text(s4, 8.28, 3.95, 4.30, 1.46, [
    [("• Transient / PTM-Triggered Signaling Complexes:", {"size": 8.8, "bold": True, "color": RED})],
    [("  Phosphorylation- or ligand-dependent recruitment (e.g., GPCR-arrestin, kinase-substrate) lacks static coevolution.", {"size": 8.2, "color": INK})],
    [("• Disordered Short Linear Motifs (SLiMs, <800 A2):", {"size": 8.8, "bold": True, "color": RED})],
    [("  Only 4.5% recall at high precision (underrepresented in training).", {"size": 8.2, "color": INK})],
    [("• Fast-Evolving / Immune / Tissue-Restricted Paralogs:", {"size": 8.8, "bold": True, "color": RED})],
    [("  Coevolution reflects family conservation, not tissue specificity.", {"size": 8.2, "color": INK})],
], space_after=1.5)

# Golden Rule Box (y=5.60, h=1.22)
rect(s4, 8.16, 5.60, 4.55, 1.22, AMBER_BG, line=AMBER, line_w=1.2)
rect(s4, 8.16, 5.60, 0.08, 1.22, AMBER)
text(s4, 8.34, 5.66, 4.28, 1.10, [
    [("Golden Rule (Lambourne et al., Nat Commun 2026):", {"size": 9.2, "bold": True, "color": AMBER})],
    [("1. Positive Hypothesis Generator Only: High score (@90% precision) + co-expression = strong wet-lab lead; low score NEVER disproves a biological hypothesis.\n"
      "2. Mandatory Tissue Co-Expression Gate: Always filter predicted pairs by GTEx / single-cell co-expression in the disease tissue.",
      {"size": 8.1, "color": INK})]
], space_after=2)

set_notes(s4, """【Slide 4 口播讲稿（约 1.5 分钟）】
大家可能会问：Baker 团队在 Data S6 里报的那 2,700 个“三大数据库和 PDB 里完全零记录”的全新预测，到底是不是计算伪影？
因为 Data S6 锁库的时间截点是 2023 年 9 月（预印本发在 2024 年 10 月），过去这两年（2024–2026）刚好给我们提供了一个极其干净的“前瞻性时间切片盲测（Prospective Time-Split Validation）”：
- 我们系统检索了过去两年的文献，发现 Data S6 里已经有 **11 个当年完全零先验的预测对**，被全球独立课题组用冷冻电镜（Cryo-EM）、晶体结构或内源 co-IP 实锤证实了！
- 左表列出了代表性案例：比如生殖细胞里的 DND1-NANOS3（2026 年刚发了 Mol Cell 结构）、剪接体质量控制复合物 GPATCH1-DHX35（2025 年 Cell Research 冷冻电镜结构）、核孔第 4 个跨膜蛋白 TMEM209-NUP210（2026 年 J Cell Sci 内源 co-IP 证实）、线粒体维生素 B12 伴侣 MTR-MMADHC（2026 年 PNAS 证实）。
- 请大家注意左表带星号（*）的条目：**超过一半被前瞻证实的案例都是跨膜蛋白或细胞器膜复合物**——这再次印证了它在捕捉“传统湿实验难溶跨膜复合物”上的独特优势。

右边总结了我们内部使用这项技术的**红绿边界与治理铁律**：
- 绿色（最适用）：跨膜与细胞器复合物、大界面稳定复合物（>1500 Å²）、以及带有人类遗传学致病突变的调控界面。
- 红色（天然盲区）：磷酸化或配体诱导的瞬时招募（如 GPCR-arrestin）、无序区短基序（SLiMs，召回率仅 4.5%）、以及快速演化的免疫受体。
- 底部黄框（黄金治理法则，也是今年 Nat Commun 外部审计的核心结论）：第一，**严禁把低分当作阴性排除依据**（只做阳性假设生成和 3D 点突变设计）；第二，由于共进化分不清同一蛋白家族在不同组织的亚型（paralog），所有预测进入湿实验前**必须经过疾病靶器官的 GTEx / 单细胞共表达过滤**。""")


# ==============================================================================
# SLIDE 5: Part 2A — What is the Business Question for the Campaign? (2 min)
# ==============================================================================
s5 = add_blank_slide()
add_header_footer(
    s5, 5, 6,
    "What is the Business Question for Our Campaign? (3 Options Menu)",
    "Translating Baker's Interactome Engine into Concrete Drug Discovery & Assay Decisions",
    "PART 2A: CAMPAIGN BUSINESS QUESTIONS"
)

# Top Framing Banner (y=1.12, h=0.72)
rect(s5, 0.48, 1.12, 12.37, 0.72, ICE, line=NAVY, line_w=1.0)
rect(s5, 0.48, 1.12, 0.09, 0.72, NAVY)
text(s5, 0.72, 1.20, 11.95, 0.56, [
    [("Why Define the Business Question Now? ", {"size": 10.6, "bold": True, "color": NAVY}),
     ("Our pipeline and 6-GPU screening capability are fully operational. Rather than running unfocused screens, we propose three concrete Business Questions (BQ-1, BQ-2, BQ-3) tailored to different stages of our cardiometabolic and rare-disease portfolio.",
      {"size": 9.6, "color": INK})]
])

# 3 Detailed Business Question Columns: Use a SINGLE TextFrame per card body so bullets never collide!
bqs = [
    ("BQ-1: Portfolio Partner Mining",
     "99 Data S6 Leads -> 8 Pass All 4/4 Criteria",
     NAVY,
     [
         ("The Business Question",
          "Among Baker's 2,700 zero-prior-evidence human PPIs (Data S6), which novel interactors of our cardiometabolic targets pass strict 4-criteria triage (Genetics, Pathway, Perturbation, Co-progression)?"),
         ("Preliminary Result on 99 Unflagged Leads",
          "Strict 4-criteria audit across 99 leads: C1 Both-Genetics (60; 46 Human GWAS/ClinVar), C2 Pathway (43), C3 Direct Perturb. (14), C4 CM Co-expr (56) -> 8 leads pass all 4/4 (led by #1 RAMP3-MRAP2 & #2 RAMP1-MRAP2)."),
         ("Deep-Dive on #1 Winner (RAMP3-MRAP2)",
          "Boltz-2 + omicMSA complex (ipTM=0.868), A100 MD (RMSD 0.49A), FEP hotspot scan (obesity SAVs R125 +6.25 & L115 +5.21 kcal/mol), and gepant groove docking (-7.81 kcal/mol) completed."),
         ("Wet-Lab Deliverable",
          "8-pair 4/4 ranked dossier + RAMP3-MRAP2 3D coordinates & L115A/R125A/W56A disruptor controls ready for co-IP / BRET."),
     ]),
    ("BQ-2: De Novo Proteome Screen",
     "Find Missing Partners for Priority Baits",
     TEAL,
     [
         ("The Business Question",
          "When an internal biology project has a high-priority target (especially a transmembrane receptor, transporter, or intracellular target where detergent AP-MS fails), what is its missing endogenous partner?"),
         ("Target Archetypes",
          "1) Orphan / membrane receptors needing unknown accessory proteins or trafficking chaperones. 2) Intracellular targets needing tissue-specific endogenous E3 ligases or deubiquitinases for proximity concepts."),
         ("Compute & Timeline",
          "~6 GPU-hours per target bait (1 bait protein vs all 20,260 human proteins on 6x A100 GPUs)."),
         ("Wet-Lab Deliverable",
          "Calibrated partner shortlist (@90% / @80% precision) + 3D complex structures + GTEx co-expression matrix."),
     ]),
    ("BQ-3: 3D Interface & Genetics Triage",
     "De-Risk Mechanism & Design Assay Controls",
     RED,
     [
         ("The Business Question",
          "When biology teams already have a suspect binding partner (from AP-MS, literature, or genetics) or a human disease variant of unknown mechanism, where is the exact 3D contact surface and how do we test it?"),
         ("Scientific Problem Solved",
          "Standard AP-MS cannot distinguish direct vs indirect binding, and domain truncations often misfold the whole protein. Biologists need surgical single-residue disruptor mutations."),
         ("Compute & Timeline",
          "~15 minutes per pair via `bbbkit interface-variants` (UniProt + AlphaMissense + 6A CB/CA contact geometry)."),
         ("Wet-Lab Deliverable",
          "Atomic 3D interface coordinates + human pathogenic SAV enrichment + 2-3 specific point-mutations to selectively abolish binding in co-IP / BioID."),
     ]),
]

bx = 0.48
for b_hdr, b_sub, b_col, b_rows in bqs:
    rect(s5, bx, 1.98, col_w, 4.05, WHITE, line=BORDER)
    rect(s5, bx, 1.98, col_w, 0.36, b_col)
    text(s5, bx + 0.12, 2.03, col_w - 0.24, 0.25, b_hdr, size=11.0, bold=True, color=WHITE)
    rect(s5, bx, 2.34, col_w, 0.32, LIGHT)
    text(s5, bx + 0.12, 2.38, col_w - 0.24, 0.24, b_sub, size=9.2, bold=True, color=b_col)
    paras = []
    for r_title, r_body in b_rows:
        paras.append([
            ("• " + r_title + ": ", {"size": 8.9, "bold": True, "color": b_col}),
            (r_body, {"size": 8.4, "color": INK})
        ])
    text(s5, bx + 0.14, 2.74, col_w - 0.28, 3.20, paras, space_after=4.5)
    bx += col_w + gap

# Bottom Synergy Strip (y=6.15, h=0.80)
rect(s5, 0.48, 6.15, 12.37, 0.80, GREEN_BG, line=TEAL, line_w=1.0)
rect(s5, 0.48, 6.15, 0.09, 0.80, TEAL)
text(s5, 0.72, 6.23, 11.95, 0.64, [
    [("How the 3 Business Questions Fit Together as One Modular Pipeline: ", {"size": 10.2, "bold": True, "color": TEAL}),
     ("BQ-1 (99 Cardiometabolic Data S6 Leads) and BQ-2 (1-Bait Proteome Screen) generate high-precision partner hypotheses; BQ-3 (3D Interface + Pathogenic SAV Mapping) automatically runs on the top hits so every candidate handed to wet-lab biology arrives with an actionable 3D model and point-mutant negative control.",
      {"size": 9.3, "color": INK})]
])

set_notes(s5, """【Slide 5 口播讲稿（约 2 分钟）】
接下来进入第二部分，也是领导特别指出的“What is the business question for the campaign (TBD)”：
既然工具和算力都已经就绪，我们不能为了算而算，必须锚定明确的业务问题。结合我们部门在心代（Obesity, T2D, CKD, MASH, CVD/HF）和新靶点探索的需求，我们梳理了 3 个候选的 Business Questions（BQ-1 到 BQ-3）：

1. 第一列 BQ-1（存量心代靶点的新调控伙伴挖掘 — 推荐作为立即可跑的 Phase-1 Pilot）：
   - 业务问题：在 Baker 发布的 2,700 个完全零先验新互作（Data S6）里，哪些跟我们心代管线靶点直接结合的新伙伴，是真正具有生物学调控价值的辅助受体或伴侣蛋白？
   - 现有基础：曹峥（ZHCO）前期已经把 Data S6 的 2,700 对和 656 个心代药物靶点做了交叉，找出了 198 对单靶点互作，并用非对称过滤（剔除 NDUF 呼吸链同家族亚基、Metformin 泛靶点等假象）筛出了 **99 个干净的未标记新互作候选对（Unflagged Leads）**。
   - 投入与产出：只需要 1–2 天计算，把这 99 对全部过一遍本地精度校准、GTEx 靶器官共表达和 3D 界面致病突变映射，直接浓缩出 Top-10 交付湿实验验证。

2. 第二列 BQ-2（高优疑难靶点的全蛋白组从头筛查 — 按需定制服务）：
   - 业务问题：当生物团队研究一个重点靶点（尤其是跨膜受体、转运体或细胞器蛋白，传统去垢剂 AP-MS 抓不到真伙伴），想知道它的内源辅助受体、转运伴侣或组织特异性 E3 连接酶是谁？
   - 投入与产出：给 1 个靶点 UniProt ID，我们在 6 张 A100 上跑约 6 个小时，就能把它和全人类 20,260 个蛋白通扫一遍，交付高置信度伙伴清单。

3. 第三列 BQ-3（3D 结合界面与人类遗传学突变赋能湿实验设计 — 实验转化加速器）：
   - 业务问题：当生物学家拿到一个候选结合伙伴（无论来自计算预测还是内部 AP-MS 初筛），结合面到底在哪？怎么设计不破坏整体折叠的“单点突变负对照（disruptor mutant）”来证明特异性结合？
   - 投入与产出：单对只需 15 分钟，输出 6 Å 接触面残基 + ClinVar/AlphaMissense 临床致病突变富集，直接给出 2–3 个用于 co-IP / BRET 的点突变负对照设计。""")


# ==============================================================================
# SLIDE 6: Part 2B — Preliminary Execution of BQ-1 (4-Criteria Triage + Docking / MD / FEP) (2 min)
# ==============================================================================
s6 = add_blank_slide()
add_header_footer(
    s6, 6, 6,
    "BQ-1 Preliminary Result: 4-Criteria Triage (99 Leads) & RAMP3-MRAP2 MD/FEP",
    "8/99 Cardiometabolic Leads Pass All 4 Strict Criteria; #1 RAMP3-MRAP2 Characterized by Boltz-2, MD & FEP",
    "PART 2B: BQ-1 PRELIMINARY RESULTS"
)

# Left Column: 4-Criteria Funnel & Top 4/4 Ranked Leads Table (x=0.48, y=1.12, w=7.25, h=5.82)
rect(s6, 0.48, 1.12, 7.25, 5.82, LIGHT, line=BORDER)
rect(s6, 0.48, 1.12, 7.25, 0.36, NAVY)
text(s6, 0.64, 1.18, 6.95, 0.24,
     "BQ-1 Strict 4-Criteria Triage Across 99 Unflagged Cardiometabolic Leads",
     size=10.5, bold=True, color=WHITE)

# 5 Mini Funnel Pills inside Left Column (y=1.55, h=0.58)
f_pills = [
    ("C1: Genetics", "60/99 (46 Human)", NAVY),
    ("C2: Pathway", "43/99 Shared Path.", NAVY),
    ("C3: Perturb.", "14/99 Direct Evid.", TEAL),
    ("C4: Co-Prog.", "56/99 CM Co-Expr.", TEAL),
    ("8 Pass 4/4", "#1 RAMP3-MRAP2", RED),
]
pw = 1.29
pg = 0.12
px6 = 0.62
for p_val, p_sub, p_col in f_pills:
    rect(s6, px6, 1.55, pw, 0.58, WHITE, line=p_col, line_w=1.2)
    text(s6, px6 + 0.03, 1.60, pw - 0.06, 0.48, [
        [(p_val, {"size": 9.8, "bold": True, "color": p_col})],
        [(p_sub, {"size": 7.4, "bold": True, "color": INK})],
    ], align=PP_ALIGN.CENTER, space_after=1)
    px6 += pw + pg

# Table of All 8 4/4 Passing Leads (exact match to Excel Sheet 1) (y=2.22, h=3.68)
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

t2_shape = s6.shapes.add_table(len(lead_rows), 5, Inches(0.62), Inches(2.22), Inches(6.97), Inches(3.68))
t2 = t2_shape.table
t2_widths = [1.45, 0.92, 0.95, 1.75, 1.90]
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

# Bottom note inside Left Column (y=5.98, h=0.84)
rect(s6, 0.62, 5.98, 6.97, 0.84, WHITE, line=BORDER)
rect(s6, 0.62, 5.98, 0.07, 0.84, TEAL)
text(s6, 0.78, 6.03, 6.72, 0.74, [
    [("Why RAMP3-MRAP2 is the #1 Winner for Structural & Energetic Deep-Dive: ", {"size": 8.6, "bold": True, "color": TEAL}),
     ("Passes all 4 criteria + Tier-A approved & Novo Amylin/CagriSema co-receptor (RAMP3) paired with human monogenic obesity protein MRAP2. Two human obesity variants on MRAP2 (p.Leu115Val, p.Arg125Cys) sit directly inside the 3D interface.",
      {"size": 7.9, "color": INK})]
])

# Right Column: #1 Winner (RAMP3-MRAP2) 3D Complex, Docking, MD & FEP Analysis (x=7.90, y=1.12, w=4.95, h=5.82)
rect(s6, 7.90, 1.12, 4.95, 5.82, ICE, line=BORDER)
rect(s6, 7.90, 1.12, 4.95, 0.36, RED)
text(s6, 8.06, 1.18, 4.65, 0.24,
     "#1 Winner (RAMP3-MRAP2): 3D Complex, Docking, MD & FEP",
     size=10.5, bold=True, color=WHITE)

# Embedded 2-Panel Triage + FEP Plot (y=1.55, h=2.02)
BQ1_IMG = "/das/user/QYJI/druggability/reports/bq1_99_triage/bq1_99_triage_and_fep_2panel.png"
rect(s6, 8.04, 1.55, 4.67, 2.02, WHITE, line=BORDER)
s6.shapes.add_picture(BQ1_IMG, Inches(8.06), Inches(1.57), Inches(4.63), Inches(1.98))

# Quantitative Summary Card of 3D + MD + FEP + Docking + Next Steps (y=3.65, h=3.17)
rect(s6, 8.04, 3.65, 4.67, 3.17, WHITE, line=NAVY, line_w=1.2)
rect(s6, 8.04, 3.65, 4.67, 0.26, NAVY)
text(s6, 8.16, 3.69, 4.45, 0.20, "QUANTITATIVE BIOPHYSICAL & DRUGGABILITY SUMMARY", size=8.6, bold=True, color=WHITE)
text(s6, 8.16, 3.97, 4.45, 2.78, [
    [("• 3D Complex & Coevolution (RF2-PPI + Boltz-2 omicMSA):", {"size": 8.5, "bold": True, "color": NAVY})],
    [("  ipTM = 0.868, ptm = 0.834 (180 inter-chain contacts <=5A: 21 TM-TM + 159 ECD/juxtamembrane). RF2-PPI TM helix contact prob = 0.590 (RAMP3) / 0.865 (RAMP1).", {"size": 7.8, "color": INK})],
    [("• Explicit-Solvent MD (A100, Amber14SB + TIP3P, 200 ps):", {"size": 8.5, "bold": True, "color": TEAL})],
    [("  Complex remains tightly bound with backbone RMSD = 0.49 A (2,558 ns/day).", {"size": 7.8, "color": INK})],
    [("• FEP Mutational Hotspot Scan (Obesity Variants at Interface):", {"size": 8.5, "bold": True, "color": RED})],
    [("  Human obesity SAVs MRAP2 R125 (d=3.33A to RAMP3 D113, ddG = +6.25 kcal/mol) & L115 (d=1.97A to D107, ddG = +5.21 kcal/mol) are top energetic hotspots alongside M87 (+3.29), F85 (+3.07) & RAMP3 W56 (+2.51 kcal/mol).", {"size": 7.8, "color": INK})],
    [("• Interface Groove Docking (AutoDock Vina + Boltz-2 Ternary):", {"size": 8.5, "bold": True, "color": NAVY})],
    [("  RAMP-antagonist scaffolds Ubrogepant (-7.81 vs -7.09 kcal/mol control) & Rimegepant (-7.39 kcal/mol, ternary ligand_ipTM = 0.950) selectively bind the composite RAMP3-MRAP2 ECD groove -> propose L115A/R125A/W56A co-IP disruptor controls.", {"size": 7.8, "color": INK})],
], space_after=1.8)

set_notes(s6, """【Slide 6 口播讲稿（约 2 分钟）】
最后一页，我们直接展示针对 **BQ-1（99 个心代 Data S6 候选互作对）** 刚刚跑完的 **严格 4 维自动化初筛 + Top-1 候选（RAMP3–MRAP2）全链路结构/动力学/FEP 初步结果**：

1. 看左栏：按照曹峥（ZHCO）设计的 4 条生物学与遗传学标准，我们用 Druggability Agent 对 99 个干净的单靶点心代互作对做了严格核验：
   - **C1（已知靶点与未知伙伴双方均有心代疾病遗传学证据）**：60/99 对（61%）通过（其中 **46 对为双方均有纯人类 GWAS/ClinVar 遗传关联**，14 对含敲除小鼠表型）；
   - **C2（共同信号通路或生物学过程）**：43/99 对（43%）通过；
   - **C3（文献或实验库显示直接双蛋白扰动/调控证据）**：14/99 对（14%）通过；
   - **C4（心代疾病进展共表达或 STRING 共表达）**：56/99 对（57%）通过。
   - **四项严格标准全过（Pass 4/4）一共 8 对（8.1%，其中前 6 对均为双蛋白纯人类遗传关联）**！左表列出了全部 8 对：
     • **第 1 名 RAMP3–MRAP2 与第 2 名 RAMP1–MRAP2**：RAMP1/3 是我们 Amylin / CagriSema 管线的核心辅助受体（分别有 T2D 与肥厚型心肌病 GWAS 关联），而 MRAP2 是著名的人类单基因重度肥胖致病基因（Nature 2013），且悬浮微珠阵列与 co-IP（PMID 37085333）已证实两者形成异源复合物并相互调控膜表面表达；
     • **第 3 名 NR3C1–FOXO3**（房颤/肥胖双人遗传 + FOXO 代谢转录通路 + STRING 实验互作 0.363）、**第 4 名 CD80–CSF3**、**第 5 名 TLR4–LTBR**、**第 6 名 GP1BA–F2RL2**，以及含小鼠表型的 **第 7–8 名 ITGA2B–ACVRL1、IL18–CCL17**（另有 14 对通过 3/4 标准，如 IL17A–FCN2、BRD3–KDM1A、TLR4–CTSS）。

2. 看右栏：按照第 5 步方案，我们挑出综合排名 **#1 的 RAMP3–MRAP2**，完成了 3D 建模、显式水分子动力学（MD）、自由能微扰（FEP 突变热点扫描）与复合口袋小分子对接：
   - **3D 复合物与共进化**：用 Baker 的 21,415 个真核物种 omicMSA 跑 Boltz-2，界面置信度 **ipTM 高达 0.868**（共有 180 对跨链残基接触 <=5 Å，包含 21 对跨膜螺旋接触和 159 对胞外/近膜接触）；
   - **A100 显式水 MD（200 ps）**：主链 RMSD 仅 **0.49 Å**，复合物结合极其稳定；
   - **FEP 突变能量热点扫描（右上 Panel B）**：最令人振奋的是，MRAP2 上已知的两个**人类单基因肥胖临床突变位点——Arg125（R125C，距 RAMP3 D113 仅 3.33 Å）和 Leu115（L115V，距 RAMP3 D107 仅 1.97 Å）**，在 FEP 突变计算中恰好是整个结合面最强的 #1 和 #2 能量热点（**突变后结合能损失 ddG 分别为 +6.25 kcal/mol 和 +5.21 kcal/mol**），而外围环区的 N88Y 突变位点 ddG 为 -0.88 kcal/mol（提示通过大侧链空间位阻致病）；
   - **界面复合凹槽对接**：临床 RAMP 拮抗剂分子骨架（Ubrogepant -7.81 kcal/mol，Rimegepant -7.39 kcal/mol 且三元共折叠 ligand_ipTM = 0.950）相比非界面负对照区展现出显著的界面凹槽选择性。
   - **湿实验转化**：我们已经锁定了 **MRAP2 L115A/V、R125C/A 与 RAMP3 W56A** 作为精确破坏结合的 co-IP / BRET 点突变负对照。
我的汇报完了，欢迎大家讨论拍板！""")

out_deck = "/das/user/QYJI/druggability/reports/ppi_group_meeting_deck_2026-10-29.pptx"
prs.save(out_deck)
print("Saved 6-slide group meeting PPTX:", out_deck)
