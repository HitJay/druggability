"""WS3a: alpidem Open Targets genetics for candidate set + zolpidem key rows."""
import json
import subprocess

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 alpidem-ws3a/1.0"
GQL = "https://api.platform.opentargets.org/api/v4/graphql"

candidates = {
    "TSPO": "ENSG00000137909",
    "GABRA1": "ENSG00000122606",
    "GABRA2": "ENSG00000151834",
    "GABRA3": "ENSG00000106295",
    "GABRA5": "ENSG00000101463",
    "NR1I2": "ENSG00000144852",
    "NR1I3": "ENSG00000131477",
    "NR0B2": "ENSG00000158733",
    "ABCB11": "ENSG00000051592",
    "ALB": "ENSG00000163631",
    "ORM1": "ENSG00000272515",
    "PPARG": "ENSG00000132170",
    "KCNH2": "ENSG00000055118",
    "THRB": "ENSG00000151067",
}

QUERY = """query($ens:[String!]!){
  targets(ensemblIds:$ens){
    id approvedSymbol
    associatedDiseases{
      count
      rows{disease{id name} score datasourceScores{id score}}
    }
  }
}"""

METAB_PAT = ("diabet|obes|insulin|steatos|fatty liver|metabolic syndrome|body weight|adipos|"
             "anxiety|liver|hepat|cholesterol|lipid|bile")


def gql(query, variables):
    payload = json.dumps({"query": query, "variables": variables})
    r = subprocess.run(["curl", "-sS", "--max-time", "90", "-A", UA, "-X", "POST", GQL,
                        "-H", "Content-Type: application/json", "-d", payload],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:300]}


d = gql(QUERY, {"ens": list(candidates.values())})
errs = d.get("errors")
if errs:
    print("GraphQL errors:", json.dumps(errs)[:400])
report = {}
for t in (d.get("data") or {}).get("targets", []):
    sym = t["approvedSymbol"]
    rows = t["associatedDiseases"]["rows"]
    keep = [r for r in rows
            if any(p in r["disease"]["name"].lower() for p in METAB_PAT.split("|"))]
    keep.sort(key=lambda r: -r["score"])
    report[sym] = {"overall_count": t["associatedDiseases"]["count"],
                   "filtered": [{"d": r["disease"]["name"], "score": round(r["score"], 3),
                                 "ot": round(next((ds["score"] for ds in (r["datasourceScores"] or [])
                                                   if ds.get("id") == "OPEN_TARGETS_GENETICS"), 0.0), 3)}
                                for r in keep[:8]]}
    print(f"{sym}: overall={t['associatedDiseases']['count']} filtered={len(keep)}")
    for r in report[sym]["filtered"]:
        print(f"   {r['score']:.3f} (gen {r['ot']:.3f}) {r['d'][:80]}")
    if not keep:
        print("   (nothing in filtered set)")

json.dump(report, open(f"{BASE}/data/alpidem_ws3_ot_associations.json", "w"), indent=1)
