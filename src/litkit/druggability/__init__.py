"""
litkit.druggability — 靶点可药性评估核心模块

提供统一的 druggability 评估接口，集成多个数据源：
- Open Targets tractability API（知识库可追踪性）
- ChEMBL ligandability proxy（已知配体覆盖度）
- fpocket 口袋检测（基于结构的分析）
"""

from .tractability import query_tractability, TractabilityResult
from .ligandability import assess_ligandability, LigandabilityResult
from .pocket import detect_pockets, PocketAnalysisResult


def assess_druggability(
    query: str,
    query_type: str = "gene_symbol",
    structure_path: str | None = None,
    include_structure_analysis: bool = True,
) -> dict:
    """
    统一入口：对靶点执行 Tier 1（结构无关）druggability 评估。

    Parameters
    ----------
    query : str
        靶点标识符（gene symbol / UniProt ID / Ensembl ID）
    query_type : str
        标识符类型: "gene_symbol" | "uniprot_id" | "ensembl_id"
    structure_path : str | None
        PDB 文件路径。若提供则同时运行 fpocket 结构分析。
    include_structure_analysis : bool
        若为 True 且未提供 structure_path，尝试从 AlphaFold DB 自动获取结构。

    Returns
    -------
    dict
        综合 druggability 评估报告
    """
    result: dict = {
        "query": query,
        "query_type": query_type,
    }

    # Tier 1: Open Targets tractability
    try:
        tractability = query_tractability(query, query_type=query_type)
        result["tractability"] = tractability.to_dict()
    except Exception as e:
        result["tractability"] = {"error": str(e)}

    # Tier 1: ChEMBL ligandability
    try:
        ligandability = assess_ligandability(query)
        result["ligandability"] = ligandability.to_dict()
    except Exception as e:
        result["ligandability"] = {"error": str(e)}

    # Tier 2: Structure-based pocket analysis
    if include_structure_analysis or structure_path:
        try:
            pockets = detect_pockets(
                structure_path=structure_path or query,
                auto_download=structure_path is None,
            )
            result["pocket_analysis"] = pockets.to_dict()
        except Exception as e:
            result["pocket_analysis"] = {"error": str(e)}

    # Composite score
    result["composite"] = _compute_composite(result)
    return result


def _compute_composite(result: dict) -> dict:
    """
    合成多来源 druggability 综合评分（0-1）。
    """
    scores: list[float] = []

    tractability = result.get("tractability", {})
    if tractability and "error" not in tractability:
        # 映射 tractability category 到分数
        cat_map = {
            "Tractable with high-quality targets": 1.0,
            "Clinical Precedence": 0.9,
            "Discovery_Precedence": 0.7,
            "Predicted Tractable": 0.5,
            "Predicted to be tractable at high confidence": 0.5,
            "Discovery Precedence": 0.7,
        }
        for modality in ["small_molecule", "antibody", "protac"]:
            info = tractability.get(modality, {})
            cat = info.get("category", "")
            if cat in cat_map:
                scores.append(cat_map[cat])

    ligandability = result.get("ligandability", {})
    if ligandability and "error" not in ligandability:
        scores.append(ligandability.get("ligandability_score", 0.0))

    pocket_analysis = result.get("pocket_analysis", {})
    if pocket_analysis and "error" not in pocket_analysis:
        best = pocket_analysis.get("best_druggability_score", 0.0)
        scores.append(best)

    overall = sum(scores) / len(scores) if scores else 0.0
    return {
        "overall_score": round(overall, 3),
        "contributing_scores": {
            "tractability": scores[0] if len(scores) > 0 else None,
            "ligandability": scores[1] if len(scores) > 1 else None,
            "structure": scores[2] if len(scores) > 2 else None,
        },
    }