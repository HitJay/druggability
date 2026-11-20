# Marjorie HPC (AWS ParallelCluster / Slurm) Workflow for Druggability

## 1. Connection & Storage

- **SSH alias**: `ssh marjorie` (configured in `~/.ssh/config`, `User qyji`, `IdentityFile ~/.ssh/id_ed25519`).
- **Home isolation**: Remote home is `/novo/users/qyji` (NOT shared with on-prem `/das/user/QYJI`). Sync code/inputs explicitly via `rsync`.
- **RIC Team Shared Disk**: `/novo/projects/departments/ric/QYJI` (alongside `IJDN`, `LLJG`, `NYGZ`, `TFWG`, `YUXM`, `shared_projects`; `/novo/projects` has 749 TB total / 124 TB avail, 84% used — use for durable team-shared results).
- **Large scratch / transient outputs**: `/delete90d/qyji/` (48 TB total / ~34 TB free, 30% used; auto-purged after 90 days — use for large MD/docking/screening intermediates).
- **Shared DataHub / NNEDH (`/dataconnector/*` & `dmacli`)**: Modern replacement for legacy NNEDL S3:
  - Ready without extra auth: `/dataconnector/biodata` (99 curated datasets incl. `chembl_latest`, `drugbank_latest`, `bindingdb_raw`, `enamine_raw`, `chemspace_raw`, `clinvar_latest`, `ctgov_latest`, `STRING_raw`, `GTEx_raw`) and `/dataconnector/masif_seed`.
  - Controlled buckets (`dptx-tde-imaging-data`, `seahorse-virtual-assay`, `red-dp.*`) are gated by AD group / NNEDH dataset permissions.
  - NNEDH CLI: `/novo/software/scripts/dmacli_src/1.7.7/venv/bin/dmacli nnedh` (`login`, `login-test`, `dataset`, `environment`).
  - (Old docs referencing `/nfs_home/`, `okta-awscli`, and `prd.nnedl.pub.aws.novonordisk.com/credentials` are obsolete.)
- **Login-shell PATH requirement**: Non-interactive SSH must wrap commands in `bash -l -c "..."` so `/opt/slurm/bin` and `/novo/software/scripts` (`nnjr`) are on `PATH`.

## 2. Partitions, GPUs & Reference Pricing

On-demand reference rates from `nnjr` EC2 pricing (`-spot` partitions are cheaper; prefer `-spot` for interruptible or checkpointed jobs):

| Partition | Instance | GPU / CPU | Mem | Est. On-Demand Rate |
|---|---|---|---|---|
| `gpu` / `gpu-spot` | `g6.2xlarge` | 1× NVIDIA L4 (24 GB) / 4c | 32 GB | ~$0.98/hr |
| `gpu` / `gpu-spot` | `g6.12xlarge` | 4× NVIDIA L4 / 24c | 192 GB | ~$4.60/hr |
| `gpu` / `gpu-spot` | `g6.48xlarge` | 8× NVIDIA L4 / 96c | 768 GB | ~$13.35/hr |
| `g6e` / `g6e-spot` | `g6e.8xlarge` | 1× NVIDIA L40S (48 GB) / 16c | 256 GB | ~$4.53/hr |
| `g6e` / `g6e-spot` | `g6e.24xlarge` | 4× NVIDIA L40S / 48c | 768 GB | ~$15.07/hr |
| `compute` / `compute-spot` | `c7i.12xlarge` | 24c CPU | 96 GB | ~$2.14/hr |

Note: `idle~` nodes spin up on demand (cold-start ~5–8 min; warm nodes start in seconds).

## 3. Budget & Cost Tracking (`nnjr`)

- **Slurm Account**: `40033476 research insights china` (QOS `normal`, no hard Slurm `GrpTRESMins`/`MaxTRESMins` cap).
- **Cloud Monthly Budget Cap**: **USD 5,000/month** across covered cloud systems. Already-running jobs continue if the limit is reached, but new submissions near the limit may be blocked or queued.
- **Check personal MTD spend**:
  ```bash
  nnjr -u qyji -S $(date +%Y-%m-01) -f json | python3 -c "import sys,json; d=json.load(sys.stdin); print('jobs:', len(d), 'node_cost:', round(sum(x.get('node_cost',0) or 0 for x in d),2))"
  ```
- **Check department/account MTD spend (by user)**:
  ```bash
  nnjr --account "40033476 research insights china" -S $(date +%Y-%m-01) -f json
  ```
- **Check single job**: `nnjr -j <JOBID> -f table`

## 4. Druggability Closed-Loop Workflow

1. **Estimate**: Estimate GPU/CPU hours and USD cost before submitting.
2. **Sync**: `rsync -az` code/inputs from `/das/user/QYJI/druggability/` to `marjorie:/novo/users/qyji/Projects/druggability/`.
3. **Environment**: `.venv` on marjorie uses Python 3.12 + `uv`. Avoid full `uv sync` (pulls `decimer`→TensorFlow >500 MB over NFS); install task-specific deps with `uv pip install` + `uv pip install --no-deps -e .`.
4. **Submit & Verify**: `scp` `.sbatch` + `.py` scripts to marjorie, `sbatch --parsable`, poll `squeue`/`sacct`, inspect `logs/` + `nnjr -j <JOBID>`, and `rsync` outputs back.

## 5. Reusable Tools & Datasets on Marjorie (Mapped to `druggability`)

| Module / Capability | Reusable Datasets (`/dataconnector/*`) | Reusable Tools (`/novo/systems/modules` & spack) |
|---|---|---|
| `tractability.py` / `assess` / `batch.py` | `chembl_latest`, `drugbank_latest`, `bindingdb_raw`, `hpa_latest`, `ctgov_latest`, `tox21_raw` | `duckdb/1.3.0-spk` (fast local Parquet/TSV queries) |
| `interface_variants.py` | `clinvar_latest`, `gnomad_raw`, `omim_latest`, `open_targets_genetics_latest`, `pdb_latest`, `dssp_raw` | `vep`, `DockQ`, `rosetta` (`cartesian_ddg` example) |
| `drugclip.py` / SMoL / Virtual Screening | `enamine_raw`, `chemspace_raw`, `Molport_raw`, `MedChemExpress_raw`, `SelleckChem_raw`, `targetmol_raw` | `infinisee`, `schrodinger`, `moe`, `openmm/8.1.1-spk`, `amber/26`, `gromacs`, `plumed` |
| `peptide/` & PPI | `thpdb_raw`, `string_latest`, `cellphonedb_raw`, `/dataconnector/masif_seed` | `piper`, `DockQ`, `signalp`, `biolib` |
