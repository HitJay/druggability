"""WS2b DrugCLIP reverse retrieval (ligand -> pocket library).

Driver: builds pocket LMDB (candidate target pockets) + ligand LMDB (4 seeds +
3 decoys) with the wrapper helpers, then runs scripts/reverse_retrieve_dcvenv.py
inside the drugclip venv (official encoders), and ranks pockets per ligand by
transposing the cosine matrix.
"""
import json, pickle, subprocess, sys
from pathlib import Path

import numpy as np

PROJ = Path("/das/user/QYJI/druggability")
sys.path.insert(0, str(PROJ / "src"))
from druggability.drugclip import (
    extract_pocket_from_pdb, write_pocket_lmdb, parse_pdb_atoms)

DC = PROJ / "output/2026-07-02/drugclip_install_probe/DrugCLIP"
CKPT = PROJ / "output/2026-07-02/drugclip_install_probe/checkpoints/drugclip_data/checkpoint_best.pt"
DCPY = "/data/user/QYJI/venvs/drugclip/bin/python"
WORK = PROJ / "TSPO_assessment/output/drugclip_reverse"
WORK.mkdir(parents=True, exist_ok=True)

LIGS = {
    "PK11195": "CCC(C)N(C)C(=O)c1cc2cccc(-c3ccccc3Cl)c2cn1",
    "emapunil": "CCN1C(=O)N(C)c2cc(Cl)ccc2N=C1c1ccccc1",
    "etifoxine": "CCN(CC)C(=O)c1cc(Cl)ccc1NC(C)=O",
    "Ro5-4864": "CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=C(C=C3)Cl",
    "decoy_lisinopril": "NCCCCC(N)C(=O)N1CCCC(C(=O)O)CC1C(=O)O",
    "decoy_glycine": "NCC(=O)O",
    "decoy_aspirin": "CC(=O)Oc1ccccc1C(=O)O",
}

POCKETS = [
    ("TSPO_4RYI", "4RYI", "PKA", "A"),
    ("CAR_1XVP_D", "1XVP", "CID", "D"),
    ("PXR_2QNV_A", "2QNV", "CDZ", "A"),
]
OBABEL = "/home/QYJI/das/druggability/.venv/bin/obabel"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FAIL: {cmd[:120]}\n{r.stderr[-600:]}")
    return r.stdout


def lig_pdb(pdb, ligcode, chain):
    src = PROJ / f"TSPO_assessment/structures/{pdb}.pdb"
    out = WORK / f"ref_{pdb}_{ligcode}.pdb"
    lines = [l for l in open(src) if l.startswith("HETATM")
             and l[17:20].strip() == ligcode and l[21] == chain]
    out.write_text("".join(lines))
    return str(out)


def write_mol_lmdb(entries, out_path):
    import lmdb
    env = lmdb.open(str(out_path), subdir=False, map_size=1 << 30)
    with env.begin(write=True) as txn:
        for i, (name, atoms, coords) in enumerate(entries):
            txn.put(str(i).encode(), pickle.dumps({
                "smi": name,
                "atoms": atoms,
                "coordinates": np.asarray(coords, dtype=np.float32)[np.newaxis, ...],
            }))
    env.close()
    return Path(out_path)


def write_all_pockets(pocket_dicts, out_path):
    import lmdb
    p = Path(out_path)
    if p.exists():
        p.unlink()
    env = lmdb.open(str(p), subdir=False, map_size=1 << 30)
    with env.begin(write=True) as txn:
        for i, d in enumerate(pocket_dicts):
            txn.put(str(i).encode(), pickle.dumps(d))
    env.close()
    return p


def main():
    # 1) pockets
    pocket_dicts = []
    for name, pdb, lig, chain in POCKETS:
        pdb_path = PROJ / f"TSPO_assessment/structures/{pdb}.pdb"
        d = extract_pocket_from_pdb(str(pdb_path), ligand_pdb=lig_pdb(pdb, lig, chain),
                                    radius=8.0, pocket_name=name)
        print(name, "pocket atoms:", len(d["pocket_atoms"]))
        pocket_dicts.append(d)
    pockets_lmdb = write_all_pockets(pocket_dicts, WORK / "pockets.lmdb")

    # 2) ligands
    mol_entries = []
    for name, smi in LIGS.items():
        pdb = WORK / f"mol_{name}.pdb"
        sh(f"{OBABEL} -:'{smi}' -O {pdb} --gen3d -h")
        atoms, coords, _ = parse_pdb_atoms(str(pdb))
        mol_entries.append((name, atoms, coords))
        print("mol3d ok:", name, len(atoms), "atoms")
    mols_lmdb = write_mol_lmdb(mol_entries, WORK / "ligands.lmdb")

    # 3) reverse retrieve in drugclip venv
    emb_dir = WORK / "emb"
    emb_dir.mkdir(exist_ok=True)
    cmd = (f"cd {DC} && CUDA_VISIBLE_DEVICES=0 {DCPY} "
           f"{PROJ}/TSPO_assessment/scripts/reverse_retrieve_dcvenv.py "
           f"./data --user-dir ./unimol --valid-subset test "
           f"--results-path {WORK} --num-workers 4 --ddp-backend=c10d --batch-size 4 "
           f"--task drugclip --loss in_batch_softmax --arch drugclip --max-pocket-atoms 256 "
           f"--fp16 --fp16-init-scale 4 --fp16-scale-window 256 --seed 1 --path {CKPT} "
           f"--log-interval 50 --log-format simple --mol-path {mols_lmdb} "
           f"--pocket-path {pockets_lmdb} --emb-dir {emb_dir} ")
    out = sh(cmd)
    print(out[-1500:])

    # 4) rank pockets per ligand
    with open(emb_dir / "reverse_matrix.pkl", "rb") as f:
        R = pickle.load(f)
    S, mols, pocks = R["S"], R["mol_names"], R["pocket_names"]
    result = {}
    for j, mn in enumerate(mols):
        order = np.argsort(-S[:, j])
        result[mn] = [(pocks[i], round(float(S[i, j]), 4)) for i in order]
    json.dump(result, open(WORK / "reverse_results.json", "w"), indent=1)
    print("\n== ligand -> pocket ranking (cosine) ==")
    for mn, ranked in result.items():
        print(f"{mn:18s} " + "  >  ".join(f"{n}({s:.3f})" for n, s in ranked))


if __name__ == "__main__":
    main()
