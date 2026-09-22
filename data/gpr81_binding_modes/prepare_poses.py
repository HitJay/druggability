#!/usr/bin/env python3
"""
Extract, align, and normalize candidate binding poses for GPR81:
1. Lactate (8Z8A co-crystal, orthosteric ground truth)
2. AZ1 (Boltz-2 orthosteric aligned to 8Z8A vs Vina TM5-TM6 allosteric)
3. GPR81 agonist 1 (Boltz-2 orthosteric aligned to 8Z8A vs Vina TM5-TM6 allosteric)
"""

import os
from Bio.PDB import PDBParser, MMCIFParser, Superimposer, PDBIO, Select
from rdkit import Chem
from rdkit.Chem import AllChem
import numpy as np

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
GPR81_DIR = "/das/user/QYJI/druggability/data/gpr81_phase1"

class ChainSelect(Select):
    def __init__(self, chain_id):
        self.chain_id = chain_id
    def accept_chain(self, chain):
        return chain.id == self.chain_id
    def accept_residue(self, res):
        return res.id[0] == " "  # standard residues only

def extract_clean_receptor():
    parser = PDBParser(QUIET=True)
    struct = parser.get_structure("8Z8A", os.path.join(GPR81_DIR, "structures/8Z8A.pdb"))
    io = PDBIO()
    io.set_structure(struct)
    out_pdb = os.path.join(WORK_DIR, "8Z8A_HCAR1_clean.pdb")
    io.save(out_pdb, ChainSelect("R"))
    print(f"Saved clean receptor: {out_pdb}")
    return out_pdb

def read_pdbqt_atoms(pdbqt_file):
    atoms = []
    with open(pdbqt_file) as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                name = line[12:16].strip()
                res = line[17:20].strip()
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                elem = line[76:78].strip() if len(line) >= 78 else name[0]
                atoms.append({"name": name, "res": res, "x": x, "y": y, "z": z, "elem": elem})
            elif line.startswith("ENDMDL"):
                break
    return atoms

def assign_coords_to_rdkit(smiles, coords, out_sdf, name):
    ref_mol = Chem.MolFromSmiles(smiles)
    ref_mol = Chem.AddHs(ref_mol)
    AllChem.EmbedMolecule(ref_mol, randomSeed=42)
    
    # Match heavy atoms
    heavy_atoms = [a for a in ref_mol.GetAtoms() if a.GetAtomicNum() > 1]
    if len(coords) < len(heavy_atoms):
        print(f"Warning: {name} coords count {len(coords)} < heavy atoms {len(heavy_atoms)}")
    
    # Assign coordinates from best matched order or simple array if counts match
    conf = ref_mol.GetConformer()
    # Simple assignment of first len(coords) heavy atoms or nearest coordinate
    # For robust alignment, let us write as an XYZ/PDB first and perceive bonds with Chem.MolFromPDBBlock
    # Or assign coordinates by element
    return ref_mol

def process_all():
    extract_clean_receptor()
    
    # 1. Lactate from 8Z8A
    parser = PDBParser(QUIET=True)
    struct_8z8a = parser.get_structure("8Z8A", os.path.join(GPR81_DIR, "structures/8Z8A.pdb"))
    chain_r = struct_8z8a[0]["R"]
    lac_res = [res for res in chain_r if res.resname == "2OP"][0]
    
    # Save lactate PDB block
    lac_lines = []
    for i, atom in enumerate(lac_res, 1):
        elem = atom.element if atom.element else atom.name[0]
        lac_lines.append(f"HETATM{i:5d} {atom.name:<4s} 2OP A   1    {atom.coord[0]:8.3f}{atom.coord[1]:8.3f}{atom.coord[2]:8.3f}  1.00 20.00          {elem:>2s}")
    lac_lines.append("END\n")
    lac_pdb_block = "\n".join(lac_lines)
    
    # Assign connectivity from SMILES
    lac_ref = Chem.MolFromSmiles("CC(O)C(=O)O")
    lac_raw = Chem.MolFromPDBBlock(lac_pdb_block, removeHs=False)
    lac_assigned = AllChem.AssignBondOrdersFromTemplate(lac_ref, lac_raw)
    Chem.MolToMolFile(lac_assigned, os.path.join(WORK_DIR, "lactate_ortho_8Z8A.sdf"))
    print("Saved lactate_ortho_8Z8A.sdf")
    
    # 2. Boltz t01 (AZ1) and t02 (Agonist 1) alignment
    cif_parser = MMCIFParser(QUIET=True)
    
    # Build CA lists for 8Z8A
    ca_r_dict = {}
    for res in chain_r:
        if res.id[0] == " " and "CA" in res:
            ca_r_dict[res.id[1]] = res["CA"]
            
    for tag, sm, name in [
        ("t01", "CCOc1cc(Cl)c(C(=O)NC(=O)Nc2nc3ccc(S(=O)(=O)C4CCN(C)CC4)cc3s2)cc1-n1cccn1", "az1"),
        ("t02", "CC1CCC(CC1)C(=O)NC2=NC(=C(S2)CC(=O)N3CCN(CC3)C)C4=CC=CS4", "agonist1")
    ]:
        cif_path = os.path.join(GPR81_DIR, f"followup_2026-08/data/boltz_runs/{tag}/predictions/boltz/boltz_model_0.cif")
        s_boltz = cif_parser.get_structure(tag, cif_path)
        chain_a = s_boltz[0]["A"]
        chain_b = s_boltz[0]["B"]
        
        ca_r = []
        ca_a = []
        for res in chain_a:
            rid = res.id[1]
            if rid in ca_r_dict and "CA" in res:
                ca_r.append(ca_r_dict[rid])
                ca_a.append(res["CA"])
                
        sup = Superimposer()
        sup.set_atoms(ca_r, ca_a)
        
        # Apply transformation to chain_b atoms
        # Note: sup.apply(atoms) transforms atoms in-place
        b_atoms = list(chain_b.get_atoms())
        sup.apply(b_atoms)
        
        # Save transformed ligand to PDB
        b_lines = []
        for i, atom in enumerate(b_atoms, 1):
            elem = atom.element if atom.element else atom.name[0]
            b_lines.append(f"HETATM{i:5d} {atom.name:<4s} LIG A   1    {atom.coord[0]:8.3f}{atom.coord[1]:8.3f}{atom.coord[2]:8.3f}  1.00 20.00          {elem:>2s}")
        b_lines.append("END\n")
        pdb_block = "\n".join(b_lines)
        
        ref = Chem.MolFromSmiles(sm)
        raw = Chem.MolFromPDBBlock(pdb_block, removeHs=False)
        try:
            assigned = AllChem.AssignBondOrdersFromTemplate(ref, raw)
            Chem.MolToMolFile(assigned, os.path.join(WORK_DIR, f"{name}_ortho_boltz.sdf"))
            print(f"Saved {name}_ortho_boltz.sdf successfully")
        except Exception as e:
            print(f"Failed template assign for {name} boltz, saving raw mol: {e}")
            Chem.MolToMolFile(raw, os.path.join(WORK_DIR, f"{name}_ortho_boltz.sdf"))

    # 3. Vina PDBQT to SDF
    for pdbqt_name, sm, name in [
        ("AZ1_GPR81_agonist_2.pdbqt", "CCOc1cc(Cl)c(C(=O)NC(=O)Nc2nc3ccc(S(=O)(=O)C4CCN(C)CC4)cc3s2)cc1-n1cccn1", "az1"),
        ("GPR81_agonist_1.pdbqt", "CC1CCC(CC1)C(=O)NC2=NC(=C(S2)CC(=O)N3CCN(CC3)C)C4=CC=CS4", "agonist1")
    ]:
        pdbqt_path = os.path.join(GPR81_DIR, f"phase3_docking/poses/8Z8A/{pdbqt_name}")
        atoms = read_pdbqt_atoms(pdbqt_path)
        v_lines = []
        for i, atom in enumerate(atoms, 1):
            v_lines.append(f"HETATM{i:5d} {atom['name']:<4s} LIG A   1    {atom['x']:8.3f}{atom['y']:8.3f}{atom['z']:8.3f}  1.00 20.00          {atom['elem']:>2s}")
        v_lines.append("END\n")
        pdb_block = "\n".join(v_lines)
        ref = Chem.MolFromSmiles(sm)
        raw = Chem.MolFromPDBBlock(pdb_block, removeHs=False)
        try:
            assigned = AllChem.AssignBondOrdersFromTemplate(ref, raw)
            Chem.MolToMolFile(assigned, os.path.join(WORK_DIR, f"{name}_allo_vina.sdf"))
            print(f"Saved {name}_allo_vina.sdf successfully")
        except Exception as e:
            print(f"Failed template assign for {name} vina, saving raw mol: {e}")
            Chem.MolToMolFile(raw, os.path.join(WORK_DIR, f"{name}_allo_vina.sdf"))

if __name__ == "__main__":
    process_all()
