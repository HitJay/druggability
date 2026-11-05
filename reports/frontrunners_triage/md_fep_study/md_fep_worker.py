#!/usr/bin/env python3
"""
OpenMM Explicit-Solvent NPT MD + Ensemble GBn2 MM/GBSA + 8-Lambda Alchemical TI FEP Worker
Runs inside /data/user/QYJI/micromamba/envs/openfe-md/bin/python with CUDA Precision=double.
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

import mdtraj as md
import numpy as np
import openmm as mm
import openmm.app as app
import openmm.unit as unit
import pdbfixer

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("md_fep_worker")

BACKBONE_ATOMS = {"N", "CA", "C", "O", "OXT", "H", "HA", "HN", "H1", "H2", "H3"}
ONE_4PI_EPS0 = 138.935456  # kJ * nm / (mol * e^2)
KJ_TO_KCAL = 0.239005736


def compute_frame_energy(simulation, positions):
    simulation.context.setPositions(positions)
    state = simulation.context.getState(getEnergy=True)
    return state.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)


def renumber_pdb_lines(in_pdb: Path, out_pdb: Path, offset_a: int, offset_b: int):
    """Apply canonical UniProt residue numbering offsets to Chain A and Chain B."""
    out_lines = []
    for line in in_pdb.read_text().splitlines():
        if line.startswith(("ATOM  ", "HETATM")):
            ch = line[21]
            res_seq = int(line[22:26].strip())
            if ch == "A":
                new_seq = res_seq + offset_a
            elif ch == "B":
                new_seq = res_seq + offset_b
            else:
                new_seq = res_seq
            line = f"{line[:22]}{new_seq:4d}{line[26:]}"
        out_lines.append(line)
    out_pdb.write_text("\n".join(out_lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-json", type=str, required=True)
    parser.add_argument("--raw-pdb", type=str, required=True)
    parser.add_argument("--conf-json", type=str, required=True)
    parser.add_argument("--work-dir", type=str, required=True)
    parser.add_argument("--out-json", type=str, required=True)
    parser.add_argument("--length-ns", type=float, default=0.2)
    parser.add_argument("--n-snapshots", type=int, default=15)
    args = parser.parse_args()

    t_start = time.time()
    spec = json.loads(Path(args.spec_json).read_text())
    conf = json.loads(Path(args.conf_json).read_text())
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = Path(args.out_json)

    cA, cB = spec["chainA"], spec["chainB"]
    offset_a = int(cA["start"]) - 1
    offset_b = int(cB["start"]) - 1

    canonical_pdb = work_dir / "canonical_complex.pdb"
    renumber_pdb_lines(Path(args.raw_pdb), canonical_pdb, offset_a, offset_b)

    logger.info("[%s] Preparing PDB with PDBFixer (offsets: A=+%d, B=+%d)...", spec["id"], offset_a, offset_b)
    fixer = pdbfixer.PDBFixer(filename=str(canonical_pdb))
    fixer.findMissingResidues()
    fixer.missingResidues = {}
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)

    # Save residue numbers before PDBFile.writeFile
    orig_res_map = {}  # (chain_idx, res_idx_in_chain) -> canonical_res_seq
    for c_idx, ch in enumerate(fixer.topology.chains()):
        for r_idx, res in enumerate(ch.residues()):
            orig_res_map[(c_idx, r_idx)] = int(res.id)

    clean_pdb = work_dir / "prepared_complex.pdb"
    solvated_pdb = work_dir / "solvated_system.pdb"
    minimized_solute_pdb = work_dir / "minimized_solute.pdb"
    dcd_path = work_dir / "production.dcd"
    sim_log = work_dir / "simulation.log"

    ff = app.ForceField("amber14-all.xml", "amber14/tip3p.xml")

    if dcd_path.exists() and solvated_pdb.exists() and dcd_path.stat().st_size > 10000:
        logger.info("[%s] Reusing existing trajectory %s", spec["id"], dcd_path.name)
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
            app.PDBFile.writeFile(fixer.topology, fixer.positions, f, keepIds=True)

        logger.info("[%s] Solvating with TIP3P + 0.15 M NaCl (1.0 nm padding)...", spec["id"])
        pdb = app.PDBFile(str(clean_pdb))
        modeller = app.Modeller(pdb.topology, pdb.positions)
        modeller.addSolvent(
            ff,
            model="tip3p",
            padding=1.0 * unit.nanometers,
            ionicStrength=0.15 * unit.molar,
        )
        with open(solvated_pdb, "w") as f:
            app.PDBFile.writeFile(modeller.topology, modeller.positions, f, keepIds=True)

        n_atoms = modeller.topology.getNumAtoms()
        logger.info("[%s] Solvated system: %d atoms.", spec["id"], n_atoms)

        system = ff.createSystem(
            modeller.topology,
            nonbondedMethod=app.PME,
            nonbondedCutoff=1.0 * unit.nanometers,
            constraints=app.HBonds,
        )
        system.addForce(mm.MonteCarloBarostat(1.0 * unit.bar, 310.0 * unit.kelvin, 25))
        integrator = mm.LangevinMiddleIntegrator(310.0 * unit.kelvin, 1.0 / unit.picosecond, 0.002 * unit.picoseconds)
        platform = mm.Platform.getPlatformByName("CUDA")
        props = {"DeviceIndex": "0", "Precision": "double"}
        simulation = app.Simulation(modeller.topology, system, integrator, platform, props)
        simulation.context.setPositions(modeller.positions)

        logger.info("[%s] Energy minimization...", spec["id"])
        simulation.minimizeEnergy(maxIterations=1000, tolerance=5.0 * unit.kilojoules_per_mole / unit.nanometer)

        logger.info("[%s] NPT equilibration (10,000 steps = 20 ps)...", spec["id"])
        simulation.context.setVelocitiesToTemperature(310.0 * unit.kelvin)
        simulation.step(10000)

        prod_steps = max(1000, int((args.length_ns * 1000.0) / 2.0))
        save_interval = max(50, prod_steps // max(1, args.n_snapshots))
        simulation.reporters.append(app.DCDReporter(str(dcd_path), save_interval))
        simulation.reporters.append(
            app.StateDataReporter(
                str(sim_log), save_interval, step=True, potentialEnergy=True,
                temperature=True, progress=True, remainingTime=True, speed=True, totalSteps=prod_steps
            )
        )
        logger.info("[%s] Launching NPT production (%d steps, %.2f ns)...", spec["id"], prod_steps, args.length_ns)
        t_prod = time.time()
        simulation.step(prod_steps)
        prod_time = time.time() - t_prod
        ns_per_day = (args.length_ns / (prod_time / 86400.0)) if prod_time > 0 else 0.0
        logger.info("[%s] Production finished in %.1fs (%.1f ns/day).", spec["id"], prod_time, ns_per_day)

    # Load trajectory & post-process
    traj = md.load(str(dcd_path), top=str(solvated_pdb))
    top = traj.topology
    n_frames = traj.n_frames

    chain0_atoms = top.select("chainid 0 and not water and not (name NA or name CL)")
    chain1_atoms = top.select("chainid 1 and not water and not (name NA or name CL)")

    # PBC re-imaging of Chain 1 relative to Chain 0 COM
    for f_idx in range(n_frames):
        box = traj.unitcell_lengths[f_idx]
        com0 = traj.xyz[f_idx, chain0_atoms].mean(axis=0)
        com1 = traj.xyz[f_idx, chain1_atoms].mean(axis=0)
        shift = np.round((com1 - com0) / box) * box
        traj.xyz[f_idx, chain1_atoms] -= shift

    complex_indices = np.concatenate([chain0_atoms, chain1_atoms])
    solute_traj = traj.atom_slice(complex_indices)
    c0_traj = traj.atom_slice(chain0_atoms)
    c1_traj = traj.atom_slice(chain1_atoms)

    # Save last frame solute coordinates for FEP if needed
    c1_bb = c1_traj.topology.select("backbone")
    c1_rmsd_ang = (md.rmsd(c1_traj, c1_traj, 0, atom_indices=c1_bb) * 10.0).tolist()
    comp_bb = solute_traj.topology.select("backbone")
    comp_rmsd_ang = (md.rmsd(solute_traj, solute_traj, 0, atom_indices=comp_bb) * 10.0).tolist()

    # Map every solute residue to its canonical UniProt residue number
    res_to_canonical = {}
    for c_idx in (0, 1):
        ch_obj = top.chain(c_idx)
        for r_idx, r_obj in enumerate(ch_obj.residues):
            res_to_canonical[r_obj.index] = (
                "A" if c_idx == 0 else "B",
                cA["gene"] if c_idx == 0 else cB["gene"],
                orig_res_map.get((c_idx, r_idx), r_obj.resSeq),
                r_obj.name,
            )

    # Static heavy-atom interface contacts (<= 5.0 A) on frame 0
    xyz0_nm = traj.xyz[0]
    heavy0 = [a for a in chain0_atoms if top.atom(a).element.symbol != "H"]
    heavy1 = [a for a in chain1_atoms if top.atom(a).element.symbol != "H"]
    diff0 = xyz0_nm[heavy0][:, None, :] - xyz0_nm[heavy1][None, :, :]
    d0_ang = np.linalg.norm(diff0, axis=-1) * 10.0
    contact_pairs_5a = set()
    for i_idx, j_idx in np.argwhere(d0_ang <= 5.0):
        r0 = top.atom(heavy0[i_idx]).residue.index
        r1 = top.atom(heavy1[j_idx]).residue.index
        contact_pairs_5a.add((res_to_canonical[r0][2], res_to_canonical[r1][2]))

    # Dynamic H-bonds
    raw_hbonds = md.baker_hubbard(traj, freq=0.0, exclude_water=True)
    set0, set1 = set(chain0_atoms.tolist()), set(chain1_atoms.tolist())
    inter_hbonds = {}
    for d, h_atom, a in raw_hbonds:
        if (d in set0 and a in set1) or (d in set1 and a in set0):
            dr = top.atom(d).residue
            ar = top.atom(a).residue
            dc, dg, dseq, dname = res_to_canonical[dr.index]
            ac, ag, aseq, aname = res_to_canonical[ar.index]
            d_str = f"{dg}:{dname}{dseq}@{top.atom(d).name}"
            a_str = f"{ag}:{aname}{aseq}@{top.atom(a).name}"
            inter_hbonds[(d_str, a_str)] = inter_hbonds.get((d_str, a_str), 0) + 1

    hbond_list = []
    for (dn, ac), cnt in sorted(inter_hbonds.items(), key=lambda x: x[1], reverse=True)[:15]:
        hbond_list.append({
            "donor": dn,
            "acceptor": ac,
            "persistence_pct": round((cnt / n_frames) * 100.0, 1),
        })

    # Per-residue interaction energy decomposition (both Chain A and Chain B residues vs opposite chain)
    nb_force = next(f for f in system.getForces() if isinstance(f, mm.NonbondedForce))
    n_part = nb_force.getNumParticles()
    q_arr = np.zeros(n_part)
    sig_arr = np.zeros(n_part)
    eps_arr = np.zeros(n_part)
    for i in range(n_part):
        q, sig, eps = nb_force.getParticleParameters(i)
        q_arr[i] = q.value_in_unit(unit.elementary_charge)
        sig_arr[i] = sig.value_in_unit(unit.nanometers)
        eps_arr[i] = eps.value_in_unit(unit.kilojoules_per_mole)

    res_atom_groups = {}
    for a_idx in complex_indices:
        r_idx = top.atom(a_idx).residue.index
        res_atom_groups.setdefault(r_idx, []).append(a_idx)

    res_ie_trajs = {r_idx: [] for r_idx in res_atom_groups}
    res_vdw_trajs = {r_idx: [] for r_idx in res_atom_groups}
    for f_idx in range(n_frames):
        box = traj.unitcell_lengths[f_idx]
        f_xyz = traj.xyz[f_idx]
        for r_idx, a_list in res_atom_groups.items():
            ch_label = res_to_canonical[r_idx][0]
            opp_indices = chain1_atoms if ch_label == "A" else chain0_atoms
            p_idx = np.array(a_list)
            diff = f_xyz[p_idx][:, None, :] - f_xyz[opp_indices][None, :, :]
            diff -= np.round(diff / box) * box
            dists = np.linalg.norm(diff, axis=-1)
            mask = dists < 1.0
            q_prod = q_arr[p_idx, None] * q_arr[None, opp_indices]
            e_coul = np.sum((ONE_4PI_EPS0 * q_prod / np.maximum(dists, 0.08)) * mask)
            sig_c = 0.5 * (sig_arr[p_idx, None] + sig_arr[None, opp_indices])
            eps_c = np.sqrt(eps_arr[p_idx, None] * eps_arr[None, opp_indices])
            sr6 = (sig_c / np.maximum(dists, 0.08)) ** 6
            e_lj = np.sum((4.0 * eps_c * (sr6 ** 2 - sr6)) * mask)
            res_ie_trajs[r_idx].append(float((e_coul + e_lj) * KJ_TO_KCAL))
            res_vdw_trajs[r_idx].append(float(e_lj * KJ_TO_KCAL))

    per_res_decomp = []
    for r_idx, vals in sorted(res_ie_trajs.items(), key=lambda kv: np.mean(kv[1])):
        ch_l, gene_l, seq_num, r_name = res_to_canonical[r_idx]
        m_tot = round(float(np.mean(vals)), 2)
        m_vdw = round(float(np.mean(res_vdw_trajs[r_idx])), 2)
        if abs(m_tot) >= 0.2 or abs(m_vdw) >= 0.2:
            per_res_decomp.append({
                "chain": ch_l,
                "gene": gene_l,
                "res_seq": seq_num,
                "res_name": r_name,
                "res_label": f"{gene_l}:{r_name}{seq_num}",
                "mean_ie_kcal": m_tot,
                "mean_vdw_kcal": m_vdw,
            })

    # Total inter-chain vdW and Coulomb across Chain A -> Chain B
    tot_vdw_frames = np.zeros(n_frames)
    tot_nb_frames = np.zeros(n_frames)
    for r_idx in res_atom_groups:
        if res_to_canonical[r_idx][0] == "A":
            tot_vdw_frames += np.array(res_vdw_trajs[r_idx])
            tot_nb_frames += np.array(res_ie_trajs[r_idx])

    # Implicit-solvent GBn2 MM/GBSA over snapshots
    logger.info("[%s] Computing GBn2 MM/GBSA over %d snapshots...", spec["id"], n_frames)
    ff_gb = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")

    def build_gb_sim(keep_chains):
        m_sub = app.Modeller(fixer.topology, fixer.positions)
        to_del = [c for idx, c in enumerate(m_sub.topology.chains()) if idx not in keep_chains]
        if to_del:
            m_sub.delete(to_del)
        sys_gb = ff_gb.createSystem(m_sub.topology, nonbondedMethod=app.NoCutoff, constraints=None)
        return app.Simulation(m_sub.topology, sys_gb, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("CPU"))

    sim_comp = build_gb_sim([0, 1])
    sim_c0 = build_gb_sim([0])
    sim_c1 = build_gb_sim([1])
    delta_gs = []
    for f_idx in range(n_frames):
        pos_comp = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in solute_traj.xyz[f_idx]]
        pos_c0 = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in c0_traj.xyz[f_idx]]
        pos_c1 = [mm.Vec3(c[0], c[1], c[2]) * unit.nanometers for c in c1_traj.xyz[f_idx]]
        ec = compute_frame_energy(sim_comp, pos_comp)
        e0 = compute_frame_energy(sim_c0, pos_c0)
        e1 = compute_frame_energy(sim_c1, pos_c1)
        delta_gs.append(round(float(ec - (e0 + e1)), 2))

    # =========================================================================
    # Stage 3: 8-Lambda Alchemical TI FEP Mutational Hotspot Scan (Precision=double)
    # =========================================================================
    logger.info("[%s] Starting 8-Lambda Alchemical TI FEP Scan...", spec["id"])
    # Build solute Nonbonded system on the MD-minimized/equilibrated solute coordinates (frame -1 of solute_traj)
    solute_top = fixer.topology
    sys_fep_base = ff.createSystem(
        solute_top,
        nonbondedMethod=app.CutoffNonPeriodic,
        nonbondedCutoff=1.2 * unit.nanometers,
        constraints=app.HBonds,
    )
    nb_fep = next(f for f in sys_fep_base.getForces() if isinstance(f, mm.NonbondedForce))
    n_sol = nb_fep.getNumParticles()
    q_sol = np.zeros(n_sol)
    sig_sol = np.zeros(n_sol)
    eps_sol = np.zeros(n_sol)
    for i in range(n_sol):
        q, s, e = nb_fep.getParticleParameters(i)
        q_sol[i] = q.value_in_unit(unit.elementary_charge)
        sig_sol[i] = s.value_in_unit(unit.nanometers)
        eps_sol[i] = e.value_in_unit(unit.kilojoules_per_mole)

    # Relaxed solute coordinates from last MD snapshot (in nm)
    pos_relaxed_nm = solute_traj.xyz[-1].copy()

    # Map (chain_id, canonical_res_seq) -> side-chain atom indices & opposite-chain atom indices
    solute_c0_all = [a.index for a in list(solute_top.chains())[0].atoms()]
    solute_c1_all = [a.index for a in list(solute_top.chains())[1].atoms()]
    target_map = {}
    for c_idx, ch in enumerate(solute_top.chains()):
        ch_id = "A" if c_idx == 0 else "B"
        gene_name = cA["gene"] if c_idx == 0 else cB["gene"]
        for r_idx, res in enumerate(ch.residues()):
            can_seq = orig_res_map[(c_idx, r_idx)]
            sc_atoms = [a.index for a in res.atoms() if a.name not in BACKBONE_ATOMS]
            if not sc_atoms:
                # For GLY, include CA+HA
                sc_atoms = [a.index for a in res.atoms() if a.name in ("CA", "HA", "HA2", "HA3")]
            target_map[(ch_id, can_seq)] = {
                "chain": ch_id,
                "gene": gene_name,
                "res_seq": can_seq,
                "res_name": res.name,
                "sc_atoms": sc_atoms,
                "opp_atoms": solute_c1_all if c_idx == 0 else solute_c0_all,
            }

    # Combine explicit fep_targets + top 4 energetic interface hotspots from MD
    fep_queue = []
    seen_keys = set()
    for ch_id, r_seq, desc in spec.get("fep_targets", []):
        if (ch_id, int(r_seq)) in target_map and (ch_id, int(r_seq)) not in seen_keys:
            fep_queue.append((ch_id, int(r_seq), desc))
            seen_keys.add((ch_id, int(r_seq)))

    for item in per_res_decomp[:6]:
        k = (item["chain"], int(item["res_seq"]))
        if k in target_map and k not in seen_keys and len(fep_queue) < 10:
            fep_queue.append((k[0], k[1], f"{item['gene']} {item['res_name']}{item['res_seq']} (Top MD Interface Anchor, IE={item['mean_ie_kcal']:.1f} kcal/mol)"))
            seen_keys.add(k)

    # Prepare one reusable CUDA Simulation for 8-lambda TI FEP with backbone harmonic restraints
    restraint = mm.CustomExternalForce("0.5*k_rest*((x-x0)^2 + (y-y0)^2 + (z-z0)^2)")
    restraint.addGlobalParameter("k_rest", 1000.0)
    restraint.addPerParticleParameter("x0")
    restraint.addPerParticleParameter("y0")
    restraint.addPerParticleParameter("z0")
    for a in solute_top.atoms():
        if a.name in ("N", "CA", "C", "O"):
            p0 = pos_relaxed_nm[a.index]
            restraint.addParticle(a.index, [float(p0[0]), float(p0[1]), float(p0[2])])
    sys_fep_base.addForce(restraint)

    integ_fep = mm.LangevinMiddleIntegrator(310.0 * unit.kelvin, 1.0 / unit.picosecond, 0.002 * unit.picoseconds)
    plat_fep = mm.Platform.getPlatformByName("CUDA")
    sim_fep = app.Simulation(solute_top, sys_fep_base, integ_fep, plat_fep, {"DeviceIndex": "0", "Precision": "double"})

    LAMBDAS = [0.0, 0.15, 0.30, 0.45, 0.60, 0.75, 0.90, 1.0]
    fep_results = []

    for ch_id, r_seq, desc in fep_queue:
        t_info = target_map[(ch_id, r_seq)]
        sc_idx = np.array(t_info["sc_atoms"], dtype=int)
        opp_idx = np.array(t_info["opp_atoms"], dtype=int)

        # Minimum heavy-atom distance to opposite chain at relaxed state
        d_mat = np.linalg.norm(pos_relaxed_nm[sc_idx][:, None, :] - pos_relaxed_nm[opp_idx][None, :, :], axis=-1)
        d_min_ang = float(d_mat.min() * 10.0)

        qi_sc, si_sc, ei_sc = q_sol[sc_idx], sig_sol[sc_idx], eps_sol[sc_idx]
        qj_op, sj_op, ej_op = q_sol[opp_idx], sig_sol[opp_idx], eps_sol[opp_idx]

        win_records = []
        dudl_raw_means = []
        dudl_screened_means = []

        # Dielectric screening factor (eps_r = 4.0 for buried polar/salt bridge, 1.0 for vdW)
        ELEC_SCREEN = 0.10 if t_info["res_name"] in ("ARG", "LYS", "ASP", "GLU") else 0.35

        for lam in LAMBDAS:
            scale = 1.0 - lam
            for idx_a in sc_idx:
                nb_fep.setParticleParameters(
                    int(idx_a),
                    q_sol[idx_a] * scale * unit.elementary_charge,
                    sig_sol[idx_a] * unit.nanometers,
                    eps_sol[idx_a] * scale * unit.kilojoules_per_mole,
                )
            nb_fep.updateParametersInContext(sim_fep.context)
            sim_fep.context.setPositions([mm.Vec3(float(c[0]), float(c[1]), float(c[2])) * unit.nanometers for c in pos_relaxed_nm])
            if lam < 1.0:
                sim_fep.step(500)  # 1 ps local side-chain relaxation
                dudl_samples_raw = []
                dudl_samples_scr = []
                for _ in range(8):
                    sim_fep.step(250)
                    st = sim_fep.context.getState(getPositions=True)
                    pts = np.asarray(st.getPositions(asNumpy=True).value_in_unit(unit.nanometers), dtype=float)
                    d = np.maximum(np.linalg.norm(pts[sc_idx][:, None, :] - pts[opp_idx][None, :, :], axis=-1), 0.08)
                    sr6 = ((si_sc[:, None] + sj_op[None, :]) * 0.5 / d) ** 6
                    eps_cross = np.sqrt((ei_sc[:, None] * scale) * ej_op[None, :])
                    vdw_part = (2.0 * eps_cross * (sr6 ** 2 - sr6)).sum()
                    coul_part = (ONE_4PI_EPS0 * (qi_sc[:, None] * scale) * qj_op[None, :] / d).sum()
                    dudl_samples_raw.append(float(vdw_part + coul_part))
                    dudl_samples_scr.append(float(vdw_part + ELEC_SCREEN * coul_part))
                m_raw = float(np.mean(dudl_samples_raw))
                m_scr = float(np.mean(dudl_samples_scr))
            else:
                m_raw = 0.0
                m_scr = 0.0

            win_records.append({"lambda": lam, "minus_dUdlam_kJmol": round(m_raw, 2), "minus_dUdlam_screened_kJmol": round(m_scr, 2)})
            dudl_raw_means.append(m_raw)
            dudl_screened_means.append(m_scr)

        # Restore original parameters for sc_idx
        for idx_a in sc_idx:
            nb_fep.setParticleParameters(
                int(idx_a),
                q_sol[idx_a] * unit.elementary_charge,
                sig_sol[idx_a] * unit.nanometers,
                eps_sol[idx_a] * unit.kilojoules_per_mole,
            )
        nb_fep.updateParametersInContext(sim_fep.context)

        # Integrate ddG = - int <dU/dlam> dlam
        ddg_raw_kj = float(-np.trapezoid(dudl_raw_means, LAMBDAS))
        ddg_scr_kj = float(-np.trapezoid(dudl_screened_means, LAMBDAS))
        ddg_scr_kcal = round(ddg_scr_kj * KJ_TO_KCAL, 2)
        ddg_raw_kcal = round(ddg_raw_kj * KJ_TO_KCAL, 2)

        fep_results.append({
            "chain": ch_id,
            "gene": t_info["gene"],
            "res_seq": r_seq,
            "res_name": t_info["res_name"],
            "mutation_label": f"{t_info['gene']} {t_info['res_name']}{r_seq}Ala",
            "description": desc,
            "d_min_partner_A": round(d_min_ang, 2),
            "ddG_screened_kcal_mol": ddg_scr_kcal,
            "ddG_raw_kcal_mol": ddg_raw_kcal,
            "ddG_screened_kJ_mol": round(ddg_scr_kj, 2),
            "windows": win_records,
        })
        logger.info(
            "  FEP [%s %s%d] d_min=%.2f A -> ddG_screened = %+.2f kcal/mol (raw=%+.2f kcal/mol)",
            t_info["gene"], t_info["res_name"], r_seq, d_min_ang, ddg_scr_kcal, ddg_raw_kcal
        )

    summary = {
        "id": spec["id"],
        "axis": spec["axis"],
        "pair_label": spec["pair_label"],
        "chainA": cA,
        "chainB": cB,
        "boltz_confidence": {
            "confidence_score": round(float(conf.get("confidence_score", 0.0)), 4),
            "ptm": round(float(conf.get("ptm", 0.0)), 4),
            "iptm": round(float(conf.get("iptm", 0.0)), 4),
            "complex_plddt": round(float(conf.get("complex_plddt", 0.0)), 4),
            "n_interchain_contacts_5A": len(contact_pairs_5a),
        },
        "explicit_md": {
            "length_ns": args.length_ns,
            "n_snapshots": n_frames,
            "ns_per_day": round(ns_per_day, 1),
            "mean_partner_rmsd_A": round(float(np.mean(c1_rmsd_ang)), 2),
            "final_partner_rmsd_A": round(float(c1_rmsd_ang[-1]), 2),
            "mean_complex_rmsd_A": round(float(np.mean(comp_rmsd_ang)), 2),
            "mean_delta_g_gbn2_kcal": round(float(np.mean(delta_gs)), 2),
            "std_delta_g_gbn2_kcal": round(float(np.std(delta_gs)), 2),
            "mean_vdw_ie_kcal": round(float(np.mean(tot_vdw_frames)), 2),
            "mean_total_nb_ie_kcal": round(float(np.mean(tot_nb_frames)), 2),
            "top_hbonds": hbond_list[:10],
            "top_residue_decomposition": per_res_decomp[:15],
        },
        "fep_hotspot_scan": fep_results,
        "elapsed_seconds": round(time.time() - t_start, 1),
    }

    out_json.write_text(json.dumps(summary, indent=2))
    logger.info("[%s] COMPLETE in %.1fs -> %s", spec["id"], summary["elapsed_seconds"], out_json)


if __name__ == "__main__":
    main()
