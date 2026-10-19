"""WS2d: alpidem Europe PMC literature sweep + cited-abstract batch + zolpidem remaining pages."""
import json
import subprocess
import urllib.parse

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws2d/1.0"


def jget(url, timeout=90):
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


def search_epmc(query, size=15):
    d = jget("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
             + urllib.parse.quote(query) + f"&format=json&pageSize={size}&resultType=core")
    return d.get("resultList", {}).get("result", [])


queries = {
    "tspo": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND ("peripheral benzodiazepine" OR TSPO OR translocator)',
    "gabaa": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND ("GABA-A" OR "central benzodiazepine" OR "benzodiazepine receptor")',
    "hepato": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND (hepatotoxicity OR "liver injury" OR "transaminases" OR hepatic)',
    "pk": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND (pharmacokinetics OR "protein binding" OR "alpha1-acid glycoprotein" OR orosomucoid OR Cmax)',
    "metab": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND (metabolite OR metabolism OR desalkyl OR carboxylic acid derivative)',
    "clinic": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND (anxiolytic OR anxiety OR generalized anxiety OR placebo)',
    "pet_occ": '"alpidem" AND (occupancy OR "positron emission" OR PET)',
    "review": '(TITLE:"alpidem" OR ABSTRACT:"alpidem") AND (review OR profile OR overview)',
}
out = {}
for k, q in queries.items():
    res = search_epmc(q)
    out[k] = [{"pmid": r.get("pmid"), "doi": r.get("doi"), "title": r.get("title"),
               "year": r.get("pubYear"), "journal": (r.get("journalInfo") or {}).get("journal", {}).get("title"),
               "abstract": (r.get("abstractText") or "")[:1500]}
              for r in res]
    print(f"\n== {k}: {len(res)} hits")
    for r in out[k][:8]:
        print(f"  PMID:{r['pmid']} {r['year']} {r['title'][:100]}")

json.dump(out, open(f"{BASE}/data/alpidem_ws2d_europepmc.json", "w"), indent=1)

# ---- cited papers' abstracts by DOI
dois = ["10.1021/jm960325j", "10.3390/molecules25215132",
        "10.1016/0924-977x(92)90081-i", "10.1007/BF00609419"]
q = " OR ".join(f'DOI:"{d}"' for d in dois)
res = search_epmc(q, size=10)
print(f"\n== cited papers by DOI: {len(res)} hits")
cited = [{"pmid": r.get("pmid"), "doi": r.get("doi"), "title": r.get("title"),
          "year": r.get("pubYear"), "abstract": (r.get("abstractText") or "")[:2000]} for r in res]
for c in cited:
    print(f"  PMID:{c['pmid']} {c['year']} {c['title'][:110]}")
json.dump(cited, open(f"{BASE}/data/alpidem_cited_abstracts.json", "w"), indent=1)
