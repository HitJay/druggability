"""
bbbkit.peptide.predict — 端到端 BBB 通透性预测（序列 → ESM-2 → BBB 头 → P + CI）

在 B3Pred 训练集上拟合一个轻量 BBB 头（基于冻结 ESM-2 嵌入），对查询肽给出
P(BBB+) 与 bootstrap 置信区间。返回结构可直接喂给
``bbbkit.peptide.report.build_bbb_report``。

需要可选依赖（torch + fair-esm + scikit-learn，``pip install 'bbbkit[peptide]'``）
与 ESM-2 权重（路径解析见 ``bbbkit.peptide.config``；可用 ckpt= 或 ESM2_CKPT 指定）。
GPU 自动使用（``embed`` 检测 CUDA）；嵌入带磁盘缓存，重复序列只算一次。
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# B3Pred 训练集候选路径（取首个存在者）。列：sequence,label[,length]
_TRAIN_CANDIDATES = [
    "data/peptide/bbb/train.csv",
    "output/2026-06-15/peptide_esm_platform/data/bbb/train.csv",
    "output/2026-06-15/brp_bbb_prediction/data/train.csv",
]


def _find_train_csv(train_csv=None) -> Path:
    if train_csv:
        p = Path(train_csv)
        if not p.exists():
            raise FileNotFoundError(f"train_csv not found: {p}")
        return p
    for c in _TRAIN_CANDIDATES:
        if Path(c).exists():
            return Path(c)
    raise FileNotFoundError(
        "B3Pred training set not found; pass train_csv= (columns: sequence,label)."
    )


def _load_train(path: Path):
    seqs, ys = [], []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            s = (r.get("sequence") or "").strip().upper()
            lab = r.get("label", r.get("y", ""))
            if not s or lab == "":
                continue
            seqs.append(s)
            ys.append(int(float(lab)))
    return seqs, ys


def predict_bbb(
    sequences,
    *,
    names=None,
    modifications=None,
    known_routes=None,
    train_csv=None,
    cache_dir=None,
    ckpt=None,
    head_kind: str = "linear",
    n_bootstrap: int = 200,
    seed: int = 42,
    apply_protraction: bool = False,
) -> list[dict]:
    """端到端预测查询肽的 BBB 通透性。

    Parameters
    ----------
    sequences : Iterable[str]
        查询肽序列（仅 20 种标准氨基酸大写字母）。
    names / modifications / known_routes : list[str], optional
        与 sequences 对齐的元信息（用于报告标注；modification 会触发适用域判定）。
    train_csv : path, optional
        BBB 头训练集（默认自动查找 B3Pred）。
    ckpt : path, optional
        ESM-2 权重路径（覆盖 ESM2_CKPT 环境变量）。
    n_bootstrap : int
        训练集 bootstrap 重采样次数，用于 90% 置信区间（0 = 不算 CI）。
    apply_protraction : bool
        True 时对含修饰的肽叠加 protraction 惩罚（WS2 hybrid 基线）：
        序列分 p_seq 作为骨架上界，p_bbb 变为下调后的 p_final；返回额外字段
        p_seq / delta / is_protracted。无修饰肽 p_final == p_seq（零回归）。

    Returns
    -------
    list[dict]
        每条含 name/sequence/length/p_bbb/call/ci[/modification/known_route]，
        可直接传给 ``build_bbb_report``。
    """
    from . import embed as _embed
    from . import heads as _heads

    sequences = [str(s).strip().upper() for s in sequences]
    if not sequences:
        return []

    train_path = _find_train_csv(train_csv)
    tr_seqs, y_tr = _load_train(train_path)
    logger.info("BBB head training set: %s (%d peptides)", train_path, len(tr_seqs))

    Xtr = _embed.embed(tr_seqs, cache_dir=cache_dir, ckpt=ckpt, verbose=True)
    Xq = _embed.embed(sequences, cache_dir=cache_dir, ckpt=ckpt, verbose=True)
    y_arr = np.asarray(y_tr)

    # 主模型
    clf = _heads.make_head(head_kind).fit(Xtr, y_arr)
    p = clf.predict_proba(Xq)[:, 1] * 100.0

    # bootstrap 置信区间
    lo: list = [None] * len(sequences)
    hi: list = [None] * len(sequences)
    if n_bootstrap and n_bootstrap > 0:
        rng = np.random.default_rng(seed)
        n = len(y_arr)
        boots = []
        for _ in range(n_bootstrap):
            idx = rng.integers(0, n, n)
            if len(np.unique(y_arr[idx])) < 2:
                continue
            c = _heads.make_head(head_kind).fit(Xtr[idx], y_arr[idx])
            boots.append(c.predict_proba(Xq)[:, 1] * 100.0)
        if boots:
            B = np.vstack(boots)
            lo = np.percentile(B, 5, axis=0).tolist()
            hi = np.percentile(B, 95, axis=0).tolist()

    out = []
    for i, s in enumerate(sequences):
        mod = modifications[i] if modifications and i < len(modifications) else None
        p_seq = round(float(p[i]), 1)
        p_bbb = p_seq
        rec = {
            "name": (names[i] if names and i < len(names) and names[i] else f"peptide_{i + 1}"),
            "sequence": s,
            "length": len(s),
            "p_bbb": p_bbb,
            "call": "BBB+" if p_bbb >= 50 else "BBB-",
            "ci": ([round(float(lo[i]), 1), round(float(hi[i]), 1)]
                   if lo[i] is not None else None),
        }
        if apply_protraction and mod:
            from .descriptors import protraction_adjust
            adj = protraction_adjust(p_seq, mod)
            if adj["delta"] > 0 and adj["p_final"] is not None:
                rec["p_seq"] = p_seq          # 骨架上界
                rec["p_bbb"] = adj["p_final"]  # 下调后的最终分
                rec["protraction_delta"] = adj["delta"]
                rec["call"] = "BBB+" if adj["p_final"] >= 50 else "BBB-"
        if mod:
            rec["modification"] = mod
        if known_routes and i < len(known_routes) and known_routes[i]:
            rec["known_route"] = known_routes[i]
        out.append(rec)
    return out
