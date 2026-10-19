"""ws6 P5: emapunil docking into NOVEL_v2 pockets (scan tier) + controls.

Scan tier (declared, mirrors GPR81 phase-6 precedent): exhaustiveness 16,
5 poses, single seed, box 24 A centered on the fpocket pocket centroid.
Hit tier (follow-up for shortlist): exhaustiveness 32, 3 seeds.

Controls per NEW structure (4OO9, 7M93, 9ZIR):
  - redock the co-crystal ligand into its own pocket (tight box 14) -> receptor QC;
  - emapunil into the known co-crystal pocket (box 22) -> per-structure reference band.
The 14 structures from the 2026-10-19 emapunil campaign already carry controls in
emapunil_f2_docking.json (same protocol) and are NOT re-run.

Receptor: full downloaded assembly ({pdb}_prot.pdb, same file fpocket screened).
Ligand: output/docking/lig_emapunil.pdbqt (identical file as the f2 campaign ->
scores comparable across rounds).
"""
import json, math, subprocess, sys
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
NP = BASE / "output/novel_pockets"
DOCK = BASE / "output/docking"
VENVBIN = "/home/QYJI/das/druggability/.venv/bin"
LIG = DOCK / "lig_emapunil.pdbqt"
BOX = 24.0
EXH = 16
CONTROL_REDOCK = {"4OO9": ("2U8", 14.0), "7M93": ("YT1", 14.0), "9ZIR": ("A1C", 14.0)}

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd[:120]}\n{r.stderr[-400:]}")
    return r.stdout

def prep_receptor(pdb_id):
    src = NP / f"{pdb_id}_prot.pdb"
    dst = NP / f"{pdb_id}_novelq_rec.pdbqt"
    if not dst.exists():
        sh(f"{VENVBIN}/obabel {src} -O {dst} -xr")
    return dst

def ligand_code_pdbqt(pdb_id, code):
    """drug-like co-crystal ligand extracted from the entry, H-adding via obabel."""
    dst = NP / f"{pdb_id}_{code}_lig.pdbqt"
    if dst.exists():
        return dst
    # pull HETATM block for (code) from the raw pdb
    keep = [l for l in open(NP / f"{pdb_id}.pdb")
            if l.startswith("HETATM") and l[17:20].strip() == code]
    tmp = NP / f"{pdb_id}_{code}_lig_raw.pdb"
    tmp.write_text("".join(keep))
    sh(f"{VENVBIN}/obabel {tmp} -O {dst} -h --gen3d 2>/dev/null || obabel {tmp} -O {dst} -h")
    return dst

def run_vina(rec_pdbqt, lig_pdbqt, center, out_pdbqt, size=BOX, exhaustiveness=EXH, seed=42, n_poses=5):
    py = (f"from vina import Vina; "
          f"v=Vina(sf_name='vina'); "
          f"v.set_receptor('{rec_pdbqt}'); "
          f"v.set_ligand_from_file('{lig_pdbqt}'); "
          f"v.compute_vina_maps(center=[{center[0]:.3f},{center[1]:.3f},{center[2]:.3f}], box_size=[{size},{size},{size}]); "
          f"v.dock(exhaustiveness={exhaustiveness}, n_poses={n_poses}); "
          f"v.write_poses('{out_pdbqt}', n_poses={n_poses}, overwrite=True); "
          f"print('SCORES:', ' '.join(f'{{s[0]:.2f}}' for s in v.energies(n_poses={n_poses})))")
    out = sh(f"{VENVBIN}/python -c \"{py}\"")
    tail = out.split("SCORES:")[1].split("\n")[0]
    return [float(x) for x in tail.split()]

def pose_centroid(pdbqt_path, pose=1):
    coords, cur = [], 0
    for line in open(pdbqt_path):
        if line.startswith("MODEL"):
            cur += 1
        elif cur == pose and line.startswith(("ATOM", "HETATM")) and line[77:79].strip() != "HD":
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL") and cur >= pose:
            break
    return (sum(c[0] for c in coords) / len(coords),
            sum(c[1] for c in coords) / len(coords),
            sum(c[2] for c in coords) / len(coords))

def main():
    v2 = json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))["novel_v2"]
    jsonl = open(DOCK / "novelq_p5_emapunil_novel_pockets.jsonl", "w")
    print(f"{len(v2)} novel pockets to dock", flush=True)
    for r in v2:
        pdb, pid = r["pdb"], r["pocket_id"]
        tag = f"{pdb}_p{pid}"
        try:
            rec = prep_receptor(pdb)
            out = NP / f"emapunil_{tag}_docked.pdbqt"
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
        print(f"{tag:12s} {row.get('best','ERR')!s:>8} off={row.get('pose1_offset_A','-')} {row.get('verdict_scan', row.get('error',''))}", flush=True)
    # controls on new structures
    ctrl_rows = []
    for pdb, (code, box) in CONTROL_REDOCK.items():
        rec = prep_receptor(pdb)
        # known pocket center from P2 (fpocket pocket recovering the ligand)
        raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))[pdb]
        kp = [p for p in raw["pockets"] if p["recovers_known"]][0]
        kres = set(map(tuple, kp["residues"]))
        pat = [(float(l[30:38]), float(l[38:46]), float(l[46:54]))
               for l in open(NP / f"{pdb}_prot.pdb")
               if l.startswith("ATOM") and (l[21].strip(), l[22:26].strip()) in kres]
        cen = (sum(p[0] for p in pat) / len(pat), sum(p[1] for p in pat) / len(pat), sum(p[2] for p in pat) / len(pat))
        lig = ligand_code_pdbqt(pdb, code)
        out = NP / f"redock_{pdb}_{code}_docked.pdbqt"
        scores = run_vina(rec, lig, cen, out, size=box)
        off = math.dist(pose_centroid(out, 1), cen)
        ctrl_rows.append({"tag": f"redock_{pdb}_{code}", "scores": scores, "offset_A": round(off, 2),
                          "qc": "PASS" if off <= 3.0 else "FAIL"})
        print(f"QC redock {pdb} {code}: {scores[0]:.2f} off {off:.2f} {'PASS' if off<=3.0 else 'FAIL'}", flush=True)
        out2 = NP / f"emapunil_{pdb}_knownpocket_docked.pdbqt"
        scores2 = run_vina(rec, LIG, cen, out2, size=22)
        off2 = math.dist(pose_centroid(out2, 1), cen)
        ctrl_rows.append({"tag": f"emapunil_{pdb}_knownpocket", "scores": scores2,
                          "offset_A": round(off2, 2), "in_pocket": off2 <= 6.0})
        print(f"emapunil {pdb} known pocket: {scores2[0]:.2f} off {off2:.2f}", flush=True)
    with open(DOCK / "novelq_p5_controls.json", "w") as fh:
        json.dump(ctrl_rows, fh, indent=1)
    jsonl.close()
    print("done")

if __name__ == "__main__":
    main()
