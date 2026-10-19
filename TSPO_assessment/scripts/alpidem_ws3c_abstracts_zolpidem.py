"""WS3c: key abstract batch by PMID + zolpidem pages 2+ (target tally)."""
import json
import subprocess
import urllib.parse

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws3c/1.0"


def jget(url, timeout=90):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


pmids = ["1687121",  # clinical PK single doses
         "1680622",  # rat disposition
         "2574111",  # Pacifici 1989 plasma protein binding (cited)
         "7901754",  # 1993 GABA chloride current potentiation
         "11602696",  # 2001 alpidem vs zolpidem hepatocyte toxicity
         "8863805",  # Anzini 1996 (cited) PBR vs CBR selectivity
         "33158242",  # Gudasheva 2020 (cited) dipeptide TSPO ligands
         "7750686", "7750714", "7875405",  # hepatitis case reports
         "19720731",  # 2009 DILI covalent binding evaluation
         "26002041"]  # 2015 2-phenylimidazopyridine TSPO ligands behaviour
q = " OR ".join(f"EXT_ID:{p}" for p in pmids)
d = jget("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
         + urllib.parse.quote(q) + "&format=json&pageSize=20&resultType=core")
abs_out = []
for r in d.get("resultList", {}).get("result", []):
    abs_out.append({"pmid": r.get("pmid"), "year": r.get("pubYear"), "title": r.get("title"),
                    "journal": (r.get("journalInfo") or {}).get("journal", {}).get("title"),
                    "doi": r.get("doi"),
                    "abstract": (r.get("abstractText") or "")})
json.dump(abs_out, open(f"{BASE}/data/alpidem_key_abstracts.json", "w"), indent=1)
print(f"fetched {len(abs_out)} abstracts")
for a in abs_out:
    print(f"\n--- PMID:{a['pmid']} {a['year']} {a['title']}")
    print((a["abstract"] or "(no abstract)")[:900])

# ---- zolpidem pages 2..4 -> tallies beyond page 1
zacts = json.load(open(f"{BASE}/data/alpidem_zolpidem_chembl_activities_raw.json"))
for page in range(1, 4):
    dz = jget("https://www.ebi.ac.uk/chembl/api/data/activity.json?"
              f"molecule_chembl_id=CHEMBL911&limit=500&offset={page * 500}")
    zacts += dz.get("activities", [])
json.dump(zacts, open(f"{BASE}/data/alpidem_zolpidem_chembl_activities_raw.json", "w"))
print(f"\nzolpidem activities total now: {len(zacts)}")
ztally = {}
for a in zacts:
    tid = a.get("target_chembl_id")
    if not tid:
        continue
    t = ztally.setdefault(tid, {"pref": a.get("target_pref_name"), "n": 0, "best": None})
    t["n"] += 1
    v = a.get("standard_value")
    if v not in (None, ""):
        try:
            fv = float(v)
            if t["best"] is None or fv < t["best"]:
                t["best"] = fv
        except (TypeError, ValueError):
            pass
print("zolpidem top targets by record count:")
for tid, t in sorted(ztally.items(), key=lambda kv: -kv[1]["n"])[:25]:
    print(f"  {tid} {t['pref']}: n={t['n']} best={t['best']}")
json.dump(ztally, open(f"{BASE}/data/alpidem_zolpidem_target_tally.json", "w"), indent=1)
