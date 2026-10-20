"""FEP-A v3: computational alanine scanning via ligand-residue nonbonded annihilation.

Reuses the f4 build_complex path verbatim (docked pose -> Modeller complex with
openff/NAGL ligand params -> system). For each pocket x ligand:
  - anchor residue side-chain heavy atoms identified from the topology
  - 8 lambda windows scale anchor-atom charges and epsilons (0=native, 1=no
    ligand<->anchor interaction)
  - per window: 2 ps re-equilibration + 50 ps sampling; interaction energy
    E_int(lam) recomputed each frame from stored parameters
  - ddG = -integral E_int dlam  (TI with linear scaling; weak-coupling caveat noted)

negative ddG => the ligand uses this residue.
"""
import json
import os
import sys
import time

os.environ.setdefault("OPENMM_CPU_THREADS", "4")

import numpy as np
import openmm as mm
import openmm.unit as unit

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
OUT = f"{BASE}/output/fep_a"
DOCK = f"{BASE}/output/docking"

# pocket -> (label, pose pdbqt file, pocket chain, anchor resid, anchor resname)
EMAP = {
    "4RYI": ("TSPO_anchor",          "f2_4RYI_emapunil_docked.pdbqt",   "A", 23, "PHE"),
    "6X3X": ("GABA-A_BZD_site",      "f2_6X3X_emapunil4_docked.pdbqt",  "B", 223, "LEU"),
    "4DKL": ("OPRM1_orthosteric",    "f2_4DKL_emapunil_docked.pdbqt",   "A", 83, "ASP"),
    "1XVP": ("CAR_LBD",              "f2_1XVP_emapunil4_docked.pdbqt",  "A", 59, "PHE"),
    "4XAQ": ("GRM2_negative_control","f2_4XAQ_emapunil_docked.pdbqt",   "A", 199, "ARG"),
}
FGIN = {
    "4RYI": ("TSPO_anchor",          "f2_4RYI_fgin_docked.pdbqt",       "A", 43, "MET"),
    "1XVP": ("CAR_LBD",              "f2_1XVP_fgin_docked.pdbqt",       "A", 132, "PHE"),
    "5TGZ": ("CNR1_orthosteric",     "f2_5TGZ_fgin_docked.pdbqt",       "A", 410, "SER"),
    "4DJH": ("OPRK1_orthosteric",    "f2_4DJH_fgin_docked.pdbqt",       "A", 420, "TYR"),
    "4XAQ": ("GRM2_negative_control","f2_4XAQ_fgin_docked.pdbqt",       "A", 227, "ARG"),
}


def build_emapunil(pdb):
    import emapunil_f4_iedecompo as e4
    return e4.build_complex(pdb, e4.POCKETS[pdb][1])


def build_fgin(pdb):
    import fgin_f4_iedecompo as f4
    return f4.build_complex(pdb, f4.POCKETS[pdb][1])


def main():
    pdb, ligand = sys.argv[1], sys.argv[2]
    n_win = int(sys.argv[sys.argv.index("--windows") + 1]) if "--windows" in sys.argv else 8
    smoke = "--smoke" in sys.argv
    table = EMAP if ligand == "emapunil" else FGIN
    label, pose, chain, resid, resname = table[pdb]

    if ligand == "emapunil":
        mod, lig = build_emapunil(pdb)
    else:
        mod, lig = build_fgin(pdb)

    lig_idx = [a.index for a in mod.topology.atoms()
               if a.residue.name in ("UNL", "LIG") and a.element is not None
               and a.element.symbol != "H"]
    anchor_atoms = [a.index for a in mod.topology.atoms()
                    if a.residue.chain.id == chain and a.residue.id == str(resid)
                    and a.residue.name == resname
                    and a.element is not None and a.element.symbol != "H"
                    and a.name not in ("N", "CA", "C", "O", "OXT", "HA")]
    print(f"[{pdb}/{ligand}] ligand heavy: {len(lig_idx)}, "
          f"anchor SC ({resname}{resid}{chain}): {len(anchor_atoms)} atoms", flush=True)

    from openmmforcefields.generators import SystemGenerator
    from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
    from openff.nagl_models import list_available_nagl_models
    _nagl = sorted(str(x) for x in list_available_nagl_models() if "1.0.0" in str(x))[0]
    NAGLToolkitWrapper().assign_partial_charges(lig, partial_charge_method=_nagl)
    gen = SystemGenerator(
        forcefields=["amber14/protein.ff14SB.xml", "amber14/tip3p.xml"],
        small_molecule_forcefield="openff-2.1.0",
        molecules=[lig],
    )
    system = gen.create_system(mod.topology, molecules=lig)

    nb = None
    for f in range(system.getNumForces()):
        if isinstance(system.getForce(f), mm.NonbondedForce):
            nb = system.getForce(f)
    orig = {i: nb.getParticleParameters(i) for i in set(lig_idx + anchor_atoms)}

    def apply_lambda(lam):
        # scale anchor charges (=> cross Coulomb with ligand) and anchor eps
        # (=> cross LJ) by (1-lam); ligand params untouched
        for i in anchor_atoms:
            c, s, e = orig[i]
            nb.setParticleParameters(i, c * (1 - lam), s, e * (1 - lam))

    plat = mm.Platform.getPlatformByName("CUDA")
    prop = {"CudaPrecision": "mixed", "CudaDeviceIndex": os.environ.get("CUDA_DEVICE", "0")}
    integ = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 2 * unit.femtoseconds)
    ctx = mm.Context(system, integ, plat, prop)
    ctx.setPositions(mod.positions)

    COUL = 138.935456
    def pair_energy():
        posv = np.asarray(ctx.getState(getPositions=True).getPositions(asNumpy=True)
                          .value_in_unit(unit.nanometer))
        e = 0.0
        for i in lig_idx:
            ci, si, ei = nb.getParticleParameters(i)
            ci = ci.value_in_unit(unit.elementary_charge)
            si = si.value_in_unit(unit.nanometer)
            ei = ei.value_in_unit(unit.kilojoule_per_mole)
            for j in anchor_atoms:
                cj, sj, ej = nb.getParticleParameters(j)
                cj = cj.value_in_unit(unit.elementary_charge)
                sj = sj.value_in_unit(unit.nanometer)
                ej = ej.value_in_unit(unit.kilojoule_per_mole)
                r = float(np.linalg.norm(posv[i] - posv[j]))
                if r < 1e-3:
                    continue
                sr = (si + sj) * 0.5 / r
                E6 = sr ** 6
                e += 4 * np.sqrt(ei * ej) * (E6 * E6 - E6) + COUL * ci * cj / r
        return e

    lambdas = np.linspace(0, 1, n_win)
    md_per_window = 5000 if smoke else 25000   # 10 ps smoke / 50 ps full
    results = {"pdb": pdb, "ligand": ligand, "label": label,
               "residue": f"{resname}{resid}{chain}",
               "lambdas": lambdas.tolist(), "E_int_kJmol": []}
    t0 = time.time()
    for lam in lambdas:
        apply_lambda(float(lam))
        nb.updateParametersInContext(ctx)
        ctx.setVelocitiesToTemperature(300 * unit.kelvin, 42)
        integ.step(500)  # 1 ps re-equilibration
        acc, nfr = 0.0, 0
        for _ in range(20):
            integ.step(md_per_window // 20)
            acc += pair_energy()
            nfr += 1
        e_avg = acc / nfr
        results["E_int_kJmol"].append(round(e_avg, 2))
        print(f"[{pdb}/{ligand}] lam={lam:.3f}  E_int={e_avg:9.2f} kJ/mol  "
              f"({time.time()-t0:.0f}s)", flush=True)

    ddG = -float(np.trapezoid(results["E_int_kJmol"], lambdas))
    results["ddG_kJmol"] = round(ddG, 2)
    results["ddG_kcalmol"] = round(ddG / 4.184, 2)
    results["runtime_s"] = round(time.time() - t0)
    results["method"] = ("computational alanine scanning: anchor side-chain charge/eps "
                         "annihilation vs ligand, TI over lambda, amber14+openff2.1/NAGL")
    print(f"[{pdb}/{ligand}] ddG = {ddG:.2f} kJ/mol ({ddG/4.184:.2f} kcal/mol) "
          f"[negative => ligand uses {resname}{resid}]", flush=True)
    out = f"{OUT}/{pdb}_{ligand}_scan.json"
    json.dump(results, open(out, "w"), indent=1)
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()
