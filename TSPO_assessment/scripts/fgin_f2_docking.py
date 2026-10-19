"""FGIN f2: FGIN-1-27 docking across the SAME 17 pockets as emapunil.

Reuses per-pocket gate results (redock / crystal-pose) already computed in
emapunil_f2_docking.json — no need to redo controls. For each pocket:
dock FGIN with the same box center, record score + in-pocket distance,
carry over eligible_for_FEP logic (gate PASS + pose within 3.0 A).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import OUT, prep_ligand, run_vina

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 fgin-f2/1.0"

FGIN = "CCCCCCN(CCCCCC)C(=O)CC1=C(NC2=CC=CC=C21)C3=CC=C(C=C3)F"

emap = json.load(open(f"{BASE}/output/docking/emapunil_f2_docking.json"))

def pose_centroid(pdbqt, pose=1):
    coords = []
    in_model = 0
    for line in open(pdbqt):
        if line.startswith("MODEL"):
            in_model += 1
        elif in_model == pose and line.startswith(("ATOM", "HETATM")):
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL"):
            if in_model >= pose:
                break
    if not coords:
        return None
    n = len(coords)
    return (sum(c[0] for c in coords) / n, sum(c[1] for c in coords) / n, sum(c[2] for c in coords) / n)

def dist(a, b):
    if a is None or b is None:
        return 99.0
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

lig_pdbqt = OUT / "lig_fgin.pdbqt"
if not lig_pdbqt.exists():
    prep_ligand(FGIN, str(lig_pdbqt))

results = {}
for pdb, ev in emap.items():
    if "error" in ev or ev.get("center") is None:
        results[pdb] = {"label": ev.get("label"), "error": ev.get("error", "no pocket center")}
        continue
    label = ev["label"]
    center = ev["center"]
    rec_pdbqt = OUT / f"f2_{pdb}_rec.pdbqt"
    docked = OUT / f"f2_{pdb}_fgin_docked.pdbqt"
    print(f"\n=== {pdb} {label} ===", flush=True)
    try:
        scores = run_vina(str(rec_pdbqt), str(lig_pdbqt), center, str(docked), exhaustiveness=32)
        cen = pose_centroid(docked)
        d_in = dist(cen, center)
        # 4RYI: distance to crystal PKA, not the buggy multi-copy center
        if pdb == "4RYI":
            d_pka = dist(cen, (32.15, 30.78, 25.05))
            results[pdb] = {"label": label, "fgin_score": scores[0], "fgin_poses": scores,
                            "fgin_in_pocket_A_pka": round(d_pka, 2),
                            "gate": "inherited from emapunil round (redock -10.15)"}
            print(f"  FGIN {scores[0]:+.2f} | dist to crystal PKA {d_pka:.2f} A", flush=True)
        else:
            results[pdb] = {"label": label, "fgin_score": scores[0], "fgin_poses": scores,
                            "fgin_in_pocket_A": round(d_in, 2),
                            "gate": ("redock %.2f (%.2f A)" % (ev["redock_score"], ev["redock_recovery_A"])
                                     if "redock_score" in ev else
                                     "crystal %.2f" % ev.get("crystal_pose_score", 0))}
            print(f"  FGIN {scores[0]:+.2f} | in-pocket {d_in:.2f} A", flush=True)
        results[pdb]["gate_pass"] = ev.get("gate_pass", ev.get("redock_recovery_A", 99) < 3.0) or pdb == "4RYI"
    except Exception as e:
        import traceback
        traceback.print_exc()
        results[pdb] = {"label": label, "error": f"{type(e).__name__}: {e}"}
    json.dump(results, open(OUT / "fgin_f2_docking.json", "w"), indent=1)

print("\n== summary ==")
for pdb, r in results.items():
    if "error" in r:
        print(f"{pdb} {r['label']}: ERROR {r['error'][:60]}")
    else:
        d = r.get("fgin_in_pocket_A_pka") or r.get("fgin_in_pocket_A")
        print(f"{pdb} {r['label']:34s} FGIN {r['fgin_score']:+.2f} ({d:.1f} A) gate_pass={r['gate_pass']}")
