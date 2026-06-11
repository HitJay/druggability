"""
bbbkit.druggability.deep — 深度可药性评估编排 (单一真相源)

把"逐靶深挖"的编排逻辑集中到包内, 供两处复用:
  - scripts/run_deep_druggability.py  (薄壳 CLI)
  - bbbkit.report.builder             (报告生成)
  - bbbkit CLI `report` 子命令

设计文档: docs/druggability-deep-assessment-design.md

核心: 在现有 assess_druggability (tractability/ligandability/structure) 之上,
叠加 genetics 支柱 (OT associatedDiseases genetic_association datatype 分),
做模态分解 + DEEP_WEIGHTS 综合, 返回扁平 record (供矩阵) + 嵌套 raw (供报告/复现)。
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable

import requests

logger = logging.getLogger(__name__)

OPEN_TARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"

# ── 深度模式权重 (独立于 batch 模式 DEFAULT_WEIGHTS, 向后兼容) ──
DEEP_WEIGHTS: dict[str, float] = {
    "genetics": 0.25,
    "tractability": 0.25,
    "ligandability": 0.15,
    "structure": 0.15,
    "clinical": 0.10,  # Phase 1 (OT 扩展) 落地后启用
    "safety": 0.10,    # Phase 1 (OT 扩展) 落地后启用
}

# ── GWAS 性状人类可读说明 (展示用) ──
TRAIT_LABELS: dict[str, str] = {
    "WHRadjBMI": "Waist-hip ratio adjusted for BMI (脂肪分布)",
    "T2D": "Type 2 diabetes (2型糖尿病)",
    "BFPCT": "Body fat percentage (体脂率)",
}

# ── 遗传学富集 GraphQL (自包含; Phase 2 将折叠进核心模块) ──
_GENETICS_QUERY = """
query Genetics($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    associatedDiseases(page: {index: 0, size: 15}) {
      count
      rows {
        score
        datatypeScores { id score }
        disease { id name therapeuticAreas { id name } }
      }
    }
  }
}
"""


@dataclass
class GeneticsResult:
    """自包含遗传学富集结果 (Phase 2 将升级为核心模块 GeneticsResult)"""

    genetic_assoc_score: float = 0.0
    overall_top_disease: str = ""
    overall_top_score: float = 0.0
    n_associated_diseases: int = 0
    top_therapeutic_areas: list[str] = field(default_factory=list)
    genetics_score: float = 0.0
    direction: str = "unresolved (Phase 2)"
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def compute_genetics_score(has_gwas: bool, genetic_assoc_score: float) -> float:
    """
    遗传学证据阶梯 (脚手架版, 见设计文档 §2.3):
      0.40  存在 GWAS 关联 (CSV genetics=TRUE 即满足, 地板分)
    + 0.30 * OT genetic_association datatype 分
    + [Phase 2] 共定位 / 稀有变异 / 方向 的加成暂为 0
    """
    score = 0.40 if has_gwas else 0.0
    score += 0.30 * max(0.0, min(1.0, genetic_assoc_score))
    return round(min(1.0, score), 3)


def enrich_genetics(ensembl_id: str, has_gwas: bool, timeout: int = 30) -> GeneticsResult:
    """自包含 OT 遗传学富集; 任何失败都优雅降级 (仍给地板分)。"""
    res = GeneticsResult()
    try:
        resp = requests.post(
            OPEN_TARGETS_API,
            json={"query": _GENETICS_QUERY, "variables": {"ensemblId": ensembl_id}},
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        target = (resp.json().get("data") or {}).get("target") or {}
        assoc = target.get("associatedDiseases") or {}
        rows = assoc.get("rows") or []
        res.n_associated_diseases = int(assoc.get("count") or 0)

        best_genetic = 0.0
        areas: list[str] = []
        for i, row in enumerate(rows):
            for dts in row.get("datatypeScores") or []:
                if dts.get("id") == "genetic_association":
                    best_genetic = max(best_genetic, float(dts.get("score") or 0.0))
            if i == 0:
                disease = row.get("disease") or {}
                res.overall_top_disease = str(disease.get("name") or "")
                res.overall_top_score = round(float(row.get("score") or 0.0), 3)
                for ta in disease.get("therapeuticAreas") or []:
                    name = str(ta.get("name") or "")
                    if name and name not in areas:
                        areas.append(name)
        res.genetic_assoc_score = round(best_genetic, 3)
        res.top_therapeutic_areas = areas[:5]
    except Exception as e:  # noqa: BLE001 — 优雅降级
        res.error = str(e)
        logger.warning("genetics enrichment failed for %s: %s", ensembl_id, e)

    res.genetics_score = compute_genetics_score(has_gwas, res.genetic_assoc_score)
    return res


def recommend_modality(tract: dict) -> tuple[str, str]:
    """从 tractability 的三个 modality 分挑最优, 返回 (best_modality, 推荐文案)。"""
    if not tract or "error" in tract:
        return "unknown", "tractability 不可用 — 需联网或 Phase 1 OT 扩展"
    scores = {
        "small_molecule": (tract.get("small_molecule") or {}).get("score", 0.0),
        "antibody": (tract.get("antibody") or {}).get("score", 0.0),
        "protac": (tract.get("protac") or {}).get("score", 0.0),
    }
    best = max(scores, key=scores.get)
    if scores[best] <= 0:
        return "unknown", "三模态 tractability 均为 0 — 可能是 PPI/无序靶点, 转抗体轴人工复核"
    label_map = {"small_molecule": "小分子", "antibody": "抗体", "protac": "PROTAC/降解剂"}
    tied = [m for m, s in scores.items() if s == scores[best]]
    tie_note = ""
    if len(tied) > 1:
        tie_note = f" [平局: {'/'.join(label_map[m] for m in tied)} 同为 {scores[best]:.2f}, 按靶点类别人工裁决]"
    return best, f"首选 {label_map[best]} (score={scores[best]:.2f}){tie_note}; 多肽/类别精修见 Phase 4"


def deep_composite(dimensions: dict[str, float | None]) -> tuple[float, str]:
    """对可得维度做加权 (缺失维度不计入, 归一化), 返回 (overall, confidence)。"""
    avail = {k: v for k, v in dimensions.items() if v is not None}
    if not avail:
        return 0.0, "none"
    total_w = sum(DEEP_WEIGHTS.get(k, 0.1) for k in avail)
    wsum = sum(v * DEEP_WEIGHTS.get(k, 0.1) for k, v in avail.items())
    overall = round(wsum / total_w, 3) if total_w else 0.0
    n = len(avail)
    confidence = "high" if n >= 4 else "medium" if n >= 2 else "low"
    return overall, confidence


def _verdict(genetics_score: float | None, tract_best: float | None) -> str:
    """二维启发式结论 (脚手架版)。"""
    if genetics_score and tract_best:
        if genetics_score >= 0.55 and tract_best >= 0.6:
            return "Priority — 高验证 + 易成药, 建议立项"
        if genetics_score >= 0.55 and tract_best < 0.6:
            return "Hard but worth it — 验证强但成药难, 需模态创新"
        if tract_best >= 0.6:
            return "Tractable but verify — 易成药, 遗传学待加强"
        return "Watch — 两轴均中等, 暂观察"
    return "Incomplete — 数据不全 (见 raw JSON)"


def assess_target(
    gene_name: str,
    ensembl_id: str,
    *,
    gwas_trait: str = "",
    has_gwas: bool = True,
    include_structure: bool = False,
    offline: bool = False,
) -> dict[str, Any]:
    """
    对单个靶点跑深度评估。

    Returns
    -------
    dict: {"record": <扁平记录, 供矩阵/报告>, "raw": <嵌套原始, 供复现>}
    """
    record: dict[str, Any] = {
        "gene_name": gene_name,
        "gene_id": ensembl_id,
        "gwas_trait": gwas_trait,
        "gwas_trait_label": TRAIT_LABELS.get(gwas_trait, gwas_trait),
    }
    raw: dict[str, Any] = {"input": {
        "gene_name": gene_name, "gene_id": ensembl_id,
        "gwas_trait": gwas_trait, "has_gwas": has_gwas,
    }}

    if offline:
        record.update(
            genetics_score=None, tractability_best=None, best_modality="(offline)",
            ligandability_score=None, structure_score=None, overall_score=None,
            confidence="offline", recommendation="(offline scaffold)",
        )
        return {"record": record, "raw": raw}

    # ── 选择查询标识符: 有 Ensembl ID 用之, 否则退回 gene symbol ──
    if ensembl_id and ensembl_id.upper().startswith("ENSG"):
        query, query_type = ensembl_id, "ensembl_id"
    elif gene_name:
        query, query_type = gene_name, "gene_symbol"
    else:
        query, query_type = ensembl_id or gene_name, "gene_symbol"

    # ── tractability + ligandability + (可选) structure: 复用核心 ──
    full: dict[str, Any] = {}
    try:
        from . import assess_druggability
        full = assess_druggability(
            query,
            query_type=query_type,
            include_structure_analysis=include_structure,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("assess_druggability failed for %s: %s", gene_name or query, e)
        full = {"error": str(e)}
    raw["assess_druggability"] = full

    tract = full.get("tractability", {}) if isinstance(full, dict) else {}
    lig = full.get("ligandability", {}) if isinstance(full, dict) else {}
    pocket = full.get("pocket_analysis", {}) if isinstance(full, dict) else {}

    # ── 从评估结果回填 Ensembl ID / symbol (gene_symbol 输入时需要) ──
    resolved_ensembl = ensembl_id
    if isinstance(tract, dict):
        resolved_ensembl = tract.get("ensembl_id") or ensembl_id
        if not gene_name and tract.get("symbol"):
            record["gene_name"] = tract["symbol"]
    if resolved_ensembl and not record.get("gene_id"):
        record["gene_id"] = resolved_ensembl

    gen = enrich_genetics(resolved_ensembl, has_gwas) if resolved_ensembl else GeneticsResult(
        genetics_score=compute_genetics_score(has_gwas, 0.0),
        error="no ensembl_id resolved",
    )
    raw["genetics"] = gen.to_dict()

    best_modality, rec_modality = recommend_modality(tract)
    tract_best = tract.get("best_score") if isinstance(tract, dict) and "error" not in tract else None
    lig_score = lig.get("ligandability_score") if isinstance(lig, dict) and "error" not in lig else None
    struct_score = (
        pocket.get("best_druggability_score")
        if isinstance(pocket, dict) and pocket and "error" not in pocket
        else None
    )

    overall, confidence = deep_composite({
        "genetics": gen.genetics_score,
        "tractability": tract_best,
        "ligandability": lig_score,
        "structure": struct_score,
    })

    record.update(
        target_class=(tract.get("biotype") if isinstance(tract, dict) else "") or "",
        genetics_score=gen.genetics_score,
        genetic_assoc_score=gen.genetic_assoc_score,
        direction=gen.direction,
        top_disease=gen.overall_top_disease,
        top_therapeutic_areas="; ".join(gen.top_therapeutic_areas),
        tractability_best=tract_best,
        best_modality=best_modality,
        tract_SM=(tract.get("small_molecule") or {}).get("score") if isinstance(tract, dict) else None,
        tract_Ab=(tract.get("antibody") or {}).get("score") if isinstance(tract, dict) else None,
        tract_PROTAC=(tract.get("protac") or {}).get("score") if isinstance(tract, dict) else None,
        ligandability_score=lig_score,
        n_known_ligands=lig.get("n_known_ligands") if isinstance(lig, dict) else None,
        n_approved_drugs=lig.get("n_approved_drugs") if isinstance(lig, dict) else None,
        structure_score=struct_score,
        overall_score=overall,
        confidence=confidence,
        modality_note=rec_modality,
        recommendation=_verdict(gen.genetics_score, tract_best),
    )
    return {"record": record, "raw": raw}


def assess_targets(
    targets: Iterable[dict[str, Any]],
    *,
    include_structure: bool = False,
    offline: bool = False,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, Any]]:
    """
    批量深度评估。

    Parameters
    ----------
    targets : Iterable[dict]
        每项需含 gene_name + gene_id; 可选 gwas_trait / genetics(bool)。
    on_progress : Callable[(done, total, gene), None] | None
        进度回调。

    Returns
    -------
    list[dict]: 每项 {"record", "raw"}
    """
    items = list(targets)
    total = len(items)
    out: list[dict[str, Any]] = []
    for i, t in enumerate(items, 1):
        gene = str(t.get("gene_name") or t.get("gene") or "")
        ensembl = str(t.get("gene_id") or t.get("ensembl_id") or "")
        trait = str(t.get("gwas_trait") or t.get("genetics_traits") or "")
        has_gwas = bool(t.get("genetics", True))
        if on_progress:
            on_progress(i, total, gene)
        out.append(assess_target(
            gene, ensembl, gwas_trait=trait, has_gwas=has_gwas,
            include_structure=include_structure, offline=offline,
        ))
    return out
