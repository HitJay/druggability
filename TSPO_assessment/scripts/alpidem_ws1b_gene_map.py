"""WS1b: alpidem PubChem Active rows -> gene symbols (esummary) + AID descriptions."""
import json
import subprocess
import urllib.parse

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws1b/1.0"


def jget(url, timeout=90):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


# ---- 1) verify alpidem ChEMBL activity count is really zero
d = jget("https://www.ebi.ac.uk/chembl/api/data/activity.json?molecule_chembl_id=CHEMBL54349&limit=5")
print("chembl activity check:", json.dumps(d.get("page_meta", {}), indent=1)[:200])
print("first activities:", d.get("activities", []))

# ---- 2) group PubChem active rows by AID
d = json.load(open(f"{BASE}/data/alpidem_pubchem_actives_summary.json"))
by_aid = {}
for r in d["active"]:
    by_aid.setdefault(r["aid"], []).append(r)
print(f"\ndistinct AIDs among Actives: {len(by_aid)}")

# ---- 3) esummary for all geneids
gids = sorted({r["geneid"] for r in d["active"] if r["geneid"]})
print("geneids:", gids)
sym = {}
for i in range(0, len(gids), 40):
    chunk = ",".join(gids[i:i + 40])
    dd = jget("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id="
              + chunk + "&retmode=json")
    for g in dd.get("result", {}).get("uids", []):
        rec = dd["result"].get(g, {})
        sym[g] = {
            "symbol": rec.get("nomenclaturesymbol"),
            "name": rec.get("description"),
            "org": rec.get("organism", {}).get("scientificname"),
        }
for g in gids:
    print(f"  {g}: {sym.get(g)}")

# ---- 4) protein acc -> name via PubChem esummary (db=protein) for accs without geneid
accs = sorted({r["protein_acc"] for r in d["active"] if r["protein_acc"]})
acc_info = {}
for a in accs:
    if a.startswith("NP_") or a.startswith("AA") or a.startswith("BA") or a.startswith("ABB"):
        dd = jget("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=protein&id="
                  + urllib.parse.quote(a) + "&retmode=json")
        rec = dd.get("result", {}).get(a, {})
        acc_info[a] = {"title": rec.get("title"), "capture": rec.get("caption")}
        print(f"  {a}: {rec.get('title') or dd.get('result', {}).keys()}")
json.dump({"gene_map": sym, "acc_map": acc_info, "by_aid": {k: v for k, v in by_aid.items()}},
          open(f"{BASE}/data/alpidem_ws1b_geneid_map.json", "w"), indent=1)

# ---- 5) AID descriptions
for aid in by_aid:
    dd = jget(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/{aid}/description/JSON")
    recs = dd.get("PC_AssayDescription", [])
    title = None
    if recs:
        title = recs[0].get("assay", {}).get("description", {}).get("title")
        tgt = recs[0].get("assay", {}).get("target")
    print(f"AID {aid}: {title}")
