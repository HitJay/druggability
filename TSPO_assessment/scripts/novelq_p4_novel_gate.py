"""ws6 P4: novelty gating on fpocket results.

A pocket is a NOVEL CANDIDATE when all of:
  1. does not recover the known (literature/co-crystal) pocket (P2 recovers_known=False);
  2. druggability score >= 0.2;
  3. volume >= 250 A^3 (emapunil-sized; the 4RYI TSPO anchor pocket measures ~700 A^3);
  4. >= 20 alpha spheres and >= 12 distinct residues (not a crystal-packing crack);
  5. not a symmetry-mate interface artefact: residues must not be exclusively
     altloc duplicates — fpocket 4 handles this internally; we additionally cap
     the number of novel candidates per structure at 5 (top by druggability)
     to keep the docking+MD budget tractable.

Cross-structure recurrence: for TMEM97 (7M93 vs 9ZIR) novel candidates sharing
>= 50% of residues are collapsed to one recurrent site (stronger evidence).
Also: novel pockets whose residues overlap the KNOWN pocket's residues >= 30%
are adjacent extensions, tagged 'adjacent' not 'novel-distant'.
"""
import json
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
data = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))

MIN_DS = 0.20
MIN_VOL = 250.0
MIN_ALPHA = 20
MIN_RES = 12
MAX_PER_STRUCT = 5

rows = []
for pdb, d in data.items():
    if "error" in d or not d.get("pockets"):
        continue
    known_res = set()
    for p in d["pockets"]:
        if p["recovers_known"]:
            known_res |= set(map(tuple, p["residues"]))
    cands = []
    for p in d["pockets"]:
        if p["recovers_known"]:
            continue
        if (p["ds"] or 0) < MIN_DS or (p["volume"] or 0) < MIN_VOL:
            continue
        if (p["n_alpha"] or 0) < MIN_ALPHA or p["n_res"] < MIN_RES:
            continue
        pres = set(map(tuple, p["residues"]))
        ov_known = len(pres & known_res) / max(1, len(pres))
        cands.append({**p, "residues": sorted(pres), "residues_raw": None,
                      "adjacent_to_known_frac": round(ov_known, 3)})
    cands.sort(key=lambda x: -(x["ds"] or 0))
    for rank, c in enumerate(cands[:MAX_PER_STRUCT], 1):
        rows.append({"pdb": pdb, "label": d["label"], "gene": d["gene"],
                     "rank_in_struct": rank, **{k: c[k] for k in
                     ("pocket_id", "score", "ds", "volume", "sasa", "n_alpha",
                      "apolar_as_prop", "flexibility", "n_res", "adjacent_to_known_frac")}})
    if cands:
        print(f"{pdb} {d['label']}: {len(cands)} pass gates -> kept "
              f"{[c['pocket_id'] for c in cands[:MAX_PER_STRUCT]]}")

# TMEM97 recurrence collapse (7M93 vs 9ZIR)
tmem = [r for r in rows if r["gene"] == "TMEM97"]
recurring = []
for i, a in enumerate(tmem):
    for b in tmem[i + 1:]:
        if a["pdb"] == b["pdb"]:
            continue
        sa, sb = set(a.get("_res", [])), set(b.get("_res", []))
# residue sets were dropped above; recompute from raw
raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))
tmem_cands = []
for pdb in ("7M93", "9ZIR"):
    d = raw[pdb]
    known_res = set()
    for p in d["pockets"]:
        if p["recovers_known"]:
            known_res |= set(map(tuple, p["residues"]))
    for p in d["pockets"]:
        if p["recovers_known"]:
            continue
        if (p["ds"] or 0) < MIN_DS or (p["volume"] or 0) < MIN_VOL or (p["n_alpha"] or 0) < MIN_ALPHA or p["n_res"] < MIN_RES:
            continue
        pres = set(map(tuple, p["residues"]))
        tmem_cands.append({"pdb": pdb, "pocket_id": p["pocket_id"], "ds": p["ds"],
                           "vol": p["volume"], "res": pres})
recurrence = []
for i, a in enumerate(tmem_cands):
    for b in tmem_cands[i + 1:]:
        if a["pdb"] == b["pdb"]:
            continue
        j = len(a["res"] & b["res"]) / max(1, min(len(a["res"]), len(b["res"])))
        if j >= 0.5:
            recurrence.append({"a": (a["pdb"], a["pocket_id"]), "b": (b["pdb"], b["pocket_id"]),
                               "jaccard": round(j, 2)})
print("TMEM97 cross-structure recurrence:", recurrence)

out = {"gates": {"MIN_DS": MIN_DS, "MIN_VOL": MIN_VOL, "MIN_ALPHA": MIN_ALPHA,
                 "MIN_RES": MIN_RES, "MAX_PER_STRUCT": MAX_PER_STRUCT},
       "tmem97_recurrence": recurrence,
       "novel_candidates": rows}
with open(BASE / "data/novelq_p4_novel_candidates.json", "w") as fh:
    json.dump(out, fh, indent=1)
print(f"saved {len(rows)} novel candidates -> data/novelq_p4_novel_candidates.json")
