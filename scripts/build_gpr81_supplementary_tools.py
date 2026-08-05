#!/usr/bin/env python3
"""Add tool compounds (t01-t05) + lactate (lac) to the GPR81 supplementary materials.

Reads:
  ligands/*.sdf                       6 tool ligands (PubChem CIDs)
  identity_resolution.json            confirmed identities
  phase3_docking/docking_results.csv  per-receptor best scores
  phase3_5_controls/redocking_controls.csv  lactate redocking

Writes:
  supplementary/tool_compounds_index.csv
  supplementary/structures_2d/t01.png ... t05.png, lac.png
  supplementary/tool_structures_grid.png
  supplementary/supplementary_structures.html  (appends section 3)

Usage: python build_gpr81_supplementary_tools.py
"""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Draw
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

BASE = Path(__file__).resolve().parents[1] / "data" / "gpr81_phase1"
LIG = BASE / "ligands"
OUT = BASE / "supplementary"
OUT_2D = OUT / "structures_2d"

# tool compound registry: file stem -> (code, display name, identity note)
TOOLS = [
    ("AZ1_GPR81_agonist_2", "t01", "AZ1 / GPR81 agonist 2 (CID 57422810)",
     "= Davidsson 2020 paper compound 1 (CHEMBL4641579); EC50 0.023 uM"),
    ("GPR81_agonist_1", "t02", "GPR81 agonist 1 (CID 86279608)",
     "NOT paper c2; = Takeda 2014 (PMID 24486398) compound 2 (CHEMBL6177006); EC50 ~0.05 uM"),
    ("CHBA", "t03", "CHBA (CID 13071646)",
     "3-chloro-5-hydroxybenzoic acid; co-crystal ligand in 8Z87 (R401)"),
    ("3_5_DHBA", "t04", "3,5-DHBA (CID 7424)",
     "3,5-dihydroxybenzoic acid; co-crystal ligand in 9KT9 (34D)"),
    ("3_OBA", "t05", "3-OBA (CID 441)",
     "3-hydroxybutanoic acid"),
    ("lactate", "lac", "L-lactate (CID 612)",
     "endogenous agonist; co-crystal ligand in 8Z8A (2OP)"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_2D.mkdir(parents=True, exist_ok=True)

    # ---- parse SDFs ----
    rows = []
    mols = []
    for stem, code, name, identity in TOOLS:
        matches = sorted(LIG.glob(f"{stem}_CID*.sdf")) + sorted(LIG.glob(f"{stem}.sdf"))
        if not matches:
            raise SystemExit(f"no sdf found for {stem}")
        src = matches[0]
        mol = Chem.MolFromMolFile(str(src), removeHs=False)
        if mol is None:
            raise SystemExit(f"parse failed: {src}")
        smi = Chem.MolToSmiles(Chem.RemoveHs(mol))
        clean = Chem.MolFromSmiles(smi)
        mols.append(clean)
        rows.append({
            "stem": stem,
            "code": code,
            "name": name,
            "identity": identity,
            "smiles": smi,
            "formula": CalcMolFormula(clean),
            "MW": round(Descriptors.MolWt(clean), 2),
            "InChIKey": Chem.MolToInchiKey(clean),
        })

    # ---- identity resolution merge (authoritative notes) ----
    idr = json.loads((BASE / "identity_resolution.json").read_text())
    idmap = {t["compound_id"]: t.get("identity_resolution", "") for t in idr.get("tool_compounds", [])}
    for r in rows:
        if r["stem"] in idmap:
            r["identity_resolved"] = idmap[r["stem"]]

    # ---- docking scores (phase3) ----
    score_map = defaultdict(dict)
    with (BASE / "phase3_docking" / "docking_results.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            cid_, rec = row["compound_id"], row["receptor_id"]
            s = float(row["score_kcal_mol"])
            score_map[cid_][rec] = min(score_map[cid_].get(rec, s), s)
    # lactate redocking control
    lac_ctrl = {}
    with (BASE / "phase3_5_controls" / "redocking_controls.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row["compound_id"] == "lactate":
                lac_ctrl = {"score": float(row["redock_score_kcal_mol"]),
                            "centroid_A": float(row["centroid_distance_A"]),
                            "receptor": row["receptor_id"]}

    for r in rows:
        r["docking_8Z87"] = score_map.get(r["stem"], {}).get("8Z87", "")
        r["docking_8Z8A"] = score_map.get(r["stem"], {}).get("8Z8A", "")
        r["docking_9KT9"] = score_map.get(r["stem"], {}).get("9KT9", "")

    # ---- 2D PNGs ----
    for r, mol in zip(rows, mols):
        AllChem.Compute2DCoords(mol)
        Draw.MolToFile(mol, str(OUT_2D / f"{r['code']}.png"), size=(700, 520),
                       fitImage=True, kekulize=True, wedgeBonds=True)

    # grid (3 cols x 2 rows)
    grid = Draw.MolsToGridImage(mols, molsPerRow=3, subImgSize=(480, 360),
                                legends=[r["code"] for r in rows])
    grid.save(str(OUT / "tool_structures_grid.png"))

    # ---- CSV ----
    with (OUT / "tool_compounds_index.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "name", "identity", "smiles", "formula", "MW",
                    "InChIKey", "dock_8Z87", "dock_8Z8A", "dock_9KT9"])
        for r in rows:
            w.writerow([r["code"], r["name"], r["identity"], r["smiles"],
                        r["formula"], r["MW"], r["InChIKey"],
                        r["docking_8Z87"], r["docking_8Z8A"], r["docking_9KT9"]])

    # ---- append section 3 to HTML ----
    append_html(rows, lac_ctrl)

    print(f"tool compounds: {len(rows)} (t01-t05 + lac)")
    print(f"PNGs: {len(list(OUT_2D.glob('t*.png'))) + len(list(OUT_2D.glob('lac.png')))}")
    print(f"lactate redock control: {lac_ctrl}")
    print(f"grid: {OUT / 'tool_structures_grid.png'}")


def suffix(stem: str) -> str:
    return ""  # placeholder, unused


def append_html(rows, lac_ctrl) -> None:
    html_path = OUT / "supplementary_structures.html"
    html = html_path.read_text()

    trs = []
    for r in rows:
        fmt = lambda v: "—" if v == "" else f"{v:.2f}"
        trs.append(
            "<tr>"
            f"<td style='font-weight:600'>{r['code']}</td>"
            f"<td>{r['name']}</td>"
            f"<td style='font-size:11px'>{r['identity']}</td>"
            f"<td style='font-family:monospace;font-size:11px;max-width:260px;word-break:break-all'>{r['smiles']}</td>"
            f"<td>{r['formula']}</td>"
            f"<td>{r['MW']}</td>"
            f"<td style='text-align:right'>{fmt(r['docking_8Z87'])}</td>"
            f"<td style='text-align:right'>{fmt(r['docking_8Z8A'])}</td>"
            f"<td style='text-align:right'>{fmt(r['docking_9KT9'])}</td>"
            "</tr>"
        )

    imgs = "\n".join(
        f"<div class='card'><img src='structures_2d/{r['code']}.png' alt='{r['code']}'>"
        f"<div class='cap'>{r['code']} — {r['identity']}</div></div>"
        for r in rows
    )

    note = (
        "<p class='note'>Docking scores = best Vina pose per receptor (phase3, unified box; "
        "9KT9 phase3 scores affected by the deep-insert search artifact later fixed in phase5 "
        "tight-box, see report section 4). Positive/weak scores (AZ1 8Z87 +10.13) are not "
        "meaningful binding signals. Lactate was only redocked as a control in its co-crystal "
        "box (8Z8A, -4.36 kcal/mol, centroid recovery 2.89 Å); it was not part of the "
        "full-panel docking. Scores do not prove agonism or affinity.</p>"
    )
    if lac_ctrl:
        note = note.replace("8Z8A, -4.36 kcal/mol, centroid recovery 2.89 Å",
                            f"8Z8A, {lac_ctrl['score']:.2f} kcal/mol, "
                            f"centroid recovery {lac_ctrl['centroid_A']:.2f} Å")

    section = f"""
<h2>3. Tool compounds &amp; lactate (t01–t05, lac)</h2>
<p class="note">The five request tool compounds plus the endogenous ligand lactate.
AZ1/GPR81 agonist 2 was resolved as identical to paper compound c1 (see
<code>identity_resolution.json</code>).</p>
<table>
<tr><th>Code</th><th>Compound</th><th>Identity / note</th><th>SMILES</th><th>Formula</th><th>MW</th>
<th>dock 8Z87</th><th>dock 8Z8A</th><th>dock 9KT9</th></tr>
{''.join(trs)}
</table>
{note}
<div class="grid">{imgs}</div>
"""
    # insert before closing body
    marker = "</body>"
    if marker not in html:
        raise SystemExit("</body> marker not found in HTML")
    html = html.replace(marker, section + "\n" + marker)
    html_path.write_text(html)
    print(f"appended section 3 -> {html_path}")


if __name__ == "__main__":
    main()
