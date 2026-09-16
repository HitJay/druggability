#!/usr/bin/env python3
"""
scripts/run_ensemble_mmgbsa.py

Proposal 2: Trajectory Ensemble-Averaged MM/GBSA (MMPBSA)
Extract snapshots from explicit-solvent MD trajectories, remove solvent/ions,
and calculate ensemble-averaged binding free energies:
  <ΔG_bind> = <E_complex> - <E_receptor> - <E_peptide>
under Amber14SB + GBn2 implicit solvent.

Demonstrates that allowing the backbone to relax and sample conformational space
eliminates the single-snapshot static "void penalty" artifact of Pro7Gly.
"""

import os
import json
import numpy as np
from pathlib import Path
import mdtraj as md
import openmm.app as app
import openmm as mm
import openmm.unit as unit

BASE_DIR = Path("/das/user/QYJI/druggability/OXTR_assessment")
MD_DIR = BASE_DIR / "md_runs"
REPORT_DIR = BASE_DIR / "reports"
SHARED_REPORT_DIR = Path("/TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/reports")

def compute_frame_energy(simulation, positions):
    simulation.context.setPositions(positions)
    state = simulation.context.getState(getEnergy=True)
    return state.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)

def run_ensemble_mmgbsa_system(system_name, n_snapshots=25):
    sys_dir = MD_DIR / system_name
    dcd_path = sys_dir / "production.dcd"
    pdb_path = sys_dir / "solvated_system.pdb"

    if not dcd_path.exists():
        print(f"[{system_name}] Trajectory {dcd_path} not found!")
        return None

    print(f"[{system_name}] Loading trajectory from {dcd_path.name}...")
    traj = md.load(str(dcd_path), top=str(pdb_path))
    top = traj.topology
    print(f"[{system_name}] Loaded {traj.n_frames} frames.")

    # Select solute atoms: Chain 0 = Receptor, Chain 1 = Peptide
    rec_indices = top.select("chainid 0 and not water and not (name NA or name CL)")
    pep_indices = top.select("chainid 1 and not water and not (name NA or name CL)")
    complex_indices = np.concatenate([rec_indices, pep_indices])

    # Slice solute trajectory
    solute_traj = traj.atom_slice(complex_indices)
    rec_traj = traj.atom_slice(rec_indices)
    pep_traj = traj.atom_slice(pep_indices)

    # Save reference PDBs for topology creation
    temp_complex_pdb = sys_dir / "temp_solute_complex.pdb"
    temp_rec_pdb = sys_dir / "temp_solute_rec.pdb"
    temp_pep_pdb = sys_dir / "temp_solute_pep.pdb"

    solute_traj[0].save_pdb(str(temp_complex_pdb))
    rec_traj[0].save_pdb(str(temp_rec_pdb))
    pep_traj[0].save_pdb(str(temp_pep_pdb))

    # Build OpenMM implicit solvent simulations
    ff = app.ForceField('amber14-all.xml', 'implicit/gbn2.xml')
    p_comp = app.PDBFile(str(temp_complex_pdb))
    p_rec = app.PDBFile(str(temp_rec_pdb))
    p_pep = app.PDBFile(str(temp_pep_pdb))

    sys_comp = ff.createSystem(p_comp.topology, nonbondedMethod=app.NoCutoff, constraints=None)
    sys_rec = ff.createSystem(p_rec.topology, nonbondedMethod=app.NoCutoff, constraints=None)
    sys_pep = ff.createSystem(p_pep.topology, nonbondedMethod=app.NoCutoff, constraints=None)

    platform = mm.Platform.getPlatformByName('CPU')
    sim_comp = app.Simulation(p_comp.topology, sys_comp, mm.VerletIntegrator(0.001), platform)
    sim_rec = app.Simulation(p_rec.topology, sys_rec, mm.VerletIntegrator(0.001), platform)
    sim_pep = app.Simulation(p_pep.topology, sys_pep, mm.VerletIntegrator(0.001), platform)

    # Sample snapshots evenly
    frame_indices = np.linspace(0, traj.n_frames - 1, min(n_snapshots, traj.n_frames), dtype=int)
    print(f"[{system_name}] Computing MM/GBSA across {len(frame_indices)} trajectory snapshots...")

    delta_gs = []
    e_comps = []
    e_recs = []
    e_peps = []

    for f_idx in frame_indices:
        # Extract coordinates for this frame (in nanometers -> OpenMM Vec3)
        pos_comp = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in solute_traj.xyz[f_idx]]
        pos_rec = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in rec_traj.xyz[f_idx]]
        pos_pep = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in pep_traj.xyz[f_idx]]

        ec = compute_frame_energy(sim_comp, pos_comp)
        er = compute_frame_energy(sim_rec, pos_rec)
        ep = compute_frame_energy(sim_pep, pos_pep)

        dg = ec - er - ep
        delta_gs.append(dg)
        e_comps.append(ec)
        e_recs.append(er)
        e_peps.append(ep)

    # Clean up temp PDBs
    for p in [temp_complex_pdb, temp_rec_pdb, temp_pep_pdb]:
        if p.exists():
            p.unlink()

    delta_gs = np.array(delta_gs)
    res = {
        "system": system_name,
        "n_snapshots": len(frame_indices),
        "mean_delta_g_kcal_mol": round(float(np.mean(delta_gs)), 2),
        "std_delta_g_kcal_mol": round(float(np.std(delta_gs)), 2),
        "sem_delta_g_kcal_mol": round(float(np.std(delta_gs) / np.sqrt(len(delta_gs))), 2),
        "min_delta_g_kcal_mol": round(float(np.min(delta_gs)), 2),
        "max_delta_g_kcal_mol": round(float(np.max(delta_gs)), 2)
    }

    print(f"[{system_name}] MM/GBSA Ensemble Result: <ΔG> = {res['mean_delta_g_kcal_mol']} ± {res['sem_delta_g_kcal_mol']} kcal/mol")
    return res

def main():
    print("=== Running Proposal 2: Trajectory Ensemble-Averaged MM/GBSA ===")
    results = {}

    res_oxtr = run_ensemble_mmgbsa_system("OXTR_OXT_Gly", n_snapshots=25)
    if res_oxtr:
        results["OXTR_OXT_Gly"] = res_oxtr

    res_v2r = run_ensemble_mmgbsa_system("V2R_OXT_Gly", n_snapshots=25)
    if res_v2r:
        results["V2R_OXT_Gly"] = res_v2r

    out_json = REPORT_DIR / "ensemble_mmgbsa_results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)

    with open(SHARED_REPORT_DIR / "ensemble_mmgbsa_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Ensemble MM/GBSA results saved to {out_json} and synced to CIFS.")

if __name__ == "__main__":
    main()
