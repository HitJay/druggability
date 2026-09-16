#!/usr/bin/env python3
"""
scripts/run_stability_md.py

All-atom explicit-solvent Molecular Dynamics (MD) simulation on A100 GPU:
Compare binding stability & unbinding dynamics of OXT_Gly:
  - System A: OXTR : OXT_Gly (cognate, spacious vestibule)
  - System B: V2R : OXT_Gly (counter-screen, constricted Helix I)

Protocol:
1. Solvation in TIP3P water box (1.0 nm padding) + 0.15 M NaCl neutralizing ions.
2. Amber14SB + TIP3P, PME nonbonded (1.0 nm cutoff), HBonds constrained, dt = 2 fs.
3. Energy minimization (500 steps).
4. Restrained NPT equilibration (50 ps) at 310 K, 1 bar.
5. Production NPT simulation (unrestrained) with DCD trajectory saving.
6. Post-processing with MDTraj:
   - Peptide backbone RMSD
   - Receptor CA RMSD
   - Tyr2(OH) - TM7 kink H-bond distance
   - Peptide-Pocket Centroid Distance
"""

import os
import sys
import time
import argparse
import json
import numpy as np
from pathlib import Path

import openmm as mm
import openmm.app as app
import openmm.unit as unit
import mdtraj as md

def run_system(system_name, complex_pdb_path, out_dir, gpu_id="0", length_ns=2.0):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = out_dir / "simulation.log"
    print(f"[{system_name}] Starting setup on GPU {gpu_id} for {length_ns} ns...")

    # 1. Load PDB and Solvate
    pdb = app.PDBFile(str(complex_pdb_path))
    modeller = app.Modeller(pdb.topology, pdb.positions)
    ff = app.ForceField('amber14-all.xml', 'amber14/tip3p.xml')
    
    print(f"[{system_name}] Adding explicit TIP3P solvent (1.0 nm padding, 0.15 M NaCl)...")
    modeller.addSolvent(ff, model='tip3p', padding=1.0 * unit.nanometers, ionicStrength=0.15 * unit.molar)
    
    solvated_pdb = out_dir / "solvated_system.pdb"
    with open(solvated_pdb, "w") as f:
        app.PDBFile.writeFile(modeller.topology, modeller.positions, f)
    
    num_atoms = modeller.topology.getNumAtoms()
    print(f"[{system_name}] Solvated system built: {num_atoms} atoms.")

    # 2. Build OpenMM System
    sys = ff.createSystem(
        modeller.topology,
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometers,
        constraints=app.HBonds
    )
    sys.addForce(mm.MonteCarloBarostat(1.0 * unit.bar, 310.0 * unit.kelvin, 25))

    integrator = mm.LangevinMiddleIntegrator(310.0 * unit.kelvin, 1.0 / unit.picosecond, 0.002 * unit.picoseconds)
    platform = mm.Platform.getPlatformByName('CUDA')
    # Use double precision on CUDA to eliminate fixed-point accumulator overflow on clashing systems
    props = {'DeviceIndex': str(gpu_id), 'Precision': 'double'}
    sim = app.Simulation(modeller.topology, sys, integrator, platform, props)
    sim.context.setPositions(modeller.positions)

    # 3. Minimization
    print(f"[{system_name}] Minimizing energy...")
    sim.minimizeEnergy(maxIterations=1000, tolerance=5.0 * unit.kilojoules_per_mole / unit.nanometer)
    
    # 4. Equilibration (50 ps)
    print(f"[{system_name}] Running NPT equilibration (50 ps)...")
    sim.context.setVelocitiesToTemperature(310.0 * unit.kelvin)
    sim.step(25000)
    print(f"[{system_name}] Equilibration successfully completed.")

    # 5. Production (length_ns)
    total_steps = int((length_ns * 1000.0) / 0.002)  # dt = 2 fs
    save_interval = 10000  # every 20 ps
    
    dcd_path = out_dir / "production.dcd"
    sim.reporters.append(app.DCDReporter(str(dcd_path), save_interval))
    sim.reporters.append(app.StateDataReporter(
        str(log_file), save_interval,
        step=True, potentialEnergy=True, temperature=True, progress=True,
        remainingTime=True, speed=True, totalSteps=total_steps
    ))

    print(f"[{system_name}] Running NPT production: {total_steps} steps ({length_ns} ns)...")
    t0 = time.time()
    sim.step(total_steps)
    total_time = time.time() - t0
    
    speed_ns_day = (length_ns) / (total_time / 86400)
    print(f"[{system_name}] Simulation complete in {total_time:.1f} s ({speed_ns_day:.1f} ns/day).")

    # 6. Trajectory Analysis with MDTraj
    print(f"[{system_name}] Analyzing trajectory...")
    traj = md.load(str(dcd_path), top=str(solvated_pdb))
    
    # Identify Receptor and Peptide atoms
    # Chain 0 = Receptor, Chain 1 = Peptide (OXT_Gly)
    top = traj.topology
    pep_atoms = top.select("chainid 1")
    pep_bb = top.select("chainid 1 and (name CA or name C or name N)")
    rec_ca = top.select("chainid 0 and name CA")

    # Calculate RMSD
    # Align trajectory on receptor CA to remove overall translation/rotation
    traj.superpose(traj, frame=0, atom_indices=rec_ca)
    
    rec_rmsd = md.rmsd(traj, traj, frame=0, atom_indices=rec_ca) * 10.0  # to Angstrom
    pep_bb_rmsd = md.rmsd(traj, traj, frame=0, atom_indices=pep_bb) * 10.0 # to Angstrom

    # Tyr2 OH to Leu316(7QVM) / homologous Leu312(7DW9) O distance
    # In OXT_Gly, residue index 1 in peptide is Tyr2
    tyr2_oh = top.select("chainid 1 and resSeq 2 and (name OH or name CZ)")
    if "OXTR" in system_name:
        kink_o = top.select("chainid 0 and resSeq 316 and name O")
    else:
        kink_o = top.select("chainid 0 and resSeq 312 and name O")

    if len(tyr2_oh) > 0 and len(kink_o) > 0:
        pairs = np.array([[tyr2_oh[0], kink_o[0]]])
        hbond_dist = md.compute_distances(traj, pairs)[:, 0] * 10.0 # to Angstrom
    else:
        hbond_dist = np.zeros(traj.n_frames)

    # Peptide-pocket centroid distance
    pep_centroid = md.compute_center_of_mass(traj.atom_slice(pep_atoms))
    rec_centroid = md.compute_center_of_mass(traj.atom_slice(rec_ca))
    drift_dist = np.linalg.norm(pep_centroid - rec_centroid, axis=1) * 10.0 # to Angstrom

    times_ns = np.linspace(0, length_ns, traj.n_frames)

    # Save metrics JSON
    metrics = {
        "system": system_name,
        "length_ns": length_ns,
        "n_frames": traj.n_frames,
        "speed_ns_day": round(float(speed_ns_day), 1),
        "rec_ca_rmsd_mean_A": round(float(np.mean(rec_rmsd)), 2),
        "rec_ca_rmsd_std_A": round(float(np.std(rec_rmsd)), 2),
        "pep_bb_rmsd_mean_A": round(float(np.mean(pep_bb_rmsd)), 2),
        "pep_bb_rmsd_std_A": round(float(np.std(pep_bb_rmsd)), 2),
        "pep_bb_rmsd_final_A": round(float(pep_bb_rmsd[-1]), 2),
        "tyr2_kink_dist_mean_A": round(float(np.mean(hbond_dist)), 2),
        "tyr2_kink_dist_final_A": round(float(hbond_dist[-1]), 2),
        "hbond_formed_fraction": round(float(np.mean(hbond_dist < 3.5)), 3),
        "drift_mean_A": round(float(np.mean(drift_dist)), 2),
        "drift_final_A": round(float(drift_dist[-1]), 2)
    }

    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Save CSV for plotting
    csv_path = out_dir / "trajectory_data.csv"
    with open(csv_path, "w") as f:
        f.write("time_ns,rec_rmsd_A,pep_rmsd_A,tyr2_kink_dist_A,drift_A\n")
        for t, r_r, p_r, hb, dr in zip(times_ns, rec_rmsd, pep_bb_rmsd, hbond_dist, drift_dist):
            f.write(f"{t:.3f},{r_r:.3f},{p_r:.3f},{hb:.3f},{dr:.3f}\n")

    print(f"[{system_name}] Analysis complete. Metrics:")
    print(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", required=True, choices=["OXTR_OXT_Gly", "V2R_OXT_Gly"])
    parser.add_argument("--gpu", default="0")
    parser.add_argument("--ns", type=float, default=2.0)
    args = parser.parse_args()

    base_dir = Path("/das/user/QYJI/druggability/OXTR_assessment")
    if args.system == "OXTR_OXT_Gly":
        pdb_path = base_dir / "structures/OXTR_OXT_Gly_complex.min.pdb"
    else:
        pdb_path = base_dir / "structures/V2R_OXT_Gly_complex.min.pdb"

    out_dir = base_dir / f"md_runs/{args.system}"
    run_system(args.system, pdb_path, out_dir, gpu_id=args.gpu, length_ns=args.ns)
