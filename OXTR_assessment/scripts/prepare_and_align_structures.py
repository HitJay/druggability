#!/usr/bin/env python3
"""
scripts/prepare_and_align_structures.py

Extract, clean, standardize and structurally align OXTR structures:
- 7QVM: Active human OXTR bound to Oxytocin (Cryo-EM, 3.25 Å)
- 7RYC: Active human OXTR bound to Oxytocin (Cryo-EM, 2.90 Å)
- 6TPK: Inactive human OXTR bound to Retosiban (X-ray, 3.20 Å)

Coordinates of 6TPK and 7RYC are aligned into the 7QVM reference frame.
"""

import os
import copy
import warnings
import numpy as np
from Bio.PDB import MMCIFParser, PDBParser, Superimposer, PDBIO, Select

warnings.filterwarnings('ignore')

BASE_DIR = "/das/user/QYJI/druggability/OXTR_assessment"
RAW_DIR = os.path.join(BASE_DIR, "raw_pdb")
OUT_DIR = os.path.join(BASE_DIR, "structures")
SHARED_OUT_DIR = "/TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/structures"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SHARED_OUT_DIR, exist_ok=True)

cif_p = MMCIFParser(QUIET=True)
pdb_p = PDBParser(QUIET=True)

class ReceptorSelect(Select):
    def __init__(self, max_res=350):
        self.max_res = max_res
    def accept_residue(self, residue):
        return residue.id[0] == ' ' and residue.id[1] <= self.max_res

class LigandSelect(Select):
    def __init__(self, resname):
        self.resname = resname
    def accept_residue(self, residue):
        return residue.resname == self.resname

class ChainSelect(Select):
    def __init__(self, chain_id):
        self.chain_id = chain_id
    def accept_chain(self, chain):
        return chain.id == self.chain_id

def main():
    print("Loading 7QVM, 7RYC, 6TPK...")
    s_7qvm = cif_p.get_structure('7QVM', os.path.join(RAW_DIR, '7QVM.cif'))
    s_7ryc = cif_p.get_structure('7RYC', os.path.join(RAW_DIR, '7RYC.cif'))
    s_6tpk = pdb_p.get_structure('6TPK', os.path.join(RAW_DIR, '6TPK.pdb'))

    # 1. 7QVM Reference: Chain R (receptor), Chain L (OXT)
    r_7qvm = s_7qvm[0]['R']
    l_7qvm = s_7qvm[0]['L']

    io = PDBIO()

    # Save 7QVM receptor
    io.set_structure(r_7qvm)
    p_7qvm_rec = os.path.join(OUT_DIR, "7QVM_active_receptor.pdb")
    io.save(p_7qvm_rec, select=ReceptorSelect(350))
    print(f"Saved: {p_7qvm_rec}")

    # Save 7QVM OXT ligand
    io.set_structure(l_7qvm)
    p_7qvm_oxt = os.path.join(OUT_DIR, "7QVM_oxt_ligand.pdb")
    io.save(p_7qvm_oxt)
    print(f"Saved: {p_7qvm_oxt}")

    # Save 7QVM combined complex (Receptor R + Ligand L)
    # We can create a model with both chains
    from Bio.PDB.Model import Model
    from Bio.PDB.Structure import Structure
    c_struct = Structure("7QVM_complex")
    c_model = Model(0)
    c_model.add(copy.deepcopy(r_7qvm))
    c_model.add(copy.deepcopy(l_7qvm))
    c_struct.add(c_model)
    io.set_structure(c_struct)
    p_7qvm_complex = os.path.join(OUT_DIR, "7QVM_active_complex.pdb")
    io.save(p_7qvm_complex)
    print(f"Saved: {p_7qvm_complex}")

    # 2. Extract 6TPK receptor (Chain A, res <= 350) and ligand NU2
    r_6tpk = s_6tpk[0]['A']
    
    # Save raw 6TPK ligand NU2
    p_6tpk_nu2_raw = os.path.join(OUT_DIR, "6TPK_retosiban_raw.pdb")
    io.set_structure(r_6tpk)
    io.save(p_6tpk_nu2_raw, select=LigandSelect("NU2"))
    print(f"Saved: {p_6tpk_nu2_raw}")

    # 3. Superimpose 6TPK onto 7QVM
    # Use transmembrane core (TM1-TM4: 38-65, 75-103, 110-145, 155-180)
    core_ranges = [(38, 65), (75, 103), (110, 145), (155, 180)]
    atoms_7qvm = []
    atoms_6tpk = []
    for start, end in core_ranges:
        for resnum in range(start, end + 1):
            if resnum in r_7qvm and resnum in r_6tpk:
                if 'CA' in r_7qvm[resnum] and 'CA' in r_6tpk[resnum]:
                    atoms_7qvm.append(r_7qvm[resnum]['CA'])
                    atoms_6tpk.append(r_6tpk[resnum]['CA'])

    sup = Superimposer()
    sup.set_atoms(atoms_7qvm, atoms_6tpk)
    print(f"6TPK -> 7QVM Core TM1-TM4 RMSD: {sup.rms:.3f} Å ({len(atoms_7qvm)} CAs)")

    # Apply transformation to the entire 6TPK model
    sup.apply(s_6tpk[0].get_atoms())

    # Save aligned 6TPK receptor
    p_6tpk_rec_aln = os.path.join(OUT_DIR, "6TPK_inactive_receptor_aligned.pdb")
    io.set_structure(s_6tpk[0]['A'])
    io.save(p_6tpk_rec_aln, select=ReceptorSelect(350))
    print(f"Saved: {p_6tpk_rec_aln}")

    # Save aligned 6TPK ligand
    p_6tpk_nu2_aln = os.path.join(OUT_DIR, "6TPK_retosiban_aligned.pdb")
    io.set_structure(s_6tpk[0]['A'])
    io.save(p_6tpk_nu2_aln, select=LigandSelect("NU2"))
    print(f"Saved: {p_6tpk_nu2_aln}")

    # 4. Superimpose 7RYC onto 7QVM
    r_7ryc = s_7ryc[0]['O']
    l_7ryc = s_7ryc[0]['L']
    atoms_7qvm_ryc = []
    atoms_7ryc = []
    for start, end in core_ranges:
        for resnum in range(start, end + 1):
            if resnum in r_7qvm and resnum in r_7ryc:
                if 'CA' in r_7qvm[resnum] and 'CA' in r_7ryc[resnum]:
                    atoms_7qvm_ryc.append(r_7qvm[resnum]['CA'])
                    atoms_7ryc.append(r_7ryc[resnum]['CA'])

    sup_ryc = Superimposer()
    sup_ryc.set_atoms(atoms_7qvm_ryc, atoms_7ryc)
    print(f"7RYC -> 7QVM Core TM1-TM4 RMSD: {sup_ryc.rms:.3f} Å ({len(atoms_7qvm_ryc)} CAs)")
    sup_ryc.apply(s_7ryc[0].get_atoms())

    # Save aligned 7RYC receptor
    p_7ryc_rec_aln = os.path.join(OUT_DIR, "7RYC_active_receptor_aligned.pdb")
    io.set_structure(r_7ryc)
    io.save(p_7ryc_rec_aln, select=ReceptorSelect(350))
    print(f"Saved: {p_7ryc_rec_aln}")

    p_7ryc_oxt_aln = os.path.join(OUT_DIR, "7RYC_oxt_ligand_aligned.pdb")
    io.set_structure(l_7ryc)
    io.save(p_7ryc_oxt_aln)
    print(f"Saved: {p_7ryc_oxt_aln}")

    # Sync to CIFS shared directory
    os.system(f"cp -f {OUT_DIR}/*.pdb {SHARED_OUT_DIR}/")
    print(f"Synchronized structures to {SHARED_OUT_DIR}")

if __name__ == "__main__":
    main()
