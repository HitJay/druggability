"""
bbbkit.peptide.benchmark — 端到端 benchmark：嵌入一次、复用、多任务多头评估

诚实协议：每个任务用官方 train/test 划分；超参仅由训练集 CV 选择；测试集只评一次。
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import embed as _embed
from . import heads as _heads
from . import datasets as _datasets
from .tasks import get_tasks

logger = logging.getLogger(__name__)


def run_task(task, data_dir, *, kind="auto", cache_dir=None, ckpt=None):
    """对单个任务运行 benchmark。

    kind='auto' 时对 linear 与 mlp 各做训练集 CV 选超参，按 CV-AUC 选最佳头；
    也可强制 kind='linear' 或 'mlp'。返回结果 dict。
    """
    (tr_seqs, ytr), (te_seqs, yte) = _datasets.load_split(data_dir, task.key)
    Xtr = _embed.embed(tr_seqs, cache_dir=cache_dir, ckpt=ckpt)
    Xte = _embed.embed(te_seqs, cache_dir=cache_dir, ckpt=ckpt)

    kinds = ("linear", "mlp") if kind == "auto" else (kind,)
    per_head = {}
    for k in kinds:
        params, cv_auc = _heads.select_hparams(Xtr, ytr, k)
        _, test = _heads.fit_eval(Xtr, ytr, Xte, yte, kind=k, **params)
        per_head[k] = {"params": params, "cv_auc": cv_auc, "test": test}

    best_kind = max(per_head, key=lambda k: per_head[k]["cv_auc"])
    return {
        "key": task.key, "name": task.name, "property": task.prop,
        "source": task.source, "official_split": task.official_split,
        "n_train": len(tr_seqs), "n_test": len(te_seqs),
        "pos_train": int(sum(ytr)), "pos_test": int(sum(yte)),
        "heads": per_head, "best_by_cv": best_kind,
        "best": per_head[best_kind], "sota_ref": task.sota, "sota_src": task.sota_src,
    }


def run_benchmark(data_dir, keys=None, *, kind="auto", cache_dir=None,
                  ckpt=None, download_missing=True):
    """对多个任务运行 benchmark；缺失数据可自动下载（BBB 需自备，见 README）。"""
    data_dir = Path(data_dir)
    tasks = get_tasks(keys)
    if download_missing:
        need = [t.key for t in tasks
                if t.key != "bbb" and not (data_dir / t.key / "train.csv").exists()]
        if need:
            logger.info("下载缺失任务数据: %s", need)
            _datasets.download(data_dir, need)

    results = {}
    for task in tasks:
        if not (data_dir / task.key / "train.csv").exists():
            logger.warning("跳过 %s：缺少 %s/train.csv", task.key, task.key)
            continue
        results[task.key] = run_task(task, data_dir, kind=kind,
                                     cache_dir=cache_dir, ckpt=ckpt)
    return results
