"""
marjorie — Marjorie HPC (AWS ParallelCluster / Slurm) & NNEDH Biodata helpers.

Provides:
- Pre-job GPU/CPU cost estimation grounded in nnjr EC2 on-demand rates
  (with USD 5,000/month cloud budget cap awareness).
- Slurm `.sbatch` script rendering with standard scratch (`/delete90d/qyji`),
  RIC shared storage (`/novo/projects/departments/ric/QYJI`), and reusable
  HPC modules (`amber/26`, `openmm/8.1.1-spk`, `infinisee`, `schrodinger`,
  `duckdb/1.3.0-spk`, `DockQ`, `piper`, `vep`, `signalp`, etc.).
- Local NNEDH `/dataconnector/biodata` catalog & DuckDB Parquet query helper
  (e.g. `chembl_latest/Subsets/ChemblCompound/part-0/*.parquet`).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

MONTHLY_BUDGET_USD = 5000.0
DEFAULT_SLURM_ACCOUNT = "40033476 research insights china"
DEFAULT_BIODATA_ROOT = "/dataconnector/biodata"
DEFAULT_WORKDIR = "/novo/users/qyji/Projects/druggability"
DEFAULT_SCRATCH_DIR = "/delete90d/qyji"
DEFAULT_RIC_DIR = "/novo/projects/departments/ric/QYJI"

INSTANCE_PRICES_USD_HR: dict[str, dict] = {
    "g6.2xlarge": {"gpus": 1, "gpu_model": "L4", "cpus": 4, "mem_gb": 32, "usd_hr": 0.9776},
    "g6.12xlarge": {"gpus": 4, "gpu_model": "L4", "cpus": 24, "mem_gb": 192, "usd_hr": 4.6016},
    "g6.48xlarge": {"gpus": 8, "gpu_model": "L4", "cpus": 96, "mem_gb": 768, "usd_hr": 13.3504},
    "g6e.8xlarge": {"gpus": 1, "gpu_model": "L40S", "cpus": 16, "mem_gb": 256, "usd_hr": 4.52856},
    "g6e.24xlarge": {"gpus": 4, "gpu_model": "L40S", "cpus": 48, "mem_gb": 768, "usd_hr": 15.06559},
    "g6e.48xlarge": {"gpus": 8, "gpu_model": "L40S", "cpus": 96, "mem_gb": 1536, "usd_hr": 30.13118},
    "c7i.12xlarge": {"gpus": 0, "gpu_model": None, "cpus": 24, "mem_gb": 96, "usd_hr": 2.142},
    "r7i.12xlarge": {"gpus": 0, "gpu_model": None, "cpus": 48, "mem_gb": 384, "usd_hr": 3.02},
}

MARJORIE_PARTITIONS: dict[str, dict] = {
    "gpu": {"default_instance": "g6.2xlarge", "default_gres": "gpu:l4:1", "spot": False},
    "gpu-spot": {"default_instance": "g6.2xlarge", "default_gres": "gpu:l4:1", "spot": True},
    "g6e": {"default_instance": "g6e.8xlarge", "default_gres": "gpu:l40s:1", "spot": False},
    "g6e-spot": {"default_instance": "g6e.8xlarge", "default_gres": "gpu:l40s:1", "spot": True},
    "compute": {"default_instance": "c7i.12xlarge", "default_gres": None, "spot": False},
    "compute-spot": {"default_instance": "c7i.12xlarge", "default_gres": None, "spot": True},
    "highmem": {"default_instance": "r7i.12xlarge", "default_gres": None, "spot": False},
    "highmem-spot": {"default_instance": "r7i.12xlarge", "default_gres": None, "spot": True},
}

REUSABLE_MODULES: dict[str, str] = {
    "duckdb": "duckdb/1.3.0-spk",
    "openmm": "openmm/8.1.1-spk",
    "cuda": "cuda/12.8.0-spk",
    "amber": "amber/26",
    "gromacs": "gromacs",
    "plumed": "plumed",
    "schrodinger": "schrodinger",
    "moe": "moe",
    "infinisee": "infinisee",
    "dockq": "DockQ",
    "piper": "piper",
    "vep": "vep",
    "signalp": "signalp",
    "biolib": "biolib",
    "apptainer": "apptainer/1.4.0-spk",
    "nextflow": "nextflow/25.04.0-spk",
}


@dataclass
class CostEstimate:
    partition: str
    instance_type: str
    spot: bool
    nodes: int
    hours: float
    gpus_per_node: int
    gpu_model: str | None
    gpu_hours: float
    cpu_hours: float
    on_demand_usd_hr: float
    estimated_usd_upper: float
    pct_of_monthly_budget: float

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_cost(
    partition: str,
    hours: float,
    nodes: int = 1,
    instance_type: str | None = None,
) -> CostEstimate:
    """Estimate GPU/CPU hours and upper-bound on-demand USD cost for a Marjorie job."""
    if hours <= 0:
        raise ValueError("hours must be > 0")
    if nodes < 1:
        raise ValueError("nodes must be >= 1")
    if partition not in MARJORIE_PARTITIONS:
        raise ValueError(
            f"Unknown partition {partition!r}. Choose from: {sorted(MARJORIE_PARTITIONS)}"
        )

    part_info = MARJORIE_PARTITIONS[partition]
    inst = instance_type or part_info["default_instance"]
    if inst not in INSTANCE_PRICES_USD_HR:
        raise ValueError(
            f"Unknown instance_type {inst!r}. Choose from: {sorted(INSTANCE_PRICES_USD_HR)}"
        )

    spec = INSTANCE_PRICES_USD_HR[inst]
    usd_upper = round(spec["usd_hr"] * hours * nodes, 4)
    return CostEstimate(
        partition=partition,
        instance_type=inst,
        spot=bool(part_info["spot"]),
        nodes=nodes,
        hours=hours,
        gpus_per_node=spec["gpus"],
        gpu_model=spec["gpu_model"],
        gpu_hours=round(spec["gpus"] * hours * nodes, 2),
        cpu_hours=round(spec["cpus"] * hours * nodes, 2),
        on_demand_usd_hr=spec["usd_hr"],
        estimated_usd_upper=usd_upper,
        pct_of_monthly_budget=round(100.0 * usd_upper / MONTHLY_BUDGET_USD, 2),
    )


def _format_slurm_time(hours: float) -> str:
    total_mins = max(1, int(round(hours * 60)))
    hh, mm = divmod(total_mins, 60)
    return f"{hh:02d}:{mm:02d}:00"


def render_sbatch(
    job_name: str,
    command: str,
    partition: str = "gpu-spot",
    hours: float = 1.0,
    gres: str | None = None,
    cpus: int | None = None,
    mem_gb: int | None = None,
    modules: Iterable[str] | None = None,
    workdir: str = DEFAULT_WORKDIR,
    scratch_dir: str = DEFAULT_SCRATCH_DIR,
    ric_dir: str = DEFAULT_RIC_DIR,
    log_dir: str | None = None,
) -> str:
    """Render a Slurm .sbatch script configured for Marjorie."""
    if partition not in MARJORIE_PARTITIONS:
        raise ValueError(f"Unknown partition {partition!r}")

    part_info = MARJORIE_PARTITIONS[partition]
    spec = INSTANCE_PRICES_USD_HR[part_info["default_instance"]]
    eff_gres = gres if gres is not None else part_info["default_gres"]
    eff_cpus = cpus if cpus is not None else spec["cpus"]
    eff_mem = mem_gb if mem_gb is not None else max(4, min(spec["mem_gb"] - 2, spec["mem_gb"]))
    eff_log_dir = log_dir or f"{workdir.rstrip('/')}/logs"

    lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name={job_name}",
        f"#SBATCH --partition={partition}",
    ]
    if eff_gres:
        lines.append(f"#SBATCH --gres={eff_gres}")
    lines.extend(
        [
            f"#SBATCH --cpus-per-task={eff_cpus}",
            f"#SBATCH --mem={eff_mem}G",
            f"#SBATCH --time={_format_slurm_time(hours)}",
            f"#SBATCH --output={eff_log_dir}/{job_name}_%j.out",
            f"#SBATCH --error={eff_log_dir}/{job_name}_%j.err",
            "",
            "set -euo pipefail",
            f'mkdir -p "{eff_log_dir}" "{scratch_dir}" "{ric_dir}"',
            f'export MARJORIE_SCRATCH_DIR="{scratch_dir}"',
            f'export MARJORIE_RIC_DIR="{ric_dir}"',
            f'cd "{workdir}"',
        ]
    )

    if modules:
        mod_list = [REUSABLE_MODULES.get(m, m) for m in modules]
        lines.append("module load " + " ".join(mod_list))

    lines.extend(["", command.strip(), ""])
    return "\n".join(lines)


def list_biodata(
    root: str = DEFAULT_BIODATA_ROOT,
    pattern: str | None = None,
) -> list[str]:
    """List available dataset directories under `/dataconnector/biodata`."""
    p = Path(root)
    if not p.is_dir():
        raise FileNotFoundError(f"Biodata root not found: {root}")
    names = sorted(entry.name for entry in p.iterdir() if entry.is_dir())
    if pattern:
        needle = pattern.lower()
        names = [n for n in names if needle in n.lower()]
    return names


def query_chembl_compounds(
    where: str = "max_phase = 4",
    columns: Iterable[str] | None = None,
    limit: int = 20,
    root: str = DEFAULT_BIODATA_ROOT,
    duckdb_bin: str = "duckdb",
) -> list[dict]:
    """Query `/dataconnector/biodata/chembl_latest/Subsets/ChemblCompound` via DuckDB."""
    if limit < 1 or limit > 5000:
        raise ValueError("limit must be between 1 and 5000")
    if ";" in where:
        raise ValueError("where clause must not contain ';'")

    parquet_glob = os.path.join(
        root, "chembl_latest", "Subsets", "ChemblCompound", "part-0", "*.parquet"
    )
    parquet_dir = os.path.dirname(parquet_glob)
    # Trigger autofs/Storage-Gateway mount on compute nodes before deep stat
    if os.path.exists(root):
        os.listdir(root)
    if not os.path.isdir(parquet_dir):
        raise FileNotFoundError(f"ChEMBL parquet directory not found: {parquet_dir}")

    exe = shutil.which(duckdb_bin)
    if not exe:
        raise RuntimeError(
            f"duckdb binary {duckdb_bin!r} not found on PATH (run `module load duckdb/1.3.0-spk` on marjorie)"
        )

    cols = list(columns) if columns else [
        "compound_chembl_id",
        "max_phase",
        "full_mwt",
        "alogp",
        "num_ro5_violations",
        "canonical_smiles",
    ]
    col_sql = ", ".join(cols)
    sql = (
        f"SELECT {col_sql} FROM read_parquet('{parquet_glob}') "
        f"WHERE {where} LIMIT {int(limit)};"
    )
    proc = subprocess.run(
        [exe, "-json", "-c", sql],
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = proc.stdout.strip()
    return json.loads(stdout) if stdout else []
