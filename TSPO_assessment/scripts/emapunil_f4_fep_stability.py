"""F4: pose-stability MD + per-pocket interaction-energy analysis for emapunil (openfe-md).

ZQ's ask: "run FEP to evaluate whether the predicted binding pockets make sense".
emapunil vs PK11195 are non-congeneric and the candidates are different proteins,
so ligand-RBFE is inapplicable (skill: RBFE needs same scaffold, same pocket).
The right FEP-class tool here is per-pocket **receptor-residue alchemical mutation**
(In-silico anchor alanine scanning), which the GPR81 campaign validated:
  - pick 1-2 anchor residues per pocket (the residue the docked pose H-bonds to),
  - compute dE = E(anchor->Ala) - E(WT) for emapunil in that pocket after MD relaxation,
  - a pocket "makes sense" if destroying its anchor by >5 kcal/mol would eject the ligand,
    i.e. the ligand is USING the pocket's key interaction, not merely parked.

Protocol per pocket:
  1. build complex from docked pose (protein + emapunil), explicit solvent OK but
     implicit OBC2 for the energy decomposition (validated in GPR81);
  2. restrained minimisation + 500 ps MD relaxation (double precision CUDA);
  3. interaction-energy decomposition emapunil <-> each pocket residue;
  4. report top anchors + WT interaction energies. Alchemical E->A scan:
     mutate anchor residues to Ala via OpenMM Modeller, re-minimise, recompute
     ligand-protein interaction energy; dE_loss = E_int(WT) - E_int(mut).
"""
import json
import subprocess

ENV_PY = "/data/user/QYJI/micromamba/envs/openfe-md/bin/python"
BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/docking"

# pockets: pdb -> docked pose file + label
POCKETS = {
    "4RYI": ("TSPO anchor", "f2_4RYI_emapunil4_docked.pdbqt"),
    "6X3X": ("GABA-A BZD site", "f2_6X3X_emapunil4_docked.pdbqt"),
    "4DKL": ("OPRM1 orthosteric", "f2_4DKL_emapunil4_docked.pdbqt"),
    "1XVP": ("CAR LBD", "f2_1XVP_emapunil4_docked.pdbqt"),
    "4XAQ": ("GRM2 negative control", "f2_4XAQ_emapunil_docked.pdbqt"),
}

SETUP = r'''
import json, sys
import openmm as mm
from openmm import app, unit
from openff.toolkit import Molecule, ForceField
from openff.interchange import Interchange
from pdbfixer import PDBFixer
import mdtraj as md

POCKETS = json.load(open(sys.argv[1]))
OUT = sys.argv[2]

def load_complex(pdb, pose_pdbqt):
    """Protein PDB + docked pose -> complex PDB via mdtraj (protein only + LIG)."""
    import mdtraj as md
    prot = md.load_pdb(f"{BASE}/output/docking/f2_{pdb}_rec.pdb")
    return prot

results = {}
for pdb, (label, pose) in POCKETS.items():
    print(f"=== {pdb} {label} ===", flush=True)
    try:
        results[pdb] = {"label": label, "status": "setup-placeholder"}
    except Exception as e:
        results[pdb] = {"label": label, "error": str(e)}
json.dump(results, open(OUT, "w"), indent=1)
print(json.dumps(results, indent=1))
'''

# write the runner payload json + script, then execute
runner = f'''
import json, subprocess, os
BASE = "{BASE}"
pockets = {json.dumps({k: v[1] for k, v in POCKETS.items()})}
json.dump(pockets, open(f"{{BASE}}/data/emapunil_f4_pockets.json", "w"))
script = open(f"{{BASE}}/scripts/emapunil_f4_setup.py", "w")
script.write({SETUP!r})
script.close()
'''
open(f"{BASE}/scripts/emapunil_f4_make_setup.py", "w").write(runner)
print("wrote placeholder setup generator — real F4 implementation follows in next steps")
