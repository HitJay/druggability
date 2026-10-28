#!/usr/bin/env python
"""One-page proposal slide: RF2-PPI-based target screening capability.

NN corporate palette. 16:9 widescreen. python-pptx (no LibreOffice/node on this host).
Layout: title bar -> 4-panel grid (left: method+repro evidence w/ PR curve;
right-top: capability numbers; right-bottom: pipeline + positioning).
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY = RGBColor(0x00, 0x19, 0x65)
TEAL = RGBColor(0x00, 0x85, 0x7C)
RED = RGBColor(0xD9, 0x38, 0x3A)
INK = RGBColor(0x1A, 0x1A, 0x2E)
GREY = RGBColor(0x5A, 0x60, 0x70)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xE8, 0xEE, 0xF7)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
W, H = 13.333, 7.5


def rect(x, y, w, h, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def text(x, y, w, h, runs, size=12, bold=False, color=INK, align=PP_ALIGN.LEFT,
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


# ---------- background + header ----------
rect(0, 0, W, H, WHITE)
rect(0, 0, W, 1.02, NAVY)
text(0.55, 0.16, 9.6, 0.5, "Computational PPI screening for target triage", size=25,
     bold=True, color=WHITE)
text(0.55, 0.66, 9.9, 0.3,
     [[("Reproduced RF2-PPI (Zhang et al., Science 2025) ", {"size": 12, "color": ICE}),
       ("+ disease-variant interface mapping (Pei et al., Sci Rep 2026)", {"size": 12, "color": ICE, "italic": True})]])
text(10.7, 0.30, 2.2, 0.4, "RIC-410  |  2026-10-28", size=11, color=ICE, align=PP_ALIGN.RIGHT)

# ---------- left panel: evidence ----------
LP_X, LP_W = 0.55, 6.15
rect(LP_X, 1.35, LP_W, 5.75, LIGHT)
rect(LP_X, 1.35, LP_W, 0.42, TEAL)
text(LP_X + 0.15, 1.41, LP_W - 0.3, 0.3, "Independent reproduction - it works here", size=13.5,
     bold=True, color=WHITE)

# PR curve image (1280x960 px -> 4:3)
IMG = "/das/user/QYJI/druggability/humanPPI_repro/results/pr_curve.png"
img_w = 3.55
img_h = img_w * 0.75
slide.shapes.add_picture(IMG, Inches(LP_X + 0.18), Inches(1.98), Inches(img_w), Inches(img_h))

# stats right of image
SX = LP_X + 3.95
SXW = LP_W - 4.12
rows = [
    ("Pearson r", "0.919", "vs author-released scores"),
    ("Spearman r", "0.901", "8,977 pairs, full cross-check"),
    ("90% precision", "recall 20.8%", "top 623 pairs: zero false positives"),
    ("Weighted AUCPR", "0.262", "S/N 1:1000 (paper convention)"),
    ("Mean |diff|", "0.045", "89.7% of pairs within 0.1"),
]
y = 1.95
for name, val, sub in rows:
    text(SX, y, SXW, 0.58,
         [[(name + "  ", {"size": 10.5, "color": GREY}),
           (val, {"size": 13, "bold": True, "color": NAVY})],
          [(sub, {"size": 8.5, "color": GREY})]], space_after=0)
    y += 0.70
text(SX, y + 0.00, SXW, 0.55,
     [[("33k-pair benchmark, 6x A100, ~10 h. ", {"size": 9, "bold": True, "color": INK}),
       ("Residual differences match the method's documented inference stochasticity.",
        {"size": 9, "color": INK, "italic": True})]])

# bottom strip: paper scale
rect(LP_X + 0.18, 6.28, LP_W - 0.36, 0.68, WHITE, line=ICE)
text(LP_X + 0.32, 6.38, LP_W - 0.6, 0.5,
     [[("Paper scale: ", {"size": 9.5, "bold": True, "color": TEAL}),
       ("200M human pairs screened; 17,849 interactions at 90% expected precision; "
        "3,631 with no prior experimental evidence; high-quality 3D models for 29,246 complexes.",
        {"size": 9.5, "color": INK})]])

# ---------- right panel ----------
RP_X, RP_W = 6.95, 5.85

# top-right: what one run gives you
rect(RP_X, 1.35, RP_W, 2.42, ICE)
rect(RP_X, 1.35, RP_W, 0.42, NAVY)
text(RP_X + 0.15, 1.41, RP_W - 0.3, 0.3, "One proposal run: bait x whole proteome", size=13.5,
     bold=True, color=WHITE)
cards = [
    ("~6 GPU-h", "per target vs 20,260 proteins (6x A100); ranked partners + 3D complex models + interface residues"),
    ("3 evidence layers", "physical interaction score | interface geometry | disease-variant enrichment at the interface"),
    ("Validation-ready", "every hit ships with a structural hypothesis testable by co-IP / proximity labelling"),
]
cy = 1.95
for head, body in cards:
    rect(RP_X + 0.2, cy + 0.03, 0.07, 0.52, TEAL)
    text(RP_X + 0.42, cy, RP_W - 0.62, 0.6,
         [[(head + "  -  ", {"size": 11, "bold": True, "color": NAVY}),
           (body, {"size": 10, "color": INK})]], space_after=0)
    cy += 0.62

# bottom-right: positioning (honest scope)
rect(RP_X, 3.95, RP_W, 3.15, LIGHT)
rect(RP_X, 3.95, RP_W, 0.42, RED)
text(RP_X + 0.15, 4.01, RP_W - 0.3, 0.3, "Positioning and honest limits", size=13.5,
     bold=True, color=WHITE)
bullets = [
    ("Use as", "hypothesis generator + evidence layer feeding wet-lab triage - NOT a standalone discovery engine, NOT for excluding pairs."),
    ("Known blind spots", "transient interactions, immune receptors (somatic recombination), disordered-region motifs, fast-evolving partners; low recall overall (absence of signal != no interaction)."),
    ("External audit", "Nat Commun 2026 systematic assessment: high-confidence AI predictions match experimental-screen quality; main value = structural models + prioritisation."),
    ("Next step", "rerun the 99 GIGYF1-campaign lead pairs under our local precision curve; add disease-variant interface burden as ranking layer (RIC-407)."),
]
by = 4.55
for head, body in bullets:
    text(RP_X + 0.25, by, RP_W - 0.5, 0.62,
         [[(head + ":  ", {"size": 10, "bold": True, "color": RED}),
           (body, {"size": 10, "color": INK})]], space_after=0)
    by += 0.62

# footer
text(0.55, 7.14, 12.2, 0.28,
     "Zhang et al., Science 390, eadt1630 (2025) | Pei, Zhang & Cong, Sci Rep 16:25590 (2026) | "
     "code: druggability repo, commits a44be15 / b3dc421 / 1203c0c | Jira RIC-410",
     size=8.5, color=GREY)

prs.save("/das/user/QYJI/druggability/reports/ppi_screening_proposal_2026-10-28.pptx")
print("saved")
