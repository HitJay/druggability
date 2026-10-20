"""Prepare FEP-A inputs per perses PointMutationExecutor design:
protein-only PDB (pocket chain, no ligand) + ligand as separate .pdb (ligand_input).
"""
import numpy as np
import os

base = "/das/user/QYJI/druggability/TSPO_assessment/output/docking"
D = "/das/user/QYJI/druggability/TSPO_assessment/output/fep_a/inputs"
os.makedirs(D, exist_ok=True)


def split_holo(src, prot_dst, lig_dst):
    prot, lig = [], []
    for l in open(src):
        if l.startswith(("ATOM", "HETATM")):
            if l[17:20].strip() in ("UNL", "LIG"):
                lig.append(l)
            else:
                prot.append(l)
        elif l.startswith("END"):
            prot.append("END\n")
            lig.append("END\n")
            break
    open(prot_dst, "w").writelines(prot)
    open(lig_dst, "w").writelines(lig)
    print(f"{src.split('/')[-1]} -> {prot_dst.split('/')[-1]} ({sum(1 for x in prot if x.startswith('ATOM'))} prot atoms) + {lig_dst.split('/')[-1]} ({len(lig)} lines)")


# emapunil holo complexes (chain already trimmed)
for pdb, chain in [("4RYI", "A"), ("6X3X", "B"), ("4DKL", "A"), ("1XVP", "A"), ("4XAQ", "A")]:
    src = {"6X3X": f"{base}/f4_6X3X_Bonly.pdb"}.get(pdb, f"{base}/f4_{pdb}_relaxed.pdb")
    split_holo(src, f"{D}/{pdb}_emapunil_protein.pdb", f"{D}/{pdb}_emapunil_lig.pdb")

# fgin holo complexes
for pdb in ["4RYI", "1XVP", "5TGZ", "4DJH", "4XAQ"]:
    src = f"{base}/f4_{pdb}_fgin_relaxed.pdb"
    split_holo(src, f"{D}/{pdb}_fgin_protein.pdb", f"{D}/{pdb}_fgin_lig.pdb")

# apo inputs = protein-only PDB (from rec_fixed, pocket chain)
for pdb, chain in [("4RYI", "A"), ("6X3X", "B"), ("4DKL", "A"), ("1XVP", "A"), ("4XAQ", "A"),
                   ("5TGZ", "A"), ("4DJH", "A")]:
    keep = [l for l in open(f"{base}/f2_{pdb}_rec_fixed.pdb")
            if (l.startswith(("ATOM", "HETATM")) and l[21] == chain) or l.startswith("END")]
    open(f"{D}/{pdb}_apo_protein.pdb", "w").writelines(keep)
print("apo protein inputs written")
