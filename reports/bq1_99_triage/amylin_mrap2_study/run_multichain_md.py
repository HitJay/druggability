#!/usr/bin/env python3
"""
Run explicit-solvent NPT MD (OpenMM Amber14SB + TIP3P, 0.15 M NaCl, 310 K, 1 bar)
on multi-chain receptor/peptide complexes (with automatic resume if production.dcd exists!)
and compute:
  1. Peptide / partner backbone RMSD (mean & final)
  2. Multi-chain MM/GBSA binding free energy <dG_bind> = <E_complex - E_receptor - E_ligand>
  3. Per-residue interaction energy decomposition (vdW + Coulomb with PBC minimum-image)
  4. Dynamic hydrogen bond persistence network (Baker-Hubbard)
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("multichain_md")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--complex-pdb", type=str, required=True)
    parser.add_argument("--out-dir", type=str, required=True)
    parser.add_argument("--output-json", type=str, required=True)
    parser.add_argument("--rec-chains", type=str, required=True, help="Comma-separated receptor chain IDs, e.g. C,R or C,R,M")
    parser.add_argument("--pep-chains", type=str, required=True, help="Comma-separated peptide/ligand chain IDs, e.g. P or L")
    parser.add_argument("--length-ns", type=float, default=0.2)
    parser.add_argument("--n-snapshots", type=int, default=15)
    parser.add_argument("--gpu-id", type=int, default=0)
    parser.add_argument("--dt-fs", type=float, default=2.0)
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

    rec_chain_ids = [x.strip() for x in args.rec_chains.split(",") if x.strip()]
    pep_chain_ids = [x.strip() for x in args.pep_chains.split(",") if x.strip()]

    import mdtraj as md
    import numpy as np
    import openmm as mm
    import openmm.app as app
    import openmm.unit as unit
    import pdbfixer

    logger.info("Loading PDB: %s (rec=%s, pep=%s)", args.complex_pdb, rec_chain_ids, pep_chain_ids)
    fixer = pdbfixer.PDBFixer(filename=str(args.complex_pdb))
    fixer.findMissingResidues()
    fixer.missingResidues = {}
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)

    # Map original chain IDs to 0-based chain index from fixer.topology BEFORE PDBFile.writeFile renames them
    chain_id_to_md_idx = {c.id: idx for idx, c in enumerate(fixer.topology.chains())}
    logger.info("Original chain map: %s", chain_id_to_md_idx)

    clean_pdb = out_dir / "prepared_complex.pdb"
    solvated_pdb = out_dir / "solvated_system.pdb"
    dcd_path = out_dir / "production.dcd"
    sim_log = out_dir / "simulation.log"

    ff = app.ForceField("amber14-all.xml", "amber14/tip3p.xml")

    if dcd_path.exists() and solvated_pdb.exists() and dcd_path.stat().st_size > 10000:
        logger.info("Found existing trajectory %s — reusing without re-running GPU MD!", dcd_path.name)
        pdb_solv = app.PDBFile(str(solvated_pdb))
        system = ff.createSystem(
            pdb_solv.topology,
            nonbondedMethod=app.PME,
            nonbondedCutoff=1.0 * unit.nanometers,
            constraints=app.HBonds,
        )
        ns_per_day = 0.0
        if sim_log.exists():
            lines = [l for l in sim_log.read_text().splitlines() if not l.startswith("#") and l.strip()]
            if lines:
                try:
                    ns_per_day = float(lines[-1].split(",")[-1])
                except Exception:
                    pass
    else:
        with open(clean_pdb, "w") as f:
            app.PDBFile.writeFile(fixer.topology, fixer.positions, f)

        logger.info("Solvating with TIP3P + 0.15 M NaCl (1.0 nm padding)...")
        pdb = app.PDBFile(str(clean_pdb))
        modeller = app.Modeller(pdb.topology, pdb.positions)
        modeller.addSolvent(
            ff,
            model="tip3p",
            padding=1.0 * unit.nanometers,
            ionicStrength=0.15 * unit.molar,
        )

        with open(solvated_pdb, "w") as f:
            app.PDBFile.writeFile(modeller.topology, modeller.positions, f)

        n_atoms = modeller.topology.getNumAtoms()
        logger.info("Solvated system constructed: %d total atoms.", n_atoms)

        system = ff.createSystem(
            modeller.topology,
            nonbondedMethod=app.PME,
            nonbondedCutoff=1.0 * unit.nanometers,
            constraints=app.HBonds,
        )
        system.addForce(mm.MonteCarloBarostat(1.0 * unit.bar, 310.0 * unit.kelvin, 25))

        dt = args.dt_fs * 0.001 * unit.picoseconds
        integrator = mm.LangevinMiddleIntegrator(310.0 * unit.kelvin, 1.0 / unit.picosecond, dt)
        platform = mm.Platform.getPlatformByName("CUDA")
        props = {"DeviceIndex": str(args.gpu_id), "Precision": "double"}
        simulation = app.Simulation(modeller.topology, system, integrator, platform, props)
        simulation.context.setPositions(modeller.positions)

        logger.info("Executing energy minimization...")
        simulation.minimizeEnergy(
            maxIterations=1000,
            tolerance=5.0 * unit.kilojoules_per_mole / unit.nanometer,
        )

        equil_steps = 10000
        logger.info("Running NPT equilibration (%d steps, 20 ps)...", equil_steps)
        simulation.context.setVelocitiesToTemperature(310.0 * unit.kelvin)
        simulation.step(equil_steps)

        prod_steps = max(1000, int((args.length_ns * 1000.0) / args.dt_fs))
        save_interval = max(50, prod_steps // max(1, args.n_snapshots))

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

        logger.info("Launching NPT production: %d steps (%.2f ns) on GPU %d...", prod_steps, args.length_ns, args.gpu_id)
        t_prod_start = time.time()
        simulation.step(prod_steps)
        prod_time = time.time() - t_prod_start
        ns_per_day = (args.length_ns / (prod_time / 86400.0)) if prod_time > 0 else 0.0
        logger.info("Production finished in %.1fs (Performance: %.1f ns/day).", prod_time, ns_per_day)

    # Post-processing
    traj = md.load(str(dcd_path), top=str(solvated_pdb))
    top = traj.topology
    n_frames = traj.n_frames

    rec_md_chains = [chain_id_to_md_idx[cid] for cid in rec_chain_ids]
    pep_md_chains = [chain_id_to_md_idx[cid] for cid in pep_chain_ids]

    # Re-image every solute chain relative to chain 0 COM under PBC so NoCutoff GBn2 MM/GBSA & Baker-Hubbard see true bound geometry
    all_solute_chains = rec_md_chains + pep_md_chains
    ref_chain_atoms = top.select(f"chainid {all_solute_chains[0]} and not water and not (name NA or name CL)")
    for c_idx in all_solute_chains[1:]:
        c_atoms = top.select(f"chainid {c_idx} and not water and not (name NA or name CL)")
        for f_idx in range(n_frames):
            box = traj.unitcell_lengths[f_idx]
            com_ref = traj.xyz[f_idx, ref_chain_atoms].mean(axis=0)
            com_c = traj.xyz[f_idx, c_atoms].mean(axis=0)
            shift = np.round((com_c - com_ref) / box) * box
            traj.xyz[f_idx, c_atoms] -= shift

    rec_indices = np.concatenate([
        top.select(f"chainid {c_idx} and not water and not (name NA or name CL)")
        for c_idx in rec_md_chains
    ])
    pep_indices = np.concatenate([
        top.select(f"chainid {c_idx} and not water and not (name NA or name CL)")
        for c_idx in pep_md_chains
    ])
    complex_indices = np.concatenate([rec_indices, pep_indices])

    solute_traj = traj.atom_slice(complex_indices)
    rec_traj = traj.atom_slice(rec_indices)
    pep_traj = traj.atom_slice(pep_indices)

    # Backbone RMSD of peptide/ligand
    pep_bb = pep_traj.topology.select("backbone")
    if len(pep_bb) == 0:
        pep_bb = pep_traj.topology.select("name CA")
    pep_rmsd_nm = md.rmsd(pep_traj, pep_traj, 0, atom_indices=pep_bb)
    pep_rmsd_angstrom = (pep_rmsd_nm * 10.0).tolist()
    mean_pep_rmsd = float(np.mean(pep_rmsd_angstrom))
    final_pep_rmsd = float(pep_rmsd_angstrom[-1])

    # Also compute complex solute backbone RMSD
    comp_bb = solute_traj.topology.select("backbone")
    comp_rmsd_nm = md.rmsd(solute_traj, solute_traj, 0, atom_indices=comp_bb)
    mean_comp_rmsd = float(np.mean(comp_rmsd_nm * 10.0))

    # Dynamic H-bonds
    raw_hbonds = md.baker_hubbard(traj, freq=0.0, exclude_water=True)
    rec_set = set(rec_indices.tolist())
    pep_set = set(pep_indices.tolist())
    inter_hbonds = {}
    for d, h_atom, a in raw_hbonds:
        if (d in rec_set and a in pep_set) or (d in pep_set and a in rec_set):
            d_res = top.atom(d).residue
            a_res = top.atom(a).residue
            donor_str = f"{d_res.name}{d_res.resSeq}@{top.atom(d).name}"
            acceptor_str = f"{a_res.name}{a_res.resSeq}@{top.atom(a).name}"
            pair_key = (donor_str, acceptor_str)
            inter_hbonds[pair_key] = inter_hbonds.get(pair_key, 0) + 1

    hbond_persistence_list = []
    for (donor, acceptor), count in sorted(inter_hbonds.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / n_frames) * 100.0, 1)
        hbond_persistence_list.append({
            "donor": donor,
            "acceptor": acceptor,
            "frame_count": count,
            "total_frames": n_frames,
            "persistence_pct": pct,
        })

    # Per-residue interaction energy decomposition (vdW + Coulomb) + total nonbonded IE
    nb_force = next(f for f in system.getForces() if isinstance(f, mm.NonbondedForce))
    q_list, sig_list, eps_list = [], [], []
    for i in range(nb_force.getNumParticles()):
        q, sig, eps = nb_force.getParticleParameters(i)
        q_list.append(q.value_in_unit(unit.elementary_charge))
        sig_list.append(sig.value_in_unit(unit.nanometers))
        eps_list.append(eps.value_in_unit(unit.kilojoules_per_mole))

    q_arr = np.array(q_list)
    sig_arr = np.array(sig_list)
    eps_arr = np.array(eps_list)

    pep_res_groups = {}
    for a_idx in pep_indices:
        r = top.atom(a_idx).residue
        r_key = (r.resSeq, r.name)
        pep_res_groups.setdefault(r_key, []).append(a_idx)

    ONE_4PI_EPS0 = 138.935456
    KJ_TO_KCAL = 0.239005736

    per_res_trajs = {k: [] for k in pep_res_groups}
    per_res_vdw_trajs = {k: [] for k in pep_res_groups}
    for f_idx in range(n_frames):
        box = traj.unitcell_lengths[f_idx]
        frame_xyz = traj.xyz[f_idx]
        for r_key, p_indices in pep_res_groups.items():
            p_idx = np.array(p_indices)
            p_pos = frame_xyz[p_idx]
            r_pos = frame_xyz[rec_indices]
            diff = p_pos[:, None, :] - r_pos[None, :, :]
            diff -= np.round(diff / box) * box
            dists = np.linalg.norm(diff, axis=-1)
            mask = dists < 1.0
            q_prod = q_arr[p_idx, None] * q_arr[None, rec_indices]
            e_coul = np.sum((ONE_4PI_EPS0 * q_prod / np.maximum(dists, 0.08)) * mask)
            sig_comb = 0.5 * (sig_arr[p_idx, None] + sig_arr[None, rec_indices])
            eps_comb = np.sqrt(eps_arr[p_idx, None] * eps_arr[None, rec_indices])
            sr6 = (sig_comb / np.maximum(dists, 0.08)) ** 6
            sr12 = sr6 ** 2
            e_lj = np.sum((4.0 * eps_comb * (sr12 - sr6)) * mask)
            per_res_trajs[r_key].append(float((e_coul + e_lj) * KJ_TO_KCAL))
            per_res_vdw_trajs[r_key].append(float(e_lj * KJ_TO_KCAL))

    per_residue_decomposition = []
    total_vdw_frames = np.zeros(n_frames)
    total_nb_frames = np.zeros(n_frames)
    for k in pep_res_groups:
        total_vdw_frames += np.array(per_res_vdw_trajs[k])
        total_nb_frames += np.array(per_res_trajs[k])

    for (r_seq, r_name), e_vals in sorted(per_res_trajs.items(), key=lambda x: np.mean(x[1])):
        m_e = round(float(np.mean(e_vals)), 2)
        s_e = round(float(np.std(e_vals)), 2)
        m_vdw = round(float(np.mean(per_res_vdw_trajs[(r_seq, r_name)])), 2)
        per_residue_decomposition.append({
            "res_label": f"{r_name}{r_seq}",
            "res_seq": r_seq,
            "res_name": r_name,
            "mean_energy_kcal_mol": m_e,
            "std_energy_kcal_mol": s_e,
            "mean_vdw_kcal_mol": m_vdw,
        })

    # Implicit-solvent GBn2 MM/GBSA on solute snapshots using fixer topology sliced via Modeller
    logger.info("Computing GBn2 MM/GBSA over %d snapshots...", n_frames)
    ff_gb = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")

    def build_gb_sim(keep_chain_indices):
        m_sub = app.Modeller(fixer.topology, fixer.positions)
        to_del = [c for idx, c in enumerate(m_sub.topology.chains()) if idx not in keep_chain_indices]
        if to_del:
            m_sub.delete(to_del)
        sys_gb = ff_gb.createSystem(m_sub.topology, nonbondedMethod=app.NoCutoff, constraints=None)
        sim_gb = app.Simulation(m_sub.topology, sys_gb, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("CPU"))
        return sim_gb

    sim_comp = build_gb_sim(rec_md_chains + pep_md_chains)
    sim_rec = build_gb_sim(rec_md_chains)
    sim_pep = build_gb_sim(pep_md_chains)

    delta_gs = []
    for f_idx in range(n_frames):
        pos_comp = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in solute_traj.xyz[f_idx]]
        pos_rec = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in rec_traj.xyz[f_idx]]
        pos_pep = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in pep_traj.xyz[f_idx]]
        ec = compute_frame_energy(sim_comp, pos_comp)
        er = compute_frame_energy(sim_rec, pos_rec)
        ep = compute_frame_energy(sim_pep, pos_pep)
        delta_gs.append(round(float(ec - (er + ep)), 2))

    result_data = {
        "ok": True,
        "complex_name": Path(args.complex_pdb).stem,
        "receptor_chains": rec_chain_ids,
        "peptide_chains": pep_chain_ids,
        "length_ns": args.length_ns,
        "n_snapshots": n_frames,
        "mean_delta_g_gbn2": round(float(np.mean(delta_gs)), 2),
        "std_delta_g_gbn2": round(float(np.std(delta_gs)), 2),
        "delta_g_gbn2_trajectory": delta_gs,
        "mean_vdw_ie_kcal": round(float(np.mean(total_vdw_frames)), 2),
        "std_vdw_ie_kcal": round(float(np.std(total_vdw_frames)), 2),
        "mean_total_nb_ie_kcal": round(float(np.mean(total_nb_frames)), 2),
        "std_total_nb_ie_kcal": round(float(np.std(total_nb_frames)), 2),
        "mean_pep_rmsd": round(mean_pep_rmsd, 2),
        "final_pep_rmsd": round(final_pep_rmsd, 2),
        "mean_comp_rmsd": round(mean_comp_rmsd, 2),
        "pep_rmsd_trajectory": [round(x, 2) for x in pep_rmsd_angstrom],
        "ns_per_day": round(ns_per_day, 1),
        "hbond_persistence": hbond_persistence_list[:15],
        "per_residue_decomposition": per_residue_decomposition[:20],
        "elapsed_seconds": round(time.time() - t_start, 2),
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)
    logger.info("Saved %s: <dG_GBn2>=%.2f +/- %.2f kcal/mol, <E_vdW>=%.2f kcal/mol, RMSD=%.2f A",
                out_json.name, result_data["mean_delta_g_gbn2"], result_data["std_delta_g_gbn2"],
                result_data["mean_vdw_ie_kcal"], result_data["mean_pep_rmsd"])


if __name__ == "__main__":
    main()
