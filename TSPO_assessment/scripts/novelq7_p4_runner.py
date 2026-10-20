"""ws7 P4 runner: dispatch FEP annihilation-TI jobs across 4 GPUs.

Reads data/novelq7_p4_jobs.json [{tag, ligand, anchors}], splits round-robin over
4 workers, each pinned to one GPU. Output: output/fep_a7/scan7_<tag>_<ligand>.json
(anchors accumulate into the same file as anchors complete).
"""
import json, os, subprocess, sys

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
PY = "/data/user/QYJI/micromamba/envs/openfe-md/bin/python"

import sys
jobs = json.load(open(sys.argv[1] if len(sys.argv) > 1 else f"{BASE}/data/novelq7_p4_jobs.json"))

# skip jobs whose output already has all anchors done
def done_anchors(job):
    out = f"{BASE}/output/fep_a7/scan7_{job['tag']}_{job['ligand']}.json"
    if not os.path.exists(out):
        return set()
    j = json.load(open(out))
    return set(j.get("anchors", {}))

pending = []
for job in jobs:
    d = done_anchors(job)
    rem = [a for a in job["anchors"] if a not in d]
    if rem:
        pending.append({**job, "anchors": rem})
print(f"{len(pending)}/{len(jobs)} jobs pending", flush=True)

workers = [[] for _ in range(4)]
for i, job in enumerate(pending):
    workers[i % 4].append(job)
NWORK = int(os.environ.get("FEP_NWORK", "4"))
for i, w in enumerate(workers[:NWORK]):
    json.dump(w, open(f"{BASE}/data/novelq7_p4_worker{i}.json", "w"), indent=1)
    print(f"worker{i}: {[(j['tag'], j['ligand']) for j in w]}")

for i, w in enumerate(workers[:NWORK]):
    if not w:
        continue
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(i), FEP_CUDA_PRECISION="double")
    log = open(f"{BASE}/output/fep_a7/worker{i}.log", "a")
    for j, job in enumerate(w):
        if job["ligand"] == "fgin":
            cmd = [PY, f"{BASE}/scripts/novelq7_p4_fep.py", job["tag"], job["ligand"]] + job["anchors"]
        else:
            cmd = [PY, f"{BASE}/scripts/novelq7_p4_fep.py", job["tag"], job["ligand"]]  # default_anchors resolves chain
        r = subprocess.run(cmd, env=env, capture_output=True, text=True)
        log.write(r.stdout)
        if r.returncode != 0:
            log.write(f"\nJOB FAILED rc={r.returncode}: {job['tag']}/{job['ligand']}\n{r.stderr[-1500:]}\n")
        log.flush()
    log.close()
print("P4 runner done", flush=True)
