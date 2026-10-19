"""ws6 P4c (v2 novelty gate): fixes the other-protomer false-positive class.

Exclusion/tagging rules, applied AFTER the P4 quality gates:
  KNOWN_SITE_OTHER_PROTOMER : pocket within 3.0 A (centroid) of ANY copy
     (any chain) of the structure's pocket-defining co-crystal ligand
     -> same physical site as the literature pocket, on a different protomer.
  LIPID_OCCUPIED            : nearest other HETATM (non-water/ion/glyco)
     heavy atom < 3.0 A -> the cavity is occupied by a bound lipid/cofactor
     (the ligand codes: OLC/OLA/OLB/MPG/CHS/YT1 etc. are TAGGED, not excluded,
     when they are not the pocket-defining ligand; a pocket whose defining
     ligand sits inside is excluded by the rule above).
  INTERFACE                 : pocket spans >1 protein chain (dimer/oligomer
     state dependent) — kept but flagged.
Survivors = 'novel_v2', the shortlist for emapunil docking.
"""
import json, math
from collections import defaultdict
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
NP = BASE / "output/novel_pockets"
cand = json.load(open(BASE / "data/novelq_p4_novel_candidates.json"))
raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))

SKIP = {"HOH", "NA", "CL", "MG", "ZN", "MN", "CA", "K", "CD", "SO4", "PO4", "ACT", "BCT", "NH4"}
IONLIKE = {"NA", "CL", "MG", "ZN", "MN", "CA", "K", "CD", "SO4", "PO4", "ACT", "BCT", "NH4"}
res_by_pid = {}
for pdb, d in raw.items():
    for p in d.get("pockets", []):
        res_by_pid[(pdb, p["pocket_id"])] = set(map(tuple, p["residues"]))

def het_atoms(pdb_id):
    """[(resname, chain, [(x,y,z)...])] non-water HETATM heavy atoms."""
    groups = defaultdict(list)
    for l in open(NP / f"{pdb_id}.pdb"):
        if l.startswith("HETATM"):
            res, ch = l[17:20].strip(), l[21].strip()
            if res == "HOH":
                continue
            groups[(res, ch)].append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
    return groups

def pocket_atoms(pdb_id, pres):
    patoms = []
    for l in open(NP / f"{pdb}_prot.pdb"):
        if l.startswith("ATOM"):
            if (l[21].strip(), l[22:26].strip()) in pres:
                patoms.append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
    return patoms

out_rows = []
for r in cand["novel_candidates"]:
    pdb, pid = r["pdb"], r["pocket_id"]
    d = raw[pdb]
    pres = res_by_pid[(pdb, pid)]
    chains = sorted({c for c, _ in pres})
    patoms = pocket_atoms(pdb, pres)
    pcen = (sum(p[0] for p in patoms) / len(patoms),
            sum(p[1] for p in patoms) / len(patoms),
            sum(p[2] for p in patoms) / len(patoms))
    # 1) any copy of the pocket-defining ligand
    deflig, defchain = d["pocket_ligand"], d["pocket_chain"]
    verdict, near_def = None, None
    het = het_atoms(pdb)
    for (res, ch), pts in het.items():
        if res != deflig:
            continue
        dmin = min(math.dist(p, q) for p in pts for q in patoms[:400])
        ccen = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))
        dc = math.dist(ccen, pcen)
        if near_def is None or dmin < near_def[0]:
            near_def = (dmin, ch, dc)
    if near_def and near_def[2] < 3.0:
        verdict = "KNOWN_SITE_OTHER_PROTOMER"
    elif r.get("adjacent_to_known_frac", 0) >= 0.30:
        verdict = "ADJACENT_TO_KNOWN"
    # 2) other HETATM occupancy
    lip = None
    if verdict is None:
        for (res, ch), pts in het.items():
            if res == deflig or res in IONLIKE or res in {"NAG", "BMA", "MAN", "FUC"}:
                continue
            dmin = min(math.dist(p, q) for p in pts for q in patoms[:400])
            if dmin < 3.0:
                lip = f"{res}/{ch}@{dmin:.1f}A"
                break
    out_rows.append({**r, "chains": chains, "is_interface": len(chains) > 1,
                     "pocket_center": [round(v, 1) for v in pcen],
                     "verdict": verdict or ("LIPID_OCCUPIED:" + lip if lip else "NOVEL_v2"),
                     "near_deflig": (f"{near_def[0]:.1f}A/copy{near_def[1]} cen {near_def[2]:.1f}A"
                                     if near_def else None)})
    tag = verdict or ("LIPID:" + lip if lip else "NOVEL_v2")
    ifc = "IF" if len(chains) > 1 else "  "
    print(f"{pdb} p{pid:<3d} ds={r['ds']:.2f} vol={r['volume']:6.0f} {ifc} {tag}")

n_novel = sum(1 for r in out_rows if r["verdict"] == "NOVEL_v2")
print(f"\nNOVEL_v2 survivors: {n_novel}/{len(out_rows)}")
json.dump({"novel_v2": [r for r in out_rows if r["verdict"] == "NOVEL_v2"],
           "all_rows": out_rows},
          open(BASE / "data/novelq_p4c_novel_v2.json", "w"), indent=1)
print("saved data/novelq_p4c_novel_v2.json")
