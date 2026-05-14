"""
ChEMBL Ligandability Proxy — 基于已知配体覆盖度的可药性评估

支持两种查询方式：
1. 本地 SQLite 数据库（推荐，稳定高效）
2. 在线 ChEMBL API（保留向后兼容）
"""

from __future__ import annotations

import logging
import os
import socket
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Literal, Union

from .utils import TargetNotFoundError, NetworkError
from . import chembl_local

logger = logging.getLogger(__name__)

# ─── 配置和类型定义 ─────────────────────────────────────────────────

# ligandability: n_ligands → score mapping
LIGANDABILITY_THRESHOLDS: list[tuple[int, float]] = [
    (1000, 1.0),
    (100, 0.8),
    (50, 0.6),
    (10, 0.4),
    (1, 0.2),
    (0, 0.0),
]

# 活性标准 type 列表
ACTIVITY_TYPES = ["IC50", "EC50", "Ki", "Kd", "Potency", "ED50"]

# 查询后端类型
QueryBackend = Literal["local", "api", "auto"]


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
    backend_used: str = ""

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
            "backend_used": self.backend_used,
        }


def _score_from_ligand_count(n: int) -> float:
    """根据已知配体数量映射到 0-1 ligandability 分数。"""
    for threshold, score in LIGANDABILITY_THRESHOLDS:
        if n >= threshold:
            return score
    return 0.0


# ─── API 后端实现（保留向后兼容）────────────────────────────────────

def _get_chembl_client():
    """
    获取 ChEMBL webresource client 实例。

    同时设置默认 socket 超时，防止 SSL 握手卡死；
    并禁用 requests_cache（其 SQLite 后端在 Windows 上可能因文件锁挂起）。
    """
    try:
        # 禁用 ChEMBL 内置的 requests_cache SQLite 后端，避免文件锁死
        os.environ.setdefault("CHEMBL_CACHE_DISABLED", "1")

        from chembl_webresource_client.new_client import new_client

        # 全局默认 socket 超时（connect + read），避免网络不可用时永久挂起
        socket.setdefaulttimeout(30)
        return new_client
    except ImportError:
        raise ImportError(
            "chembl-webresource-client is required. Install with: "
            "pip install chembl-webresource-client"
        )


def _search_target_api(
    query: str, organism: str = "Homo sapiens"
) -> dict | None:
    """使用在线 API 搜索 ChEMBL 靶点"""
    client = _get_chembl_client()
    target = client.target

    # Step 1: 精确过滤（gene synonym）
    results = list(
        target.filter(target_synonym__icontains=query)
        .only(["target_chembl_id", "pref_name", "organism", "target_type"])
    )

    # Step 2: 按人源优先过滤
    human_matches = [r for r in results if r.get("organism") == organism]
    # 再按 SINGLE PROTEIN 优先
    protein_matches = [
        r for r in (human_matches or results)
        if r.get("target_type") in ("SINGLE PROTEIN", "PROTEIN COMPLEX", "PROTEIN FAMILY")
    ]
    candidates = protein_matches or human_matches or results

    if not candidates:
        # Step 3: 模糊搜索 fallback
        try:
            fuzzy_results = list(target.search(query))
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


def _count_ligands_api(target_chembl_id: str) -> tuple[int, list[str]]:
    """使用在线 API 统计配体数量"""
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
        batch = list(qs[start : start + batch_size])
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


def _get_strongest_activity_api(target_chembl_id: str) -> dict | None:
    """使用在线 API 获取最强活性"""
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
        acts = list(qs[0:1])
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


def _count_approved_drugs_api(target_chembl_id: str) -> int:
    """使用在线 API 统计已批准药物数量"""
    client = _get_chembl_client()
    drug = client.drug

    try:
        time.sleep(0.3)
        drugs = list(
            drug.filter(
                target_chembl_id=target_chembl_id,
                max_phase=4,
            ).only(["molecule_chembl_id"])
        )
        return len(drugs)
    except Exception as e:
        logger.warning("Failed to count approved drugs: %s", e)
        return 0


# ─── 本地数据库后端实现 ─────────────────────────────────────────────

def _search_target_local(
    query: str,
    organism: str = "Homo sapiens",
    db: Optional[chembl_local.ChemblLocalDB] = None,
) -> dict | None:
    """使用本地数据库搜索 ChEMBL 靶点"""
    if db is None:
        db = chembl_local.get_db()
    return db.search_target(query, organism=organism)


def _count_ligands_local(
    target_chembl_id: str,
    db: Optional[chembl_local.ChemblLocalDB] = None,
) -> tuple[int, list[str]]:
    """使用本地数据库统计配体数量"""
    if db is None:
        db = chembl_local.get_db()
    return db.count_ligands(target_chembl_id)


def _get_strongest_activity_local(
    target_chembl_id: str,
    db: Optional[chembl_local.ChemblLocalDB] = None,
) -> dict | None:
    """使用本地数据库获取最强活性"""
    if db is None:
        db = chembl_local.get_db()
    return db.get_strongest_activity(target_chembl_id)


def _count_approved_drugs_local(
    target_chembl_id: str,
    db: Optional[chembl_local.ChemblLocalDB] = None,
) -> int:
    """使用本地数据库统计已批准药物数量"""
    if db is None:
        db = chembl_local.get_db()
    return db.count_approved_drugs(target_chembl_id)


# ─── 主要接口 ────────────────────────────────────────────────────────

def assess_ligandability(
    query: str,
    organism: str = "Homo sapiens",
    backend: QueryBackend = "auto",
    db: Optional[chembl_local.ChemblLocalDB] = None,
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
    backend : "local" | "api" | "auto"
        查询后端：
        - "local": 强制使用本地 SQLite 数据库（推荐，稳定高效）
        - "api": 强制使用在线 API
        - "auto": 自动选择（优先本地，失败则回退到 API）
    db : ChemblLocalDB, optional
        自定义本地数据库实例，仅当 backend="local" 或 "auto" 时有效

    Returns
    -------
    LigandabilityResult

    Raises
    ------
    TargetNotFoundError
        靶点在 ChEMBL 中未找到
    NetworkError
        API 请求失败（仅当使用 API 后端时）
    ImportError
        所选后端的依赖未安装
    """
    backend_used = ""
    last_error: Optional[Exception] = None

    # 确定要尝试的后端顺序
    backends_to_try: list[QueryBackend]
    if backend == "auto":
        backends_to_try = ["local", "api"]
    elif backend == "local":
        backends_to_try = ["local"]
    elif backend == "api":
        backends_to_try = ["api"]
    else:
        raise ValueError(f"Invalid backend: {backend}")

    for current_backend in backends_to_try:
        try:
            if current_backend == "local":
                backend_used = "local"
                try:
                    target_info = _search_target_local(query, organism=organism, db=db)
                except ImportError:
                    if backend == "local":
                        raise
                    last_error = ImportError("chembl-downloader not installed")
                    continue

                if target_info is None:
                    raise TargetNotFoundError(
                        f"Target '{query}' not found in ChEMBL for organism '{organism}'"
                    )

                chembl_id = target_info["target_chembl_id"]
                if not chembl_id:
                    raise TargetNotFoundError(
                        f"Target '{query}' found but no ChEMBL ID"
                    )

                n_ligands, top_compounds = _count_ligands_local(chembl_id, db=db)
                lig_score = _score_from_ligand_count(n_ligands)
                strongest = _get_strongest_activity_local(chembl_id, db=db)
                n_drugs = _count_approved_drugs_local(chembl_id, db=db)

            else:  # api
                backend_used = "api"
                try:
                    target_info = _search_target_api(query, organism=organism)
                except Exception as e:
                    if backend == "api":
                        raise NetworkError(f"Failed to search ChEMBL target '{query}': {e}")
                    last_error = e
                    continue

                if target_info is None:
                    raise TargetNotFoundError(
                        f"Target '{query}' not found in ChEMBL for organism '{organism}'"
                    )

                chembl_id = target_info["target_chembl_id"]
                if not chembl_id:
                    raise TargetNotFoundError(
                        f"Target '{query}' found but no ChEMBL ID"
                    )

                n_ligands, top_compounds = _count_ligands_api(chembl_id)
                lig_score = _score_from_ligand_count(n_ligands)
                strongest = _get_strongest_activity_api(chembl_id)
                n_drugs = _count_approved_drugs_api(chembl_id)

            return LigandabilityResult(
                target_chembl_id=chembl_id,
                pref_name=target_info.get("pref_name", ""),
                organism=target_info.get("organism", ""),
                n_known_ligands=n_ligands,
                n_approved_drugs=n_drugs,
                ligandability_score=lig_score,
                strongest_activity=strongest,
                top_compounds=top_compounds,
                backend_used=backend_used,
            )

        except TargetNotFoundError:
            raise
        except Exception as e:
            last_error = e
            if len(backends_to_try) == 1:
                raise

    if last_error:
        raise last_error
    raise RuntimeError("No backend available")


# 保留原始函数名向后兼容
def _search_target(*args, **kwargs):
    return _search_target_api(*args, **kwargs)


def _count_ligands(*args, **kwargs):
    return _count_ligands_api(*args, **kwargs)


def _get_strongest_activity(*args, **kwargs):
    return _get_strongest_activity_api(*args, **kwargs)


def _count_approved_drugs(*args, **kwargs):
    return _count_approved_drugs_api(*args, **kwargs)
