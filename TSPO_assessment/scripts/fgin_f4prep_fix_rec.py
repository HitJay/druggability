"""F4-prep extension: pdbfixer pass on the 4 additional FGIN-campaign receptors."""
from pdbfixer import PDBFixer
from openmm.app import PDBFile

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
PDBS = ["5TGZ", "4DJH"]

for pdb in PDBS:
    src = f"{BASE}/output/docking/f2_{pdb}_rec.pdb"
    dst = f"{BASE}/output/docking/f2_{pdb}_rec_fixed.pdb"
    try:
        fx = PDBFixer(filename=src)
        fx.findMissingResidues()
        fx.findMissingAtoms()
        n_missing = sum(len(v) for v in fx.missingAtoms.values())
        fx.addMissingAtoms()
        fx.addMissingHydrogens(7.4)
        with open(dst, "w") as fh:
            PDBFile.writeFile(fx.topology, fx.positions, fh)
        print(f"{pdb}: {n_missing} missing heavy atoms fixed, H added")
    except Exception as e:
        print(f"{pdb}: FAILED {type(e).__name__}: {e}")
