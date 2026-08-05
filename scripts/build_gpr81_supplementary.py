#!/usr/bin/env python3
"""Build GPR81 paper-compound supplementary materials: full c01-c39 index
(merged from paper_structures_recovered.json + paper_compound_inventory.csv,
including compound 22), 2D structure PNGs per compound, and a grid overview.

Outputs (all under data/gpr81_phase1/supplementary/):
  compound_index.csv        full 39-row index with SMILES
  structures_2d/cNN.png     one 2D structure image per compound
  structures_grid.png       5x8 grid overview with cNN labels + EC50
  supplementary_structures.html  human-readable index + embedded images

Usage: python build_gpr81_supplementary.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Draw, rdMolDescriptors

BASE = Path(__file__).resolve().parents[1] / "data" / "gpr81_phase1"
OUT = BASE / "supplementary"
OUT_2D = OUT / "structures_2d"


def main() -> None:
    rec = json.loads((BASE / "paper_structures_recovered.json").read_text())
    compounds = {c["paper_compound_number"]: c for c in rec["compounds"]}

    inv_rows = {}
    with (BASE / "paper_compound_inventory.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                n = int(row["paper_compound"])
            except (TypeError, ValueError):
                continue
            inv_rows[n] = row

    # ---- merge ----
    rows = []
    parse_fail = []
    for n in range(1, 40):
        c = compounds.get(n)
        if c is None:
            rows.append({"paper_compound_number": n, "series": "?", "smiles": "",
                         "parse_ok": False, "error": "MISSING in recovered.json"})
            continue
        inv = inv_rows.get(n, {})
        smi = c.get("smiles", "")
        mol = Chem.MolFromSmiles(smi) if smi else None
        if mol is None:
            parse_fail.append(n)
        mw = round(Descriptors.MolWt(mol), 2) if mol else ""
        inchi = Chem.MolToInchiKey(mol) if mol else ""
        rows.append({
            "paper_compound_number": n,
            "series": inv.get("series") or c.get("series", ""),
            "source_table": inv.get("source_table", ""),
            "smiles": smi,
            "formula": c.get("formula", ""),
            "calc_M_plus_H": c.get("exact_mass_M_plus_H_calc", ""),
            "si_M_plus_H": c.get("si_reported_M_plus_H", ""),
            "delta_mDa": c.get("delta_mDa", ""),
            "MW": mw,
            "InChIKey": inchi,
            "EC50_uM": inv.get("reported_hgpr81_ec50_uM") or c.get("paper_reported_hGPR81_EC50_uM", ""),
            "status": c.get("status", ""),
            "notes": inv.get("notes", ""),
        })

    # ---- write CSV ----
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_2D.mkdir(parents=True, exist_ok=True)
    fieldnames = ["paper_compound_number", "series", "source_table", "smiles",
                  "formula", "calc_M_plus_H", "si_M_plus_H", "delta_mDa",
                  "MW", "InChIKey", "EC50_uM", "status", "notes"]
    with (OUT / "compound_index.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---- 2D structure images ----
    label_map = {1: "c01", 2: "c02"}
    failed = []
    for r in rows:
        n = r["paper_compound_number"]
        mol = Chem.MolFromSmiles(r["smiles"]) if r["smiles"] else None
        if mol is None:
            failed.append(n)
            continue
        AllChem.Compute2DCoords(mol)
        png = OUT_2D / f"c{n:02d}.png"
        Draw.MolToFile(mol, str(png), size=(700, 520), fitImage=True,
                       kekulize=True, wedgeBonds=True)

    # ---- grid overview: 8 cols x 5 rows (39 + 1 blank) ----
    grid = Draw.MolsToGridImage(
        [Chem.MolFromSmiles(r["smiles"]) if r["smiles"] else None for r in rows],
        molsPerRow=8,
        subImgSize=(480, 360),
        legends=[f"c{n:02d}  {str(r['EC50_uM'])} uM" for n, r in
                 ((r["paper_compound_number"], r) for r in rows)],
        useSVG=False,
    )
    grid.save(str(OUT / "structures_grid.png"))

    # ---- HTML ----
    build_html(rows, failed)

    print(f"index rows: {len(rows)}")
    print(f"SMILES parse failures: {parse_fail or 'none'}")
    print(f"structure PNGs written: {len(list(OUT_2D.glob('c*.png')))}")
    print(f"output dir: {OUT}")


def build_html(rows, failed) -> None:
    series_style = defaultdict(lambda: "background:#f4f4f4;")
    series_style.update({
        "acyl_urea": "background:#eef4fb;",
        "constrained_analogue_cyclic": "background:#f2f8ee;",
        "linker_variant": "background:#fdf6e8;",
        "amide": "background:#fbeef4;",
    })
    trs = []
    for r in rows:
        n = r["paper_compound_number"]
        smi = r["smiles"] or "—"
        trs.append(
            "<tr>"
            f"<td style='font-weight:600'>{n}</td>"
            f"<td style='{series_style.get(r['series'],'')}'>{r['series']}</td>"
            f"<td>{r['source_table']}</td>"
            f"<td style='font-family:monospace;font-size:11px;max-width:300px;word-break:break-all'>{smi}</td>"
            f"<td>{r['formula']}</td>"
            f"<td>{r['MW']}</td>"
            f"<td>{r['calc_M_plus_H']}</td>"
            f"<td>{r['si_M_plus_H']}</td>"
            f"<td>{r['delta_mDa']}</td>"
            f"<td>{r['EC50_uM']}</td>"
            f"<td>{r['status']}</td>"
            "</tr>"
        )
    imgs = "\n".join(
        f"<div class='card'><img src='structures_2d/c{n:02d}.png' alt='c{n:02d}'>"
        f"<div class='cap'>c{n:02d} — {r['series']} — EC50 {r['EC50_uM']} uM</div></div>"
        for r in rows for n in [r["paper_compound_number"]]
    )
    fail_note = (
        f"<p class='warn'>SMILES parse failures: {failed}</p>" if failed
        else "<p>All 39 SMILES parsed successfully by RDKit.</p>"
    )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>GPR81 (HCAR1) Davidsson 2020 paper series — compound index &amp; structures</title>
<style>
 body {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 24px; color:#222; }}
 h1 {{ font-size: 20px; }} h2 {{ font-size: 16px; margin-top: 28px; }}
 table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
 th, td {{ border: 1px solid #ccc; padding: 4px 6px; text-align: left; }}
 th {{ background: #eaeef2; position: sticky; top: 0; }}
 .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
 .card {{ border: 1px solid #ddd; border-radius: 6px; padding: 8px; text-align: center; }}
 .card img {{ max-width: 100%; height: auto; }}
 .cap {{ font-size: 12px; margin-top: 4px; color: #444; }}
 .warn {{ color: #a33; font-weight: 600; }}
 p.note {{ font-size: 12px; color: #555; }}
</style></head><body>
<h1>GPR81 (HCAR1) — Davidsson 2020 (BMCL 30:126953) paper series</h1>
<p class="note">Compound index and 2D structures, c01–c39 (paper compound numbers 1–39).
Structures recovered in Phase 1 (see <code>paper_structures_recovered.json</code>):
3 compounds authoritative (PubChem/ChEMBL cross-check), 36 reconstructed and
validated against SI-reported HRMS [M+H]+. Compound 22: SI entry shows a data
mismatch resolved 2026-08-04 (structure confirmed by figure + text + ChEMBL
CHEMBL4634029; the SI 627.1839 [M+H]+ row belongs to a different compound).</p>
{fail_note}
<h2>1. Index table</h2>
<table>
<tr><th>#</th><th>Series</th><th>Source</th><th>SMILES</th><th>Formula</th><th>MW</th>
<th>calc [M+H]+</th><th>SI [M+H]+</th><th>Δ mDa</th><th>EC50 (uM)</th><th>Status</th></tr>
{''.join(trs)}
</table>
<h2>2. Structures</h2>
<div class="grid">{imgs}</div>
</body></html>"""
    (OUT / "supplementary_structures.html").write_text(html)


if __name__ == "__main__":
    main()
