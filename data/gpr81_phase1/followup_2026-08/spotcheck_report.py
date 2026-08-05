#!/usr/bin/env python3
"""Spot-check the self-contained GPR81 follow-up report with headless Chromium.

Screenshots: header+ranking, ranking table element, representative pair cards,
recommendations, methodology. Also collects console/page errors and counts
rendered <img> elements with natural sizes > 0 (proves base64 images decoded).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "file:///das/user/QYJI/druggability/data/gpr81_phase1/followup_2026-08/gpr81_followup_report.html"
OUT = Path("/das/user/QYJI/druggability/data/gpr81_phase1/followup_2026-08/spotcheck")
OUT.mkdir(exist_ok=True)

console_msgs, page_errors = [], []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000},
                            device_scale_factor=1.5)
    page.on("console", lambda m: console_msgs.append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.goto(URL, wait_until="load")
    page.wait_for_timeout(4000)

    # --- structural checks ---
    stats = page.evaluate("""() => {
        const imgs = [...document.querySelectorAll('img')];
        const broken = imgs.filter(i => i.naturalWidth === 0 || i.naturalHeight === 0);
        const cards = document.querySelectorAll('.card').length;
        const rankRows = document.querySelectorAll('#ranking tbody tr').length;
        const tables = [...document.querySelectorAll('table')];
        const emptyTables = tables.filter(t => t.querySelectorAll('td').length === 0).length;
        return {
            images: imgs.length, brokenImages: broken.length,
            cards, rankRows, tables: tables.length, emptyTables
        };
    }""")
    print("STRUCTURE:", stats)

    # --- screenshots ---
    page.screenshot(path=str(OUT / "01_header_ranking.png"))
    page.evaluate("document.querySelector('#ranking').scrollIntoView({block:'start'})")
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / "02_ranking_viewport.png"))
    page.locator("#ranking").screenshot(path=str(OUT / "03_ranking_full.png"))

    for cid in ["pair-c01_8Z8A", "pair-c07_8Z8A", "pair-c28_8Z8A", "pair-lac_8Z8A", "pair-t01_8Z8A"]:
        el = page.locator(f"#{cid}")
        if el.count():
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            el.screenshot(path=str(OUT / f"04_card_{cid}.png"))
        else:
            print("MISSING CARD:", cid)

    # scroll through a few more cards to force layout (image decode)
    for i in range(0, 46, 12):
        page.evaluate(f"document.querySelectorAll('.card')[{i}].scrollIntoView()")
        page.wait_for_timeout(300)

    # recommendations + methodology
    h2s = page.locator("h2")
    for h2 in h2s.all():
        txt = h2.inner_text()
        if "Recommendations" in txt or "Methodology" in txt:
            h2.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / f"05_{txt.split()[0].lower()}.png"))

    browser.close()

print("console errors/warnings:", console_msgs[:8])
print("page errors:", page_errors[:5])
