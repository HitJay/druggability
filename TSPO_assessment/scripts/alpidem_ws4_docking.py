"""WS4: alpidem gated Vina arm — TSPO positive control + PXR (+ CAR recovery check).

Reuses ws2b_validation_gate helpers and the pocket set from the RIC-408 run:
  4RYI  TSPO co-crystal (positive control; must reproduce ~ -9.4 kcal/mol)
  2QNV  PXR LBD (PubChem-measured PXR agonism 0.19-0.48 uM -> recovery expected)
  1XVP  CAR LBD (negative control here; PK11195 docked -10.9 previously)
Zolpidem is the differentiation comparator (should prefer GABA-A over TSPO;
GABA-A is an oligomeric channel — not dockable in this arm, documented as a limit).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import (
    STRUCT, OUT, prep_ligand, run_vina, clean_receptor, prep_pdbqt, ligand_centroid)

LIGANDS = {
    "alpidem":  "CCCN(CCC)C(=O)CC1=C(N=C2N1C=C(C=C2)Cl)C3=CC=C(C=C3)Cl",
    "zolpidem": "CC1=CC=C(C=C1)C2=C(N3C=C(C=CC3=N2)C)CC(=O)N(C)C",
}
# (pdb, co-crystal ligand code, chain, drop chains)
RECEPTORS = [("4RYI", "PKA", "A", ()), ("2QNV", "CDZ", "A", ()),
             ("1XVP", "CID", "D", ("A", "C", "B", "E", "F"))]

results = {}
for pdb, ligcode, chain, drop in RECEPTORS:
    pdb_path = STRUCT / f"{pdb}.pdb"
    if not pdb_path.exists():
        subprocess_run = __import__("subprocess").run(
            ["curl", "-sS", "--max-time", "90", "-o", str(pdb_path),
             f"https://files.rcsb.org/download/{pdb}.pdb"], capture_output=True, text=True)
        print(f"downloaded {pdb}: rc={subprocess_run.returncode}")
    center = ligand_centroid(str(pdb_path), ligcode, chain)
    print(f"{pdb} pocket center: {center}")
    rec = OUT / f"{pdb}_rec.pdb"
    clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
    rec_pdbqt = OUT / f"{pdb}_rec.pdbqt"
    prep_pdbqt(str(rec), str(rec_pdbqt))
    for name, smi in LIGANDS.items():
        tag = f"{pdb}_{name}"
        lig_pdbqt = OUT / f"lig_{name}.pdbqt"
        if not lig_pdbqt.exists():
            prep_ligand(smi, str(lig_pdbqt))
        docked = OUT / f"alpidem_{tag}_docked.pdbqt"
        scores = run_vina(str(rec_pdbqt), str(lig_pdbqt), center, str(docked))
        results[tag] = {"center": center, "scores": scores}
        print(f"{tag:28s} {scores[0]:.2f}  (poses: {scores})", flush=True)

json.dump(results, open(OUT / "alpidem_ws4_docking.json", "w"), indent=1)
print("saved alpidem_ws4_docking.json")
