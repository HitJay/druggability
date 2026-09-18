"""
批量靶点可药性评估 — 支持多靶点并发查询与结果聚合

用法:
    from bbbkit.druggability.batch import assess_druggability_batch, BatchResult

    results = assess_druggability_batch(["EGFR", "BRAF", "KRAS"])
    for r in results:
        print(f"{r.query}: {r.composite_score}")
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Sequence

logger = logging.getLogger(__name__)

# assess_druggability 懒加载（避免循环导入：__init__.py → batch → __init__.py）
_FN_ASSESS: Callable | None = None


def _get_assess_fn():
    global _FN_ASSESS
    if _FN_ASSESS is None:
        from . import assess_druggability as fn  # type: ignore[attr-defined]
        _FN_ASSESS = fn
    return _FN_ASSESS

try:
    from tqdm.auto import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

    # 无 tqdm 时的退化进度打印
    def tqdm(iterable, *args, **kwargs):  # type: ignore
        return iterable


@dataclass
class BatchResult:
    """单条批量评估结果"""

    query: str = ""
    success: bool = False
    error: str | None = None
    elapsed_seconds: float = 0.0
    overall_score: float = 0.0
    confidence: str = "none"
    tractability_score: float | None = None
    ligandability_score: float | None = None
    tractability_best_label: str = ""
    ligandability_n_ligands: int = 0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "success": self.success,
            "error": self.error,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "tractability_score": self.tractability_score,
            "ligandability_score": self.ligandability_score,
            "tractability_best_label": self.tractability_best_label,
            "ligandability_n_ligands": self.ligandability_n_ligands,
        }


def _assess_single(
    query: str,
    query_type: str = "gene_symbol",
    include_structure_analysis: bool = False,
) -> BatchResult:
    """评估单个靶点，返回 BatchResult。失败不会抛异常。"""
    start = time.time()
    result = BatchResult(query=query)

    try:
        full = _get_assess_fn()(
            query,
            query_type=query_type,
            include_structure_analysis=include_structure_analysis,
        )

        composite = full.get("composite", {})
        result.overall_score = composite.get("overall_score", 0.0)
        result.confidence = composite.get("confidence", "none")

        # tractability
        tract = full.get("tractability", {})
        if tract and "error" not in tract:
            result.tractability_score = tract.get("best_score")
            # 取最佳 modality 的 label
            for mod in ["small_molecule", "antibody", "protac"]:
                m = tract.get(mod, {})
                if isinstance(m, dict) and m.get("score", 0) > 0:
                    lbl = m.get("top_label", "")
                    if lbl:
                        result.tractability_best_label = lbl
                        break

        # ligandability
        lig = full.get("ligandability", {})
        if lig and "error" not in lig:
            result.ligandability_score = lig.get("ligandability_score")
            result.ligandability_n_ligands = lig.get("n_known_ligands", 0)

        result.success = True

    except Exception as e:
        logger.debug("Batch assess failed for '%s': %s", query, e)
        result.error = str(e)

    result.elapsed_seconds = time.time() - start
    return result


def assess_druggability_batch(
    targets: Sequence[str],
    query_type: str = "gene_symbol",
    max_workers: int = 3,
    request_delay: float = 0.5,
    show_progress: bool = True,
    include_structure_analysis: bool = False,
    progress_description: str = "Assessing targets",
    on_progress: Callable[[int, int], None] | None = None,
) -> list[BatchResult]:
    """
    批量评估多个靶点的 druggability。

    Parameters
    ----------
    targets : Sequence[str]
        靶点标识符列表
    query_type : str
        标识符类型: "gene_symbol" | "uniprot_id" | "ensembl_id"
    max_workers : int
        并发工作线程数，默认 3
    request_delay : float
        每次 API 调用前的最小间隔（秒），默认 0.5
    show_progress : bool
        是否显示 tqdm 进度条
    include_structure_analysis : bool
        是否包含结构分析（需要 fpocket）
    progress_description : str
        进度条描述文字
    on_progress : Callable[[int, int], None] | None
        进度回调，参数为 (done, total)

    Returns
    -------
    list[BatchResult]

    Example
    -------
    >>> results = assess_druggability_batch(["EGFR", "BRAF", "KRAS"])
    >>> for r in results:
    ...     print(f"{r.query}: {r.overall_score} ({r.confidence})")
    """
    if not targets:
        return []

    total = len(targets)
    results: list[BatchResult | None] = [None] * total  # 保持输入顺序

    def _run_and_store(index: int, query: str) -> BatchResult:
        result = _assess_single(
            query,
            query_type=query_type,
            include_structure_analysis=include_structure_analysis,
        )
        return result

    done_count = 0
    iterator = range(total)

    if show_progress and HAS_TQDM:
        iterator = tqdm(iterator, desc=progress_description, unit="target")

    # 串行 + sleep 限速（比多线程+锁简单，且避免 API 429）
    for i in iterator:
        query = targets[i]
        result = _run_and_store(i, query)
        results[i] = result
        done_count += 1
        if on_progress:
            on_progress(done_count, total)
        if i < total - 1 and request_delay > 0:
            time.sleep(request_delay)

    return [r for r in results if r is not None]  # type: ignore