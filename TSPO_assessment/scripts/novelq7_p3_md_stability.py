"""ws7 P3: MD pose-stability + CORRECTED interaction-energy decomposition for
FGIN-1-27 in NOVEL pockets that passed the FGIN docking gate (hit tier confirmed).

Copy-and-swap of novelq_p6_md_stability.py (250 ps protocol reused verbatim so
numbers stay comparable) with two fixes learned from the FEP-A audit:
  1. IE decomposition uses COUL = 138.935 kJ nm / e^2 (correct kJ/mol with r in nm).
     The ws6 p6 script used 332.06371 (kcal A constant) with nm distances = 10x
     inflated Coulomb; its "sum_IE_kJmol" values are NOT comparable to ws7.
  2. Ligand = FGIN-1-27 SMILES; pose files = fgin_hit_<tag>_s*_docked.pdbqt.
Per-pocket JSONs: novelq7_p3_<tag>.json
"""
import json, math, sys, time
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import app, unit

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
NP = f"{BASE}/output/novel_pockets"
DOCK = f"{BASE}/output/docking"
COUL = 138.935456  # kJ nm / e^2  (kJ/mol with r in nm)
FGIN_SMILES = "CCCCCCN(CCCCCC)C(=O)CC1=C(NC2=CC=CC=C21)C3=CC=C(C=C3)F"

SHORTLIST = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else []


def read_pose_atoms(pdbqt, pose=1):
    coords, in_model = [], 0
    for line in open(pdbqt):
        if line.startswith("MODEL"):
            in_model += 1
        elif in_model == pose and line.startswith(("ATOM", "HETATM")):
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL") and in_model >= pose:
            break
    if not coords and in_model == 0:
        for line in open(pdbqt):
            if line.startswith(("ATOM", "HETATM")):
                coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
    return np.array(coords)


def trim_receptor(pdb_prot, pocket_center, pocket_res):
    """keep chains with pocket residues or within 8 A of pocket center."""
    keep_chains = {c for c, _ in pocket_res}
    near = set(keep_chains)
    for line in open(pdb_prot):
        if line.startswith("ATOM"):
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            if math.dist((x, y, z), pocket_center) < 8.0:
                near.add(line[21].strip())
    out = f"{NP}/mdrec_{Path(pdb_prot).stem}_{'-'.join(sorted(near))}.pdb"
    if Path(out).exists():
        return out, sorted(near)
    keep = []
    for line in open(pdb_prot):
        if line.startswith("ATOM") and line[21].strip() in near:
            keep.append(line)
        elif line.startswith(("TER", "END")):
            keep.append(line)
    open(out, "w").write("".join(keep))
    return out, sorted(near)


def build_complex(pdb, pocket_center, pocket_res, pose_pdbqt):
    from openff.toolkit import Molecule
    from pdbfixer import PDBFixer
    from openmm.app import ForceField as OMForceField

    rec_trimmed, chains = trim_receptor(f"{NP}/{pdb}_prot.pdb", pocket_center, pocket_res)
    fixer = PDBFixer(filename=rec_trimmed)
    fixer.findMissingResidues()
    fixer.findNonstandardResidues()
    fixer.replaceNonstandardResidues()
    fixer.removeHeterogens(False)
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)
    fixed_pdb = f"{NP}/mdrec_{pdb}_fgin_fixed.pdb"
    with open(fixed_pdb, "w") as fh:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, fh)
    prot = app.PDBFile(fixed_pdb)

    lig = Molecule.from_smiles(FGIN_SMILES)
    lig.generate_conformers(n_conformers=1)
    pose_xyz = read_pose_atoms(pose_pdbqt)
    conf_q = lig.conformers[0]
    conf = np.asarray(conf_q.magnitude, dtype=float)

    def inertial_frame(P):
        C = P - P.mean(0)
        cov = C.T @ C / len(C)
        w, v = np.linalg.eigh(cov)
        if np.linalg.det(v) < 0:
            v[:, 2] *= -1
        return v, P.mean(0)

    Rc, cc = inertial_frame(conf)
    Rp, cp = inertial_frame(pose_xyz)
    R = Rp @ Rc.T
    aligned = (conf - cc) @ R + cp
    lig._conformers = [type(conf_q)(np.asarray(aligned, dtype=float), conf_q.units)]

    from rdkit import Chem as RC
    lig_path = f"{NP}/md_{pdb}_fgin_lig.sdf"
    lig.to_file(lig_path, file_format="sdf")
    m = RC.MolFromMolFile(lig_path, removeHs=False)
    lig_pdb = f"{NP}/md_{pdb}_fgin_lig.pdb"
    RC.MolToPDBFile(m, lig_pdb)
    ligp = app.PDBFile(lig_pdb)

    ff_h = OMForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
    mod = app.Modeller(prot.topology, prot.positions)
    mod.addHydrogens(forcefield=ff_h)
    mod.add(ligp.topology, ligp.positions)
    return mod, lig, chains


def run_pocket(tag, pdb, pocket_center, pocket_res, pose_pdbqt, out_json):
    from openff.toolkit import Molecule
    from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
    from openff.nagl_models import list_available_nagl_models
    from openmmforcefields.generators import SystemGenerator

    t0 = time.time()
    mod, lig, chains = build_complex(pdb, pocket_center, pocket_res, pose_pdbqt)
    _nagl_model = sorted(str(p) for p in list_available_nagl_models() if "1.0.0" in str(p))[0]
    NAGLToolkitWrapper().assign_partial_charges(lig, partial_charge_method=_nagl_model)
    gen = SystemGenerator(
        forcefields=["amber14/protein.ff14SB.xml", "amber14/tip3p.xml"],
        small_molecule_forcefield="openff-2.1.0", molecules=[lig],
    )
    system = gen.create_system(mod.topology, molecules=lig)
    # restrain ALL protein heavy atoms (chain-break lesson from f4)
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
    platform = mm.Platform.getPlatformByName("CUDA")
    prop = {"CudaPrecision": "double", "CudaDeviceIndex": "0"}
    sim = app.Simulation(mod.topology, system, integ, platform, prop)
    sim.context.setPositions(mod.positions)
    sim.context.reinitialize(preserveState=True)
    sim.minimizeEnergy(maxIterations=2000)
    sim.context.setVelocitiesToTemperature(300 * unit.kelvin, 42)
    sim.step(125000)  # 250 ps
    state = sim.context.getState(getPositions=True, getEnergy=True)
    positions = state.getPositions(asNumpy=True)
    pos = positions.value_in_unit(unit.angstrom)
    if not np.isfinite(positions).all() or np.max(np.abs(positions)) > 5000:
        raise RuntimeError(f"{tag}: MD blow-up guard triggered")
    with open(f"{NP}/mdrelaxed7_{tag}.pdb", "w") as fh:
        app.PDBFile.writeFile(sim.topology, positions, fh)

    # --- IE decomposition, CORRECTED units (kJ/mol, COUL=138.935, r in nm, no-PBC)
    nb = None
    for f in system.getForces():
        if isinstance(f, mm.NonbondedForce):
            nb = f
            break
    lig_idx = [a.index for a in mod.topology.atoms() if a.residue.name in ("LIG", "UNL")]
    prot_res = {}
    for a in mod.topology.atoms():
        if a.index not in lig_idx and a.residue.name not in ("HOH",):
            prot_res.setdefault((a.residue.chain.id, a.residue.id, a.residue.name), []).append(a.index)
    q, sig, eps = [], [], []
    for i in range(nb.getNumParticles()):
        c, s, e = nb.getParticleParameters(i)
        q.append(c.value_in_unit(unit.elementary_charge))
        sig.append(s.value_in_unit(unit.nanometer))
        eps.append(e.value_in_unit(unit.kilojoule_per_mole))
    q = np.array(q); sig = np.array(sig); eps = np.array(eps)
    pos_np = positions.value_in_unit(unit.nanometer)

    def pair_E(i, j):
        r = max(np.linalg.norm(pos_np[i] - pos_np[j]), 1e-6)
        eij = COUL * q[i] * q[j] / r
        sr = (sig[i] + sig[j]) / 2
        sr6 = (sr / r) ** 6
        eij += 4 * math.sqrt(eps[i] * eps[j]) * (sr6 ** 2 - sr6)
        return eij

    decomp = {}
    for (ch, rid, rname), idxs in prot_res.items():
        e_tot = sum(pair_E(i, j) for i in lig_idx for j in idxs if abs(i - j) > 1)
        if abs(e_tot) > 0.05:
            decomp[f"{rname}{rid}{ch}"] = round(e_tot, 2)
    top = sorted(decomp.items(), key=lambda kv: kv[1])[:8]
    sum_ie = round(sum(decomp.values()), 1)
    # ligand drift (LIG/UNL centroid, start vs MD-end)
    lig_end = np.array([pos[i] for i in lig_idx])
    drift = float(np.linalg.norm(lig_end.mean(0) -
                                 np.array([pos0[i].value_in_unit(unit.angstrom) for i in lig_idx]).mean(0)))
    json.dump({"tag": tag, "pdb": pdb, "ligand": "fgin", "chains_kept": chains,
               "md_drift_A": round(drift, 2), "runtime_s": round(time.time() - t0),
               "sum_IE_kJmol": sum_ie, "ie_units": "kJ/mol, COUL=138.935, no-PBC, no desolvation",
               "top_contacts": dict(top),
               "verdict": ("md-stable" if drift <= 4.0 else "md-unstable")},
              open(out_json, "w"), indent=1)
    print(f"{tag}: drift {drift:.2f} A, sumIE {sum_ie} kJ/mol, top {top[0][0] if top else '-'}", flush=True)


def main():
    for item in SHORTLIST:
        tag = item["tag"]
        out_json = f"{DOCK}/novelq7_p3_{tag}.json"
        if Path(out_json).exists() and "error" not in json.load(open(out_json)):
            print(f"{tag}: json exists, skip (delete to rerun)", flush=True)
            continue
        try:
            run_pocket(tag, item["pdb"], item["pocket_center"],
                       set(map(tuple, item["pocket_residues"])),
                       item["pose_pdbqt"], out_json)
        except Exception as e:
            json.dump({"tag": tag, "error": f"{type(e).__name__}: {e}"}, open(out_json, "w"), indent=1)
            print(tag, "ERROR", e, flush=True)
    print("ws7 p3 done")


if __name__ == "__main__":
    main()
