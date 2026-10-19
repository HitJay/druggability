"""WS4b: alpidem GABA-A BZD-site docking (6X3X chain E, diazepam co-crystal).

Pre-registered hypotheses:
  - alpidem must dock into the diazepam pocket strongly (positive control).
  - zolpidem (clinically used BZD-site agonist) should score comparably.
  - PK11195 (known BZD-site ligand at uM) should be present but weaker than alpidem.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import (
    STRUCT, OUT, prep_ligand, run_vina, clean_receptor, prep_pdbqt, ligand_centroid)

STRUCT = Path("/das/user/QYJI/druggability/TSPO_assessment/structures")
OUT = Path("/das/user/QYJI/druggability/TSPO_assessment/output/docking")

LIGANDS = {
    "alpidem":  "CCCN(CCC)C(=O)CC1=C(N=C2N1C=C(C=C2)Cl)C3=CC=C(C=C3)Cl",
    "zolpidem": "CC1=CC=C(C=C1)C2=C(N3C=C(C=CC3=N2)C)CC(=O)N(C)C",
    "PK11195":  "CCC(C)N(C)C(=O)c1cc2cccc(-c3ccccc3Cl)c2cn1",
}


def main():
    pdb = "6X3X"
    pdb_path = STRUCT / f"{pdb}.pdb"
    if not pdb_path.exists():
        r = subprocess.run(["curl", "-sS", "--max-time", "120", "-o", str(pdb_path),
                            f"https://files.rcsb.org/download/{pdb}.pdb"],
                           capture_output=True, text=True)
        print(f"download {pdb}: rc={r.returncode}, size={pdb_path.stat().st_size if pdb_path.exists() else 0}")
    center = ligand_centroid(str(pdb_path), "DZP", "E")
    print("BZD-site pocket center (6X3X DZP E):", [round(c, 2) for c in center], flush=True)
    rec = OUT / f"{pdb}_rec.pdb"
    clean_receptor(str(pdb_path), str(rec))
    rec_pdbqt = OUT / f"{pdb}_rec.pdbqt"
    prep_pdbqt(str(rec), str(rec_pdbqt))
    results = {}
    for name, smi in LIGANDS.items():
        lig = OUT / f"lig_{name}.pdbqt"
        if not lig.exists():
            prep_ligand(smi, str(lig))
        docked = OUT / f"alpidem_{pdb}_{name}_docked.pdbqt"
        scores = run_vina(str(rec_pdbqt), str(lig), center, str(docked), size=24)
        results[name] = scores
        print(f"{name:12s} {scores[0]:.2f}  {scores}", flush=True)
    json.dump({"pocket": "GABA-A benzodiazepine site (6X3X 8AI chain E)", "results": results},
              open(OUT / "alpidem_ws4b_gabaa_matrix.json", "w"), indent=1)


if __name__ == "__main__":
    main()
