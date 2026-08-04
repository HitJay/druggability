#!/usr/bin/env python3
"""Diagnose the AZ1/8Z87 positive-score result: find the specific close contacts
(steric clashes) between the AZ1 top pose and the receptor, and compare against
the AZ1/8Z8A converged low-energy pose for contrast."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'data/gpr81_phase1'
P2 = P / 'phase2_prepared'
P3MS = P / 'phase3_multiseed'

VDW_RADII = {'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80, 'CL': 1.75, 'H': 1.20}


def pdb_atoms(path, is_pdbqt=False):
    atoms = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(('ATOM', 'HETATM')):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el == 'H':
                    continue
                atoms.append({
                    'name': line[12:16].strip(), 'resname': line[17:20].strip(),
                    'resnum': int(line[22:26]),
                    'xyz': np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
                    'element': el,
                })
            except (ValueError, IndexError):
                continue
    return atoms


def first_model_atoms(pdbqt_path):
    lines = Path(pdbqt_path).read_text().splitlines()
    out = []
    for line in lines:
        if line.startswith('ENDMDL'):
            break
        if line.startswith(('ATOM', 'HETATM')):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el == 'H':
                    continue
                out.append({'xyz': np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]), 'element': el})
            except (ValueError, IndexError):
                continue
    return out


def analyze_clashes(receptor_atoms, ligand_atoms, clash_threshold_ratio=0.75):
    """Report contacts closer than clash_threshold_ratio * sum(vdw radii)."""
    clashes = []
    close_contacts = []
    for la in ligand_atoms:
        lr = VDW_RADII.get(la['element'], 1.7)
        for ra in receptor_atoms:
            rr = VDW_RADII.get(ra['element'], 1.7)
            d = float(np.linalg.norm(la['xyz'] - ra['xyz']))
            sum_vdw = lr + rr
            if d < sum_vdw * clash_threshold_ratio:
                clashes.append({'residue': f"{ra['resname']}{ra['resnum']}", 'atom': ra['name'],
                                 'ligand_element': la['element'], 'distance_A': round(d, 2),
                                 'sum_vdw_A': round(sum_vdw, 2), 'severity': round(sum_vdw - d, 2)})
            elif d < sum_vdw * 1.1:
                close_contacts.append({'residue': f"{ra['resname']}{ra['resnum']}", 'distance_A': round(d, 2)})
    return sorted(clashes, key=lambda x: -x['severity']), close_contacts


def main():
    p2 = json.loads((P2 / 'phase2_manifest.json').read_text())
    results = {}

    # Case 1: AZ1 on 8Z87 (the positive-score clash case)
    r8z87 = next(x for x in p2['structures'] if x['pdb_id'] == '8Z87')
    receptor_atoms_8z87 = pdb_atoms(r8z87['receptor_pdb'])
    az1_8z87_pose = first_model_atoms(P3MS / 'poses' / 'AZ1_GPR81_agonist_2_8Z87_seed20260803.pdbqt')
    clashes_8z87, close_8z87 = analyze_clashes(receptor_atoms_8z87, az1_8z87_pose)

    # Case 2: AZ1 on 8Z8A (the converged favorable pose, for contrast)
    r8z8a = next(x for x in p2['structures'] if x['pdb_id'] == '8Z8A')
    receptor_atoms_8z8a = pdb_atoms(r8z8a['receptor_pdb'])
    az1_8z8a_pose = first_model_atoms(P3MS / 'poses' / 'AZ1_GPR81_agonist_2_8Z8A_seed20260803.pdbqt')
    clashes_8z8a, close_8z8a = analyze_clashes(receptor_atoms_8z8a, az1_8z8a_pose)

    # Case 3: Takeda compound on 8Z8A (the strongest convergent result)
    takeda_8z8a_pose = first_model_atoms(P3MS / 'poses' / 'GPR81_agonist_1_8Z8A_seed20260803.pdbqt')
    clashes_takeda, close_takeda = analyze_clashes(receptor_atoms_8z8a, takeda_8z8a_pose)

    results = {
        'AZ1_8Z87_clash_case': {
            'n_clash_contacts': len(clashes_8z87), 'n_close_contacts': len(close_8z87),
            'worst_clashes': clashes_8z87[:10],
            'ligand_heavy_atoms': len(az1_8z87_pose),
            'residues_involved': sorted(set(c['residue'] for c in clashes_8z87)),
        },
        'AZ1_8Z8A_favorable_case': {
            'n_clash_contacts': len(clashes_8z8a), 'n_close_contacts': len(close_8z8a),
            'worst_clashes': clashes_8z8a[:5],
            'residues_in_close_contact': sorted(set(c['residue'] for c in close_8z8a))[:15],
        },
        'Takeda_8Z8A_favorable_case': {
            'n_clash_contacts': len(clashes_takeda), 'n_close_contacts': len(close_takeda),
            'worst_clashes': clashes_takeda[:5],
            'residues_in_close_contact': sorted(set(c['residue'] for c in close_takeda))[:15],
        },
    }
    (P3MS / 'clash_diagnosis.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
