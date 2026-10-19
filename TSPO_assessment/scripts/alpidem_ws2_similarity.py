"""WS2: alpidem similarity closure (ChEMBL 70%) -> analogue activity tally + zolpidem total."""
import json
import subprocess
import time

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws2/1.0"


def jget(url, timeout=120):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


# ---- 1) similarity closure around alpidem
d = jget("https://www.ebi.ac.uk/chembl/api/data/similarity/CHEMBL54349/70.json?limit=200")
mols = d.get("molecules", [])
analogues = [m["molecule_chembl_id"] for m in mols if m["molecule_chembl_id"] != "CHEMBL54349"]
print(f"similarity(70%) analogues: {len(analogues)}")
json.dump({"n": len(analogues), "ids": analogues,
           "mols": [{"id": m["molecule_chembl_id"], "pref": m.get("pref_name"),
                     "syn": [s.get("molecule_synonym") for s in (m.get("molecule_synonyms") or [])][:6]}
                    for m in mols]},
          open(f"{BASE}/data/alpidem_ws2_similarity_raw.json", "w"), indent=1)

# ---- 2) tally targets across analogues (skip self), paged 500, capped
tally, offset, guard = {}, 0, 0
seen_acts = 0
ids = analogues
while offset < len(ids) and guard < 400:  # guard: max 400 pages
    chunk = ",".join(ids[offset:offset + 20])
    if not chunk:
        break
    dd = jget(f"https://www.ebi.ac.uk/chembl/api/data/activity.json?"
              f"molecule_chembl_id__in={chunk}&limit=500")
    acts = dd.get("activities", [])
    seen_acts += len(acts)
    for a in acts:
        tid = a.get("target_chembl_id")
        if not tid or a.get("molecule_chembl_id") == "CHEMBL54349":
            continue
        t = tally.setdefault(tid, {"pref": a.get("target_pref_name"), "n": 0,
                                   "best": None, "types": set()})
        t["n"] += 1
        v = a.get("standard_value")
        if v not in (None, ""):
            try:
                fv = float(v)
                if t["best"] is None or fv < t["best"]:
                    t["best"] = fv
            except (TypeError, ValueError):
                pass
        t["types"].add(a.get("assay_type"))
    offset += 20
    guard += 1
    time.sleep(0.2)
print(f"analogue activities scanned: {seen_acts}")
top = sorted(tally.items(), key=lambda kv: -kv[1]["n"])[:45]
for tid, t in top:
    print(f"  {tid} {t['pref']}: n={t['n']} best={t['best']} types={sorted(t['types'])}")
json.dump({"n_analogues": len(analogues), "n_activities": seen_acts,
           "tally": {k: {"pref": v["pref"], "n": v["n"], "best": v["best"],
                          "types": sorted(v["types"])} for k, v in tally.items()}},
          open(f"{BASE}/data/alpidem_ws2_analogue_target_tally.json", "w"), indent=1)

# ---- 3) zolpidem activity total + top targets
dz = jget("https://www.ebi.ac.uk/chembl/api/data/activity.json?molecule_chembl_id=CHEMBL911&limit=1")
total = dz.get("page_meta", {}).get("total_count")
print(f"\nzolpidem CHEMBL911 total activities (page_meta): {total}")
