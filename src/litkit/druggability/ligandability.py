"""
ChEMBL Ligandability Proxy — 基于已知配体覆盖度的可药性评估

利用 chembl-webresource-client 查询靶点的已知活性化合物数量，
通过配体覆盖度间接估计靶点的 ligandability（配体能力）。

所有 ChEMBL API 调用均带有超时保护，网络不可用时会优雅降级。
"""

from __future__ import annotations

import concurrent.futures
import logging
import socket
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .utils import TargetNotFoundError, NetworkError

logger = logging.getLogger(__name__)

# ─── 超时配置 ─────────────────────────────────────────────────────────

# 单个 ChEMBL API 调用的超时（秒）
_CHEMBL_CALL_TIMEOUT = 45
# 整体 assess_ligandability 的超时
_ASSESS_TIMEOUT = 90

# ─── 打分阈值配置 ───────────────────────────────────────────────────

LIGANDABILITY_THRESHOLDS: list[tuple[int, float]] = [
    (1000, 1.0),
    (100, 0.8),
    (50, 0.6),
    (10, 0.4),
    (1, 0.2),
    (0, 0.0),
]

ACTIVITY_TYPES = ["IC50", "EC50", "Ki", "Kd", "Potency", "ED50"]


@dataclass
class LigandabilityResult:
    """ligandability 评估结果"""

    target_chembl_id: str = ""
    pref_name: str = ""
    organism: str = ""
    n_known_ligands: int = 0
    n_approved_drugs: int = 0
    ligandability_score: float = 0.0
    strongest_activity: dict | None = None
    top_compounds: list[str] = field(default_factory=list)
    raw: dict | None = None

    def to_dict(self) -> dict:
        return {
            "target_chembl_id": self.target_chembl_id,
            "pref_name": self.pref_name,
            "organism": self.organism,
            "n_known_ligands": self.n_known_ligands,
            "n_approved_drugs": self.n_approved_drugs,
            "ligandability_score": self.ligandability_score,
            "strongest_activity": self.strongest_activity or {},
            "top_compounds": self.top_compounds[:5],
        }


def _score_from_ligand_count(n: int) -> float:
    """根据已知配体数量映射到 0-1 ligandability 分数。"""
    for threshold, score in LIGANDABILITY_THRESHOLDS:
        if n >= threshold:
            return score
    return 0.0


def _call_with_timeout(
    timeout: float, func: Callable, *args: Any, **kwargs: Any
) -> Any:
    """
    在独立线程中执行函数并强制执行超时。

    ChEMBL 的 requests 在 SSL 握手阶段可能永久挂起（尤其 Windows 上），
    socket.setdefaulttimeout 对此无效。本函数通过 ThreadPoolExecutor
    确保即使 SSL 层卡死也能在 timeout 秒后超时抛出 ``NetworkError``。
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(func, *args, **kwargs)
        try:
            return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise NetworkError(
                f"ChEMBL API call '{func.__name__}' timed out after {timeout}s"
            )


def _get_chembl_client():
    """
    获取 ChEMBL webresource client 实例。

    设置默认 socket 超时并禁用 requests_cache 后端。
    """
    try:
        import os

        os.environ.setdefault("CHEMBL_CACHE_DISABLED", "1")

        from chembl_webresource_client.new_client import new_client

        socket.setdefaulttimeout(30)
        return new_client
    except ImportError:
        raise ImportError(
            "chembl-webresource-client is required. Install with: "
            "pip install chembl-webresource-client"
        )


def _search_target(
    query: str, organism: str = "Homo sapiens"
) -> dict | None:
    """
    搜索 ChEMBL 靶点，返回最佳匹配的 target 信息。

    Returns
    -------
    dict with keys: target_chembl_id, pref_name, organism
    """
    client = _get_chembl_client()
    target = client.target

    # Step 1: 精确过滤（gene synonym）
    results = _call_with_timeout(
        _CHEMBL_CALL_TIMEOUT,
        lambda: list(
            target.filter(target_synonym__icontains=query)
            .only(["target_chembl_id", "pref_name", "organism", "target_type"])
        ),
    )

    # Step 2: 按人源优先过滤
    human_matches = [r for r in results if r.get("organism") == organism]
    protein_matches = [
        r for r in (human_matches or results)
        if r.get("target_type") in ("SINGLE PROTEIN", "PROTEIN COMPLEX", "PROTEIN FAMILY")
    ]
    candidates = protein_matches or human_matches or results

    if not candidates:
        # Step 3: 模糊搜索 fallback
        try:
            fuzzy_results = _call_with_timeout(
                _CHEMBL_CALL_TIMEOUT,
                lambda: list(target.search(query)),
            )
            for r in fuzzy_results:
                if r.get("organism") == organism:
                    candidates.append(r)
        except Exception:
            pass

    if not candidates:
        return None

    best = candidates[0]
    return {
        "target_chembl_id": str(best.get("target_chembl_id", "")),
        "pref_name": str(best.get("pref_name", "")),
        "organism": str(best.get("organism", "")),
    }


def _count_ligands(target_chembl_id: str) -> tuple[int, list[str]]:
    """
    统计靶点的已知配体数量并返回代表性化合物。

    Returns
    -------
    (n_unique_molecules, top_chembl_ids)
    """
    client = _get_chembl_client()
    activity = client.activity

    qs = (
        activity.filter(
            target_chembl_id=target_chembl_id,
            standard_type__in=ACTIVITY_TYPES,
        )
        .order_by("standard_value")
        .only(["molecule_chembl_id"])
    )

    all_molecules: set[str] = set()
    batch_size = 100
    start = 0

    while True:
        time.sleep(0.3)
        batch = _call_with_timeout(
            _CHEMBL_CALL_TIMEOUT,
            lambda s=start: list(qs[s : s + batch_size]),
        )
        if not batch:
            break
        for item in batch:
            mol_id = item.get("molecule_chembl_id")
            if mol_id:
                all_molecules.add(str(mol_id))
        start += batch_size
        if len(batch) < batch_size:
            break

    top_molecules = sorted(all_molecules)[:5]
    return len(all_molecules), top_molecules


def _get_strongest_activity(target_chembl_id: str) -> dict | None:
    """
    获取靶点的最强活性数据（最低 IC50/EC50/Ki/Kd 值）。
    """
    client = _get_chembl_client()
    activity = client.activity

    try:
        time.sleep(0.3)
        qs = (
            activity.filter(
                target_chembl_id=target_chembl_id,
                standard_type__in=ACTIVITY_TYPES,
            )
            .order_by("standard_value")
            .only(["standard_type", "standard_value", "standard_units"])
        )
        acts = _call_with_timeout(
            _CHEMBL_CALL_TIMEOUT,
            lambda: list(qs[0:1]),
        )
        if acts:
            act = acts[0]
            val = act.get("standard_value")
            if val is not None:
                return {
                    "type": str(act.get("standard_type", "")),
                    "value": float(val),
                    "unit": str(act.get("standard_units", "")),
                }
    except Exception as e:
        logger.warning("Failed to fetch strongest activity: %s", e)

    return None


def _count_approved_drugs(target_chembl_id: str) -> int:
    """
    统计靶点对应的已批准药物数量。
    """
    client = _get_chembl_client()
    drug = client.drug

    try:
        time.sleep(0.3)
        drugs = _call_with_timeout(
            _CHEMBL_CALL_TIMEOUT,
            lambda: list(
                drug.filter(
                    target_chembl_id=target_chembl_id,
                    max_phase=4,
                ).only(["molecule_chembl_id"])
            ),
        )
        return len(drugs)
    except Exception as e:
        logger.warning("Failed to count approved drugs: %s", e)
        return 0


def assess_ligandability(
    query: str, organism: str = "Homo sapiens"
) -> LigandabilityResult:
    """
    对靶点进行 ligandability 评估。

    通过查询 ChEMBL 数据库中靶点的已知活性化合物覆盖度，
    返回 ligandability 打分（0-1）及相关详细信息。

    Parameters
    ----------
    query : str
        靶点标识（gene symbol 或 UniProt ID）
    organism : str
        物种过滤，默认为 "Homo sapiens"

    Returns
    -------
    LigandabilityResult

    Raises
    ------
    TargetNotFoundError
        靶点在 ChEMBL 中未找到
    NetworkError
        API 请求失败或超时
    """
    try:
        return _call_with_timeout(
            _ASSESS_TIMEOUT,
            _assess_ligandability_impl,
            query,
            organism,
        )
    except NetworkError:
        raise
    except TargetNotFoundError:
        raise
    except Exception as e:
        raise NetworkError(
            f"ChEMBL ligandability assessment failed for '{query}': {e}"
        )


def _assess_ligandability_impl(query: str, organism: str) -> LigandabilityResult:
    """assess_ligandability 的实际实现（内部使用，由超时包装）。"""
    target_info = _search_target(query, organism=organism)

    if target_info is None:
        raise TargetNotFoundError(
            f"Target '{query}' not found in ChEMBL for organism '{organism}'"
        )

    chembl_id = target_info["target_chembl_id"]
    if not chembl_id:
        raise TargetNotFoundError(
            f"Target '{query}' found but no ChEMBL ID"
        )

    n_ligands, top_compounds = _count_ligands(chembl_id)
    lig_score = _score_from_ligand_count(n_ligands)
    strongest = _get_strongest_activity(chembl_id)
    n_drugs = _count_approved_drugs(chembl_id)

    return LigandabilityResult(
        target_chembl_id=chembl_id,
        pref_name=target_info.get("pref_name", ""),
        organism=target_info.get("organism", ""),
        n_known_ligands=n_ligands,
        n_approved_drugs=n_drugs,
        ligandability_score=lig_score,
        strongest_activity=strongest,
        top_compounds=top_compounds,
    )