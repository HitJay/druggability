#!/usr/bin/env python3
"""
GPR81 follow-up deliverable 1: overall ranking scorecard of all 45 compounds
(39 Davidsson 2020 paper compounds + 5 lead/tool compounds + lactate).

Methodology (documented, auditable):
- PRIMARY RANK = reported experimental hGPR81 EC50 (ascending; lower = more potent).
  Sources: paper_structures_recovered.json (paper-reported EC50 in uM, vision+MS+ChEMBL
  cross-validated in earlier phases) for c01-c39; identity_resolution.json / ChEMBL for
  t01 (23 nM) and t02 (Takeda 2014, ~50 nM). Partial-agonist efficacy (Emax%) is carried
  from the compound index and flags compounds that are potent but not full agonists.
- Docking scores (8Z8A phase-6 2-seed scan for papers; phase-3 5-pose for tools) are
  CONTEXT ONLY: project doctrine is that a Vina score is a local computational ranking
  signal, never an affinity/potency prediction, and global score-EC50 correlation is
  absent (Pearson r=-0.11, p=0.49 at n=39).
- Reference ligands without a comparable potency assay (t03 CHBA, t04 3,5-DHBA,
  t05 3-OBA, lac lactate) are listed in a separate block - ranking them against nM
  agonists would be meaningless.
- Tier (lead-suitability, A/B/C):
    A: EC50 <= 50 nM AND Emax >= 80% (or full/unknown-efficacy potent) AND
       GPR109A fold >= 25 AND GHSR fold >= 50 (where measured)
    B: EC50 <= 100 nM, any A-criterion unmet (liability noted)
    C: EC50 > 100 nM
  Compounds without selectivity data are tiered on potency/efficacy alone and flagged.

Outputs: gpr81_compound_scorecard.csv (flat), gpr81_compound_scorecard.json (full),
         gpr81_ranking_summary.md (human-readable ranking table).
"""
import csv, json, re, os, math

BASE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.normpath(os.path.join(BASE, ".."))
OUT = os.path.join(BASE, "gpr81_compound_scorecard")

# ---------------------------------------------------------------- load sources
def load(name):
    with open(os.path.join(P1, name), encoding="utf-8") as f:
        return json.load(f)

rec = load("paper_structures_recovered.json")
identity = load("identity_resolution.json")
sel = load("safety/davidsson2020_selectivity_transcription.json")
summary = load("phase6_full_series/full_series_summary.json")
region = load("phase6_full_series/full_series_region_consensus_2seed.json")
redock = load("phase3_5_controls/redocking_controls.json")

papers = {e["paper_compound_number"]: e for e in rec["compounds"]}
sel_flat = {}
for tbl, entries in sel.items():
    if not isinstance(entries, dict):
        continue
    for label, v in entries.items():
        m = re.match(r"(\d+)", str(label))
        if not m:
            continue
        cid = int(m.group(1))
        sel_flat[cid] = v

# index CSV for Emax annotation only (units in that CSV are inconsistent - JSON is truth)
idx_rows = {}
with open(os.path.join(P1, "supplementary/compound_index.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        idx_rows[int(r["paper_compound_number"])] = r

# phase-3 tool scores (best per compound x receptor)
t3 = {}
with open(os.path.join(P1, "phase3_docking/docking_results.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cid, recid = r["compound_id"], r["receptor_id"]
        try:
            s = float(r["score_kcal_mol"])
        except ValueError:
            continue
        t3.setdefault(cid, {}).setdefault(recid, 10**9)
        t3[cid][recid] = min(t3[cid][recid], s)

tool_names = {
    "AZ1_GPR81_agonist_2": "t01",
    "GPR81_agonist_1": "t02",
    "CHBA": "t03",
    "3_5_DHBA": "t04",
    "3_OBA": "t05",
}

def best8(compound_key):
    """best 8Z8A score from phase6 summary (papers) or phase3 (tools)"""
    s = summary.get(compound_key, {})
    if "8Z8A" in s:
        return s["8Z8A"]["best"]
    return None

def region8(cid_str):
    c = region["compounds"].get("c" + cid_str.zfill(2), {})
    r = c.get("8Z8A", {})
    return r.get("consensus") if isinstance(r, dict) else r

def region9(cid_str):
    c = region["compounds"].get("c" + cid_str.zfill(2), {})
    r = c.get("9KT9", {})
    return r.get("consensus") if isinstance(r, dict) else r

def emax_from_index(cid):
    s = idx_rows.get(cid, {}).get("EC50_uM", "")
    m = re.search(r"\((\d+)%\)", s)
    return int(m.group(1)) if m else None

# ---------------------------------------------------------------- build rows
rows = []

# ---- paper compounds c01-c39
for cid in range(1, 40):
    e = papers[cid]
    ec50 = e.get("paper_reported_hGPR81_EC50_uM")
    emax = emax_from_index(cid)
    selv = sel_flat.get(cid, {})
    rows.append({
        "entry_id": f"c{cid:02d}",
        "name": f"Davidsson 2020 compound {cid}",
        "series": e["series"],
        "smiles": e["smiles"],
        "chembl_id": e.get("chembl_id") or "",
        "status": e.get("status", ""),
        "ec50_uM": ec50,
        "ec50_nM": ec50 * 1000 if isinstance(ec50, (int, float)) else None,
        "emax_pct": emax,
        "ec50_source": "paper Table (transcribed, phase1-2 recovery)",
        "gpr109a_fold": selv.get("fold_GPR109A"),
        "ghsr_fold": selv.get("fold_GHSR"),
        "lle": selv.get("lle"),
        "sol_uM": selv.get("sol_uM"),
        "dock_8Z8A_best": best8(str(cid)),
        "dock_8Z8A_protocol": "phase6 2-seed x ex16 x 5poses",
        "region_8Z8A": region8(str(cid)),
        "dock_9KT9_best": summary.get(str(cid), {}).get("9KT9", {}).get("best"),
        "region_9KT9": region9(str(cid)),
    })

# ---- lead compounds t01-t05 (phase-3 protocol)
trows = []
for tname, tid in tool_names.items():
    if tname == "AZ1_GPR81_agonist_2":
        ec50 = 0.023; src = "ChEMBL 23.0 nM (= paper c1, authoritative)"
    elif tname == "GPR81_agonist_1":
        ec50 = 0.05; src = "Takeda 2014 (PMID 24486398) ~50 nM (approx.)"
    else:
        ec50 = None; src = "reference acid; no potency assay in scope"
    rows.append({
        "entry_id": tid,
        "name": tname,
        "series": "lead/tool compound",
        "smiles": None,  # filled below
        "chembl_id": "",
        "status": "tool_compound",
        "ec50_uM": ec50,
        "ec50_nM": ec50 * 1000 if ec50 else None,
        "emax_pct": None,
        "ec50_source": src,
        "gpr109a_fold": None,
        "ghsr_fold": None,
        "lle": None,
        "sol_uM": None,
        "dock_8Z8A_best": t3.get(tname, {}).get("8Z8A"),
        "dock_8Z8A_protocol": "phase3 5-pose",
        "region_8Z8A": None,
        "dock_9KT9_best": t3.get(tname, {}).get("9KT9"),
        "region_9KT9": None,
    })

# tool SMILES from tool_compounds.csv
with open(os.path.join(P1, "tool_compounds.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        tid = tool_names.get(r["compound_id"])
        if tid:
            for row in rows:
                if row["entry_id"] == tid:
                    row["smiles"] = r["canonical_smiles"]

# ---- lactate
lac = next((r for r in redock.get("controls", []) if r.get("compound_id") == "lactate"), {})
rows.append({
    "entry_id": "lac",
    "name": "L-lactate (endogenous ligand)",
    "series": "endogenous",
    "smiles": "C[C@H](O)C(=O)O",
    "chembl_id": "",
    "status": "endogenous ligand",
    "ec50_uM": None,
    "ec50_nM": None,
    "emax_pct": None,
    "ec50_source": "endogenous ligand; mM-range physiological agonist (no assay value in scope)",
    "gpr109a_fold": None, "ghsr_fold": None, "lle": None, "sol_uM": None,
    "dock_8Z8A_best": lac.get("redock_score_kcal_mol"),
    "dock_8Z8A_protocol": "redock control, 8Z8A (cognate, 2OP); centroid rec. %.2f A" % lac.get("centroid_distance_A", float("nan")),
    "region_8Z8A": "ORTHO_POCKET (co-crystal)",
    "dock_9KT9_best": None,
    "region_9KT9": None,
})

# ---------------------------------------------------------------- ranking
ranked = [r for r in rows if r["ec50_nM"] is not None]
for r in ranked:
    r["_ec50_nM"] = r["ec50_nM"]
ranked.sort(key=lambda r: r["_ec50_nM"])
for i, r in enumerate(ranked, 1):
    r["potency_rank"] = i

# tier assignment
def tier_of(r):
    ec = r["ec50_nM"]
    if ec is None:
        return None
    g109 = r["gpr109a_fold"]; ghsr = r["ghsr_fold"]
    emax = r["emax_pct"]
    basis = []
    if ec <= 50: basis.append(f"EC50 {ec:g} nM <= 50")
    elif ec <= 100: basis.append(f"EC50 {ec:g} nM <= 100")
    else: basis.append(f"EC50 {ec:g} nM > 100")
    if emax is not None and emax < 80:
        basis.append(f"partial agonist (Emax {emax}%)")
    if g109 is not None:
        basis.append(f"GPR109A {g109:g}x")
    if ghsr is not None:
        basis.append(f"GHSR {ghsr:g}x")
    if g109 is None and ghsr is None:
        basis.append("no selectivity data")
    if ec <= 50 and (emax is None or emax >= 80) and (g109 is None or g109 >= 25) and (ghsr is None or ghsr >= 50):
        t = "A"
    elif ec <= 100:
        t = "B"
    else:
        t = "C"
    return t, "; ".join(basis)

for r in rows:
    t = tier_of(r)
    r["tier"] = t[0] if t else ""
    r["tier_basis"] = t[1] if t else ""

# docking direction note for top-tier papers (structural support)
for r in rows:
    if r["ec50_nM"] is not None and r["dock_8Z8A_best"] is not None:
        r["dock_support"] = "negative score, region %s" % r["region_8Z8A"] if r["dock_8Z8A_best"] < 0 else "positive (clash) score"
    else:
        r["dock_support"] = ""

# ---------------------------------------------------------------- output
cols = ["entry_id", "name", "series", "smiles", "chembl_id", "status",
        "ec50_uM", "ec50_nM", "emax_pct", "ec50_source",
        "gpr109a_fold", "ghsr_fold", "lle", "sol_uM",
        "potency_rank", "tier", "tier_basis",
        "dock_8Z8A_best", "dock_8Z8A_protocol", "region_8Z8A",
        "dock_9KT9_best", "region_9KT9", "dock_support"]

with open(OUT + ".csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)

with open(OUT + ".json", "w", encoding="utf-8") as f:
    json.dump({"method": {
        "primary_rank": "reported experimental hGPR81 EC50 (ascending); docking = context only",
        "tier_rule": "A: EC50<=50nM & Emax>=80% & GPR109A>=25x & GHSR>=50x (where measured); B: EC50<=100nM; C: >100nM",
        "sources": [
            "paper_structures_recovered.json (EC50, SMILES, status)",
            "supplementary/compound_index.csv (Emax annotation only; unit-inconsistent, not used for numbers)",
            "safety/davidsson2020_selectivity_transcription.json (folds, LLE)",
            "phase6_full_series/full_series_summary.json + region consensus (8Z8A/9KT9)",
            "phase3_docking/docking_results.csv (tool compounds)",
            "phase3_5_controls/redocking_controls.json (lactate)",
        ],
        "caveats": [
            "Vina score is not affinity; no cross-series ranking by score",
            "t02 EC50 ~50 nM approximate (Takeda 2014)",
            "t03/t04/t05/lac have no comparable potency assay - listed separately (rank blank)",
            "c3 index shows '>3.7' but recovered JSON (vision+MS validated, consistent with c4=1.4nM analog) records 3.7 nM; JSON value used, flagged",
        ]}, "compounds": rows}, f, indent=1)

# ---------------------------------------------------------------- summary MD
ranked_rows = [r for r in rows if r.get("potency_rank")]
unranked = [r for r in rows if not r.get("potency_rank")]
md = ["# GPR81 compound overall ranking (45 compounds)",
      "",
      "Primary rank = reported experimental hGPR81 EC50. Docking scores are structural context, not affinity.",
      "",
      "## Ranked by EC50 (potent -> weak)",
      "",
      "| Rank | ID | Series | EC50 (nM) | Emax% | GPR109A x | GHSR x | LLE | 8Z8A score | 8Z8A region | 9KT9 score | Tier |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in ranked_rows:
    md.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r["potency_rank"], r["entry_id"], r["series"],
        ("%.3g" % r["ec50_nM"]) if r["ec50_nM"] is not None else "",
        r["emax_pct"] if r["emax_pct"] is not None else "",
        ("%.1f" % r["gpr109a_fold"]) if r["gpr109a_fold"] is not None else "",
        ("%.0f" % r["ghsr_fold"]) if r["ghsr_fold"] is not None else "",
        ("%.1f" % r["lle"]) if r["lle"] is not None else "",
        ("%.2f" % r["dock_8Z8A_best"]) if r["dock_8Z8A_best"] is not None else "",
        r["region_8Z8A"] or "", 
        ("%.2f" % r["dock_9KT9_best"]) if r["dock_9KT9_best"] is not None else "",
        r["tier"]))
md += ["", "## Reference ligands (no comparable potency assay; rank n/a)", "",
       "| ID | Name | 8Z8A score | protocol |", "|---|---|---|---|"]
for r in unranked:
    md.append("| %s | %s | %s | %s |" % (r["entry_id"], r["name"],
              ("%.2f" % r["dock_8Z8A_best"]) if r["dock_8Z8A_best"] is not None else "",
              r["dock_8Z8A_protocol"]))
md += ["", "## Tier rule", "",
       "- A: EC50 <= 50 nM AND Emax >= 80% (or full) AND GPR109A >= 25x AND GHSR >= 50x (where measured)",
       "- B: EC50 <= 100 nM with any A-criterion unmet (liability noted)",
       "- C: EC50 > 100 nM",
       "- Compounds lacking selectivity data are tiered on potency/efficacy alone and flagged."]
with open(os.path.join(BASE, "gpr81_ranking_summary.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print("rows:", len(rows), "| ranked:", len(ranked), "| unranked:", len(unranked))
for r in ranked_rows[:12]:
    print(r["potency_rank"], r["entry_id"], r["series"], "EC50_nM=", r["ec50_nM"], "Emax=", r["emax_pct"], "tier=", r["tier"], r["region_8Z8A"])
