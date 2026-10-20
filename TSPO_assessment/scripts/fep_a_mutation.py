"""FEP-A: perses point-mutation (anchor residue -> ALA) relative FEP, per pocket.

Scientific question (ZC's original ask): does the docked ligand actually USE the
pocket's key interaction? Protocol per pocket x ligand:
  1. complex = fixed receptor (f2_<pdb>_rec_fixed.pdb) + ligand (relaxed pose from
     the f4 MD, or docked pose where MD drifted);
  2. perses PointMutationExecutor: mutate the top-contact residue to ALA in the
     presence of the ligand, explicit TIP3P solvent;
  3. short equilibration + NEQ/repex sampling handled by perses HybridTopologyFactory
     via SAMS replica exchange; ddG = mutation free energy WITH ligand minus the
     same mutation WITHOUT ligand (apoenzyme) = interaction fingerprint.
Runtime budget: smoke test first (1 pocket x 1 ligand, reduced n_steps), then full.
"""
import json
import os
import sys
import time

os.environ.setdefault("AMBERHOME", "/data/user/QYJI/micromamba/envs/perses-abfe")
os.environ.setdefault("OPENMM_CPU_THREADS", "4")

import numpy as np
import openmm
import openmm.unit as unit
from openmm import app

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/docking"

# per ligand: pdb -> (label, ligand residue name in the relaxed/docked complex, anchor residue)
EMAPUNIL_POCKETS = {
    "4RYI": ("TSPO_anchor", "UNL", ("A", 23, "PHE")),   # PHE23 top contact
    "6X3X": ("GABA-A_BZD_site", "UNL", ("A", 223, "LEU")),
    "4DKL": ("OPRM1_orthosteric", "UNL", ("A", 83, "ASP")),
    "1XVP": ("CAR_LBD", "UNL", ("D", 59, "PHE")),       # chain D = receptor chain in 1XVP rec
    "4XAQ": ("GRM2_negative_control", "UNL", ("A", 199, "ARG")),
}
FGIN_POCKETS = {
    "4RYI": ("TSPO_anchor", "UNL", ("A", 43, "MET")),
    "1XVP": ("CAR_LBD", "UNL", ("D", 132, "PHE")),
    "5TGZ": ("CNR1_orthosteric", "UNL", ("A", 410, "SER")),
    "4DJH": ("OPRK1_orthosteric", "UNL", ("A", 420, "TYR")),
    "4XAQ": ("GRM2_negative_control", "UNL", ("A", 227, "ARG")),
}


def build_input_pdb(pdb, ligand_resname, out_pdb):
    """Strip the relaxed complex down to protein + ligand (drop waters, keep H)."""
    keep = []
    for line in open(f"{OUT}/f4_{pdb}_{ligand_resname.lower()}_relaxed.pdb"
                     if ligand_resname != "UNL" else
                     # emapunil relaxed files are f4_<pdb>_relaxed.pdb (no lig suffix)
                     f"{OUT}/f4_{pdb}_relaxed.pdb"):
        if line.startswith(("ATOM", "HETATM")):
            res = line[17:20].strip()
            if res in ("HOH", "WAT", "Na+", "Cl-"):
                continue
            keep.append(line)
        elif line.startswith("ENDMDL"):
            break
    with open(out_pdb, "w") as fh:
        fh.writelines(keep)
        fh.write("END\n")
    return out_pdb


def run_pocket(pdb, ligtag, rec_file, chain, resid, resname, ligand_resname,
               n_steps, out_dir):
    """One mutation-FEP: residue -> ALA with ligand present."""
    from perses.app.relative_point_mutation_setup import PointMutationExecutor
    t0 = time.time()
    print(f"[{pdb}/{ligtag}] mutating {resname}{resid} chain {chain} -> ALA", flush=True)
    pm = PointMutationExecutor(
        protein_filename=rec_file,
        mutation_chain_id=chain,
        mutation_residue_id=str(resid),
        proposed_residue="ALA",
        ligand_input=None,        # apoenzyme arm; holo arm built separately below
        is_solvated=True,
        water_model="tip3p",
        ionic_strength=0.15 * unit.molar,
        padding=1.0 * unit.nanometer,
        conduct_endstate_validation=False,   # skip the expensive endstate validation
    )
    # apoenzyme hybrid factory + setup
    apo_htf = pm.get_apo_htf()
    print(f"[{pdb}/{ligtag}] apo HTF built in {time.time()-t0:.0f}s", flush=True)
    return apo_htf


if __name__ == "__main__":
    # smoke: 4RYI emapunil PHE23->ALA apoenzyme HTF construction only
    pdb = sys.argv[1] if len(sys.argv) > 1 else "4RYI"
    rec = f"{OUT}/f2_{pdb}_rec_fixed.pdb"
    htf = run_pocket(pdb, "smoke", rec, "A", 23, "PHE", "UNL", 0, OUT)
    system = htf.hybrid_system
    print("hybrid system particles:", system.getNumParticles())
    print("forces:", [type(system.getForce(i)).__name__ for i in range(system.getNumForces())])
    print("SMOKE OK")
