#!/usr/bin/env python3
"""
Internal worker for Peptide Ensemble MM/GBSA under isolated openfe-md venv.
Invoked by druggability.peptide.ensemble_md.run_ensemble_mmgbsa via subprocess.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("ensemble_md_worker")


def parse_args():
    parser = argparse.ArgumentParser(description="Peptide Ensemble MD & MM/GBSA worker")
    parser.add_argument("--complex-pdb", type=str, required=True, help="Path to complex PDB")
    parser.add_argument("--out-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--output-json", type=str, required=True, help="Path to output JSON")
    parser.add_argument("--length-ns", type=float, default=1.0, help="Production MD length in ns")
    parser.add_argument("--n-snapshots", type=int, default=25, help="Number of snapshots for MM/GBSA")
    parser.add_argument("--gpu-id", type=int, default=0, help="CUDA device index")
    parser.add_argument("--rec-chain", type=str, default=None, help="Receptor chain ID")
    parser.add_argument("--pep-chain", type=str, default=None, help="Peptide chain ID")
    parser.add_argument("--dt-fs", type=float, default=2.0, help="Timestep in fs (default: 2.0)")
    return parser.parse_args()


def compute_frame_energy(simulation, positions):
    import openmm.unit as unit

    simulation.context.setPositions(positions)
    state = simulation.context.getState(getEnergy=True)
    return state.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)


def main():
    t_start = time.time()
    args = parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = Path(args.output_json).resolve()

    import mdtraj as md
    import numpy as np
    import openmm as mm
    import openmm.app as app
    import openmm.unit as unit
    import pdbfixer

    # 1. PDB preparation and chain verification
    logger.info("Loading and preparing PDB: %s", args.complex_pdb)
    fixer = pdbfixer.PDBFixer(filename=str(args.complex_pdb))
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)

    clean_pdb = out_dir / "prepared_complex.pdb"
    with open(clean_pdb, "w") as f:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, f)

    # 2. Solvation in explicit TIP3P water box
    logger.info("Solvating complex with TIP3P + 0.15 M NaCl (1.0 nm padding)...")
    pdb = app.PDBFile(str(clean_pdb))
    modeller = app.Modeller(pdb.topology, pdb.positions)
    ff = app.ForceField("amber14-all.xml", "amber14/tip3p.xml")
    modeller.addSolvent(
        ff,
        model="tip3p",
        padding=1.0 * unit.nanometers,
        ionicStrength=0.15 * unit.molar,
    )

    solvated_pdb = out_dir / "solvated_system.pdb"
    with open(solvated_pdb, "w") as f:
        app.PDBFile.writeFile(modeller.topology, modeller.positions, f)

    n_atoms = modeller.topology.getNumAtoms()
    logger.info("Solvated system constructed: %d total atoms.", n_atoms)

    # 3. Build OpenMM System & Simulation
    system = ff.createSystem(
        modeller.topology,
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometers,
        constraints=app.HBonds,
    )
    system.addForce(mm.MonteCarloBarostat(1.0 * unit.bar, 310.0 * unit.kelvin, 25))

    dt = args.dt_fs * 0.001 * unit.picoseconds
    integrator = mm.LangevinMiddleIntegrator(
        310.0 * unit.kelvin, 1.0 / unit.picosecond, dt
    )

    platform = mm.Platform.getPlatformByName("CUDA")
    props = {"DeviceIndex": str(args.gpu_id), "Precision": "double"}
    simulation = app.Simulation(modeller.topology, system, integrator, platform, props)
    simulation.context.setPositions(modeller.positions)

    # 4. Energy Minimization
    logger.info("Executing energy minimization...")
    simulation.minimizeEnergy(
        maxIterations=1000,
        tolerance=5.0 * unit.kilojoules_per_mole / unit.nanometer,
    )

    # 5. Equilibration (10000 steps = 20 ps)
    equil_steps = 10000
    logger.info("Running NPT equilibration (%d steps, 20 ps)...", equil_steps)
    simulation.context.setVelocitiesToTemperature(310.0 * unit.kelvin)
    simulation.step(equil_steps)

    # 6. Production Simulation
    prod_steps = max(1000, int((args.length_ns * 1000.0) / args.dt_fs))
    save_interval = max(50, prod_steps // max(1, args.n_snapshots))

    dcd_path = out_dir / "production.dcd"
    sim_log = out_dir / "simulation.log"

    simulation.reporters.append(app.DCDReporter(str(dcd_path), save_interval))
    simulation.reporters.append(
        app.StateDataReporter(
            str(sim_log),
            save_interval,
            step=True,
            potentialEnergy=True,
            temperature=True,
            progress=True,
            remainingTime=True,
            speed=True,
            totalSteps=prod_steps,
        )
    )

    logger.info(
        "Launching NPT production: %d steps (%.2f ns) on GPU %d...",
        prod_steps,
        args.length_ns,
        args.gpu_id,
    )
    t_prod_start = time.time()
    simulation.step(prod_steps)
    prod_time = time.time() - t_prod_start
    ns_per_day = (args.length_ns / (prod_time / 86400.0)) if prod_time > 0 else 0.0
    logger.info("Production finished in %.1fs (Performance: %.1f ns/day).", prod_time, ns_per_day)

    # 7. Post-Processing with MDTraj & Implicit MM/GBSA
    logger.info("Loading trajectory for ensemble analysis from %s...", dcd_path.name)
    traj = md.load(str(dcd_path), top=str(solvated_pdb))
    top = traj.topology
    n_frames = traj.n_frames
    logger.info("Loaded %d trajectory frames.", n_frames)

    # Select Receptor vs Peptide solute chains
    rec_indices = top.select("chainid 0 and not water and not (name NA or name CL)")
    pep_indices = top.select("chainid 1 and not water and not (name NA or name CL)")

    if len(rec_indices) == 0 or len(pep_indices) == 0:
        # Fallback to general solute selection
        chains = list(top.chains)
        solute_chains = [c for c in chains if not any(r.is_water for r in c.residues)]
        solute_chains.sort(key=lambda c: c.n_residues, reverse=True)
        rec_idx = solute_chains[0].index
        pep_idx = solute_chains[1].index
        rec_indices = top.select(f"chainid {rec_idx} and not water and not (name NA or name CL)")
        pep_indices = top.select(f"chainid {pep_idx} and not water and not (name NA or name CL)")
        rec_chain_id = solute_chains[0].chain_id
        pep_chain_id = solute_chains[1].chain_id
    else:
        rec_chain_id = top.chain(0).chain_id
        pep_chain_id = top.chain(1).chain_id

    complex_indices = np.concatenate([rec_indices, pep_indices])

    # Slice solute trajectories for MM/GBSA and peptide analysis
    solute_traj = traj.atom_slice(complex_indices)
    rec_traj = traj.atom_slice(rec_indices)
    pep_traj = traj.atom_slice(pep_indices)

    # Compute Peptide Backbone RMSD on sliced peptide
    pep_bb = pep_traj.topology.select("backbone")
    if len(pep_bb) == 0:
        pep_bb = pep_traj.topology.select("name CA")
    if len(pep_bb) > 0:
        pep_rmsd_nm = md.rmsd(pep_traj, pep_traj, 0, atom_indices=pep_bb)
        pep_rmsd_angstrom = (pep_rmsd_nm * 10.0).tolist()
    else:
        pep_rmsd_angstrom = [0.0] * n_frames

    mean_pep_rmsd = float(np.mean(pep_rmsd_angstrom))
    final_pep_rmsd = float(pep_rmsd_angstrom[-1])

    temp_complex_pdb = out_dir / "temp_solute_complex.pdb"
    temp_rec_pdb = out_dir / "temp_solute_rec.pdb"
    temp_pep_pdb = out_dir / "temp_solute_pep.pdb"

    solute_traj[0].save_pdb(str(temp_complex_pdb))
    rec_traj[0].save_pdb(str(temp_rec_pdb))
    pep_traj[0].save_pdb(str(temp_pep_pdb))

    # Build OpenMM GBn2 Implicit Solvent Systems
    ff_gb = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")
    p_comp = app.PDBFile(str(temp_complex_pdb))
    p_rec = app.PDBFile(str(temp_rec_pdb))
    p_pep = app.PDBFile(str(temp_pep_pdb))

    sys_comp = ff_gb.createSystem(p_comp.topology, nonbondedMethod=app.NoCutoff, constraints=None)
    sys_rec = ff_gb.createSystem(p_rec.topology, nonbondedMethod=app.NoCutoff, constraints=None)
    sys_pep = ff_gb.createSystem(p_pep.topology, nonbondedMethod=app.NoCutoff, constraints=None)

    cpu_plat = mm.Platform.getPlatformByName("CPU")
    sim_comp = app.Simulation(p_comp.topology, sys_comp, mm.VerletIntegrator(0.001), cpu_plat)
    sim_rec = app.Simulation(p_rec.topology, sys_rec, mm.VerletIntegrator(0.001), cpu_plat)
    sim_pep = app.Simulation(p_pep.topology, sys_pep, mm.VerletIntegrator(0.001), cpu_plat)

    # Select snapshot frame indices
    n_snap = min(args.n_snapshots, n_frames)
    frame_indices = np.linspace(0, n_frames - 1, n_snap, dtype=int)
    logger.info("Computing MM/GBSA over %d snapshots...", len(frame_indices))

    delta_gs = []
    for f_idx in frame_indices:
        pos_comp = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in solute_traj.xyz[f_idx]]
        pos_rec = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in rec_traj.xyz[f_idx]]
        pos_pep = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in pep_traj.xyz[f_idx]]

        ec = compute_frame_energy(sim_comp, pos_comp)
        er = compute_frame_energy(sim_rec, pos_rec)
        ep = compute_frame_energy(sim_pep, pos_pep)
        dg = ec - (er + ep)
        delta_gs.append(round(float(dg), 2))

    mean_dg = round(float(np.mean(delta_gs)), 2)
    std_dg = round(float(np.std(delta_gs)), 2)
    min_dg = round(float(np.min(delta_gs)), 2)
    max_dg = round(float(np.max(delta_gs)), 2)

    # Clean up temp PDBs
    for p in [temp_complex_pdb, temp_rec_pdb, temp_pep_pdb]:
        if p.exists():
            p.unlink()

    # Stable binder heuristic: RMSD < 2.5 A and favorable mean ΔG < -10 kcal/mol
    is_stable = bool(mean_pep_rmsd < 2.5 and mean_dg < -10.0)

    elapsed_total = round(time.time() - t_start, 2)
    logger.info(
        "Ensemble MM/GBSA done: <ΔG> = %.2f ± %.2f kcal/mol (Range: [%.2f, %.2f]), Peptide RMSD = %.2f A",
        mean_dg,
        std_dg,
        min_dg,
        max_dg,
        mean_pep_rmsd,
    )

    result_data = {
        "ok": True,
        "complex_name": Path(args.complex_pdb).stem,
        "receptor_chain": rec_chain_id,
        "peptide_chain": pep_chain_id,
        "length_ns": args.length_ns,
        "n_snapshots": len(frame_indices),
        "mean_delta_g": mean_dg,
        "std_delta_g": std_dg,
        "min_delta_g": min_dg,
        "max_delta_g": max_dg,
        "delta_g_trajectory": delta_gs,
        "mean_pep_rmsd": round(mean_pep_rmsd, 2),
        "final_pep_rmsd": round(final_pep_rmsd, 2),
        "pep_rmsd_trajectory": [round(x, 2) for x in pep_rmsd_angstrom],
        "is_stable_binder": is_stable,
        "ns_per_day": round(ns_per_day, 1),
        "production_dcd": str(dcd_path),
        "solvated_pdb": str(solvated_pdb),
        "simulation_log": str(sim_log),
        "elapsed_seconds": elapsed_total,
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    logger.info("Results saved to %s", out_json)


if __name__ == "__main__":
    main()
