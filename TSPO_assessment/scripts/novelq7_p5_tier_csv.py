"""ws7 P5: combined tier CSV (docking + MD + TI layers per novel pocket, both ligands).

Vocabulary stays capped: anchor / computed-md / computed-dock / computed-negative /
computed-ti / skipped / untested / demoted-adjacent. No 'computed-positive'.
Output: output/novelq7_tiered_targets_v1.csv
"""
import csv, glob, json

BASE = "/das/user/QYJI/druggability/TSPO_assessment"

scan = {json.loads(l)["tag"]: json.loads(l)
        for l in open(f"{BASE}/output/docking/novelq7_p1_fgin_scan.jsonl")}
emap_scan = {json.loads(l)["tag"]: json.loads(l)
             for l in open(f"{BASE}/output/docking/novelq_p5_emapunil_novel_pockets.jsonl")}
hit = json.load(open(f"{BASE}/output/docking/novelq7_p2_fgin_hittier.json"))
emap_hit = json.load(open(f"{BASE}/output/docking/novelq_p5c_hittier.json"))

md7 = {}
for f in glob.glob(f"{BASE}/output/docking/novelq7_p3_*.json"):
    j = json.load(open(f)); md7[j["tag"]] = j
md6 = {}
for f in glob.glob(f"{BASE}/output/docking/novelq_p6_*.json"):
    j = json.load(open(f)); md6[j["tag"]] = j

ti = {}
for f in glob.glob(f"{BASE}/output/fep_a7/scan7_*.json"):
    j = json.load(open(f))
    ti[(j["tag"], j["ligand"])] = {a: v["ddG_kJmol"] for a, v in j.get("anchors", {}).items()}

v2 = json.load(open(f"{BASE}/data/novelq_p4c_novel_v2.json"))
meta = {f"{r['pdb']}_p{r['pocket_id']}": r for r in v2["all_rows"]}

rows = []
all_tags = sorted(set(scan) | set(emap_scan) | set(meta))
for tag in all_tags:
    m = meta.get(tag, {})
    g = scan.get(tag) or emap_scan.get(tag) or {}
    row = {
        "pocket_tag": tag,
        "gene": g.get("gene") or m.get("gene", ""),
        "structure": g.get("pdb") or m.get("pdb", ""),
        "fpocket_ds": g.get("ds") or m.get("ds", ""),
        "volume_A3": g.get("volume") or m.get("volume", ""),
        "is_interface": g.get("is_interface", m.get("is_interface", "")),
        "novelty_verdict": m.get("verdict", ""),
        # --- FGIN layers ---
        "fgin_scan_best": scan.get(tag, {}).get("best", ""),
        "fgin_scan_verdict": scan.get(tag, {}).get("verdict_scan", "not-docked"),
        "fgin_hittier_best3": hit.get(tag, {}).get("best_of_seeds", ""),
        "fgin_hittier_confirmed": "yes" if hit.get(tag, {}).get("confirmed") else ("no" if tag in hit else ""),
        "fgin_md_drift_A": md7.get(tag, {}).get("md_drift_A", ""),
        "fgin_md_verdict": md7.get(tag, {}).get("verdict", ""),
        "fgin_md_top_contact": (list(md7[tag]["top_contacts"])[0] if md7.get(tag, {}).get("top_contacts") else ""),
        "fgin_ti_top_ddG_kJmol": (f"{max(v for v in ti[(tag,'fgin')].values()):.1f}"
                                   if (tag, "fgin") in ti and ti[(tag, "fgin")] else ""),
        "fgin_ti_anchor": (max(ti[(tag, "fgin")], key=ti[(tag, "fgin")].get)
                            if (tag, "fgin") in ti and ti[(tag, "fgin")] else ""),
        # --- emapunil layers (ws6, this round's TI for the 6-pocket cross-set) ---
        "emapunil_scan_best": emap_scan.get(tag, {}).get("best", ""),
        "emapunil_scan_verdict": emap_scan.get(tag, {}).get("verdict_scan", "not-docked"),
        "emapunil_hittier_confirmed": "yes" if emap_hit.get(tag, {}).get("confirmed") else ("no" if tag in emap_hit else ""),
        "emapunil_md_verdict": md6.get(tag, {}).get("verdict", ""),
        "emapunil_ti_top_ddG_kJmol": (f"{max(v for v in ti[(tag,'emapunil')].values()):.1f}"
                                      if (tag, "emapunil") in ti and ti[(tag, "emapunil")] else ""),
        "emapunil_ti_anchor": (max(ti[(tag, "emapunil")], key=ti[(tag, "emapunil")].get)
                               if (tag, "emapunil") in ti and ti[(tag, "emapunil")] else ""),
    }
    # combined layer per ligand: capped vocabulary
    def layer(scan_v, md_v, ti_v):
        if md_v == "md-stable" and ti_v:
            return "computed-ti"
        if md_v == "md-stable":
            return "computed-md"
        if md_v == "md-unstable":
            return "computed-negative"
        if scan_v == "engaged":
            return "computed-dock"
        return "skipped"
    row["fgin_layer"] = layer(row["fgin_scan_verdict"], row["fgin_md_verdict"], row["fgin_ti_top_ddG_kJmol"])
    row["emapunil_layer"] = layer(row["emapunil_scan_verdict"], row["emapunil_md_verdict"], row["emapunil_ti_top_ddG_kJmol"])
    # demoted-adjacent keeps its data with the demotion inline
    if row["novelty_verdict"] == "ADJACENT_TO_KNOWN":
        row["fgin_layer"] += "+demoted-adjacent" if row["fgin_layer"] != "skipped" else "demoted-adjacent"
    rows.append(row)

out = f"{BASE}/output/novelq7_tiered_targets_v1.csv"
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} rows -> {out}")
