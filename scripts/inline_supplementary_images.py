#!/usr/bin/env python3
"""Inline all structure PNGs into the supplementary HTML as base64 data URIs,
producing a self-contained single-file version that opens with images anywhere
(no relative path dependency).

Input : supplementary/supplementary_structures.html (relative img srcs)
Output: supplementary/supplementary_structures_selfcontained.html

Usage: python inline_supplementary_images.py
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "gpr81_phase1" / "supplementary"
SRC = OUT / "supplementary_structures.html"
DST = OUT / "supplementary_structures_selfcontained.html"


def main() -> None:
    html = SRC.read_text()
    srcs = sorted(set(re.findall(r"src='([^']+\.png)'", html)))
    print(f"image references found: {len(srcs)}")

    def repl(m):
        rel = m.group(1)
        p = OUT / rel
        if not p.exists():
            print(f"  !! missing: {rel}")
            return m.group(0)
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f"src='data:image/png;base64,{b64}'"

    new = re.sub(r"src='([^']+\.png)'", repl, html)
    DST.write_text(new)
    mb = DST.stat().st_size / 1e6
    print(f"wrote {DST} ({mb:.1f} MB, self-contained)")
    # verify: no relative .png srcs remain
    rem = re.findall(r"src='([^']+\.png)'", new)
    print(f"remaining relative srcs: {len(rem)}")


if __name__ == "__main__":
    main()
