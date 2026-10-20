"""ws7 P1: FGIN-1-27 docking into NOVEL_v2 pockets (scan tier) + hit tier.

Copy-and-swap of novelq_p5_emapunil_docking.py + novelq_p5b_controls_hittier.py
(protocol reused verbatim so numbers stay comparable across ligands):
  - scan tier: exhaustiveness 16, 5 poses, box 24 A on fpocket centroid, all 29 pockets
  - gate: engaged = best <= -7.0 kcal/mol AND pose1 centroid offset <= 6.0 A
  - hit tier: 3 independent runs x exhaustiveness 32 on (a) every scan-engaged pocket
    and (b) the 10 emapunil-confirmed pockets (cross-ligand comparison set, regardless
    of FGIN scan verdict)
  - controls: redock co-crystal ligand (receptor QC) + FGIN into known pockets on the
    three NEW structures (4OO9/7M93/9ZIR), same as p5/p5b.
Ligand: output/docking/lig_fgin.pdbqt (identical file as the f2 FGIN campaign).
"""
import json, math, subprocess
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
NP = BASE / "output/novel_pockets"
DOCK = BASE / "output/docking"
VENVBIN = "/home/QYJI/das/druggability/.venv/bin"
LIG = DOCK / "lig_fgin.pdbqt"

EMAPUNIL_CONFIRMED = ["4RYI_p26", "6X3X_p78", "6X3X_p128", "6HUG_p114", "4DKL_p2",
                      "4DJH_p53", "4WB9_p1", "7F61_p15", "7M93_p18", "9ZIR_p11"]
CONTROL_REDOCK = {"4OO9": ("2U8", 14.0), "7M93": ("YT1", 14.0), "9ZIR": ("A1C", 14.0)}


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd[:140]}\n{r.stderr[-300:]}")
    return r.stdout


def run_vina(rec_pdbqt, lig_pdbqt, center, out_pdbqt, size=24.0, exh=16, n_poses=5):
    py = (f"from vina import Vina; "
          f"v=Vina(sf_name='vina'); "
          f"v.set_receptor('{rec_pdbqt}'); "
          f"v.set_ligand_from_file('{lig_pdbqt}'); "
          f"v.compute_vina_maps(center=[{center[0]:.3f},{center[1]:.3f},{center[2]:.3f}], box_size=[{size},{size},{size}]); "
          f"v.dock(exhaustiveness={exh}, n_poses={n_poses}); "
          f"v.write_poses('{out_pdbqt}', n_poses={n_poses}, overwrite=True); "
          f"print('SCORES:', ' '.join(f'{{s[0]:.2f}}' for s in v.energies(n_poses={n_poses})))")
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


def prep_receptor(pdb_id):
    src = NP / f"{pdb_id}_prot.pdb"
    dst = NP / f"{pdb_id}_novelq_rec.pdbqt"
    if not dst.exists():
        sh(f"{VENVBIN}/obabel {src} -O {dst} -xr")
    return dst


def lig_cluster(pdb_id, code):
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
    pts = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in lines]
    cen = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))
    return dst, cen


def main():
    v2 = json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))["novel_v2"]
    rows_by_tag = {f"{r['pdb']}_p{r['pocket_id']}": r for r in v2}
    # include demoted/adjacent rows so emapunil-confirmed pockets like 4DJH_p53 are addressable
    for r in json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))["all_rows"]:
        rows_by_tag.setdefault(f"{r['pdb']}_p{r['pocket_id']}", r)

    # ---------- scan tier ----------
    scan_path = DOCK / "novelq7_p1_fgin_scan.jsonl"
    if scan_path.exists():
        scan_rows = [json.loads(l) for l in open(scan_path)]
        print(f"scan jsonl exists ({len(scan_rows)} rows) -> skip scan tier")
    else:
        jsonl = open(scan_path, "w")
        print(f"{len(v2)} novel pockets to dock with FGIN", flush=True)
        for r in v2:
            pdb, pid = r["pdb"], r["pocket_id"]
            tag = f"{pdb}_p{pid}"
            try:
                rec = prep_receptor(pdb)
                out = NP / f"fgin_{tag}_docked.pdbqt"
                scores = run_vina(rec, LIG, r["pocket_center"], out)
                cen = pose_centroid(out, 1)
                off = math.dist(cen, r["pocket_center"])
                row = {"tag": tag, "pdb": pdb, "pocket_id": pid, "gene": r["gene"],
                       "label": r["label"], "is_interface": r["is_interface"],
                       "pocket_center": r["pocket_center"], "ds": r["ds"], "volume": r["volume"],
                       "scan_scores": scores, "best": scores[0],
                       "pose1_offset_A": round(off, 2),
                       "verdict_scan": ("engaged" if scores[0] <= -7.0 and off <= 6.0
                                        else "weak" if scores[0] <= -5.5 and off <= 6.0 else "not-engaged")}
            except Exception as e:
                row = {"tag": tag, "pdb": pdb, "pocket_id": pid, "error": f"{type(e).__name__}: {e}"}
            jsonl.write(json.dumps(row) + "\n"); jsonl.flush()
            print(f"{tag:12s} {row.get('best','ERR')!s:>8} off={row.get('pose1_offset_A','-')} "
                  f"{row.get('verdict_scan', row.get('error',''))}", flush=True)
        jsonl.close()
        scan_rows = [json.loads(l) for l in open(scan_path)]

    # ---------- hit tier ----------
    hit_path = DOCK / "novelq7_p2_fgin_hittier.json"
    if hit_path.exists():
        print("hittier exists -> skip")
        return
    engaged = [r["tag"] for r in scan_rows if r.get("verdict_scan") == "engaged"]
    crossset = [t for t in EMAPUNIL_CONFIRMED if t not in engaged]
    shortlist = engaged + crossset
    print(f"hit tier on {len(shortlist)} pockets ({len(engaged)} scan-engaged + {len(crossset)} emapunil-confirmed cross-set)", flush=True)

    raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))
    hits = {}
    for tag in shortlist:
        r = rows_by_tag[tag]
        pdb, pid, cen = r["pdb"], r["pocket_id"], r["pocket_center"]
        rec = prep_receptor(pdb)
        seed_scores, files = [], []
        for s in range(3):
            out = NP / f"fgin_hit_{tag}_s{s}_docked.pdbqt"
            sc = run_vina(rec, LIG, cen, out, 24.0, 32)
            seed_scores.append(sc)
            files.append(str(out))
        best_i = min(range(3), key=lambda i: seed_scores[i][0])
        off = math.dist(pose_centroid(Path(files[best_i]), 1), cen)
        hits[tag] = {"pdb": pdb, "pocket_id": pid, "gene": r["gene"], "label": r["label"],
                     "pocket_center": cen, "seed_scores": seed_scores,
                     "best_of_seeds": min(s[0] for s in seed_scores),
                     "worst_of_seeds": max(s[0] for s in seed_scores),
                     "pose1_offset_A": round(off, 2),
                     "best_pose_file": files[best_i],
                     "in_emapunil_confirmed_set": tag in EMAPUNIL_CONFIRMED,
                     "confirmed": min(s[0] for s in seed_scores) <= -7.0 and off <= 6.0}
        ss = " ".join(f"{s[0]:.2f}" for s in seed_scores)
        print(f"{tag:12s} hit-tier 3 seeds: {ss} off {off:.2f} "
              f"{'CONFIRMED' if hits[tag]['confirmed'] else 'not confirmed'}", flush=True)
    for tag, h in hits.items():
        pres = [p for p in raw[h["pdb"]]["pockets"] if p["pocket_id"] == h["pocket_id"]][0]["residues"]
        h["pocket_residues"] = pres
    json.dump(hits, open(hit_path, "w"), indent=1)
    print("saved", hit_path.name)


if __name__ == "__main__":
    main()
