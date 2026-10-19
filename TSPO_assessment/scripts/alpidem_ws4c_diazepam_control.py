"""WS4c: diazepam positive control into its own 6X3X pocket (gate completion)."""
import json
import sys

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from ws2b_validation_gate import (
    STRUCT, OUT, prep_ligand, run_vina, ligand_centroid)

center = ligand_centroid(str(STRUCT / "6X3X.pdb"), "DZP", "E")
rec_pdbqt = str(OUT / "6X3X_rec.pdbqt")
lig = OUT / "lig_diazepam.pdbqt"
if not lig.exists():
    prep_ligand("CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=CC=C3", str(lig))
docked = OUT / "alpidem_6X3X_diazepam_docked.pdbqt"
scores = run_vina(rec_pdbqt, str(lig), center, str(docked), size=24)
print(f"diazepam (own co-crystal pocket): {scores[0]:.2f}  {scores}")
json.dump({"diazepam": scores},
          open(OUT / "alpidem_ws4c_diazepam_control.json", "w"), indent=1)
