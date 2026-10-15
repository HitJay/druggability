"""WS2b validation-gate docking: PK11195 vs TSPO(4RYI)/CAR(1XVP chainD)/PXR(2QNV).

Receptor prep: strip waters/ions/ligands, keep protein; re-dock PK11195 into
each co-crystal pocket; compare score to the off-target threshold band.
"""
import subprocess, tempfile, os, sys
from pathlib import Path

VENV = "/home/QYJI/das/druggability/.venv/bin/python"
STRUCT = Path("/das/user/QYJI/druggability/TSPO_assessment/structures")
OUT = Path("/das/user/QYJI/druggability/TSPO_assessment/output/docking")
OUT.mkdir(parents=True, exist_ok=True)

PK_SMILES = "CCC(C)N(C)C(=O)c1cc2cccc(-c3ccccc3Cl)c2cn1"

# pocket centres from co-crystal ligand centroids (computed below)
LIGS = {"4RYI": "PKA", "1XVP": "CID", "2QNV": "CDZ"}


def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[:80]} failed: {r.stderr[-400:]}")
    return r.stdout


def ligand_centroid(pdb_path, ligcode, chain):
    xs, ys, zs = [], [], []
    for line in open(pdb_path):
        if line.startswith("HETATM") and line[17:20].strip() == ligcode and line[21] == chain:
            xs.append(float(line[30:38])); ys.append(float(line[38:46])); zs.append(float(line[46:54]))
    if not xs:
        raise RuntimeError(f"no {ligcode} chain {chain} in {pdb_path}")
    n = len(xs)
    return (sum(xs)/n, sum(ys)/n, sum(zs)/n)


def clean_receptor(pdb_path, out_path, drop_chains=()):
    keep = []
    dropped_chains = set(drop_chains)
    for line in open(pdb_path):
        if line.startswith(("ATOM", "HETATM")):
            if line[:6].startswith("HETATM"):
                continue  # drop all hetero incl ligands/waters
            chain = line[21]
            if chain in dropped_chains:
                continue
            keep.append(line)
        elif line.startswith(("TER", "END")):
            keep.append(line)
    Path(out_path).write_text("".join(keep))
    return out_path


def prep_pdbqt(pdb_path, pdbqt_path):
    sh(f"{VENV} -c \"import sys; sys.argv=['prepare_receptor']\" 2>/dev/null; true")
    # use obabel for receptor->pdbqt (adds polar H, partial charges)
    sh(f"/home/QYJI/das/druggability/.venv/bin/obabel {pdb_path} -O {pdbqt_path} -xr")
    return pdbqt_path


def prep_ligand(smiles, pdbqt_path):
    sh(f"/home/QYJI/das/druggability/.venv/bin/obabel -:'{smiles}' -O {pdbqt_path} --gen3d -h")
    return pdbqt_path


def run_vina(rec_pdbqt, lig_pdbqt, center, out_pdbqt, size=22, exhaustiveness=16, seed=42):
    cmd = (f"{VENV} -c \"from vina import Vina; "
           f"v=Vina(sf_name='vina'); "
           f"v.set_receptor('{rec_pdbqt}'); "
           f"v.set_ligand_from_file('{lig_pdbqt}'); "
           f"v.compute_vina_maps(center=[{center[0]:.2f},{center[1]:.2f},{center[2]:.2f}], box_size=[{size},{size},{size}]); "
           f"v.dock(exhaustiveness={exhaustiveness}, n_poses=5); "
           f"v.write_poses('{out_pdbqt}', n_poses=5, overwrite=True); "
           f"print('SCORES:', ' '.join(f'{{s[0]:.2f}}' for s in v.energies(n_poses=5)))\"")
    out = sh(cmd)
    tail = out.split("SCORES:")[1]
    tail = tail.split("\n")[0]          # vina also prints a human table after our line
    scores = [float(x) for x in tail.split()]
    return scores


def rmsd_to_cocrystal(docked_pdbqt, ref_ligand_lines):
    # crude best-pose RMSD on common heavy atoms (no symmetry): min over poses
    import math
    def parse(pdbqt):
        poses, cur = [], []
        for line in open(pdbqt):
            if line.startswith("MODEL"):
                cur = []
            elif line.startswith(("ATOM", "HETATM")) and not line[77:79].strip() == "HD":
                if line[12:16].strip().startswith("H"):
                    continue
                cur.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            elif line.startswith("ENDMDL"):
                if cur: poses.append(cur)
        if cur and not poses: poses.append(cur)
        return poses
    ref = []
    for line in ref_ligand_lines:
        ref.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
    best = None
    for pose in parse(docked_pdbqt):
        n = min(len(pose), len(ref))
        if n == 0: continue
        # naive index alignment (same mol, deterministic 3D gen)
        r = math.sqrt(sum((pose[i][0]-ref[i][0])**2 + (pose[i][1]-ref[i][1])**2 + (pose[i][2]-ref[i][2])**2 for i in range(n)) / n)
        if best is None or r < best: best = r
    return best


def main():
    results = {}
    lig_mol2 = OUT / "pk11195.pdbqt"
    prep_ligand(PK_SMILES, str(lig_mol2))
    for pdb, ligcode in LIGS.items():
        pdb_path = STRUCT / f"{pdb}.pdb"
        # chain of the ligand
        chain = None
        for line in open(pdb_path):
            if line.startswith("HETATM") and line[17:20].strip() == ligcode:
                chain = line[21]; break
        center = ligand_centroid(str(pdb_path), ligcode, chain)
        rec = OUT / f"{pdb}_rec.pdb"
        # for 1XVP drop RXR chains A,C (keep CAR=D); map: CAR is chain D per earlier scan
        drop = ("A", "C", "B", "E", "F") if pdb == "1XVP" else ()
        clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
        rec_pdbqt = OUT / f"{pdb}_rec.pdbqt"
        prep_pdbqt(str(rec), str(rec_pdbqt))
        docked = OUT / f"{pdb}_docked.pdbqt"
        scores = run_vina(str(rec_pdbqt), str(lig_mol2), center, str(docked))
        # redock RMSD for 4RYI (PK11195 co-crystal = validation)
        rmsd = None
        if ligcode == "PKA":
            ref = [l for l in open(pdb_path) if l.startswith("HETATM") and l[17:20].strip() == "PKA" and l[21] == chain]
            rmsd = rmsd_to_cocrystal(str(docked), ref)
        results[pdb] = {"pocket_center": [round(c, 2) for c in center], "chain": chain,
                        "vina_scores": scores, "redock_rmsd": round(rmsd, 2) if rmsd else None}
        print(pdb, "chain", chain, "scores", scores, "rmsd", rmsd)
    import json
    json.dump(results, open(OUT / "validation_gate_results.json", "w"), indent=1)
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
