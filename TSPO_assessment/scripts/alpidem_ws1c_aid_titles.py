"""WS1c: alpidem PubChem AID descriptions via PC_AssayContainer.assay.descr; gene map print."""
import json
import subprocess

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws1c/1.0"


def jget(url, timeout=90):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


d = json.load(open(f"{BASE}/data/alpidem_pubchem_actives_summary.json"))
by_aid = {}
for r in d["active"]:
    by_aid.setdefault(r["aid"], []).append(r)

# esummary gene map (recompute in-kernel to survive fresh interpreter)
gids = sorted({r["geneid"] for r in d["active"] if r["geneid"]})
sym = {}
for i in range(0, len(gids), 40):
    chunk = ",".join(gids[i:i + 40])
    dd = jget("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id="
              + chunk + "&retmode=json")
    for g in dd.get("result", {}).get("uids", []):
        rec = dd["result"].get(g, {})
        sym[g] = {"symbol": rec.get("nomenclaturesymbol"),
                  "name": rec.get("description"),
                  "org": rec.get("organism", {}).get("scientificname")}
json.dump(sym, open(f"{BASE}/data/alpidem_gene_symbols.json", "w"), indent=1)
print("== gene map ==")
for g in gids:
    m = sym.get(g, {})
    print(f"  {g} {m.get('symbol')} | {m.get('name')} | {m.get('org')}")

print("\n== AID titles ==")
aid_info = {}
for aid in sorted(by_aid, key=int):
    dd = jget(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/{aid}/description/JSON")
    title, src, tgt, comments = None, None, None, []
    cont = dd.get("PC_AssayContainer") or []
    if cont:
        rec = (cont[0].get("assay") or {})
        a = rec.get("descr") or rec
        title = a.get("name")
        src = json.dumps(a.get("aid_source", {}))[:80]
        tgt = json.dumps(a.get("target", {}))[:150]
        comments = [str(c)[:160] for c in (rec.get("comment") or [])][:4]
    aid_info[aid] = {"title": title, "source": src, "target": tgt, "comments": comments}
    vals = sorted({r["uM"] for r in by_aid[aid] if r["uM"]}, key=float)
    accs = sorted({r["protein_acc"] for r in by_aid[aid] if r["protein_acc"]})
    gsyms = sorted({sym.get(r["geneid"], {}).get("symbol") or r["geneid"]
                    for r in by_aid[aid] if r["geneid"]})
    print(f"AID {aid} n={len(by_aid[aid])} vals={vals} accs={accs[:6]} genes={gsyms[:6]}")
    print(f"   {title} | src={src}")
    if tgt:
        print(f"   tgt={tgt}")
    for c in comments:
        print(f"   C: {c}")
json.dump(aid_info, open(f"{BASE}/data/alpidem_aid_descriptions.json", "w"), indent=1)
