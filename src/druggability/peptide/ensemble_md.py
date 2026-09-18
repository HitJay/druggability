"""
druggability.peptide.ensemble_md — GPU 加速短轨迹动力学系综 MM/GBSA 评估模块

核心物理优势:
- 彻底解决静态单构象 MM/GBSA 在多肽点突变上的“未松弛空洞伪影” (Void Penalty Artifact)；
- 在显式 TIP3P 水盒 + 0.15 M NaCl 离子环境下，利用 NVIDIA A100 GPU 进行全原子平衡与生产采样；
- 提取平衡轨迹系综快照 (Snapshots)，在 Amber14SB + GBn2 力场下计算系综时间平均值:
    <ΔG_bind> = <E_complex> - <E_receptor> - <E_peptide> ± σ
- 提取多肽主链动态 RMSD、构象漂移与稳定性判定。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

logger = logging.getLogger(__name__)

# 默认 OpenMM 执行环境与 Worker 路径 (支持环境变量覆盖)
DEFAULT_OPENMM_PYTHON = Path(
    os.getenv(
        "OPENMM_PYTHON",
        "/data/user/QYJI/micromamba/envs/openfe-md/bin/python",
    )
)
DEFAULT_WORKER_SCRIPT = Path(__file__).parent / "ensemble_md_worker.py"


@dataclass
class EnsembleMDResult:
    """短轨迹动力学系综 MM/GBSA 计算结果对象"""

    ok: bool
    complex_name: str
    receptor_chain: str
    peptide_chain: str
    length_ns: float
    n_snapshots: int
    mean_delta_g: float  # <ΔG_bind> kcal/mol
    std_delta_g: float  # σ kcal/mol
    min_delta_g: float
    max_delta_g: float
    delta_g_trajectory: list[float] = field(default_factory=list)
    mean_pep_rmsd: float = 0.0  # Å
    final_pep_rmsd: float = 0.0  # Å
    pep_rmsd_trajectory: list[float] = field(default_factory=list)
    is_stable_binder: bool = False
    ns_per_day: float = 0.0
    production_dcd: str = ""
    solvated_pdb: str = ""
    simulation_log: str = ""
    result_json: str = ""
    elapsed_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_df(self):
        """转为 pandas DataFrame (包含每帧的 ΔG 与 RMSD)"""
        import pandas as pd

        frames = list(range(len(self.delta_g_trajectory)))
        return pd.DataFrame({
            "frame": frames,
            "delta_g_kcal_mol": self.delta_g_trajectory,
        })

    def summary_markdown(self) -> str:
        """生成供 Agent 汇报和交付总结的 Markdown 表格"""
        if not self.ok:
            return f"**Ensemble MM/GBSA Calculation Failed**: {self.error}"

        stability_badge = (
            "🟢 **Stable Binder** (Mean RMSD < 2.5 Å, <ΔG> < -10 kcal/mol)"
            if self.is_stable_binder
            else "🟡 **Borderline / Dynamic Fluctuations**"
        )

        lines = [
            f"### Short-MD Ensemble MM/GBSA Profile: `{self.complex_name}`",
            rf"- **Ensemble Binding Free Energy ($\langle \Delta G_\text{{bind}} \rangle$)**: **`{self.mean_delta_g:.2f} ± {self.std_delta_g:.2f} kcal/mol`**",
            f"- **Trajectory Energy Range**: `[{self.min_delta_g:.2f}, {self.max_delta_g:.2f}] kcal/mol` across **{self.n_snapshots} snapshots**",
            f"- **Peptide Backbone RMSD**: Mean = **`{self.mean_pep_rmsd:.2f} Å`**, Final = **`{self.final_pep_rmsd:.2f} Å`**",
            f"- **Binding Assessment**: {stability_badge}",
            f"- **Simulation Sampling**: `{self.length_ns:.2f} ns` explicit TIP3P solvent (Speed: **`{self.ns_per_day:.1f} ns/day`**)",
            f"- **Chains Profile**: Receptor = `{self.receptor_chain}`, Peptide = `{self.peptide_chain}`",
            "",
            r"#### 1. Snapshot Energy Samples (Head & Tail Frames)",
            r"| Frame Index | $\Delta G_\text{bind}$ (kcal/mol) | Trajectory Timestamp |",
            "| :---: | :---: | :---: |",
        ]

        traj = self.delta_g_trajectory
        sample_indices = []
        if len(traj) <= 6:
            sample_indices = list(range(len(traj)))
        else:
            sample_indices = [0, 1, len(traj) // 2, len(traj) - 2, len(traj) - 1]

        for idx in sample_indices:
            approx_ps = round((idx / max(1, len(traj) - 1)) * (self.length_ns * 1000.0), 1)
            lines.append(f"| Snapshot {idx + 1} | `{traj[idx]:.2f}` | ~{approx_ps} ps |")

        return "\n".join(lines)


# ── 核心调度函数 ───────────────────────────────────────────────────────


def run_ensemble_mmgbsa(
    complex_pdb: str | Path,
    *,
    length_ns: float = 1.0,
    n_snapshots: int = 25,
    gpu_id: int = 0,
    out_dir: str | Path | None = None,
    receptor_chain: str | None = None,
    peptide_chain: str | None = None,
    dt_fs: float = 2.0,
    timeout: int = 7200,
    openmm_python: str | Path | None = None,
) -> EnsembleMDResult:
    """
    运行显式水短轨迹平衡动力学并计算系综平均 MM/GBSA 结合自由能。

    Parameters
    ----------
    complex_pdb : str | Path
        复合物结构 PDB 路径。
    length_ns : float, default 1.0
        生产动力学时长 (ns)。支持快速烟测 (如 0.05 ns) 或生产运行 (如 1.0~2.0 ns)。
    n_snapshots : int, default 25
        提取用于 MM/GBSA 能量分解的构象快照数量。
    gpu_id : int, default 0
        CUDA 设备编号 (A100)。
    out_dir : str | Path | None
        轨迹输出目录。若为 None 则自动创建临时目录。
    receptor_chain : str | None
        受体链 ID (自动推断若为空)。
    peptide_chain : str | None
        多肽链 ID (自动推断若为空)。
    dt_fs : float, default 2.0
        动力学积分步长 (飞秒)。
    timeout : int, default 7200
        运行超时时间 (秒)。
    openmm_python : str | Path | None
        OpenMM 运行环境解释器路径。

    Returns
    -------
    EnsembleMDResult
        包含均值结合能、标准差、能量轨迹与 RMSD 统计的结构体。
    """
    t_start = time.time()
    pdb_path = Path(complex_pdb).resolve()
    if not pdb_path.exists():
        return EnsembleMDResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            receptor_chain="",
            peptide_chain="",
            length_ns=length_ns,
            n_snapshots=n_snapshots,
            mean_delta_g=0.0,
            std_delta_g=0.0,
            min_delta_g=0.0,
            max_delta_g=0.0,
            error=f"Complex PDB file not found: {pdb_path}",
        )

    # 1. 验证 OpenMM Python 解释器 (不执行 .resolve() 防止脱离 venv)
    py_bin = Path(openmm_python or DEFAULT_OPENMM_PYTHON)
    if not py_bin.exists():
        return EnsembleMDResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            receptor_chain="",
            peptide_chain="",
            length_ns=length_ns,
            n_snapshots=n_snapshots,
            mean_delta_g=0.0,
            std_delta_g=0.0,
            min_delta_g=0.0,
            max_delta_g=0.0,
            error=f"OpenMM Python interpreter not found: {py_bin}",
        )

    # 2. 准备输出目录与文件
    if out_dir:
        work_dir = Path(out_dir).resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="ensemble_md_"))

    out_json = work_dir / "ensemble_md_results.json"
    worker_script = DEFAULT_WORKER_SCRIPT.resolve()

    # 3. 隔离子进程环境（清除 uv/主环境污染）
    sub_env = os.environ.copy()
    sub_env.pop("PYTHONPATH", None)
    sub_env.pop("PYTHONHOME", None)
    sub_env["VIRTUAL_ENV"] = str(py_bin.parent.parent)
    sub_env["PATH"] = f"{py_bin.parent}:{sub_env.get('PATH', '')}"

    cmd = [
        str(py_bin),
        str(worker_script),
        "--complex-pdb",
        str(pdb_path),
        "--out-dir",
        str(work_dir),
        "--output-json",
        str(out_json),
        "--length-ns",
        str(length_ns),
        "--n-snapshots",
        str(n_snapshots),
        "--gpu-id",
        str(gpu_id),
        "--dt-fs",
        str(dt_fs),
    ]
    if receptor_chain:
        cmd.extend(["--rec-chain", str(receptor_chain)])
    if peptide_chain:
        cmd.extend(["--pep-chain", str(peptide_chain)])

    logger.info("Executing Ensemble MD worker on GPU %d (length: %.2f ns)...", gpu_id, length_ns)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
        env=sub_env,
    )

    if proc.returncode != 0:
        logger.error("Ensemble MD worker failed with return code %d: %s", proc.returncode, proc.stderr)
        return EnsembleMDResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            receptor_chain=receptor_chain or "",
            peptide_chain=peptide_chain or "",
            length_ns=length_ns,
            n_snapshots=n_snapshots,
            mean_delta_g=0.0,
            std_delta_g=0.0,
            min_delta_g=0.0,
            max_delta_g=0.0,
            error=f"Worker exit {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}",
            elapsed_seconds=round(time.time() - t_start, 2),
        )

    if not out_json.exists():
        return EnsembleMDResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            receptor_chain=receptor_chain or "",
            peptide_chain=peptide_chain or "",
            length_ns=length_ns,
            n_snapshots=n_snapshots,
            mean_delta_g=0.0,
            std_delta_g=0.0,
            min_delta_g=0.0,
            max_delta_g=0.0,
            error=f"Expected output file not found: {out_json}",
            elapsed_seconds=round(time.time() - t_start, 2),
        )

    with open(out_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    elapsed_total = round(time.time() - t_start, 2)
    return EnsembleMDResult(
        ok=True,
        complex_name=data.get("complex_name", str(pdb_path.stem)),
        receptor_chain=data.get("receptor_chain", ""),
        peptide_chain=data.get("peptide_chain", ""),
        length_ns=data.get("length_ns", length_ns),
        n_snapshots=data.get("n_snapshots", n_snapshots),
        mean_delta_g=data.get("mean_delta_g", 0.0),
        std_delta_g=data.get("std_delta_g", 0.0),
        min_delta_g=data.get("min_delta_g", 0.0),
        max_delta_g=data.get("max_delta_g", 0.0),
        delta_g_trajectory=data.get("delta_g_trajectory", []),
        mean_pep_rmsd=data.get("mean_pep_rmsd", 0.0),
        final_pep_rmsd=data.get("final_pep_rmsd", 0.0),
        pep_rmsd_trajectory=data.get("pep_rmsd_trajectory", []),
        is_stable_binder=data.get("is_stable_binder", False),
        ns_per_day=data.get("ns_per_day", 0.0),
        production_dcd=data.get("production_dcd", ""),
        solvated_pdb=data.get("solvated_pdb", ""),
        simulation_log=data.get("simulation_log", ""),
        result_json=str(out_json),
        elapsed_seconds=elapsed_total,
    )
