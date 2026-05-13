"""
Open Targets Tractability Wrapper — 靶点可追踪性评估

封装 Open Targets Platform GraphQL API，
返回靶点的 small molecule / antibody / PROTAC 三级 tractability 评估。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import requests

from .utils import (
    TargetNotFoundError,
    NetworkError,
    resolve_ensembl_id,
    rate_limit,
)

logger = logging.getLogger(__name__)

# ─── 常量 ────────────────────────────────────────────────────────────

OPEN_TARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"

TRACTABILITY_QUERY = """
query TractabilityQuery($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    tractability {
      label
      modality
    }
  }
}
"""

# modality 名称映射
MODALITY_MAP = {
    "SM": "small_molecule",
    "AB": "antibody",
    "PROTAC": "protac",
}

# ─── Tractability label → score 映射 ─────────────────────────────────
# 分数基于 Open Targets 官方 tractability bucket 体系
# 每个 modality 的 label 列表可能不同，但均映射到 0-1 分数

TRACTABILITY_LABEL_SCORES: dict[str, float] = {
    # ── Small Molecule (SM) 常见 labels ──
    "Approved Drug": 1.0,
    "Advanced Clinical": 0.9,
    "Phase 1 Clinical": 0.8,
    "Structure with Ligand": 0.7,
    "High-Quality Ligand": 0.65,
    "High-Quality Pocket": 0.6,
    "Med-Quality Pocket": 0.5,
    "Druggable Family": 0.4,
    # ── Antibody (AB) 常见 labels ──
    "UniProt loc": 0.5,
    "GO CC": 0.45,
    "UniProt SigP or TMHMM": 0.4,
    "Human Protein Atlas loc": 0.35,
    # ── PROTAC 常见 labels ──
    "Literature": 0.5,
    "UniProt Ubiquitination": 0.45,
    "Database Ubiquitination": 0.4,
    "Half-life Data": 0.35,
    "Small Molecule Binder": 0.3,
    # ── 通用 ──
    "Clinical Precedence": 0.9,
    "Discovery Precedence": 0.7,
    "Predicted Tractable": 0.5,
    "Predicted Tractable - High Confidence": 0.55,
    "Predicted Tractable - Medium Confidence": 0.45,
}


def label_to_score(label: str) -> float:
    """将 Open Targets tractability label 映射为 0-1 分数。"""
    return TRACTABILITY_LABEL_SCORES.get(label, 0.2)


@dataclass
class ModalityTractability:
    """单个 modality 的 tractability 信息"""

    modality: str = ""
    labels: list[str] = field(default_factory=list)
    top_label: str = ""
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "modality": self.modality,
            "labels": self.labels,
            "top_label": self.top_label,
            "score": round(self.score, 3),
        }


@dataclass
class TractabilityResult:
    """tractability 评估结果"""

    ensembl_id: str = ""
    symbol: str = ""
    name: str = ""
    biotype: str = ""
    small_molecule: ModalityTractability = field(
        default_factory=lambda: ModalityTractability(modality="small_molecule")
    )
    antibody: ModalityTractability = field(
        default_factory=lambda: ModalityTractability(modality="antibody")
    )
    protac: ModalityTractability = field(
        default_factory=lambda: ModalityTractability(modality="protac")
    )
    raw: dict | None = None

    @property
    def best_score(self) -> float:
        """所有 modality 中的最高 tractability 分数。"""
        return max(
            self.small_molecule.score,
            self.antibody.score,
            self.protac.score,
        )

    def to_dict(self) -> dict:
        return {
            "ensembl_id": self.ensembl_id,
            "symbol": self.symbol,
            "name": self.name,
            "biotype": self.biotype,
            "small_molecule": self.small_molecule.to_dict(),
            "antibody": self.antibody.to_dict(),
            "protac": self.protac.to_dict(),
            "best_score": round(self.best_score, 3),
        }


@rate_limit(delay=0.2)
def _query_graphql(ensembl_id: str) -> dict:
    """
    执行 GraphQL 查询，返回 Open Targets API 原始响应。
    """
    payload = {
        "query": TRACTABILITY_QUERY,
        "variables": {"ensemblId": ensembl_id},
    }

    try:
        resp = requests.post(
            OPEN_TARGETS_API,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            raise NetworkError(
                f"Open Targets GraphQL error: {data['errors']}"
            )

        return data
    except requests.exceptions.Timeout:
        raise NetworkError("Open Targets API request timed out")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Open Targets API request failed: {e}")


def query_tractability(
    query: str, query_type: str = "gene_symbol"
) -> TractabilityResult:
    """
    查询靶点的 tractability 信息。

    通过 Open Targets Platform GraphQL API 获取靶点的小分子、
    抗体和 PROTAC 可追踪性评估。

    Parameters
    ----------
    query : str
        靶点标识符（gene symbol / UniProt ID / Ensembl ID）
    query_type : str
        标识符类型: "gene_symbol" | "uniprot_id" | "ensembl_id"

    Returns
    -------
    TractabilityResult

    Raises
    ------
    TargetNotFoundError
        靶点在 Open Targets 中未找到或 Ensembl ID 无法解析
    NetworkError
        API 请求失败
    """
    # 解析 Ensembl ID
    if query_type == "ensembl_id":
        ensembl_id = query if query.startswith("ENSG") else None
    else:
        ensembl_id = resolve_ensembl_id(query, query_type=query_type)

    if not ensembl_id:
        raise TargetNotFoundError(
            f"Could not resolve Ensembl ID from '{query}' (type={query_type})"
        )

    # 查询 API
    data = _query_graphql(ensembl_id)
    target_data = data.get("data", {}).get("target")

    if target_data is None:
        raise TargetNotFoundError(
            f"Target '{query}' (Ensembl: {ensembl_id}) not found in Open Targets"
        )

    # 解析结果
    result = TractabilityResult(
        ensembl_id=str(target_data.get("id", "")),
        symbol=str(target_data.get("approvedSymbol", "")),
        name=str(target_data.get("approvedName", "")),
        biotype=str(target_data.get("biotype", "")),
        raw=target_data,
    )

    # 聚合 tractability labels per modality
    tractability_list = target_data.get("tractability", []) or []
    modality_labels: dict[str, list[str]] = {
        "small_molecule": [],
        "antibody": [],
        "protac": [],
    }

    for t in tractability_list:
        modality_short = t.get("modality", "")
        modality = MODALITY_MAP.get(modality_short, modality_short.lower())
        label = str(t.get("label", ""))
        if modality in modality_labels and label:
            modality_labels[modality].append(label)

    # 为每个 modality 计算最高分 label
    for modality, labels in modality_labels.items():
        mod_tract = getattr(result, modality)
        mod_tract.labels = labels
        if labels:
            scored = [(lbl, label_to_score(lbl)) for lbl in labels]
            best_label, best_score = max(scored, key=lambda x: x[1])
            mod_tract.top_label = best_label
            mod_tract.score = best_score

    return result
