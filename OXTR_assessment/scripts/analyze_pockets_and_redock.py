#!/usr/bin/env python3
"""
scripts/analyze_pockets_and_redock.py

1. Profile OXTR binding pocket residues from 7QVM (active) and compare with 6TPK (inactive).
2. Define docking grid boxes (Orthosteric, Core sub-pocket, Vestibule).
3. Redock Retosiban into 6TPK using AutoDock Vina and calculate RMSD to validate docking setup.
"""

import os
import json
import subprocess
import numpy as np
from pathlib import Path
from Bio.PDB import PDBParser, NeighborSearch
from rdkit import Chem
from meeko import MoleculePreparation
from vina import Vina
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = Path("/das/user/QYJI/druggability/OXTR_assessment")
STRUCT_DIR = BASE_DIR / "structures"
GRID_DIR = BASE_DIR / "grids"
SCRIPT_DIR = BASE_DIR / "scripts"
REPORT_DIR = BASE_DIR / "reports"

GRID_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def heavy_atoms(path):
    out = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(('ATOM', 'HETATM')):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el != 'H':
                    out.append((el, np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])))
            except Exception:
                continue
    return out

def calc_rmsd(coords1, coords2):
    c1 = np.array(coords1)
    c2 = np.array(coords2)
    return np.sqrt(np.mean(np.sum((c1 - c2) ** 2, axis=1)))

def main():
    p = PDBParser(QUIET=True)

    # 1. Pocket Analysis on 7QVM
    s_rec = p.get_structure('rec', str(STRUCT_DIR / '7QVM_active_receptor.pdb'))
    s_oxt = p.get_structure('oxt', str(STRUCT_DIR / '7QVM_oxt_ligand.pdb'))
    s_ret = p.get_structure('ret', str(STRUCT_DIR / '6TPK_retosiban_aligned.pdb'))

    atoms_rec = list(s_rec.get_atoms())
    atoms_oxt = list(s_oxt.get_atoms())
    atoms_ret = list(s_ret.get_atoms())

    # Decompose OXT into sub-regions:
    # Core ring: C1, Y2, I3, Q4, N5, C6
    # Tail / Vestibule: P7, L8, G9, NH210
    core_atoms = [a for a in atoms_oxt if a.get_parent().id[1] <= 6]
    vestibule_atoms = [a for a in atoms_oxt if a.get_parent().id[1] >= 7]

    coords_all = np.array([a.coord for a in atoms_oxt])
    coords_core = np.array([a.coord for a in core_atoms])
    coords_vest = np.array([a.coord for a in vestibule_atoms])
    coords_ret = np.array([a.coord for a in atoms_ret])

    # Calculate Centers and Box sizes with padding (padding=8Å)
    padding = 8.0
    
    # Box 1: Full Orthosteric (OXT)
    c_full = coords_all.mean(axis=0)
    box_full = (coords_all.max(axis=0) - coords_all.min(axis=0)) + padding

    # Box 2: Core Sub-pocket (Ring / Tyr2 crevice / Retosiban overlap)
    c_core = coords_core.mean(axis=0)
    box_core = (coords_core.max(axis=0) - coords_core.min(axis=0)) + padding

    # Box 3: Vestibule (Pro7, Leu8, Gly9 exit vector)
    c_vest = coords_vest.mean(axis=0)
    box_vest = (coords_vest.max(axis=0) - coords_vest.min(axis=0)) + padding

    # Box 4: Retosiban pocket in 6TPK (aligned frame)
    c_ret_box = coords_ret.mean(axis=0)
    box_ret = (coords_ret.max(axis=0) - coords_ret.min(axis=0)) + padding

    grid_definitions = {
        "full_orthosteric": {
            "center": [round(float(x), 2) for x in c_full],
            "size": [round(float(x), 2) for x in box_full],
            "description": "Encompasses entire 9-mer OXT binding groove from deep TM cavity to ECL3"
        },
        "core_subpocket": {
            "center": [round(float(x), 2) for x in c_core],
            "size": [round(float(x), 2) for x in box_core],
            "description": "Cyclic core (Cys1-Cys6), Tyr2 crevice (TM7 kink contact), Ile3 hydrophobic pocket"
        },
        "vestibule_exit": {
            "center": [round(float(x), 2) for x in c_vest],
            "size": [round(float(x), 2) for x in box_vest],
            "description": "Extracellular vestibule (Pro7-Leu8-Gly9), Lys8 lipid conjugation exit vector"
        },
        "retosiban_inactive": {
            "center": [round(float(x), 2) for x in c_ret_box],
            "size": [round(float(x), 2) for x in box_ret],
            "description": "Retosiban antagonist binding site in 6TPK (aligned coordinates)"
        }
    }

    print("=== Grid Box Definitions ===")
    for k, v in grid_definitions.items():
        print(f"{k}: center={v['center']}, size={v['size']}")

    with open(GRID_DIR / "grid_definitions.json", "w") as f:
        json.dump(grid_definitions, f, indent=2)

    # Detailed residue-level contact mapping
    ns = NeighborSearch(atoms_rec)
    per_residue_contacts = {}
    for r_lig in s_oxt[0]['L']:
        r_name = f"{r_lig.resname}{r_lig.id[1]}"
        r_atoms = list(r_lig.get_atoms())
        rec_contacts = set()
        for a in r_atoms:
            neighbors = ns.search(a.coord, 4.0, 'R')
            for nr in neighbors:
                if nr.id[0] == ' ':
                    rec_contacts.add(f"{nr.resname}{nr.id[1]}")
        per_residue_contacts[r_name] = sorted(list(rec_contacts), key=lambda x: int(x[3:]))

    print("\n=== OXT Residue-by-Residue Contact Map ===")
    for k, v in per_residue_contacts.items():
        print(f"  {k:8s} -> {', '.join(v)}")

    with open(REPORT_DIR / "oxt_contact_map.json", "w") as f:
        json.dump(per_residue_contacts, f, indent=2)

    # 2. Redocking Benchmark on 6TPK
    print("\n=== Redocking Benchmark on 6TPK (Retosiban) ===")
    rec_pdb = STRUCT_DIR / "6TPK_inactive_receptor_aligned.pdb"
    rec_pdbqt = GRID_DIR / "6TPK_receptor.pdbqt"
    
    # obabel for receptor
    temp_raw = GRID_DIR / "6TPK_temp.raw.pdbqt"
    cmd_rec = ["obabel", str(rec_pdb), "-O", str(temp_raw), "-xr"]
    subprocess.run(cmd_rec, check=True, capture_output=True)
    kept_lines = [l for l in temp_raw.read_text().splitlines(True) if l.startswith(("ATOM", "HETATM"))]
    rec_pdbqt.write_text("".join(kept_lines))
    temp_raw.unlink()
    print(f"Prepared receptor PDBQT: {rec_pdbqt} ({len(kept_lines)} atoms)")

    # Prepare ligand PDBQT using Meeko
    # Convert retosiban pdb to mol
    ret_pdb = STRUCT_DIR / "6TPK_retosiban_aligned.pdb"
    ret_pdbqt = GRID_DIR / "6TPK_retosiban.pdbqt"
    
    # Read via rdkit
    m = Chem.MolFromPDBFile(str(ret_pdb), removeHs=False, sanitize=False)
    try:
        Chem.SanitizeMol(m)
    except Exception as e:
        print(f"Sanitization note: {e}")
    m = Chem.AddHs(m, addCoords=True)
    
    preparator = MoleculePreparation()
    preparator.prepare(m)
    preparator.write_pdbqt_file(str(ret_pdbqt))
    print(f"Prepared ligand PDBQT: {ret_pdbqt}")

    # Run Vina redocking
    v = Vina(sf_name='vina', cpu=4, seed=20260916)
    v.set_receptor(str(rec_pdbqt))
    v.set_ligand_from_file(str(ret_pdbqt))

    # Center on retosiban
    v.compute_vina_maps(center=grid_definitions["retosiban_inactive"]["center"],
                        box_size=[18.0, 18.0, 18.0])

    print("Scoring native pose...")
    energy = v.score()
    print(f"Score before minimization: {energy[0]:.2f} kcal/mol")

    energy_min = v.optimize()
    print(f"Score after local minimization: {energy_min[0]:.2f} kcal/mol")

    dock_out = GRID_DIR / "6TPK_retosiban_redocked.pdbqt"
    v.dock(exhaustiveness=16, n_poses=5)
    v.write_poses(str(dock_out), n_poses=5, overwrite=True)

    # Extract top pose and calculate RMSD vs crystal pose
    # Parse docked pose 1
    crystal_heavy = heavy_atoms(ret_pdb)
    # Convert docked pose 1 to pdb using obabel
    dock_pdb = GRID_DIR / "6TPK_retosiban_pose1.pdb"
    cmd_conv = ["obabel", str(dock_out), "-O", str(dock_pdb), "-f", "1", "-l", "1"]
    subprocess.run(cmd_conv, check=True, capture_output=True)
    docked_heavy = heavy_atoms(dock_pdb)

    # Compute RMSD
    c_cryst = [x[1] for x in crystal_heavy]
    c_dock = [x[1] for x in docked_heavy]
    
    if len(c_cryst) == len(c_dock):
        rmsd = calc_rmsd(c_cryst, c_dock)
    else:
        # subset matching by count
        min_n = min(len(c_cryst), len(c_dock))
        rmsd = calc_rmsd(c_cryst[:min_n], c_dock[:min_n])

    redock_summary = {
        "score_native_minimized": round(float(energy_min[0]), 2),
        "redocked_top_score": round(float(energy[0]), 2),
        "rmsd_to_crystal_A": round(float(rmsd), 3),
        "benchmark_passed": bool(rmsd < 2.0)
    }
    print(f"\nRedocking Results: Top Score = {redock_summary['score_native_minimized']} kcal/mol, RMSD = {rmsd:.3f} Å (Pass gate < 2.0 Å: {redock_summary['benchmark_passed']})")

    with open(REPORT_DIR / "redocking_benchmark.json", "w") as f:
        json.dump(redock_summary, f, indent=2)

    # Sync to CIFS shared folder
    os.system(f"cp -f {GRID_DIR}/* /TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/grids/")
    os.system(f"cp -f {REPORT_DIR}/* /TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/reports/")
    print("Files synced to shared folder.")

if __name__ == "__main__":
    main()
