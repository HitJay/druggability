"""WS2c: extend the validation-gate docking matrix to all ligands x 3 pockets.

Reuses helpers from ws2b_validation_gate. Ligands: emapunil, etifoxine,
Ro5-4864, R-PK11195, S-PK11195 (PK11195 racemate already docked in WS2b).
Hypotheses to test (pre-registered here to avoid HARKing):
  - emapunil should dock strongest into TSPO (selective ligand)
  - etifoxine should be weak everywhere (uM ligand)
  - Ro5-4864 should prefer TSPO over CAR/PXR
  - R-PK11195 should score better than S-PK11195 on TSPO (stereospecificity)
"""
import json, sys
from pathlib import Path

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import (
    STRUCT, OUT, prep_ligand, run_vina, clean_receptor, prep_pdbqt, ligand_centroid)

LIGANDS = {
    "emapunil":  "CCN1C(=O)N(C)c2cc(Cl)ccc2N=C1c1ccccc1",
    "etifoxine": "CCN(CC)C(=O)c1cc(Cl)ccc1NC(C)=O",
    "Ro5-4864":  "CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=C(C=C3)Cl",
    "R-PK11195": "CC[C@@H](C)N(C)C(=O)c1cc2ccccc2c(-c2ccccc2Cl)n1",
    "S-PK11195": "CC[C@H](C)N(C)C(=O)c1cc2ccccc2c(-c2ccccc2Cl)n1",
}
RECEPTORS = [("4RYI", "PKA", "A", ()), ("1XVP", "CID", "D", ("A", "C", "B", "E", "F")), ("2QNV", "CDZ", "A", ())]


def main():
    results = {}
    for pdb, ligcode, chain, drop in RECEPTORS:
        pdb_path = STRUCT / f"{pdb}.pdb"
        center = ligand_centroid(str(pdb_path), ligcode, chain)
        rec = OUT / f"{pdb}_rec.pdb"
        clean_receptor(str(pdb_path), str(rec), drop_chains=drop)
        rec_pdbqt = OUT / f"{pdb}_rec.pdbqt"
        prep_pdbqt(str(rec), str(rec_pdbqt))
        for name, smi in LIGANDS.items():
            tag = f"{pdb}_{name}"
            lig_pdbqt = OUT / f"lig_{name}.pdbqt"
            if not lig_pdbqt.exists():
                prep_ligand(smi, str(lig_pdbqt))
            docked = OUT / f"{tag}_docked.pdbqt"
            scores = run_vina(str(rec_pdbqt), str(lig_pdbqt), center, str(docked))
            results[tag] = {"scores": scores}
            print(f"{tag:24s} {scores[0]:.2f}  (poses: {scores})", flush=True)
    # print matrix
    print("\n== cross matrix (top scores, kcal/mol) ==")
    ligs = list(LIGANDS) + ["PK11195_rac"]
    for pdb, *_ in RECEPTORS:
        row = []
        for name in ligs:
            if name == "PK11195_rac":
                f = OUT / "validation_gate_results.json"
                v = json.loads(f.read_text())[pdb]["vina_scores"][0]
            else:
                v = results[f"{pdb}_{name}"]["scores"][0]
            row.append(f"{name}:{v:.2f}")
        print(pdb, " ".join(row))
    json.dump(results, open(OUT / "ws2c_docking_matrix.json", "w"), indent=1)


if __name__ == "__main__":
    main()
