"""F2: emapunil docking campaign across all PK11195-binder protein pockets.

Protocol per pocket:
  1. download PDB, auto-detect the drug-like co-crystal ligand (largest hetero HETATM cluster);
  2. redock control: co-crystal ligand into its own pocket (tight box 14 A, exhaustiveness 32);
     GATE: centroid recovery < 3.0 A;
  3. dock emapunil into the gated pocket (same box).
Pre-registered FEP selection rule (written BEFORE seeing results):
  eligible = redock gate PASS AND emapunil top pose centroid within 3.0 A of pocket center
  ranked by emapunil Vina top score; top 3 -> FEP set, plus TSPO 4RYI anchor and
  the worst eligible pocket as negative control.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import (
    STRUCT, OUT, prep_ligand, run_vina, clean_receptor, prep_pdbqt, ligand_centroid)

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 emapunil-f2/1.0"

EMAPUNIL = "CCN(CC1=CC=CC=C1)C(=O)CN2C3=NC(=NC=C3N(C2=O)C)C4=CC=CC=CC=C4"  # placeholder, corrected below
EMAPUNIL = "CCN(CC1=CC=CC=C1)C(=O)CN2C3=NC(=NC=C3N(C2=O)C)C4=CC=CC=C4"

# pdb -> (label, fixed ligand code/chain or None for auto, chains to drop)
POCKETS = [
    ("4RYI",  "TSPO (construct, prior anchor)", "PKA",     ()),
    ("1XVP",  "CAR LBD",                        "CID",     ("A", "C", "B", "E", "F")),
    ("2QNV",  "PXR LBD",                        "CDZ",     ()),
    ("6X3X",  "GABA-A BZD site",                "DZP",     ()),
    ("6HUG",  "GABA-A picrotoxin site",         "PIO",     ()),
    ("5EDU",  "HDAC6 catalytic",                None,      ()),
    ("5HK1",  "SIGMAR1",                        None,      ()),
    ("5TGZ",  "CNR1 orthosteric",               None,      ()),
    ("4DJH",  "OPRK1 orthosteric",              None,      ()),
    ("4DKL",  "OPRM1 orthosteric",              None,      ()),
    ("2ILT",  "HSD11B1",                        None,      ()),
    ("4WB9",  "ALDH1A1",                        None,      ()),
    ("1NOP",  "TDP1",                           None,      ()),
    ("4GQ4",  "MEN1 (MLL-i pocket)",            None,      ()),
    ("7X1U",  "TRHR peptide site",              None,      ()),
    ("7F61",  "HRH3 orthosteric",               None,      ()),
    ("4XAQ",  "GRM2 (allosteric site if present)", None,   ()),
]


def fetch(pdb):
    p = STRUCT / f"{pdb}.pdb"
    if p.exists() and p.stat().st_size > 10000:
        return p
    r = subprocess.run(["curl", "-sS", "--max-time", "120", "-o", str(p),
                        f"https://files.rcsb.org/download/{pdb}.pdb"], capture_output=True, text=True)
    return p if p.exists() and p.stat().st_size > 10000 else None


def het_ligands(pdb_path, chain=None):
    """Return [(resname, chain, n_atoms)] for HETATM clusters sorted by atom count desc."""
    counts = {}
    for line in open(pdb_path):
        if line.startswith("HETATM"):
            res = line[17:20].strip()
            ch = line[21].strip()
            resn = line[22:26].strip()
            # skip waters/ions/glycans
            if res in {"HOH", "SO4", "PO4", "GOL", "EDO", "MES", "ACT", "CL", "NA", "MG", "ZN",
                       "CA", "K", "MN", "CD", "HG", "F", "BR", "I", "NAG", "BMA", "MAN", "FUC",
                       "FUL", "MLI", "PEG", "P6G", "MPD", "DMS", "ACES", "EPE", "TRS", "TAR",
                       "CIT", "PGA", "FLC", "BGC", "GAL", "SIA"}:
                continue
            key = (res, ch, resn)
            counts[key] = counts.get(key, 0) + 1
    items = sorted(counts.items(), key=lambda kv: -kv[1])
    # cluster by resname: keep resnames with >= 15 atoms (drug-like) first
    return [(r, c, n, resn) for (r, c, resn), n in items]


def run(pdb, label, lig, drop):
    pdb_path = fetch(pdb)
    if pdb_path is None:
        return {"label": label, "error": "download failed"}
    if lig is None:
        cands = het_ligands(pdb_path)
        if not cands:
            return {"label": label, "error": "no drug-like co-crystal ligand found"}
        resname, ch, natoms, _ = cands[0]
        if natoms < 12:
            return {"label": label, "error": f"best ligand {resname} too small ({natoms} atoms)"}
        lig = (resname, ch)
    elif isinstance(lig, str):
        lig = (lig, "")
    code, chain = lig
    center = ligand_centroid(str(pdb_path), code, chain if chain else None)
    rec = OUT / f"f2_{pdb}_rec.pdb"
    clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
    rec_pdbqt = OUT / f"f2_{pdb}_rec.pdbqt"
    prep_pdbqt(str(rec), str(rec_pdbqt))
    out = {"label": label, "pdb": pdb, "pocket_ligand": code, "chain": chain, "center": center}
    # redock control
    ctrl_lig = OUT / f"f2_{pdb}_ctrl.pdbqt"
    prep_ligand_from_pdb(pdb_path, code, chain, ctrl_lig)
    docked = OUT / f"f2_{pdb}_ctrl_docked.pdbqt"
    scores = run_vina(str(rec_pdbqt), str(ctrl_lig), center, str(docked), exhaustiveness=32)
    out["redock_score"] = scores[0]
    out["redock_poses"] = scores
    # centroid recovery: extract pose 1 centroid from docked pdbqt
    cen = pose_centroid(docked)
    out["redock_centroid"] = cen
    out["redock_recovery_A"] = round(dist(cen, center), 2)
    # emapunil
    emap = OUT / "lig_emapunil.pdbqt"
    if not emap.exists():
        prep_ligand(EMAPUNIL, str(emap))
    docked_e = OUT / f"f2_{pdb}_emapunil_docked.pdbqt"
    scores_e = run_vina(str(rec_pdbqt), str(emap), center, str(docked_e), exhaustiveness=32)
    out["emapunil_score"] = scores_e[0]
    out["emapunil_poses"] = scores_e
    cen_e = pose_centroid(docked_e)
    out["emapunil_centroid"] = cen_e
    out["emapunil_in_pocket_A"] = round(dist(cen_e, center), 2)
    out["eligible_for_FEP"] = bool(out["redock_recovery_A"] < 3.0 and out["emapunil_in_pocket_A"] < 3.0)
    return out


def prep_ligand_from_pdb(pdb_path, code, chain, out_pdbqt):
    """Extract co-crystal ligand PDB -> SDF (bond perception) -> rigid-ligand pdbqt.

    Vina (as opposed to AutoDock) rejects ROOT/BRANCH blocks in ligand files it
    reads via set_ligand_from_file for some inputs; the robust path is a flat
    pdbqt. obabel pdb->pdbqt emits torsion trees for some inputs; going through
    SDF normalises it. If still tree-form, strip torsion lines to make it rigid.
    """
    import tempfile
    txt = []
    for line in open(pdb_path):
        if line.startswith(("HETATM",)) and line[17:20].strip() == code \
                and (not chain or line[21].strip() == chain):
            txt.append(line)
    if not txt:
        raise RuntimeError(f"no HETATM for {code} chain={chain or '*'} in {pdb_path}")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".pdb", delete=False)
    tmp.write("".join(txt))
    tmp.close()
    sdf = str(out_pdbqt).replace(".pdbqt", ".sdf")
    subprocess.run(["obabel", tmp.name, "-O", sdf], capture_output=True, text=True)
    r = subprocess.run(["obabel", sdf, "-O", str(out_pdbqt)], capture_output=True, text=True)
    Path(tmp.name).unlink()
    if not Path(out_pdbqt).exists() or Path(out_pdbqt).stat().st_size == 0:
        raise RuntimeError(f"obabel conversion failed for {code}: {r.stderr[-200:]}")
    # obabel may emit duplicated ROOT/torsion trees when bond perception splits the
    # ligand; vina accepts exactly one tree. Truncate at the first TORSDOF.
    lines = open(out_pdbqt).readlines()
    keep, seen_tors = [], 0
    for line in lines:
        if line.startswith("TORSDOF"):
            seen_tors += 1
            if seen_tors == 1:
                keep.append(line)
            continue
        if seen_tors >= 1:
            break
        keep.append(line)
    Path(out_pdbqt).write_text("".join(keep))


def pose_centroid(pdbqt, pose=1):
    coords = []
    in_model = 0
    for line in open(pdbqt):
        if line.startswith("MODEL"):
            in_model += 1
        elif in_model == pose and line.startswith(("ATOM", "HETATM")):
            # skip polar hydrogens (type HD) — fine to include, minor
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


if __name__ == "__main__":
    results = {}
    for pdb, label, lig, drop in POCKETS:
        print(f"\n=== {pdb} {label} ===", flush=True)
        try:
            res = run(pdb, label, lig, drop)
        except Exception as e:
            import traceback
            traceback.print_exc()
            res = {"label": label, "error": f"{type(e).__name__}: {e}"}
        results[pdb] = res
        print(json.dumps({k: v for k, v in res.items() if k != "center"}, default=str), flush=True)
        json.dump(results, open(OUT / "emapunil_f2_docking.json", "w"), indent=1)  # checkpoint each
    print("\n== summary ==")
    for pdb, r in results.items():
        if "error" in r:
            print(f"{pdb} {r['label']}: ERROR {r['error']}")
        else:
            print(f"{pdb} {r['label']:34s} redock {r['redock_score']:+.2f} ({r['redock_recovery_A']:.1f} A)"
                  f" | emapunil {r['emapunil_score']:+.2f} ({r['emapunil_in_pocket_A']:.1f} A)"
                  f" {'FEP-ELIGIBLE' if r['eligible_for_FEP'] else ''}")
