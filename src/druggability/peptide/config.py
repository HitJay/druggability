"""
bbbkit.peptide.config — ESM-2 权重路径解析与（可选）自动下载

权重解析优先级（``resolve_ckpt``）：
  1. 显式传入的路径参数
  2. 环境变量 ``ESM2_CKPT``
  3. bbbkit 模型目录 ``~/.cache/bbbkit/models/<model>.pt``（或 ``BBBKIT_MODEL_DIR``）
  4. fair-esm / torch hub 缓存 ``~/.cache/torch/hub/checkpoints/<model>.pt``

本环境 HuggingFace 常不可达，但 fair-esm 的 Facebook CDN 可达；
``ensure_ckpt`` 会在缺失时用 curl 从该 CDN 下载到 bbbkit 模型目录。
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# 默认基座：150M（对短肽足够，比 650M 快约 4 倍）
DEFAULT_MODEL = "esm2_t30_150M_UR50D"

# fair-esm 权重 CDN（HuggingFace 被墙时仍可达）
FAIR_ESM_CDN = "https://dl.fbaipublicfiles.com/fair-esm/models"

# 已知 fair-esm 模型（embedding 维度仅供参考/校验）
KNOWN_MODELS = {
    "esm2_t6_8M_UR50D": 320,
    "esm2_t12_35M_UR50D": 480,
    "esm2_t30_150M_UR50D": 640,
    "esm2_t33_650M_UR50D": 1280,
}


def model_dir() -> Path:
    """bbbkit 权重目录（可用 BBBKIT_MODEL_DIR 覆盖）。"""
    d = Path(os.environ.get("BBBKIT_MODEL_DIR",
                            Path.home() / ".cache" / "bbbkit" / "models"))
    return d


def _candidates(model: str) -> list[Path]:
    return [
        model_dir() / f"{model}.pt",
        Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / f"{model}.pt",
    ]


def resolve_ckpt(ckpt: str | os.PathLike | None = None,
                 model: str = DEFAULT_MODEL) -> str | None:
    """返回已存在的权重路径，找不到则 None（调用方可选择 ensure_ckpt 下载）。"""
    if ckpt and Path(ckpt).is_file():
        return str(ckpt)
    env = os.environ.get("ESM2_CKPT")
    if env and Path(env).is_file():
        return env
    for c in _candidates(model):
        if c.is_file():
            return str(c)
    return None


def ensure_ckpt(ckpt: str | os.PathLike | None = None,
                model: str = DEFAULT_MODEL,
                auto_download: bool = True,
                timeout: int = 1200) -> str:
    """确保权重可用并返回其路径；缺失时（默认）从 fair-esm CDN 下载。

    Raises
    ------
    FileNotFoundError
        当权重缺失且 ``auto_download=False`` 或下载失败时。
    """
    found = resolve_ckpt(ckpt, model)
    if found:
        return found

    if not auto_download:
        raise FileNotFoundError(
            f"找不到 ESM-2 权重 '{model}.pt'。请设置 ESM2_CKPT 指向本地权重，"
            f"或运行 `bbbkit peptide download-weights` 自动下载。")

    if model not in KNOWN_MODELS:
        raise FileNotFoundError(
            f"未知模型 '{model}'，无法自动下载。已知：{list(KNOWN_MODELS)}")

    dest = model_dir() / f"{model}.pt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{FAIR_ESM_CDN}/{model}.pt"
    # 用 curl（系统 CA；本环境 Python ssl 因企业自签根证书会失败）
    out = subprocess.run(
        ["curl", "-fL", "--connect-timeout", "10", "-m", str(timeout),
         "-o", str(dest), url],
        capture_output=True, text=True)
    if out.returncode != 0 or not dest.is_file() or dest.stat().st_size < 1_000_000:
        if dest.exists():
            dest.unlink(missing_ok=True)
        raise FileNotFoundError(
            f"从 fair-esm CDN 下载 '{model}' 失败（curl {out.returncode}）。\n"
            f"可手动下载：curl -L -o {dest} {url}")
    return str(dest)
