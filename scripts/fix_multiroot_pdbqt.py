#!/usr/bin/env python3
"""Fix PDBQT files with multiple ROOT sections — properly split by molecule."""
import os

LIG = "/das/user/QYJI/druggability/output/2026-07-10/ghsr_inverse_agonist_docking/ligands"
D7  = "/das/user/QYJI/druggability/output/2026-07-10/ghsr_inverse_agonist_docking/docked_7F83"

done = set(f.replace('_out.pdbqt','') for f in os.listdir(D7) if f.endswith('_out.pdbqt'))
all_lig = sorted(f.replace('.pdbqt','') for f in os.listdir(LIG) if f.endswith('.pdbqt'))
missing = [c for c in all_lig if c not in done]

def split_molecules(lines):
    mols = []
    i = 0
    while i < len(lines):
        l = lines[i].strip()
        if l == "ROOT":
            start = i; i += 1
            while i < len(lines) and lines[i].strip() != "ENDROOT":
                i += 1
            if i < len(lines):
                i += 1  # skip ENDROOT
            # Collect following BRANCH/ENDBRANCH blocks
            while i < len(lines) and (lines[i].strip().startswith("BRANCH") or lines[i].strip().startswith("ENDBRANCH")):
                # Walk to matching ENDBRANCH if it's a BRANCH
                if lines[i].strip().startswith("BRANCH"):
                    depth = 1
                    i += 1
                    while i < len(lines) and depth > 0:
                        s = lines[i].strip()
                        if s.startswith("BRANCH") and not s.startswith("ENDBRANCH"):
                            depth += 1
                        elif s.startswith("ENDBRANCH"):
                            depth -= 1
                        i += 1
                else:
                    i += 1
            end = i
            text = '\n'.join(lines[start:end])
            n_atoms = sum(1 for l in text.split('\n') if l.startswith("ATOM"))
            # Count torsions: count BRANCH lines (not ENDBRANCH)
            n_tors = sum(1 for l in text.split('\n') if l.strip().startswith("BRANCH ") 
                         and not l.strip().startswith("ENDBRANCH"))
            mols.append((n_atoms, n_tors, text))
        else:
            i += 1
    return mols

fixed = 0
for cid in missing:
    path = os.path.join(LIG, cid+'.pdbqt')
    with open(path) as f:
        lines = f.read().strip().split('\n')
    # Check if already single molecule
    root_count = sum(1 for l in lines if l.strip() == "ROOT")
    if root_count <= 1:
        continue
    
    mols = split_molecules(lines)
    if len(mols) < 2:
        continue
    # Keep the largest molecule by atom count
    best = max(mols, key=lambda m: m[0])
    best_text = best[2]
    n_tors = best[1]
    # Append TORSDOF if not present
    if not best_text.strip().endswith(f"TORSDOF {n_tors}"):
        best_text = best_text.rstrip() + f"\nTORSDOF {n_tors}\n"
    with open(path, 'w') as f:
        f.write(best_text)
    fixed += 1
    if fixed <= 3:
        print(f'{cid}: kept {best[0]} atoms, {n_tors} torsions')

print(f'\nFixed {fixed} multi-root ligand files')
