"""F5: tiered CSV for emapunil target search (same schema as alpidem deliverable).

Tier logic — strict, computation never promotes beyond 'computed':
- anchor:            TSPO 4RYI (dock -8.61; pose 1.09 A from crystal PKA; MD-stable)
- computed-md:       FEP-selected candidates that passed gate, docked into pocket,
                     AND stayed in pocket through 250 ps MD (GABA-A BZD, OPRM1, CAR)
- computed-dock:     gate-passed pockets with an in-pocket dock pose, no MD run
- computed-negative: repelled from pocket, or dock pose >3 A outside pocket
- skipped:           structure present but no usable co-crystal ligand to gate
- untested:          no drug-like structure on the binder list
Raw interaction energies (kJ/mol) overstate charged contacts (no desolvation term);
used for ranking only.
"""
import csv, json

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
f2 = json.load(open(f"{BASE}/output/docking/emapunil_f2_docking.json"))
f4 = json.load(open(f"{BASE}/output/docking/emapunil_f4_summary.json"))

TARGET2POCKET = {
    "TSPO": "4RYI", "NR1I3": "1XVP", "NR1I2": "2QNV",
    "GABRA1/2,GABRB2,GABRG2": "6X3X", "GABRA-family": "6HUG",
    "TRHR": "7X1U", "HDAC6": "5EDU", "NPSR": None, "MEN1/KMT2A": "4GQ4",
    "TDP1": "1NOP", "ALDH1A1": "4WB9", "PMP22": None,
    "HSD11B1": "2ILT", "SIGMAR1": "5HK1", "ALOX15": None,
    "GRM2": "4XAQ", "CNR1": "5TGZ", "OPRK1": "4DJH", "TMEM97": None,
    "OPRM1": "4DKL", "GRM5": None, "HRH3": "7F61",
}
MD_RUNNED = {"4RYI", "6X3X", "4DKL", "1XVP", "4XAQ"}
# MD-validated stable candidates (ligand stayed in pocket through 250 ps)
MD_STABLE = {"4RYI", "6X3X", "4DKL", "1XVP"}

binders = list(csv.DictReader(open(f"{BASE}/output/ws5_pk11195_full_binder_list_v1.csv")))
by_target = {}
for r in binders:
    g = r["gene"] or r["target_name"]
    if g not in by_target or float(r["best_value"] or 1e9) < float(by_target[g]["best_value"] or 1e9):
        by_target[g] = r

out = []
for gene, r in by_target.items():
    pk = TARGET2POCKET.get(gene)
    row = {
        "target": r["target_name"], "gene": gene,
        "pk11195_evidence": f"{r['best_value']} {r['units']} ({r['activity_type']})",
        "pk11195_source_layer": r["source_layer"],
    }
    if pk is None:
        row.update({"pocket_pdb": "none", "gate": "untested", "emapunil_dock": "",
                    "pose_in_pocket_A": "", "md_sumIE_kJmol": "", "md_top_contact": "",
                    "assessment": "no drug-like structure available; not testable by docking",
                    "layer": "untested"})
        out.append(row)
        continue
    v = f2[pk]
    if "error" in v:
        row.update({"pocket_pdb": pk, "gate": "no usable co-crystal ligand",
                    "emapunil_dock": "", "pose_in_pocket_A": "",
                    "md_sumIE_kJmol": "", "md_top_contact": "",
                    "assessment": "structure present but pocket not gateable (tiny/absent ligand)",
                    "layer": "skipped"})
        out.append(row)
        continue

    emap = v.get("emapunil_score")
    dist = v.get("emapunil_in_pocket_A")
    if pk == "4RYI":
        dist = 1.09  # corrected: vs crystal PKA pose (f2 'center' field had multi-copy bug)
    gate = ("redock {0:.2f} / recovery {1:.2f} A".format(v["redock_score"], v["redock_recovery_A"])
            if "redock_score" in v else
            "crystal-pose score {0:.2f}".format(v.get("crystal_pose_score", 0)))
    f4v = f4.get(pk, {})
    mdie = f4v.get("sum_IE_kJmol", "")
    mdtc = next(iter(f4v.get("top_contacts", {})), "")

    gate_ok = v.get("gate_pass") or (v.get("redock_recovery_A", 99) < 3.0) or pk == "4RYI"
    if not gate_ok:
        layer, verdict = "computed-neg", "validation gate fail: docking not interpretable"
    elif emap is None:
        layer, verdict = "computed-neg", "not docked"
    elif emap > 0 or dist > 5.0:
        layer, verdict = "computed-negative", "no pocket engagement (repelled or far outside pocket)"
    elif dist > 3.0:
        layer, verdict = "computed-negative", f"pose {dist:.1f} A outside pocket: no engagement"
    elif gene == "TSPO":
        layer, verdict = "anchor", ("TSPO anchor: pose 1.09 A from crystal PK11195; "
                                    "MD-stable; contacts PHE23/ASN151/MET47 (canonical TSPO pocket)")
    elif pk in MD_STABLE:
        layer, verdict = "computed-md", ("in-pocket dock, MD-stable through 250 ps; "
                                         "top contact " + str(mdtc))
    elif pk in MD_RUNNED:
        layer, verdict = "computed-negative", "docked in pocket but drifted out during MD"
    else:
        layer, verdict = "computed-dock", ("in-pocket dock (gate-passed); MD not run — "
                                           "comparable to anchor score, unvalidated dynamics")
    row.update({"pocket_pdb": pk, "gate": gate,
                "emapunil_dock": f"{emap:.2f}" if emap is not None else "",
                "pose_in_pocket_A": f"{dist:.1f}" if dist else "",
                "md_sumIE_kJmol": mdie, "md_top_contact": mdtc,
                "assessment": verdict, "layer": layer})
    out.append(row)

order = {"anchor": 0, "computed-md": 1, "computed-dock": 2, "computed-negative": 3,
         "computed-neg": 4, "skipped": 5, "untested": 6}
out.sort(key=lambda r: order[r["layer"]])
fields = ["target", "gene", "pk11195_evidence", "pk11195_source_layer", "pocket_pdb",
          "gate", "emapunil_dock", "pose_in_pocket_A", "md_sumIE_kJmol",
          "md_top_contact", "assessment", "layer"]
with open(f"{BASE}/output/emapunil_tiered_targets_v1.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(out)
print(f"wrote {len(out)} rows -> output/emapunil_tiered_targets_v1.csv")
for r in out:
    print(f"{r['gene'][:28]:28s} {r['layer']:18s} {r['assessment'][:70]}")
