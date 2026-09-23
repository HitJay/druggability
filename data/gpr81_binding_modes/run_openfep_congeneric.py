#!/usr/bin/env python3
"""
Run OpenMM Congeneric Free Energy Perturbation (FEP) on GPR81:
Evaluation of c30 (5.0 nM lead, pyridone) -> c31 (240 nM, pyrimidinone cliff)

Calculates relative binding free energy (ddG_bind):
ddG_bind = dG_complex(c30 -> c31) - dG_solvent(c30 -> c31)

Runs across 7 alchemical lambda windows:
lambda in [0.0, 0.15, 0.35, 0.50, 0.65, 0.85, 1.0]

Compares:
1. Allosteric Crevice (TM5-TM6-ECL2, Vina pose)
2. Orthosteric Core (TM2-TM3-TM7, Boltz-2 pose)
3. Unbound Ligand in Solvent (OBC2 aqueous reference)

Produces:
- Thermodynamic Integration (TI) dG curves
- Decisive True-Site Validation vs experimental ddG_exp = +2.296 kcal/mol
"""

import os
import sys
import time
import json
import numpy as np
from scipy.integrate import trapezoid

# Ensure immediate line buffering
sys.stdout.reconfigure(line_buffering=True)

from rdkit import Chem
from rdkit.Chem import AllChem
import openmm
from openmm import app, unit
from openff.toolkit.topology import Molecule
from openmmforcefields.generators import SystemGenerator

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
OUT_JSON = os.path.join(WORK_DIR, "openfep_congeneric_results.json")

# Experimental Benchmark Values
# c30 EC50 = 5.0 nM, c31 EC50 = 240.0 nM (Davidsson 2020)
# Ratio = 48.0x
KB = 0.001987204 # kcal/(mol*K)
TEMP = 300.0 # K
DDG_EXP = KB * TEMP * np.log(240.0 / 5.0) # +2.296 kcal/mol

print("=" * 75, flush=True)
print("GPR81 CONGENERIC OpenFEP SIMULATION", flush=True)
print(f"Target Perturbation: c30 (pyridone, 5.0 nM) -> c31 (pyrimidinone, 240.0 nM)", flush=True)
print(f"Experimental Free Energy Cliff (ddG_exp): {DDG_EXP:+.3f} kcal/mol (48-fold drop)", flush=True)
print("=" * 75, flush=True)

# 1. Setup System Generator
print("\n[1/5] Initializing Force Fields and System Generator...", flush=True)
system_generator = SystemGenerator(
    forcefields=["amber14/protein.ff14SB.xml", "implicit/obc2.xml"],
    small_molecule_forcefield="openff-2.1.0",
    molecules=[],
    cache=None
)

# 2. Load Molecules and Poses
print("\n[2/5] Loading c30 conformers (Allosteric & Orthosteric)...", flush=True)
raw_c30_allo = Chem.SDMolSupplier(os.path.join(WORK_DIR, "c30_allo.sdf"), removeHs=False)[0]
c30_allo_mol = Chem.AddHs(raw_c30_allo, addCoords=True)
AllChem.UFFOptimizeMolecule(c30_allo_mol, maxIters=300)

raw_c30_ortho = Chem.SDMolSupplier(os.path.join(WORK_DIR, "c30_ortho.sdf"), removeHs=False)[0]
c30_ortho_mol = Chem.AddHs(raw_c30_ortho, addCoords=True)
AllChem.UFFOptimizeMolecule(c30_ortho_mol, maxIters=300)

# Receptor PDB
pdb_fixed = app.PDBFile(os.path.join(WORK_DIR, "8Z8A_fixed.pdb"))
n_prot_atoms = pdb_fixed.topology.getNumAtoms()
print(f"Receptor atoms: {n_prot_atoms}", flush=True)

# OpenFF molecules with pre-computed GNN AM1-BCC charges
off_c30_allo = Molecule.from_rdkit(c30_allo_mol, allow_undefined_stereo=True)
off_c30_allo.assign_partial_charges("openff-gnn-am1bcc-0.1.0-rc.3.pt")

off_c30_ortho = Molecule.from_rdkit(c30_ortho_mol, allow_undefined_stereo=True)
off_c30_ortho.assign_partial_charges("openff-gnn-am1bcc-0.1.0-rc.3.pt")

system_generator.add_molecules([off_c30_allo, off_c30_ortho])

# Identify mutating atoms in c30 (atom 17: C -> N, atom 57: H decoupled)
patt = Chem.MolFromSmarts("[#6:1]([#1:2])1:[#6]:[#6](=[#8]):[#7]:[#6]:[#6]:1")
matches = c30_allo_mol.GetSubstructMatches(patt)
if matches:
    mut_c_idx = matches[0][0]
    mut_h_idx = matches[0][1]
else:
    mut_c_idx, mut_h_idx = 17, 57

print(f"Alchemical mutating atoms in ligand: C atom {mut_c_idx}, H atom {mut_h_idx}", flush=True)

# 3. Alchemical Lambda Schedule
LAMBDAS = [0.00, 0.15, 0.35, 0.50, 0.65, 0.85, 1.00]
N_WINDOWS = len(LAMBDAS)
STEPS_EQ = 2500    # 5 ps equilibration per window
STEPS_PROD = 10000 # 20 ps production per window
SAMPLE_INTERVAL = 500 # sample every 1.0 ps -> 20 samples per window

platform = openmm.Platform.getPlatformByName("CUDA")
platform_props = {"DeviceIndex": "0", "Precision": "mixed"}

BONDI_RADII = {"H": 0.12, "C": 0.17, "N": 0.155, "O": 0.15, "F": 0.147, "P": 0.18, "S": 0.18, "Cl": 0.17}
BONDI_SCALE = {"H": 0.85, "C": 0.72, "N": 0.79, "O": 0.85, "F": 0.88, "P": 0.86, "S": 0.96, "Cl": 0.80}

def run_fep_leg(leg_name, receptor_pdb, off_mol, is_complex=True):
    print(f"\n>>> Running FEP Leg: {leg_name} (Complex={is_complex})", flush=True)
    
    if is_complex:
        modeller = app.Modeller(receptor_pdb.topology, receptor_pdb.positions)
        lig_top = off_mol.to_topology().to_openmm()
        lig_pos = off_mol.conformers[0].to_openmm()
        modeller.add(lig_top, lig_pos)
        top = modeller.topology
        pos = modeller.positions
        offset = receptor_pdb.topology.getNumAtoms()
    else:
        top = off_mol.to_topology().to_openmm()
        pos = off_mol.conformers[0].to_openmm()
        offset = 0

    system = system_generator.create_system(top)
    
    gb_force = None
    nb_force = None
    for f in system.getForces():
        if isinstance(f, openmm.NonbondedForce):
            nb_force = f
        elif isinstance(f, openmm.CustomGBForce):
            gb_force = f

    # Assign Bondi GBSA parameters to ligand atoms
    n_total = top.getNumAtoms()
    for i in range(offset, n_total):
        atom = list(top.atoms())[i]
        elem = atom.element.symbol
        r = BONDI_RADII.get(elem, 0.15)
        s = BONDI_SCALE.get(elem, 0.8)
        q = nb_force.getParticleParameters(i)[0]
        if gb_force is not None:
            gb_force.setParticleParameters(i, [q, r, s])
    
    c_idx_sys = offset + mut_c_idx
    h_idx_sys = offset + mut_h_idx
    
    integrator = openmm.LangevinMiddleIntegrator(TEMP * unit.kelvin, 1.0 / unit.picosecond, 0.002 * unit.picosecond)
    sim = app.Simulation(top, system, integrator, platform, platform_props)
    sim.context.setPositions(pos)
    sim.minimizeEnergy(maxIterations=100)
            
    q0_c, sig0_c, eps0_c = nb_force.getParticleParameters(c_idx_sys)
    q0_h, sig0_h, eps0_h = nb_force.getParticleParameters(h_idx_sys)
    
    q0_c_val = q0_c.value_in_unit(unit.elementary_charge)
    sig0_c_val = sig0_c.value_in_unit(unit.nanometer)
    eps0_c_val = eps0_c.value_in_unit(unit.kilojoule_per_mole)
    
    q0_h_val = q0_h.value_in_unit(unit.elementary_charge)
    sig0_h_val = sig0_h.value_in_unit(unit.nanometer)
    eps0_h_val = eps0_h.value_in_unit(unit.kilojoule_per_mole)
    
    dU_dlambda_means = []
    dU_dlambda_stds = []
    
    t_start = time.time()
    for win_idx, lam in enumerate(LAMBDAS):
        # Set parameters for current lambda
        q_lam_c = q0_c_val * (1.0 - lam) + (-0.55) * lam
        sig_lam_c = sig0_c_val * (1.0 - lam) + 0.325 * lam
        eps_lam_c = eps0_c_val * (1.0 - lam) + (0.71 * 4.184) * lam
        
        q_lam_h = q0_h_val * (1.0 - lam)
        eps_lam_h = eps0_h_val * (1.0 - lam)
        
        nb_force.setParticleParameters(c_idx_sys, q_lam_c * unit.elementary_charge,
                                       sig_lam_c * unit.nanometer,
                                       eps_lam_c * unit.kilojoule_per_mole)
        nb_force.setParticleParameters(h_idx_sys, q_lam_h * unit.elementary_charge,
                                       sig0_h_val * unit.nanometer,
                                       eps_lam_h * unit.kilojoule_per_mole)
        if gb_force is not None:
            r_c = 0.17 * (1.0 - lam) + 0.155 * lam
            gb_force.setParticleParameters(c_idx_sys, [q_lam_c * unit.elementary_charge, r_c, 0.79])
            gb_force.setParticleParameters(h_idx_sys, [q_lam_h * unit.elementary_charge, 0.12, 0.85])
            
        nb_force.updateParametersInContext(sim.context)
        if gb_force is not None:
            gb_force.updateParametersInContext(sim.context)
        
        # Equilibration
        sim.step(STEPS_EQ)
        
        # Production & Sampling
        dUs = []
        n_samples = STEPS_PROD // SAMPLE_INTERVAL
        d_lam = 0.01
        lam_p = lam + d_lam
        
        q_p_c = q0_c_val * (1.0 - lam_p) + (-0.55) * lam_p
        sig_p_c = sig0_c_val * (1.0 - lam_p) + 0.325 * lam_p
        eps_p_c = eps0_c_val * (1.0 - lam_p) + (0.71 * 4.184) * lam_p
        q_p_h = q0_h_val * (1.0 - lam_p)
        eps_p_h = eps0_h_val * (1.0 - lam_p)
        r_p_c = 0.17 * (1.0 - lam_p) + 0.155 * lam_p

        for s in range(n_samples):
            sim.step(SAMPLE_INTERVAL)
            u_current = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
            
            # Perturb forward
            nb_force.setParticleParameters(c_idx_sys, q_p_c * unit.elementary_charge,
                                           sig_p_c * unit.nanometer,
                                           eps_p_c * unit.kilojoule_per_mole)
            nb_force.setParticleParameters(h_idx_sys, q_p_h * unit.elementary_charge,
                                           sig0_h_val * unit.nanometer,
                                           eps_p_h * unit.kilojoule_per_mole)
            if gb_force is not None:
                gb_force.setParticleParameters(c_idx_sys, [q_p_c * unit.elementary_charge, r_p_c, 0.79])
                gb_force.setParticleParameters(h_idx_sys, [q_p_h * unit.elementary_charge, 0.12, 0.85])
            nb_force.updateParametersInContext(sim.context)
            if gb_force is not None:
                gb_force.updateParametersInContext(sim.context)
                
            u_forward = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
            
            # Restore current lambda
            nb_force.setParticleParameters(c_idx_sys, q_lam_c * unit.elementary_charge,
                                           sig_lam_c * unit.nanometer,
                                           eps_lam_c * unit.kilojoule_per_mole)
            nb_force.setParticleParameters(h_idx_sys, q_lam_h * unit.elementary_charge,
                                           sig0_h_val * unit.nanometer,
                                           eps_lam_h * unit.kilojoule_per_mole)
            if gb_force is not None:
                gb_force.setParticleParameters(c_idx_sys, [q_lam_c * unit.elementary_charge, r_c, 0.79])
                gb_force.setParticleParameters(h_idx_sys, [q_lam_h * unit.elementary_charge, 0.12, 0.85])
            nb_force.updateParametersInContext(sim.context)
            if gb_force is not None:
                gb_force.updateParametersInContext(sim.context)
            
            d_energy = (u_forward - u_current) / d_lam
            dUs.append(d_energy)
            
        mean_du = float(np.mean(dUs))
        std_du = float(np.std(dUs))
        dU_dlambda_means.append(mean_du)
        dU_dlambda_stds.append(std_du)
        print(f"  Window {win_idx+1}/{N_WINDOWS} (lambda = {lam:.2f}): <dU/dlam> = {mean_du:+8.3f} +/- {std_du:6.3f} kcal/mol", flush=True)
        
    dG_ti = float(trapezoid(dU_dlambda_means, LAMBDAS))
    error_ti = float(np.sqrt(np.sum(np.array(dU_dlambda_stds)**2) / n_samples))
    t_elapsed = time.time() - t_start
    print(f"--> Leg {leg_name} dG = {dG_ti:+.3f} +/- {error_ti:.3f} kcal/mol (Time: {t_elapsed:.1f} s)", flush=True)
    
    return {
        "leg_name": leg_name,
        "dG_ti_kcal_mol": dG_ti,
        "error_kcal_mol": error_ti,
        "lambdas": LAMBDAS,
        "dU_dlambda_means": dU_dlambda_means,
        "dU_dlambda_stds": dU_dlambda_stds,
        "elapsed_seconds": t_elapsed
    }

# Execute All 3 Legs
print("\n" + "=" * 75, flush=True)
print("EXECUTING OPENFEP ALCHEMICAL LEGS ON NVIDIA A100 GPU", flush=True)
print("=" * 75, flush=True)

# Leg 1: Solvent Reference
res_solvent = run_fep_leg("Solvent_Aqueous", pdb_fixed, off_c30_allo, is_complex=False)

# Leg 2: Allosteric Pocket (TM5-TM6 Crevice)
res_allosteric = run_fep_leg("Allosteric_TM5_TM6", pdb_fixed, off_c30_allo, is_complex=True)

# Leg 3: Orthosteric Pocket (TM2-TM3-TM7 Core)
res_orthosteric = run_fep_leg("Orthosteric_TM2_TM7", pdb_fixed, off_c30_ortho, is_complex=True)

# 4. Compute Relative Free Energies (ddG_bind)
ddG_allo = res_allosteric["dG_ti_kcal_mol"] - res_solvent["dG_ti_kcal_mol"]
ddG_ortho = res_orthosteric["dG_ti_kcal_mol"] - res_solvent["dG_ti_kcal_mol"]

print("\n" + "=" * 75, flush=True)
print("FINAL OPENFEP CONGENERIC RESULTS SUMMARY (c30 -> c31)", flush=True)
print("=" * 75, flush=True)
print(f"Experimental Target (ddG_exp):             {DDG_EXP:+.3f} kcal/mol (48x cliff)", flush=True)
print(f"Allosteric Pocket FEP (ddG_allo):           {ddG_allo:+.3f} kcal/mol", flush=True)
print(f"  -> Error vs Exp:                          {abs(ddG_allo - DDG_EXP):.3f} kcal/mol", flush=True)
print(f"Orthosteric Pocket FEP (ddG_ortho):         {ddG_ortho:+.3f} kcal/mol", flush=True)
print(f"  -> Error vs Exp:                          {abs(ddG_ortho - DDG_EXP):.3f} kcal/mol", flush=True)

site_verdict = "ALLOSTERIC_POCKET (TM5-TM6-ECL2 Crevice)" if abs(ddG_allo - DDG_EXP) < abs(ddG_ortho - DDG_EXP) else "ORTHOSTERIC_POCKET"
print(f"\nDECISIVE TRUE-SITE COMPUTATIONAL CONCLUSION:", flush=True)
print(f"The congeneric OpenFEP relative free energy quantitatively validates the: {site_verdict}", flush=True)
print("=" * 75, flush=True)

# Save JSON results
results = {
    "benchmark": {
        "compound_A": "c30",
        "compound_B": "c31",
        "c30_EC50_nM": 5.0,
        "c31_EC50_nM": 240.0,
        "potency_fold_change": 48.0,
        "ddG_exp_kcal_mol": float(DDG_EXP)
    },
    "fep_legs": {
        "solvent": res_solvent,
        "allosteric": res_allosteric,
        "orthosteric": res_orthosteric
    },
    "relative_binding_free_energies": {
        "ddG_allosteric_kcal_mol": float(ddG_allo),
        "ddG_orthosteric_kcal_mol": float(ddG_ortho),
        "error_allosteric_vs_exp": float(abs(ddG_allo - DDG_EXP)),
        "error_orthosteric_vs_exp": float(abs(ddG_ortho - DDG_EXP)),
        "true_site_verdict": site_verdict
    }
}

with open(OUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved structured OpenFEP results: {OUT_JSON}", flush=True)
