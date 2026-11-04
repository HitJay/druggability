"""P3: 250 ps OpenMM all-atom pose-stability MD + residue interaction-energy
decomposition (with exact kJ/mol units, COUL = 138.935456 kJ*nm/e^2) across the
10 beta-cell relevant candidate pockets + negative control.

Uses exact 1-to-1 heavy-atom coordinate mapping from the docked Vina PDBQT
via meeko's REMARK SMILES IDX map (0.00 A heavy-atom placement fidelity).
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import app, unit

BASE = Path("/das/user/QYJI/druggability/Imatinib_beta_cell_assessment")
DATA = BASE / "data"
STRUCT = BASE / "structures"
DOCK = BASE / "output/docking"
MD_OUT = BASE / "output/md"
MD_OUT.mkdir(parents=True, exist_ok=True)

COUL = 138.935456  # kJ * nm / e^2 (exact kJ/mol when r is in nm)
IMATINIB_SMILES = "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC4=NC=CC(=N4)C5=CN=CC=C5"

MD_TARGETS = [
    ("DDR1",   "4BKJ", "anchor_primary"),
    ("ABL1",   "2HYY", "anchor_primary"),
    ("ABL2",   "3GVU", "anchor_primary"),
    ("PDGFRA", "6JOL", "anchor_primary"),
    ("KIT",    "1T46", "anchor_primary"),
    ("NQO2",   "3FW1", "candidate_offtarget"),
    ("ERN1",   "4U6R", "candidate_pathway"),
    ("PPARG",  "6KTN", "candidate_pathway"),
    ("KCNJ11", "6C3O", "candidate_channel"),
    ("ECHS1",  "8ZRW", "negative_control"),
]


def trim_receptor_near_pocket(rec_pdb, pocket_center, out_pdb, cutoff_res_A=26.0):
    STD_AA = {
        "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
        "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
        "HID", "HIE", "HIP", "CYX"
    }
    res_lines = {}
    res_min_d = {}
    for line in open(rec_pdb):
        if line.startswith("ATOM"):
            rname = line[17:20].strip()
            if rname not in STD_AA:
                continue
            ch = line[21].strip()
            resn = line[22:26].strip()
            key = (ch, resn)
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            d = math.dist((x, y, z), pocket_center)
            res_lines.setdefault(key, []).append(line)
            if key not in res_min_d or d < res_min_d[key]:
                res_min_d[key] = d

    keep_lines = []
    last_ch = None
    for key, lines in res_lines.items():
        if res_min_d[key] <= cutoff_res_A:
            ch = key[0]
            if last_ch is not None and ch != last_ch:
                keep_lines.append("TER\n")
            keep_lines.extend(lines)
            last_ch = ch
    keep_lines.append("END\n")
    Path(out_pdb).write_text("".join(keep_lines))


def build_exact_pose_molecule(pose_pdbqt):
    """Map docked Vina PDBQT heavy-atom coordinates 1-to-1 onto RDKit/OpenFF Molecule
    using meeko's REMARK SMILES IDX table (zero RMSD to docked Vina pose)."""
    from rdkit import Chem
    from openff.toolkit import Molecule

    pdbqt_init = DOCK / "lig_imatinib.pdbqt"
    smiles_str = None
    idx_pairs = []
    for line in open(pdbqt_init):
        if line.startswith("REMARK SMILES IDX"):
            toks = [int(x) for x in line.split()[3:]]
            for i in range(0, len(toks), 2):
                idx_pairs.append((toks[i] - 1, toks[i + 1]))
        elif line.startswith("REMARK SMILES "):
            smiles_str = line.split("REMARK SMILES ")[1].strip()

    serial_xyz = {}
    in_m = 0
    for line in open(pose_pdbqt):
        if line.startswith("MODEL"):
            in_m += 1
        elif (in_m == 1 or in_m == 0) and line.startswith(("ATOM", "HETATM")):
            ser = int(line[6:11].strip())
            serial_xyz[ser] = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        elif line.startswith("ENDMDL") and in_m >= 1:
            break

    mol_no_h = Chem.MolFromSmiles(smiles_str)
    conf = Chem.Conformer(mol_no_h.GetNumAtoms())
    for rdk_idx, ser in idx_pairs:
        conf.SetAtomPosition(rdk_idx, serial_xyz[ser])
    mol_no_h.AddConformer(conf, assignId=True)
    mol_h = Chem.AddHs(mol_no_h, addCoords=True)

    rdk_heavy = np.array([mol_h.GetConformer().GetAtomPosition(i) for i in range(mol_no_h.GetNumAtoms())])
    pose_heavy = np.array([serial_xyz[ser] for _, ser in sorted(idx_pairs)])
    rmsd = float(np.sqrt(np.mean(np.sum((rdk_heavy - pose_heavy) ** 2, axis=1))))

    off_mol = Molecule.from_rdkit(mol_h, allow_undefined_stereo=True, hydrogens_are_explicit=True)
    return off_mol, mol_h, round(rmsd, 4)


def build_complex(gene, pdb, pocket_center, pose_pdbqt):
    from pdbfixer import PDBFixer
    from openmm.app import ForceField as OMForceField
    from rdkit import Chem as RC

    raw_rec = DOCK / f"rec_{gene}_{pdb}.pdb"
    trim_rec = MD_OUT / f"trim_{gene}_{pdb}.pdb"
    n_atom_lines = sum(1 for l in open(raw_rec) if l.startswith("ATOM"))
    if n_atom_lines > 4000 or gene == "NQO2":
        trim_receptor_near_pocket(raw_rec, pocket_center, trim_rec, cutoff_res_A=26.0)
    else:
        trim_receptor_near_pocket(raw_rec, pocket_center, trim_rec, cutoff_res_A=100.0)

    fixer = PDBFixer(filename=str(trim_rec))
    fixer.findMissingResidues()
    for k in list(fixer.missingResidues.keys()):
        if len(fixer.missingResidues[k]) > 6:
            del fixer.missingResidues[k]
    fixer.findNonstandardResidues()
    fixer.replaceNonstandardResidues()
    fixer.removeHeterogens(False)
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)
    fixed_pdb = MD_OUT / f"fixed_{gene}_{pdb}.pdb"
    with open(fixed_pdb, "w") as fh:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, fh)
    prot = app.PDBFile(str(fixed_pdb))

    lig, mol_h, align_rmsd = build_exact_pose_molecule(pose_pdbqt)
    lig_pdb = MD_OUT / f"lig_{gene}_{pdb}.pdb"
    RC.MolToPDBFile(mol_h, str(lig_pdb))
    ligp = app.PDBFile(str(lig_pdb))

    ff_h = OMForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
    mod = app.Modeller(prot.topology, prot.positions)
    mod.addHydrogens(forcefield=ff_h)
    mod.add(ligp.topology, ligp.positions)
    return mod, lig, align_rmsd


def run_one_md(gene, pdb, role, gpu_id="0", force_rerun=False):
    out_json = MD_OUT / f"md_{gene}_{pdb}.json"
    if out_json.exists() and not force_rerun:
        old = json.load(open(out_json))
        if "error" not in old:
            print(f"[SKIP] {gene} ({pdb}) already completed.")
            return old

    from openmmforcefields.generators import SystemGenerator
    from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
    from openff.nagl_models import list_available_nagl_models

    t0 = time.time()
    dock_res = json.load(open(DOCK / "p2_docking_results.json"))[gene]
    pocket_center = tuple(dock_res["pocket_center"])
    pose_pdbqt = DOCK / f"imat_{gene}_{pdb}_docked.pdbqt"

    try:
        mod, lig, align_nn_rmsd = build_complex(gene, pdb, pocket_center, pose_pdbqt)
        _nagl_model = sorted(str(p) for p in list_available_nagl_models() if "1.0.0" in str(p))[0]
        NAGLToolkitWrapper().assign_partial_charges(lig, partial_charge_method=_nagl_model)

        gen = SystemGenerator(
            forcefields=["amber14/protein.ff14SB.xml", "amber14/tip3p.xml"],
            small_molecule_forcefield="openff-2.1.0",
            molecules=[lig],
        )
        system = gen.create_system(mod.topology, molecules=lig)

        k = 5.0 * unit.kilocalorie_per_mole / unit.angstrom ** 2
        reb = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
        reb.addGlobalParameter("k", k)
        for p in ["x0", "y0", "z0"]:
            reb.addPerParticleParameter(p)
        pos0 = mod.positions
        topology_atoms = list(mod.topology.atoms())
        for atom in topology_atoms:
            if atom.residue.name not in ("LIG", "UNL") and atom.element is not None and atom.element.symbol != "H":
                i = atom.index
                p = pos0[i]
                reb.addParticle(i, [p.x, p.y, p.z])
        system.addForce(reb)

        integ = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 2 * unit.femtoseconds)
        integ.setConstraintTolerance(1e-5)
        plat = mm.Platform.getPlatformByName("CUDA")
        sim = app.Simulation(mod.topology, system, integ, plat,
                             {"CudaPrecision": "double", "CudaDeviceIndex": str(gpu_id)})
        sim.context.setPositions(mod.positions)

        lig_heavy = [a.index for a in topology_atoms
                     if a.residue.name in ("LIG", "UNL") and a.element is not None and a.element.symbol != "H"]
        pos_init = np.array([[pos0[i].x, pos0[i].y, pos0[i].z] for i in lig_heavy]) * 10.0
        cen_init = pos_init.mean(0)

        sim.minimizeEnergy(maxIterations=2000)
        sim.context.setVelocitiesToTemperature(300 * unit.kelvin, 42)
        steps = int(250 * unit.picoseconds / (2 * unit.femtoseconds))
        sim.step(steps)

        st = sim.context.getState(getPositions=True, getEnergy=True)
        pos_end = st.getPositions(asNumpy=True).value_in_unit(unit.angstrom)
        if not np.isfinite(pos_end).all() or np.max(np.abs(pos_end)) > 5000:
            raise RuntimeError("MD blow-up: coordinates out of range")

        lig_end = pos_end[lig_heavy]
        cen_end = lig_end.mean(0)
        drift_A = float(np.linalg.norm(cen_end - cen_init))
        rmsd_A = float(np.sqrt(np.mean(np.sum((lig_end - pos_init) ** 2, axis=1))))
        dist_to_pocket_A = float(np.linalg.norm(cen_end - np.array(pocket_center)))

        relaxed_pdb = MD_OUT / f"relaxed_{gene}_{pdb}.pdb"
        with open(relaxed_pdb, "w") as fh:
            app.PDBFile.writeFile(sim.topology, st.getPositions(), fh)

        nb = next(f for f in system.getForces() if isinstance(f, mm.NonbondedForce))
        lig_all = [a.index for a in topology_atoms if a.residue.name in ("LIG", "UNL")]
        prot_res = {}
        for a in topology_atoms:
            if a.index not in lig_all and a.residue.name not in ("HOH",):
                prot_res.setdefault((a.residue.chain.id, a.residue.id, a.residue.name), []).append(a.index)

        n_part = nb.getNumParticles()
        q = np.zeros(n_part); sig = np.zeros(n_part); eps = np.zeros(n_part)
        for i in range(n_part):
            c, s, e = nb.getParticleParameters(i)
            q[i] = c.value_in_unit(unit.elementary_charge)
            sig[i] = s.value_in_unit(unit.nanometer)
            eps[i] = e.value_in_unit(unit.kilojoule_per_mole)

        pos_nm = pos_end * 0.1
        li = np.asarray(lig_all)
        P = pos_nm[li]
        qi, si, ei = q[li], sig[li], eps[li]

        decomp = {}
        for (ch, rid, rname), idxs in prot_res.items():
            ji = np.asarray(idxs)
            Q = pos_nm[ji]
            d = np.maximum(np.linalg.norm(P[:, None, :] - Q[None, :, :], axis=-1), 1e-6)
            qj, sj, ej = q[ji], sig[ji], eps[ji]
            sr6 = ((si[:, None] + sj[None, :]) * 0.5 / d) ** 6
            vdw = (4.0 * np.sqrt(ei[:, None] * ej[None, :]) * (sr6 ** 2 - sr6)).sum()
            coul = (COUL * qi[:, None] * qj[None, :] / d).sum()
            e_tot = float(vdw + coul)
            if abs(e_tot) > 0.2:
                decomp[f"{rname}{rid}{ch}"] = round(e_tot, 2)

        top = sorted(decomp.items(), key=lambda kv: kv[1])[:8]
        sum_ie = round(sum(v for _, v in top[:5]), 2)
        md_stable = bool(drift_A < 3.0 and dist_to_pocket_A < 3.5)

        res = {
            "gene": gene,
            "pdb": pdb,
            "role": role,
            "status": "ok",
            "gpu_id": str(gpu_id),
            "ie_units": "kJ/mol (COUL=138.935456 kJ*nm/e^2, r in nm)",
            "pose_align_nn_rmsd_A": align_nn_rmsd,
            "centroid_drift_A": round(drift_A, 2),
            "ligand_rmsd_A": round(rmsd_A, 2),
            "end_dist_to_pocket_center_A": round(dist_to_pocket_A, 2),
            "md_stable": md_stable,
            "sum_top5_IE_kJmol": sum_ie,
            "sum_top5_IE_kcalmol": round(sum_ie / 4.184, 2),
            "top_contacts_kJmol": dict(top),
            "runtime_s": round(time.time() - t0, 1)
        }
        print(f"  [MD OK] {gene:8s} ({pdb}) | drift={drift_A:.2f} A, rmsd={rmsd_A:.2f} A, "
              f"end_dist={dist_to_pocket_A:.2f} A, stable={md_stable} | "
              f"top5_IE={sum_ie:.1f} kJ/mol | top={top[:3]} [{res['runtime_s']}s]", flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        res = {"gene": gene, "pdb": pdb, "role": role, "error": f"{type(e).__name__}: {e}"}

    json.dump(res, open(out_json, "w"), indent=2)
    return res


if __name__ == "__main__":
    gpu = sys.argv[1] if len(sys.argv) > 1 else "0"
    filter_genes = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    force = "--force" in sys.argv
    for gene, pdb, role in MD_TARGETS:
        if filter_genes and gene not in filter_genes:
            continue
        run_one_md(gene, pdb, role, gpu_id=gpu, force_rerun=force)
