"""F1: pocket map — resolve ligand-bound structures for PK11195 binder-list proteins.

Targets (from ws5_pk11195_full_binder_list_v1.csv, measured layer + prediction-only):
  TSPO (P30536) [have 4RYI], NR1I3/CAR (Q14994) [have 1XVP], NR1I2/PXR (O75469) [have 2QNV],
  GABRA1 (P47869) [have 6X3X BZD site / 6HUG PIO site], HDAC6 (Q9UBN7), TRHR (P34981),
  NPSR (Q6W5P4), MEN1 (O00255), TDP1 (Q9NUW8), ALDH1A1 (P00352), PMP22 (Q01453),
  HSD11B1 (P28845), SIGMAR1 (Q99720), ALOX15 (P16050), GRM2 (Q14416), CNR1 (P21554),
  OPRK1 (P41145), TMEM97 (Q5BJF2), OPRM1 (P35372), GRM5 (P41574), HRH3 (Q9Y5N1).
"""
import json
import subprocess

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 emapunil-f1/1.0"


def post(url, payload):
    r = subprocess.run(["curl", "-sS", "--max-time", "90", "-A", UA, "-H",
                        "Content-Type: application/json", "-d", payload, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout[:200]}


TARGETS = {
    "TSPO_h":   ("P30536", None),
    "CAR":      ("Q14994", None),
    "PXR":      ("O75469", None),
    "GABRA1":   ("P47869", None),
    "HDAC6":    ("Q9UBN7", None),
    "TRHR":     ("P34981", None),
    "NPSR":     ("Q6W5P4", None),
    "MEN1":     ("O00255", None),
    "TDP1":     ("Q9NUW8", None),
    "ALDH1A1":  ("P00352", None),
    "PMP22":    ("Q01453", None),
    "HSD11B1":  ("P28845", None),
    "SIGMAR1":  ("Q99720", None),
    "ALOX15":   ("P16050", None),
    "GRM2":     ("Q14416", None),
    "CNR1":     ("P21554", None),
    "OPRK1":    ("P41145", None),
    "TMEM97":   ("Q5BJF2", None),
    "OPRM1":    ("P35372", None),
    "GRM5":     ("P41574", None),
    "HRH3":     ("Q9Y5N1", None),
}

QUERY = {
    "query": {
        "type": "terminal",
        "service": "text",
        "parameters": {"attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.gene_accession",
                        "operator": "exact_match", "value": None},
    },
    "return_type": "polymer_entity",
    "request_options": {
        "results_content_type": ["experimental"],
        "paginate": {"start": 0, "rows": 25},
        "sort": [{"sort_by": "score", "direction": "desc"}],
    },
}

map_out = {}
for name, (acc, _) in TARGETS.items():
    q = json.loads(json.dumps(QUERY))
    q["query"]["parameters"]["value"] = acc
    d = post("https://search.rcsb.org/rcsbsearch/v2/query", json.dumps(q))
    entries = []
    for r in (d.get("result_set") or [])[:25]:
        pdb = r["identifier"]
        score = r.get("score", 0)
        entries.append({"pdb": pdb, "score": round(score, 3)})
    map_out[name] = {"uniprot": acc, "n_entries": d.get("total_count", 0), "entries": entries}
    print(f"{name:9s} {acc}: {d.get('total_count', 0)} entries | top: "
          + ", ".join(e["pdb"] for e in entries[:6]))

json.dump(map_out, open(f"{BASE}/data/emapunil_f1_pdb_map.json", "w"), indent=1)
