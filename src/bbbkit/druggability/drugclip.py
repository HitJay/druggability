"""
bbbkit.druggability.drugclip — DrugCLIP AI 虚拟筛选 Agent Tool Wrapper

本模块将 NeurIPS 2023 开源模型 DrugCLIP 封装为 Druggability Agent 可直接调用的标准化工具：
- 支持直接输入 PDB 文件（自动根据配体或空间坐标截取 pocket 残基原子）
- 支持输入既有 pocket.lmdb
- 自动调度专属环境 (/data/user/QYJI/venvs/drugclip/bin/python) 进行 GPU 加速推理
- 产出结构化 DrugCLIPResult / DrugCLIPHit，无缝衔接后续 Vina 对接与 Boltz-2 验证
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)

# ── 默认运行路径与资产配置 (支持环境变量覆盖) ───────────────────────────
DEFAULT_DRUGCLIP_PYTHON = Path(
    os.getenv("DRUGCLIP_PYTHON", "/data/user/QYJI/venvs/drugclip/bin/python")
)
DEFAULT_DRUGCLIP_REPO = Path(
    os.getenv(
        "DRUGCLIP_REPO",
        "/das/user/QYJI/druggability/output/2026-07-02/drugclip_install_probe/DrugCLIP",
    )
)
DEFAULT_CHECKPOINT = Path(
    os.getenv(
        "DRUGCLIP_CHECKPOINT",
        "/das/user/QYJI/druggability/output/2026-07-02/drugclip_install_probe/checkpoints/drugclip_data/checkpoint_best.pt",
    )
)
DEFAULT_MOL_LMDB = Path(
    os.getenv(
        "DRUGCLIP_MOL_LMDB",
        "/das/user/QYJI/druggability/output/2026-07-02/drugclip_install_probe/checkpoints/drugclip_data/retrieval/mols.lmdb",
    )
)
DEFAULT_WORKER_SCRIPT = Path(__file__).parent / "drugclip_worker.py"


@dataclass
class DrugCLIPHit:
    """单个命中化合物记录"""

    rank: int
    smi: str
    score: float
    mol_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DrugCLIPResult:
    """DrugCLIP 虚拟筛选结果集合"""

    ok: bool
    pocket_name: str
    hits: list[DrugCLIPHit] = field(default_factory=list)
    top_k: int = 0
    elapsed_seconds: float = 0.0
    checkpoint: str = ""
    mol_lmdb: str = ""
    pocket_lmdb: str = ""
    result_json: str = ""
    result_tsv: str = ""
    error: str | None = None

    @property
    def hit_count(self) -> int:
        return len(self.hits)

    def top(self, n: int = 10) -> list[DrugCLIPHit]:
        """获取前 N 个命中化合物"""
        return self.hits[:n]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["hit_count"] = self.hit_count
        return data

    def to_df(self):
        """转为 pandas.DataFrame 格式（需环境中已安装 pandas）"""
        import pandas as pd

        return pd.DataFrame([h.to_dict() for h in self.hits])

    def summary_markdown(self, top_n: int = 10) -> str:
        """生成供 Agent 汇报与总结展示的 Markdown 表格"""
        if not self.ok:
            return f"**DrugCLIP Virtual Screening Failed**: {self.error}"

        lines = [
            f"### DrugCLIP Virtual Screening Summary: `{self.pocket_name}`",
            f"- **Status**: {'Success' if self.ok else 'Failed'}",
            f"- **Target Pocket**: `{self.pocket_name}`",
            f"- **Retrieved Hits**: {self.hit_count} (requested top {self.top_k})",
            f"- **Elapsed Time**: {self.elapsed_seconds:.2f}s",
            f"- **Database**: `{Path(self.mol_lmdb).name}`",
            "",
            "| Rank | Score | SMILES |",
            "| :---: | :---: | :--- |",
        ]
        for h in self.top(top_n):
            smi_display = h.smi if len(h.smi) <= 60 else f"{h.smi[:57]}..."
            lines.append(f"| {h.rank} | {h.score:.4f} | `{smi_display}` |")

        if self.hit_count > top_n:
            lines.append(f"\n*Showing top {top_n} of {self.hit_count} candidates.*")
        return "\n".join(lines)


# ── 口袋解析与 LMDB 生成函数 ──────────────────────────────────────────


def parse_pdb_atoms(pdb_path: str | Path) -> tuple[list[str], list[list[float]], list[str]]:
    """
    轻量无依赖解析 PDB 文件中的原子名称、三维坐标及残基标识。

    Returns
    -------
    tuple of (atoms, coords, residues)
        - atoms: 元素或原子名列表 (如 ['N', 'CA', 'C', 'O', ...])
        - coords: 坐标列表 [[x, y, z], ...]
        - residues: 残基唯一标识列表 (如 ['A123_LEU', ...])
    """
    atoms: list[str] = []
    coords: list[list[float]] = []
    residues: list[str] = []

    with open(pdb_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith(("ATOM  ", "HETATM")):
                atom_name = line[12:16].strip()
                res_name = line[17:20].strip()
                chain_id = line[21:22].strip() or "A"
                res_seq = line[22:26].strip()
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                except ValueError:
                    continue
                atoms.append(atom_name)
                coords.append([x, y, z])
                residues.append(f"{chain_id}{res_seq}_{res_name}")

    if not atoms:
        raise ValueError(f"No ATOM or HETATM records found in PDB file: {pdb_path}")

    return atoms, coords, residues


def extract_pocket_from_pdb(
    pdb_path: str | Path,
    *,
    ligand_pdb: str | Path | None = None,
    center: tuple[float, float, float] | Sequence[float] | None = None,
    radius: float = 8.0,
    pocket_name: str | None = None,
) -> dict[str, Any]:
    """
    从受体或复合物 PDB 中提取结合口袋原子与坐标。

    Parameters
    ----------
    pdb_path : str | Path
        受体结构或口袋结构 PDB 路径。
    ligand_pdb : str | Path | None
        参考配体结构 PDB 路径。若提供，则选取距离配体任一原子 <= radius 距离内的全部残基原子。
    center : tuple of 3 floats | None
        口袋几何中心 (x, y, z)。若未提供 ligand_pdb 且提供了 center，则选取以此中心为球心、radius 为半径的残基原子。
    radius : float, default 8.0
        截取口袋的半径阈值（Å）。
    pocket_name : str | None
        口袋标识名称，默认采用 pdb_path 的 stem。

    Returns
    -------
    dict
        含 'pocket', 'pocket_atoms', 'pocket_coordinates' 的字典结构。
    """
    p_path = Path(pdb_path).resolve()
    if not p_path.exists():
        raise FileNotFoundError(f"Receptor PDB not found: {p_path}")

    name = pocket_name or p_path.stem
    rec_atoms, rec_coords, rec_residues = parse_pdb_atoms(p_path)

    if ligand_pdb is not None:
        l_path = Path(ligand_pdb).resolve()
        if not l_path.exists():
            raise FileNotFoundError(f"Ligand PDB not found: {l_path}")
        _, lig_coords, _ = parse_pdb_atoms(l_path)

        pocket_res_set = set()
        for r_idx, (rx, ry, rz) in enumerate(rec_coords):
            res_id = rec_residues[r_idx]
            if res_id in pocket_res_set:
                continue
            for lx, ly, lz in lig_coords:
                dist_sq = (rx - lx) ** 2 + (ry - ly) ** 2 + (rz - lz) ** 2
                if dist_sq <= (radius**2):
                    pocket_res_set.add(res_id)
                    break

        selected_atoms = [
            atom for atom, res in zip(rec_atoms, rec_residues) if res in pocket_res_set
        ]
        selected_coords = [
            coord for coord, res in zip(rec_coords, rec_residues) if res in pocket_res_set
        ]

    elif center is not None:
        cx, cy, cz = float(center[0]), float(center[1]), float(center[2])
        pocket_res_set = set()
        for r_idx, (rx, ry, rz) in enumerate(rec_coords):
            res_id = rec_residues[r_idx]
            if res_id in pocket_res_set:
                continue
            dist_sq = (rx - cx) ** 2 + (ry - cy) ** 2 + (rz - cz) ** 2
            if dist_sq <= (radius**2):
                pocket_res_set.add(res_id)

        selected_atoms = [
            atom for atom, res in zip(rec_atoms, rec_residues) if res in pocket_res_set
        ]
        selected_coords = [
            coord for coord, res in zip(rec_coords, rec_residues) if res in pocket_res_set
        ]

    else:
        # 直接使用传入 PDB 的所有原子作为口袋（如 fpocket 提取好的口袋文件）
        selected_atoms = rec_atoms
        selected_coords = rec_coords

    return {
        "pocket": name,
        "pocket_atoms": selected_atoms,
        "pocket_coordinates": selected_coords,
    }


def write_pocket_lmdb(pocket_data: dict[str, Any], output_path: str | Path) -> Path:
    """
    将口袋字典序列化并写入符合 DrugCLIP 规范的 LMDB 文件。
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 优先导入 lmdb
    try:
        import lmdb
    except ImportError:
        # 若主环境无 lmdb，使用轻量 python 调用 drugclip venv 写入
        worker_code = (
            f"import lmdb, pickle; "
            f"env = lmdb.open(r'{out_file}', subdir=False, map_size=10485760); "
            f"txn = env.begin(write=True); "
            f"data = {repr(pocket_data)}; "
            f"txn.put(b'0', pickle.dumps(data)); "
            f"txn.commit(); env.close()"
        )
        res = subprocess.run(
            [str(DEFAULT_DRUGCLIP_PYTHON), "-c", worker_code],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(f"Failed to write pocket LMDB via worker: {res.stderr}")
        return out_file

    env = lmdb.open(str(out_file), subdir=False, map_size=10485760)
    with env.begin(write=True) as txn:
        txn.put(b"0", pickle.dumps(pocket_data))
    env.close()
    return out_file


# ── 核心调度函数 ───────────────────────────────────────────────────────


def screen_drugclip(
    pocket_input: str | Path | dict[str, Any],
    *,
    mol_lmdb: str | Path | None = None,
    ligand_pdb: str | Path | None = None,
    center: tuple[float, float, float] | None = None,
    radius: float = 8.0,
    top_k: int = 100,
    device_id: int = 0,
    output_dir: str | Path | None = None,
    checkpoint: str | Path | None = None,
    drugclip_repo: str | Path | None = None,
    drugclip_python: str | Path | None = None,
    batch_size: int = 8,
    timeout: int = 1800,
) -> DrugCLIPResult:
    """
    运行 DrugCLIP AI 虚拟筛选，检索与靶点口袋表征匹配的 Top-K 候选分子。

    Parameters
    ----------
    pocket_input : str | Path | dict
        口袋定义：
        - 若为 .pdb 路径：自动解析（可结合 ligand_pdb 或 center 截取口袋）；
        - 若为 .lmdb 路径：直接作为 pocket LMDB 文件；
        - 若为 dict：包含 'pocket', 'pocket_atoms', 'pocket_coordinates'。
    mol_lmdb : str | Path | None
        分子库 LMDB 路径。默认使用官方下载的 294万 分子库 (mols.lmdb)。
    ligand_pdb : str | Path | None
        参考配体 PDB（当 pocket_input 为受体 PDB 时有效）。
    center : tuple of floats | None
        口袋空间中心坐标 (x, y, z)。
    radius : float, default 8.0
        口袋截取球半径。
    top_k : int, default 100
        返回得分最高的前 K 个候选化合物。
    device_id : int, default 0
        CUDA 设备编号。
    output_dir : str | Path | None
        结果与中间缓存输出目录。默认创建独立临时目录。
    checkpoint : str | Path | None
        模型权重路径，默认使用已下载的 checkpoint_best.pt。
    drugclip_repo : str | Path | None
        DrugCLIP 源码目录。
    drugclip_python : str | Path | None
        drugclip 虚拟环境的 Python 解释器路径。
    batch_size : int, default 8
        推断 batch 大小。
    timeout : int, default 1800
        子进程执行超时时间（秒）。

    Returns
    -------
    DrugCLIPResult
        包含命中列表、打分、统计耗时及输出文件路径的结构化对象。
    """
    start_time = time.time()

    # 1. 验证关键资产与环境路径（注意：虚拟环境 bin/python 不能执行 .resolve()，否则会丢失 pyvenv.cfg 关联）
    py_bin = Path(drugclip_python or DEFAULT_DRUGCLIP_PYTHON)
    repo_dir = Path(drugclip_repo or DEFAULT_DRUGCLIP_REPO).resolve()
    ckpt_path = Path(checkpoint or DEFAULT_CHECKPOINT).resolve()
    mols_path = Path(mol_lmdb or DEFAULT_MOL_LMDB).resolve()

    if not py_bin.exists():
        raise FileNotFoundError(f"DrugCLIP python interpreter not found: {py_bin}")
    if not repo_dir.exists():
        raise FileNotFoundError(f"DrugCLIP repository not found: {repo_dir}")
    if not ckpt_path.exists():
        raise FileNotFoundError(f"DrugCLIP checkpoint not found: {ckpt_path}")
    if not mols_path.exists():
        raise FileNotFoundError(f"Molecules LMDB database not found: {mols_path}")

    # 2. 准备工作输出目录
    if output_dir:
        work_dir = Path(output_dir).resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
        cleanup_temp = False
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="drugclip_run_"))
        cleanup_temp = False

    emb_dir = work_dir / "emb_cache"
    emb_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "drugclip_results.json"
    out_tsv = work_dir / "drugclip_results.tsv"

    # 3. 准备口袋 LMDB
    pocket_name = "target_pocket"
    pocket_lmdb_file = work_dir / "pocket.lmdb"

    try:
        if isinstance(pocket_input, dict):
            pocket_name = pocket_input.get("pocket", "target_pocket")
            write_pocket_lmdb(pocket_input, pocket_lmdb_file)
        elif isinstance(pocket_input, (str, Path)):
            p_in = Path(pocket_input).resolve()
            if not p_in.exists():
                raise FileNotFoundError(f"Pocket input path does not exist: {p_in}")

            if p_in.suffix.lower() == ".lmdb":
                pocket_lmdb_file = p_in
                pocket_name = p_in.stem
            elif p_in.suffix.lower() in [".pdb", ".ent"]:
                pocket_name = p_in.stem
                p_data = extract_pocket_from_pdb(
                    p_in,
                    ligand_pdb=ligand_pdb,
                    center=center,
                    radius=radius,
                    pocket_name=pocket_name,
                )
                write_pocket_lmdb(p_data, pocket_lmdb_file)
            else:
                raise ValueError(f"Unsupported pocket file format: {p_in.suffix}")
        else:
            raise TypeError(f"Invalid pocket_input type: {type(pocket_input)}")

        # 4. 构建并执行子进程（清理父环境环境变量，避免 uv/主环境 venv 污染）
        sub_env = os.environ.copy()
        sub_env.pop("PYTHONPATH", None)
        sub_env.pop("PYTHONHOME", None)
        sub_env["VIRTUAL_ENV"] = str(py_bin.parent.parent)
        sub_env["PATH"] = f"{py_bin.parent}:{sub_env.get('PATH', '')}"

        worker_script = DEFAULT_WORKER_SCRIPT.resolve()
        cmd = [
            str(py_bin),
            str(worker_script),
            "--drugclip-repo",
            str(repo_dir),
            "--checkpoint",
            str(ckpt_path),
            "--pocket-lmdb",
            str(pocket_lmdb_file),
            "--mol-lmdb",
            str(mols_path),
            "--emb-dir",
            str(emb_dir),
            "--output-json",
            str(out_json),
            "--top-k",
            str(top_k),
            "--device-id",
            str(device_id),
            "--batch-size",
            str(batch_size),
        ]

        logger.info("Executing DrugCLIP worker on device %d...", device_id)
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
            logger.error("DrugCLIP worker failed with return code %d: %s", proc.returncode, proc.stderr)
            return DrugCLIPResult(
                ok=False,
                pocket_name=pocket_name,
                top_k=top_k,
                elapsed_seconds=round(time.time() - start_time, 3),
                checkpoint=str(ckpt_path),
                mol_lmdb=str(mols_path),
                pocket_lmdb=str(pocket_lmdb_file),
                error=f"Worker exit {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}",
            )

        # 5. 读取并格式化结果
        if not out_json.exists():
            return DrugCLIPResult(
                ok=False,
                pocket_name=pocket_name,
                top_k=top_k,
                elapsed_seconds=round(time.time() - start_time, 3),
                error=f"Expected output file not found: {out_json}",
            )

        with open(out_json, "r", encoding="utf-8") as f:
            raw_res = json.load(f)

        hits = [
            DrugCLIPHit(
                rank=item["rank"],
                smi=item["smi"],
                score=item["score"],
            )
            for item in raw_res.get("hits", [])
        ]

        elapsed = round(time.time() - start_time, 3)
        return DrugCLIPResult(
            ok=True,
            pocket_name=pocket_name,
            hits=hits,
            top_k=top_k,
            elapsed_seconds=elapsed,
            checkpoint=str(ckpt_path),
            mol_lmdb=str(mols_path),
            pocket_lmdb=str(pocket_lmdb_file),
            result_json=str(out_json),
            result_tsv=str(out_tsv),
        )

    except Exception as e:
        logger.exception("Error during DrugCLIP screen: %s", e)
        return DrugCLIPResult(
            ok=False,
            pocket_name=pocket_name,
            top_k=top_k,
            elapsed_seconds=round(time.time() - start_time, 3),
            error=str(e),
        )
