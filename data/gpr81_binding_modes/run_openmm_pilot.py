#!/usr/bin/env python3
"""
OpenMM/OpenFF stability & interaction energy evaluation of GPR81 agonist poses:
- Lactate (orthosteric ground truth)
- AZ1 (Boltz orthosteric vs Vina TM5-TM6 allosteric)
- GPR81 agonist 1 (Boltz orthosteric vs Vina TM5-TM6 allosteric)
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

POSES = [
    {"id": "lactate_ortho", "name": "Lactate (8Z8A Co-crystal)", "sdf": "lactate_ortho_8Z8A.sdf", "mode": "Orthosteric", "smiles": "C[C@@H](O)C(=O)[O-]"},
    {"id": "az1_ortho", "name": "AZ1 (Boltz-2 Pose)", "sdf": "az1_ortho_boltz.sdf", "mode": "Orthosteric", "smiles": "CCOc1cc(Cl)c(C(=O)NC(=O)Nc2nc3ccc(S(=O)(=O)C4CCN(C)CC4)cc3s2)cc1-n1cccn1"},
    {"id": "az1_allo", "name": "AZ1 (Vina 8Z8A Pose)", "sdf": "az1_allo_vina.sdf", "mode": "TM5-TM6 Allosteric", "smiles": "CCOc1cc(Cl)c(C(=O)NC(=O)Nc2nc3ccc(S(=O)(=O)C4CCN(C)CC4)cc3s2)cc1-n1cccn1"},
    {"id": "ag1_ortho", "name": "Agonist 1 (Boltz-2 Pose)", "sdf": "agonist1_ortho_boltz.sdf", "mode": "Orthosteric", "smiles": "CC1CCC(CC1)C(=O)NC2=NC(=C(S2)CC(=O)N3CCN(CC3)C)C4=CC=CS4"},
    {"id": "ag1_allo", "name": "Agonist 1 (Vina 8Z8A Pose)", "sdf": "agonist1_allo_vina.sdf", "mode": "TM5-TM6 Allosteric", "smiles": "CC1CCC(CC1)C(=O)NC2=NC(=C(S2)CC(=O)N3CCN(CC3)C)C4=CC=CS4"},
]

def load_ligand_openff(sdf_path, smiles):
    suppl = Chem.SDMolSupplier(sdf_path, removeHs=False)
    m = suppl[0]
    
    # If m has hydrogens, use directly; otherwise construct from ref SMILES
    if m.GetNumAtoms() > 15: # AZ1 or Agonist 1 with Hs
        m_hs = Chem.AddHs(m, addCoords=True)
        off_mol = Molecule.from_rdkit(m_hs, allow_undefined_stereo=True)
    else:
        ref = Chem.MolFromSmiles(smiles)
        ref = Chem.AddHs(ref)
        match = ref.GetSubstructMatch(m)
        conf = Chem.Conformer(ref.GetNumAtoms())
        for m_idx, ref_idx in enumerate(match):
            pos = m.GetConformer().GetAtomPosition(m_idx)
            conf.SetAtomPosition(ref_idx, pos)
        ref.AddConformer(conf)
        # Fast optimize only H coordinates while keeping heavy atoms fixed
        for atom_idx in match:
            pass # heavy atoms
        AllChem.MMFFOptimizeMolecule(ref, confId=0, ignoreInterfragInteractions=True)
        off_mol = Molecule.from_rdkit(ref, allow_undefined_stereo=True)

    off_mol.assign_partial_charges("openff-gnn-am1bcc-0.1.0-rc.3.pt")
    return off_mol

def build_complex(receptor_pdb, off_mol):
    pdb = PDBFile(receptor_pdb)
    modeller = Modeller(pdb.topology, pdb.positions)
    lig_top = off_mol.to_topology().to_openmm()
    lig_pos = off_mol.conformers[0].to_openmm()
    modeller.add(lig_top, lig_pos)
    return modeller, pdb.topology.getNumAtoms(), lig_top.getNumAtoms()

def evaluate_pose(pose_info):
    pose_id = pose_info["id"]
    print(f"\n==========================================", flush=True)
    print(f"Evaluating {pose_info['name']} ({pose_info['mode']})", flush=True)
    print(f"==========================================", flush=True)
    
    sdf_path = os.path.join(WORK_DIR, pose_info["sdf"])
    off_mol = load_ligand_openff(sdf_path, pose_info["smiles"])
    
    generator = SystemGenerator(
        forcefields=["amber14/protein.ff14SB.xml", "implicit/obc2.xml"],
        small_molecule_forcefield="openff-2.1.0",
        molecules=[off_mol]
    )
    
    modeller, n_prot_atoms, n_lig_atoms = build_complex(RECEPTOR_PDB, off_mol)
    system = generator.create_system(modeller.topology)
    
    # Identify atom indices
    prot_atoms = list(range(n_prot_atoms))
    lig_atoms = list(range(n_prot_atoms, n_prot_atoms + n_lig_atoms))
    
    # Build mapping from fixed residue index to original HCAR1 sequence number
    # Fixed chain A residues start at 1, corresponding to original 6..286
    fix_to_orig = {res.index: res.index + 6 for res in modeller.topology.residues() if res.chain.index == 0}

    # Map key residues: Arg71 (fixed 66), Glu153 (fixed 148), His177 (fixed 172)
    r71_atoms = []
    r71_sidechain = []
    e153_atoms = []
    e153_sidechain = []
    h177_atoms = []
    
    # Per-residue atom grouping
    res_atom_groups = {}
    for atom in modeller.topology.atoms():
        if atom.residue.chain.index == 0:
            orig_rid = atom.residue.index + 6
            if orig_rid not in res_atom_groups:
                res_atom_groups[orig_rid] = {"name": atom.residue.name, "atoms": []}
            res_atom_groups[orig_rid]["atoms"].append(atom.index)
            
            if orig_rid == 71:
                r71_atoms.append(atom.index)
                if atom.name not in ["N", "CA", "C", "O", "H", "HA", "CB"]:
                    r71_sidechain.append(atom.index)
            elif orig_rid == 153:
                e153_atoms.append(atom.index)
                if atom.name not in ["N", "CA", "C", "O", "H", "HA", "CB"]:
                    e153_sidechain.append(atom.index)
            elif orig_rid == 177:
                h177_atoms.append(atom.index)
                
    platform = openmm.Platform.getPlatformByName("CUDA")
    properties = {"Precision": "mixed", "DeviceIndex": "0"}
    
    integrator = openmm.LangevinMiddleIntegrator(300*unit.kelvin, 1.0/unit.picosecond, 0.002*unit.picoseconds)
    simulation = app.Simulation(modeller.topology, system, integrator, platform, properties)
    simulation.context.setPositions(modeller.positions)
    
    # Initial minimization
    state0 = simulation.context.getState(getEnergy=True)
    e0 = state0.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
    print(f"Initial energy: {e0:.2f} kcal/mol", flush=True)
    
    simulation.minimizeEnergy(maxIterations=1000)
    state_min = simulation.context.getState(getEnergy=True, getPositions=True)
    emin = state_min.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
    print(f"Minimized energy: {emin:.2f} kcal/mol", flush=True)
    
    pos_min = state_min.getPositions()
    
    # Calculate nonbonded interaction energy
    nb_force = None
    for f in system.getForces():
        if isinstance(f, openmm.NonbondedForce):
            nb_force = f
            break
            
    pos_array = np.array([[p.x, p.y, p.z] for p in pos_min.value_in_unit(unit.nanometer)])
    
    charges = []
    sigmas = []
    epsilons = []
    for i in range(system.getNumParticles()):
        q, sig, eps = nb_force.getParticleParameters(i)
        charges.append(q.value_in_unit(unit.elementary_charge))
        sigmas.append(sig.value_in_unit(unit.nanometer))
        epsilons.append(eps.value_in_unit(unit.kilojoules_per_mole) / 4.184) # kcal/mol
        
    charges = np.array(charges)
    sigmas = np.array(sigmas)
    epsilons = np.array(epsilons)
    
    ONE_4PI_EPS0_NM = 138.935456 / 4.184 # ~ 33.20637 kcal * nm / (mol * e^2)
    
    def compute_pair_energy(group_a, group_b):
        e_coul = 0.0
        e_lj = 0.0
        for i in group_a:
            for j in group_b:
                dr = np.linalg.norm(pos_array[i] - pos_array[j]) # nm
                if dr > 0.01:
                    e_coul += ONE_4PI_EPS0_NM * charges[i] * charges[j] / dr
                    sig_ij = 0.5 * (sigmas[i] + sigmas[j])
                    eps_ij = np.sqrt(epsilons[i] * epsilons[j])
                    if eps_ij > 1e-6 and sig_ij > 1e-6:
                        ratio = sig_ij / dr
                        ratio6 = ratio**6
                        ratio12 = ratio6**2
                        e_lj += 4.0 * eps_ij * (ratio12 - ratio6)
        return e_coul, e_lj, e_coul + e_lj

    e_coul_prot, e_lj_prot, e_tot_prot = compute_pair_energy(lig_atoms, prot_atoms)
    _, _, e_tot_r71 = compute_pair_energy(lig_atoms, r71_atoms)
    _, _, e_tot_r71_sc = compute_pair_energy(lig_atoms, r71_sidechain)
    _, _, e_tot_e153 = compute_pair_energy(lig_atoms, e153_atoms)
    _, _, e_tot_e153_sc = compute_pair_energy(lig_atoms, e153_sidechain)
    _, _, e_tot_h177 = compute_pair_energy(lig_atoms, h177_atoms)
    
    print(f"Total Ligand-Receptor Interaction: {e_tot_prot:.2f} kcal/mol (Coul: {e_coul_prot:.2f}, LJ: {e_lj_prot:.2f})", flush=True)
    print(f"  -> Interaction with Arg71 (Ortho anchor):   {e_tot_r71:.2f} kcal/mol (Sidechain penalty R71A: {-e_tot_r71_sc:+.2f} kcal/mol)", flush=True)
    print(f"  -> Interaction with Glu153 (Allo anchor):  {e_tot_e153:.2f} kcal/mol (Sidechain penalty E153A: {-e_tot_e153_sc:+.2f} kcal/mol)", flush=True)
    print(f"  -> Interaction with His177 (Allo anchor):  {e_tot_h177:.2f} kcal/mol", flush=True)
    
    # Calculate all residue interactions to get top contributors
    per_res_energies = []
    for orig_rid, group in res_atom_groups.items():
        _, _, e_res = compute_pair_energy(lig_atoms, group["atoms"])
        if abs(e_res) > 0.5:
            per_res_energies.append((orig_rid, group["name"], e_res))
    per_res_energies.sort(key=lambda x: x[2])
    print(f"  -> Top favorable residues: {', '.join([f'{r[1]}{r[0]} ({r[2]:.2f})' for r in per_res_energies[:6]])}", flush=True)
    
    # 100 ps MD relaxation on GPU with backbone restraints
    print("Running 100 ps MD relaxation on GPU (CUDA)...", flush=True)
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
    lig_start_pos = pos_array[lig_atoms]
    
    rmsd_history = []
    total_samples = 10 # 100 ps total (10 ps per sample)
    for step in range(total_samples):
        simulation.step(5000) # 10 ps
        cur_pos = simulation.context.getState(getPositions=True).getPositions()
        cur_arr = np.array([[p.x, p.y, p.z] for p in cur_pos.value_in_unit(unit.nanometer)])
        cur_lig = cur_arr[lig_atoms]
        rmsd = np.sqrt(np.mean(np.sum((cur_lig - lig_start_pos)**2, axis=1))) * 10.0 # Angstrom
        rmsd_history.append(float(rmsd))
        
    final_rmsd = rmsd_history[-1]
    mean_rmsd_last50ps = float(np.mean(rmsd_history[-5:]))
    print(f"MD Complete: Final RMSD = {final_rmsd:.2f} A, Last 50ps Mean RMSD = {mean_rmsd_last50ps:.2f} A", flush=True)
    
    return {
        "pose_id": pose_id,
        "name": pose_info["name"],
        "mode": pose_info["mode"],
        "e_tot_prot": float(e_tot_prot),
        "e_coul_prot": float(e_coul_prot),
        "e_lj_prot": float(e_lj_prot),
        "e_tot_r71": float(e_tot_r71),
        "r71a_penalty": float(-e_tot_r71_sc),
        "e_tot_e153": float(e_tot_e153),
        "e153a_penalty": float(-e_tot_e153_sc),
        "e_tot_h177": float(e_tot_h177),
        "final_rmsd": float(final_rmsd),
        "mean_rmsd": float(mean_rmsd_last50ps),
        "rmsd_history": rmsd_history
    }

def main():
    results = []
    for pose in POSES:
        res = evaluate_pose(pose)
        results.append(res)
        
    out_json = os.path.join(WORK_DIR, "openmm_pilot_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll poses evaluated! Results written to {out_json}")

if __name__ == "__main__":
    main()
