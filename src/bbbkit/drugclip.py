"""
bbbkit.drugclip — DrugCLIP 虚拟筛选（蛋白口袋 ↔ 小分子 对比学习打分）

DrugCLIP（NeurIPS 2023, Gao et al.）把蛋白口袋与小分子编码进共享向量空间，
用对比学习做超高通量虚拟筛选 / 蛋白-配体结合打分，远快于传统分子对接。
代码: https://github.com/bowen-gao/DrugCLIP  ，基于 Uni-Mol / Uni-Core 框架。

与 bbbkit.boltz（经 BioLib 云端）不同，DrugCLIP 是本地仓库部署：需要 Python 3.8 +
rdkit + Uni-Core + torch。本模块不重复实现模型，而是封装「环境部署 / 推理调用 /
权重获取」三件事，把官方 retrieval.sh / test.sh 改造成可在 CPU 上运行的 Python API。

部署:
    一键脚本（CPU，免 conda/GPU）::

        bash scripts/setup_drugclip_env.sh

    或调用本模块::

        from bbbkit.drugclip import setup_environment
        setup_environment(force_cuda=False)   # 建 venv + 装 torch/unicore/rdkit + 克隆仓库

环境就绪后，权重 + 示例数据需从 Google Drive 手动获取（部分网络屏蔽 drive.google.com）:
    https://drive.google.com/drive/folders/1zW1MGpgunynFxTKXC2Q4RgWxZmg6CInV
    → checkpoint_best.pt, mols.lmdb, pocket.lmdb 放入 DrugCLIP/

推理:
    from bbbkit.drugclip import run_retrieval, run_test, ensure_environment
    ensure_environment()                # 激活 venv（同一进程内设置 sys.path）
    run_retrieval(weight="checkpoint_best.pt")  # CPU 虚拟筛选，结果落 DrugCLIP/test/

注意:
    - 官方脚本带 ``--fp16`` 需 GPU；本模块默认 CPU，已去掉 ``--fp16``、调小 batch。
    - 真正推理需权重文件，缺失时会清晰报错指引下载。
    - 训练（drugclip.sh）需 GPU + Uni-Mol 预训练权重，本模块不封装训练。
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Sequence

# ── 路径约定 ────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[2]  # 仓库根
DRUGCLIP_DIR = Path(os.environ.get("DRUGCLIP_DIR", _ROOT / "DrugCLIP"))
DRUGCLIP_VENV = Path(os.environ.get("DRUGCLIP_VENV", _ROOT / "drugclip-venv"))
UNICORE_DIR = Path(os.environ.get("UNICORE_DIR", _ROOT / "Uni-Core"))
SETUP_SCRIPT = _ROOT / "scripts" / "setup_drugclip_env.sh"
RUN_SCRIPT = _ROOT / "scripts" / "run_drugclip_cpu.sh"

DEFAULT_WEIGHT = DRUGCLIP_DIR / "checkpoint_best.pt"


# ── 环境部署 ────────────────────────────────────────────────────────
def setup_environment(*, force_cuda: bool = False) -> Path:
    """一键部署 DrugCLIP 运行环境（CPU 优先，免 conda / GPU）。

    内部调用 ``scripts/setup_drugclip_env.sh``：用 uv 建 Python 3.8 venv，
    装 CPU torch + rdkit + Uni-Core（禁用 CUDA ext）+ 克隆 DrugCLIP 仓库。

    Args:
        force_cuda: True 时装 CUDA 版 torch（有 GPU 的机器）。

    Returns:
        venv 路径。
    """
    env = dict(os.environ, FORCE_CUDA="1" if force_cuda else "0")
    _run([str(SETUP_SCRIPT)], env=env, cwd=str(_ROOT))
    return DRUGCLIP_VENV


def is_environment_ready() -> bool:
    """环境是否已部署（venv + DrugCLIP 仓库 + unicore 均就绪）。"""
    py = DRUGCLIP_VENV / "bin" / "python"
    if not (py.exists() and DRUGCLIP_DIR.is_dir()):
        return False
    # 顺手验证 unicore 可导入
    r = subprocess.run(
        [str(py), "-c", "import unicore, torch, rdkit, lmdb"],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def ensure_environment(*, force_cuda: bool = False) -> Path:
    """确保环境就绪；未部署则自动调用 setup_environment()。"""
    if not is_environment_ready():
        setup_environment(force_cuda=force_cuda)
    return DRUGCLIP_VENV


def _venv_python() -> str:
    """返回 venv 内的 python 路径，用于直接调用推理。"""
    py = DRUGCLIP_VENV / "bin" / "python"
    if not py.exists():
        raise RuntimeError(
            f"DrugCLIP 环境未部署: {py} 不存在。请先运行 "
            "from bbbkit.drugclip import setup_environment; setup_environment()"
        )
    return str(py)


# ── 权重 / 数据 ─────────────────────────────────────────────────────
GDRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1zW1MGpgunynFxTKXC2Q4RgWxZmg6CInV"
)


def check_weights(weight: str | Path = DEFAULT_WEIGHT) -> Path:
    """校验权重文件存在，否则清晰报错并给出下载指引。"""
    weight = Path(weight)
    if not weight.is_absolute():
        weight = DRUGCLIP_DIR / weight
    if not weight.exists():
        raise FileNotFoundError(
            f"DrugCLIP 权重缺失: {weight}\n"
            f"请从 Google Drive 下载 checkpoint_best.pt: {GDRIVE_FOLDER_URL}\n"
            "放入 DrugCLIP/ 后重试。（部分网络屏蔽 drive.google.com，需在可访问处下载）"
        )
    return weight


# ── 推理 ────────────────────────────────────────────────────────────
def run_retrieval(
    *,
    weight: str | Path = DEFAULT_WEIGHT,
    mols_lmdb: str | Path | None = None,
    pocket_lmdb: str | Path | None = None,
    results_path: str | Path = "test",
    batch_size: int = 2,
    max_pocket_atoms: int = 256,
    extra_args: Sequence[str] = (),
) -> Path:
    """运行 retrieval 虚拟筛选（CPU）：对口袋向量库检索匹配小分子并打分。

    对应官方 retrieval.sh，去掉 ``--fp16``、强制 CPU、调小 batch。

    Args:
        weight:         训练好的权重路径（默认 DrugCLIP/checkpoint_best.pt）。
        mols_lmdb:      待筛选分子库 LMDB（默认 DrugCLIP/mols.lmdb）。
        pocket_lmdb:    口袋库 LMDB（默认 DrugCLIP/pocket.lmdb）。
        results_path:   结果输出目录（相对 DrugCLIP_DIR）。
        batch_size:     CPU 下建议 1~4。
        max_pocket_atoms: 口袋最大原子数，retrieval 默认 256。
        extra_args:     透传给 unicore 的额外参数。

    Returns:
        结果目录 Path。
    """
    ensure_environment()
    weight = check_weights(weight)
    mol = _resolve(mols_lmdb, "mols.lmdb")
    pkt = _resolve(pocket_lmdb, "pocket.lmdb")

    cmd = [
        _venv_python(), "unimol/retrieval.py", "--user-dir", "./unimol",
        "./data", "--valid-subset", "test",
        "--results-path", str(results_path),
        "--num-workers", "0", "--ddp-backend=c10d", "--batch-size", str(batch_size),
        "--task", "drugclip", "--loss", "in_batch_softmax", "--arch", "drugclip",
        "--max-pocket-atoms", str(max_pocket_atoms), "--seed", "1",
        "--path", str(weight),
        "--log-interval", "100", "--log-format", "simple",
        "--mol-path", str(mol), "--pocket-path", str(pkt),
        "--emb-dir", "./data/emb",
        *extra_args,
    ]
    _run(cmd, cwd=str(DRUGCLIP_DIR), env=_cpu_env())
    return DRUGCLIP_DIR / results_path


def run_test(
    *,
    weight: str | Path = DEFAULT_WEIGHT,
    task: str = "PCBA",
    results_path: str | Path = "test",
    batch_size: int = 2,
    extra_args: Sequence[str] = (),
) -> Path:
    """运行 benchmark 评测（CPU）：在 DUD-E / PCBA 上算 BEDROC / EF1% / AUC。

    对应官方 test.sh，去掉 ``--fp16``、强制 CPU。

    Args:
        weight:       权重路径。
        task:         'PCBA' 或 'DUDE'。
        results_path: 结果输出目录。
        batch_size:   CPU 下建议 1~4。
        extra_args:   透传给 unicore 的额外参数。

    Returns:
        结果目录 Path。
    """
    if task not in ("PCBA", "DUDE"):
        raise ValueError("task 必须是 'PCBA' 或 'DUDE'")
    ensure_environment()
    weight = check_weights(weight)

    cmd = [
        _venv_python(), "unimol/test.py", "--user-dir", "./unimol",
        "./data", "--valid-subset", "test",
        "--results-path", str(results_path),
        "--num-workers", "0", "--ddp-backend=c10d", "--batch-size", str(batch_size),
        "--task", "drugclip", "--loss", "in_batch_softmax", "--arch", "drugclip",
        "--seed", "1",
        "--path", str(weight),
        "--log-interval", "100", "--log-format", "simple",
        "--max-pocket-atoms", "511",
        "--test-task", task,
        *extra_args,
    ]
    _run(cmd, cwd=str(DRUGCLIP_DIR), env=_cpu_env())
    return DRUGCLIP_DIR / results_path


# ── 辅助 ────────────────────────────────────────────────────────────
def _resolve(p: str | Path | None, default_name: str) -> Path:
    """解析路径：None → DrugCLIP_DIR/<default_name>；相对 → DrugCLIP_DIR 下。"""
    if p is None:
        return DRUGCLIP_DIR / default_name
    p = Path(p)
    return p if p.is_absolute() else DRUGCLIP_DIR / p


def _cpu_env() -> dict:
    """强制 CPU 的环境变量。"""
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = ""
    env.setdefault("OMP_NUM_THREADS", "4")
    return env


def _run(cmd: Sequence[str], **kw) -> None:
    """运行子进程，实时透传输出，失败抛异常。"""
    print(f"[drugclip] $ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], **kw)
    if r.returncode != 0:
        raise RuntimeError(f"命令失败 (exit={r.returncode}): {' '.join(cmd)}")


__all__ = [
    "DRUGCLIP_DIR",
    "DRUGCLIP_VENV",
    "GDRIVE_FOLDER_URL",
    "setup_environment",
    "is_environment_ready",
    "ensure_environment",
    "check_weights",
    "run_retrieval",
    "run_test",
]
