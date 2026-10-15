"""WS2e: GABA-A picrotoxin-site docking (6HUG, human alpha1beta3gamma2L, PIO co-crystal).

Pre-registered hypotheses:
  - etifoxine is the known channel ligand (IC50 6.7 uM TBPS displacement) ->
    should dock into the PIO site and outscore PK11195/emapunil there.
  - PK11195/emapunil (central benzodiazepine site ligands) should NOT bind the
    picrotoxin site strongly.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import (
    prep_ligand, run_vina, clean_receptor, prep_pdbqt, ligand_centroid)

STRUCT = Path("/das/user/QYJI/druggability/TSPO_assessment/structures")
OUT = Path("/das/user/QYJI/druggability/TSPO_assessment/output/docking")

LIGANDS = {
    "etifoxine": "CCN(CC)C(=O)c1cc(Cl)ccc1NC(C)=O",
    "PK11195": "CCC(C)N(C)C(=O)c1cc2cccc(-c3ccccc3Cl)c2cn1",
    "emapunil": "CCN1C(=O)N(C)c2cc(Cl)ccc2N=C1c1ccccc1",
    "Ro5-4864": "CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=C(C=C3)Cl",
}


def main():
    pdb = "6HUG"
    pdb_path = STRUCT / f"{pdb}.pdb"
    # keep all protein chains (heteropentamer), drop glycans/waters/other ligands
    rec = OUT / f"{pdb}_rec.pdb"
    clean_receptor(str(pdb_path), str(rec))
    rec_pdbqt = OUT / f"{pdb}_rec.pdbqt"
    prep_pdbqt(str(rec), str(rec_pdbqt))
    center = ligand_centroid(str(pdb_path), "PIO", "D")
    print("pocket center:", [round(c, 2) for c in center], flush=True)
    results = {}
    for name, smi in LIGANDS.items():
        lig = OUT / f"lig_{name}.pdbqt"
        if not lig.exists():
            prep_ligand(smi, str(lig))
        docked = OUT / f"{pdb}_{name}_docked.pdbqt"
        scores = run_vina(str(rec_pdbqt), str(lig), center, str(docked), size=24)
        results[name] = scores
        print(f"{name:12s} {scores[0]:.2f}  {scores}", flush=True)
    json.dump({"pocket": "GABA-A picrotoxin site (6HUG PIO D)", "results": results},
              open(OUT / "ws2e_gabaa_matrix.json", "w"), indent=1)


if __name__ == "__main__":
    main()
