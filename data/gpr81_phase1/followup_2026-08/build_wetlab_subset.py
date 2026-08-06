#!/usr/bin/env python3
"""
GPR81 wet-lab benchmark subset (20 compounds) — selection rationale.

Goal: a stratified panel that lets the wet-lab data answer the open questions
(1) does either computational layer correlate with measured EC50?
(2) do partial agonists separate from full agonists?
(3) do the pyridone/pyrimidinone and linker cliffs reproduce?

Selection logic (explicit, auditable):
- LEADS (9): best-balanced / most potent leads by paper data + Vina tier
    c28 (22nM, 41x/82x, LLE 5.3) | c26 (21nM) | c29 (75nM, 667x GHSR) |
    c30 (5nM) | c38 (54nM, 500x GHSR, sol 95uM) | c04 (1.4nM) | c07 (3.6nM) |
    c10 (13nM) | c11 (19nM)
- PARTIAL-AGONISM PROBE (2): c05 (0.74nM, Emax 47%) | c08 (7nM, Emax 74%)
- MECHANISM PAIRS (3): c27 (pyrimidinone vs c26) | c31 (pyrimidinone vs c30) |
    c24 (linker-variant collapse, 33uM)
- BOLTZ CONTROLS (2): t02 (highest Boltz prob 0.586, ~50nM) |
    c35 (Boltz A 0.549 but weak potency 600nM)  -> tests whether Boltz
    probability carries any signal at all
- REFERENCE ACIDS (4): t03 CHBA | t04 3,5-DHBA | t05 3-OBA | lac lactate
    (orthosteric-pocket controls; lactate = endogenous)

Counterscreen: GPR109A (niacin-flush liability) + GHS-R1a for every analog
measured (the paper's own selectivity panel).

Outputs: wetlab_benchmark_subset.csv + section 6 in gpr81_boltz_wetlab_report.html
"""
import csv, json
from pathlib import Path
import html as H

BASE = Path(__file__).resolve().parent

SELECT = {
    # entry_id: rationale
    "c28": "lead: best balance (22nM, 41x GPR109A, 82x GHSR, LLE 5.3)",
    "c26": "lead: 21nM, 29x/62x",
    "c29": "lead: 75nM, 25x/667x GHSR",
    "c30": "lead: most potent 5nM (7.4x GPR109A only)",
    "c38": "lead: amide series, 54nM, 500x GHSR, sol 95uM",
    "c04": "potent acyl-urea 1.4nM (selectivity unknown)",
    "c07": "potent acyl-urea 3.6nM, Emax 70% (selectivity unknown)",
    "c10": "potent acyl-urea 13nM",
    "c11": "potent acyl-urea 19nM",
    "c05": "partial-agonist probe: 0.74nM, Emax 47%",
    "c08": "partial-agonist probe: 7nM, Emax 74%",
    "c27": "mechanism pair: pyrimidinone vs c26 (21x loss)",
    "c31": "mechanism pair: pyrimidinone vs c30 (47x loss)",
    "c24": "mechanism pair: linker-variant collapse (33uM)",
    "t02": "Boltz control: highest affinity prob 0.586 (Takeda ~50nM)",
    "c35": "Boltz control: prob 0.549 but weak potency 600nM",
    "t03": "reference acid CHBA (8Z87 co-crystal)",
    "t04": "reference acid 3,5-DHBA (9KT9 co-crystal)",
    "t05": "reference acid 3-OBA",
    "lac": "endogenous ligand lactate (8Z8A co-crystal, assay control)",
}


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
    boltz = {}
    csv_path = BASE / "data/boltz_results.csv"
    if csv_path.exists():
        for r in csv.DictReader(open(csv_path)):
            boltz[r["entry_id"]] = r

    by_id = {c["entry_id"]: c for c in sc["compounds"]}
    rows = []
    for eid, rationale in SELECT.items():
        c = by_id[eid]
        b = boltz.get(eid, {})
        prob = f(b.get("boltz_affinity_probability_binary"))
        rows.append({
            "entry_id": eid,
            "name": c.get("name", ""),
            "series": c.get("series", ""),
            "ec50_nM": c.get("ec50_nM"),
            "emax_pct": c.get("emax_pct"),
            "vina_tier": c.get("tier", ""),
            "vina_8Z8A_score": c.get("dock_8Z8A_best"),
            "boltz_prob": prob,
            "boltz_tier": b.get("_tier", ""),
            "gpr109a_fold": c.get("gpr109a_fold"),
            "ghsr_fold": c.get("ghsr_fold"),
            "rationale": rationale,
            "counterscreen": "GPR109A + GHS-R1a",
        })
    # Boltz tier from the report module rule (tertiles) - replicate here
    probs = sorted(f(r.get("boltz_affinity_probability_binary")) for r in boltz.values()
                   if f(r.get("boltz_affinity_probability_binary")) is not None)
    if len(probs) >= 9:
        lo, hi = probs[len(probs) // 3], probs[2 * len(probs) // 3]
        for r in rows:
            p = r["boltz_prob"]
            if p is None:
                r["boltz_tier"] = ""
            else:
                r["boltz_tier"] = "A" if p >= hi else ("B" if p >= lo else "C")

    with open(BASE / "wetlab_benchmark_subset.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"subset: {len(rows)} compounds -> wetlab_benchmark_subset.csv")
    for r in rows:
        print(f"  {r['entry_id']:5s} EC50={r['ec50_nM']} Vina={r['vina_tier']} "
              f"Boltz={r['boltz_tier']} ({r['boltz_prob']}) | {r['rationale'][:60]}")
    return rows


if __name__ == "__main__":
    main()
