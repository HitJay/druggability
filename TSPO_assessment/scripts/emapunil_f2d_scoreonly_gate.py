"""F2d: gate the 5 problem pockets via Vina score-only of the CRYSTAL pose.

Rationale: reconstructing the co-crystal ligand into a Vina-readable pdbqt keeps
corrupting large ligands (obabel mol2 fragments; SDF bond perception disconnects;
meeko fragment filter drops atoms). For gating purposes we do NOT need to re-dock:
Vina can SCORE the crystal pose as-is. A crystal pose scoring in the expected band
for its ligand validates receptor prep + pocket definition. Then emapunil is docked
into the same pocket normally (SMILES->3D, no reconstruction issue).

Gate: crystal-pose Vina energy < -6.0 kcal/mol for drug-like ligands
      (PKA/CID/CDZ/DZP/PIO are all sub-uM-uM ligands; -6 is conservative).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
import emapunil_f2_docking_campaign as m

OUT = m.OUT
VENV = "/home/QYJI/das/druggability/.venv/bin/python"

# element -> autodock type (co-crystal ligands are CHNO(S))
TYPE_MAP = {"C": "C", "N": "N", "O": "OA", "S": "SA", "P": "P", "F": "F", "CL": "Cl",
            "BR": "Br", "H": "HD"}


def crystal_pose_pdbqt(pdb_path, code, chain, out_pdbqt):
    """Hand-build a Vina pdbqt from HETATM lines: keep coords, assign types, q=0."""
    from collections import Counter
    txt = [l for l in open(pdb_path)
           if l.startswith("HETATM") and l[17:20].strip() == code
           and (not chain or l[21].strip() == chain)]
    resn = Counter(l[22:26] for l in txt).most_common(1)[0][0]
    inst = [l for l in txt if l[22:26] == resn]
    lines = []
    for i, l in enumerate(inst, 1):
        el = l[76:78].strip().upper()
        if not el:
            # infer from atom name
            name = l[12:16].strip()
            el = "".join(ch for ch in name if ch.isalpha())[:2]
            if el not in TYPE_MAP:
                el = el[0]
        atype = TYPE_MAP.get(el, "C")
        if el == "H":
            continue  # skip hydrogens, let vina treat as united-atom
        # PDBQT fixed columns: 1-6 rec, 7-11 serial, 12-15 blank, 13-16 name,
        # 17 altloc, 18-20 resname, 22 chain, 23-26 resseq, 31-54 coords,
        # 55-60 q, 61-66 vdw, 68-70 chars, 71-76 charges, 78-79 type
        lines.append(
            "ATOM  {:5d} {:^4s} UNL     1    {:8.3f}{:8.3f}{:8.3f}"
            "  0.00  0.00    0.000 {:<2s}\n".format(
                i, l[12:16].strip()[:4], float(l[30:38]), float(l[38:46]),
                float(l[46:54]), atype))
    Path(out_pdbqt).write_text("".join(lines))
    return len(lines), "".join(lines)


def vina_score_only(rec_pdbqt, lig_pdbqt, center, box=24):
    cmd = (f"{VENV} -c \"from vina import Vina; "
           f"v=Vina(sf_name='vina'); "
           f"v.set_receptor('{rec_pdbqt}'); "
           f"v.set_ligand_from_file('{lig_pdbqt}'); "
           f"v.compute_vina_maps(center=[{center[0]:.2f},{center[1]:.2f},{center[2]:.2f}], box_size=[{box},{box},{box}]); "
           f"e=v.score(); print('SCORE:', e)\"")
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"vina score failed: {out.stderr[-300:]}")
    for line in out.stdout.splitlines():
        if line.startswith("SCORE:"):
            raw = line.replace("SCORE:", "").strip().strip("[]").split()
            return float(raw[0])
    raise RuntimeError(f"no score in output: {out.stdout[-200:]}")


PDBQT_TREE_HEAD = ["REMARK  crystal pose (fixed, rigid)\n", "ROOT\n"]
PDBQT_TREE_TAIL = ["ENDROOT\n", "TORSDOF 0\n"]


def crystal_pose_pdbqt_tree(pdb_path, code, chain, out_pdbqt):
    """Crystal-pose rigid ligand in the single-ROOT tree form Vina accepts.

    Chain/resSeq selection must match ligand_centroid_one: same chain, same copy.
    """
    from collections import Counter
    txt = [l for l in open(pdb_path)
           if l.startswith("HETATM") and l[17:20].strip() == code
           and (not chain or l[21].strip() == chain)]
    if not txt:
        raise RuntimeError(f"no {code}")
    if not chain:
        chain = Counter(l[21] for l in txt).most_common(1)[0][0]
    sub = [l for l in txt if l[21] == chain]
    res = Counter(l[22:26] for l in sub).most_common(1)[0][0]
    inst = [l for l in sub if l[22:26] == res]
    TYPE = {"C": "C", "N": "N", "O": "OA", "S": "SA", "P": "P", "F": "F",
            "CL": "Cl", "BR": "Br"}
    atoms, i = [], 0
    for l in inst:
        el = l[76:78].strip().upper()
        if el == "H":
            continue
        t = TYPE.get(el, "C")
        i += 1
        atoms.append(
            "ATOM  {:5d}  X   UNL     1    {:8.3f}{:8.3f}{:8.3f}"
            "  0.00  0.00    +0.000 {:<2s} \n".format(
                i, float(l[30:38]), float(l[38:46]), float(l[46:54]), t))
    Path(out_pdbqt).write_text("".join(PDBQT_TREE_HEAD + atoms + PDBQT_TREE_TAIL))
    return len(atoms)


def ligand_centroid_one(pdb_path, code, chain):
    """Centroid of a SINGLE copy (chain-specific); falls back to first resSeq group."""
    from collections import Counter
    txt = [l for l in open(pdb_path)
           if l.startswith("HETATM") and l[17:20].strip() == code
           and (not chain or l[21].strip() == chain)]
    if not txt:
        raise RuntimeError(f"no {code}")
    # group by CHAIN first (a chain may host several ligand copies with same resSeq
    # across symmetry mates); take the largest chain, then its largest resSeq group
    if not chain:
        chain = Counter(l[21] for l in txt).most_common(1)[0][0]
    sub = [l for l in txt if l[21] == chain]
    res = Counter(l[22:26] for l in sub).most_common(1)[0][0]
    inst = [l for l in sub if l[22:26] == res]
    n = len(inst)
    return (sum(float(l[30:38]) for l in inst) / n,
            sum(float(l[38:46]) for l in inst) / n,
            sum(float(l[46:54]) for l in inst) / n)


def run_pocket(pdb, label, lig, drop):
    code, chain = (lig, "") if isinstance(lig, str) else lig
    pdb_path = m.fetch(pdb)
    center = ligand_centroid_one(pdb_path, code, chain if chain else None)
    rec = OUT / f"f2_{pdb}_rec.pdb"
    m.clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
    rec_pdbqt = OUT / f"f2_{pdb}_rec.pdbqt"
    m.prep_pdbqt(str(rec), str(rec_pdbqt))
    res = {"label": label, "pdb": pdb, "pocket_ligand": code, "center": center}
    # crystal pose score (grid centered on the crystal ligand itself)
    ctrl = OUT / f"f2_{pdb}_crystal.pdbqt"
    n_at = crystal_pose_pdbqt_tree(pdb_path, code, chain, ctrl)
    res["crystal_pose_atoms"] = n_at
    # for large channel ligands the 24 A box may not cover the whole molecule;
    # score with box centered per-ligand-extent: center on ligand, size 30
    sc = vina_score_only(str(rec_pdbqt), str(ctrl), center, box=30)
    res["crystal_pose_score"] = round(sc, 2)
    res["gate_pass"] = bool(sc < -6.0)
    # emapunil docking
    emap = OUT / "lig_emapunil.pdbqt"
    if not emap.exists():
        m.prep_ligand(m.EMAPUNIL, str(emap))
    de = OUT / f"f2_{pdb}_emapunil4_docked.pdbqt"
    se = m.run_vina(str(rec_pdbqt), str(emap), center, str(de), exhaustiveness=32)
    res["emapunil_score"] = se[0]
    cene = m.pose_centroid(de)
    res["emapunil_in_pocket_A"] = round(m.dist(cene, center), 2)
    res["eligible_for_FEP"] = bool(res["gate_pass"] and res["emapunil_in_pocket_A"] < 3.0)
    return res


if __name__ == "__main__":
    import emapunil_f2_docking_campaign as mm
    jobs = [p for p in mm.POCKETS if p[0] in ("1XVP", "2QNV", "6X3X", "6HUG")]
    results = {}
    for pdb, label, lig, drop in jobs:
        print(f"=== {pdb} {label} ===", flush=True)
        try:
            res = run_pocket(pdb, label, lig, drop)
        except Exception as e:
            import traceback
            traceback.print_exc()
            res = {"label": label, "error": f"{type(e).__name__}: {e}"}
        results[pdb] = res
        print(json.dumps({k: v for k, v in res.items() if k != "center"}, default=str), flush=True)
    path = OUT / "emapunil_f2_docking.json"
    allr = json.load(open(path))
    allr.update(results)
    json.dump(allr, open(path, "w"), indent=1)
    print("merged")
