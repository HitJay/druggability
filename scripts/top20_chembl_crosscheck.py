#!/usr/bin/env python3
"""Top-20 GHSR strong_inverse_agonist ChEMBL known-activity cross-check.

Queries the real ChEMBL REST API for each compound:
1. Any activity record against GHSR (target_chembl_id=CHEMBL4616, confirmed via
   target.json?target_synonym__icontains=Ghrelin -> "Growth hormone secretagogue
   receptor type 1", accession Q92847, human single protein).
2. mechanism.json for known primary target/mechanism (drug_mechanism records),
   falling back to the most frequent non-GHSR target across activity.json if no
   mechanism record exists, to flag likely off-target/promiscuous hits.
"""
import csv
import json
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path

OUTDIR = Path("output/2026-07-10/ghsr_inverse_agonist_docking")
RANKED = OUTDIR / "ranked_hits.csv"
LIBRARY = OUTDIR / "ghsr_screening_library.csv"
OUT_CSV = OUTDIR / "top20_chembl_crosscheck.csv"
OUT_MD = OUTDIR / "top20_chembl_summary.md"

GHSR_TARGET_ID = "CHEMBL4616"
BASE = "https://www.ebi.ac.uk/chembl/api/data"
UA = {"User-Agent": "druggability-research/1.0 (contact: QYJI@novonordisk.com)"}


def fetch_json(url, retries=3, delay=1.5):
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise last_err


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
    n_queried_ok = 0
    n_query_fail = 0
    n_known_ghsr = 0

    for row in top20:
        cid = row["compound_id"]
        lrow = lib.get(cid, {})
        name = lrow.get("name", cid)

        rec = {
            "rank": row["rank"], "compound_id": cid, "name": name,
            "has_known_ghsr_activity": "", "ghsr_activity_details": "",
            "primary_known_target": "", "primary_indication_or_mechanism": "",
            "promiscuity_flag": "", "notes": "",
        }

        # --- 1) GHSR-specific activity ---
        try:
            act_url = f"{BASE}/activity.json?molecule_chembl_id={cid}&target_chembl_id={GHSR_TARGET_ID}&limit=25"
            act_data = fetch_json(act_url)
            ghsr_acts = act_data.get("activities", [])
            n_queried_ok += 1
        except Exception as e:
            rec["notes"] = f"GHSR activity query FAILED: {e}"
            n_query_fail += 1
            ghsr_acts = None

        if ghsr_acts:
            n_known_ghsr += 1
            rec["has_known_ghsr_activity"] = "True"
            details = []
            for a in ghsr_acts[:5]:
                details.append(
                    f"{a.get('standard_type', '?')}={a.get('standard_value', '?')}"
                    f"{a.get('standard_units', '')} ({a.get('assay_description', '')[:60]})"
                )
            rec["ghsr_activity_details"] = " | ".join(details)
        elif ghsr_acts is not None:
            rec["has_known_ghsr_activity"] = "False"
            rec["ghsr_activity_details"] = "no GHSR activity records in ChEMBL"

        time.sleep(0.34)  # be polite to EBI

        # --- 2) Primary known mechanism/target (drug_mechanism) ---
        try:
            mech_url = f"{BASE}/mechanism.json?molecule_chembl_id={cid}&limit=10"
            mech_data = fetch_json(mech_url)
            mechs = mech_data.get("mechanisms", [])
        except Exception as e:
            mechs = None
            if not rec["notes"]:
                rec["notes"] = f"mechanism query FAILED: {e}"

        if mechs:
            targets = []
            actions = []
            for m in mechs:
                tname = m.get("target_chembl_id", "")
                mech_of_action = m.get("mechanism_of_action", "")
                if mech_of_action:
                    actions.append(mech_of_action)
                if tname:
                    targets.append(tname)
            rec["primary_known_target"] = "; ".join(sorted(set(targets))) or "n/a"
            rec["primary_indication_or_mechanism"] = "; ".join(sorted(set(actions))) or "n/a"
            is_ghsr_only = all(t == GHSR_TARGET_ID for t in targets) if targets else False
            rec["promiscuity_flag"] = "False" if is_ghsr_only else "True (has non-GHSR annotated mechanism)"
        else:
            # Fallback: look at most frequent target across broader activity search (top 25 records)
            try:
                broad_url = f"{BASE}/activity.json?molecule_chembl_id={cid}&limit=25"
                broad_data = fetch_json(broad_url)
                broad_acts = broad_data.get("activities", [])
                tgt_counter = Counter(a.get("target_pref_name", "unknown") for a in broad_acts if a.get("target_pref_name"))
                if tgt_counter:
                    top_targets = tgt_counter.most_common(3)
                    rec["primary_known_target"] = "; ".join(f"{t}({c})" for t, c in top_targets)
                    rec["primary_indication_or_mechanism"] = "no annotated drug_mechanism; inferred from activity assay targets"
                    non_ghsr_names = [t for t, c in tgt_counter.items() if "ghrelin" not in t.lower() and "GHSR" not in t]
                    rec["promiscuity_flag"] = "True (multiple assay targets, no clean single-target mechanism)" if len(tgt_counter) > 1 else "False"
                else:
                    rec["primary_known_target"] = "no activity records found at all"
                    rec["primary_indication_or_mechanism"] = "n/a"
                    rec["promiscuity_flag"] = "unknown (no data)"
            except Exception as e:
                rec["primary_known_target"] = "query failed"
                rec["primary_indication_or_mechanism"] = "n/a"
                rec["promiscuity_flag"] = "unknown"
                if not rec["notes"]:
                    rec["notes"] = f"fallback activity query FAILED: {e}"

        time.sleep(0.34)
        out_rows.append(rec)
        print(f"{cid} {name}: ghsr_activity={rec['has_known_ghsr_activity']} target={rec['primary_known_target'][:60]}")

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "compound_id", "name", "has_known_ghsr_activity",
                                           "ghsr_activity_details", "primary_known_target",
                                           "primary_indication_or_mechanism", "promiscuity_flag", "notes"])
        w.writeheader()
        w.writerows(out_rows)

    novel = [r for r in out_rows if r["has_known_ghsr_activity"] == "False"]
    known = [r for r in out_rows if r["has_known_ghsr_activity"] == "True"]
    promiscuous = [r for r in out_rows if str(r["promiscuity_flag"]).startswith("True")]

    with open(OUT_MD, "w") as f:
        f.write(f"""# GHSR Top-20 Strong Inverse Agonists — ChEMBL Known-Activity Cross-Check

**Method**: Live queries against ChEMBL REST API (`www.ebi.ac.uk/chembl/api/data`).
GHSR target confirmed as `{GHSR_TARGET_ID}` (Growth hormone secretagogue receptor type 1,
UniProt Q92847, human single protein) via `target.json?target_synonym__icontains=Ghrelin`.

Queries succeeded for {n_queried_ok}/20 compounds on the GHSR-specific activity check
({n_query_fail} failures, recorded in `notes`).

## Summary

| Category | Count |
|---|---:|
| Already has documented GHSR activity in ChEMBL | {len(known)} |
| No GHSR activity record found (potential novel hit) | {len(novel)} |
| Flagged as promiscuous / multi-target known compound | {len(promiscuous)} |

## Novel GHSR hits (no prior ChEMBL GHSR activity record)

""")
        if novel:
            for r in novel:
                f.write(f"- **{r['compound_id']}** ({r['name']}) — known target(s): {r['primary_known_target']}; "
                        f"mechanism: {r['primary_indication_or_mechanism']}\n")
        else:
            f.write("None — all 20 have some prior GHSR activity record.\n")

        f.write("\n## Known GHSR ligands re-discovered by docking\n\n")
        if known:
            for r in known:
                f.write(f"- **{r['compound_id']}** ({r['name']}) — {r['ghsr_activity_details']}\n")
        else:
            f.write("None.\n")

        f.write(f"""
## Off-target / promiscuity caution

{len(promiscuous)} of 20 compounds carry a known non-GHSR mechanism or multiple assay
targets in ChEMBL. These docking hits may reflect the compound's general binding
promiscuity (e.g. known kinase inhibitors, other GPCR ligands) rather than a
GHSR-specific interaction. Treat with extra caution before prioritizing for synthesis
or purchase — cross-check against the companion liability screen and the raw docking
pose before committing resources.

## Full table

| Rank | Compound | Name | Known GHSR activity | Primary known target | Mechanism/indication | Promiscuity |
|---:|---|---|---|---|---|---|
""")
        for r in out_rows:
            f.write(f"| {r['rank']} | {r['compound_id']} | {r['name']} | {r['has_known_ghsr_activity']} | "
                    f"{r['primary_known_target']} | {r['primary_indication_or_mechanism']} | {r['promiscuity_flag']} |\n")

    print(f"\nWrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"\nQueried OK: {n_queried_ok}/20, failed: {n_query_fail}/20")
    print(f"Known GHSR activity: {n_known_ghsr}/20")
    print("\nFirst 5 CSV rows:")
    for r in out_rows[:5]:
        print(r)
    print(f"\nTotal rows: {len(out_rows)}")


if __name__ == "__main__":
    main()
