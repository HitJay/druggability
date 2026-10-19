"""WS2b: similarity closure retry with backoff + zolpidem page fetch retry."""
import json
import subprocess
import time

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws2b/1.0"


def jget_retry(url, tries=5, timeout=120):
    for i in range(tries):
        r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                           capture_output=True, text=True)
        out = r.stdout
        if out.lstrip().startswith(("{", "[")):
            try:
                return json.loads(out)
            except json.JSONDecodeError:
                pass
        wait = 5 * (2 ** i)
        print(f"  retry {i + 1} in {wait}s (got HTML/empty, len={len(out)})")
        time.sleep(wait)
    return {"_failed": True}


# ---- 1) similarity closure around alpidem
d = jget_retry("https://www.ebi.ac.uk/chembl/api/data/similarity/CHEMBL54349/70.json?limit=200")
mols = d.get("molecules", [])
analogues = [m["molecule_chembl_id"] for m in mols if m["molecule_chembl_id"] != "CHEMBL54349"]
print(f"similarity(70%) analogues: {len(analogues)}")
json.dump({"n": len(analogues),
           "mols": [{"id": m["molecule_chembl_id"], "pref": m.get("pref_name"),
                     "sim": m.get("similarity"),
                     "syn": [s.get("molecule_synonym") for s in (m.get("molecule_synonyms") or [])][:8]}
                    for m in mols]},
          open(f"{BASE}/data/alpidem_ws2_similarity_raw.json", "w"), indent=1)

# ---- 2) tally targets across analogues
tally, offset, guard = {}, 0, 0
seen_acts = 0
while offset < len(analogues) and guard < 60:
    chunk = ",".join(analogues[offset:offset + 20])
    dd = jget_retry(f"https://www.ebi.ac.uk/chembl/api/data/activity.json?"
                    f"molecule_chembl_id__in={chunk}&limit=500")
    if dd.get("_failed"):
        print(f"  chunk at {offset} failed permanently, skipping")
        offset += 20
        continue
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
    time.sleep(1)
print(f"analogue activities scanned: {seen_acts}")
top = sorted(tally.items(), key=lambda kv: -kv[1]["n"])[:45]
for tid, t in top:
    print(f"  {tid} {t['pref']}: n={t['n']} best={t['best']} types={sorted(t['types'])}")
json.dump({"n_analogues": len(analogues), "n_activities": seen_acts,
           "tally": {k: {"pref": v["pref"], "n": v["n"], "best": v["best"],
                          "types": sorted(v["types"])} for k, v in tally.items()}},
          open(f"{BASE}/data/alpidem_ws2_analogue_target_tally.json", "w"), indent=1)

# ---- 3) zolpidem full activity count
dz = jget_retry("https://www.ebi.ac.uk/chembl/api/data/activity.json?molecule_chembl_id=CHEMBL911&limit=1")
print(f"zolpidem total activities (page_meta): {dz.get('page_meta', {}).get('total_count')}")
