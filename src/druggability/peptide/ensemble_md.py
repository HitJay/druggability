"""
druggability.peptide.ensemble_md — GPU 加速短轨迹动力学系综 MM/GBSA 评估模块

核心物理优势与 P2 特性:
- 彻底解决静态单构象 MM/GBSA 在多肽点突变上的“未松弛空洞伪影” (Void Penalty Artifact)；
- 在显式 TIP3P 水盒 + 0.15 M NaCl 离子环境下，利用 NVIDIA A100 GPU 进行全原子平衡与生产采样；
- [P2] 残基级相互作用能分解 (Per-Residue Energy Decomposition):
    精确测定多肽每个氨基酸对受体的物理吸引能与位阻排斥能 (vdW + 静电)；
- [P2] 动态氢键网络持久度谱 (Dynamic H-Bond Lifetime / Persistence %):
    精确追踪多肽-受体结合界面的强氢键锚点与瞬态接触；
- 提取平衡轨迹系综快照 (Snapshots)，在 Amber14SB + GBn2 力场下计算系综时间平均值:
    <ΔG_bind> = <E_complex> - <E_receptor> - <E_peptide> ± σ
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

DEFAULT_OPENMM_PYTHON = Path(
    os.getenv(
        "OPENMM_PYTHON",
        "/data/user/QYJI/micromamba/envs/openfe-md/bin/python",
    )
)
DEFAULT_WORKER_SCRIPT = Path(__file__).parent / "ensemble_md_worker.py"


@dataclass
class ResidueDecompositionEntry:
    """多肽单残基在动力学中的平均物理相互作用能贡献"""

    res_label: str  # e.g., 'TYR2', 'GLN4'
    res_seq: int
    res_name: str
    mean_energy_kcal_mol: float
    std_energy_kcal_mol: float
    role: str  # e.g., 'Major Interaction Anchor', 'Strong Contributor', 'Solvent-Exposed'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HBondPersistenceEntry:
    """界面动态氢键持久度条目"""

    donor: str
    acceptor: str
    frame_count: int
    total_frames: int
    persistence_pct: float
    classification: str  # Strong / Persistent (>=50%), Moderate (20-50%), Transient (<20%)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    per_residue_decomposition: list[ResidueDecompositionEntry] = field(default_factory=list)
    hbond_persistence: list[HBondPersistenceEntry] = field(default_factory=list)
    is_stable_binder: bool = False
    ns_per_day: float = 0.0
    production_dcd: str = ""
    solvated_pdb: str = ""
    simulation_log: str = ""
    result_json: str = ""
    elapsed_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["per_residue_decomposition"] = [r.to_dict() for r in self.per_residue_decomposition]
        data["hbond_persistence"] = [h.to_dict() for h in self.hbond_persistence]
        return data

    def to_df(self):
        """转为 pandas DataFrame"""
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
            f"### Short-MD Ensemble MM/GBSA & Dynamic Decomposition: `{self.complex_name}`",
            rf"- **Ensemble Binding Free Energy ($\langle \Delta G_\text{{bind}} \rangle$)**: **`{self.mean_delta_g:.2f} ± {self.std_delta_g:.2f} kcal/mol`**",
            f"- **Trajectory Energy Range**: `[{self.min_delta_g:.2f}, {self.max_delta_g:.2f}] kcal/mol` across **{self.n_snapshots} snapshots**",
            f"- **Peptide Backbone RMSD**: Mean = **`{self.mean_pep_rmsd:.2f} Å`**, Final = **`{self.final_pep_rmsd:.2f} Å`**",
            f"- **Binding Assessment**: {stability_badge}",
            f"- **Simulation Sampling**: `{self.length_ns:.2f} ns` explicit TIP3P solvent (Speed: **`{self.ns_per_day:.1f} ns/day`**)",
            f"- **Chains Profile**: Receptor = `{self.receptor_chain}`, Peptide = `{self.peptide_chain}`",
        ]

        if self.per_residue_decomposition:
            lines.extend([
                "",
                "#### 1. Per-Residue Dynamic Interaction Energy Decomposition",
                "| Residue | Mean Energy (kcal/mol) | Fluctuations (±σ) | Interaction Role |",
                "| :---: | :---: | :---: | :--- |",
            ])
            for r in self.per_residue_decomposition:
                badge = r.role
                if "Anchor" in r.role or "Major" in r.role:
                    badge = f"🔥 **{r.role}**"
                elif "Strong" in r.role:
                    badge = f"⚡ **{r.role}**"
                lines.append(
                    f"| `{r.res_label}` | **`{r.mean_energy_kcal_mol:6.2f}`** | ±{r.std_energy_kcal_mol:4.2f} | {badge} |"
                )

        if self.hbond_persistence:
            lines.extend([
                "",
                "#### 2. Dynamic Hydrogen Bond Persistence Network (Top Interfaces)",
                "| Donor Atom | Acceptor Atom | Persistence (%) | Classification |",
                "| :--- | :--- | :---: | :--- |",
            ])
            for h in self.hbond_persistence[:8]:
                badge = h.classification
                if "Strong" in h.classification:
                    badge = f"💎 **{h.classification}**"
                lines.append(
                    f"| `{h.donor}` | `{h.acceptor}` | **{h.persistence_pct:.1f}%** | {badge} |"
                )

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
    运行显式水短轨迹平衡动力学并计算系综平均 MM/GBSA 结合自由能 (含残基级能量分解与动态氢键网络)。
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

    if out_dir:
        work_dir = Path(out_dir).resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="ensemble_md_"))

    out_json = work_dir / "ensemble_md_results.json"
    worker_script = DEFAULT_WORKER_SCRIPT.resolve()

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

    # Parse P2 entries
    decomp_entries = [
        ResidueDecompositionEntry(
            res_label=item["res_label"],
            res_seq=item["res_seq"],
            res_name=item["res_name"],
            mean_energy_kcal_mol=item["mean_energy_kcal_mol"],
            std_energy_kcal_mol=item["std_energy_kcal_mol"],
            role=item["role"],
        )
        for item in data.get("per_residue_decomposition", [])
    ]

    hbond_entries = [
        HBondPersistenceEntry(
            donor=item["donor"],
            acceptor=item["acceptor"],
            frame_count=item["frame_count"],
            total_frames=item["total_frames"],
            persistence_pct=item["persistence_pct"],
            classification=item["classification"],
        )
        for item in data.get("hbond_persistence", [])
    ]

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
        per_residue_decomposition=decomp_entries,
        hbond_persistence=hbond_entries,
        is_stable_binder=data.get("is_stable_binder", False),
        ns_per_day=data.get("ns_per_day", 0.0),
        production_dcd=data.get("production_dcd", ""),
        solvated_pdb=data.get("solvated_pdb", ""),
        simulation_log=data.get("simulation_log", ""),
        result_json=str(out_json),
        elapsed_seconds=elapsed_total,
    )
