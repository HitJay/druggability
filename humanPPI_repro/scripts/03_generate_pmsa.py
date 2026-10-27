#!/usr/bin/env python3
"""Step 3: run paired-MSA generation for all benchmark shards (parallel).

Each shard runs generate_protein_pair_MSA.py with its own cwd (the script writes
a shared-name tmplog into cwd via hhfilter redirect, so shards must not share cwd).
Outputs: work/paired_msas/*.i90.a3m  + work/pmsa_inputs/shard_XXX.txt_input
"""
import os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RF2 = os.path.join(ROOT, "external", "RoseTTAFold2-PPI")
SINGLE = os.path.join(ROOT, "work", "single_msas")
PAIRED = os.path.join(ROOT, "work", "paired_msas")
RUNDIR = os.path.join(ROOT, "work", "pmsa_run")
SHARDS = os.path.join(ROOT, "work", "pair_lists")

NPROC = int(sys.argv[1]) if len(sys.argv) > 1 else 32

os.makedirs(PAIRED, exist_ok=True)
os.makedirs(RUNDIR, exist_ok=True)

shard_files = sorted(f for f in os.listdir(SHARDS) if f.endswith(".txt"))
print(f"{len(shard_files)} shards, {NPROC} parallel workers", flush=True)

def run_shard(shard_fn):
    shard_path = os.path.join(SHARDS, shard_fn)
    tag = shard_fn.replace(".txt", "")
    workdir = os.path.join(RUNDIR, tag)
    os.makedirs(workdir, exist_ok=True)
    env = dict(os.environ)
    t0 = time.time()
    r = subprocess.run(
        ["python", os.path.join(RF2, "generate_protein_pair_MSA.py"),
         shard_path, SINGLE, PAIRED],
        cwd=workdir, env=env, capture_output=True, text=True)
    dt = time.time() - t0
    status = "OK" if r.returncode == 0 else f"RC={r.returncode}"
    return f"{tag}: {status} {dt:.0f}s  {r.stderr.strip()[-200:] if r.returncode else ''}"

with ThreadPoolExecutor(max_workers=NPROC) as ex:
    for res in ex.map(run_shard, shard_files):
        print(res, flush=True)
print("ALL_SHARDS_DONE", flush=True)
