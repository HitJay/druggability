"""FEP-A v4: computational alanine scanning (side-chain interaction annihilation, TI).

Single source of truth for both the IE audit and the ddG numbers:

  contacts mode:  rebuild each relaxed complex's system exactly as F4 did
                  (amber14/protein.ff14SB + tip3p water params, openff-2.1.0/NAGL
                  ligand), extract NonbondedForce parameters, compute the ligand vs
                  every-residue interaction energy at t=0 from the RELAXED positions
                  with CORRECT units (kJ/mol, COUL=138.935 kJ nm e^-2), heavy atoms
                  both sides. Output: fep_a/contacts_<pdb>_<ligand>.json

  run mode:       for each anchor residue (side-chain heavy atoms), 8 lambda windows
                  scale that side chain's charges and epsilons by (1-lambda); per
                  window 2.5 ps equilibration + 25 ps sampling; estimator
                  dU/dlambda = -[Coulomb + 2*eps_cross*(sr6^2-sr6)] summed over
                  ligand(x)-anchor heavy pairs (exact derivative of the linearly
                  scaled parameters, lj mixing eps_cross = sqrt(eps_i(1-lam) eps_j));
                  ddG = trapz(<dU/dlam>, lam). Protein heavy atoms restrained as in
                  F4; ligand free. Output: fep_a/scan_<pdb>_<ligand>_<anchor>.json

Usage:
  python fep_a3_scan.py contacts <pdb> <emapunil|fgin>
  python fep_a3_scan.py run <pdb> <emapunil|fgin> <ANCHOR1,ANCHOR2,...>   # e.g. PHE23A
"""
import json
import os
import sys
import time

os.environ.setdefault("OPENMM_CPU_THREADS", "4")

import numpy as np
import openmm as mm
import openmm.unit as unit
from openmm import app
from openmmforcefields.generators import SMIRNOFFTemplateGenerator

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/fep_a"
DOCK = f"{BASE}/output/docking"
COUL = 138.935456  # kJ nm / e^2  (kJ/mol with r in nm)

BACKBONE = {"N", "CA", "C", "O", "OXT", "HA", "H", "HN"}


def lig_molecule(ligand):
    from openmmforcefields.generators import SMIRNOFFTemplateGenerator  # noqa: F401
    # import order empirically matters: generators must be in before the openff
    # Molecule is built, or SMIRNOFF template matching later fails silently
    from openff.toolkit import Molecule
    from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
    from openff.nagl_models import list_available_nagl_models
    from fep_smiles import LIGAND_SMILES
    lig = Molecule.from_smiles(LIGAND_SMILES[ligand])
    model = sorted(str(p) for p in list_available_nagl_models() if "1.0.0" in str(p))[0]
    NAGLToolkitWrapper().assign_partial_charges(lig, partial_charge_method=model)
    return lig


_FF_CACHE = {}

def build_system(pdb, ligand):
    """Relaxed complex PDB -> (topology, positions[nm ndarray], system, nb, lig_idx,
    res_atoms). Reuses the F4 parametrisation exactly."""
    lig = lig_molecule(ligand)
    if ligand not in _FF_CACHE:
        tg = SMIRNOFFTemplateGenerator(molecules=[lig])
        ff = app.ForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
        ff.registerTemplateGenerator(tg.generator)
        _FF_CACHE[ligand] = ff
    ff = _FF_CACHE[ligand]

    def gen_create(topology):
        return ff.createSystem(topology, nonbondedMethod=app.CutoffNonPeriodic,
                               nonbondedCutoff=1.2 * unit.nanometer)
    relaxed = f"{DOCK}/f4_{pdb}_{ligand}_relaxed.pdb" if ligand == "fgin" else f"{DOCK}/f4_{pdb}_relaxed.pdb"
    p = app.PDBFile(relaxed)
    system = gen_create(p.topology)
    nb = None
    for f in range(system.getNumForces()):
        if isinstance(system.getForce(f), mm.NonbondedForce):
            nb = system.getForce(f)
    if nb is None:
        raise RuntimeError("no NonbondedForce")
    n = system.getNumParticles()
    q = np.zeros(n); sig = np.zeros(n); eps = np.zeros(n)
    for i in range(n):
        c, s, e = nb.getParticleParameters(i)
        q[i] = c.value_in_unit(unit.elementary_charge)
        sig[i] = s.value_in_unit(unit.nanometer)
        eps[i] = e.value_in_unit(unit.kilojoule_per_mole)
    pos = np.asarray(p.positions.value_in_unit(unit.nanometer), dtype=float)
    # ligand: ALL atoms (H included) — charges are physically distributed over H;
    # heavy-only subsets carry a spurious net charge and corrupt Coulomb sums
    lig_idx = [a.index for a in p.topology.atoms()
               if a.residue.name in ("UNL", "LIG")]
    res_atoms = {}
    for a in p.topology.atoms():
        if a.residue.name in ("UNL", "LIG", "HOH"):
            continue
        key = f"{a.residue.name}{a.residue.id}{a.residue.chain.id}"
        # side-chain definition: residue-filtered, backbone names excluded
        if a.name not in BACKBONE:
            res_atoms.setdefault(key, []).append(a.index)
    return p.topology, pos, system, nb, q, sig, eps, lig_idx, res_atoms


def ie_decomp(pos, q, sig, eps, lig_idx, res_atoms):
    """Ligand-vs-residue interaction energies (kJ/mol), heavy atoms, exact LJ mixing."""
    li = np.asarray(lig_idx)
    P = pos[li]
    qi, si, ei = q[li], sig[li], eps[li]
    out = {}
    for key, idxs in res_atoms.items():
        ji = np.asarray(idxs)
        Q = pos[ji]
        d = np.linalg.norm(P[:, None, :] - Q[None, :, :], axis=-1)          # (nL, nR)
        qj, sj, ej = q[ji], sig[ji], eps[ji]
        sr6 = ((si[:, None] + sj[None, :]) * 0.5 / d) ** 6
        vdw = (4 * np.sqrt(ei[:, None] * ej[None, :]) * (sr6 ** 2 - sr6)).sum()
        coul = (COUL * qi[:, None] * qj[None, :] / d).sum()
        e = vdw + coul
        if abs(e) > 0.05:
            out[key] = round(float(e), 2)
    return dict(sorted(out.items(), key=lambda kv: kv[1]))


def mode_contacts(pdb, ligand):
    t0 = time.time()
    topo, pos, system, nb, q, sig, eps, lig_idx, res_atoms = build_system(pdb, ligand)
    decomp = ie_decomp(pos, q, sig, eps, lig_idx, res_atoms)
    res = {"pdb": pdb, "ligand": ligand, "units": "kJ/mol",
           "note": "recomputed from f4 relaxed complex at t=0, heavy atoms, COUL=138.935",
           "top_contacts": dict(list(decomp.items())[:10]),
           "all_contacts": decomp, "runtime_s": round(time.time() - t0)}
    out = f"{OUT}/contacts_{pdb}_{ligand}.json"
    json.dump(res, open(out, "w"), indent=1)
    print(f"[{pdb}/{ligand}] top:", list(res["top_contacts"].items())[:8], flush=True)
    print("saved", out, flush=True)


# ---------------- run mode ----------------

def dUdlam(pos_lig, pos_anch, qi_l, si_l, ei_l, qj_a, sj_a, ej_a, lam):
    """dU/dlambda of scaling anchor (q,e) by (1-lam); exact for LJ geometric mixing."""
    d = np.linalg.norm(pos_lig[:, None, :] - pos_anch[None, :, :], axis=-1)
    d = np.maximum(d, 1e-6)
    sr6 = ((si_l[:, None] + sj_a[None, :]) * 0.5 / d) ** 6
    eps_cross = np.sqrt((ei_l[:, None] * (1 - lam)) * ej_a[None, :])
    vdw = 2 * eps_cross * (sr6 ** 2 - sr6)          # = -dU/dlam vdW part
    coul = COUL * qi_l[:, None] * (qj_a[None, :] * (1 - lam)) / d  # = -dU/dlam coul part
    return float((vdw + coul).sum())                 # <-dU/dlam>


def mode_run(pdb, ligand, anchors):
    t0 = time.time()
    topo, pos, system, nb, q, sig, eps, lig_idx, res_atoms = build_system(pdb, ligand)
    li = np.asarray(lig_idx)
    # restraint: protein heavy atoms to relaxed positions (ligand free) — same spirit as F4
    force = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    force.addGlobalParameter("k", 5.0 * unit.kilocalorie_per_mole / unit.angstrom ** 2)
    for p_ in ("x0", "y0", "z0"):
        force.addPerParticleParameter(p_)
    for a in topo.atoms():
        if (a.residue.name not in ("UNL", "LIG") and a.element is not None
                and a.element.symbol != "H"):
            i = a.index
            force.addParticle(i, [pos[i, 0], pos[i, 1], pos[i, 2]])
    # ligand heavy atoms restrained weakly (1 kcal/mol/A^2) to the relaxed binding
    # pose: in vacuum the ligand otherwise diffuses out of the pocket within ps,
    # which annihilates the signal (observed: 4DKL gradient -> 0 after 2.5 ps).
    # ddG then measures interaction annihilation AT the binding geometry.
    force.setForceGroup(1)
    lig_force = mm.CustomExternalForce("0.5*k_lig*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    lig_force.addGlobalParameter("k_lig", 1.0 * unit.kilocalorie_per_mole / unit.angstrom ** 2)
    for p_ in ("x0", "y0", "z0"):
        lig_force.addPerParticleParameter(p_)
    for a in topo.atoms():
        if (a.residue.name in ("UNL", "LIG") and a.element is not None
                and a.element.symbol != "H"):
            i = a.index
            lig_force.addParticle(i, [pos[i, 0], pos[i, 1], pos[i, 2]])
    system.addForce(force)
    system.addForce(lig_force)

    plat = mm.Platform.getPlatformByName("CUDA")
    prop = {"CudaPrecision": os.environ.get("FEP_CUDA_PRECISION", "mixed"),
            "CudaDeviceIndex": os.environ.get("CUDA_DEVICE", "0")}
    integ = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 2 * unit.femtoseconds)
    ctx = mm.Context(system, integ, plat, prop)
    ctx.setPositions(pos)
    # minimise BEFORE dynamics: relaxed PDBs from F4 were written post-MD but the
    # SystemGenerator rebuild can carry clashes (6X3X t0 E = +1.2e5 kJ/mol -> MD blow-up)
    e0 = ctx.getState(getEnergy=True).getPotentialEnergy()
    e0v = e0.value_in_unit(unit.kilojoule_per_mole)
    mm.LocalEnergyMinimizer.minimize(ctx, tolerance=100, maxIterations=500)
    e1 = ctx.getState(getEnergy=True).getPotentialEnergy()
    e1v = e1.value_in_unit(unit.kilojoule_per_mole)
    if e1v > e0v:  # minimisation diverged (observed on 1XVP/fgin) -> revert to t0 coords
        ctx.setPositions(pos)
        e1v = e0v
        print(f"[{pdb}/{ligand}] minimisation DIVERGED ({e0v:.0f} -> {e1v:.0f}); "
              f"reverted to unminimised coordinates", flush=True)
    else:
        print(f"[{pdb}/{ligand}] minimisation: {e0v:.0f} -> {e1v:.0f} kJ/mol", flush=True)
    if e1v > 5000:  # still clashy -> stronger minimisation attempt
        mm.LocalEnergyMinimizer.minimize(ctx, tolerance=10, maxIterations=5000)
        e2 = ctx.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        if e2 < e1v:
            e1v = e2
        else:
            ctx.setPositions(pos)
            e1v = e0v
        print(f"[{pdb}/{ligand}] second-pass minimisation -> {e1v:.0f} kJ/mol", flush=True)

    results = {"pdb": pdb, "ligand": ligand, "method": "side-chain annihilation TI, "
               "8 windows, 2.5 ps eq + 25 ps sampling per window, protein-heavy "
               "restraints 5 kcal/mol/A^2, ligand heavy atoms restrained 1 kcal/mol/A^2 to relaxed pose", "anchors": {}}
    for anchor in anchors:
        if anchor not in res_atoms:
            print(f"[{pdb}/{ligand}] anchor {anchor}: no side-chain heavy atoms, skip", flush=True)
            continue
        a_idx = res_atoms[anchor]
        # t0 validation: dU/dlam at lam=0 must equal -(native ligand-anchor IE)
        ai = np.asarray(a_idx)
        native_ie = dUdlam(pos[li], pos[ai], q[li], sig[li], eps[li],
                           q[ai], sig[ai], eps[ai], 0.0)
        lambdas = [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0]
        grad, rows = [], []
        ta = time.time()
        for lam in lambdas:
            for i in a_idx:
                nb.setParticleParameters(i, q[i] * (1 - lam) * unit.elementary_charge,
                                         sig[i] * unit.nanometer,
                                         eps[i] * (1 - lam) * unit.kilojoule_per_mole)
            nb.updateParametersInContext(ctx)
            ctx.setVelocitiesToTemperature(300 * unit.kelvin, 42)
            integ.step(1250)  # 2.5 ps
            acc, nfr = 0.0, 0
            for _ in range(25):
                integ.step(625)  # 25 ps / 25 frames
                st = ctx.getState(getPositions=True)
                pv = st.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
                acc += dUdlam(pv[li], pv[ai], q[li], sig[li], eps[li],
                              q[ai], sig[ai], eps[ai], lam)
                nfr += 1
            m = acc / nfr  # <-dU/dlam>
            grad.append(m)
            rows.append({"lambda": lam, "minus_dUdlam_kJmol": round(m, 2)})
            print(f"[{pdb}/{ligand}/{anchor}] lam={lam:.2f} <-dU/dlam>={m:9.2f} kJ/mol "
                  f"({time.time()-ta:.0f}s)", flush=True)
        ddG = -float(np.trapezoid(grad, lambdas))  # dG = int <dU/dlam> dlam
        results["anchors"][anchor] = {
            "native_IE_kJmol_t0": round(native_ie, 2),
            "windows": rows,
            "ddG_kJmol": round(ddG, 2),
            "ddG_kcalmol": round(ddG / 4.184, 2),
            "interpretation": ("positive => annihilation costs binding free energy => ligand uses this side chain"
                               if ddG > 0 else "~zero/negative => no net contribution"),
        }
        print(f"[{pdb}/{ligand}/{anchor}] ddG = {ddG:.2f} kJ/mol ({ddG/4.184:.2f} kcal/mol)",
              flush=True)
        json.dump(results, open(f"{OUT}/scan_{pdb}_{ligand}.json", "w"), indent=1)
    results["runtime_s"] = round(time.time() - t0)
    json.dump(results, open(f"{OUT}/scan_{pdb}_{ligand}.json", "w"), indent=1)
    print(f"[{pdb}/{ligand}] DONE in {results['runtime_s']}s -> scan_{pdb}_{ligand}.json", flush=True)




def build_manual_debug(pdb, ligand):
    """Byte-for-byte manual recipe (module scope) for the UNL-match A/B test."""
    lig = lig_molecule(ligand)
    from openmmforcefields.generators import SMIRNOFFTemplateGenerator
    tg = SMIRNOFFTemplateGenerator(molecules=[lig])
    ff = app.ForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
    ff.registerTemplateGenerator(tg.generator)
    relaxed = f"{DOCK}/f4_{pdb}_{ligand}_relaxed.pdb" if ligand == "fgin" else f"{DOCK}/f4_{pdb}_relaxed.pdb"
    p = app.PDBFile(relaxed)
    return ff.createSystem(p.topology, nonbondedMethod=app.CutoffNonPeriodic,
                           nonbondedCutoff=1.2 * unit.nanometer)
