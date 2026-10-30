#!/usr/bin/env python
"""One-page proposal slide: RF2-PPI-based target screening capability (Group Meeting Edition).

Explicitly answers leadership's two questions:
  1. Summary of what David Baker & Qian Cong's teams achieved (Science 2025 + Sci Rep 2026) & our in-house validation
  2. What the Business Question for the Campaign is (3 Candidate Business Questions + Immediate Pilot Decision)

NN corporate palette (#001965 / #00857C / #D9383A). 16:9 widescreen (13.333 x 7.5 in).
Includes speaker notes (Chinese oral script + Q&A defense).
"""
from pptx import Presentation
from pptx.util import Inches, Pt
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
text(0.45, 0.14, 10.10, 0.38,
     "Proteome-Wide PPI & Disease-Interface Triage: Baker Summary & Business Questions",
     size=17.5, bold=True, color=WHITE)
text(0.45, 0.56, 10.10, 0.28,
     [[("What Baker & Cong Achieved + Campaign Business Questions  |  ", {"size": 10.5, "bold": True, "color": ICE}),
       ("Zhang et al., Science 2025 + Pei et al., Sci Rep 2026", {"size": 10.5, "color": ICE, "italic": True})]])
text(10.60, 0.18, 2.28, 0.54,
     [[("GROUP MEETING  |  RIC-410", {"size": 10.5, "bold": True, "color": WHITE})],
      [("2026-10-29  |  Novo Nordisk", {"size": 9.2, "color": ICE})]],
     align=PP_ALIGN.RIGHT, space_after=2)

# ==============================================================================
# 2. Left Panel: What David Baker & Qian Cong Achieved + In-House Validation (x=0.45, w=6.10)
# ==============================================================================
LP_X, LP_W = 0.45, 6.10
rect(LP_X, 1.15, LP_W, 5.87, LIGHT, line=BORDER)
rect(LP_X, 1.15, LP_W, 0.36, TEAL)
text(LP_X + 0.16, 1.21, LP_W - 0.32, 0.26,
     "1. Baker & Cong's Achievement (Science 2025) & In-House Reproduction",
     size=11.0, bold=True, color=WHITE)

# 4 Hero KPI Callout Cards (y=1.62, h=0.84) — Single unified TextFrame per KPI card
kpis = [
    ("200M->17.8k", "Baker Interactome", "3,631 novel @90% (2,700 S6)", NAVY),
    ("262x", "In-House Enrichment", "AUCPR 0.262 vs 0.001 (1:1000)", TEAL),
    ("43.2%", "Large-Complex Recall", "Interfaces >1500 A2 (r=0.919)", NAVY),
    ("~6 hrs", "Per-Target Screen", "1 bait vs 20,260 proteins", RED),
]
kw = 1.38
kgap = 0.10
kx = LP_X + 0.14
for val, lbl, sub, col in kpis:
    rect(kx, 1.62, kw, 0.84, WHITE, line=BORDER)
    rect(kx, 1.62, kw, 0.05, col)
    text(kx + 0.03, 1.70, kw - 0.06, 0.72, [
        [(val, {"size": 13.5, "bold": True, "color": col})],
        [(lbl, {"size": 8.3, "bold": True, "color": INK})],
        [(sub, {"size": 7.1, "color": GREY})],
    ], align=PP_ALIGN.CENTER, space_after=1.5)
    kx += kw + kgap

# 2-Panel Evidence Plot (PR curve + Biological Interface Size Recall) (y=2.56, h=2.45)
IMG = "/das/user/QYJI/druggability/humanPPI_repro/results/repro_2panel_evidence.png"
img_w = LP_W - 0.28  # 5.82 in
rect(LP_X + 0.14, 2.56, img_w, 2.45, WHITE, line=BORDER)
slide.shapes.add_picture(IMG, Inches(LP_X + 0.16), Inches(2.58), Inches(img_w - 0.04), Inches(2.41))

# Bottom Evidence Box: Single Textbox with 3 Paragraphs -> impossible to self-collide! (y=5.11, h=1.80)
rect(LP_X + 0.14, 5.11, LP_W - 0.28, 1.80, WHITE, line=BORDER)
rect(LP_X + 0.14, 5.11, 0.07, 1.80, TEAL)

text(LP_X + 0.28, 5.15, LP_W - 0.48, 1.72, [
    [("2025 Science vs 2026 Sci Rep Division (FACT): ", {"size": 8.4, "bold": True, "color": TEAL}),
     ("2025 built the engine (7x omicMSAs, 17x AFDB DDI training -> RF2-PPI; 191M->111.2M->43.6M->1.9M funnel; 17,849 PPIs @90% prec [de novo + prior-guided], 3,631 novel, 2,700 Data S6 lacking complex templates, 1,413 uncharacterized). 2026 mined 2025 models for disease SAVs & AF3 assemblies.",
      {"size": 7.9, "color": INK})],
    [("Why Recall is 20.8% Overall & Where It Excels (MECH): ", {"size": 8.4, "bold": True, "color": NAVY}),
     ("At realistic 1:1000 proteome odds (balanced 1:1 AUC=0.813), recall is 43.2% on large stable complexes (>1500 A2) vs 4.5% on small transient SLiMs (<800 A2). Over half of 2,700 Data S6 novel PPIs (1,556; 58%) are transmembrane complexes missed by AP-MS.",
      {"size": 7.9, "color": INK})],
    [("Prospective Audit & Variant Interpretation Caveat (OBS): ", {"size": 8.4, "bold": True, "color": NAVY}),
     ("11 Data S6 pairs (cutoff Sep 2023) are now proved by cryo-EM/co-IP (DND1-NANOS3, DHX35-GPATCH1, TMEM209-NUP210). On CASR, 64% of 89 pathogenic SAVs map to the ECD dimer interface (note: interface SAVs propose testable disruption hypotheses, not proof of loss-of-binding).",
      {"size": 7.9, "color": INK})],
], space_after=3.5)

# ==============================================================================
# 3. Right Panel Top: Campaign Business Question Menu (3 Candidate Questions) (x=6.75, w=6.13, y=1.15, h=3.02)
# ==============================================================================
RP_X, RP_W = 6.75, 6.13
rect(RP_X, 1.15, RP_W, 3.02, ICE, line=BORDER)
rect(RP_X, 1.15, RP_W, 0.36, NAVY)
text(RP_X + 0.16, 1.21, RP_W - 0.32, 0.26,
     "2. Campaign Business Question Menu (3 Candidate Questions for Alignment)",
     size=11.0, bold=True, color=WHITE)

bq_cards = [
    ("BQ-1: Portfolio Partner Mining", "99 Leads -> 8 Pass All 4/4",
     "Strict 4-Criteria Triage on 99 Data S6 cardiometabolic leads (C1 Both-Genetics 60 [46 Human], C2 Pathway 43, C3 Direct Perturb. 14, C4 CM Co-expr 56) -> 8 pass all 4/4 (#1 RAMP3-MRAP2, #2 RAMP1-MRAP2).",
     NAVY),
    ("BQ-2: De Novo Target Screen", "1 Bait vs 20,260 Proteins",
     "For an internal priority receptor/enzyme (especially transmembrane or organelle targets where detergent AP-MS fails), what is its missing endogenous co-receptor, trafficking chaperone, or E3 ligase (~6 GPU-h/target)?",
     TEAL),
    ("BQ-3: Disease-Interface Assay", "3D Pocket & Disruptor Mutants",
     "Given a target complex or human genetics signal, where is the exact 6A contact surface and which clinical pathogenic variants (ClinVar/AlphaMissense) sit at the interface to design point-mutant negative controls?",
     RED),
]
bw_box = 1.85
bgap = 0.15
bx = RP_X + 0.14
for bq_hdr, bq_sub, bq_body, bq_col in bq_cards:
    rect(bx, 1.60, bw_box, 1.72, WHITE, line=BORDER)
    rect(bx, 1.60, bw_box, 0.26, bq_col)
    text(bx + 0.04, 1.64, bw_box - 0.08, 0.20, bq_hdr, size=8.0, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    text(bx + 0.04, 1.89, bw_box - 0.08, 0.20, bq_sub, size=7.8, bold=True, color=bq_col, align=PP_ALIGN.CENTER)
    text(bx + 0.06, 2.11, bw_box - 0.12, 1.16, bq_body, size=7.4, color=INK, align=PP_ALIGN.LEFT)
    bx += bw_box + bgap

# Deliverable Strip inside top-right panel (y=3.40, h=0.68)
rect(RP_X + 0.14, 3.40, RP_W - 0.28, 0.68, WHITE, line=BORDER)
rect(RP_X + 0.14, 3.40, 0.07, 0.68, NAVY)
text(RP_X + 0.28, 3.45, RP_W - 0.48, 0.58, [
    [("End-to-End Handoff to Wet-Lab (~6 GPU-h / Target): ", {"size": 8.4, "bold": True, "color": NAVY}),
     ("(1) Calibrated partner probability (@90% precision cutoff), (2) 3D complex coordinates (6A contact residues), and (3) Interface pathogenic variants (Pei et al. 2026) -> exact point-mutant negative controls for co-IP / BioID / BRET.",
      {"size": 8.0, "color": INK})]
])

# ==============================================================================
# 4. Right Panel Bottom: Biological Scope Matrix & Campaign Pilot Decision (y=4.28, h=2.74)
# ==============================================================================
rect(RP_X, 4.28, RP_W, 2.74, LIGHT, line=BORDER)
rect(RP_X, 4.28, RP_W, 0.36, RED)
text(RP_X + 0.16, 4.34, RP_W - 0.32, 0.26,
     "3. Biological Fit Matrix, Golden Rule & Proposed Pilot Decision",
     size=11.0, bold=True, color=WHITE)

# Side-by-side 2-column matrix: Best Suited For (TEAL) vs Known Blind Spots (RED) (y=4.72, h=1.12)
col_w = (RP_W - 0.40) / 2  # 2.865 in each
rect(RP_X + 0.14, 4.72, col_w, 1.12, GREEN_BG, line=TEAL, line_w=1.0)
rect(RP_X + 0.14, 4.72, col_w, 0.23, TEAL)
text(RP_X + 0.22, 4.75, col_w - 0.16, 0.18, "IDEAL TARGETS (HIGH SENSITIVITY)", size=8.2, bold=True, color=WHITE)
text(RP_X + 0.22, 4.98, col_w - 0.16, 0.84, [
    [("• Obligate & constitutive complexes ", {"size": 7.8, "bold": True, "color": TEAL}),
     ("(43.2% recall on interfaces >1500 A2)", {"size": 7.6, "color": INK})],
    [("• Transmembrane & organelle complexes ", {"size": 7.8, "bold": True, "color": TEAL}),
     ("(58% of Data S6; missed by detergent AP-MS)", {"size": 7.6, "color": INK})],
    [("• Co-receptors, chaperones & enzymes ", {"size": 7.8, "bold": True, "color": TEAL}),
     ("with human genetic variants at interface", {"size": 7.6, "color": INK})],
], space_after=1.0)

rx2 = RP_X + 0.14 + col_w + 0.12
rect(rx2, 4.72, col_w, 1.12, RED_BG, line=RED, line_w=1.0)
rect(rx2, 4.72, col_w, 0.23, RED)
text(rx2 + 0.08, 4.75, col_w - 0.16, 0.18, "BLIND SPOTS (DO NOT EXCLUDE)", size=8.2, bold=True, color=WHITE)
text(rx2 + 0.08, 4.98, col_w - 0.16, 0.84, [
    [("• Transient / PTM-triggered signaling ", {"size": 7.8, "bold": True, "color": RED}),
     ("(e.g., GPCR-arrestin, kinase-substrate)", {"size": 7.6, "color": INK})],
    [("• Disordered short linear motifs (SLiMs) ", {"size": 7.8, "bold": True, "color": RED}),
     ("(4.5% recall on interfaces <800 A2)", {"size": 7.6, "color": INK})],
    [("• Immune receptors (TCR/BCR/MHC) ", {"size": 7.8, "bold": True, "color": RED}),
     ("& lineage-specific / paralog swaps", {"size": 7.6, "color": INK})],
], space_after=1.0)

# Bottom 2 full-width cards (y=5.91 and y=6.45)
bot_cards = [
    ("Golden Rule for Campaign Governance",
     "Use strictly as a POSITIVE hypothesis generator & 3D assay design tool — never discard a biologically supported candidate due to a low score (confirmed by Lambourne et al., Nat Commun 2026).",
     TEAL, 5.91),
    ("Phase-1 Pilot Executed (BQ-1 4-Criteria Triage + Docking / MD / FEP)",
     "8/99 cardiometabolic leads pass all 4 strict criteria (6 with human GWAS/ClinVar on both proteins: #1 RAMP3-MRAP2, #2 RAMP1-MRAP2, #3 NR3C1-FOXO3). #1 RAMP3-MRAP2 verified by Boltz-2 (ipTM=0.868), MD (0.49A) & FEP.",
     NAVY, 6.45),
]
for btitle, bbody, bcol, by in bot_cards:
    rect(RP_X + 0.14, by, RP_W - 0.28, 0.50, WHITE, line=BORDER)
    rect(RP_X + 0.14, by, 0.07, 0.50, bcol)
    text(RP_X + 0.28, by + 0.04, RP_W - 0.48, 0.44, [
        [(btitle + ": ", {"size": 8.2, "bold": True, "color": bcol}),
         (bbody, {"size": 7.7, "color": INK})]
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
notes_tf.text = """【组会 5–10 分钟汇报单页口播讲稿（紧扣领导两个问题：1. Baker 团队做成了什么？2. 我们的 Business Question 是什么？）】

一、David Baker 与 Qian Cong 团队到底做成了什么？（左栏，约 2.5 分钟）
1. 为什么以前全人类蛋白组 PPI 预测做不准？
   - 酵母和细菌早就能全基因组算 PPI，但人类蛋白组有 2 亿对可能组合（真实互作约 7.4万–20万对，信噪比低至 1:1000），而且高等真核生物演化历史短、缺少共进化信号，同时 AlphaFold2 太慢（扫 2 亿对需要几十万 GPU 年）。
2. Baker & Cong 团队（Science 2025 + Sci Rep 2026）的三大突破与双文递进关系：
   - 2025 Science（造引擎 + 全蛋白组筛查）：（1）从 NCBI 未组装的 30 PB 原始真核测序数据（21,415 个物种）中用考虑 mRNA 剪接的管线拼出同源序列，把人类蛋白 MSA 深度提升了 7 倍；（2）从 2 亿个 AFDB 单体结构中蒸馏出 22.3 万个结构域互作（比已知 PDB 训练集扩大 17 倍），并且加入阴性非互作对训练出轻量级网络 RF2-PPI（比 AF2 快 20 倍）；（3）对 19,528 个蛋白（1.91 亿对）走四级过滤（共定位 1.112 亿 -> DCA 4360 万 -> RF2-PPI 190 万 -> AF2 建模），筛出 17,849 个 >=90% 精度的高置信互作（3,631 个此前未见报道，2,700 个无同源复合物模板即 Data S6，1,413 个涉及未知功能暗蛋白）。
   - 2026 Sci Rep（案例深挖与高阶组装）：没有重训模型或重跑筛查，而是基于 2025 年预测模型深入解析界面致病突变（如 C12orf57 L51Q、BBS7-WDR19 V80D、SCO1-COA6）并用 AlphaFold3 组装多亚基复合物（如 NRZ 新亚基 C19orf25、BLOC-1/BORC）。
3. 我们的内部完整复现与前瞻性检验（左中双图 + 左下）：
   - 我们在 6 张 A100 上完整复现了 33,000 对基准集：在真实 1:1000 极低信噪比下 AUCPR 达 0.262（相比随机盲筛浓缩富集 262 倍；1:1 平衡集 AUC=0.813），与原作者打分相关性 r=0.919。
   - 物理机制拆解（Panel B）：为什么总体召回率是 20.8%？因为对大界面稳定复合物（>1500 Å²）召回率高达 43.2%（中等阈值 51.8%），而对小界面瞬时短基序（<800 Å²）只有 4.5%。更关键的是，Data S6 的 2,700 个全新 PPI 中有 58%（1,556 对）是跨膜或细胞器膜蛋白——这恰恰是传统去垢剂裂解 AP-MS / co-IP 最容易漏掉的盲区。
   - 2024–2026 前瞻性时间切片验证：Data S6 的数据库截点是 2023 年 9 月；过去两年里，已有 11 个当年“零先验”的预测对被独立实验室用 Cryo-EM 或内源 co-IP 证实（且过半是跨膜/细胞器复合物，如核孔跨膜蛋白 TMEM209-NUP210、线粒体 MTR-MMADHC、生殖颗粒 DND1-NANOS3）。

二、我们这项 Campaign 的 Business Question 是什么？（右栏，约 2.5 分钟）
针对我们心代与罕见病管线，我们梳理了 3 个层级的候选 Business Questions 供团队拍板：
1. BQ-1（存量管线靶点的新调控伙伴挖掘 — 现成可立即启动）：
   - 在 Baker 的 2,700 个零先验新 PPI（Data S6）中，前期已用 Open Targets + 内部管线（656 个心代靶点）筛出 198 对单靶点互作，剔除同家族/泛靶点假象后得到 **99 个干净的未标记新互作假设（Unflagged Leads）**，包含 18 个 Tier A 已上市药靶点对和 8 个内部管线靶点对（如 Amylin/CagriSema 相关的 RAMP1/2/3 与 NMUR1/MRAP2/CEND1、CKD 靶点 CASR 与 CABP7/CALN1、心衰靶点 TTR 与 ANK1）。
   - 业务问题：这 99 个新伙伴中，哪些在疾病靶器官真正共表达、界面携带人类遗传学致病突变，值得提名 Top-10 上湿实验做 co-IP 验证？
2. BQ-2（高优疑难/跨膜靶点的全蛋白组从头筛查 — 按需定制服务）：
   - 当生物团队手头有一个孤儿受体、跨膜转运体或胞内靶点，常规 AP-MS 找不到内源辅助受体（co-receptor）、转运伴侣（chaperone）或组织特异性 E3 连接酶时，我们用 ~6 GPU 小时把该靶点对全人类 20,260 个蛋白通扫一遍，给出高置信候选伙伴。
3. BQ-3（疾病突变界面映射与湿实验点突变负对照设计 — 实验赋能）：
   - 不仅给名字，还给原子级 3D 结合面（6 Å）+ 临床致病突变富集（如我们在 CASR 上验证 64% 致病突变落在二聚化界面；注意界面突变代表可检验的结合破坏假设，需湿实验验证），直接为生物团队设计 co-IP / BRET 的点突变破坏对照（disruptor mutant negative controls）。

三、治理铁律与今日拍板建议（右下）：
- 黄金法则：只作阳性假设生成与结构赋能工具，绝不用低分枪毙生物团队已有的候选假设。
- 建议首期 Pilot：立即启动 BQ-1 + BQ-3（用本地精度校准 + GTEx 靶器官共表达 + 界面致病突变把 99 个心代 Data S6 leads 浓缩到 Top-10 交付湿实验），同时开放征集 1–2 个生物团队最头疼的跨膜靶点试跑 BQ-2。
"""

out_pptx = "/das/user/QYJI/druggability/reports/ppi_screening_proposal_2026-10-28.pptx"
prs.save(out_pptx)
print("Saved group-meeting-optimized One-Pager PPTX:", out_pptx)
