"""Alpidem target search — WS0: compound curation (PubChem + ChEMBL)."""
import json
import subprocess
import urllib.parse

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 (X11; Linux x86_64) alpidem-ws0/1.0"


def get(url, timeout=60):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    return r.stdout


def jget(url):
    txt = get(url)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt[:500]}


# ---- 1) PubChem by name
names = ["alpidem"]
out = {"pubchem": {}, "chembl": {}}
for n in names:
    q = urllib.parse.quote(n)
    d = jget(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/"
             f"CanonicalSMILES,IsomericSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON")
    out["pubchem"][n] = d
    print(n, "->", json.dumps(d.get("PropertyTable", {}), indent=1)[:400])

# zolpidem as comparator (same 2-aminomethylimidazo[1,2-a]pyridine scaffold)
for n in ["zolpidem"]:
    q = urllib.parse.quote(n)
    d = jget(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/"
             f"CanonicalSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON")
    out["pubchem"][n] = d
    print(n, "->", json.dumps(d.get("PropertyTable", {}), indent=1)[:300])

# ---- 2) ChEMBL search
for n in names + ["zolpidem"]:
    d = jget(f"https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q={n}&limit=25")
    mols = d.get("molecules", [])
    hits = []
    for m in mols:
        syns = [s.get("molecule_synonym", "") for s in (m.get("molecule_synonyms") or [])]
        syn_low = [s.lower() for s in syns]
        if n in syn_low or (m.get("pref_name") or "").lower() == n:
            hits.append({
                "chembl_id": m["molecule_chembl_id"],
                "pref_name": m.get("pref_name"),
                "synonyms": syns[:12],
                "max_phase": m.get("max_phase"),
                "inchikey": (m.get("molecule_structures") or {}).get("standard_inchikey"),
                "smiles": (m.get("molecule_structures") or {}).get("canonical_smiles"),
            })
    out["chembl"][n] = hits
    print("ChEMBL", n, "->", [(h["chembl_id"], h["pref_name"]) for h in hits])

json.dump(out, open(f"{BASE}/data/alpidem_ws0_curation.json", "w"), indent=1)
print("saved alpidem_ws0_curation.json")
