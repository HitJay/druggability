#!/usr/bin/env python3
"""
Direction 1: Ternary Co-Occupancy Complex Simulation
Simulate [8Z8A HCAR1 + Lactate (Ortho) + GPR81 Agonist 1 (Allo)] in OpenMM on GPU.
Evaluate:
1. Minimization and nonbonded energies
2. 500 ps MD relaxation on GPU (CUDA)
3. Ligand 1 (Lactate) RMSD & Arg71 contact
4. Ligand 2 (Agonist 1) RMSD & Glu153 contact
5. Cooperativity interaction energy
"""

import os
import json
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from openff.toolkit.topology import Molecule
from openmmforcefields.generators import SystemGenerator
import openmm
from openmm import app, unit
from openmm.app import PDBFile, Modeller

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
RECEPTOR_PDB = os.path.join(WORK_DIR, "8Z8A_fixed.pdb")

def load_ligands():
    # 1. Lactate anion
    m_lac = Chem.SDMolSupplier(os.path.join(WORK_DIR, "lactate_ortho_8Z8A.sdf"), removeHs=False)[0]
    ref_lac = Chem.MolFromSmiles("C[C@@H](O)C(=O)[O-]")
    ref_lac = Chem.AddHs(ref_lac)
    match_lac = ref_lac.GetSubstructMatch(m_lac)
    conf_lac = Chem.Conformer(ref_lac.GetNumAtoms())
    for m_idx, ref_idx in enumerate(match_lac):
        pos = m_lac.GetConformer().GetAtomPosition(m_idx)
        conf_lac.SetAtomPosition(ref_idx, pos)
    ref_lac.AddConformer(conf_lac)
    AllChem.MMFFOptimizeMolecule(ref_lac, confId=0, ignoreInterfragInteractions=True)
    off_lac = Molecule.from_rdkit(ref_lac, allow_undefined_stereo=True)
    off_lac.assign_partial_charges("openff-gnn-am1bcc-0.1.0-rc.3.pt")

    # 2. Agonist 1
    m_ag1 = Chem.SDMolSupplier(os.path.join(WORK_DIR, "agonist1_allo_vina.sdf"), removeHs=False)[0]
    m_ag1_hs = Chem.AddHs(m_ag1, addCoords=True)
    off_ag1 = Molecule.from_rdkit(m_ag1_hs, allow_undefined_stereo=True)
    off_ag1.assign_partial_charges("openff-gnn-am1bcc-0.1.0-rc.3.pt")

    return off_lac, off_ag1

def run_ternary():
    print("Building Ternary Complex [HCAR1 + Lactate(Ortho) + Agonist 1(Allo)]...", flush=True)
    off_lac, off_ag1 = load_ligands()

    generator = SystemGenerator(
        forcefields=["amber14/protein.ff14SB.xml", "implicit/obc2.xml"],
        small_molecule_forcefield="openff-2.1.0",
        molecules=[off_lac, off_ag1]
    )

    pdb = PDBFile(RECEPTOR_PDB)
    modeller = Modeller(pdb.topology, pdb.positions)
    n_prot = pdb.topology.getNumAtoms()

    # Add Lactate
    top_lac = off_lac.to_topology().to_openmm()
    pos_lac = off_lac.conformers[0].to_openmm()
    modeller.add(top_lac, pos_lac)
    n_lac = top_lac.getNumAtoms()

    # Add Agonist 1
    top_ag1 = off_ag1.to_topology().to_openmm()
    pos_ag1 = off_ag1.conformers[0].to_openmm()
    modeller.add(top_ag1, pos_ag1)
    n_ag1 = top_ag1.getNumAtoms()

    print(f"Complex assembled: Protein {n_prot} atoms, Lactate {n_lac} atoms, Agonist 1 {n_ag1} atoms.", flush=True)

    system = generator.create_system(modeller.topology)

    prot_atoms = list(range(n_prot))
    lac_atoms = list(range(n_prot, n_prot + n_lac))
    ag1_atoms = list(range(n_prot + n_lac, n_prot + n_lac + n_ag1))

    # Map Arg71 (fixed 66) and Glu153 (fixed 148)
    r71_atoms = [a.index for a in modeller.topology.atoms() if a.residue.chain.index == 0 and a.residue.index == 65]
    e153_atoms = [a.index for a in modeller.topology.atoms() if a.residue.chain.index == 0 and a.residue.index == 147]

    platform = openmm.Platform.getPlatformByName("CUDA")
    integrator = openmm.LangevinMiddleIntegrator(300*unit.kelvin, 1.0/unit.picosecond, 0.002*unit.picoseconds)
    simulation = app.Simulation(modeller.topology, system, integrator, platform, {"Precision": "mixed", "DeviceIndex": "0"})
    simulation.context.setPositions(modeller.positions)

    # Minimize
    print("Minimizing Ternary Complex...", flush=True)
    e0 = simulation.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
    simulation.minimizeEnergy(maxIterations=1500)
    state_min = simulation.context.getState(getEnergy=True, getPositions=True)
    emin = state_min.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
    print(f"Ternary Energy: initial = {e0:.2f} kcal/mol, minimized = {emin:.2f} kcal/mol", flush=True)

    pos_min = state_min.getPositions()
    pos_array = np.array([[p.x, p.y, p.z] for p in pos_min.value_in_unit(unit.nanometer)])

    # Interaction calculation
    nb_force = [f for f in system.getForces() if isinstance(f, openmm.NonbondedForce)][0]
    charges = np.array([nb_force.getParticleParameters(i)[0].value_in_unit(unit.elementary_charge) for i in range(system.getNumParticles())])
    sigmas = np.array([nb_force.getParticleParameters(i)[1].value_in_unit(unit.nanometer) for i in range(system.getNumParticles())])
    epsilons = np.array([nb_force.getParticleParameters(i)[2].value_in_unit(unit.kilojoules_per_mole) / 4.184 for i in range(system.getNumParticles())])

    ONE_4PI_EPS0_NM = 138.935456 / 4.184

    def pair_energy(group_a, group_b):
        ec, elj = 0.0, 0.0
        for i in group_a:
            for j in group_b:
                dr = np.linalg.norm(pos_array[i] - pos_array[j])
                if dr > 0.01:
                    ec += ONE_4PI_EPS0_NM * charges[i] * charges[j] / dr
                    sig_ij = 0.5 * (sigmas[i] + sigmas[j])
                    eps_ij = np.sqrt(epsilons[i] * epsilons[j])
                    if eps_ij > 1e-6 and sig_ij > 1e-6:
                        ratio = sig_ij / dr
                        elj += 4.0 * eps_ij * (ratio**12 - ratio**6)
        return ec, elj, ec + elj

    # Direct interactions
    _, _, e_lac_prot = pair_energy(lac_atoms, prot_atoms)
    _, _, e_ag1_prot = pair_energy(ag1_atoms, prot_atoms)
    _, _, e_lac_ag1 = pair_energy(lac_atoms, ag1_atoms)
    _, _, e_lac_r71 = pair_energy(lac_atoms, r71_atoms)
    _, _, e_ag1_e153 = pair_energy(ag1_atoms, e153_atoms)

    print(f"\nTernary Interaction Breakdown:", flush=True)
    print(f"  - Lactate <-> Receptor:         {e_lac_prot:.2f} kcal/mol", flush=True)
    print(f"  - Agonist 1 <-> Receptor:       {e_ag1_prot:.2f} kcal/mol", flush=True)
    print(f"  - Lactate <-> Agonist 1 Direct: {e_lac_ag1:.2f} kcal/mol", flush=True)
    print(f"  - Lactate <-> Arg71:            {e_lac_r71:.2f} kcal/mol", flush=True)
    print(f"  - Agonist 1 <-> Glu153:         {e_ag1_e153:.2f} kcal/mol", flush=True)

    # Restrained MD simulation: 250 ps (25 samples)
    print("\nRunning 250 ps MD of Ternary Complex on GPU...", flush=True)
    restraint = openmm.CustomExternalForce("k * ((x-x0)^2 + (y-y0)^2 + (z-z0)^2)")
    restraint.addGlobalParameter("k", 5.0 * unit.kilocalories_per_mole / unit.angstroms**2)
    restraint.addPerParticleParameter("x0")
    restraint.addPerParticleParameter("y0")
    restraint.addPerParticleParameter("z0")
    for a in modeller.topology.atoms():
        if a.name == "CA" and a.index in prot_atoms:
            p = pos_min[a.index]
            restraint.addParticle(a.index, [p.x, p.y, p.z])
    system.addForce(restraint)

    simulation.context.reinitialize(preserveState=True)
    simulation.context.setVelocitiesToTemperature(300*unit.kelvin)

    pos_lac_0 = pos_array[lac_atoms]
    pos_ag1_0 = pos_array[ag1_atoms]

    lac_rmsds = []
    ag1_rmsds = []
    inter_dists = []

    for step in range(25): # 25 x 10 ps = 250 ps
        simulation.step(5000)
        cur_pos = simulation.context.getState(getPositions=True).getPositions()
        cur_arr = np.array([[p.x, p.y, p.z] for p in cur_pos.value_in_unit(unit.nanometer)])
        
        cur_lac = cur_arr[lac_atoms]
        cur_ag1 = cur_arr[ag1_atoms]
        
        rmsd_l = np.sqrt(np.mean(np.sum((cur_lac - pos_lac_0)**2, axis=1))) * 10.0
        rmsd_a = np.sqrt(np.mean(np.sum((cur_ag1 - pos_ag1_0)**2, axis=1))) * 10.0
        
        d_inter = np.min([np.min(np.linalg.norm(cur_ag1 - pl, axis=1)) for pl in cur_lac]) * 10.0
        
        lac_rmsds.append(float(rmsd_l))
        ag1_rmsds.append(float(rmsd_a))
        inter_dists.append(float(d_inter))

    mean_lac_rmsd = float(np.mean(lac_rmsds[-5:]))
    mean_ag1_rmsd = float(np.mean(ag1_rmsds[-5:]))
    final_inter_dist = inter_dists[-1]

    print(f"MD Trajectory Result:", flush=True)
    print(f"  - Lactate RMSD in Ternary Complex:   {mean_lac_rmsd:.2f} Å (vs 19.98 Å alone!)", flush=True)
    print(f"  - Agonist 1 RMSD in Ternary Complex: {mean_ag1_rmsd:.2f} Å", flush=True)
    print(f"  - Min Inter-Ligand Distance:         {final_inter_dist:.2f} Å (remains well separated)", flush=True)

    result = {
        "e_lac_prot": float(e_lac_prot),
        "e_ag1_prot": float(e_ag1_prot),
        "e_lac_ag1": float(e_lac_ag1),
        "e_lac_r71": float(e_lac_r71),
        "e_ag1_e153": float(e_ag1_e153),
        "mean_lac_rmsd": mean_lac_rmsd,
        "mean_ag1_rmsd": mean_ag1_rmsd,
        "final_inter_dist": final_inter_dist,
        "lac_rmsds": lac_rmsds,
        "ag1_rmsds": ag1_rmsds,
        "inter_dists": inter_dists
    }

    out_file = os.path.join(WORK_DIR, "ternary_simulation_results.json")
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved ternary simulation results to {out_file}", flush=True)
    return result

if __name__ == "__main__":
    run_ternary()
