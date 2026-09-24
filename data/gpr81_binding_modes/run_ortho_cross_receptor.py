#!/usr/bin/env python3
"""
Simulate and compare Agonist 1 in the ORTHOSTERIC pocket of:
1. HCAR1 (PDB 8Z8A, active state)
2. HCAR2 (PDB 8J6P, active state)

Evaluates:
- Nonbonded Interaction Energy (Coulomb + LJ)
- Specific interaction with orthosteric anchors:
  HCAR1: Arg71, Arg99, Ser167, Phe168
  HCAR2: Leu83, Arg111, Ser179, Phe180
- Resolves whether the orthosteric pocket can explain the >200-fold selectivity
"""

import os
import sys
import numpy as np
from rdkit import Chem
from openff.toolkit.topology import Molecule
from openmmforcefields.generators import SystemGenerator
import openmm
from openmm import app, unit
from openmm.app import PDBFile, Modeller

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
sys.stdout.reconfigure(line_buffering=True)

def load_agonist1_ortho():
    sdf_path = os.path.join(WORK_DIR, "agonist1_ortho_boltz.sdf")
    suppl = Chem.SDMolSupplier(sdf_path, removeHs=False)
    m = suppl[0]
    m_hs = Chem.AddHs(m, addCoords=True)
    off_mol = Molecule.from_rdkit(m_hs, allow_undefined_stereo=True)
    off_mol.assign_partial_charges("openff-gnn-am1bcc-0.1.0-rc.3.pt")
    return off_mol

def evaluate_ortho(receptor_pdb_path, receptor_name, anchor_map):
    print(f"\n=======================================================", flush=True)
    print(f"Evaluating Agonist 1 Orthosteric Mode in {receptor_name}", flush=True)
    print(f"=======================================================", flush=True)

    off_mol = load_agonist1_ortho()

    generator = SystemGenerator(
        forcefields=["amber14/protein.ff14SB.xml", "implicit/obc2.xml"],
        small_molecule_forcefield="openff-2.1.0",
        molecules=[off_mol]
    )

    pdb = PDBFile(receptor_pdb_path)
    modeller = Modeller(pdb.topology, pdb.positions)
    lig_top = off_mol.to_topology().to_openmm()
    lig_pos = off_mol.conformers[0].to_openmm()
    modeller.add(lig_top, lig_pos)

    system = generator.create_system(modeller.topology)
    n_prot_atoms = pdb.topology.getNumAtoms()
    n_lig_atoms = lig_top.getNumAtoms()
    prot_atoms = list(range(n_prot_atoms))
    lig_atoms = list(range(n_prot_atoms, n_prot_atoms + n_lig_atoms))

    # Map residues to atom indices
    res_atoms = {rname: [] for rname in anchor_map}
    for atom in modeller.topology.atoms():
        if atom.residue.chain.index == 0:
            res_idx = atom.residue.index + 1 # 1-indexed
            for anchor_label, target_idx in anchor_map.items():
                if res_idx == target_idx:
                    res_atoms[anchor_label].append(atom.index)

    platform = openmm.Platform.getPlatformByName("CUDA")
    properties = {"Precision": "mixed", "DeviceIndex": "0"}
    integrator = openmm.LangevinMiddleIntegrator(300*unit.kelvin, 1.0/unit.picosecond, 0.002*unit.picoseconds)
    sim = app.Simulation(modeller.topology, system, integrator, platform, properties)
    sim.context.setPositions(modeller.positions)

    state0 = sim.context.getState(getEnergy=True)
    e0 = state0.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)

    sim.minimizeEnergy(maxIterations=1000)
    state_min = sim.context.getState(getEnergy=True, getPositions=True)
    emin = state_min.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)

    pos_min = state_min.getPositions()
    pos_array = np.array([[p.x, p.y, p.z] for p in pos_min.value_in_unit(unit.nanometer)])

    nb_force = [f for f in system.getForces() if isinstance(f, openmm.NonbondedForce)][0]
    charges = np.array([nb_force.getParticleParameters(i)[0].value_in_unit(unit.elementary_charge) for i in range(system.getNumParticles())])
    sigmas = np.array([nb_force.getParticleParameters(i)[1].value_in_unit(unit.nanometer) for i in range(system.getNumParticles())])
    epsilons = np.array([nb_force.getParticleParameters(i)[2].value_in_unit(unit.kilojoules_per_mole) / 4.184 for i in range(system.getNumParticles())])
    ONE_4PI = 138.935456 / 4.184

    def compute_pair(ga, gb):
        c, lj = 0.0, 0.0
        for i in ga:
            for j in gb:
                dr = np.linalg.norm(pos_array[i] - pos_array[j])
                if dr > 0.01:
                    c += ONE_4PI * charges[i] * charges[j] / dr
                    sig = 0.5 * (sigmas[i] + sigmas[j])
                    eps = np.sqrt(epsilons[i] * epsilons[j])
                    if eps > 1e-6 and sig > 1e-6:
                        r = sig / dr
                        lj += 4.0 * eps * (r**12 - r**6)
        return c, lj, c + lj

    coul_prot, lj_prot, tot_prot = compute_pair(lig_atoms, prot_atoms)

    print(f"Results for {receptor_name}:", flush=True)
    print(f"  System Initial Energy:   {e0:10.2f} kcal/mol", flush=True)
    print(f"  System Minimized Energy: {emin:10.2f} kcal/mol", flush=True)
    print(f"  Ligand-Protein Interaction (Total): {tot_prot:8.2f} kcal/mol", flush=True)
    print(f"    - Coulomb:                       {coul_prot:8.2f} kcal/mol", flush=True)
    print(f"    - Van der Waals (LJ):            {lj_prot:8.2f} kcal/mol", flush=True)

    anchor_energies = {}
    for anchor_label, a_atoms in res_atoms.items():
        _, _, e_anc = compute_pair(lig_atoms, a_atoms) if a_atoms else (0.0, 0.0, 0.0)
        anchor_energies[anchor_label] = e_anc
        print(f"  Anchor {anchor_label:15s}: {e_anc:8.2f} kcal/mol", flush=True)

    return {
        "receptor": receptor_name,
        "e_initial": float(e0),
        "e_min": float(emin),
        "e_tot_prot": float(tot_prot),
        "e_coul_prot": float(coul_prot),
        "e_lj_prot": float(lj_prot),
        "anchors": anchor_energies
    }

if __name__ == "__main__":
    # In 8Z8A_fixed: Chain A residues start at 1, corresponding to original seq 6..286
    # Arg71 is fixed index 66; Arg99 is fixed index 94; Ser167 is 162; Phe168 is 163
    map_h1 = {
        "Arg71 (TM2)": 66,
        "Arg99 (TM3)": 94,
        "Ser167 (ECL2)": 162,
        "Phe168 (ECL2)": 163
    }

    # In 8J6P_fixed: Chain A residues start at 1, corresponding to original seq 19..298
    # Arg111 is 111 - 19 + 1 = 93; Leu83 is 83 - 19 + 1 = 65; Ser179 is 179 - 19 + 1 = 161; Phe180 is 162
    map_h2 = {
        "Leu83 (TM2)": 65,
        "Arg111 (TM3)": 93,
        "Ser179 (ECL2)": 161,
        "Phe180 (ECL2)": 162
    }

    r_h1 = evaluate_ortho(f"{WORK_DIR}/8Z8A_fixed.pdb", "HCAR1 (GPR81, PDB 8Z8A)", map_h1)
    r_h2 = evaluate_ortho(f"{WORK_DIR}/8J6P_fixed.pdb", "HCAR2 (GPR109A, PDB 8J6P)", map_h2)

    print("\n" + "=" * 65, flush=True)
    print("ORTHOSTERIC CROSS-RECEPTOR SELECTIVITY SIMULATION SUMMARY", flush=True)
    print("=" * 65, flush=True)
    print(f"HCAR1 Orthosteric Total Interaction: {r_h1['e_tot_prot']:8.2f} kcal/mol (Coul: {r_h1['e_coul_prot']:.2f}, LJ: {r_h1['e_lj_prot']:.2f})")
    print(f"HCAR2 Orthosteric Total Interaction: {r_h2['e_tot_prot']:8.2f} kcal/mol (Coul: {r_h2['e_coul_prot']:.2f}, LJ: {r_h2['e_lj_prot']:.2f})")
    delta_e = r_h2['e_tot_prot'] - r_h1['e_tot_prot']
    print(f"Delta Interaction (HCAR2 - HCAR1):    {delta_e:+8.2f} kcal/mol")
