"""WS1: alpidem (CHEMBL54349) ChEMBL activities + PubChem assay summary + zolpidem total check."""
import json
import subprocess

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws1/1.0"


def jget(url, timeout=90):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


# ---- 1) alpidem activities, paged 500
acts, offset = [], 0
while True:
    d = jget(f"https://www.ebi.ac.uk/chembl/api/data/activity.json?"
             f"molecule_chembl_id=CHEMBL54349&limit=500&offset={offset}")
    page = d.get("activities", [])
    total = d.get("page_meta", {}).get("total_count")
    acts += page
    offset += 500
    print(f"page offset={offset} got={len(page)} total={total}")
    try:
        if offset >= int(total) or not page:
            break
    except (TypeError, ValueError):
        break
json.dump(acts, open(f"{BASE}/data/alpidem_chembl_activities_raw.json", "w"))
print(f"alpidem activities saved: {len(acts)}")

# compact view: target, type, value, units, pchembl, assay desc snippet
rows = {}
for a in acts:
    tid = a.get("target_chembl_id")
    if not tid:
        continue
    rows.setdefault(tid, []).append({
        "pref": a.get("target_pref_name"),
        "type": a.get("standard_type"),
        "rel": a.get("relation"),
        "val": a.get("standard_value"),
        "units": a.get("standard_units"),
        "p": a.get("pchembl_value"),
        "assay_type": a.get("assay_type"),
        "desc": (a.get("assay_description") or "")[:110],
        "doc": a.get("document_chembl_id"),
        "organism": a.get("target_organism"),
    })
print(f"\ndistinct alpidem targets in ChEMBL: {len(rows)}")
for tid, rs in sorted(rows.items(), key=lambda kv: -len(kv[1])):
    best = min([r for r in rs if r["val"] not in (None, "")],
               key=lambda r: float(r["val"]) if r["val"] else 9e9, default=None)
    print(f"{tid} {rs[0]['pref']}: n={len(rs)} best={best and (best['type'], best['val'], best['units'], 'p'+str(best['p']))} e.g. {rs[0]['desc'][:80]}")

# ---- 2) PubChem assaysummary for CID 54897
d = jget("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/54897/assaysummary/JSON")
json.dump(d, open(f"{BASE}/data/alpidem_pubchem_assays_raw.json", "w"))
n_assay = 0
active_rows = []
try:
    table = d["Table"]["Table"][0] if isinstance(d["Table"]["Table"][0], dict) else None
except (KeyError, TypeError, IndexError):
    table = None
# generic parse: Table.Row[].Cell
try:
    rows_pc = d["Table"]["Row"]
    n_assay = len(rows_pc)
    for r in rows_pc:
        c = r["Cell"]
        if c[4] == "Active":
            active_rows.append({"aid": c[0], "name": c[2] if len(c) > 2 else None,
                                "outcome": c[4], "protein_acc": c[5] if len(c) > 5 else None,
                                "geneid": c[6] if len(c) > 6 else None, "uM": c[7] if len(c) > 7 else None})
except (KeyError, TypeError):
    pass
print(f"\nPubChem assays for CID 54897: {n_assay} total, {len(active_rows)} Active")
for a in active_rows[:60]:
    print("  ", a)
json.dump({"n_total": n_assay, "active": active_rows},
          open(f"{BASE}/data/alpidem_pubchem_actives_summary.json", "w"), indent=1)
