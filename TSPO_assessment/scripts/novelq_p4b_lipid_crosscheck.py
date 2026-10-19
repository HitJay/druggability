"""ws6 P4b: novelty cross-check — do novel candidate pockets coincide with
bound lipids/cofactors/ions already present in the PDB entries?
A pocket within 6 A of a non-water HETATM cluster is labelled 'coincides with
<resname>' (likely a lipid/allosteric-lipid site, weaker novelty claim).
Also flags multi-chain pockets (interface pockets, dimer-state dependent).
"""
import json, math
from collections import defaultdict
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
NP = BASE / "output/novel_pockets"
cand = json.load(open(BASE / "data/novelq_p4_novel_candidates.json"))
raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))

SKIP = {"HOH", "NA", "CL", "MG", "ZN", "MN", "CA", "K", "CD", "SO4", "PO4", "ACT", "BCT", "NH4"}
res_by_pid = {}
for pdb, d in raw.items():
    for p in d.get("pockets", []):
        res_by_pid[(pdb, p["pocket_id"])] = set(map(tuple, p["residues"]))

def het_clusters(pdb_id):
    """[(resname, chain, centroid, natoms)] for non-solvent/ion HETATM."""
    groups = defaultdict(list)
    for l in open(NP / f"{pdb_id}.pdb"):
        if l.startswith("HETATM"):
            res, ch = l[17:20].strip(), l[21].strip()
            if res in SKIP:
                continue
            groups[(res, ch)].append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
    out = []
    for (res, ch), pts in groups.items():
        c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))
        out.append((res, ch, c, len(pts)))
    return out

report = []
for r in cand["novel_candidates"]:
    pdb, pid = r["pdb"], r["pocket_id"]
    pres = res_by_pid[(pdb, pid)]
    chains = sorted({c for c, _ in pres})
    # min distance from pocket residue atoms to each het cluster centroid
    patoms = defaultdict(list)
    for l in open(NP / f"{pdb}_prot.pdb"):
        if l.startswith("ATOM"):
            key = (l[21].strip(), l[22:26].strip())
            if key in pres:
                patoms[key].append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
    allp = [p for v in patoms.values() for p in v]
    near = []
    for res, ch, c, n in het_clusters(pdb):
        dmin = min(math.dist(p, c) for p in allp)
        if dmin < 6.0:
            near.append(f"{res}/{ch}({dmin:.1f}A)")
    report.append({**r, "chains": chains, "n_chains": len(chains),
                   "is_interface": len(chains) > 1,
                   "het_within_6A": near[:6]})
    tag = "INTERFACE" if len(chains) > 1 else "single-chain"
    print(f"{pdb} p{pid:<3d} ds={r['ds']:.2f} vol={r['volume']:6.0f} {tag:9s} "
          f"near: {', '.join(near[:4]) if near else '-'}")

json.dump(report, open(BASE / "data/novelq_p4b_novelty_crosscheck.json", "w"), indent=1)
print("saved data/novelq_p4b_novelty_crosscheck.json")
