"""F2c: redock controls for the 5 remaining pockets with coordinates preserved.

Robust path learned from the 4RYI debugging:
  - extract ONE ligand instance (first resSeq) HETATM lines;
  - obabel pdb -> mol2 (Gasteiger, coords preserved) -> pdbqt (full torsion tree);
  - truncate duplicate trees after first TORSDOF;
  - verify centroid preservation (input HETATM centroid vs converted ATOM centroid) < 0.5 A.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
import emapunil_f2_docking_campaign as m

OUT = m.OUT


def prep_ctrl_keepcoords(pdb_path, code, chain, out_pdbqt):
    """HETATM -> SDF (bond perception, coords kept) -> RDKit sanitise -> meeko PDBQT.

    obabel's mol2->pdbqt fragments large flexible ligands (CID 54 atoms -> 2);
    meeko is the reliable writer. Coordinates preserved because the SDF carries
    the original crystal frame.
    """
    import tempfile
    from rdkit import Chem
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    txt = [l for l in open(pdb_path)
           if l.startswith("HETATM") and l[17:20].strip() == code
           and (not chain or l[21].strip() == chain)]
    if not txt:
        raise RuntimeError(f"no HETATM {code}")
    from collections import Counter
    resn = Counter(l[22:26] for l in txt).most_common(1)[0][0]
    inst = [l for l in txt if l[22:26] == resn]
    n = len(inst)
    cen_in = (sum(float(l[30:38]) for l in inst) / n,
              sum(float(l[38:46]) for l in inst) / n,
              sum(float(l[46:54]) for l in inst) / n)
    t = tempfile.NamedTemporaryFile("w", suffix=".pdb", delete=False)
    t.write("".join(inst))
    t.close()
    sdf = str(out_pdbqt).replace(".pdbqt", ".sdf")
    subprocess.run(["obabel", t.name, "-O", sdf], capture_output=True, text=True)
    Path(t.name).unlink()
    mol = Chem.SDMolSupplier(sdf, removeHs=False)[0]
    if mol is None:
        raise RuntimeError(f"RDKit cannot read SDF for {code}")
    # bond perception from raw PDB can miss orders -> disconnected fragments.
    # Keep the largest fragment (main ligand body), drop co-crystallised ions/waters.
    frags = Chem.GetMolFrags(mol, asMols=True)
    if len(frags) > 1:
        mol = max(frags, key=lambda fm: fm.GetNumAtoms())
    try:
        Chem.SanitizeMol(mol)
    except Exception:
        pass
    prep = MoleculePreparation()
    setups = prep.prepare(Chem.AddHs(mol))
    with open(out_pdbqt, "w") as fh:
        fh.write(PDBQTWriterLegacy.write_string(setups[0])[0])
    atoms = [l for l in open(out_pdbqt) if l.startswith(("ATOM", "HETATM"))]
    if not atoms:
        raise RuntimeError(f"meeko wrote no atoms for {code}")
    na = len(atoms)
    cen_out = (sum(float(l[30:38]) for l in atoms) / na,
               sum(float(l[38:46]) for l in atoms) / na,
               sum(float(l[46:54]) for l in atoms) / na)
    shift = sum((a - b) ** 2 for a, b in zip(cen_in, cen_out)) ** 0.5
    return shift, n, na


def run_pocket(pdb, label, lig, drop):
    code, chain = (lig, "") if isinstance(lig, str) else lig
    pdb_path = m.fetch(pdb)
    center = m.ligand_centroid(str(pdb_path), code, chain if chain else None)
    rec = OUT / f"f2_{pdb}_rec.pdb"
    m.clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
    rec_pdbqt = OUT / f"f2_{pdb}_rec.pdbqt"
    m.prep_pdbqt(str(rec), str(rec_pdbqt))
    res = {"label": label, "pdb": pdb, "pocket_ligand": code, "center": center}
    ctrl = OUT / f"f2_{pdb}_ctrl3.pdbqt"
    shift, n_in, n_out = prep_ctrl_keepcoords(pdb_path, code, chain, ctrl)
    res["ctrl_centroid_shift_A"] = round(shift, 2)
    res["ctrl_atoms_in_out"] = [n_in, n_out]
    docked = OUT / f"f2_{pdb}_ctrl3_docked.pdbqt"
    scores = m.run_vina(str(rec_pdbqt), str(ctrl), center, str(docked), exhaustiveness=32)
    res["redock_score"] = scores[0]
    cen = m.pose_centroid(docked)
    res["redock_recovery_A"] = round(m.dist(cen, center), 2)
    emap = OUT / "lig_emapunil.pdbqt"
    if not emap.exists():
        m.prep_ligand(m.EMAPUNIL, str(emap))
    de = OUT / f"f2_{pdb}_emapunil3_docked.pdbqt"
    se = m.run_vina(str(rec_pdbqt), str(emap), center, str(de), exhaustiveness=32)
    res["emapunil_score"] = se[0]
    cene = m.pose_centroid(de)
    res["emapunil_in_pocket_A"] = round(m.dist(cene, center), 2)
    res["eligible_for_FEP"] = bool(res["redock_recovery_A"] < 3.0
                                   and res["emapunil_in_pocket_A"] < 3.0
                                   and shift < 0.5)
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
