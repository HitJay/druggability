#!/usr/bin/env python3
"""Multi-seed, high-exhaustiveness docking for the two conformation-sensitive
compounds identified in P3 (AZ1 / GPR81 agonist 2, and GPR81 agonist 1 / Takeda
compound 2), across all three ligand-bound receptors. Reports score and pose-cluster
stability per seed so a single-seed anomaly is not mistaken for a real biological
signal.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from vina import Vina

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'data/gpr81_phase1'
P2 = P / 'phase2_prepared'
P3 = P / 'phase3_docking'
OUT = P / 'phase3_multiseed'
(OUT / 'poses').mkdir(parents=True, exist_ok=True)

TARGET_COMPOUNDS = ['CHBA', '3_OBA']
RECEPTORS = ['8Z87', '9KT9', '8Z8A']
SEEDS = [20260803, 1, 2, 3, 4, 5, 6, 7]
EXHAUSTIVENESS = 32
N_POSES = 8
OUT_SUFFIX = '_batch2'


def parse_pose(p):
    lines = p.read_text().splitlines()
    models, cur = [], []
    for l in lines:
        if l.startswith('MODEL') and cur:
            models.append(cur); cur = []
        cur.append(l)
    if cur:
        models.append(cur)
    out = []
    for m in models:
        score = None
        for l in m:
            if l.startswith('REMARK VINA RESULT:'):
                score = float(l.split()[3])
        atoms = []
        for l in m:
            if l.startswith(('ATOM', 'HETATM')):
                try:
                    atoms.append(np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])]))
                except (ValueError, IndexError):
                    continue
        if score is not None and atoms:
            out.append((score, np.mean(atoms, axis=0)))
    return out


def cluster_by_centroid(poses, threshold=2.5):
    """Greedy clustering of (score, centroid) poses by centroid distance."""
    clusters = []
    for score, centroid in poses:
        placed = False
        for c in clusters:
            if np.linalg.norm(c['centroid_ref'] - centroid) < threshold:
                c['members'].append((score, centroid))
                placed = True
                break
        if not placed:
            clusters.append({'centroid_ref': centroid, 'members': [(score, centroid)]})
    for c in clusters:
        scores = [m[0] for m in c['members']]
        c['n_members'] = len(c['members'])
        c['best_score'] = min(scores)
        c['mean_score'] = round(float(np.mean(scores)), 3)
        del c['centroid_ref'], c['members']
    return sorted(clusters, key=lambda c: c['best_score'])


def main():
    p2 = json.loads((P2 / 'phase2_manifest.json').read_text())
    rows = []
    cluster_summaries = []
    for cid in TARGET_COMPOUNDS:
        ligand_pdbqt = P3 / 'ligands_pdbqt' / f'{cid}.pdbqt'
        assert ligand_pdbqt.exists(), f"missing prepared ligand {ligand_pdbqt}"
        for rid in RECEPTORS:
            receptor = next(x for x in p2['structures'] if x['pdb_id'] == rid)
            geom = receptor['ligand_geometry']
            all_poses = []
            for seed in SEEDS:
                v = Vina(sf_name='vina', seed=seed)
                v.set_receptor(receptor['receptor_pdbqt']['path'])
                v.compute_vina_maps(center=geom['center_A'], box_size=geom['box_size_A'])
                v.set_ligand_from_file(str(ligand_pdbqt))
                v.dock(exhaustiveness=EXHAUSTIVENESS, n_poses=N_POSES)
                pose_file = OUT / 'poses' / f'{cid}_{rid}_seed{seed}.pdbqt'
                v.write_poses(str(pose_file), n_poses=N_POSES, overwrite=True)
                parsed = parse_pose(pose_file)
                for rank, (score, centroid) in enumerate(parsed, start=1):
                    rows.append({'compound_id': cid, 'receptor_id': rid, 'seed': seed,
                                 'pose_rank': rank, 'score_kcal_mol': score,
                                 'centroid_x': round(float(centroid[0]), 3),
                                 'centroid_y': round(float(centroid[1]), 3),
                                 'centroid_z': round(float(centroid[2]), 3)})
                    all_poses.append((score, centroid))
            clusters = cluster_by_centroid(all_poses)
            cluster_summaries.append({
                'compound_id': cid, 'receptor_id': rid,
                'n_seeds': len(SEEDS), 'total_poses': len(all_poses),
                'n_distinct_pose_clusters': len(clusters),
                'best_score_overall': min(p[0] for p in all_poses),
                'top_3_clusters': clusters[:3],
            })
            print(f"[DONE] {cid} {rid}: {len(clusters)} clusters, best={min(p[0] for p in all_poses):.3f}")

    with (OUT / f'multiseed_results{OUT_SUFFIX}.csv').open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (OUT / f'multiseed_cluster_summary{OUT_SUFFIX}.json').write_text(json.dumps(cluster_summaries, indent=2) + '\n')
    print(json.dumps(cluster_summaries, indent=2))


if __name__ == '__main__':
    main()
