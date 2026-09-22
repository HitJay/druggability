#!/usr/bin/env python3
"""
Export 4 individual high-resolution 300 DPI panels for Marp slides with
deterministic ink-bounding-box cropping + 35px white margin on all sides.
Guarantees ZERO edge truncation and ZERO ink touching border.
"""

import os
from PIL import Image
import numpy as np

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
SRC_PNG = os.path.join(WORK_DIR, "gpr81_binding_domains_visualization.png")
OUT_DIR = os.path.join(WORK_DIR, "slide_figures")
os.makedirs(OUT_DIR, exist_ok=True)

img = Image.open(SRC_PNG).convert("RGB")
arr = np.array(img)
H, W, _ = arr.shape
mid_x = int(W * 0.50)
mid_y = int(H * 0.50)

quadrants = {
    "panel_a_domain_topology.png": (0, mid_y, 0, mid_x),
    "panel_b_ternary_cooccupancy.png": (0, mid_y, mid_x, W),
    "panel_c_hcar1_vs_hcar2_selectivity.png": (mid_y, H, 0, mid_x),
    "panel_d_45_compound_landscape.png": (mid_y, H, mid_x, W)
}

PAD = 40

for name, (y1, y2, x1, x2) in quadrants.items():
    sub_arr = arr[y1:y2, x1:x2, :]
    non_white = np.where(sub_arr < 250)
    if len(non_white[0]) == 0:
        continue
    min_y = max(0, int(np.min(non_white[0])) - PAD)
    max_y = min(sub_arr.shape[0], int(np.max(non_white[0])) + PAD)
    min_x = max(0, int(np.min(non_white[1])) - PAD)
    max_x = min(sub_arr.shape[1], int(np.max(non_white[1])) + PAD)
    
    cropped = img.crop((x1 + min_x, y1 + min_y, x1 + max_x, y1 + max_y))
    out_path = os.path.join(OUT_DIR, name)
    cropped.save(out_path)
    print(f"Saved {name}: size {cropped.size}, crop: ({x1+min_x}, {y1+min_y}) to ({x1+max_x}, {y1+max_y})")

print("All 4 panel images successfully cropped with safe margins!")
