"""Fetch a URL that sits behind a JS interstitial (NCBI/PMC 'Preparing to download')."""
import sys
from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(accept_downloads=True, user_agent=(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"))
    pg = ctx.new_page()
    try:
        with pg.expect_download(timeout=180000) as dl_info:
            pg.goto(url, timeout=60000)
        dl = dl_info.value
        dl.save_as(out)
        print("downloaded:", dl.suggested_filename)
    except Exception as e:
        # maybe it rendered inline instead of triggering a download
        print("no download event:", str(e)[:150])
        content = pg.content()
        if len(content) > 10000:
            with open(out, "w") as f:
                f.write(content)
            print("saved rendered page instead,", len(content), "chars")
        else:
            print("page:", content[:200])
    b.close()
