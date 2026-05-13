"""
Open Targets Tractability Wrapper — 靶点可追踪性评估

封装 Open Targets Platform GraphQL API，
返回靶点的 small molecule / antibody / PROTAC 三级 tractability 评估。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

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
    proteinIds {
      id
      source
    }
    dbXrefs {
      id
      source
    }
  }
}
"""

SEARCH_QUERY = """
query SearchQuery($queryString: String!) {
  search(queryString: $queryString, entityNames: ["target"], page: {index: 0, size: 5}) {
    total
    hits {
      object {
        __typename
        ... on Target {
          id
          approvedSymbol
          approvedName
          biotype
          proteinIds {
            id
            source
          }
          dbXrefs {
            id
            source
          }
        }
      }
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
class TargetInfo:
    """从 Open Targets 解析出的所有靶点标识符"""

    ensembl_id: str = ""
    symbol: str = ""
    name: str = ""
    biotype: str = ""
    uniprot_id: str = ""
    chembl_id: str = ""
    pdb_ids: list[str] = field(default_factory=list)
    source: Literal["opentargets", "mygene"] = "opentargets"


def _pick_best_search_hit(hits: list[dict]) -> dict | None:
    """从 search 结果中挑选最佳匹配：protein_coding > 其他人源蛋白"""
    for hit in hits:
        obj = hit.get("object", {})
        if obj.get("biotype") == "protein_coding":
            return obj
    for hit in hits:
        obj = hit.get("object", {})
        if "protein" in obj.get("biotype", "").lower():
            return obj
    return hits[0].get("object") if hits else None


def _pick_best_target(targets: list[dict]) -> dict | None:
    """从 direct target() 查询结果列表中挑选 protein_coding"""
    for t in targets:
        if t.get("biotype") == "protein_coding":
            return t
    return targets[0] if targets else None


def _extract_ids_from_target(target_data: dict) -> TargetInfo:
    """从 Open Targets target 对象中提取所有 ID。"""
    info = TargetInfo(
        ensembl_id=str(target_data.get("id", "")),
        symbol=str(target_data.get("approvedSymbol", "")),
        name=str(target_data.get("approvedName", "")),
        biotype=str(target_data.get("biotype", "")),
        source="opentargets",
    )

    for pid in target_data.get("proteinIds", []):
        src = pid.get("source", "")
        if "swissprot" in src.lower() and not info.uniprot_id:
            info.uniprot_id = str(pid.get("id", ""))

    for xref in target_data.get("dbXrefs", []):
        src = xref.get("source", "")
        if src == "ChEMBL" and not info.chembl_id:
            info.chembl_id = str(xref.get("id", ""))
        elif src == "PDB":
            pdb = str(xref.get("id", ""))
            if pdb:
                info.pdb_ids.append(pdb)

    return info


@rate_limit(delay=0.3)
def resolve_target_info(query: str, query_type: str = "gene_symbol") -> TargetInfo | None:
    """
    用 Open Targets 解析任意形式的靶点标识符，一次返回所有关键 ID。

    **优先走 Open Targets**；仅当 Open Targets 查不到时才降级到 mygene.info。

    Parameters
    ----------
    query : str
        靶点标识符（gene symbol / UniProt ID / Ensembl ID）
    query_type : str
        标识符类型: "gene_symbol" | "uniprot_id" | "ensembl_id"

    Returns
    -------
    TargetInfo | None
        包含 ensembl_id, symbol, name, biotype, uniprot_id, chembl_id, pdb_ids
        若所有途径均失败则返回 None
    """
    ensembl_id: str | None = None
    uniprot_id_hint: str | None = None

    if query_type == "ensembl_id":
        if query.startswith("ENSG"):
            ensembl_id = query
        else:
            return None
    elif query_type == "uniprot_id":
        uniprot_id_hint = query
    elif query_type == "gene_symbol":
        pass
    else:
        raise ValueError(f"Unknown query_type: {query_type}")

    try:
        if ensembl_id:
            payload = {"query": TRACTABILITY_QUERY, "variables": {"ensemblId": ensembl_id}}
        elif uniprot_id_hint:
            payload = {"query": SEARCH_QUERY, "variables": {"queryString": uniprot_id_hint}}
        else:
            payload = {"query": SEARCH_QUERY, "variables": {"queryString": query}}

        resp = requests.post(
            OPEN_TARGETS_API,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            logger.debug("Open Targets GraphQL errors: %s", data["errors"])

        if ensembl_id:
            t = data.get("data", {}).get("target")
            if t:
                info = _extract_ids_from_target(t)
                if uniprot_id_hint and not info.uniprot_id:
                    info.uniprot_id = uniprot_id_hint
                return info
        else:
            hits = data.get("data", {}).get("search", {}).get("hits", [])
            target_data = _pick_best_search_hit(hits)
            if target_data:
                info = _extract_ids_from_target(target_data)
                if uniprot_id_hint and not info.uniprot_id:
                    info.uniprot_id = uniprot_id_hint
                return info

    except Exception as e:
        logger.debug("Open Targets resolve failed for '%s': %s", query, e)

    if query_type == "gene_symbol":
        return _resolve_via_mygene(query)
    elif query_type == "uniprot_id":
        ensembl_fallback = _resolve_uniprot_to_ensembl_via_ot(uniprot_id_hint)
        if ensembl_fallback:
            try:
                payload = {"query": TRACTABILITY_QUERY, "variables": {"ensemblId": ensembl_fallback}}
                resp = requests.post(
                    OPEN_TARGETS_API, json=payload,
                    headers={"Content-Type": "application/json"}, timeout=30,
                )
                resp.raise_for_status()
                t = resp.json().get("data", {}).get("target")
                if t:
                    info = _extract_ids_from_target(t)
                    info.uniprot_id = uniprot_id_hint
                    return info
            except Exception:
                pass
        return _resolve_via_mygene_uniprot(uniprot_id_hint)

    return None


def _resolve_via_mygene(gene_symbol: str) -> TargetInfo | None:
    """降级：使用 mygene.info 解析基因符号。"""
    try:
        import mygene
        mg = mygene.MyGeneInfo()
        r = mg.query(gene_symbol, species="human", fields="ensembl.gene,uniprot.Swiss-Prot,symbol,name", size=1)
        hits = r.get("hits", [])
        if not hits:
            return None
        hit = hits[0]
        ensg = hit.get("ensembl", {})
        ensg_id = ensg.get("gene") if isinstance(ensg, dict) else (ensg if ensg else None)
        uniprot_raw = hit.get("uniprot", {})
        usp = uniprot_raw.get("Swiss-Prot") if isinstance(uniprot_raw, dict) else None
        if isinstance(usp, list):
            usp = usp[0]
        return TargetInfo(
            ensembl_id=str(ensg_id) if ensg_id else "",
            symbol=str(hit.get("symbol", gene_symbol)),
            name=str(hit.get("name", "")),
            uniprot_id=str(usp) if usp else "",
            source="mygene",
        )
    except Exception as e:
        logger.error("mygene fallback failed for '%s': %s", gene_symbol, e)
        return None


def _resolve_uniprot_to_ensembl_via_ot(uniprot_id: str) -> str | None:
    """用 Open Targets search 查询 UniProt ID 返回 Ensembl。"""
    try:
        payload = {"query": SEARCH_QUERY, "variables": {"queryString": uniprot_id}}
        resp = requests.post(
            OPEN_TARGETS_API, json=payload,
            headers={"Content-Type": "application/json"}, timeout=30,
        )
        resp.raise_for_status()
        hits = resp.json().get("data", {}).get("search", {}).get("hits", [])
        obj = _pick_best_search_hit(hits)
        if obj:
            return str(obj.get("id", ""))
    except Exception:
        pass
    return None


def _resolve_via_mygene_uniprot(uniprot_id: str) -> TargetInfo | None:
    """降级：使用 mygene.info 通过 UniProt 解析。"""
    try:
        import mygene
        mg = mygene.MyGeneInfo()
        r = mg.query(f"uniprot:{uniprot_id}", species="human", fields="ensembl.gene,symbol,name", size=1)
        hits = r.get("hits", [])
        if not hits:
            return None
        hit = hits[0]
        ensg = hit.get("ensembl", {})
        ensg_id = ensg.get("gene") if isinstance(ensg, dict) else (ensg if ensg else None)
        return TargetInfo(
            ensembl_id=str(ensg_id) if ensg_id else "",
            symbol=str(hit.get("symbol", "")),
            name=str(hit.get("name", "")),
            uniprot_id=uniprot_id,
            source="mygene",
        )
    except Exception as e:
        logger.error("mygene UniProt fallback failed for '%s': %s", uniprot_id, e)
        return None


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
    target_info: TargetInfo | None = None

    @property
    def best_score(self) -> float:
        """所有 modality 中的最高 tractability 分数。"""
        return max(
            self.small_molecule.score,
            self.antibody.score,
            self.protac.score,
        )

    def to_dict(self) -> dict:
        d = {
            "ensembl_id": self.ensembl_id,
            "symbol": self.symbol,
            "name": self.name,
            "biotype": self.biotype,
            "small_molecule": self.small_molecule.to_dict(),
            "antibody": self.antibody.to_dict(),
            "protac": self.protac.to_dict(),
            "best_score": round(self.best_score, 3),
        }
        if self.target_info:
            d["uniprot_id"] = self.target_info.uniprot_id
            d["chembl_id"] = self.target_info.chembl_id
            d["pdb_ids"] = self.target_info.pdb_ids[:20]
        return d


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
    抗体和 PROTAC 可追踪性评估，并将 TargetInfo 附在结果中。

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
    target_info = resolve_target_info(query, query_type=query_type)
    if target_info is None or not target_info.ensembl_id:
        raise TargetNotFoundError(
            f"Could not resolve target info for '{query}' (type={query_type})"
        )

    try:
        data = _query_graphql(target_info.ensembl_id)
    except NetworkError:
        raise
    except Exception as e:
        raise NetworkError(f"Open Targets query failed: {e}")

    target_data = data.get("data", {}).get("target")
    if target_data is None:
        raise TargetNotFoundError(
            f"Target '{query}' (Ensembl: {target_info.ensembl_id}) "
            "not found in Open Targets"
        )

    result = TractabilityResult(
        ensembl_id=str(target_data.get("id", target_info.ensembl_id)),
        symbol=str(target_data.get("approvedSymbol", target_info.symbol)),
        name=str(target_data.get("approvedName", target_info.name)),
        biotype=str(target_data.get("biotype", target_info.biotype)),
        raw=target_data,
        target_info=target_info,
    )

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

    for modality, labels in modality_labels.items():
        mod_tract = getattr(result, modality)
        mod_tract.labels = labels
        if labels:
            scored = [(lbl, label_to_score(lbl)) for lbl in labels]
            best_label, best_score = max(scored, key=lambda x: x[1])
            mod_tract.top_label = best_label
            mod_tract.score = best_score

    return result
