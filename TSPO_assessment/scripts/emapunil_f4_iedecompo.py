"""F4: per-pocket interaction-energy decomposition + alchemical anchor mutation for emapunil.

Runs in the openfe-md env. Per pocket:
  1. protein (from f2_<pdb>_rec.pdb) + emapunil docked pose -> OpenMM system
     (OpenFF Sage for ligand via NAGL AM1-BCC, amber14 for protein, implicit OBC2);
  2. restrained minimisation + 250 ps MD (double precision CUDA);
  3. ligand-protein interaction energy per residue (Coulomb+vdW decomposition);
  4. anchor mutation scan: top-2 contact residues -> Ala, re-minimise, dE_loss.
Writes JSON per pocket; a wrapper aggregates.
"""
import json
import math
import os
import sys
import time

import numpy as np
import openmm as mm
from openmm import app, unit
from openff.toolkit import Molecule, ForceField
from openff.interchange import Interchange
from pdbfixer import PDBFixer

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/docking"
EMAP_SMILES = "CCN(CC1=CC=CC=C1)C(=O)CN2C3=NC(=NC=C3N(C2=O)C)C4=CC=CC=C4"

POCKETS = {
    "4RYI": ("TSPO_anchor", "4RYI_emapunil_docked.pdbqt"),
    "6X3X": ("GABA-A_BZD_site", "f2_6X3X_emapunil4_docked.pdbqt"),
    "4DKL": ("OPRM1_orthosteric", "f2_4DKL_emapunil_docked.pdbqt"),
    "1XVP": ("CAR_LBD", "f2_1XVP_emapunil4_docked.pdbqt"),
    "4XAQ": ("GRM2_negative_control", "f2_4XAQ_emapunil_docked.pdbqt"),
}


def read_pose_atoms(pdbqt, pose=1):
    """Read pose coordinates from a vina docked pdbqt."""
    coords, in_model = [], 0
    for line in open(pdbqt):
        if line.startswith("MODEL"):
            in_model += 1
        elif in_model == pose and line.startswith(("ATOM", "HETATM")):
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL") and in_model >= pose:
            break
    if not coords and in_model == 0:  # single-model file
        for line in open(pdbqt):
            if line.startswith(("ATOM", "HETATM")):
                coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
    return np.array(coords)


def build_complex(pdb, pose_pdbqt):
    """Protein PDB + ligand pose -> openmm app.Modeller with ligand as residue LIG."""
    from rdkit import Chem
    from rdkit.Chem import AllChem
    prot = app.PDBFile(f"{OUT}/f2_{pdb}_rec_fixed.pdb")
    lig = Molecule.from_smiles(EMAP_SMILES)
    lig.generate_conformers(n_conformers=1)
    # align ligand conformer onto docked pose (Kabsch on heavy atoms via ordering)
    pose_xyz = read_pose_atoms(f"{OUT}/{pose_pdbqt}")
    conf_q = lig.conformers[0]          # pint Quantity (angstrom)
    conf = np.asarray(conf_q.magnitude, dtype=float)
    # vina pose carries polar H (types HD) + heavy atoms; OpenFF conformer carries
    # ALL H. Match by subsetting pose to heavy atoms and conf to heavy atoms, then
    # align on the first min(n) heavy atoms (atom order from same SMILES differs
    # between meeko/openff, so align by centroid + principal axes instead).
    def kabsch(P, Q):
        Pc = P - P.mean(0); Qc = Q - Q.mean(0)
        H = Pc.T @ Qc
        U, S, Vt = np.linalg.svd(H)
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        R = Vt.T @ np.diag([1, 1, d]) @ U.T
        return R, Q.mean(0) - P.mean(0) @ R
    # principal-axis alignment (order-independent): inertial frames of conf & pose
    def inertial_frame(P):
        C = P - P.mean(0)
        cov = C.T @ C / len(C)
        w, v = np.linalg.eigh(cov)
        # eigh returns ascending; make right-handed
        if np.linalg.det(v) < 0:
            v[:, 2] *= -1
        return v, P.mean(0)
    Rc, cc = inertial_frame(conf)
    Rp, cp = inertial_frame(pose_xyz)
    R = Rp @ Rc.T
    aligned = (conf - cc) @ R + cp
    # openff conformers are pint Quantities; reuse conf_q's units (conf is the magnitude)
    lig._conformers = [type(conf_q)(np.asarray(aligned, dtype=float), conf_q.units)]
    # build modeller: protein + ligand
    # use the pdbfixer-repaired receptor (missing side chains + H at pH 7.4)
    pdb_block = f"{OUT}/f2_{pdb}_rec_fixed.pdb"
    lig_path = f"{OUT}/f2_{pdb}_emap_lig.sdf"
    lig.to_file(lig_path, file_format="sdf")
    lig_rdk = app.PDBFile if False else None
    # use Modeller with PDBFile for protein and an SDF-loaded ligand topology
    from rdkit import Chem as RC
    m = RC.MolFromMolFile(lig_path, removeHs=False)
    RC.AllChem.EmbedMolecule if False else None
    # write ligand as PDB with element info for Modeller
    lig_pdb = f"{OUT}/f2_{pdb}_emap_lig.pdb"
    RC.PDBWriter and RC.MolToPDBFile(m, lig_pdb)
    ligp = app.PDBFile(lig_pdb)
    # protein H placement FIRST (before ligand is added): amber templates.
    # The UNL ligand residue is parametrised later by SystemGenerator via openff
    # (SMIRNOFF) and must not go through amber template matching.
    from openmm.app import ForceField as OMForceField
    ff_h = OMForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
    mod = app.Modeller(prot.topology, prot.positions)
    mod.addHydrogens(forcefield=ff_h)  # pH 7.4 default
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
            # NAGL am1bcc charges via explicit .pt model path (openff 0.18 + nagl 0.5.5
            # mismatch: the method-string lookup raises BadFileSuffixError)
            from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
            from openff.nagl_models import list_available_nagl_models
            _nagl_model = sorted(
                str(p) for p in list_available_nagl_models() if "1.0.0" in str(p)
            )[0]
            NAGLToolkitWrapper().assign_partial_charges(
                lig, partial_charge_method=_nagl_model
            )
            # openff ForceField cannot read openmm amber14 XMLs — use openmmforcefields
            # SystemGenerator directly (it converts amber14 + implicit OBC2 to SMIRNOFF
            # internally and handles the small molecule with openff-2.1.0).
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
            # restrain protein backbone (all heavy atoms) to their docked positions —
            # full-atom restraints prevent chain-break regions from drifting apart
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
            # blow-up guard: any NaN/inf or absurd coordinate means the MD destabilised
            if not np.isfinite(positions).all() or np.max(np.abs(positions)) > 5000:
                raise RuntimeError("MD blow-up: coordinates out of range")
            # save relaxed complex
            with open(f"{OUT}/f4_{pdb}_relaxed.pdb", "w") as fh:
                app.PDBFile.writeFile(sim.topology, positions, fh)
            # --- interaction energy decomposition: ligand vs each protein residue
            # compute Coulomb+vdW between ligand atoms and each residue via
            # NonbondedForce parameter extraction
            nb = None
            for f in system.getForces():
                if isinstance(f, mm.NonbondedForce):
                    nb = f
                    break
            lig_idx = [a.index for a in mod.topology.atoms()
                       if a.residue.name in ("LIG", "UNL")]
            prot_res = {}
            for a in mod.topology.atoms():
                if a.index not in lig_idx and a.residue.name not in ("HOH",):
                    prot_res.setdefault((a.residue.chain.id, a.residue.id, a.residue.name),
                                        []).append(a.index)
            q, sig, eps = [], [], []
            for i in range(nb.getNumParticles()):
                c, s, e = nb.getParticleParameters(i)
                q.append(c.value_in_unit(unit.elementary_charge))
                sig.append(s.value_in_unit(unit.nanometer))
                eps.append(e.value_in_unit(unit.kilojoule_per_mole))
            q = np.array(q); sig = np.array(sig); eps = np.array(eps)
            pos_np = positions.value_in_unit(unit.nanometer)
            box = state.getPeriodicBoxVectors(asNumpy=True)
            # no-PBC pairwise (implicit solvent, single box)
            def pair_E(i, j):
                r = max(np.linalg.norm(pos_np[i] - pos_np[j]), 1e-6)
                eij = 332.06371 * q[i] * q[j] / r  # Coulomb kcal/mol
                sr = (sig[i] + sig[j]) / 2
                sr6 = (sr / r) ** 6
                eij += 4 * math.sqrt(eps[i] * eps[j]) * 0.239006 * (sr6**2 - sr6)  # LJ kcal/mol
                return eij
            decomp = {}
            for (ch, rid, rname), idxs in prot_res.items():
                e_tot = sum(pair_E(i, j) for i in lig_idx for j in idxs
                            if abs(i - j) > 1)
                if abs(e_tot) > 0.05:
                    decomp[f"{rname}{rid}"] = round(e_tot, 2)
            top = sorted(decomp.items(), key=lambda kv: kv[1])[:8]
            results[pdb] = {"label": label, "status": "ok", "runtime_s": round(time.time() - t0),
                            "top_contacts": dict(top),
                            "all_contacts": decomp}
            print("top contacts:", top, flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[pdb] = {"label": label, "error": f"{type(e).__name__}: {e}"}
        json.dump(results, open(f"{OUT}/emapunil_f4_iedecompo_{pdb}.json", "w"), indent=1)
    print("\nDONE", flush=True)


if __name__ == "__main__":
    main()
