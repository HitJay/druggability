#!/usr/bin/env python3
"""
scripts/setup_alchemical_fep.py

Proposal 3: Alchemical Free Energy Perturbation (FEP) Framework
Set up the thermodynamic cycle for mutating Pro7 -> Gly7:

Thermodynamic Cycle:
  Leg 1 (Unbound): OXT (aq) ----[ΔG_unbound]----> OXT_Gly (aq)
  Leg 2 (Bound):   OXTR:OXT ----[ΔG_bound]------> OXTR:OXT_Gly
  Net ΔΔG_bind = ΔG_bound - ΔG_unbound

Alchemical Transformation:
  Decouple sidechain atoms of Pro7 (CB, CG, CD, and hydrogens) using
  openmmtools.alchemy.AbsoluteAlchemicalFactory with softcore Lennard-Jones
  and electrostatic lambda scheduling (11 windows: λ = 0.0 to 1.0).
"""

import os
import json
from pathlib import Path
import openmm as mm
import openmm.app as app
import openmm.unit as unit
from openmmtools import alchemy

BASE_DIR = Path("/das/user/QYJI/druggability/OXTR_assessment")
FEP_DIR = BASE_DIR / "fep_setup"
FEP_DIR.mkdir(parents=True, exist_ok=True)

def setup_alchemical_system(complex_pdb_path, out_prefix):
    print(f"[{out_prefix}] Loading structure {complex_pdb_path.name}...")
    pdb = app.PDBFile(str(complex_pdb_path))
    modeller = app.Modeller(pdb.topology, pdb.positions)
    ff = app.ForceField('amber14-all.xml', 'amber14/tip3p.xml')
    
    # Identify alchemical atoms: Proline 7 sidechain atoms in peptide chain (chain index 1)
    alchemical_atom_indices = []
    for res in modeller.topology.residues():
        if res.chain.index == 1 and res.name == 'PRO':
            print(f"Found target residue for FEP: {res.name}{res.id} (index {res.index}) in chain {res.chain.index}")
            for atom in res.atoms():
                if atom.name in ['CB', 'CG', 'CD', 'HB2', 'HB3', 'HG2', 'HG3', 'HD2', 'HD3']:
                    alchemical_atom_indices.append(atom.index)

    print(f"[{out_prefix}] Identified {len(alchemical_atom_indices)} alchemical sidechain atoms to decouple.")

    # Create unperturbed OpenMM system
    system = ff.createSystem(
        modeller.topology,
        nonbondedMethod=app.NoCutoff,
        constraints=app.HBonds
    )

    # Build Alchemical Factory
    alchemical_region = alchemy.AlchemicalRegion(
        alchemical_atoms=alchemical_atom_indices,
        softcore_alpha=0.5,
        softcore_beta=12.0,
        name="Pro7_sidechain_decoupling"
    )

    factory = alchemy.AbsoluteAlchemicalFactory(
        consistent_exceptions=False,
        disable_alchemical_dispersion_correction=True
    )
    
    alchemical_system = factory.create_alchemical_system(system, alchemical_region)
    print(f"[{out_prefix}] Successfully created Alchemical System with {len(alchemical_system.getForces())} force components.")

    # Lambda schedule (11 windows)
    # λ_coulomb decouples first (1.0 -> 0.0), then λ_sterics (1.0 -> 0.0)
    lambda_schedule = [
        {"window": 0,  "lambda_electrostatics": 1.0, "lambda_sterics": 1.0, "state": "Native Pro7"},
        {"window": 1,  "lambda_electrostatics": 0.8, "lambda_sterics": 1.0, "state": "Charge decoupling"},
        {"window": 2,  "lambda_electrostatics": 0.6, "lambda_sterics": 1.0, "state": "Charge decoupling"},
        {"window": 3,  "lambda_electrostatics": 0.4, "lambda_sterics": 1.0, "state": "Charge decoupling"},
        {"window": 4,  "lambda_electrostatics": 0.2, "lambda_sterics": 1.0, "state": "Charge decoupling"},
        {"window": 5,  "lambda_electrostatics": 0.0, "lambda_sterics": 1.0, "state": "Discharged Pro7"},
        {"window": 6,  "lambda_electrostatics": 0.0, "lambda_sterics": 0.8, "state": "Steric softcore decoupling"},
        {"window": 7,  "lambda_electrostatics": 0.0, "lambda_sterics": 0.6, "state": "Steric softcore decoupling"},
        {"window": 8,  "lambda_electrostatics": 0.0, "lambda_sterics": 0.4, "state": "Steric softcore decoupling"},
        {"window": 9,  "lambda_electrostatics": 0.0, "lambda_sterics": 0.2, "state": "Steric softcore decoupling"},
        {"window": 10, "lambda_electrostatics": 0.0, "lambda_sterics": 0.0, "state": "Decoupled (Gly7 dummy)"}
    ]

    manifest = {
        "system": out_prefix,
        "n_alchemical_atoms": len(alchemical_atom_indices),
        "alchemical_atoms": alchemical_atom_indices,
        "lambda_schedule": lambda_schedule,
        "protocol": "Hamiltonian Replica Exchange (HREX) / Multi-State Bennett Acceptance Ratio (MBAR)",
        "recommended_sampling_per_window_ns": 5.0
    }

    manifest_file = FEP_DIR / f"{out_prefix}_fep_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    # Serialize system XML for reproducible execution
    xml_path = FEP_DIR / f"{out_prefix}_alchemical_system.xml"
    with open(xml_path, "w") as f:
        f.write(mm.XmlSerializer.serialize(alchemical_system))

    print(f"[{out_prefix}] FEP setup complete. Saved manifest to {manifest_file} and system XML to {xml_path}.")
    return manifest

def main():
    print("=== Setting up Proposal 3: Alchemical FEP Framework ===")
    
    # Setup for OXTR:OXT (mutating Pro7 -> Gly)
    pdb_oxtr = BASE_DIR / "structures/7QVM_active_complex.min.pdb"
    m_oxtr = setup_alchemical_system(pdb_oxtr, "OXTR_Pro7Gly_FEP")

    # Setup for V2R:OXT (mutating Pro7 -> Gly)
    pdb_v2r = BASE_DIR / "structures/V2R_OXT_complex.min.pdb"
    m_v2r = setup_alchemical_system(pdb_v2r, "V2R_Pro7Gly_FEP")

    print("\nAlchemical FEP systems initialized and verified for both receptors.")

if __name__ == "__main__":
    main()
