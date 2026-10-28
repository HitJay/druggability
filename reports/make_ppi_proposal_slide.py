#!/usr/bin/env python
"""One-page proposal slide: RF2-PPI-based target screening capability (Biology-friendly edition).

NN corporate palette (#001965 / #00857C / #D9383A). 16:9 widescreen (13.333 x 7.5 in).
Includes speaker notes (Chinese oral script + Q&A defense).
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY = RGBColor(0x00, 0x19, 0x65)
TEAL = RGBColor(0x00, 0x85, 0x7C)
RED = RGBColor(0xD9, 0x38, 0x3A)
INK = RGBColor(0x1A, 0x1A, 0x2E)
GREY = RGBColor(0x5A, 0x60, 0x70)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xE8, 0xEE, 0xF7)
BORDER = RGBColor(0xD0, 0xD7, 0xE5)
GREEN_BG = RGBColor(0xEB, 0xF7, 0xF5)
RED_BG = RGBColor(0xFD, 0xF2, 0xF2)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
W, H = 13.333, 7.5


def rect(x, y, w, h, fill, line=None, line_w=0.75, shape_type=MSO_SHAPE.RECTANGLE):
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


def text(x, y, w, h, runs, size=11, bold=False, color=INK, align=PP_ALIGN.LEFT,
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


# ==============================================================================
# 1. Background & Header Banner (0.00 - 0.98)
# ==============================================================================
rect(0, 0, W, H, WHITE)
rect(0, 0, W, 0.98, NAVY)
text(0.45, 0.14, 9.8, 0.40,
     "Proteome-Wide Binding Partner & Disease-Interface Triage",
     size=21, bold=True, color=WHITE)
text(0.45, 0.58, 9.8, 0.28,
     [[("Pre-Screening Target Complexes Before Wet-Lab Assays  |  ", {"size": 11, "bold": True, "color": ICE}),
       ("Zhang et al., Science 2025 + Pei et al., Sci Rep 2026", {"size": 11, "color": ICE, "italic": True})]])
text(10.35, 0.20, 2.53, 0.52,
     [[("PROPOSAL  |  RIC-410", {"size": 11, "bold": True, "color": WHITE})],
      [("2026-10-28  |  Novo Nordisk", {"size": 9.5, "color": ICE})]],
     align=PP_ALIGN.RIGHT, space_after=2)

# ==============================================================================
# 2. Left Panel: Biological Motivation & In-House Validation (x=0.45, w=6.10)
# ==============================================================================
LP_X, LP_W = 0.45, 6.10
rect(LP_X, 1.15, LP_W, 5.87, LIGHT, line=BORDER)
rect(LP_X, 1.15, LP_W, 0.36, TEAL)
text(LP_X + 0.16, 1.21, LP_W - 0.32, 0.26,
     "1. Why It Matters & In-House Validation (33,000 Benchmark Pairs)",
     size=11.5, bold=True, color=WHITE)

# 4 Hero KPI Callout Cards (y=1.62, h=0.84)
kpis = [
    ("262x", "vs Random Screening", "AUC 0.262 vs 0.001 (1:1000)", NAVY),
    ("43.2%", "Large-Complex Recall", "At >=90% precision (51.8% @0.5)", TEAL),
    ("0.919", "Author Score Parity", "Pearson r across 8,977 pairs", NAVY),
    ("~6 hrs", "Per Target Screen", "1 bait vs 20,260 human proteins", RED),
]
kw = 1.38
kgap = 0.10
kx = LP_X + 0.14
for val, lbl, sub, col in kpis:
    rect(kx, 1.62, kw, 0.84, WHITE, line=BORDER)
    rect(kx, 1.62, kw, 0.05, col)
    text(kx + 0.06, 1.70, kw - 0.12, 0.32, val, size=16.0, bold=True, color=col, align=PP_ALIGN.CENTER)
    text(kx + 0.04, 2.05, kw - 0.08, 0.18, lbl, size=8.5, bold=True, color=INK, align=PP_ALIGN.CENTER)
    text(kx + 0.04, 2.24, kw - 0.08, 0.18, sub, size=7.5, color=GREY, align=PP_ALIGN.CENTER)
    kx += kw + kgap

# 2-Panel Evidence Plot (PR curve + Biological Interface Size Recall) (y=2.56, h=2.45)
IMG = "/das/user/QYJI/druggability/humanPPI_repro/results/repro_2panel_evidence.png"
img_w = LP_W - 0.28  # 5.82 in
img_h = img_w * (3.15 / 7.6)  # 2.41 in
rect(LP_X + 0.14, 2.56, img_w, 2.45, WHITE, line=BORDER)
slide.shapes.add_picture(IMG, Inches(LP_X + 0.16), Inches(2.58), Inches(img_w - 0.04), Inches(2.41))

# Bottom Evidence Box: 3 Biology-First Takeaways (y=5.11, h=1.78)
rect(LP_X + 0.14, 5.11, LP_W - 0.28, 1.78, WHITE, line=BORDER)
rect(LP_X + 0.14, 5.11, 0.07, 1.78, TEAL)

ev_rows = [
    ("Biological Bottleneck (FACT)",
     "Affinity purification (AP-MS / co-IP) often misses low-abundance or membrane complexes. Zhang et al. (Science 2025) identified 17,849 high-precision human PPIs (3,631 novel) with 29,246 3D structures.",
     TEAL, 5.17),
    ("Why Recall is 20.8% Overall (MECH)",
     "At realistic 1:1000 proteome odds, sensitivity depends on contact area: 43.2% recall on large stable complexes (>1500 A2) vs 4.5% on small transient motifs (<800 A2). Balanced 1:1 AUC = 0.813.",
     NAVY, 5.73),
    ("Human Genetics Proof-of-Concept (OBS)",
     "On Calcium-Sensing Receptor (CASR), our module mapped 89 clinical pathogenic mutations (HHC1/HYPOC1); 64% cluster directly at the ECD dimerization interface (<=612), confirming biological validity.",
     NAVY, 6.29),
]
for etitle, ebody, ecol, ey in ev_rows:
    text(LP_X + 0.28, ey, LP_W - 0.48, 0.52, [
        [(etitle + ": ", {"size": 8.8, "bold": True, "color": ecol}),
         (ebody, {"size": 8.4, "color": INK})]
    ], space_after=0)

# ==============================================================================
# 3. Right Panel Top: Biologist-Friendly 4-Step Workflow (x=6.75, w=6.13, y=1.15, h=2.70)
# ==============================================================================
RP_X, RP_W = 6.75, 6.13
rect(RP_X, 1.15, RP_W, 2.70, ICE, line=BORDER)
rect(RP_X, 1.15, RP_W, 0.36, NAVY)
text(RP_X + 0.16, 1.21, RP_W - 0.32, 0.26,
     "2. From Target of Interest to Wet-Lab Assay Design (~6 Hours / Target)",
     size=11.5, bold=True, color=WHITE)

steps = [
    ("Step 1: Target Input", "1 Bait Protein",
     "Provide any target UniProt ID; screened against 20,260 human proteins with deep evolutionary alignments", NAVY),
    ("Step 2: Partner Screen", "Binding Probability",
     "Rapid coevolutionary & structural scoring (~6h on 6 GPUs); calibrated against our local 90% precision cutoff", NAVY),
    ("Step 3: 3D & Genetics", "Interface Mapping",
     "3D complex model (6A contact residues) + clinical disease-mutation enrichment (ClinVar / UniProt / AlphaMissense)", TEAL),
    ("Step 4: Assay Design", "Wet-Lab Handoff",
     "Top-N partner list + exact interface point-mutations to design negative controls for co-IP / BioID / BRET", RED),
]
sw_box = 1.32
sgap = 0.19
sx = RP_X + 0.14
for idx, (st_hdr, st_sub, st_body, st_col) in enumerate(steps):
    rect(sx, 1.62, sw_box, 1.34, WHITE, line=BORDER)
    rect(sx, 1.62, sw_box, 0.27, st_col)
    text(sx + 0.05, 1.66, sw_box - 0.10, 0.20, st_hdr, size=8.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    text(sx + 0.05, 1.94, sw_box - 0.10, 0.19, st_sub, size=8.8, bold=True, color=st_col, align=PP_ALIGN.CENTER)
    text(sx + 0.06, 2.15, sw_box - 0.12, 0.76, st_body, size=7.6, color=INK, align=PP_ALIGN.LEFT)
    if idx < 3:
        ch = slide.shapes.add_shape(
            MSO_SHAPE.CHEVRON, Inches(sx + sw_box + 0.03), Inches(2.17), Inches(0.13), Inches(0.24)
        )
        ch.fill.solid()
        ch.fill.fore_color.rgb = TEAL
        ch.line.fill.background()
    sx += sw_box + sgap

# Value proposition strip inside top-right panel (y=3.05, h=0.68)
rect(RP_X + 0.14, 3.05, RP_W - 0.28, 0.68, WHITE, line=BORDER)
rect(RP_X + 0.14, 3.05, 0.07, 0.68, NAVY)
text(RP_X + 0.28, 3.11, RP_W - 0.48, 0.56, [
    [("What Biology Teams Receive per Candidate: ", {"size": 8.8, "bold": True, "color": NAVY}),
     ("(1) Calibrated binding confidence, (2) 3D complex structure with pocket/interface coordinates, and (3) Human genetic disease variants at the contact surface — directly guiding mutational validation.",
      {"size": 8.5, "color": INK})]
])

# ==============================================================================
# 4. Right Panel Bottom: Biological Scope Matrix & Campaign Pilot (y=3.98, h=3.04)
# ==============================================================================
rect(RP_X, 3.98, RP_W, 3.04, LIGHT, line=BORDER)
rect(RP_X, 3.98, RP_W, 0.36, RED)
text(RP_X + 0.16, 4.04, RP_W - 0.32, 0.26,
     "3. Biological Fit Matrix, Golden Rule & Cardiometabolic Pilot",
     size=11.5, bold=True, color=WHITE)

# Side-by-side 2-column matrix: Best Suited For (TEAL) vs Known Blind Spots (RED) (y=4.43, h=1.18)
col_w = (RP_W - 0.40) / 2  # 2.865 in each
# Left box: Best Suited For
rect(RP_X + 0.14, 4.43, col_w, 1.18, GREEN_BG, line=TEAL, line_w=1.0)
rect(RP_X + 0.14, 4.43, col_w, 0.24, TEAL)
text(RP_X + 0.22, 4.46, col_w - 0.16, 0.20, "IDEAL TARGETS (HIGH SENSITIVITY)", size=8.5, bold=True, color=WHITE)
text(RP_X + 0.22, 4.71, col_w - 0.16, 0.86, [
    [("• Obligate & constitutive complexes ", {"size": 8.2, "bold": True, "color": TEAL}),
     ("(43.2% recall on interfaces >1500 A2)", {"size": 8.0, "color": INK})],
    [("• Transmembrane & organelle complexes ", {"size": 8.2, "bold": True, "color": TEAL}),
     ("hard to solubilize in standard AP-MS", {"size": 8.0, "color": INK})],
    [("• Endogenous receptor / enzyme complexes ", {"size": 8.2, "bold": True, "color": TEAL}),
     ("& genetic disease-linked interfaces", {"size": 8.0, "color": INK})],
], space_after=1.5)

# Right box: Blind Spots
rx2 = RP_X + 0.14 + col_w + 0.12
rect(rx2, 4.43, col_w, 1.18, RED_BG, line=RED, line_w=1.0)
rect(rx2, 4.43, col_w, 0.24, RED)
text(rx2 + 0.08, 4.46, col_w - 0.16, 0.20, "BLIND SPOTS (DO NOT EXCLUDE)", size=8.5, bold=True, color=WHITE)
text(rx2 + 0.08, 4.71, col_w - 0.16, 0.86, [
    [("• Transient / PTM-triggered signaling ", {"size": 8.2, "bold": True, "color": RED}),
     ("(e.g., GPCR-arrestin, kinase-substrate)", {"size": 8.0, "color": INK})],
    [("• Disordered short linear motifs (SLiMs) ", {"size": 8.2, "bold": True, "color": RED}),
     ("(4.5% recall on interfaces <800 A2)", {"size": 8.0, "color": INK})],
    [("• Immune receptors (TCR/BCR/MHC) ", {"size": 8.2, "bold": True, "color": RED}),
     ("& fast-evolving / lineage-specific pairs", {"size": 8.0, "color": INK})],
], space_after=1.5)

# Bottom 2 full-width cards (y=5.69 and y=6.33)
bot_cards = [
    ("Prospective Validation (2024–2026 Time-Split Audit)",
     "11 'zero-prior-evidence' pairs in Data S6 (cutoff Sep 2023) have since been independently proved by cryo-EM or co-IP — e.g., DND1-NANOS3 (Mol Cell 2026), DHX35-GPATCH1 (Cell Res 2025), EFCAB10-AK8 & MTR-MMADHC (PNAS 2025/26), TMEM209-NUP210 (JCS 2026).",
     TEAL, 5.69),
    ("Immediate Pilot — 99 Cardiometabolic Novel PPI Leads (Data S6)",
     "Prioritize our 99 unflagged novel PPI leads across 5 indications (Obesity, T2D, CKD, MASH, CVD; Tier A/B/C targets) by integrating local PR precision, GTEx co-expression, and interface pathogenic SAV burden -> nominate Top-10 for co-IP.",
     NAVY, 6.33),
]
for btitle, bbody, bcol, by in bot_cards:
    rect(RP_X + 0.14, by, RP_W - 0.28, 0.58, WHITE, line=BORDER)
    rect(RP_X + 0.14, by, 0.07, 0.58, bcol)
    text(RP_X + 0.28, by + 0.05, RP_W - 0.48, 0.48, [
        [(btitle + ": ", {"size": 8.8, "bold": True, "color": bcol}),
         (bbody, {"size": 8.2, "color": INK})]
    ], space_after=0)

# ==============================================================================
# 5. Footer Bar (y=7.12, h=0.28)
# ==============================================================================
text(0.45, 7.12, 12.43, 0.28,
     "References: Zhang et al., Science 390, eadt1630 (2025) | Pei, Zhang & Cong, Sci Rep 16:25590 (2026) | Lambourne et al., Nat Commun (2026)  —  "
     "Pipeline: druggability repo (RIC-410)",
     size=8.0, color=GREY)

# ==============================================================================
# 6. Speaker Notes (Biology-first Chinese oral script + Q&A defense)
# ==============================================================================
notes_slide = slide.notes_slide
notes_tf = notes_slide.notes_text_frame
notes_tf.text = """【面向生物学与管理团队的汇报口播讲稿（约 2 分钟）】

1. 生物学痛点与为什么建这套能力（左栏顶部 + 底部第 1 条，30 秒）：
- 在靶点发现和机制研究里，我们经常要问：我的靶点蛋白在体内到底和谁直接结合？结合界面在哪？传统 AP-MS 或 co-IP 容易漏掉低丰度蛋白或跨膜蛋白复合物，而且给不出原子级结构。
- 去年底 Baker 与 Cong 实验室在 Science 发表了全人类蛋白组互作图谱（从 2 亿对里筛出 17,849 个 90% 精度的直接互作，以及近 3 万个 3D 结构模型），今年又在 Sci Rep 发表了把临床疾病突变映射到互作界面的方法。
- 我们在内部 6 张 A100 上把这套方法在 33,000 对基准集上完整复现并验证通过：与原作者分数的相关性达 0.919，单靶点扫遍全人类 2 万个蛋白只需约 6 小时。

2. 为什么总召回率是 20.8%，以及哪些生物学体系最管用？（左中双图 Panel A & B，40 秒）：
- 大家看左边的两张图：Panel A 是在全蛋白组真实 1:1000 极低信噪比下的表现——随机盲猜的基线只有 0.001，我们的 AUC 是 0.262，相当于把命中率浓缩富集了 **262 倍**（如果按常规 1:1 平衡集算 AUC 是 0.813）。在 >=90% 精度阈值下，前 623 个阳性预测零假阳性。
- 更有生物学指导意义的是右边的 **Panel B（按结合界面大小分层）**：为什么总体召回率是 20.8%？因为模型对**大界面、稳定结合的复合物（>1500 Å²）召回率高达 43.2%（中等阈值下 51.8%）**；而对**小界面、瞬时结合的短线性基序（<800 Å²）召回率只有 4.5%**。这从物理机制上告诉我们：它是一台专抓“稳定结构复合物”的高精度显微镜。

3. 生物团队能拿到什么交付物？（右上四步流程 + 右下红绿对照矩阵，50 秒）：
- 给一个靶点 UniProt ID，6 小时后我们交付给生物团队三样东西：（1）校准过精度的候选结合伙伴排序；（2）3D 复合物结构与 6 Å 接触面残基；（3）接触面上的临床致病突变富集（比如我们在钙敏感受体 CASR 上实测，89 个临床致病突变中 64% 精准落在胞外二聚化界面上）。这意味着生物学家拿到的不仅是一个蛋白名字，连做 co-IP 负对照所需的**界面点突变设计（disruptor mutations）**都直接配齐了。
- 右下角我们用红绿矩阵明确了适用边界：
  • **最适合（绿色）**：稳定/内源复合物（召回 43%）、难溶跨膜蛋白复合物（比如今年 J Cell Sci 刚用它实验证实的核孔跨膜蛋白 TMEM209-Nup210）、以及内源受体/酶调控复合物。
  • **天然盲区（红色，绝不用作阴性排除）**：磷酸化/配体触发的瞬时信号复合物（如 GPCR-arrestin）、无序区短基序（SLiMs）、以及体细胞重组免疫受体。
- **立即落地的 Pilot（代谢心血管 Data S6 99 个候选对）**：针对前期从 2,700 个全新预测 PPI（Data S6）中筛出的 **99 个代谢心血管（Obesity/T2D/CKD/MASH/CVD，Tier A/B/C）单靶点新伙伴候选对**，我们将结合本地精度校准、GTEx 组织共表达和界面致病突变负担重新分级，挑出 Top-10（附带界面点突变负对照设计）交由湿实验做 co-IP 验证。
"""

out_pptx = "/das/user/QYJI/druggability/reports/ppi_screening_proposal_2026-10-28.pptx"
prs.save(out_pptx)
print("Saved biology-friendly PPTX:", out_pptx)
