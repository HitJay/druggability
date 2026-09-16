#!/usr/bin/env python3
"""
scripts/compare_selectivity_mechanisms.py

Evaluate whether computational tools can predict/explain the >1000-fold selectivity
of OXT_Gly (Pro7Gly) over vasopressin receptors (especially V2R / V1aR).

Methods:
1. Structural superposition of active OXTR (7QVM) and active V2R (7DW9).
2. Helix I shift & steric clash analysis (measuring why OXT/OXT_Gly is sterically compromised in V2R).
3. Residue micro-environment analysis at Position 7 (Pro vs Gly in OXTR vs V2R).
4. Physics-based OpenMM MM/GBSA (Amber14SB + GBn2 with SD+L-BFGS minimization) binding free energy:
   - OXTR:OXT
   - OXTR:OXT_Gly
   - V2R:AVP
   - V2R:OXT
   - V2R:OXT_Gly
5. Generate comparison report JSON.
"""

import os
import copy
import json
import numpy as np
from pathlib import Path
import warnings
from Bio.PDB import MMCIFParser, PDBParser, Superimposer, PDBIO, Select
from pdbfixer import PDBFixer
import openmm.app as app
import openmm as mm
import openmm.unit as unit

warnings.filterwarnings('ignore')

BASE_DIR = Path("/das/user/QYJI/druggability/OXTR_assessment")
RAW_DIR = BASE_DIR / "raw_pdb"
STRUCT_DIR = BASE_DIR / "structures"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

cif_p = MMCIFParser(QUIET=True)
pdb_p = PDBParser(QUIET=True)

class V2RSelect(Select):
    """Truncate disordered flexible C-terminal tail beyond Helix 8 at residue 335 to ensure clean forcefield parametrization."""
    def accept_residue(self, residue):
        return residue.id[0] == ' ' and residue.id[1] <= 335

class ChainSelect(Select):
    def __init__(self, chain_id):
        self.chain_id = chain_id
    def accept_chain(self, chain):
        return chain.id == self.chain_id

def minimize_and_energy(pdb_path):
    """Run PDBFixer + OpenMM minimization (Amber14SB + GBn2) and return potential energy (kcal/mol)."""
    fixer = PDBFixer(filename=str(pdb_path))
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)

    temp_fixed = pdb_path.with_suffix(".fixed.pdb")
    with open(temp_fixed, "w") as f:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, f)

    p = app.PDBFile(str(temp_fixed))
    forcefield = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")
    system = forcefield.createSystem(p.topology, nonbondedMethod=app.NoCutoff, constraints=None)
    integrator = mm.VerletIntegrator(0.001 * unit.picoseconds)
    sim = app.Simulation(p.topology, system, integrator)
    sim.context.setPositions(p.positions)

    # 2-step minimization: SD 100 + L-BFGS 200
    sim.minimizeEnergy(maxIterations=100)
    sim.minimizeEnergy(maxIterations=200, tolerance=0.05 * unit.kilojoules_per_mole / unit.nanometer)
    
    e = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)
    
    min_pdb = pdb_path.with_suffix(".min.pdb")
    with open(min_pdb, "w") as f:
        app.PDBFile.writeFile(p.topology, sim.context.getState(getPositions=True).getPositions(), f)

    if temp_fixed.exists():
        temp_fixed.unlink()

    return e

def compute_mmgbsa_binding_energy(rec_pdb, pep_pdb, complex_pdb):
    """ΔG_bind = E(complex) - E(receptor) - E(peptide)"""
    print(f"  Minimizing complex: {complex_pdb.name}...")
    e_complex = minimize_and_energy(complex_pdb)
    print(f"  Minimizing receptor: {rec_pdb.name}...")
    e_rec = minimize_and_energy(rec_pdb)
    print(f"  Minimizing peptide: {pep_pdb.name}...")
    e_pep = minimize_and_energy(pep_pdb)

    delta_g = e_complex - e_rec - e_pep
    return delta_g, e_complex, e_rec, e_pep

def main():
    print("=== Step 1: Loading structures & Structural Superposition ===")
    s_7qvm = cif_p.get_structure('7QVM', str(RAW_DIR / '7QVM.cif'))
    s_7dw9 = cif_p.get_structure('7DW9', str(RAW_DIR / '7DW9.cif'))

    r_7qvm = s_7qvm[0]['R'] # OXTR
    l_7qvm = s_7qvm[0]['L'] # OXT
    r_7dw9 = s_7dw9[0]['R'] # V2R
    l_7dw9 = s_7dw9[0]['C'] # AVP

    # Transmembrane core alignment (TM2, TM3, TM4, TM6)
    core_pairs = [
        (92, 92), (96, 96), (100, 100),   # TM2
        (116, 116), (119, 119), (120, 120), (136, 136), (137, 137), # TM3
        (171, 176), (175, 180),           # TM4
        (291, 287), (292, 288), (295, 291) # TM6 bottom
    ]
    
    atoms_oxtr = []
    atoms_v2r = []
    for r_o, r_v in core_pairs:
        if r_o in r_7qvm and r_v in r_7dw9:
            if 'CA' in r_7qvm[r_o] and 'CA' in r_7dw9[r_v]:
                atoms_oxtr.append(r_7qvm[r_o]['CA'])
                atoms_v2r.append(r_7dw9[r_v]['CA'])

    sup = Superimposer()
    sup.set_atoms(atoms_oxtr, atoms_v2r)
    print(f"OXTR (7QVM) vs V2R (7DW9) Core Transmembrane RMSD: {sup.rms:.3f} Å ({len(atoms_oxtr)} CAs)")

    # Apply superposition to 7DW9
    sup.apply(s_7dw9[0].get_atoms())

    # Save aligned V2R receptor (truncated at 335) and AVP ligand
    io = PDBIO()
    v2r_rec_pdb = STRUCT_DIR / "7DW9_v2r_aligned_receptor.pdb"
    avp_lig_pdb = STRUCT_DIR / "7DW9_avp_aligned_ligand.pdb"
    io.set_structure(r_7dw9)
    io.save(str(v2r_rec_pdb), select=V2RSelect())
    io.set_structure(l_7dw9)
    io.save(str(avp_lig_pdb), select=ChainSelect('C'))

    # Save V2R:AVP complex (truncated at 335)
    from Bio.PDB.Model import Model
    from Bio.PDB.Structure import Structure
    c_v2r_struct = Structure("7DW9_complex")
    c_v2r_model = Model(0)
    # add clean truncated receptor
    p_temp = PDBParser(QUIET=True).get_structure('rec_clean', str(v2r_rec_pdb))
    c_v2r_model.add(copy.deepcopy(p_temp[0]['R']))
    c_v2r_model.add(copy.deepcopy(l_7dw9))
    c_v2r_struct.add(c_v2r_model)
    io.set_structure(c_v2r_struct)
    v2r_avp_complex_pdb = STRUCT_DIR / "7DW9_v2r_avp_complex.pdb"
    io.save(str(v2r_avp_complex_pdb))

    print("\n=== Step 2: Measuring Helix I Shift & Steric Clash Mechanism ===")
    ca_e42_oxtr = r_7qvm[42]['CA'].coord
    ca_a42_v2r = r_7dw9[42]['CA'].coord
    helix1_ca_dist = np.linalg.norm(ca_e42_oxtr - ca_a42_v2r)
    print(f"TM1 (Pos 42) CA coordinate displacement OXTR vs V2R: {helix1_ca_dist:.2f} Å")

    gly9_atoms = [a for a in l_7qvm[9].get_atoms()]
    min_dist_to_oxtr = min(np.linalg.norm(a.coord - b.coord) for a in gly9_atoms for b in r_7qvm[42].get_atoms())
    min_dist_to_v2r = min(np.linalg.norm(a.coord - b.coord) for a in gly9_atoms for b in r_7dw9[42].get_atoms())
    print(f"OXT Gly9 closest distance to OXTR E42: {min_dist_to_oxtr:.2f} Å")
    print(f"OXT Gly9 closest distance to V2R A42: {min_dist_to_v2r:.2f} Å")

    print("\n=== Step 3: Residue Environment at Position 7 (Pro vs Gly) ===")
    pro7 = l_7qvm[7]
    k306 = r_7qvm[306]
    dist_p7_k306 = min(np.linalg.norm(a.coord - b.coord) for a in pro7.get_atoms() for b in k306.get_atoms())
    print(f"OXTR: OXT Pro7 closest contact to Lys306: {dist_p7_k306:.2f} Å")
    
    l302 = r_7dw9[302]
    dist_p7_l302 = min(np.linalg.norm(a.coord - b.coord) for a in pro7.get_atoms() for b in l302.get_atoms())
    print(f"V2R: OXT Pro7 closest contact to Leu302: {dist_p7_l302:.2f} Å")

    print("\n=== Step 4: Constructing Mutated & Chimeric Complexes for MM/GBSA ===")
    oxtr_rec_pdb = STRUCT_DIR / "7QVM_active_receptor.pdb"
    oxt_pep_pdb = STRUCT_DIR / "7QVM_oxt_ligand.pdb"
    oxtr_oxt_complex_pdb = STRUCT_DIR / "7QVM_active_complex.pdb"

    # Build OXT_Gly ligand pdb
    l_oxt_gly = copy.deepcopy(l_7qvm)
    r7 = l_oxt_gly[7]
    r7.resname = "GLY"
    for atom_id in ['CB', 'CG', 'CD']:
        if atom_id in r7:
            r7.detach_child(atom_id)
    
    oxt_gly_pep_pdb = STRUCT_DIR / "OXT_Gly_ligand.pdb"
    io.set_structure(l_oxt_gly)
    io.save(str(oxt_gly_pep_pdb))

    # Complex OXTR:OXT_Gly
    c_oxtr_oxtgly = Structure("OXTR_OXT_Gly")
    m_oxtr_oxtgly = Model(0)
    m_oxtr_oxtgly.add(copy.deepcopy(r_7qvm))
    m_oxtr_oxtgly.add(copy.deepcopy(l_oxt_gly))
    c_oxtr_oxtgly.add(m_oxtr_oxtgly)
    oxtr_oxtgly_complex_pdb = STRUCT_DIR / "OXTR_OXT_Gly_complex.pdb"
    io.set_structure(c_oxtr_oxtgly)
    io.save(str(oxtr_oxtgly_complex_pdb))

    # 2. V2R:OXT and V2R:OXT_Gly complexes (using clean truncated V2R)
    c_v2r_oxt = Structure("V2R_OXT")
    m_v2r_oxt = Model(0)
    m_v2r_oxt.add(copy.deepcopy(p_temp[0]['R']))
    m_v2r_oxt.add(copy.deepcopy(l_7qvm))
    c_v2r_oxt.add(m_v2r_oxt)
    v2r_oxt_complex_pdb = STRUCT_DIR / "V2R_OXT_complex.pdb"
    io.set_structure(c_v2r_oxt)
    io.save(str(v2r_oxt_complex_pdb))

    c_v2r_oxtgly = Structure("V2R_OXT_Gly")
    m_v2r_oxtgly = Model(0)
    m_v2r_oxtgly.add(copy.deepcopy(p_temp[0]['R']))
    m_v2r_oxtgly.add(copy.deepcopy(l_oxt_gly))
    c_v2r_oxtgly.add(m_v2r_oxtgly)
    v2r_oxtgly_complex_pdb = STRUCT_DIR / "V2R_OXT_Gly_complex.pdb"
    io.set_structure(c_v2r_oxtgly)
    io.save(str(v2r_oxtgly_complex_pdb))

    print("\n=== Step 5: Running OpenMM MM/GBSA Binding Free Energy Calculations ===")
    
    # 1. OXTR : OXT
    print("\n[Complex 1/5] Calculating OXTR : OXT (Native Agonist)...")
    dg_oxtr_oxt, e_c1, e_r1, e_p1 = compute_mmgbsa_binding_energy(oxtr_rec_pdb, oxt_pep_pdb, oxtr_oxt_complex_pdb)
    print(f"  -> OXTR:OXT ΔG_bind = {dg_oxtr_oxt:.2f} kcal/mol")

    # 2. OXTR : OXT_Gly
    print("\n[Complex 2/5] Calculating OXTR : OXT_Gly (Lilly Selective Analog)...")
    dg_oxtr_oxtgly, e_c2, e_r2, e_p2 = compute_mmgbsa_binding_energy(oxtr_rec_pdb, oxt_gly_pep_pdb, oxtr_oxtgly_complex_pdb)
    print(f"  -> OXTR:OXT_Gly ΔG_bind = {dg_oxtr_oxtgly:.2f} kcal/mol")

    # 3. V2R : AVP
    print("\n[Complex 3/5] Calculating V2R : AVP (Native Cognate Pair)...")
    dg_v2r_avp, e_c3, e_r3, e_p3 = compute_mmgbsa_binding_energy(v2r_rec_pdb, avp_lig_pdb, v2r_avp_complex_pdb)
    print(f"  -> V2R:AVP ΔG_bind = {dg_v2r_avp:.2f} kcal/mol")

    # 4. V2R : OXT
    print("\n[Complex 4/5] Calculating V2R : OXT (Cross-reactivity)...")
    dg_v2r_oxt, e_c4, e_r4, e_p4 = compute_mmgbsa_binding_energy(v2r_rec_pdb, oxt_pep_pdb, v2r_oxt_complex_pdb)
    print(f"  -> V2R:OXT ΔG_bind = {dg_v2r_oxt:.2f} kcal/mol")

    # 5. V2R : OXT_Gly
    print("\n[Complex 5/5] Calculating V2R : OXT_Gly (Counter-screen)...")
    dg_v2r_oxtgly, e_c5, e_r5, e_p5 = compute_mmgbsa_binding_energy(v2r_rec_pdb, oxt_gly_pep_pdb, v2r_oxtgly_complex_pdb)
    print(f"  -> V2R:OXT_Gly ΔG_bind = {dg_v2r_oxtgly:.2f} kcal/mol")

    # Selectivity Metrics
    sel_oxt = dg_v2r_oxt - dg_oxtr_oxt
    sel_oxtgly = dg_v2r_oxtgly - dg_oxtr_oxtgly
    enhancement = sel_oxtgly - sel_oxt

    results = {
        "structural_metrics": {
            "core_transmembrane_rmsd_A": round(float(sup.rms), 3),
            "tm1_ca_displacement_A": round(float(helix1_ca_dist), 2),
            "gly9_closest_to_oxtr_e42_A": round(float(min_dist_to_oxtr), 2),
            "gly9_closest_to_v2r_a42_A": round(float(min_dist_to_v2r), 2),
            "pro7_to_k306_oxtr_A": round(float(dist_p7_k306), 2),
            "pro7_to_l302_v2r_A": round(float(dist_p7_l302), 2)
        },
        "mmgbsa_binding_energies_kcal_mol": {
            "OXTR_OXT (native)": round(float(dg_oxtr_oxt), 2),
            "OXTR_OXT_Gly (selective)": round(float(dg_oxtr_oxtgly), 2),
            "V2R_AVP (cognate)": round(float(dg_v2r_avp), 2),
            "V2R_OXT (cross-reactive)": round(float(dg_v2r_oxt), 2),
            "V2R_OXT_Gly (counter-screen)": round(float(dg_v2r_oxtgly), 2)
        },
        "selectivity_evaluations_kcal_mol": {
            "delta_delta_G_OXT_selectivity (V2R - OXTR)": round(float(sel_oxt), 2),
            "delta_delta_G_OXT_Gly_selectivity (V2R - OXTR)": round(float(sel_oxtgly), 2),
            "selectivity_enhancement_by_Pro7Gly": round(float(enhancement), 2),
            "predicted_preference": "OXTR strongly favored over V2R for OXT_Gly" if sel_oxtgly > sel_oxt else "Inconclusive"
        }
    }

    print("\n=======================================================")
    print("=== SUMMARY OF COMPUTATIONAL SELECTIVITY PREDICTION ===")
    print("=======================================================")
    print(json.dumps(results, indent=2))

    with open(REPORT_DIR / "selectivity_computational_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    os.system(f"cp -f {REPORT_DIR}/* /TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/reports/")
    print("\nResults saved and synced to CIFS shared drive.")

if __name__ == "__main__":
    main()
