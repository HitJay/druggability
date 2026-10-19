"""ws6 P7: build the novel-pocket round tier CSV from P2-P6 artifacts.

Row universe: all 30 NOVEL_v2 pockets (scan tier), enriched with hit-tier and
MD results for the shortlist. Layer vocabulary (capped, mirrors the 2026-10-19
emapunil/FGIN campaigns):
  computed-md      — docking gate + 3-seed confirmation + 250 ps MD stable
  computed-dock    — docking gate only (scan or hit tier, no MD)
  computed-negative— docked but not engaged / MD-unstable
Every row: novelty evidence (disjoint from co-crystal pocket, cross-structure
recurrence, lipid-adjacency) and the literature-inventory pointer.
"""
import csv, json
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
DOCK = BASE / "output/docking"

scan = [json.loads(l) for l in open(DOCK / "novelq_p5_emapunil_novel_pockets.jsonl")]
v2j = json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))
v2 = v2j["novel_v2"]
v2_by_tag = {f"{r['pdb']}_p{r['pocket_id']}": r for r in v2j["all_rows"]}
hit = json.load(open(DOCK / "novelq_p5c_hittier.json"))
ctrl = json.load(open(DOCK / "novelq_p5_controls.json"))
cross = json.load(open(BASE / "data/novelq_p4b_novelty_crosscheck.json"))
cross_by_tag = {f"{r['pdb']}_p{r['pocket_id']}": r for r in cross}
lit = json.load(open(BASE / "data/novelq_p3_literature_pockets.json"))

def md_for(tag):
    p = DOCK / f"novelq_p6_{tag}.json"
    if not p.exists():
        return {}
    return json.load(open(p))

rows = []
for s in scan:
    if "error" in s:
        rows.append({"pocket_tag": s["tag"], "gene": s.get("gene", ""), "structure": s["pdb"],
                     "pocket_id": s["pocket_id"], "layer": "error", "assessment": s["error"]})
        continue
    tag = s["tag"]
    v = v2_by_tag[tag]
    verdict4c = v.get("verdict", "NOVEL_v2")
    cx = cross_by_tag[tag]
    h = hit.get(tag, {})
    md = md_for(tag)
    lipid = [x for x in cx["het_within_6A"]] if cx.get("het_within_6A") else []
    demoted = verdict4c != "NOVEL_v2"
    if md and "error" not in md:
        layer = "computed-md" if md["verdict"] == "md-stable" else "computed-negative"
        top_res = next(iter(md.get("top_contacts", {})), "-")
        md_txt = (f"MD 250 ps: drift {md['md_drift_A']} A -> {md['verdict']}; "
                  f"sumIE {md['sum_IE_kJmol']} (kcal-equiv, raw); top contact {top_res}")
    elif h:
        layer = "computed-dock"
        md_txt = "MD not run"
    else:
        layer = "computed-negative" if s["verdict_scan"] == "not-engaged" else "computed-dock"
        md_txt = "MD not run"
    if demoted:
        layer = "computed-negative"
        md_txt = f"demoted after P4c re-gate ({verdict4c}: {round(v.get('adjacent_to_known_frac',0)*100)}% residue overlap with the known orthosteric pocket); docking/MD data retained for reference"
    seeds = h.get("seed_scores")
    seeds_txt = " / ".join(f"{s0[0]:.2f}" for s0 in seeds) if seeds else ""
    conf = "yes" if h.get("confirmed") else ""
    novelty = []
    if cx.get("is_interface"):
        novelty.append("interface pocket (oligomer-state dependent)")
    if lipid:
        novelty.append("lipid-adjacent: " + ", ".join(lipid[:2]))
    if v["gene"] == "TMEM97":
        novelty.append("recurs across 7M93/9ZIR (see report)")
    known_desc = lit.get(v["gene"].split("/")[0], {}).get("hitCount", 0)
    rows.append({
        "pocket_tag": tag,
        "target": v["label"], "gene": v["gene"], "structure": s["pdb"],
        "pocket_id": s["pocket_id"],
        "fpocket_ds": v["ds"], "volume_A3": round(v["volume"]),
        "novelty_basis": ("disjoint from co-crystal (reported) pocket; not in lit inventory "
                          f"({known_desc} PMIDs screened); " + "; ".join(novelty) if novelty else
                          f"disjoint from co-crystal (reported) pocket; not in lit inventory ({known_desc} PMIDs screened)"),
        "is_interface": cx.get("is_interface", False),
        "emapunil_scan_best": s["best"], "scan_verdict": s["verdict_scan"],
        "hittier_3seeds": seeds_txt, "hittier_confirmed": conf,
        "pose1_offset_A": h.get("pose1_offset_A", s.get("pose1_offset_A")),
        "md_drift_A": md.get("md_drift_A", ""), "md_sumIE_kJmol": md.get("sum_IE_kJmol", ""),
        "md_top_contact": next(iter(md.get("top_contacts", {})), ""),
        "layer": layer,
        "assessment": (f"{s['verdict_scan']} at scan tier; " +
                       (f"confirmed 3-seed {seeds_txt}; " if seeds else "") + md_txt),
    })

cols = ["pocket_tag", "target", "gene", "structure", "pocket_id", "fpocket_ds", "volume_A3",
        "novelty_basis", "is_interface", "emapunil_scan_best", "scan_verdict",
        "hittier_3seeds", "hittier_confirmed", "pose1_offset_A", "md_drift_A",
        "md_sumIE_kJmol", "md_top_contact", "layer", "assessment"]
with open(BASE / "output/novel_pockets_tiered_targets_v1.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"wrote {len(rows)} rows -> output/novel_pockets_tiered_targets_v1.csv")
print("layer counts:", {l: sum(1 for r in rows if r["layer"] == l) for l in {r["layer"] for r in rows}})
