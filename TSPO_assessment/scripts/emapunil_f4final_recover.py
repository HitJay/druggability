"""F4-final: recompute interaction-energy decomposition from the relaxed complexes.

The 4RYI/1XVP/4DKL/4XAQ runs printed top contacts to stdout but their per-pdb JSONs
were lost to the older shared-filename version. The relaxed complexes were saved, so
this script recomputes the decomposition from them (deterministic, no re-MD needed).
"""
import sys, json
import numpy as np

OUT = "/das/user/QYJI/druggability/TSPO_assessment/output/docking"
LABELS = {
    "4RYI": "TSPO_anchor",
    "6X3X": "GABA-A_BZD_site",
    "4DKL": "OPRM1_orthosteric",
    "1XVP": "CAR_LBD",
    "4XAQ": "GRM2_negative_control",
}

import openmm as mm
import openmm.unit as unit
from openmm import app

# Get AMBER-level protein charges once via a reference system (charges are identical
# across systems for the same forcefield); simpler: build a system per complex and
# extract NonbondedForce params.
from openmmforcefields.generators import SystemGenerator
from openff.toolkit import Molecule
from openff.toolkit.utils.nagl_wrapper import NAGLToolkitWrapper
from openff.nagl_models import list_available_nagl_models

_nagl_model = sorted(str(p) for p in list_available_nagl_models() if "1.0.0" in str(p))[0]

# emapunil SMILES from the f4 script
sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")
from emapunil_f4_iedecompo import EMAP_SMILES

lig = Molecule.from_smiles(EMAP_SMILES)
NAGLToolkitWrapper().assign_partial_charges(lig, partial_charge_method=_nagl_model)

gen = SystemGenerator(
    forcefields=["amber14/protein.ff14SB.xml", "amber14/tip3p.xml"],
    small_molecule_forcefield="openff-2.1.0",
    molecules=[lig],
)

def decompose(pdb):
    # load relaxed complex (already has H)
    p = app.PDBFile(f"{OUT}/f4_{pdb}_relaxed.pdb")
    # build system to obtain charges/sigmas/epsilons
    system = gen.create_system(p.topology, molecules=lig)
    nb = None
    for f in range(system.getNumForces()):
        fo = system.getForce(f)
        if isinstance(fo, mm.NonbondedForce):
            nb = fo
    if nb is None:
        raise RuntimeError("no NonbondedForce")
    n = system.getNumParticles()
    charge = np.zeros(n)
    sigma = np.zeros(n)
    eps = np.zeros(n)
    for i in range(n):
        c, s, e = nb.getParticleParameters(i)
        charge[i] = c.value_in_unit(unit.elementary_charge)
        sigma[i] = s.value_in_unit(unit.nanometer)
        eps[i] = e.value_in_unit(unit.kilojoule_per_mole)
    # positions
    pos = p.positions.value_in_unit(unit.nanometer)
    # ligand atoms = residue UNL/LIG
    lig_idx = [a.index for a in p.topology.atoms() if a.residue.name in ("UNL", "LIG")]
    # protein residues
    prot_res = {}
    for a in p.topology.atoms():
        if a.residue.name in ("UNL", "LIG"):
            continue
        if a.element is None or a.element.symbol == "H":
            continue
        key = (a.residue.chain.id, a.residue.id, a.residue.name)
        prot_res.setdefault(key, []).append(a.index)

    COUL = 138.935456  # kJ nm / e^2
    def pair_E(i, j):
        r = float(np.linalg.norm(pos[i] - pos[j]))
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
    return {"label": LABELS[pdb], "status": "ok",
            "top_contacts": dict(top), "all_contacts": decomp}

if __name__ == "__main__":
    only = sys.argv[1:] or [p for p in LABELS if p != "6X3X"]
    for pdb in only:
        print(f"=== {pdb} {LABELS[pdb]} ===", flush=True)
        try:
            res = decompose(pdb)
            print("top contacts:", list(res["top_contacts"].items()), flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            res = {"label": LABELS[pdb], "error": f"{type(e).__name__}: {e}"}
        json.dump({pdb: res}, open(f"{OUT}/emapunil_f4_iedecompo_{pdb}.json", "w"), indent=1)
    print("DONE")
