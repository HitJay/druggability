#!/usr/bin/env python3
"""Render the GPR81 one-pager at 1920x1080 and run deterministic layout checks."""
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image

URL = "file:///das/user/QYJI/druggability/data/gpr81_phase1/followup_2026-08/gpr81_onepager_summary.html"
PNG = "/tmp/gpr81_onepager.png"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(1200)
    pg.screenshot(path=PNG)
    # structural checks in-page
    stats = pg.evaluate("""() => ({
        divs: document.querySelectorAll('div').length,
        cards: document.querySelectorAll('.card').length,
        metrics: document.querySelectorAll('.metric').length,
        tables: document.querySelectorAll('table').length,
        h2: document.querySelectorAll('h2').length,
        overflowX: document.documentElement.scrollWidth > 1920,
        overflowY: document.documentElement.scrollHeight > 1080,
        bodyOverflow: getComputedStyle(document.body).overflow
    })""")
    print("PAGE:", stats, "| JS errors:", errs[:3])
    b.close()

img = np.array(Image.open(PNG).convert("RGB"))
h, w, _ = img.shape
print(f"PNG: {w}x{h}")
# 1. canvas fully covered (no white page edge band)
rows = (img != 255).any(axis=2).mean(axis=1)
print(f"non-white fraction: {rows.mean():.3f}")
# 2. bottom edge: last row should be page bg (#eef1f6) or card white - not clipped content
print("last row px (x=100):", img[-1, 100].tolist(), "expect ~[238,241,246] (#eef1f6)")
# 3. per-column content density (left/mid/right thirds) - all should have content
for name, x0, x1 in [("col1", 20, 640), ("col2", 650, 1270), ("col3", 1280, 1900)]:
    band = img[:, x0:x1]
    frac = (band != 255).any(axis=2).mean()
    print(f"{name} content fraction: {frac:.3f}")
# 4. header band: dark blue present at top
top = img[:100]
blue = ((top[:,:,2] > 80) & (top[:,:,2] < 140) & (top[:,:,0] < 40)).mean()
print(f"header blue fraction: {blue:.3f}")
# 5. no all-white gap rows > 120px inside main area (y 240..1060)
mid = img[240:1060]
white_rows = (mid == 255).all(axis=2).mean(axis=1)
max_gap = 0; cur = 0
for v in white_rows:
    cur = cur + 1 if v > 0.98 else 0
    max_gap = max(max_gap, cur)
print(f"max continuous white row gap: {max_gap}px (limit 120)")
