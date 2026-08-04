#!/usr/bin/env python3
"""Reference-guided (tight-box, multi-seed) redocking control for 3,5-DHBA on 9KT9.

Vina has no native distance-restraint API in this installation, so 'reference-guided'
here means: (1) a tight box centered exactly on the experimental ligand centroid with
minimal padding to constrain the search volume to the known pocket, and (2) multiple
random seeds with high exhaustiveness, selecting the pose with the best centroid
recovery among top-scoring poses. This is reported as a distinct, more constrained
condition -- NOT as proof of the true binding pose.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation
from vina import Vina

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'data/gpr81_phase1'
P2 = P / 'phase2_prepared'
OUT = P / 'phase3_5_controls_restrained'
(OUT / 'poses').mkdir(parents=True, exist_ok=True)

SEEDS = [20260803, 1, 2, 3, 4]
EXHAUSTIVENESS = 32


def atoms(path):
    out = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(('ATOM', 'HETATM')):
            try:
                el = (line[76:78].strip() or line[12:16].strip()[0]).upper()
                if el != 'H':
                    out.append(np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]))
            except (ValueError, IndexError):
                # Locally-written reference-ligand PDBs are minimally formatted and can
                # have non-standard column widths; fall back to whitespace splitting.
                fields = line.split()
                try:
                    el = fields[2].upper(); coord_start = 6
                    if el != 'H':
                        out.append(np.array([float(fields[coord_start]), float(fields[coord_start + 1]), float(fields[coord_start + 2])]))
                except (ValueError, IndexError):
                    continue
    return out


def parse_pose(p):
    lines = p.read_text().splitlines()
    models, cur = [], []
    for l in lines:
        if l.startswith('MODEL') and cur:
            models.append(cur); cur = []
        cur.append(l)
    if cur:
        models.append(cur)
    results = []
    for m in models:
        score = None
        for l in m:
            if l.startswith('REMARK VINA RESULT:'):
                score = float(l.split()[3])
        pose_atoms = []
        for l in m:
            if l.startswith(('ATOM', 'HETATM')):
                try:
                    el = (l[76:78].strip() or l[12:16].strip()[0]).upper()
                    if el != 'H':
                        pose_atoms.append(np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])]))
                except (ValueError, IndexError):
                    continue
        results.append((score, pose_atoms))
    return results


def main():
    p2 = json.loads((P2 / 'phase2_manifest.json').read_text())
    r9kt9 = next(x for x in p2['structures'] if x['pdb_id'] == '9KT9')
    geom = r9kt9['ligand_geometry']
    exp_atoms = atoms(next(P2.joinpath('reference_ligands').glob('9KT9_34D.pdb')))
    exp_centroid = np.mean(exp_atoms, axis=0)

    # Reference-guided/tight box: minimal padding around the experimental ligand span
    # instead of the general-purpose 24A minimum used in the unconstrained P3 box.
    tight_box = [round(max(s + 5.0, 12.0), 3) for s in [3.518, 3.789, 4.839]]

    ligand_pdbqt = P / 'phase3_5_controls/ligands/3_5_DHBA.pdbqt'
    assert ligand_pdbqt.exists(), f"expected prepared ligand at {ligand_pdbqt}"

    rows = []
    all_poses = []
    for seed in SEEDS:
        v = Vina(sf_name='vina', seed=seed)
        v.set_receptor(r9kt9['receptor_pdbqt']['path'])
        v.compute_vina_maps(center=geom['center_A'], box_size=tight_box)
        v.set_ligand_from_file(str(ligand_pdbqt))
        v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=5)
        pose_file = OUT / 'poses' / f'3_5_DHBA_9KT9_seed{seed}.pdbqt'
        v.write_poses(str(pose_file), n_poses=5, overwrite=True)
        for rank, (score, patoms) in enumerate(parse_pose(pose_file), start=1):
            if not patoms:
                continue
            pc = np.mean(patoms, axis=0)
            dist = float(np.linalg.norm(pc - exp_centroid))
            rows.append({'seed': seed, 'pose_rank': rank, 'score_kcal_mol': score,
                         'centroid_distance_A': round(dist, 3), 'box_size_A': tight_box,
                         'pose_file': str(pose_file)})
            all_poses.append((seed, rank, score, dist))

    with (OUT / 'restrained_redocking_results.csv').open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    best_by_centroid = min(all_poses, key=lambda x: x[3])
    best_by_score = min(all_poses, key=lambda x: x[2])
    summary = {
        'tight_box_size_A': tight_box,
        'unconstrained_box_size_A': geom['box_size_A'],
        'n_seeds': len(SEEDS), 'exhaustiveness': EXHAUSTIVENESS,
        'total_poses_evaluated': len(all_poses),
        'best_centroid_recovery': {'seed': best_by_centroid[0], 'pose_rank': best_by_centroid[1],
                                    'score_kcal_mol': best_by_centroid[2], 'centroid_distance_A': round(best_by_centroid[3], 3)},
        'best_score_pose': {'seed': best_by_score[0], 'pose_rank': best_by_score[1],
                             'score_kcal_mol': best_by_score[2], 'centroid_distance_A': round(best_by_score[3], 3)},
        'note': 'Tight-box multi-seed condition, not a distance-restrained dock (Vina has no native restraint API here). Reported as a separate, more constrained hypothesis alongside the unconstrained P3.5 result.'
    }
    (OUT / 'restrained_redocking_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
