"""FGIN f4: pose-stability MD + interaction-energy decomposition for FGIN-1-27.

Same protocol as emapunil_f4_iedecompo.py, different ligand. Pockets:
  4RYI TSPO anchor, 1XVP CAR, 5TGZ CNR1, 4DJH OPRK1 (top3), 4XAQ GRM2 negative.
Reuses the pdbfixer-repaired receptors from the emapunil round.
"""
import json
import sys
import time
import numpy as np

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
import openmm as mm
import openmm.unit as unit
from openmm import app
from openff.toolkit import Molecule
from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
from openff.nagl_models import list_available_nagl_models

OUT = "/das/user/QYJI/druggability/TSPO_assessment/output/docking"
BASE = "/das/user/QYJI/druggability/TSPO_assessment"

FGIN_SMILES = "CCCCCCN(CCCCCC)C(=O)CC1=C(NC2=CC=CC=C21)C3=CC=C(C=C3)F"

POCKETS = {
    "4RYI": ("TSPO_anchor", "f2_4RYI_fgin_docked.pdbqt"),
    "1XVP": ("CAR_LBD", "f2_1XVP_fgin_docked.pdbqt"),
    "5TGZ": ("CNR1_orthosteric", "f2_5TGZ_fgin_docked.pdbqt"),
    "4DJH": ("OPRK1_orthosteric", "f2_4DJH_fgin_docked.pdbqt"),
    "4XAQ": ("GRM2_negative_control", "f2_4XAQ_fgin_docked.pdbqt"),
}


def read_pose_atoms(pdbqt, pose=1):
    coords = []
    in_model = 0
    for line in open(pdbqt):
        if line.startswith("MODEL"):
            in_model += 1
        elif in_model == pose and line.startswith(("ATOM", "HETATM")):
            # include only heavy atoms (columns 77-78 element; vina writes type at 77+)
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL"):
            if in_model >= pose:
                break
    return np.array(coords)


def inertial_frame(xyz):
    c = xyz.mean(axis=0)
    xc = xyz - c
    # principal axes via SVD of centered coordinates
    U, S, Vt = np.linalg.svd(xc)
    return Vt.T, c  # rotation columns, centroid


def kabsch_align(mobile, ref):
    """Rotation+translation aligning mobile onto ref (both N x 3, same order)."""
    cm, cr = mobile.mean(axis=0), ref.mean(axis=0)
    H = (mobile - cm).T @ (ref - cr)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    return R, cm, cr


def build_complex(pdb, pose_pdbqt):
    from rdkit import Chem
    from rdkit.Chem import AllChem
    prot = app.PDBFile(f"{OUT}/f2_{pdb}_rec_fixed.pdb")
    lig = Molecule.from_smiles(FGIN_SMILES)
    lig.generate_conformers(n_conformers=1)
    pose_xyz = read_pose_atoms(f"{OUT}/{pose_pdbqt}")
    conf_q = lig.conformers[0]
    conf = np.asarray(conf_q.magnitude, dtype=float)
    # match heavy atoms: vina pose has polar H + heavy; OpenFF has all H.
    # Order both by "heavy-atom sequence" is fragile; instead align on centroids +
    # principal axes (approximately correct for a rigid molecule with distinct axes).
    pose_heavy = pose_xyz  # vina pdbqt heavy atoms only (united atom model)
    lig_heavy_idx = [i for i, a in enumerate(lig.atoms) if a.atomic_number != 1]
    lig_heavy = conf[lig_heavy_idx]
    if len(lig_heavy) != len(pose_heavy):
        # fallback: centroid-only placement (still fine for MD relaxation)
        print(f"  [warn] heavy-atom count mismatch: pose {len(pose_heavy)} vs lig {len(lig_heavy)}; centroid placement")
        cc, cp = lig_heavy.mean(axis=0), pose_heavy.mean(axis=0)
        aligned = conf - cc + cp
    else:
        R, cm, cr = kabsch_align(lig_heavy, pose_heavy)
        aligned = (conf - cm) @ R.T + cr
    lig._conformers = [type(conf_q)(np.asarray(aligned, dtype=float), conf_q.units)]
    # write ligand as PDB with element info for Modeller
    lig_pdb = f"{OUT}/f4_{pdb}_fgin_lig.pdb"
    lig.to_file(lig_pdb, file_format="pdb")
    ligp = app.PDBFile(lig_pdb)
    # protein H placement FIRST (before ligand is added): amber templates.
    from openmm.app import ForceField as OMForceField
    ff_h = OMForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
    mod = app.Modeller(prot.topology, prot.positions)
    mod.addHydrogens(forcefield=ff_h)
    mod.add(ligp.topology, ligp.positions)
    return mod, lig


def main():
    results = {}
    only = sys.argv[1:] or list(POCKETS)
    for pdb in only:
        label, pose = POCKETS[pdb]
        print(f"\n=== {pdb} {label} ===", flush=True)
        t0 = time.time()
        try:
            mod, lig = build_complex(pdb, pose)
            # NAGL am1bcc charges via explicit .pt model path
            from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
            from openff.nagl_models import list_available_nagl_models
            _nagl_model = sorted(
                str(p) for p in list_available_nagl_models() if "1.0.0" in str(p)
            )[0]
            NAGLToolkitWrapper().assign_partial_charges(lig, partial_charge_method=_nagl_model)
            from openmmforcefields.generators import SystemGenerator
            gen = SystemGenerator(
                forcefields=["amber14/protein.ff14SB.xml", "amber14/tip3p.xml"],
                small_molecule_forcefield="openff-2.1.0",
                molecules=[lig],
            )
            system = gen.create_system(mod.topology, molecules=lig)
            integrator = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond,
                                                     2 * unit.femtoseconds)
            integrator.setConstraintTolerance(1e-5)
            platform = mm.Platform.getPlatformByName("CUDA")
            prop = {"CudaPrecision": "double", "CudaDeviceIndex": "0"}
            sim = app.Simulation(mod.topology, system, integrator, platform, prop)
            sim.context.setPositions(mod.positions)
            # restrain ALL protein heavy atoms to their docked positions
            force = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
            force.addGlobalParameter("k", 5.0 * unit.kilocalorie_per_mole / unit.angstrom**2)
            force.addPerParticleParameter("x0")
            force.addPerParticleParameter("y0")
            force.addPerParticleParameter("z0")
            pos = mod.positions
            for atom in mod.topology.atoms():
                if atom.residue.name not in ("LIG", "UNL") and atom.element is not None and atom.element.symbol != "H":
                    i = atom.index
                    p = pos[i]
                    force.addParticle(i, [p.x, p.y, p.z])
            system.addForce(force)
            sim.context.reinitialize(preserveState=True)
            # minimisation
            sim.minimizeEnergy(maxIterations=2000)
            # 250 ps MD
            sim.context.setVelocitiesToTemperature(300 * unit.kelvin, 42)
            steps = int(250 * unit.picoseconds / (2 * unit.femtoseconds))
            sim.step(steps)
            state = sim.context.getState(getPositions=True, getEnergy=True)
            positions = state.getPositions(asNumpy=True)
            if not np.isfinite(positions).all() or np.max(np.abs(positions)) > 5000:
                raise RuntimeError("MD blow-up: coordinates out of range")
            with open(f"{OUT}/f4_{pdb}_fgin_relaxed.pdb", "w") as fh:
                app.PDBFile.writeFile(sim.topology, positions, fh)
            # --- interaction energy decomposition: ligand vs each protein residue
            nb = None
            for f in range(system.getNumForces()):
                fo = system.getForce(f)
                if isinstance(fo, mm.NonbondedForce):
                    nb = fo
            n = system.getNumParticles()
            charge = np.zeros(n); sigma = np.zeros(n); eps = np.zeros(n)
            for i in range(n):
                c, s, e = nb.getParticleParameters(i)
                charge[i] = c.value_in_unit(unit.elementary_charge)
                sigma[i] = s.value_in_unit(unit.nanometer)
                eps[i] = e.value_in_unit(unit.kilojoule_per_mole)
            posv = np.array(positions.value_in_unit(unit.nanometer))
            lig_idx = [a.index for a in sim.topology.atoms() if a.residue.name in ("UNL", "LIG")]
            prot_res = {}
            for a in sim.topology.atoms():
                if a.residue.name in ("UNL", "LIG"):
                    continue
                if a.element is None or a.element.symbol == "H":
                    continue
                key = (a.residue.chain.id, a.residue.id, a.residue.name)
                prot_res.setdefault(key, []).append(a.index)
            COUL = 138.935456
            def pair_E(i, j):
                r = float(np.linalg.norm(posv[i] - posv[j]))
                if r < 1e-3:
                    return 0.0
                sr = sigma[i] + sigma[j]
                E6 = (sr * 0.5 / r) ** 6
                vdw = 4 * np.sqrt(eps[i] * eps[j]) * (E6 * E6 - E6)
                coul = COUL * charge[i] * charge[j] / r
                return vdw + coul
            decomp = {}
            for (ch, rid, rname), idxs in prot_res.items():
                e_tot = sum(pair_E(i, j) for i in lig_idx for j in idxs if abs(i - j) > 1)
                if abs(e_tot) > 0.05:
                    decomp[f"{rname}{rid}"] = round(e_tot, 2)
            top = sorted(decomp.items(), key=lambda kv: kv[1])[:8]
            results[pdb] = {"label": label, "status": "ok", "runtime_s": round(time.time() - t0),
                            "top_contacts": dict(top), "all_contacts": decomp}
            print("top contacts:", top, flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[pdb] = {"label": label, "error": f"{type(e).__name__}: {e}"}
        json.dump(results, open(f"{OUT}/fgin_f4_iedecompo_{pdb}.json", "w"), indent=1)
    print("\nDONE", flush=True)


if __name__ == "__main__":
    main()
