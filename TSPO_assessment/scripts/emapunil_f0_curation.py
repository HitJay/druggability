"""F0: emapunil identity (runtime-resolved) + verify prior PK11195 docking numbers for gate."""
import json
import subprocess
import urllib.parse

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 emapunil-f0/1.0"


def jget(url, timeout=60):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


out = {}
# PubChem: emapunil / XBD-173 / AC-5216
for n in ["emapunil", "XBD-173", "AC-5216"]:
    d = jget(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(n)}/property/"
             f"CanonicalSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON")
    props = d.get("PropertyTable", {}).get("Properties", [])
    out[n] = props[0] if props else d
    print(n, "->", out[n])

# ChEMBL search (emapunil may be under synonym XBD173/AC-5216)
for n in ["emapunil", "XBD173", "AC-5216"]:
    d = jget(f"https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q={urllib.parse.quote(n)}&limit=15")
    hits = []
    for m in d.get("molecules", []):
        syns = " ".join(s.get("molecule_synonym", "") for s in (m.get("molecule_synonyms") or [])).lower()
        if n.lower() in syns or n.lower().replace("-", "") in syns:
            hits.append({"id": m["molecule_chembl_id"], "pref": m.get("pref_name"),
                         "smiles": (m.get("molecule_structures") or {}).get("canonical_smiles"),
                         "syn": [s.get("molecule_synonym") for s in (m.get("molecule_synonyms") or [])][:10]})
    out["chembl_" + n] = hits
    print("chembl", n, "->", [(h["id"], h["pref"]) for h in hits])

# prior docking numbers (gate anchors)
try:
    prior = json.load(open(f"{BASE}/output/docking/validation_gate_results.json"))
    out["prior_pk11195_gate"] = {k: v.get("vina_scores", [None])[0] for k, v in prior.items()}
    print("prior PK11195 gate:", out["prior_pk11195_gate"])
except FileNotFoundError:
    print("no validation_gate_results.json")
try:
    prior2 = json.load(open(f"{BASE}/output/docking/ws2c_docking_matrix.json"))
    out["prior_ws2c"] = {k: v["scores"][0] for k, v in prior2.items()}
    print("prior ws2c emapunil rows:", {k: v for k, v in out["prior_ws2c"].items() if "emapunil" in k})
except FileNotFoundError:
    print("no ws2c matrix")

json.dump(out, open(f"{BASE}/data/emapunil_f0_curation.json", "w"), indent=1)
