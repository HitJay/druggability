"""Extract presigned S3 URLs for all Dryad files by clicking download links in headless chromium.

The aws-waf-token + anubis cookies from the page session unlock /downloads/file_stream/<id>,
which 302s to a presigned S3 URL (24h validity). We capture the URL and cancel the browser
download so the actual transfer happens via curl (resumable, parallel, logged).
"""
import json
import sys
from playwright.sync_api import sync_playwright

OUT_JSON = "/das/user/QYJI/druggability/humanPPI_repro/downloads/dryad_urls.json"

# file_id -> name (from Dryad API listing, version 396143)
FILES = {
    "4357017": "protein_omicMSAs.tar.gz",
    "4357018": "segment_omicMSAs.tar.gz",
    "4357020": "final_predictions.tar.gz",
    "4357022": "RF2-PPI.pt",
    "4357023": "DCA_scores.gz",
    "4357024": "AF_scores.gz",
    "4357025": "screened_pairs.tar.gz",
    "4357026": "RF2-PPI_scores.gz",
    "4357029": "README.md",
}

urls = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(accept_downloads=True, user_agent=(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"))
    pg = ctx.new_page()
    pg.goto("https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p84", timeout=60000,
            wait_until="domcontentloaded")
    pg.wait_for_timeout(8000)

    for fid, name in FILES.items():
        ok = False
        for attempt in range(4):
            try:
                link = pg.locator(f'a.js-individual-dl[href*="{fid}"]').first
                with pg.expect_download(timeout=45000) as dl_info:
                    link.click()
                dl = dl_info.value
                urls[name] = dl.url
                print(f"OK  {name}: {dl.url[:120]}...", flush=True)
                try:
                    dl.cancel()
                except Exception:
                    pass
                ok = True
                break
            except Exception as e:
                print(f"retry {name} (attempt {attempt}): {type(e).__name__} {str(e)[:120]}", flush=True)
                pg.wait_for_timeout(12000)
                try:
                    pg.goto("https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p84",
                            timeout=60000, wait_until="domcontentloaded")
                    pg.wait_for_timeout(6000)
                except Exception:
                    pass
        if not ok:
            print(f"FAIL {name}", flush=True)

    b.close()

with open(OUT_JSON, "w") as f:
    json.dump(urls, f, indent=1)
print(f"\nsaved {len(urls)}/{len(FILES)} urls -> {OUT_JSON}")
sys.exit(0 if len(urls) == len(FILES) else 1)
