"""
ChEMBL Ligandability Proxy — 基于已知配体覆盖度的可药性评估

[DISABLED] ChEMBL API 尚未就绪（chembl-webresource-client 可能无法正常工作，
或需要单独配置环境）。当前模块仅返回占位结果，不发起网络请求。

如需启用：
1. 安装依赖: pip install chembl-webresource-client
2. 移除 ligandability.py 中的 _CHEMBL_DISABLED = True
3. 在 druggability/__init__.py 中恢复 ligandability 的导入和使用
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from typing import Any

from .utils import TargetNotFoundError, NetworkError

logger = logging.getLogger(__name__)

# ─── 禁用开关 ───────────────────────────────────────────────────────────
# 设为 True 时，assess_ligandability 立即返回占位结果（不调 ChEMBL API）。
# 化学信息学功能尚未就绪，暂时屏蔽。
_CHEMBL_DISABLED = True

# ─── 打分阈值配置 ───────────────────────────────────────────────────

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


def _get_chembl_client():
    """
    获取 ChEMBL webresource client 实例。

    同时设置默认 socket 超时，防止 SSL 握手卡死；
    并禁用 requests_cache（其 SQLite 后端在 Windows 上可能因文件锁挂起）。
    """
    try:
        # 禁用 ChEMBL 内置的 requests_cache SQLite 后端，避免文件锁死
        import os

        os.environ.setdefault("CHEMBL_CACHE_DISABLED", "1")

        from chembl_webresource_client.new_client import new_client

        # 全局默认 socket 超时（connect + read），避免网络不可用时永久挂起
        socket.setdefaulttimeout(30)

        # ── 修复：禁用连接池复用 ──────────────────────────────────────
        # chembl_webresource_client 底层使用 requests.Session，
        # 默认启用了 HTTP 连接池。在特定网络环境下（如防火墙/代理），
        # 复用 HTTPS 连接会导致后续请求永久阻塞（一直等待响应）。
        #
        # 解决方法：替换底层 requests.Session 的 HTTPAdapter，
        # 设置 pool_connections=0 和 pool_maxsize=0，
        # 强制每次请求都创建新连接（Connection: close）。
        import requests

        sess = requests.Session()
        # 不缓存连接，每次用完即关闭
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=0,
            pool_maxsize=0,
            max_retries=0,
        )
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
        # 将 custom session 赋值到 new_client 的内部 session
        # 依赖 new_client 使用 self._session 或 client.session 发送请求
        for attr in ("session", "_session", "session_factory"):
            if hasattr(new_client, attr):
                setattr(new_client, attr, sess)
                break

        # 更彻底的方案：patch 模块级的 Session 单例
        # 也适用于新版本的 chembl_webresource_client
        try:
            from chembl_webresource_client import (
                https_connection as _hc,
            )

            if hasattr(_hc, "_session"):
                _hc._session = sess
        except ImportError:
            pass

        return new_client
    except ImportError as e:
        # 如果连 requests 都无法导入，说明环境有问题
        if "requests" in str(e):
            raise ImportError("requests is required")
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


def _count_ligands(target_chembl_id: str) -> tuple[int, list[str]]:
    """
    统计靶点的已知配体数量并返回代表性化合物。

    Returns
    -------
    (n_unique_molecules, top_chembl_ids)
    """
    client = _get_chembl_client()
    activity = client.activity

    # 搭建 QuerySet（不执行）
    qs = (
        activity.filter(
            target_chembl_id=target_chembl_id,
            standard_type__in=ACTIVITY_TYPES,
        )
        .order_by("standard_value")
        .only(["molecule_chembl_id"])
    )

    # 用 Python 切片分页（QuerySet 在 v0.10.9 不再支持 .offset/.limit）
    all_molecules: set[str] = set()
    batch_size = 100
    start = 0

    while True:
        time.sleep(0.3)  # 速率限制
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


def _count_approved_drugs(target_chembl_id: str) -> int:
    """
    统计靶点对应的已批准药物数量。
    """
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


def assess_ligandability(
    query: str, organism: str = "Homo sapiens"
) -> LigandabilityResult:
    """
    对靶点进行 ligandability 评估。

    [DISABLED] 当前版本不执行真实的 ChEMBL 查询，直接返回占位结果。
    """
    if _CHEMBL_DISABLED:
        logger.warning(
            "ChEMBL ligandability assessment is disabled. "
            "Set _CHEMBL_DISABLED = False in ligandability.py to enable."
        )
        return LigandabilityResult(
            target_chembl_id="",
            pref_name=query,
            organism=organism,
            n_known_ligands=0,
            n_approved_drugs=0,
            ligandability_score=0.0,
            strongest_activity=None,
            top_compounds=[],
        )

    try:
        target_info = _search_target(query, organism=organism)
    except Exception as e:
        raise NetworkError(f"Failed to search ChEMBL target '{query}': {e}")

    if target_info is None:
        raise TargetNotFoundError(
            f"Target '{query}' not found in ChEMBL for organism '{organism}'"
        )

    chembl_id = target_info["target_chembl_id"]
    if not chembl_id:
        raise TargetNotFoundError(
            f"Target '{query}' found but no ChEMBL ID"
        )

    # 统计配体数量
    n_ligands, top_compounds = _count_ligands(chembl_id)
    lig_score = _score_from_ligand_count(n_ligands)

    # 最强活性
    strongest = _get_strongest_activity(chembl_id)

    # 已批准药物
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
