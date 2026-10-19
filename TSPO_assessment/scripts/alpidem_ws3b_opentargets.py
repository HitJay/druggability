"""WS3b: resolve Ensembl IDs by symbol via OT search, then associations (fixed datasource id)."""
import json
import subprocess
import time

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws3b/1.0"
GQL = "https://api.platform.opentargets.org/api/v4/graphql"

symbols = ["TSPO", "GABRA1", "GABRA2", "GABRA3", "GABRA5", "NR1I2", "NR1I3",
           "NR0B2", "ABCB11", "ALB", "ORM1", "PPARG", "THRB", "KCNH2"]

QUERY = """query($ens:[String!]!){
  targets(ensemblIds:$ens){
    id approvedSymbol
    associatedDiseases{
      count
      rows{disease{id name} score datasourceScores{id score}}
    }
  }
}"""


def gql(query, variables=None):
    payload = json.dumps({"query": query, "variables": variables or {}})
    r = subprocess.run(["curl", "-sS", "--max-time", "90", "-A", UA, "-X", "POST", GQL,
                        "-H", "Content-Type: application/json", "-d", payload],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


# ---- resolve ids by symbol
resolved = {}
for sym in symbols:
    d = gql("""query{search(queryString:"%s",entityNames:["target"]){hits{id name entity}}}""" % sym)
    hits = (d.get("data") or {}).get("search", {}).get("hits", [])
    pick = next((h for h in hits if h.get("name", "").upper() == sym), None)
    if pick:
        resolved[sym] = pick["id"]
    print(sym, "->", pick and (pick["id"], pick["name"]))
    time.sleep(0.5)
json.dump(resolved, open(f"{BASE}/data/alpidem_ws3_ot_ids.json", "w"), indent=1)

# ---- associations
d = gql(QUERY, {"ens": list(resolved.values())})
errs = d.get("errors")
if errs:
    print("GraphQL errors:", json.dumps(errs)[:400])
METAB_PAT = ("diabet|obes|insulin|steatos|fatty liver|metabolic syndrome|body weight|adipos|"
             "anxiety|liver|hepat|cholesterol|lipid|bile")
report = {}
for t in (d.get("data") or {}).get("targets", []):
    sym = t["approvedSymbol"]
    rows = t["associatedDiseases"]["rows"]
    keep = [r for r in rows
            if any(p in r["disease"]["name"].lower() for p in METAB_PAT.split("|"))]
    keep.sort(key=lambda r: -r["score"])
    report[sym] = {"ensembl": t["id"], "overall_count": t["associatedDiseases"]["count"],
                   "filtered": [{"d": r["disease"]["name"], "score": round(r["score"], 3),
                                 "gen": round(next((ds["score"] for ds in (r["datasourceScores"] or [])
                                                    if ds.get("id") == "OPEN_TARGETS_GENETICS"), 0.0), 3)}
                                for r in keep[:8]]}
    print(f"{sym}: overall={t['associatedDiseases']['count']} filtered={len(keep)}")
    for r in report[sym]["filtered"]:
        print(f"   {r['score']:.3f} (gen {r['gen']:.3f}) {r['d'][:80]}")
    if not keep:
        print("   (nothing in filtered set)")

json.dump(report, open(f"{BASE}/data/alpidem_ws3_ot_associations.json", "w"), indent=1)
