#!/usr/bin/env python3
"""
GPR81 follow-up: full-chain data-integrity audit (2026-08-05).

Re-verifies every layer from INDEPENDENT sources rather than trusting the
delivered files:
  1. Boltz layer: boltz_results.csv vs re-parsed local BioLib outputs
     (affinity_boltz.json + confidence_boltz_model_0.json in data/boltz_runs/)
  2. Scorecard: EC50 vs paper_structures_recovered.json; Vina scores vs
     phase6_full_series/full_series_summary.json; region vs consensus JSON;
     tier rule recomputed independently
  3. Pocket pairs: scores vs re-parsed pose PDBQTs (best-of-all-models),
     pair count vs 46, unique entry ids
  4. Lactate x 9KT9 tight-box: CSV vs JSON consistency

Prints PASS/FAIL per check with exact deltas. Exit 1 if any FAIL.
"""
import csv, json, math, sys
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent          # followup_2026-08
P1 = BASE.parent                                # gpr81_phase1
FAILS, PASSES = [], []


def check(name, cond, detail=""):
    (PASSES if cond else FAILS).append((name, detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 1. Boltz layer
print("== 1. Boltz layer: boltz_results.csv vs local BioLib outputs ==")
rows = list(csv.DictReader(open(BASE / "data/boltz_results.csv")))
check("boltz_results.csv row count == 45", len(rows) == 45, f"n={len(rows)}")
ids = [r["entry_id"] for r in rows]
check("entry_id unique", len(set(ids)) == len(ids))
sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
sc_ids = {c["entry_id"] for c in sc["compounds"]}
check("entry_ids cover all 45 scorecard entries", set(ids) == sc_ids,
      f"missing={sc_ids - set(ids)}")
check("all exit_code == 0", all(r["boltz_exit_code"] == "0" for r in rows),
      f"exits={ {r['boltz_exit_code'] for r in rows} }")
check("no error column set", all(not r.get("error") for r in rows))
check("all job_ids present", all(len(r.get("boltz_job_id", "")) >= 8 for r in rows))
# spot-check 6 compounds against the local downloaded BioLib outputs
mism = 0
checked = 0
for r in rows:
    eid = r["entry_id"]
    run = BASE / "data/boltz_runs" / eid / "predictions/boltz"
    aff_p = run / "affinity_boltz.json"
    conf_p = run / "confidence_boltz_model_0.json"
    if not (aff_p.exists() and conf_p.exists()):
        check(f"boltz {eid} local outputs exist", False, f"missing {run}")
        mism += 1
        continue
    aff = json.load(open(aff_p))
    conf = json.load(open(conf_p))
    pairs = [
        ("boltz_affinity_pred_value", "affinity_pred_value", aff),
        ("boltz_affinity_probability_binary", "affinity_probability_binary", aff),
        ("boltz_confidence_score", "confidence_score", conf),
        ("boltz_ligand_iptm", "ligand_iptm", conf),
    ]
    for csv_k, json_k, src in pairs:
        a, b = f(r.get(csv_k)), f(src.get(json_k))
        if a is None or b is None or abs(a - b) > 1e-6:
            mism += 1
            check(f"boltz {eid} {csv_k} matches re-parsed JSON", False,
                  f"csv={a} json={b}")
    checked += 1
check(f"ALL {checked}/45 compounds: all 4 metrics match re-parsed local JSON", mism == 0)

# ---------------------------------------------------------------- 2. Scorecard
print("== 2. Scorecard: EC50 / Vina scores / region / tier ==")
rec = json.load(open(P1 / "paper_structures_recovered.json"))
paper_ec50 = {e["paper_compound_number"]: e.get("paper_reported_hGPR81_EC50_uM")
              for e in rec["compounds"]}
sc_rows = {c["entry_id"]: c for c in sc["compounds"]}
ec_mism = 0
for cid in range(1, 40):
    key = f"c{cid:02d}"
    got = sc_rows[key]["ec50_uM"]
    want = paper_ec50.get(cid)
    if got is None or want is None:
        if got != want:
            ec_mism += 1
            check(f"EC50 c{cid:02d} matches recovered JSON", False, f"got={got} want={want}")
    elif abs(float(got) - float(want)) > 1e-9:
        ec_mism += 1
        check(f"EC50 c{cid:02d} matches recovered JSON", False, f"got={got} want={want}")
check("all 39 paper EC50 values match recovered JSON", ec_mism == 0)

# Vina scores vs phase6 summary
summ = json.load(open(P1 / "phase6_full_series/full_series_summary.json"))
vs_mism = 0
for cid in range(1, 40):
    key = f"c{cid:02d}"
    want = summ[str(cid)]["8Z8A"]["best"]
    got = sc_rows[key]["dock_8Z8A_best"]
    if got is None or abs(float(got) - float(want)) > 1e-6:
        vs_mism += 1
        check(f"8Z8A best score c{cid:02d}", False, f"scorecard={got} summary={want}")
check("39 paper 8Z8A best scores match full_series_summary.json", vs_mism == 0)

# region vs consensus
cons = json.load(open(P1 / "phase6_full_series/full_series_region_consensus_2seed.json"))
reg_mism = 0
for cid in range(1, 40):
    key = f"c{cid:02d}"
    want = cons["compounds"][key]["8Z8A"]["consensus"]
    got = sc_rows[key]["region_8Z8A"]
    if got != want:
        reg_mism += 1
        check(f"region c{cid:02d}", False, f"scorecard={got} consensus={want}")
check("39 paper 8Z8A regions match consensus JSON", reg_mism == 0)

# tier recomputed independently
def tier_recompute(c):
    ec = c["ec50_nM"]
    if ec is None:
        return None
    emax = c["emax_pct"]
    g109, ghsr = c["gpr109a_fold"], c["ghsr_fold"]
    if ec <= 50 and (emax is None or emax >= 80) and (g109 is None or g109 >= 25) and (ghsr is None or ghsr >= 50):
        return "A"
    if ec <= 100:
        return "B"
    return "C"
t_mism = 0
for c in sc["compounds"]:
    if c["ec50_nM"] is None:
        continue
    want = tier_recompute(c)
    if want != c["tier"]:
        t_mism += 1
        check(f"tier {c['entry_id']}", False, f"stored={c['tier']} recomputed={want}")
check("tier rule recomputed identically for all ranked compounds", t_mism == 0)

# ---------------------------------------------------------------- 3. Pocket pairs
print("== 3. Pocket pairs: 46 pairs, scores vs re-parsed poses ==")
pairs = json.load(open(BASE / "data/gpr81_pocket_analysis_pairs.json"))["pairs"]
check("pairs count == 46", len(pairs) == 46, f"n={len(pairs)}")
pids = [p["pair_id"] for p in pairs]
check("pair_id unique", len(set(pids)) == len(pids))
check("expected pair_id set matches", set(pids) == {
    *(f"c{c:02d}_8Z8A" for c in range(1, 40)),
    *("t01_8Z8A", "t02_8Z8A", "t03_8Z8A", "t04_8Z8A", "t05_8Z8A"),
    "lac_8Z8A", "lac_9KT9",
}, f"unexpected={set(pids) - {*(f'c{c:02d}_8Z8A' for c in range(1,40)), 't01_8Z8A','t02_8Z8A','t03_8Z8A','t04_8Z8A','t05_8Z8A','lac_8Z8A','lac_9KT9'}}")


def parse_pose_best(path):
    best = None
    for line in Path(path).read_text().splitlines():
        if line.startswith("REMARK VINA RESULT:"):
            try:
                s = float(line.split()[3])
            except (ValueError, IndexError):
                continue
            if best is None or s < best:
                best = s
    return best


pm_mism = 0
import random
random.seed(42)
for p in random.sample(pairs, 8):
    best = None
    for pf in p["_pose_files"]:
        if Path(pf).exists():
            s = parse_pose_best(pf)
            if s is not None and (best is None or s < best):
                best = s
    if best is None:
        pm_mism += 1
        check(f"pose parse {p['pair_id']}", False, "no REMARK VINA RESULT found")
    elif abs(best - float(p["best_score_kcal_mol"])) > 0.01:
        pm_mism += 1
        check(f"best score {p['pair_id']}", False,
              f"stored={p['best_score_kcal_mol']} re-parsed={best:.3f}")
check(f"spot-checked 8 pairs: best scores match re-parsed pose files", pm_mism == 0)

# centroid distances recomputed for 4 pairs
def parse_pose_atoms(path):
    atoms, in_model = [], False
    for line in Path(path).read_text().splitlines():
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
                if el in ("H", "HD"):
                    continue
                atoms.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except (ValueError, IndexError):
                continue
    return np.array(atoms)


def parse_pdb_xyz(path):
    out = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el == "H":
                    continue
                out.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except (ValueError, IndexError):
                try:
                    fl = line.split()
                    out.append([float(fl[6]), float(fl[7]), float(fl[8])])
                except (ValueError, IndexError):
                    continue
    return np.array(out)


ref_map = {"8Z8A": "8Z8A_2OP.pdb", "9KT9": "9KT9_34D.pdb", "8Z87": "8Z87_A1D71.pdb"}
cent_mism = 0
for p in random.sample(pairs, 4):
    pose = None
    for pf in p["_pose_files"]:
        if Path(pf).exists():
            a = parse_pose_atoms(pf)
            if len(a):
                pose = a
                break
    ref = parse_pdb_xyz(P1 / "phase2_prepared/reference_ligands" / ref_map[p["receptor"]])
    if pose is None or not len(ref):
        cent_mism += 1
        check(f"centroid {p['pair_id']}", False, "parse failed")
        continue
    d = float(np.linalg.norm(pose.mean(axis=0) - ref.mean(axis=0)))
    if abs(d - float(p["pose_centroid_to_cocrystal_A"])) > 0.5:
        cent_mism += 1
        check(f"centroid {p['pair_id']}", False,
              f"stored={p['pose_centroid_to_cocrystal_A']} recomputed={d:.2f}")
check("spot-checked 4 pairs: centroid-to-co-crystal distances recompute", cent_mism == 0)

# ---------------------------------------------------------------- 3b. HTML renders source values
print("== 3b. HTML table values vs source CSV ==")
html = (BASE / "gpr81_boltz_wetlab_report.html").read_text(encoding="utf-8")
html_mism = 0
for eid in ("c30", "c28", "t02", "lac"):
    row = next(r for r in rows if r["entry_id"] == eid)
    prob = f"{f(row['boltz_affinity_probability_binary']):.3f}"
    if prob not in html:
        html_mism += 1
        check(f"html contains boltz prob for {eid}", False)
check("HTML embeds source Boltz values (c30/c28/t02/lac)", html_mism == 0)

# ---------------------------------------------------------------- 4. Lactate 9KT9
print("== 4. Lactate x 9KT9 tight-box: CSV vs JSON ==")
lac_csv = list(csv.DictReader(open(BASE / "data/lactate_9kt9_tightbox.csv")))
lac_json = json.load(open(BASE / "data/lactate_9kt9_tightbox.json"))
check("lactate tightbox CSV has 15 pose rows (3 seeds x 5 poses)", len(lac_csv) == 15,
      f"n={len(lac_csv)}")
scores = [f(r["score_kcal_mol"]) for r in lac_csv]
check("CSV best score matches JSON best", min(scores) == lac_json["best_score_kcal_mol"],
      f"csv_min={min(scores)} json={lac_json['best_score_kcal_mol']}")
dists = [f(r["centroid_distance_A"]) for r in lac_csv]
check("CSV best centroid matches JSON", min(dists) == lac_json["best_centroid_recovery_A"],
      f"csv_min={min(dists)} json={lac_json['best_centroid_recovery_A']}")

# ---------------------------------------------------------------- summary
print()
print(f"RESULT: {len(PASSES)} passed, {len(FAILS)} failed")
if FAILS:
    print("FAILED CHECKS:")
    for name, detail in FAILS:
        print(f"  - {name}: {detail}")
    sys.exit(1)
print("ALL CHECKS PASSED")
