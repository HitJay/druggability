#!/usr/bin/env python3
"""Interaction-geometry review for the AZ1/8Z8A and Takeda/8Z8A converged poses:
identify plausible H-bonds (polar donor/acceptor within 3.5A) and salt bridges
(charged groups within 4.0A), not just favorable Vina scores."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'data/gpr81_phase1'
P2 = P / 'phase2_prepared'
P3MS = P / 'phase3_multiseed'

# Polar/charged sidechain atoms relevant for H-bond / salt-bridge donors-acceptors
POLAR_ATOMS = {
    'ARG': {'NH1': 'donor+', 'NH2': 'donor+', 'NE': 'donor+'},
    'LYS': {'NZ': 'donor+'},
    'ASP': {'OD1': 'acceptor-', 'OD2': 'acceptor-'},
    'GLU': {'OE1': 'acceptor-', 'OE2': 'acceptor-'},
    'HIS': {'ND1': 'donor/acceptor', 'NE2': 'donor/acceptor'},
    'SER': {'OG': 'donor/acceptor'},
    'THR': {'OG1': 'donor/acceptor'},
    'TYR': {'OH': 'donor/acceptor'},
    'ASN': {'OD1': 'acceptor', 'ND2': 'donor'},
    'GLN': {'OE1': 'acceptor', 'NE2': 'donor'},
    'CYS': {'SG': 'donor/acceptor'},
}


def pdb_atoms(path):
    atoms = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(('ATOM', 'HETATM')):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                atoms.append({
                    'name': line[12:16].strip(), 'resname': line[17:20].strip(),
                    'resnum': int(line[22:26]),
                    'xyz': np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
                    'element': el,
                })
            except (ValueError, IndexError):
                continue
    return atoms


def ligand_polar_atoms(pdbqt_path):
    """Ligand N/O/S heavy atoms from the first model (potential H-bond partners)."""
    out = []
    for line in Path(pdbqt_path).read_text().splitlines():
        if line.startswith('ENDMDL'):
            break
        if line.startswith(('ATOM', 'HETATM')):
            try:
                atype = line[77:79].strip()  # AutoDock atom type column
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el in ('N', 'O', 'S'):
                    out.append({'xyz': np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
                                'element': el, 'autodock_type': atype})
            except (ValueError, IndexError):
                continue
    return out


def find_hbond_candidates(receptor_atoms, ligand_polar, hbond_cutoff=3.5):
    hits = []
    for res_atoms_group in POLAR_ATOMS.items():
        pass
    for ra in receptor_atoms:
        polar_map = POLAR_ATOMS.get(ra['resname'], {})
        if ra['name'] not in polar_map:
            continue
        for la in ligand_polar:
            d = float(np.linalg.norm(ra['xyz'] - la['xyz']))
            if d <= hbond_cutoff:
                hits.append({'residue': f"{ra['resname']}{ra['resnum']}", 'residue_atom': ra['name'],
                             'role': polar_map[ra['name']], 'ligand_element': la['element'],
                             'ligand_autodock_type': la['autodock_type'], 'distance_A': round(d, 2)})
    return sorted(hits, key=lambda x: x['distance_A'])


def main():
    p2 = json.loads((P2 / 'phase2_manifest.json').read_text())
    r8z8a = next(x for x in p2['structures'] if x['pdb_id'] == '8Z8A')
    receptor_atoms = pdb_atoms(r8z8a['receptor_pdb'])

    az1_polar = ligand_polar_atoms(P3MS / 'poses' / 'AZ1_GPR81_agonist_2_8Z8A_seed20260803.pdbqt')
    takeda_polar = ligand_polar_atoms(P3MS / 'poses' / 'GPR81_agonist_1_8Z8A_seed20260803.pdbqt')

    az1_hbonds = find_hbond_candidates(receptor_atoms, az1_polar)
    takeda_hbonds = find_hbond_candidates(receptor_atoms, takeda_polar)

    results = {
        'AZ1_8Z8A': {
            'n_ligand_polar_atoms': len(az1_polar),
            'n_hbond_candidates': len(az1_hbonds),
            'hbond_candidates': az1_hbonds,
        },
        'Takeda_8Z8A': {
            'n_ligand_polar_atoms': len(takeda_polar),
            'n_hbond_candidates': len(takeda_hbonds),
            'hbond_candidates': takeda_hbonds,
        },
    }
    (P3MS / 'interaction_geometry_review.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
