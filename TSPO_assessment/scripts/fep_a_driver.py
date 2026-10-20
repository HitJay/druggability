"""FEP-A driver: perses point-mutation (anchor residue -> ALA).

Uses perses PointMutationExecutor with protein-only PDB + ligand as separate .pdb
(ligand_input .pdb branch needs no openeye). The oechem stub satisfies module imports.

Phases:
  holo: protein + ligand present during the mutation
  apo:  protein only
ddG(interaction fingerprint) = dG_mut(holo) - dG_mut(apo); negative => the ligand
uses that residue.

Usage: python fep_a_driver.py <pdb> <ligand: emapunil|fgin> <phase: holo|apo> [--smoke]
"""
import os
import sys
import time

os.environ.setdefault("AMBERHOME", "/data/user/QYJI/micromamba/envs/perses-abfe")
os.environ.setdefault("OPENMM_CPU_THREADS", "4")

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from oechem_stub import install_stub
install_stub()  # must precede any perses import

import openmm.unit as unit

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/fep_a"
IN = f"{OUT}/inputs"

# pdb -> (protein pdb, ligand pdb, pocket chain, anchor resid, resname)
EMAP = {
    "4RYI": (f"{IN}/4RYI_emapunil_protein.pdb", f"{IN}/4RYI_emapunil_lig.pdb", "A", 23, "PHE"),
    "6X3X": (f"{IN}/6X3X_emapunil_protein.pdb", f"{IN}/6X3X_emapunil_lig.pdb", "B", 223, "LEU"),
    "4DKL": (f"{IN}/4DKL_emapunil_protein.pdb", f"{IN}/4DKL_emapunil_lig.pdb", "A", 83, "ASP"),
    "1XVP": (f"{IN}/1XVP_emapunil_protein.pdb", f"{IN}/1XVP_emapunil_lig.pdb", "A", 59, "PHE"),
    "4XAQ": (f"{IN}/4XAQ_emapunil_protein.pdb", f"{IN}/4XAQ_emapunil_lig.pdb", "A", 199, "ARG"),
}
FGIN = {
    "4RYI": (f"{IN}/4RYI_fgin_protein.pdb", f"{IN}/4RYI_fgin_lig.pdb", "A", 43, "MET"),
    "1XVP": (f"{IN}/1XVP_fgin_protein.pdb", f"{IN}/1XVP_fgin_lig.pdb", "A", 132, "PHE"),
    "5TGZ": (f"{IN}/5TGZ_fgin_protein.pdb", f"{IN}/5TGZ_fgin_lig.pdb", "A", 410, "SER"),
    "4DJH": (f"{IN}/4DJH_fgin_protein.pdb", f"{IN}/4DJH_fgin_lig.pdb", "A", 420, "TYR"),
    "4XAQ": (f"{IN}/4XAQ_fgin_protein.pdb", f"{IN}/4XAQ_fgin_lig.pdb", "A", 227, "ARG"),
}


def main():
    pdb, ligand, phase = sys.argv[1], sys.argv[2], sys.argv[3]
    smoke = "--smoke" in sys.argv
    table = EMAP if ligand == "emapunil" else FGIN
    prot_pdb, lig_pdb, chain, resid, resname = table[pdb]

    from perses.app.relative_point_mutation_setup import PointMutationExecutor
    t0 = time.time()
    print(f"[{pdb}/{ligand}/{phase}] {resname}{resid} chain {chain} -> ALA", flush=True)
    pm = PointMutationExecutor(
        protein_filename=prot_pdb,
        mutation_chain_id=chain,
        mutation_residue_id=str(resid),
        proposed_residue="ALA",
        ligand_input=lig_pdb if phase == "holo" else None,
        ligand_index=0,
        is_solvated=True,
        water_model="tip3p",
        ionic_strength=0.15 * unit.molar,
        padding=1.0 * unit.nanometer,
        conduct_endstate_validation=False,
    )
    htf = pm.get_complex_htf() if phase == "holo" else pm.get_apo_htf()
    print(f"[{pdb}/{ligand}/{phase}] HTF built in {time.time()-t0:.0f}s; "
          f"hybrid particles: {htf.hybrid_system.getNumParticles()}", flush=True)

    import openmm as mm
    integ = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 2 * unit.femtoseconds)
    plat = mm.Platform.getPlatformByName("CUDA")
    prop = {"CudaPrecision": "mixed", "CudaDeviceIndex": os.environ.get("CUDA_DEVICE", "0")}
    ctx = mm.Context(htf.hybrid_system, integ, plat, prop)
    ctx.setPositions(htf.hybrid_positions)
    try:
        ctx.minimizeEnergy(maxIterations=200 if smoke else 2000)
        e = ctx.getState(getEnergy=True).getPotentialEnergy()
        print(f"[{pdb}/{ligand}/{phase}] hybrid minimise OK, E = {e}", flush=True)
    finally:
        del ctx
    print(f"[{pdb}/{ligand}/{phase}] SETUP OK in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
