"""ws6 P5b: fixed controls (single-cluster ligand extraction, crystal-ligand
centroid boxes) + hit-tier confirmation re-dock for the MD shortlist.

Hit tier: 3 independent Vina runs x exhaustiveness 32 (vina 1.2.7 python API has
no seed argument — each run draws a random seed; the spread IS the seed
sensitivity). MD shortlist (top per target family):
  4RYI_p26 (TSPO), 6X3X_p78, 6X3X_p128 (GABA-A a/g TMD), 6HUG_p114 (GABA-A pore),
  4DKL_p2 (OPRM1), 4DJH_p53 (OPRK1), 4WB9_p1 (ALDH1A1), 7F61_p15 (HRH3),
  7M93_p18 + 9ZIR_p11 (TMEM97, one per structure).
"""
import json, math, subprocess
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
NP = BASE / "output/novel_pockets"
DOCK = BASE / "output/docking"
VENVBIN = "/home/QYJI/das/druggability/.venv/bin"
LIG = DOCK / "lig_emapunil.pdbqt"

SHORTLIST = ["4RYI_p26", "6X3X_p78", "6X3X_p128", "6HUG_p114", "4DKL_p2",
             "4DJH_p53", "4WB9_p1", "7F61_p15", "7M93_p18", "9ZIR_p11"]

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd[:140]}\n{r.stderr[-300:]}")
    return r.stdout

def run_vina(rec_pdbqt, lig_pdbqt, center, out_pdbqt, size, exh):
    py = (f"from vina import Vina; "
          f"v=Vina(sf_name='vina'); "
          f"v.set_receptor('{rec_pdbqt}'); "
          f"v.set_ligand_from_file('{lig_pdbqt}'); "
          f"v.compute_vina_maps(center=[{center[0]:.3f},{center[1]:.3f},{center[2]:.3f}], box_size=[{size},{size},{size}]); "
          f"v.dock(exhaustiveness={exh}, n_poses=5); "
          f"v.write_poses('{out_pdbqt}', n_poses=5, overwrite=True); "
          f"print('SCORES:', ' '.join(f'{{s[0]:.2f}}' for s in v.energies(n_poses=5)))")
    out = sh(f"{VENVBIN}/python -c \"{py}\"")
    return [float(x) for x in out.split("SCORES:")[1].split("\n")[0].split()]

def pose_centroid(pdbqt_path, pose=1):
    coords, cur = [], 0
    for line in open(pdbqt_path):
        if line.startswith("MODEL"):
            cur += 1
        elif cur == pose and line.startswith(("ATOM", "HETATM")) and line[77:79].strip() != "HD":
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL") and cur >= pose:
            break
    n = len(coords)
    return (sum(c[0] for c in coords) / n, sum(c[1] for c in coords) / n, sum(c[2] for c in coords) / n)

def lig_cluster(pdb_id, code):
    """largest single cluster of HETATM resname==code -> pdbqt."""
    from collections import defaultdict
    g = defaultdict(list)
    for l in open(NP / f"{pdb_id}.pdb"):
        if l.startswith("HETATM") and l[17:20].strip() == code:
            g[l[21].strip()].append(l)
    ch, lines = max(g.items(), key=lambda kv: len(kv[1]))
    dst = NP / f"{pdb_id}_{code}_lig.pdbqt"
    tmp = NP / f"{pdb_id}_{code}_lig_raw.pdb"
    tmp.write_text("".join(lines))
    sh(f"{VENVBIN}/obabel {tmp} -O {dst} -h 2>/dev/null")
    # crystal ligand centroid (heavy atoms, original coords)
    pts = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in lines]
    cen = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))
    return dst, cen

def main():
    raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))
    v2 = json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))
    rows_by_tag = {f"{r['pdb']}_p{r['pocket_id']}": r for r in v2["novel_v2"]}

    # ---- controls (fixed) ----
    ctrl = []
    for pdb, code in [("4OO9", "2U8"), ("7M93", "YT1"), ("9ZIR", "A1C")]:
        rec = NP / f"{pdb}_novelq_rec.pdbqt"
        lig, cen = lig_cluster(pdb, code)
        out = NP / f"redock_{pdb}_{code}_docked.pdbqt"
        scores = run_vina(rec, lig, cen, out, 14.0, 16)
        off = math.dist(pose_centroid(out, 1), cen)
        ctrl.append({"tag": f"redock_{pdb}_{code}", "scores": scores, "offset_A": round(off, 2),
                     "qc": "PASS" if off <= 3.0 else "FAIL"})
        print(f"QC redock {pdb} {code}: {scores[0]:.2f} off {off:.2f} {'PASS' if off <= 3.0 else 'FAIL'}", flush=True)
        out2 = NP / f"emapunil_{pdb}_knownpocket_docked.pdbqt"
        scores2 = run_vina(rec, LIG, cen, out2, 22.0, 16)
        off2 = math.dist(pose_centroid(out2, 1), cen)
        ctrl.append({"tag": f"emapunil_{pdb}_knownpocket", "scores": scores2,
                     "offset_A": round(off2, 2), "in_pocket": off2 <= 6.0})
        print(f"emapunil {pdb} known pocket: {scores2[0]:.2f} off {off2:.2f}", flush=True)
    json.dump(ctrl, open(DOCK / "novelq_p5_controls.json", "w"), indent=1)

    # ---- hit tier ----
    hits = {}
    for tag in SHORTLIST:
        r = rows_by_tag[tag]
        pdb, pid, cen = r["pdb"], r["pocket_id"], r["pocket_center"]
        rec = NP / f"{pdb}_novelq_rec.pdbqt"
        seed_scores, files = [], []
        for s in range(3):
            out = NP / f"hit_{tag}_s{s}_docked.pdbqt"
            sc = run_vina(rec, LIG, cen, out, 24.0, 32)
            seed_scores.append(sc)
            files.append(str(out))
        best_i = min(range(3), key=lambda i: seed_scores[i][0])
        off = math.dist(pose_centroid(Path(files[best_i]), 1), cen)
        hits[tag] = {"pdb": pdb, "pocket_id": pid, "gene": r["gene"], "label": r["label"],
                     "pocket_center": cen, "pocket_residues": None,
                     "seed_scores": seed_scores,
                     "best_of_seeds": min(s[0] for s in seed_scores),
                     "worst_of_seeds": max(s[0] for s in seed_scores),
                     "pose1_offset_A": round(off, 2),
                     "best_pose_file": files[best_i],
                     "confirmed": min(s[0] for s in seed_scores) <= -7.0 and off <= 6.0}
        ss = " ".join(f"{s[0]:.2f}" for s in seed_scores)
        print(f"{tag:12s} hit-tier 3 seeds: {ss} off {off:.2f} "
              f"{'CONFIRMED' if hits[tag]['confirmed'] else 'not confirmed'}", flush=True)
    # attach pocket residues from P2 for the MD step
    for tag, h in hits.items():
        pres = [p for p in raw[h["pdb"]]["pockets"] if p["pocket_id"] == h["pocket_id"]][0]["residues"]
        h["pocket_residues"] = pres
    json.dump(hits, open(DOCK / "novelq_p5c_hittier.json", "w"), indent=1)
    print("saved novelq_p5c_hittier.json")

if __name__ == "__main__":
    main()
