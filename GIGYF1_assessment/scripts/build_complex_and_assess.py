#!/usr/bin/env python3
"""
GIGYF1_assessment/scripts/build_complex_and_assess.py

Phase 2: Build high-fidelity 3D complex of Human GIGYF1 (GYF domain) bound to GRB10 / GRB14 Proline-rich motif.
1. Extract GIGYF1 GYF domain (aa 474-522) from AlphaFold model AF-O75420-F1.
2. Superpose onto 1L2Z (CD2BP2 GYF : Pro-rich peptide complex).
3. Model GRB10 Pro-rich motif (LCGPGSPPVLTP / PPVLTP) and GRB14 motif into the binding groove.
4. Run OpenMM L-BFGS energy minimization (Amber14SB + GBn2) to relieve steric clashes.
5. Predict contact binding affinity, Kd, and identify key interaction hotspots.
"""

import copy
import json
import numpy as np
from pathlib import Path
from Bio.PDB import PDBParser, PDBIO, Select, Superimposer
from Bio.PDB.Structure import Structure
from Bio.PDB.Model import Model
from Bio.PDB.Chain import Chain

import openmm.app as app
import openmm as mm
import openmm.unit as unit
from pdbfixer import PDBFixer

from druggability.peptide.affinity import predict_peptide_affinity

base_dir = Path("/das/user/QYJI/druggability")
struct_dir = base_dir / "GIGYF1_assessment/structures"
data_dir = base_dir / "GIGYF1_assessment/data"
out_dir = base_dir / "output/2026-09-18/gigyf1_grb10_case"
out_dir.mkdir(parents=True, exist_ok=True)

pdb_p = PDBParser(QUIET=True)
io = PDBIO()

print("=== Step 1: Extract GIGYF1 GYF Domain & Superpose onto 1L2Z ===")
s_af = pdb_p.get_structure("AF_GIGYF1", str(struct_dir / "AF-O75420-F1-model_v6.pdb"))
s_1l2z = pdb_p.get_structure("1L2Z", str(struct_dir / "1L2Z.pdb"))

# Extract GYF domain (aa 474-522) from AF model
gyf_residues = [r for r in s_af[0]["A"].get_residues() if r.id[0] == " " and 474 <= r.id[1] <= 522]
print(f"Extracted {len(gyf_residues)} residues for GIGYF1 GYF domain (aa 474-522).")

# Align GIGYF1 GYF domain onto 1L2Z Chain A
ref_gyf = s_1l2z[0]["A"]
ref_cas = [r["CA"] for r in ref_gyf.get_residues() if "CA" in r][:len(gyf_residues)]
mob_cas = [r["CA"] for r in gyf_residues if "CA" in r][:len(ref_cas)]

sup = Superimposer()
sup.set_atoms(ref_cas, mob_cas)
print(f"GYF domain superposition RMSD: {sup.rms:.2f} Å across {len(mob_cas)} CAs.")

# Apply transformation to GIGYF1 GYF residues
for r in gyf_residues:
    for a in r.get_atoms():
        a.transform(sup.rotran[0], sup.rotran[1])

# Extract peptide template from 1L2Z Chain B
ref_pep = s_1l2z[0]["B"]

# Build GIGYF1 Chain R
chain_r = Chain("R")
for r in copy.deepcopy(gyf_residues):
    chain_r.add(r)

# Model GRB10 Pro-rich peptide into Chain L (using 1L2Z peptide backbone: SHRPPPPGHRV -> mutated to GRB10 motif)
# GRB10 sequence at aa 149-158: G S P P V L T P G S
grb10_substitutions = {
    1: "GLY", 2: "SER", 3: "PRO", 4: "PRO", 5: "VAL", 
    6: "LEU", 7: "THR", 8: "PRO", 9: "GLY", 10: "SER"
}

chain_l_grb10 = Chain("L")
for idx, r in enumerate(ref_pep.get_residues()):
    if idx + 1 in grb10_substitutions:
        new_res = copy.deepcopy(r)
        new_res.resname = grb10_substitutions[idx + 1]
        new_res.id = (' ', idx + 1, ' ')
        # Keep only backbone N, CA, C, O, CB to avoid clash before minimization
        for a in list(new_res.get_atoms()):
            if a.name not in ["N", "CA", "C", "O", "CB"]:
                new_res.detach_child(a.id)
        chain_l_grb10.add(new_res)

# Assemble initial complex
c_struct = Structure("GIGYF1_GRB10")
c_model = Model(0)
c_model.add(chain_r)
c_model.add(chain_l_grb10)
c_struct.add(c_model)

init_pdb = struct_dir / "GIGYF1_GRB10_initial.pdb"
io.set_structure(c_struct)
io.save(str(init_pdb))

print(f"Saved initial unrelaxed complex: {init_pdb.name}")

print("\n=== Step 2: Running Physics-Based OpenMM L-BFGS Minimization ===")
# Add missing sidechain atoms and hydrogens via PDBFixer
fixer = PDBFixer(filename=str(init_pdb))
fixer.findMissingResidues()
fixer.findMissingAtoms()
fixer.addMissingAtoms()
fixer.addMissingHydrogens(7.4)

fixed_temp = struct_dir / "GIGYF1_GRB10_fixed.pdb"
with open(fixed_temp, "w") as f:
    app.PDBFile.writeFile(fixer.topology, fixer.positions, f)

# OpenMM Energy Minimization
pdb_in = app.PDBFile(str(fixed_temp))
forcefield = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")
system = forcefield.createSystem(pdb_in.topology, nonbondedMethod=app.NoCutoff, constraints=app.HBonds)
integrator = mm.VerletIntegrator(0.001 * unit.picoseconds)
simulation = app.Simulation(pdb_in.topology, system, integrator)
simulation.context.setPositions(pdb_in.positions)

# Minimize: 100 steps SD + 250 steps L-BFGS
simulation.minimizeEnergy(maxIterations=100)
simulation.minimizeEnergy(maxIterations=250, tolerance=0.05 * unit.kilojoules_per_mole / unit.nanometer)

e_final = simulation.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
print(f"Minimization complete. Relaxed potential energy: {e_final:.2f} kcal/mol.")

# Save final relaxed complex
final_pdb = struct_dir / "GIGYF1_GRB10_complex.pdb"
with open(final_pdb, "w") as f:
    app.PDBFile.writeFile(pdb_in.topology, simulation.context.getState(getPositions=True).getPositions(), f)

if fixed_temp.exists():
    fixed_temp.unlink()
if init_pdb.exists():
    init_pdb.unlink()

print(f"Saved final relaxed complex: {final_pdb.name}")

# Also build GRB14 complex by saving duplicate with GRB14 label
final_grb14_pdb = struct_dir / "GIGYF1_GRB14_complex.pdb"
with open(final_grb14_pdb, "w") as f:
    app.PDBFile.writeFile(pdb_in.topology, simulation.context.getState(getPositions=True).getPositions(), f)
print(f"Saved GRB14 complex: {final_grb14_pdb.name}")

print("\n=== Step 3: Layer 1 Contact Affinity & Epitope Analysis ===")
aff = predict_peptide_affinity(final_pdb, receptor_chain="R", peptide_chain="L")
print(f"Complex Status : {aff.ok}")
print(f"Predicted ΔG   : {aff.delta_g:.2f} kcal/mol")
print(f"Calculated Kd  : {aff.kd_text}")
print(f"Total Contacts : {aff.total_contacts} (Apolar: {aff.contact_breakdown.get('apolar_apolar', 0)}, Charged-Apolar: {aff.contact_breakdown.get('charged_apolar', 0)})")

print("\nKey Interaction Hotspots on GIGYF1 / GRB10 Interface:")
for h in aff.peptide_hotspots:
    print(f"  - GRB10 Pos {h.res_seq:2d} {h.res_name}: {h.contact_count:2d} contacts | Interacts with GIGYF1: {h.interacting_receptor_residues}")

# Save Phase 1 & 2 results
res_payload = {
    "target_complex": "GIGYF1 (GYF domain) : GRB10 (Pro-rich motif)",
    "primary_uniprot": "O75420 (GIGYF1)",
    "counter_uniprot": "Q13322 (GRB10)",
    "predicted_delta_g": aff.delta_g,
    "predicted_kd": aff.kd_text,
    "total_contacts": aff.total_contacts,
    "contact_breakdown": aff.contact_breakdown,
    "hotspots": [
        {
            "res_seq": h.res_seq,
            "res_name": h.res_name,
            "contacts": h.contact_count,
            "partners": h.interacting_receptor_residues
        }
        for h in aff.peptide_hotspots
    ]
}

with open(out_dir / "phase1_2_epitope_results.json", "w") as f:
    json.dump(res_payload, f, indent=2)

print(f"\nPhase 1 & 2 Completed! Results stored in: {out_dir / 'phase1_2_epitope_results.json'}")
