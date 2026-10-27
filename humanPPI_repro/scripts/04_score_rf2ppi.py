#!/usr/bin/env python3
"""Step 4: RF2-PPI batch scoring across GPUs with checkpoint/resume.

Splits the *_input lists (path + L1) into per-GPU sublists; each GPU process
runs the official predict_list_PPI.py on its sublist. Resume = skip pairs whose
a3m is absent (pMSA generation failure) and rerun failed sharded lists fresh
(the official script rewrites its .log/.npz per list).
"""
import os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RF2 = os.path.join(ROOT, "external", "RoseTTAFold2-PPI")
MODEL = os.path.join(ROOT, "downloads", "RF2-PPI.pt")
IN_DIR = os.path.join(ROOT, "work", "pair_lists")     # *_input lists from step 3 (written next to shard lists)
WORK = os.path.join(ROOT, "work", "scoring")
GPUS = [int(g) for g in (sys.argv[1].split(",") if len(sys.argv) > 1 else ["0", "1", "2", "3", "4", "5"])]
PER_GPU = int(sys.argv[2]) if len(sys.argv) > 2 else 1   # concurrent lists per GPU
# NOTE: 4 concurrent lists per A100-40GB OOMs on deep-MSA pairs; 1 is safe
# (each worker peaks ~38GB on the largest pMSAs).

os.makedirs(WORK, exist_ok=True)

# collect all *_input lists produced by step 3, skipping fully scored ones
lists = []
for f in sorted(os.listdir(IN_DIR)):
    if not f.endswith("_input"):
        continue
    lf = os.path.join(IN_DIR, f)
    shard_list = lf[:-len("_input")]  # e.g. shard_000.txt
    try:
        n_expected = sum(1 for _ in open(shard_list))
    except OSError:
        n_expected = None
    log_fn = lf + ".log"
    n_done = -1
    if os.path.exists(log_fn):
        with open(log_fn) as fh:
            n_done = sum(1 for line in fh) - 1  # minus header
    if n_expected is not None and n_done >= n_expected > 0:
        print(f"skip {f}: already scored {n_done}/{n_expected}", flush=True)
        continue
    lists.append(lf)
print(f"{len(lists)} input lists to (re)run, GPUs {GPUS} x {PER_GPU} workers", flush=True)

# assign lists round-robin to GPU slots
jobs = []
for i, lf in enumerate(lists):
    gpu = GPUS[i % len(GPUS)]
    slot = (i // len(GPUS)) % PER_GPU
    jobs.append((gpu, slot, lf))

def run_job(job):
    gpu, slot, lf = job
    tag = os.path.basename(lf).replace("_input", "")
    gpu_dir = os.path.join(WORK, f"gpu{gpu}")
    os.makedirs(gpu_dir, exist_ok=True)
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512")
    # torch>=1.8 Categorical(validate_args) rejects fp16 probs summing to 0.9999
    # (sporadic, MSA-dependent). The authors' SE3nv image predates this strictness;
    # sitecustomize.py turns validation off, restoring it. PYTHONPATH injects it.
    env["PYTHONPATH"] = os.path.join(ROOT, "work", "patch") + os.pathsep + env.get("PYTHONPATH", "")
    t0 = time.time()
    r = subprocess.run(
        ["python", os.path.join(RF2, "src", "predict_list_PPI.py"),
         "-list_fn", lf, "-model_file", MODEL],
        cwd=gpu_dir, env=env, capture_output=True, text=True)
    dt = time.time() - t0
    status = "OK" if r.returncode == 0 else f"RC={r.returncode}"
    detail = "" if r.returncode == 0 else r.stderr.strip()[-300:]
    return f"{tag} gpu{gpu}: {status} {dt:.0f}s {detail}", r.returncode

results = {}
with ThreadPoolExecutor(max_workers=len(GPUS) * PER_GPU) as ex:
    for msg, rc in ex.map(run_job, jobs):
        print(msg, flush=True)
        results[msg.split()[0]] = rc

n_ok = sum(1 for rc in results.values() if rc == 0)
print(f"DONE {n_ok}/{len(results)} lists OK", flush=True)
sys.exit(0 if n_ok == len(results) else 1)
