"""Dryad WAF probe v2: click download, observe WAF challenge, retry after challenge."""
import sys
from playwright.sync_api import sync_playwright

FILE_ID = sys.argv[1] if len(sys.argv) > 1 else "4357019"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/das/user/QYJI/druggability/humanPPI_repro/downloads/test_benchmarks.bin"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(accept_downloads=True, user_agent=(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"))
    pg = ctx.new_page()
    pg.goto("https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p84", timeout=60000,
            wait_until="domcontentloaded")
    pg.wait_for_timeout(8000)
    print("title:", pg.title())
    print("cookies:", sorted(c["name"] for c in ctx.cookies()))

    for attempt in range(3):
        try:
            link = pg.locator(f'a.js-individual-dl[href*="{FILE_ID}"]').first
            with pg.expect_download(timeout=60000) as dl_info:
                link.click()
            dl = dl_info.value
            print("download url:", dl.url)
            print("filename:", dl.suggested_filename)
            dl.save_as(OUT)
            print("saved:", OUT)
            break
        except Exception as e:
            print(f"attempt {attempt}: {type(e).__name__}: {str(e)[:200]}")
            print("now at:", pg.url)
            # WAF challenge likely: wait for it to resolve then reload the page
            pg.wait_for_timeout(15000)
            print("cookies now:", sorted(c["name"] for c in ctx.cookies()))
            if "awswaf" in pg.url or attempt == 0:
                try:
                    pg.wait_for_load_state("domcontentloaded", timeout=30000)
                except Exception:
                    pass
                pg.goto("https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p84",
                        timeout=60000, wait_until="domcontentloaded")
                pg.wait_for_timeout(8000)
    b.close()
