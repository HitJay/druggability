"""F2-fix: re-run the 4 fixed-ligand pockets with CO-CRYSTAL LIGAND coordinates preserved
(no SDF 3D re-generation) so redock controls validate the pocket.

Root cause of the bad recovery distances: obabel re-generated 3D coordinates from the
SDF in a local frame, so the redock 'control' ligand no longer sat in the pocket.
Fix: keep original HETATM coordinates -> write MOL2-free path: use openbabel with
'--gen3d none'? Simplest robust route: convert extracted PDB to pdbqt with
obabel keeping coordinates (default keeps coords when input has them; the earlier
multi-ROOT issue came from SDF round-trip). Here: pdb -> mol2 -> pdbqt, then verify
the first ATOM coordinate matches the original HETATM coordinate.
"""
import sys, json
sys.path.insert(0, "scripts")
import emapunil_f2_docking_campaign as m
from pathlib import Path
import subprocess, tempfile

OUT = m.OUT


def prep_ligand_from_pdb_keepcoords(pdb_path, code, chain, out_pdbqt):
    txt = [l for l in open(pdb_path)
           if l.startswith("HETATM") and l[17:20].strip() == code
           and (not chain or l[21].strip() == chain)]
    if not txt:
        raise RuntimeError(f"no HETATM {code}")
    # keep only the first copy (one instance of the ligand)
    resn = txt[0][22:26]
    txt = [l for l in txt if l[22:26] == resn]
    t = tempfile.NamedTemporaryFile("w", suffix=".pdb", delete=False)
    t.write("".join(txt)); t.close()
    mol2 = str(out_pdbqt).replace(".pdbqt", ".mol2")
    subprocess.run(["obabel", t.name, "-O", mol2], capture_output=True, text=True)
    r = subprocess.run(["obabel", mol2, "-O", str(out_pdbqt)], capture_output=True, text=True)
    # truncate duplicate trees
    lines = open(out_pdbqt).readlines()
    keep, seen = [], 0
    for line in lines:
        if line.startswith("TORSDOF"):
            seen += 1
            if seen == 1:
                keep.append(line)
            continue
        if seen >= 1:
            break
        keep.append(line)
    open(out_pdbqt, "w").writelines(keep)
    # verify coordinate preservation
    orig = (float(txt[0][30:38]), float(txt[0][38:46]), float(txt[0][46:54]))
    conv = open(out_pdbqt).readlines()
    atom = next(l for l in conv if l.startswith("ATOM") or l.startswith("HETATM"))
    got = (float(atom[30:38]), float(atom[38:46]), float(atom[46:54]))
    d = sum((a-b)**2 for a, b in zip(orig, got)) ** 0.5
    print(f"  coord preservation {code}: {d:.2f} A")
    return d


results = {}
for pdb, label, lig, drop in [p for p in m.POCKETS if p[0] in ("4RYI", "1XVP", "2QNV", "6X3X", "6HUG")]:
    print(f"=== {pdb} {label} ===", flush=True)
    try:
        code, chain = (lig, "") if isinstance(lig, str) else lig
        pdb_path = m.fetch(pdb)
        center = m.ligand_centroid(str(pdb_path), code, chain if chain else None)
        rec = OUT / f"f2_{pdb}_rec.pdb"
        m.clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
        rec_pdbqt = OUT / f"f2_{pdb}_rec.pdbqt"
        m.prep_pdbqt(str(rec), str(rec_pdbqt))
        res = {"label": label, "pdb": pdb, "pocket_ligand": code, "center": center}
        ctrl = OUT / f"f2_{pdb}_ctrl2.pdbqt"
        prep_ligand_from_pdb_keepcoords(pdb_path, code, chain, ctrl)
        docked = OUT / f"f2_{pdb}_ctrl2_docked.pdbqt"
        scores = m.run_vina(str(rec_pdbqt), str(ctrl), center, str(docked), exhaustiveness=32)
        res["redock_score"] = scores[0]
        cen = m.pose_centroid(docked)
        res["redock_recovery_A"] = round(m.dist(cen, center), 2)
        emap = OUT / "lig_emapunil.pdbqt"
        if not emap.exists():
            m.prep_ligand(m.EMAPUNIL, str(emap))
        de = OUT / f"f2_{pdb}_emapunil_docked.pdbqt"
        se = m.run_vina(str(rec_pdbqt), str(emap), center, str(de), exhaustiveness=32)
        res["emapunil_score"] = se[0]
        cene = m.pose_centroid(de)
        res["emapunil_in_pocket_A"] = round(m.dist(cene, center), 2)
        res["eligible_for_FEP"] = bool(res["redock_recovery_A"] < 3.0 and res["emapunil_in_pocket_A"] < 3.0)
    except Exception as e:
        import traceback; traceback.print_exc()
        res = {"label": label, "error": f"{type(e).__name__}: {e}"}
    results[pdb] = res
    print(json.dumps({k: v for k, v in res.items() if k != "center"}, default=str), flush=True)

path = OUT / "emapunil_f2_docking.json"
allr = json.load(open(path))
allr.update(results)
json.dump(allr, open(path, "w"), indent=1)
print("merged")
