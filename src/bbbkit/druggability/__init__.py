"""
bbbkit.druggability — 靶点可药性评估核心模块

提供统一的 druggability 评估接口，集成多个数据源：
- Open Targets tractability API（知识库可追踪性）
- ChEMBL ligandability proxy（已知配体覆盖度）
- fpocket 口袋检测（基于结构的分析）
"""

from __future__ import annotations

import logging

from .tractability import query_tractability, TractabilityResult, resolve_target_info
from .ligandability import assess_ligandability, LigandabilityResult
from .pocket import detect_pockets, PocketAnalysisResult
from .batch import assess_druggability_batch, BatchResult

logger = logging.getLogger(__name__)

# ─── 综合评分权重 ─────────────────────────────────────────────────────
# 三个维度的默认权重（总和不必为 1，内部会归一化）
DEFAULT_WEIGHTS = {
    "tractability": 0.35,
    "ligandability": 0.35,
    "structure": 0.30,
}


def assess_druggability(
    query: str,
    query_type: str = "gene_symbol",
    structure_path: str | None = None,
    include_structure_analysis: bool = False,
) -> dict:
    """
    统一入口：对靶点执行多层 druggability 评估。

    Parameters
    ----------
    query : str
        靶点标识符（gene symbol / UniProt ID / Ensembl ID）
    query_type : str
        标识符类型: "gene_symbol" | "uniprot_id" | "ensembl_id"
    structure_path : str | None
        PDB 文件路径。若提供则同时运行 fpocket 结构分析。
    include_structure_analysis : bool
        若为 True 且未提供 structure_path，尝试从 Open Targets → RCSB PDB
        自动获取结构。**默认 False**（fpocket 需要 Docker/本地安装）。

    Returns
    -------
    dict
        综合 druggability 评估报告
    """
    result: dict = {
        "query": query,
        "query_type": query_type,
    }

    target_info = None
    tractability = None

    # ── Tier 1: Open Targets tractability ──
    try:
        tractability = query_tractability(query, query_type=query_type)
        result["tractability"] = tractability.to_dict()
        target_info = tractability.target_info
    except Exception as e:
        logger.warning("Tractability query failed for '%s': %s", query, e)
        result["tractability"] = {"error": str(e)}
        try:
            target_info = resolve_target_info(query, query_type=query_type)
        except Exception:
            target_info = None

    chembl_id: str | None = None
    if target_info and target_info.chembl_id:
        chembl_id = target_info.chembl_id
        logger.info("Using ChEMBL ID from Open Targets: %s", chembl_id)

    # ── Tier 1: ChEMBL ligandability ──
    # 优先用 Open Targets 提供的 ChEMBL ID 精准查询
    try:
        if chembl_id:
            ligandability = assess_ligandability_by_chembl_id(chembl_id)
        else:
            ligandability = assess_ligandability(query)
        result["ligandability"] = ligandability.to_dict()
    except Exception as e:
        logger.warning("Ligandability query failed for '%s': %s", query, e)
        result["ligandability"] = {"error": str(e)}

    # ── Tier 2: Structure-based pocket analysis ──
    if structure_path or include_structure_analysis:
        try:
            pdb_ids: list[str] = []
            if target_info and target_info.pdb_ids:
                pdb_ids = target_info.pdb_ids
            pocket_input = _resolve_structure_input(query, query_type, target_info)
            pockets = detect_pockets(
                structure_path=pocket_input,
                auto_download=structure_path is None,
                preferred_pdb_ids=pdb_ids if not structure_path else None,
            )
            result["pocket_analysis"] = pockets.to_dict()
        except Exception as e:
            logger.warning("Pocket analysis failed for '%s': %s", query, e)
            result["pocket_analysis"] = {"error": str(e)}

    # ── Composite score ──
    result["composite"] = _compute_composite(result)
    return result


def assess_ligandability_by_chembl_id(chembl_id: str) -> LigandabilityResult:
    """
    用 ChEMBL ID 直接查询 ligandability（绕过基因符号搜索）。

    Parameters
    ----------
    chembl_id : str
        ChEMBL Target ID，如 "CHEMBL203"

    Returns
    -------
    LigandabilityResult
    """
    from .ligandability import _count_ligands, _get_strongest_activity, _count_approved_drugs
    from .ligandability import _score_from_ligand_count, LigandabilityResult as LR

    n_ligands, top_compounds = _count_ligands(chembl_id)
    strongest = _get_strongest_activity(chembl_id)
    n_drugs = _count_approved_drugs(chembl_id)
    return LR(
        target_chembl_id=chembl_id,
        pref_name="",
        organism="",
        n_known_ligands=n_ligands,
        n_approved_drugs=n_drugs,
        ligandability_score=_score_from_ligand_count(n_ligands),
        strongest_activity=strongest,
        top_compounds=top_compounds,
    )


def _resolve_structure_input(
    query: str, query_type: str, target_info=None
) -> str:
    """
    将靶点标识符解析为可用于结构下载的 UniProt ID。

    Parameters
    ----------
    target_info : TargetInfo | None
        若已通过 Open Targets 解析出 target_info，直接使用其 uniprot_id

    Returns
    -------
    str
        UniProt accession（如 "P00533"）

    Raises
    ------
    ValueError
        无法解析为 UniProt ID
    """
    if target_info and target_info.uniprot_id:
        return target_info.uniprot_id

    if query_type == "uniprot_id":
        return query

    from .utils import gene_symbol_to_uniprot

    if query_type == "gene_symbol":
        uniprot_id = gene_symbol_to_uniprot(query)
        if uniprot_id:
            return uniprot_id
        raise ValueError(
            f"Cannot resolve gene symbol '{query}' to UniProt ID for structure download. "
            f"Please provide a structure_path or UniProt ID directly."
        )

    if query_type == "ensembl_id":
        raise ValueError(
            f"Automatic structure download from Ensembl ID is not yet supported. "
            f"Please provide a structure_path or use query_type='gene_symbol'."
        )

    raise ValueError(f"Unknown query_type: {query_type}")


def _compute_composite(result: dict) -> dict:
    """
    合成多来源 druggability 综合评分（0-1）。

    评分逻辑：
    - tractability: 取三个 modality（SM/AB/PROTAC）中的最高分
    - ligandability: 直接使用 ligandability_score
    - structure: 使用 best_druggability_score
    - 最终分数为各维度加权平均（仅计算成功查询的维度）
    """
    dimension_scores: dict[str, float] = {}

    # ── Tractability ──
    tractability = result.get("tractability", {})
    if tractability and "error" not in tractability:
        # 新结构：每个 modality 有 .score，取 best_score
        best = tractability.get("best_score")
        if best is not None and best > 0:
            dimension_scores["tractability"] = float(best)
        else:
            # 尝试从各 modality 的 score 字段取
            modality_scores = []
            for mod in ["small_molecule", "antibody", "protac"]:
                mod_info = tractability.get(mod, {})
                if isinstance(mod_info, dict):
                    s = mod_info.get("score", 0.0)
                    if s > 0:
                        modality_scores.append(s)
            if modality_scores:
                dimension_scores["tractability"] = max(modality_scores)

    # ── Ligandability ──
    ligandability = result.get("ligandability", {})
    if ligandability and "error" not in ligandability:
        lig_score = ligandability.get("ligandability_score", 0.0)
        if lig_score > 0:
            dimension_scores["ligandability"] = float(lig_score)

    # ── Structure (pocket) ──
    pocket_analysis = result.get("pocket_analysis", {})
    if pocket_analysis and "error" not in pocket_analysis:
        best_pocket = pocket_analysis.get("best_druggability_score", 0.0)
        if best_pocket > 0:
            dimension_scores["structure"] = float(best_pocket)

    # ── 加权平均 ──
    if not dimension_scores:
        return {
            "overall_score": 0.0,
            "confidence": "none",
            "dimensions_available": 0,
            "contributing_scores": {},
        }

    total_weight = sum(
        DEFAULT_WEIGHTS.get(dim, 0.3) for dim in dimension_scores
    )
    weighted_sum = sum(
        score * DEFAULT_WEIGHTS.get(dim, 0.3)
        for dim, score in dimension_scores.items()
    )
    overall = weighted_sum / total_weight if total_weight > 0 else 0.0

    # 置信度标签
    n_dims = len(dimension_scores)
    if n_dims >= 3:
        confidence = "high"
    elif n_dims == 2:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "overall_score": round(overall, 3),
        "confidence": confidence,
        "dimensions_available": n_dims,
        "contributing_scores": {
            dim: round(score, 3) for dim, score in dimension_scores.items()
        },
    }
