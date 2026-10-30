#!/usr/bin/env python3
"""BQ-1 99 Unflagged Cardiometabolic Leads — 4-Criteria Automated Triage Pipeline (ZHCO Request).

Evaluates all 99 unflagged Data S6 one-target cardiometabolic PPI leads across Zheng Cao's 4 criteria:
  Criterion 1 (Genetics): Genetic analysis for both the known target and the unknown partner suggests
                          the same or relevant cardiometabolic disease indications (Obesity, T2D, CKD,
                          MASH, CVD/HF), in either the same or opposite direction.
  Criterion 2 (Signaling Pathway): Known target and unknown partner belong to the same signaling pathway
                          (Reactome / Open Targets pathways, STRING database `dscore`, or shared UniProt
                          biological process / GO signaling terms).
  Criterion 3 (Perturbation Regulation): Literature and omics databases show that perturbation (knockout,
                          knockdown, overexpression, agonist/antagonist, cleavage) of one protein causes
                          a change in the protein or RNA level of the other protein.
  Criterion 4 (Disease Co-progression): Literature and omics databases (or STRING coexpression `ascore`
                          + Open Targets RNA expression / disease signatures) show that protein or RNA
                          levels of both genes change simultaneously with disease progression.
"""
import concurrent.futures
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path("/das/user/QYJI/druggability/reports/bq1_99_triage")
OUT_DIR.mkdir(parents=True, exist_ok=True)
LEADS_JSON = OUT_DIR / "leads_99_base.json"

leads = json.loads(LEADS_JSON.read_text())
print(f"Loaded {len(leads)} unflagged Data S6 cardiometabolic leads.")

# 1. Unique proteins (UniProt + Gene symbol)
unique_proteins = {}
for x in leads:
    unique_proteins[x["target_uniprot"]] = x["target_gene"]
    unique_proteins[x["partner_uniprot"]] = x["partner_gene"]
print(f"Unique proteins across 99 pairs: {len(unique_proteins)}")

# Cardiometabolic indication keyword buckets for matching Open Targets diseases
CM_BUCKETS = {
    "Obesity": [
        "obesity", "body mass index", "bmi", "body weight", "waist", "adipose", "fat mass",
        "overweight", "hyperphagia", "anorexia", "metabolic syndrome", "leptin", "appetite"
    ],
    "T2D": [
        "diabetes", "type 2 diabetes", "t2d", "glucose", "insulin", "hba1c", "glycemic",
        "hyperglycemia", "hypoglycemia", "beta cell", "diabetic"
    ],
    "CKD": [
        "kidney", "renal", "nephropathy", "glomerular", "egfr", "albuminuria", "proteinuria",
        "chronic kidney", "ckd", "nephritis", "urat", "creatinine", "calcium", "hypercalcemia", "hypocalcemia"
    ],
    "MASH": [
        "liver", "hepatic", "mash", "nash", "nafld", "steatosis", "steatohepatitis", "cirrhosis",
        "fibrosis", "transaminase", "alanine aminotransferase", "aspartate aminotransferase",
        "cholesterol", "triglyceride", "lipid", "dyslipidemia", "hyperlipidemia"
    ],
    "CVD": [
        "cardiovascular", "coronary", "myocardial", "heart failure", "cardiomyopathy", "hypertension",
        "blood pressure", "atherosclerosis", "stroke", "thrombosis", "arrhythmia", "atrial fibrillation",
        "vascular", "ischemic", "angina", "ventricul", "cardiac", "aortic"
    ],
}


def classify_cm_indications(text_str):
    t = (text_str or "").lower()
    matched = set()
    for ind, kw_list in CM_BUCKETS.items():
        if any(k in t for k in kw_list):
            matched.add(ind)
    return sorted(matched)


# ==============================================================================
# STEP 1: Query Open Targets v4 GraphQL for all unique proteins
# ==============================================================================
OT_CACHE = OUT_DIR / "opentargets_cache.json"
if OT_CACHE.exists():
    ot_data = json.loads(OT_CACHE.read_text())
    print(f"Loaded Open Targets cache ({len(ot_data)} proteins)")
else:
    ot_data = {}

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
OT_QUERY = """
query($q: String!) {
  search(queryString: $q, entityNames: ["target"], page: {index: 0, size: 3}) {
    hits {
      id
      name
      object {
        ... on Target {
          id
          approvedSymbol
          approvedName
          proteinIds { id source }
          pathways {
            pathwayId
            pathway
            topLevelTerm
          }
          associatedDiseases(page: {index: 0, size: 100}) {
            rows {
              disease { id name }
              score
              datatypeScores { id score }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_ot_protein(uniprot_id, gene_sym):
    q_term = gene_sym if gene_sym and gene_sym != "none" else uniprot_id
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                OT_URL,
                data=json.dumps({"query": OT_QUERY, "variables": {"q": q_term}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
            hits = data.get("data", {}).get("search", {}).get("hits", [])
            chosen = None
            for h in hits:
                obj = h.get("object") or {}
                pids = [p.get("id") for p in (obj.get("proteinIds") or [])]
                if uniprot_id in pids or (gene_sym and obj.get("approvedSymbol", "").upper() == gene_sym.upper()):
                    chosen = obj
                    break
            if not chosen and hits:
                chosen = hits[0].get("object")
            if not chosen:
                return uniprot_id, {"symbol": gene_sym, "pathways": [], "diseases": []}

            pathways = [
                {"id": p.get("pathwayId"), "name": p.get("pathway"), "top": p.get("topLevelTerm")}
                for p in (chosen.get("pathways") or [])
            ]
            diseases = []
            for r in (chosen.get("associatedDiseases", {}).get("rows") or []):
                d_name = r.get("disease", {}).get("name", "")
                dts = {d["id"]: round(d["score"], 4) for d in (r.get("datatypeScores") or [])}
                cm_inds = classify_cm_indications(d_name)
                diseases.append({
                    "id": r.get("disease", {}).get("id"),
                    "name": d_name,
                    "score": round(r.get("score", 0.0), 4),
                    "dts": dts,
                    "cm_indications": cm_inds,
                })
            return uniprot_id, {
                "ensembl_id": chosen.get("id"),
                "symbol": chosen.get("approvedSymbol", gene_sym),
                "pathways": pathways,
                "diseases": diseases,
            }
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return uniprot_id, {"symbol": gene_sym, "pathways": [], "diseases": []}


missing_ot = [(u, g) for u, g in unique_proteins.items() if u not in ot_data]
if missing_ot:
    print(f"Fetching Open Targets data for {len(missing_ot)} proteins...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_ot_protein, u, g) for u, g in missing_ot]
        for fut in concurrent.futures.as_completed(futs):
            u, info = fut.result()
            ot_data[u] = info
    OT_CACHE.write_text(json.dumps(ot_data, indent=2))
    print("Saved Open Targets cache.")


# ==============================================================================
# STEP 2: Query UniProt JSON for exact GO Biological Process, Reactome & Function text
# ==============================================================================
UP_CACHE = OUT_DIR / "uniprot_cache.json"
if UP_CACHE.exists():
    up_data = json.loads(UP_CACHE.read_text())
else:
    up_data = {}


def fetch_uniprot(u):
    url = f"https://rest.uniprot.org/uniprotkb/{u}.json"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                d = json.loads(r.read())
            reactome = []
            go_bp = []
            go_cc = []
            for x in d.get("uniProtKBCrossReferences", []):
                db = x.get("database")
                if db == "Reactome":
                    p_name = next((p["value"] for p in x.get("properties", []) if p["key"] == "PathwayName"), "")
                    reactome.append({"id": x.get("id"), "name": p_name})
                elif db == "GO":
                    term = next((p["value"] for p in x.get("properties", []) if p["key"] == "GoTerm"), "")
                    if term.startswith("P:"):
                        go_bp.append({"id": x.get("id"), "name": term[2:]})
                    elif term.startswith("C:"):
                        go_cc.append({"id": x.get("id"), "name": term[2:]})
            diseases = []
            func_txt = ""
            sub_txt = ""
            for c in d.get("comments", []):
                ct = c.get("commentType")
                if ct == "DISEASE":
                    dis = c.get("disease", {})
                    if dis.get("diseaseId"):
                        diseases.append(dis.get("diseaseId") + ": " + dis.get("description", ""))
                elif ct == "FUNCTION":
                    txts = [t.get("value", "") for t in c.get("texts", [])]
                    func_txt += " ".join(txts)
                elif ct == "SUBUNIT":
                    txts = [t.get("value", "") for t in c.get("texts", [])]
                    sub_txt += " ".join(txts)
            return u, {
                "reactome": reactome,
                "go_bp": go_bp,
                "go_cc": go_cc,
                "diseases": diseases,
                "function_text": func_txt[:600],
                "subunit_text": sub_txt[:600],
            }
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    return u, {"reactome": [], "go_bp": [], "go_cc": [], "diseases": [], "function_text": "", "subunit_text": ""}


missing_up = [u for u in unique_proteins if u not in up_data]
if missing_up:
    print(f"Fetching UniProt JSON for {len(missing_up)} proteins...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for u, info in ex.map(fetch_uniprot, missing_up):
            up_data[u] = info
    UP_CACHE.write_text(json.dumps(up_data, indent=2))
    print("Saved UniProt cache.")


# ==============================================================================
# STEP 3: Query STRING API for all 99 pairs (coexpression `ascore`, pathway `dscore`, exp `escore`, text `tscore`)
# ==============================================================================
STRING_CACHE = OUT_DIR / "string_cache.json"
if STRING_CACHE.exists():
    string_edges = json.loads(STRING_CACHE.read_text())
else:
    all_syms = sorted({g for g in unique_proteins.values() if g and g != "none"})
    url = "https://string-db.org/api/json/network?identifiers=" + "%0d".join(all_syms) + "&species=9606&required_score=100"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        net = json.loads(r.read())
    string_edges = {}
    for e in net:
        ga, gb = e["preferredName_A"].upper(), e["preferredName_B"].upper()
        key = "__".join(sorted([ga, gb]))
        string_edges[key] = {
            "score": e.get("score", 0),
            "ascore_coexpr": e.get("ascore", 0),
            "escore_exp": e.get("escore", 0),
            "dscore_pathway": e.get("dscore", 0),
            "tscore_text": e.get("tscore", 0),
        }
    STRING_CACHE.write_text(json.dumps(string_edges, indent=2))
    print(f"Saved STRING cache ({len(string_edges)} edges).")


# ==============================================================================
# STEP 4: Query Europe PMC for all 99 pairs (Co-mentions, Perturbation C3, Disease Progression C4)
# ==============================================================================
EPMC_CACHE = OUT_DIR / "epmc_cache.json"
if EPMC_CACHE.exists():
    epmc_data = json.loads(EPMC_CACHE.read_text())
else:
    epmc_data = {}

PERTURB_PAT = re.compile(
    r"\b(knockout|knock-out|knockdown|siRNA|shRNA|CRISPR|deplet\w+|overexpress\w+|"
    r"induc\w+|upregulat\w+|downregulat\w+|suppress\w+|inhibit\w+|activat\w+|"
    r"cleav\w+|degrad\w+|stabiliz\w+|phosphorylat\w+|attenuat\w+|deficien\w+|"
    r"mRNA level\w*|protein level\w*|expression of)\b",
    re.I,
)
PROG_PAT = re.compile(
    r"\b(disease progression|stage\w*|severity|fibrosis stage|heart failure|steatohepatitis|"
    r"diabetic nephropathy|atherosclero\w+|obesity|upregulated in patients|downregulated in patients|"
    r"elevated in patients|correlated with|prognos\w+|biomarker|transcriptom\w+|proteom\w+|"
    r"differential\w* express\w+|co-express\w+|simultaneously)\b",
    re.I,
)


def fetch_epmc_pair(lead):
    g1, g2 = lead["target_gene"], lead["partner_gene"]
    pair_key = f"{g1}__{g2}"
    if not g2 or g2 == "none":
        return pair_key, {"hit_count": 0, "c3_hits": [], "c4_hits": [], "top_papers": []}
    q = f'("{g1}" AND "{g2}")'
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
        + urllib.parse.quote(q)
        + "&resultType=core&pageSize=25&format=json"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                res = json.loads(r.read())
            hit_count = res.get("hitCount", 0)
            results = res.get("resultList", {}).get("result", [])
            c3_hits = []
            c4_hits = []
            top_papers = []
            g1_re = re.compile(r"\b" + re.escape(g1) + r"\b", re.I)
            g2_re = re.compile(r"\b" + re.escape(g2) + r"\b", re.I)
            for item in results:
                pmid = item.get("pmid") or item.get("id", "")
                title = item.get("title", "")
                abs_txt = item.get("abstractText", "") or ""
                journal = item.get("journalTitle", "")
                pub_year = item.get("pubYear", "")
                full = f"{title} {abs_txt}"
                both_in_abs = bool(g1_re.search(full) and g2_re.search(full))
                top_papers.append({
                    "pmid": pmid,
                    "year": pub_year,
                    "journal": journal,
                    "title": title[:160],
                    "both_in_title_or_abs": both_in_abs,
                })
                if both_in_abs:
                    sentences = re.split(r"(?<=[.!?])\s+", full)
                    for s in sentences:
                        has_both = bool(g1_re.search(s) and g2_re.search(s))
                        if has_both and PERTURB_PAT.search(s):
                            c3_hits.append({"pmid": pmid, "year": pub_year, "sentence": s[:280]})
                        if has_both and PROG_PAT.search(s):
                            c4_hits.append({"pmid": pmid, "year": pub_year, "sentence": s[:280]})
                    if not c3_hits and PERTURB_PAT.search(full):
                        c3_hits.append({"pmid": pmid, "year": pub_year, "sentence": f"[Abstract] {title[:180]}"})
                    if not c4_hits and PROG_PAT.search(full):
                        c4_hits.append({"pmid": pmid, "year": pub_year, "sentence": f"[Abstract] {title[:180]}"})
            return pair_key, {
                "hit_count": hit_count,
                "both_in_abs_count": sum(1 for p in top_papers if p["both_in_title_or_abs"]),
                "c3_hits": c3_hits[:5],
                "c4_hits": c4_hits[:5],
                "top_papers": top_papers[:5],
            }
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    return pair_key, {"hit_count": 0, "both_in_abs_count": 0, "c3_hits": [], "c4_hits": [], "top_papers": []}


missing_epmc = [x for x in leads if f"{x['target_gene']}__{x['partner_gene']}" not in epmc_data]
if missing_epmc:
    print(f"Querying Europe PMC for {len(missing_epmc)} pairs...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for pk, info in ex.map(fetch_epmc_pair, missing_epmc):
            epmc_data[pk] = info
    EPMC_CACHE.write_text(json.dumps(epmc_data, indent=2))
    print("Saved Europe PMC cache.")

print("All external evidence caches ready.")
