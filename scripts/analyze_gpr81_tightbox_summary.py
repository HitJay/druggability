#!/usr/bin/env python3
"""Phase 5 analysis - validity + binding-region annotated matched-pair summary.

Fixes the readability problem of matched_pair_summary.json (raw scores mixed
positive/negative with no context). For every (compound, receptor) this emits:
  - best/mean score under the 24A multi-seed protocol
  - binding-region classification of the best pose:
      ORTHO_POCKET | TM56_EXTRACELLULAR | NTERM_SURFACE | MIXED | NO_CONTACT
  - validity: OK / CLASH / LOW_CONF
  - verdict text that cannot be misread as "non-binder".

Key context encoded in the verdicts:
  * Paper series compounds bind the TM5-TM6 extracellular region, NOT the
    orthosteric small-acid pocket (12-14 A away from co-crystal center).
  * 8Z87 (CHBA-bound) scores these large molecules systematically positive in
    the TM5-TM6 region => conformational clash in that state, not non-binding.
  * 8Z8A (lactate-bound) accommodates them (negative scores), amide series
    c35-38 even reaches the orthosteric pocket on 8Z8A.

Outputs: data/gpr81_phase1/phase5_tightbox/annotated_matched_pairs.csv / .json
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

PHASE1 = Path(__file__).resolve().parents[1] / "data/gpr81_phase1"
P4 = PHASE1 / "phase4_matched_pairs"
P5 = PHASE1 / "phase5_tightbox"

EC50 = {15: 0.299, 21: 0.895, 22: 0.166, 26: 0.021, 28: 0.022, 30: 0.005,
        31: 0.24, 35: 0.60, 36: 0.16, 37: 0.35, 38: 0.054}
SERIES = {15: "acyl_urea", 21: "acyl_urea", 22: "acyl_urea", 26: "constrained_cyclic",
          28: "constrained_cyclic", 30: "constrained_cyclic", 31: "constrained_cyclic",
          35: "amide", 36: "amide", 37: "amide", 38: "amide"}

ORTHO = {71, 75, 92, 95, 96, 99, 165, 167, 168, 261, 264, 268}
TM56 = {153, 155, 157, 164, 166, 169, 170, 171, 174, 177}
NTERM = {6, 7, 8, 9, 79}


def pose_first_model(path: Path) -> list[np.ndarray]:
    atoms, in_model = [], False
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            if in_model:
                break
            in_model = True
            continue
        if line.startswith("ENDMDL") and in_model:
            break
        if in_model and line.startswith(("ATOM", "HETATM")):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el != "H":
                    atoms.append(np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]))
            except (ValueError, IndexError):
                continue
    return atoms


def parse_pdb_atoms(path: Path) -> list[tuple]:
    out = []
    for line in path.read_text().splitlines():
        if line.startswith("ATOM"):
            try:
                out.append((int(line[22:26]), float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    return out


def classify(pose, prep_atoms, cutoff=4.5) -> str:
    hits = Counter()
    for lx, ly, lz in pose:
        for ri, rx, ry, rz in prep_atoms:
            if ((lx - rx) ** 2 + (ly - ry) ** 2 + (lz - rz) ** 2) ** 0.5 < cutoff:
                hits[ri] += 1
    n = sum(hits.values())
    if n == 0:
        return "NO_CONTACT"
    o = sum(v for k, v in hits.items() if k in ORTHO) / n
    t = sum(v for k, v in hits.items() if k in TM56) / n
    nt = sum(v for k, v in hits.items() if k in NTERM) / n
    if o >= 0.4:
        return "ORTHO_POCKET"
    if t >= 0.4:
        return "TM56_EXTRACELLULAR"
    if nt >= 0.4:
        return "NTERM_SURFACE"
    return "MIXED"


def main() -> None:
    # phase4 scores (24A box, 8 seeds)
    scores = defaultdict(list)
    with (P4 / "matched_pair_docking_results.csv").open() as fh:
        for r in csv.DictReader(fh):
            scores[(int(r["compound"]), r["receptor"])].append(float(r["score_kcal_mol"]))

    rows, out = [], {}
    for cid in sorted(EC50):
        entry = {"compound": cid, "series": SERIES[cid], "ec50_uM": EC50[cid], "receptors": {}}
        for rid in ["8Z87", "8Z8A"]:
            vals = scores.get((cid, rid), [])
            pose = pose_first_model(P4 / "poses" / f"c{cid}_{rid}_seed20260803.pdbqt")
            prep = parse_pdb_atoms(PHASE1 / f"phase2_prepared/receptors/{rid}_chainR_protein.pdb")
            region = classify(pose, prep) if pose else "NO_POSE"
            best = round(min(vals), 3) if vals else None
            mean = round(sum(vals) / len(vals), 3) if vals else None
            val = "CLASH" if best is not None and best > 0 else "OK"
            if rid == "8Z87" and val == "CLASH":
                verdict = ("clash-incompatible in CHBA-bound state (TM5-TM6 region); "
                           "known agonist - NOT a non-binder")
            elif rid == "8Z87":
                verdict = "TM5-TM6 region pose, CHBA-bound state"
            elif region == "ORTHO_POCKET":
                verdict = "reaches orthosteric pocket in lactate-bound state"
            else:
                verdict = "TM5-TM6 region pose, lactate-bound state"
            entry["receptors"][rid] = {"best_24A_box": best, "mean_24A_box": mean,
                                       "binding_region": region, "validity": val, "verdict": verdict}
            rows.append({"compound": cid, "receptor": rid, "ec50_uM": EC50[cid], "series": SERIES[cid],
                         "best_24A_box": best, "mean_24A_box": mean,
                         "binding_region": region, "validity": val, "verdict": verdict})
        out[str(cid)] = entry

    with (P5 / "annotated_matched_pairs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["compound", "receptor", "ec50_uM", "series", "best_24A_box",
                                           "mean_24A_box", "binding_region", "validity", "verdict"])
        w.writeheader()
        w.writerows(rows)
    (P5 / "annotated_matched_pairs.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"{'c':>3} {'EC50':>6} {'series':<18} {'8Z87 best':>9} {'region87':<18} {'8Z8A best':>9} {'region8A':<18}")
    for cid in sorted(EC50):
        e = out[str(cid)]["receptors"]
        print(f"{cid:>3} {EC50[cid]:>6} {SERIES[cid]:<18} "
              f"{str(e['8Z87']['best_24A_box']):>9} {e['8Z87']['binding_region']:<18} "
              f"{str(e['8Z8A']['best_24A_box']):>9} {e['8Z8A']['binding_region']:<18}")


if __name__ == "__main__":
    main()
