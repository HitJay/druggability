#!/usr/bin/env python3
"""Top-20 GHSR strong_inverse_agonist liability/ADMET heuristic screen.

Uses real RDKit PAINS/Brenk FilterCatalog + MW/clogP descriptors.
CYP/hERG flags are rule-of-thumb structural heuristics (NOT a validated
ML ADMET model) — documented explicitly in the summary as such.
"""
import csv
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

OUTDIR = Path("output/2026-07-10/ghsr_inverse_agonist_docking")
RANKED = OUTDIR / "ranked_hits.csv"
LIBRARY = OUTDIR / "ghsr_screening_library.csv"
OUT_CSV = OUTDIR / "top20_liability_screen.csv"
OUT_MD = OUTDIR / "top20_liability_summary.md"

# Build PAINS + Brenk catalogs
params_pains = FilterCatalogParams()
params_pains.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
pains_catalog = FilterCatalog(params_pains)

params_brenk = FilterCatalogParams()
params_brenk.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
brenk_catalog = FilterCatalog(params_brenk)

# Structural heuristic SMARTS for CYP / hERG risk flags (rule-of-thumb, not validated ML)
HERG_RISK_SMARTS = [
    ("basic_N_lipophilic", "[NX3;H0,H1;!$(N-C=O)]"),  # tertiary/secondary basic amine
]
CYP_RISK_SMARTS = [
    ("aniline", "c1ccccc1[NX3;H2,H1;!$(N-C=O)]"),
    ("furan", "c1ccoc1"),
    ("thiophene", "c1ccsc1"),
]

def herg_flag(mol, mw, clogp):
    """Heuristic: basic amine + high lipophilicity + high MW correlates with hERG liability."""
    has_basic_amine = mol.HasSubstructMatch(Chem.MolFromSmarts(HERG_RISK_SMARTS[0][1]))
    if has_basic_amine and clogp > 3.5 and mw > 350:
        return True, "basic amine + clogP>3.5 + MW>350 (rule-of-thumb hERG liability pattern)"
    return False, ""

def cyp_flag(mol):
    hits = []
    for name, smarts in CYP_RISK_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt and mol.HasSubstructMatch(patt):
            hits.append(name)
    if hits:
        return True, "contains " + ",".join(hits) + " (known CYP-reactive/metabolically labile motif)"
    return False, ""

def main():
    lib = {}
    with open(LIBRARY) as f:
        for row in csv.DictReader(f):
            lib[row["compound_id"]] = row

    top20 = []
    with open(RANKED) as f:
        for row in csv.DictReader(f):
            if row["class"] == "strong_inverse_agonist":
                top20.append(row)
                if len(top20) == 20:
                    break

    out_rows = []
    for row in top20:
        cid = row["compound_id"]
        lrow = lib.get(cid, {})
        smi = lrow.get("canonical_smiles", "")
        name = lrow.get("name", cid)
        max_phase = lrow.get("max_phase", "")

        mol = Chem.MolFromSmiles(smi) if smi else None
        if mol is None:
            out_rows.append({
                "rank": row["rank"], "compound_id": cid, "name": name, "max_phase": max_phase,
                "mw": "", "clogp": "", "pains_hit": "PARSE_FAIL", "brenk_hit": "PARSE_FAIL",
                "cyp_risk_flag": "", "herg_risk_flag": "", "notes": f"RDKit failed to parse SMILES: {smi!r}",
            })
            continue

        mw = round(Descriptors.MolWt(mol), 1)
        clogp = round(Crippen.MolLogP(mol), 2)

        pains_matches = pains_catalog.GetMatches(mol)
        pains_hit = "; ".join(sorted({m.GetDescription() for m in pains_matches})) if pains_matches else "none"

        brenk_matches = brenk_catalog.GetMatches(mol)
        brenk_hit = "; ".join(sorted({m.GetDescription() for m in brenk_matches})) if brenk_matches else "none"

        cyp_bool, cyp_note = cyp_flag(mol)
        herg_bool, herg_note = herg_flag(mol, mw, clogp)

        notes_parts = []
        if max_phase and max_phase not in ("", "None"):
            try:
                mp = float(max_phase)
                if mp >= 4:
                    notes_parts.append("approved drug")
                elif mp > 0:
                    notes_parts.append(f"clinical phase {mp:g}")
            except ValueError:
                pass
        if pains_hit != "none":
            notes_parts.append("PAINS alert")
        if brenk_hit != "none":
            notes_parts.append("Brenk structural alert")
        if cyp_bool:
            notes_parts.append("CYP-risk motif")
        if herg_bool:
            notes_parts.append("hERG-risk pattern")
        if not notes_parts:
            notes_parts.append("clean by heuristic filters")

        out_rows.append({
            "rank": row["rank"], "compound_id": cid, "name": name, "max_phase": max_phase,
            "mw": mw, "clogp": clogp,
            "pains_hit": pains_hit, "brenk_hit": brenk_hit,
            "cyp_risk_flag": f"{cyp_bool}" + (f" ({cyp_note})" if cyp_note else ""),
            "herg_risk_flag": f"{herg_bool}" + (f" ({herg_note})" if herg_note else ""),
            "notes": "; ".join(notes_parts),
        })

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "compound_id", "name", "max_phase", "mw", "clogp",
                                           "pains_hit", "brenk_hit", "cyp_risk_flag", "herg_risk_flag", "notes"])
        w.writeheader()
        w.writerows(out_rows)

    # Summary markdown
    n_pains = sum(1 for r in out_rows if r["pains_hit"] not in ("none", ""))
    n_brenk = sum(1 for r in out_rows if r["brenk_hit"] not in ("none", ""))
    n_cyp = sum(1 for r in out_rows if str(r["cyp_risk_flag"]).startswith("True"))
    n_herg = sum(1 for r in out_rows if str(r["herg_risk_flag"]).startswith("True"))
    n_clean = sum(1 for r in out_rows if r["notes"] == "clean by heuristic filters")
    n_clinical = [r for r in out_rows if r["max_phase"] not in ("", "0.0", "0", "None")]

    with open(OUT_MD, "w") as f:
        f.write(f"""# GHSR Top-20 Strong Inverse Agonists — Liability/ADMET Heuristic Screen

**Method**: RDKit `FilterCatalog` (real PAINS + Brenk substructure catalogs), MW/clogP via RDKit Descriptors/Crippen.
CYP/hERG flags are **structural rule-of-thumb heuristics** (basic-amine+lipophilicity for hERG; aniline/furan/thiophene
motifs for CYP reactivity) — **not a validated predictive ADMET model**. Treat as triage signal only.

## Summary counts (of 20)

| Metric | Count |
|---|---:|
| PAINS alert | {n_pains} |
| Brenk structural alert | {n_brenk} |
| CYP-risk motif flagged | {n_cyp} |
| hERG-risk pattern flagged | {n_herg} |
| Clean by all heuristic filters | {n_clean} |
| Already clinical-stage or approved (max_phase>0) | {len(n_clinical)} |

## Full table

| Rank | Compound | Name | Phase | MW | clogP | PAINS | Brenk | CYP | hERG | Notes |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
""")
        for r in out_rows:
            f.write(f"| {r['rank']} | {r['compound_id']} | {r['name']} | {r['max_phase']} | {r['mw']} | {r['clogp']} | "
                    f"{r['pains_hit']} | {r['brenk_hit']} | {r['cyp_risk_flag']} | {r['herg_risk_flag']} | {r['notes']} |\n")

        f.write(f"""
## Prioritization notes

- **{n_clean} of 20** are clean by all heuristic structural filters — best starting points for follow-up.
- **{len(n_clinical)} of 20** are already at clinical stage or approved — faster to purchase/assay if repurposing is viable,
  but check for off-target/known indication conflicts (see companion ChEMBL cross-check).
- PAINS/Brenk hits do not automatically disqualify a hit but warrant closer look at the flagged substructure before
  committing synthesis/purchase resources.
- These CYP/hERG heuristics are coarse triage signals, not replacements for real ADMET assays (microsomal stability,
  hERG patch-clamp) before any in vivo consideration.
""")

    print(f"Wrote {OUT_CSV} ({len(out_rows)} rows)")
    print(f"Wrote {OUT_MD}")
    print()
    print("First 5 CSV rows:")
    for r in out_rows[:5]:
        print(r)
    print(f"\nTotal rows: {len(out_rows)}")

if __name__ == "__main__":
    main()
