"""WS0b: find alpidem in ChEMBL by InChIKey / SMILES substring; keep raw for evidence."""
import json
import subprocess
import urllib.parse

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws0b/1.0"
IK = "JRTIDHTUMYMPRU-UHFFFAOYSA-N"
SMI = "CCCN(CCC)C(=O)CC1=C(N=C2N1C=C(C=C2)Cl)C3=CC=C(C=C3)Cl"


def get(url, timeout=60):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    return r.stdout


def jget(url):
    try:
        return json.loads(get(url))
    except json.JSONDecodeError:
        return {"_raw": get(url)[:300]}


found = []
# InChIKey search
d = jget(f"https://www.ebi.ac.uk/chembl/api/data/molecule.json?"
         f"molecule_structures__standard_inchikey__exact={IK}&format=json")
found += d.get("molecules", [])
# SMILES substring (flexmatch for the core)
d = jget("https://www.ebi.ac.uk/chembl/api/data/molecule.json?"
         + urllib.parse.urlencode({"molecule_structures__canonical_smiles__flexmatch": SMI,
                                   "format": "json"}))
found += d.get("molecules", [])
# synonym scan: StA + RP-31
for syn in ["RP-31264", "RP31264", "64047", "stupen"]:
    d = jget(f"https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q={urllib.parse.quote(syn)}&limit=15")
    for m in d.get("molecules", []):
        syns = " ".join(s.get("molecule_synonym", "") for s in (m.get("molecule_synonyms") or [])).lower()
        if "alpidem" in syns or syn.lower() in syns:
            found.append(m)

seen, uniq = set(), []
for m in found:
    cid = m["molecule_chembl_id"]
    if cid not in seen:
        seen.add(cid)
        uniq.append({
            "chembl_id": cid,
            "pref_name": m.get("pref_name"),
            "molecule_type": m.get("molecule_type"),
            "max_phase": m.get("max_phase"),
            "synonyms": [s.get("molecule_synonym") for s in (m.get("molecule_synonyms") or [])][:20],
            "inchikey": (m.get("molecule_structures") or {}).get("standard_inchikey"),
            "smiles": (m.get("molecule_structures") or {}).get("canonical_smiles"),
        })

print(json.dumps(uniq, indent=1))
json.dump({"alpidem_inchembl": uniq, "inchikey": IK, "smiles": SMI, "pubchem_cid": 54897},
          open(f"{BASE}/data/alpidem_ws0b_chembl_resolve.json", "w"), indent=1)

# ---- Zolpidem ChEMBL activities (comparator backbone), paged at 500
acts, offset = [], 0
while True:
    d = jget(f"https://www.ebi.ac.uk/chembl/api/data/activity.json?"
             f"molecule_chembl_id=CHEMBL911&limit=500&offset={offset}")
    page = d.get("activities", [])
    acts += page
    total = d.get("page_meta", {}).get("total_count")
    offset += 500
    try:
        if offset >= int(total) or not page:
            break
    except (TypeError, ValueError):
        break
json.dump(acts, open(f"{BASE}/data/alpidem_zolpidem_chembl_activities_raw.json", "w"))
print(f"zolpidem CHEMBL911 activities: {len(acts)} records saved")
targets = sorted({(a.get("target_chembl_id"), a.get("target_pref_name")) for a in acts
                  if a.get("target_chembl_id")})
print(f"zolpidem distinct protein targets: {len(targets)}")
for t in targets[:40]:
    print("  ", t)
