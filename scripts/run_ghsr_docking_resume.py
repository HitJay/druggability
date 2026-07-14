#!/usr/bin/env python3
"""Phase 5+6: Resumable docking — load receptor ONCE, dock all ligands.
Resumes from docking_results.csv — already-docked compounds are skipped.
Run inside tmux: tmux new -s ghsr_dock './scripts/run_ghsr_docking_resume.py'
"""
import os, json, time, csv, sys

from vina import Vina

OUTDIR = "/das/user/QYJI/druggability/output/2026-07-10/ghsr_inverse_agonist_docking"
STRUCT = f"{OUTDIR}/structures"
LIGAND_DIR = f"{OUTDIR}/ligands"
DOCKED_7F83 = f"{OUTDIR}/docked_7F83"
DOCKED_8JSR = f"{OUTDIR}/docked_8JSR"
CSV = f"{OUTDIR}/docking_results.csv"

os.makedirs(DOCKED_7F83, exist_ok=True)
os.makedirs(DOCKED_8JSR, exist_ok=True)

with open(f"{OUTDIR}/grid_params.json") as f:
    grid = json.load(f)

ligand_files = sorted([
    f for f in os.listdir(LIGAND_DIR)
    if f.endswith('.pdbqt') and os.path.getsize(os.path.join(LIGAND_DIR, f)) > 100
])
print(f"Ligands on disk: {len(ligand_files)}", flush=True)

# Resume: read already-done compound IDs from CSV
done = set()
if os.path.exists(CSV):
    with open(CSV) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            cid = row.get('compound_id', '').strip()
            if cid:
                done.add(cid)
    print(f"Already docked: {len(done)}", flush=True)

FN = ['compound_id', 'score_7F83', 'score_8JSR', 'delta_score',
      'time_7F83', 'time_8JSR', 'error']

def append(csv_path, row):
    exists = os.path.exists(csv_path)
    with open(csv_path, 'a', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=FN)
        if not exists:
            w.writeheader()
        w.writerow(row)

EXH = 8
NPOSES = 3

# Pre-load both receptors once
print("Loading receptors + computing maps...", flush=True)
v7 = Vina(sf_name='vina')
v7.set_receptor(f"{STRUCT}/7F83_chainA_apo.pdbqt")
v7.compute_vina_maps(center=grid['7F83']['center'], box_size=grid['7F83']['box_size'])

v8 = Vina(sf_name='vina')
v8.set_receptor(f"{STRUCT}/8JSR_chainR_apo.pdbqt")
v8.compute_vina_maps(center=grid['8JSR']['center'], box_size=grid['8JSR']['box_size'])
print("Maps ready.", flush=True)

# Filter to pending
todo = [(f, f.replace('.pdbqt', '')) for f in ligand_files if f.replace('.pdbqt', '') not in done]
print(f"Pending: {len(todo)}", flush=True)

if len(todo) == 0:
    print("All compounds already docked. Nothing to do.")
    sys.exit(0)

t0 = time.time()
batch_t0 = t0

for i, (fname, cid) in enumerate(todo):
    lig_path = os.path.join(LIGAND_DIR, fname)
    row = {'compound_id': cid, 'error': ''}

    try:
        t1 = time.time()
        v7.set_ligand_from_file(lig_path)
        v7.dock(exhaustiveness=EXH, n_poses=NPOSES)
        s7 = v7.energies(n_poses=1)[0][0]
        t7 = time.time() - t1

        t2 = time.time()
        v8.set_ligand_from_file(lig_path)
        v8.dock(exhaustiveness=EXH, n_poses=NPOSES)
        s8 = v8.energies(n_poses=1)[0][0]
        t8 = time.time() - t2

        v7.write_poses(f"{DOCKED_7F83}/{cid}_out.pdbqt", n_poses=1, overwrite=True)
        v8.write_poses(f"{DOCKED_8JSR}/{cid}_out.pdbqt", n_poses=1, overwrite=True)

        row.update({'score_7F83': round(s7, 2), 'score_8JSR': round(s8, 2),
                     'delta_score': round(s7 - s8, 2), 'time_7F83': round(t7, 1),
                     'time_8JSR': round(t8, 1)})
    except Exception as e:
        row['error'] = str(e)[:200].replace('\n',' ').replace('\r',' ')

    append(CSV, row)

    if (i + 1) % 100 == 0:
        elapsed = time.time() - batch_t0
        rate = 100 / elapsed * 60  # per minute
        remaining = (len(todo) - i - 1) / rate
        print(f"  [{i+1}/{len(todo)}] {rate:.1f}/min — {remaining:.0f} min remaining  "
              f"last: {cid} 7F83={row.get('score_7F83','?')} 8JSR={row.get('score_8JSR','?')}",
              flush=True)
        batch_t0 = time.time()

elapsed = time.time() - t0
print(f"\nDone in {elapsed/60:.0f} min ({len(todo)/elapsed*60:.0f} compounds/min)", flush=True)
print(f"Results: {CSV}", flush=True)
