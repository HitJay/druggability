#!/usr/bin/env python3
"""
GPR81 follow-up: Boltz-2 predicted binding-site vs Vina docking region
consistency analysis (45 compounds, HCAR1).

For each compound's Boltz-2 complex (boltz_runs/<id>/predictions/boltz/boltz_model_0.cif):
  - extract ligand atoms (chain B) and receptor atoms (chain A) via Bio.PDB MMCIFParser
  - receptor residues within 4.5 A of any ligand atom = contact residues
  - classify into ORTHO_POCKET / TM56_EXTRACELLULAR / NTERM_SURFACE / MIXED /
    NO_CONTACT using the SAME residue sets and fraction rule as the Vina
    positional QC (ORTHO {71,75,92,95,96,99,165,167,168,261,264,268},
    TM56 {153,155,157,164,166,169,170,171,174,177}, NTERM {6,7,8,9,79};
    HCAR1/UniProt numbering, verified 8Z8A chain R numbering == UniProt).

Compare with the Vina 8Z8A consensus region (scorecard) and the paper EC50.

Outputs: data/boltz_site_vs_vina.csv + .json; report section in the three-layer HTML.
"""
import csv, json, sys
from pathlib import Path
from collections import Counter

import numpy as np
from Bio.PDB import MMCIFParser, PDBParser

BASE = Path(__file__).resolve().parent
P1 = BASE.parent

ORTHO = {71, 75, 92, 95, 96, 99, 165, 167, 168, 261, 264, 268}
TM56 = {153, 155, 157, 164, 166, 169, 170, 171, 174, 177}
NTERM = {6, 7, 8, 9, 79}
CUTOFF = 4.5


def classify(contact_residues: set[int]) -> str:
    n = len(contact_residues)
    if n == 0:
        return "NO_CONTACT"
    o = len(contact_residues & ORTHO) / n
    t = len(contact_residues & TM56) / n
    nt = len(contact_residues & NTERM) / n
    if o >= 0.4:
        return "ORTHO_POCKET"
    if t >= 0.4:
        return "TM56_EXTRACELLULAR"
    if nt >= 0.4:
        return "NTERM_SURFACE"
    return "MIXED"


def analyze_cif(cif_path: Path):
    parser = MMCIFParser(QUIET=True)
    s = parser.get_structure("boltz", str(cif_path))
    model = s[0]
    lig_atoms, rec_atoms = [], []
    for chain in model:
        cid = chain.id
        for res in chain:
            rnum = res.id[1]
            for atom in res:
                coord = atom.coord
                el = atom.element.strip().upper() if atom.element else atom.name.strip()
                if el.startswith("H"):
                    continue
                if cid == "B":
                    lig_atoms.append(coord)
                elif cid == "A":
                    rec_atoms.append((rnum, coord))
                # other chains ignored
    if not lig_atoms:
        return "NO_CONTACT", set(), 0
    lig = np.array(lig_atoms)
    contacts = set()
    for rnum, coord in rec_atoms:
        d = np.linalg.norm(lig - coord, axis=1).min()
        if d < CUTOFF:
            contacts.add(rnum)
    return classify(contacts), contacts, len(lig)


def main():
    boltz_rows = {}
    with open(BASE / "data/boltz_results.csv") as f:
        for r in csv.DictReader(f):
            boltz_rows[r["entry_id"]] = r

    sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
    vina_region = {c["entry_id"]: c.get("region_8Z8A") for c in sc["compounds"]}
    ec50 = {c["entry_id"]: c.get("ec50_nM") for c in sc["compounds"]}

    out = []
    n_ok = n_fail = 0
    for eid in sorted(boltz_rows):
        cif = BASE / "data/boltz_runs" / eid / "predictions/boltz/boltz_model_0.cif"
        if not cif.exists():
            out.append({"entry_id": eid, "error": "cif missing"})
            n_fail += 1
            continue
        try:
            region, contacts, n_lig = analyze_cif(cif)
        except Exception as e:
            out.append({"entry_id": eid, "error": str(e)[:120]})
            n_fail += 1
            continue
        n_ok += 1
        v = vina_region.get(eid)
        agree = "n/a" if not v else ("YES" if region == v else "NO")
        out.append({
            "entry_id": eid,
            "boltz_region": region,
            "boltz_contact_residues": sorted(contacts),
            "n_boltz_lig_atoms": n_lig,
            "vina_8Z8A_region": v or "",
            "agree": agree,
            "ec50_nM": ec50.get(eid),
        })

    with open(BASE / "data/boltz_site_vs_vina.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entry_id", "boltz_region", "vina_8Z8A_region",
                                          "agree", "ec50_nM", "n_boltz_lig_atoms",
                                          "boltz_contact_residues"])
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})
    with open(BASE / "data/boltz_site_vs_vina.json", "w") as f:
        json.dump({"method": "Boltz-2 complex CIF (chain A receptor / chain B ligand), contact cutoff 4.5 A, "
                             "same residue sets as Vina positional QC (UniProt numbering)",
                   "results": out}, f, indent=1)

    print(f"analyzed: {n_ok}, failed: {n_fail}")
    from collections import Counter as C
    agree_c = C(r["agree"] for r in out if "agree" in r)
    print("agreement:", dict(agree_c))
    reg_c = C(r.get("boltz_region") for r in out)
    print("boltz regions:", dict(reg_c))
    print()
    print(f"{'id':6s} {'boltz':22s} {'vina':22s} agree")
    for r in out:
        print(f"{r['entry_id']:6s} {r.get('boltz_region','?'):22s} {r.get('vina_8Z8A_region','?'):22s} {r.get('agree','?')}")


if __name__ == "__main__":
    main()
