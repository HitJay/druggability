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


@dataclass
class TractabilityResult:
    """tractability 评估结果"""

    ensembl_id: str = ""
    symbol: str = ""
    name: str = ""
    biotype: str = ""
    small_molecule: dict = field(default_factory=dict)
    antibody: dict = field(default_factory=dict)
    protac: dict = field(default_factory=dict)
    raw: dict | None = None

    def to_dict(self) -> dict:
        return {
            "ensembl_id": self.ensembl_id,
            "symbol": self.symbol,
            "name": self.name,
            "biotype": self.biotype,
            "small_molecule": self.small_molecule or {},
            "antibody": self.antibody or {},
            "protac": self.protac or {},
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

    tractability_list = target_data.get("tractability", [])
    if tractability_list:
        for t in tractability_list:
            modality_short = t.get("modality", "")
            modality = MODALITY_MAP.get(modality_short, modality_short.lower())
            info = {
                "label": str(t.get("label", "")),
                "modality": modality,
            }
            setattr(result, modality, info)

    return result