"""ws6 P3: literature inventory of REPORTED pockets per target on the binder list.
Europe PMC title/abstract search; saves PMIDs+titles as the audit trail for
"known/literature-reported pockets". Reviewer-facing claim: a pocket is
'novel' only if absent from this inventory AND absent from the co-crystal
ligand positions (P2).
"""
import json, time, urllib.parse, urllib.request
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
OUT = BASE / "data/novelq_p3_literature_pockets.json"

# per-target Europe PMC queries (title/abstract). Curated: each targets the
# pocket literature of that target, not the protein generally.
QUERIES = {
    "TSPO":    ['"translocator protein" AND ("cholesterol binding" OR "drug binding pocket" OR "PK 11195" OR "PK11195")',
                'TSPO AND ("steroidogenic" OR "porphyrin" OR "heme") AND (pocket OR site)'],
    "NR1I3":   ['"constitutive androstane receptor" AND ("ligand-binding pocket" OR "crystal structure")'],
    "NR1I2":   ['"pregnane X receptor" AND ("ligand-binding pocket" OR "crystal structure")'],
    "GABRA1":  ['"benzodiazepine site" AND GABA AND ("alpha1" OR "alpha 1")',
                '"picrotoxin site" AND GABA'],
    "OPRM1":   ['"mu opioid receptor" AND ("orthosteric" OR "allosteric") AND (pocket OR site) AND (structure OR crystal)'],
    "OPRK1":   ['"kappa opioid receptor" AND ("orthosteric" OR "allosteric") AND (pocket OR site)'],
    "ALDH1A1": ['"aldehyde dehydrogenase 1A1" AND (inhibitor OR pocket OR "catalytic site")'],
    "CNR1":    ['"cannabinoid receptor 1" AND ("orthosteric" OR "allosteric") AND (pocket OR site)'],
    "HRH3":    ['"histamine H3 receptor" AND ("orthosteric" OR "allosteric") AND (pocket OR site)'],
    "HSD11B1": ['"11 beta-hydroxysteroid dehydrogenase 1" AND (inhibitor OR pocket) AND (crystal OR structure)'],
    "SIGMAR1": ['"sigma-1 receptor" AND ("ligand binding site" OR pocket) AND (crystal OR structure)'],
    "GRM2":    ['"mGlu2" OR "metabotropic glutamate receptor 2" AND allosteric AND (pocket OR site) AND transmembrane'],
    "GRM5":    ['"mGlu5" AND ("allosteric site" OR MPEP OR "transmembrane domain")'],
    "MEN1":    ['menin AND (MLL OR inhibitor) AND (pocket OR "binding site") AND structure'],
    "TMEM97":  ['"sigma-2 receptor" AND ("binding site" OR pocket) AND (structure OR crystal)'],
    "NPSR":    ['"neuropeptide S receptor" AND (pocket OR site OR structure)'],
    "PMP22":   ['"peripheral myelin protein 22" AND (structure OR pocket OR cavity)'],
    "ALOX15":  ['"15-lipoxygenase" AND ("catalytic pocket" OR "active site" OR inhibitor) AND structure'],
}

def esearch(q, page_size=25):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
           + urllib.parse.quote(q + " AND (SRC:MED)")
           + f"&format=json&pageSize={page_size}&resultType=lite")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    hits = []
    for h in d.get("resultList", {}).get("result", []):
        hits.append({"pmid": h.get("pmid"), "title": h.get("title"),
                     "year": h.get("pubYear"), "journal": h.get("journalTitle", "")[:40]})
    return d.get("hitCount", 0), hits

def main():
    res = {}
    for gene, qs in QUERIES.items():
        entry = {"queries": qs, "hits": []}
        for q in qs:
            try:
                n, hits = esearch(q)
                entry["hitCount"] = entry.get("hitCount", 0) + n
                entry["hits"].extend(hits)
                time.sleep(0.4)
            except Exception as e:
                entry.setdefault("errors", []).append(f"{q[:40]}: {e}")
        # dedupe pmids, sort newest first
        seen = set()
        dd = []
        for h in sorted(entry["hits"], key=lambda x: -(int(x["year"] or 0))):
            if h["pmid"] and h["pmid"] not in seen:
                seen.add(h["pmid"])
                dd.append(h)
        entry["hits"] = dd[:40]
        res[gene] = entry
        print(f"{gene:8s} hitCount~{entry.get('hitCount',0):5d}  kept={len(dd)}  e.g. {dd[0]['title'][:70] if dd else '-'}")
    json.dump(res, open(OUT, "w"), indent=1)
    print("saved", OUT)

if __name__ == "__main__":
    main()
