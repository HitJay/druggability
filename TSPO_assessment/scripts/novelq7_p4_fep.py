"""ws7 P4: annihilation-TI computational alanine scanning on ws7 novel-pocket
complexes (mdrelaxed7_<tag>.pdb), for FGIN and (optionally) emapunil.

Reuses the fep_a3 machinery verbatim (same dUdlam, same 8-lambda window schedule,
same restraints) but reads the ws7 relaxed novel-pocket complexes instead of the
f4 known-pocket ones. Anchor keys use the ws7 p3 decomp convention
<RESNAME><resid><chain> on the mdrelaxed complex (pdbfixer-numbering, self-consistent).

Usage: python novelq7_p4_fep.py <tag> <ligand> [ANCHOR ...]
       anchors default = top-3 side-chain contacts from novelq7_p3_<tag>.json
Output: output/fep_a7/scan7_<tag>_<ligand>.json
"""
import json, os, sys, time
import numpy as np

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/fep_a7"
os.makedirs(OUT, exist_ok=True)

# reuse fep_a3_lib internals (dUdlam, constants, ff cache) without its hard-coded paths
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("fep_a3_lib", f"{BASE}/scripts/fep_a3_lib.py")
_flib = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_flib)

import openmm as mm
from openmm import app, unit


def build_ws7_system(relaxed_pdb, ligand):
    """Same recipe as fep_a3_lib.build_system but on an arbitrary relaxed PDB."""
    lig = _flib.lig_molecule(ligand)
    if ligand not in _flib._FF_CACHE:
        tg = _flib.SMIRNOFFTemplateGenerator(molecules=[lig])
        ff = app.ForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
        ff.registerTemplateGenerator(tg.generator)
        _flib._FF_CACHE[ligand] = ff
    ff = _flib._FF_CACHE[ligand]
    p = app.PDBFile(relaxed_pdb)
    system = ff.createSystem(p.topology, nonbondedMethod=app.CutoffNonPeriodic,
                             nonbondedCutoff=1.2 * unit.nanometer)
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
    lig_idx = [a.index for a in p.topology.atoms() if a.residue.name in ("UNL", "LIG")]
    res_atoms = {}
    for a in p.topology.atoms():
        if a.residue.name in ("UNL", "LIG", "HOH"):
            continue
        if a.name not in _flib.BACKBONE:
            res_atoms.setdefault(f"{a.residue.name}{a.residue.id}{a.residue.chain.id}", []).append(a.index)
    return p.topology, pos, system, nb, q, sig, eps, lig_idx, res_atoms


def run_ti(tag, ligand, anchors, relaxed=None):
    if relaxed is None:
        relaxed = (f"{BASE}/output/novel_pockets/mdrelaxed7_{tag}.pdb" if ligand == "fgin"
                   else f"{BASE}/output/novel_pockets/mdrelaxed_{tag}.pdb")
    topo, pos, system, nb, q, sig, eps, lig_idx, res_atoms = build_ws7_system(relaxed, ligand)
    li = np.asarray(lig_idx)
    # restraints identical to fep_a3 mode_run
    force = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    force.addGlobalParameter("k", 5.0 * unit.kilocalorie_per_mole / unit.angstrom ** 2)
    for p_ in ("x0", "y0", "z0"):
        force.addPerParticleParameter(p_)
    for a in topo.atoms():
        if (a.residue.name not in ("UNL", "LIG") and a.element is not None
                and a.element.symbol != "H"):
            i = a.index
            force.addParticle(i, [pos[i, 0], pos[i, 1], pos[i, 2]])
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
    e0 = ctx.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    mm.LocalEnergyMinimizer.minimize(ctx, tolerance=100, maxIterations=500)
    e1 = ctx.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    if e1 > e0:
        ctx.setPositions(pos); e1 = e0
        print(f"[{tag}/{ligand}] minimisation diverged -> reverted", flush=True)
    if e1 > 5000:
        mm.LocalEnergyMinimizer.minimize(ctx, tolerance=10, maxIterations=5000)
        e2 = ctx.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        if e2 < e1:
            e1 = e2
        else:
            ctx.setPositions(pos); e1 = e0

    out = {"tag": tag, "ligand": ligand, "method": "side-chain annihilation TI (fep_a3 recipe), "
           "8 windows, 2.5 ps eq + 25 ps sampling per window, protein-heavy 5 kcal/mol/A^2, "
           "ligand heavy 1 kcal/mol/A^2 restraints", "anchors": {}}
    t0 = time.time()
    for anchor in anchors:
        if anchor not in res_atoms:
            print(f"[{tag}/{ligand}] anchor {anchor}: no side-chain heavy atoms, skip", flush=True)
            continue
        a_idx = res_atoms[anchor]
        ai = np.asarray(a_idx)
        native_ie = _flib.dUdlam(pos[li], pos[ai], q[li], sig[li], eps[li],
                                 q[ai], sig[ai], eps[ai], 0.0)
        lambdas = [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0]
        grad, rows = [], []
        for lam in lambdas:
            for i in a_idx:
                nb.setParticleParameters(i, q[i] * (1 - lam) * unit.elementary_charge,
                                         sig[i] * unit.nanometer,
                                         eps[i] * (1 - lam) * unit.kilojoule_per_mole)
            nb.updateParametersInContext(ctx)
            ctx.setVelocitiesToTemperature(300 * unit.kelvin, 42)
            integ.step(1250)
            acc, nfr = 0.0, 0
            for _ in range(25):
                integ.step(625)
                pv = ctx.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
                acc += _flib.dUdlam(pv[li], pv[ai], q[li], sig[li], eps[li],
                                    q[ai], sig[ai], eps[ai], lam)
                nfr += 1
            m = acc / nfr
            grad.append(m)
            rows.append({"lambda": lam, "minus_dUdlam_kJmol": round(m, 2)})
            print(f"[{tag}/{ligand}/{anchor}] lam={lam:.2f} <-dU/dlam>={m:9.2f} ({time.time()-t0:.0f}s)", flush=True)
        ddG = -float(np.trapezoid(grad, lambdas))
        out["anchors"][anchor] = {"native_IE_kJmol_t0": round(native_ie, 2), "windows": rows,
                                  "ddG_kJmol": round(ddG, 2), "ddG_kcalmol": round(ddG / 4.184, 2),
                                  "interpretation": ("positive => ligand uses this side chain" if ddG > 0
                                                     else "~zero/negative => no net contribution")}
        json.dump(out, open(f"{OUT}/scan7_{tag}_{ligand}.json", "w"), indent=1)
        print(f"[{tag}/{ligand}/{anchor}] ddG = {ddG:.2f} kJ/mol", flush=True)
    out["runtime_s"] = round(time.time() - t0)
    json.dump(out, open(f"{OUT}/scan7_{tag}_{ligand}.json", "w"), indent=1)
    print(f"[{tag}/{ligand}] DONE -> scan7_{tag}_{ligand}.json", flush=True)


def default_anchors(tag, ligand="fgin"):
    src_json = (f"{BASE}/output/docking/novelq7_p3_{tag}.json" if ligand == "fgin"
                else f"{BASE}/output/docking/novelq_p6_{tag}.json")
    j = json.load(open(src_json))
    keys = [k for k, v in sorted(j["top_contacts"].items(), key=lambda kv: kv[1])[:3]]
    if ligand == "fgin":
        return keys  # p3 keys already carry the chain suffix
    # ws6 p6 keys have NO chain suffix (e.g. "LEU58") -> resolve chain from the
    # relaxed complex PDB (unique resid within each kept chain set)
    relaxed = f"{BASE}/output/novel_pockets/mdrelaxed_{tag}.pdb"
    seen = {}
    for l in open(relaxed):
        if l.startswith(("ATOM", "HETATM")) and l[17:20].strip() not in ("UNL", "LIG", "HOH"):
            seen.setdefault(l[17:20].strip() + l[22:26].strip(), set()).add(l[21].strip())
    out = []
    for k in keys:
        chains = sorted(seen.get(k, []))
        if not chains:
            print(f"[{tag}/{ligand}] anchor {k}: residue not found in relaxed PDB, skip")
            continue
        out.append(k + chains[0])
    return out


if __name__ == "__main__":
    tag, ligand = sys.argv[1], sys.argv[2]
    anchors = sys.argv[3:] or default_anchors(tag, ligand)
    run_ti(tag, ligand, anchors)
