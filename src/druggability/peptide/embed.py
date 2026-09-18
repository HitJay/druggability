"""
bbbkit.peptide.embed — 可复用的 ESM-2 肽序列嵌入服务（带磁盘缓存）

核心思想："一个蛋白质语言模型基座，多个轻量任务头"。每条肽的 ESM-2 嵌入只计算
一次并缓存在磁盘（按 sha1(model:sequence) 命名），随后被所有下游任务头复用——
这样昂贵的 GPU 步骤被摊薄到 N 个下游任务上。

设计：
- torch / fair-esm 为可选依赖（`pip install bbbkit[peptide]`），未安装时给出清晰报错。
- checkpoint 路径可配置：参数 > 环境变量 ESM2_CKPT > 默认缓存目录。
- HuggingFace 在部分环境不可达；权重可经 fair-esm 的 Facebook CDN 获取后离线加载。
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import numpy as np

from . import config

logger = logging.getLogger(__name__)

# 默认 150M 模型（对短肽足够，且比 650M 快约 4 倍）
MODEL_NAME = config.DEFAULT_MODEL
_DEFAULT_CACHE = Path(os.environ.get(
    "BBBKIT_ESM_CACHE", Path.home() / ".cache" / "bbbkit" / "esm_emb"))

_MODEL = None
_ALPHABET = None
_BATCH_CONVERTER = None


def _key(seq: str) -> str:
    return hashlib.sha1(f"{MODEL_NAME}:{seq}".encode()).hexdigest()


def load_model(ckpt: str | os.PathLike | None = None,
               auto_download: bool = True):
    """加载 ESM-2 模型（懒加载，全局单例）。需要 torch + fair-esm。

    权重路径解析见 ``bbbkit.peptide.config``；缺失时默认从 fair-esm CDN 下载。
    """
    global _MODEL, _ALPHABET, _BATCH_CONVERTER
    if _MODEL is not None:
        return
    try:
        import torch
        import esm
    except ImportError as exc:  # pragma: no cover - 依赖缺失路径
        raise ImportError(
            "bbbkit.peptide 需要 torch 与 fair-esm。请安装可选依赖：\n"
            "  pip install 'bbbkit[peptide]'\n"
            f"（底层报错：{exc}）"
        ) from exc

    ckpt_path = config.ensure_ckpt(ckpt, MODEL_NAME, auto_download=auto_download)
    state = torch.load(ckpt_path, map_location="cpu")
    # 用 core 加载并跳过 contact-regression 头（embedding 用不到，且该文件常不可得）
    model, alphabet = esm.pretrained.load_model_and_alphabet_core(
        MODEL_NAME, state, regression_data=None)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _MODEL = model.to(device).eval()
    _ALPHABET = alphabet
    _BATCH_CONVERTER = alphabet.get_batch_converter()
    logger.info("ESM-2 模型已加载到 %s（权重 %s）", device, ckpt_path)


def _embed_batch(seqs: list[str], ckpt=None) -> list[np.ndarray]:
    import torch

    load_model(ckpt=ckpt)
    device = next(_MODEL.parameters()).device
    layer = _MODEL.num_layers
    data = [(f"s{i}", s) for i, s in enumerate(seqs)]
    _, _, toks = _BATCH_CONVERTER(data)
    toks = toks.to(device)
    out = []
    with torch.no_grad():
        reps = _MODEL(toks, repr_layers=[layer])["representations"][layer]
        for k, s in enumerate(seqs):
            # 对真实残基做均值池化（排除首位 BOS 与末位 EOS）
            out.append(reps[k, 1:len(s) + 1].mean(0).float().cpu().numpy())
    return out


def embed(
    sequences,
    *,
    cache_dir: str | os.PathLike | None = None,
    batch_size: int = 16,
    ckpt: str | os.PathLike | None = None,
    verbose: bool = False,
) -> np.ndarray:
    """返回 `sequences` 的 ESM-2 嵌入矩阵 (N, D)，复用磁盘缓存；仅缓存未命中走 GPU。

    Parameters
    ----------
    sequences : Iterable[str]
        肽序列（仅 20 种标准氨基酸大写字母）。
    cache_dir : path, optional
        嵌入缓存目录（默认 ``~/.cache/bbbkit/esm_emb`` 或 BBBKIT_ESM_CACHE）。
    batch_size : int
        GPU 批大小。
    ckpt : path, optional
        ESM-2 权重路径（覆盖 ESM2_CKPT）。
    """
    cdir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE
    cdir.mkdir(parents=True, exist_ok=True)
    sequences = list(sequences)
    result: list[np.ndarray | None] = [None] * len(sequences)
    todo_idx, todo_seq = [], []

    for i, s in enumerate(sequences):
        fp = cdir / (_key(s) + ".npy")
        if fp.exists():
            result[i] = np.load(fp)
        else:
            todo_idx.append(i)
            todo_seq.append(s)

    if verbose:
        logger.info("embed: %d 请求, %d 命中缓存, %d 待计算",
                    len(sequences), len(sequences) - len(todo_seq), len(todo_seq))

    for b in range(0, len(todo_seq), batch_size):
        chunk = todo_seq[b:b + batch_size]
        idxs = todo_idx[b:b + batch_size]
        for j, vec in zip(idxs, _embed_batch(chunk, ckpt=ckpt)):
            result[j] = vec
            np.save(cdir / (_key(sequences[j]) + ".npy"), vec)

    return np.vstack(result)


def cache_stats(cache_dir: str | os.PathLike | None = None) -> dict:
    cdir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE
    if not cdir.is_dir():
        return {"cached": 0, "dir": str(cdir)}
    return {"cached": len(list(cdir.glob("*.npy"))), "dir": str(cdir)}
