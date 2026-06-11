#!/usr/bin/env python
"""
6 靶点深度可药性评估 — 编排脚手架 (Phase 0)

设计文档: docs/druggability-deep-assessment-design.md

本脚手架在 **不改动核心模块** 的前提下跑通深度评估工作流:
  1. 读取靶点 CSV (gene_name, gene_id, genetics, genetics_traits)
  2. 复用现有 bbbkit.druggability.assess_druggability 拿到
     tractability / ligandability / (可选) structure
  3. 自包含的 Open Targets 遗传学富集 (associatedDiseases + genetic_association
     datatype score) -> genetics_score  ⭐ 新支柱
  4. 模态分解 + 简单模态推荐 + DEEP_WEIGHTS 综合分
  5. 输出: 对比矩阵 CSV + 每靶 markdown one-pager + 原始 JSON

后续 Phase 1-2 会把遗传学/clinical/safety 折叠进核心模块的单次 GraphQL 调用
(见 docs/design-opentargets-expansion.md)。本脚手架的在线调用全部 try/except,
网络不可用时优雅降级并把已得结果落盘。

用法:
    python scripts/run_deep_druggability.py                      # 默认: data/druggability_targets.csv, 不跑结构
    python scripts/run_deep_druggability.py --structure          # 额外跑 fpocket 结构层 (需装 fpocket)
    python scripts/run_deep_druggability.py --offline            # 只生成空矩阵脚手架, 不联网
    python scripts/run_deep_druggability.py --outdir /tmp/x      # 自定义输出目录
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import requests

# ── 让脚本能直接运行 (python scripts/...) 也能在装好包时运行 ──
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("deep_druggability")

OPEN_TARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"

# ── 深度模式权重 (独立于 batch 模式的 DEFAULT_WEIGHTS, 不影响向后兼容) ──
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

# ── 遗传学富集 GraphQL (自包含, Phase 2 将折叠进核心模块) ──
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

    genetic_assoc_score: float = 0.0          # OT genetic_association datatype 最高分
    overall_top_disease: str = ""
    overall_top_score: float = 0.0
    n_associated_diseases: int = 0
    top_therapeutic_areas: list[str] = field(default_factory=list)
    genetics_score: float = 0.0               # 证据阶梯综合分 (0-1)
    direction: str = "unresolved (Phase 2)"   # 效应方向: 需 evidence 层 beta/OR
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _compute_genetics_score(has_gwas: bool, genetic_assoc_score: float) -> float:
    """
    遗传学证据阶梯 (脚手架版, 见设计文档 §2.3):
      0.40  存在 GWAS 关联 (CSV genetics=TRUE 即满足, 地板分)
    + 0.30 * OT genetic_association datatype 分
    + [Phase 2] 共定位 / 稀有变异 / 方向 的加成暂为 0
    """
    score = 0.0
    if has_gwas:
        score += 0.40
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

    res.genetics_score = _compute_genetics_score(has_gwas, res.genetic_assoc_score)
    return res


def _recommend_modality(tract: dict) -> tuple[str, str]:
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
    # 平局提示 (e.g. SM 与 Ab 同分时, max() 默认取 SM, 需人工按靶点类别裁决)
    tied = [m for m, s in scores.items() if s == scores[best]]
    tie_note = ""
    if len(tied) > 1:
        tie_note = f" [平局: {'/'.join(label_map[m] for m in tied)} 同为 {scores[best]:.2f}, 按靶点类别人工裁决]"
    return best, f"首选 {label_map[best]} (score={scores[best]:.2f}){tie_note}; 多肽/类别精修见 Phase 4"


def _deep_composite(dimensions: dict[str, float]) -> tuple[float, str]:
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


def assess_one(row: pd.Series, *, include_structure: bool, offline: bool) -> dict[str, Any]:
    """对单个靶点跑深度评估, 返回扁平记录 (供矩阵) + 嵌套原始 (供 JSON/报告)。"""
    gene = str(row["gene_name"])
    ensembl = str(row["gene_id"])
    trait = str(row.get("genetics_traits", ""))
    has_gwas = bool(row.get("genetics", True))

    record: dict[str, Any] = {
        "gene_name": gene,
        "gene_id": ensembl,
        "gwas_trait": trait,
        "gwas_trait_label": TRAIT_LABELS.get(trait, trait),
    }
    raw: dict[str, Any] = {"input": dict(row)}

    if offline:
        record.update(genetics_score=None, tractability_best=None, best_modality="(offline)",
                      ligandability_score=None, structure_score=None,
                      overall_score=None, confidence="offline", recommendation="(offline scaffold)")
        return {"record": record, "raw": raw}

    # ── tractability + ligandability + (可选) structure: 复用现有核心 ──
    full: dict[str, Any] = {}
    try:
        from bbbkit.druggability import assess_druggability
        full = assess_druggability(
            ensembl,
            query_type="ensembl_id",
            include_structure_analysis=include_structure,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("assess_druggability failed for %s: %s", gene, e)
        full = {"error": str(e)}
    raw["assess_druggability"] = full

    tract = full.get("tractability", {}) if isinstance(full, dict) else {}
    lig = full.get("ligandability", {}) if isinstance(full, dict) else {}
    pocket = full.get("pocket_analysis", {}) if isinstance(full, dict) else {}

    # ── 遗传学富集 (新支柱) ──
    gen = enrich_genetics(ensembl, has_gwas)
    raw["genetics"] = gen.to_dict()

    best_modality, rec_modality = _recommend_modality(tract)

    tract_best = tract.get("best_score") if isinstance(tract, dict) and "error" not in tract else None
    lig_score = lig.get("ligandability_score") if isinstance(lig, dict) and "error" not in lig else None
    struct_score = (
        pocket.get("best_druggability_score")
        if isinstance(pocket, dict) and pocket and "error" not in pocket
        else None
    )

    overall, confidence = _deep_composite({
        "genetics": gen.genetics_score,
        "tractability": tract_best,
        "ligandability": lig_score,
        "structure": struct_score,
    })

    # ── 推荐结论 (脚手架启发式) ──
    if gen.genetics_score and tract_best:
        if gen.genetics_score >= 0.55 and tract_best >= 0.6:
            verdict = "Priority — 高验证 + 易成药, 建议立项"
        elif gen.genetics_score >= 0.55 and tract_best < 0.6:
            verdict = "Hard but worth it — 验证强但成药难, 需模态创新"
        elif tract_best >= 0.6:
            verdict = "Tractable but verify — 易成药, 遗传学待加强"
        else:
            verdict = "Watch — 两轴均中等, 暂观察"
    else:
        verdict = "Incomplete — 数据不全 (见 raw JSON)"

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
        recommendation=verdict,
    )
    return {"record": record, "raw": raw}


def _write_report(rec: dict[str, Any], raw: dict[str, Any], path: Path) -> None:
    """写每靶 markdown one-pager。"""
    g = rec["gene_name"]
    lines = [
        f"# {g} — 深度可药性 one-pager",
        "",
        f"> Ensembl: `{rec['gene_id']}` | GWAS: **{rec['gwas_trait']}** ({rec.get('gwas_trait_label','')})",
        f"> 生成: {_dt.date.today().isoformat()} | 脚本: scripts/run_deep_druggability.py",
        "",
        "## 结论",
        f"- **推荐:** {rec.get('recommendation','N/A')}",
        f"- **最优模态:** {rec.get('best_modality','N/A')} — {rec.get('modality_note','')}",
        f"- **综合分:** {rec.get('overall_score','N/A')} (confidence: {rec.get('confidence','N/A')})",
        "",
        "## 二维定位",
        f"- **验证轴 (genetics_score):** {rec.get('genetics_score','N/A')} "
        f"(OT genetic_association={rec.get('genetic_assoc_score','N/A')}, 方向={rec.get('direction','N/A')})",
        f"- **可药轴 (tractability_best):** {rec.get('tractability_best','N/A')}",
        "",
        "## 维度明细",
        "| 维度 | 值 |",
        "|---|---|",
        f"| 靶点类别 (biotype) | {rec.get('target_class','')} |",
        f"| top 疾病关联 | {rec.get('top_disease','')} |",
        f"| 治疗领域 | {rec.get('top_therapeutic_areas','')} |",
        f"| tractability SM / Ab / PROTAC | {rec.get('tract_SM')} / {rec.get('tract_Ab')} / {rec.get('tract_PROTAC')} |",
        f"| ligandability (已知配体 / 获批药) | {rec.get('ligandability_score')} ({rec.get('n_known_ligands')} / {rec.get('n_approved_drugs')}) |",
        f"| structure (fpocket 最佳) | {rec.get('structure_score')} |",
        "",
        "## 待人工复核 (Phase 2+)",
        "- GWAS 效应方向 (beta/OR) → 决定激动/拮抗",
        "- 旁系同源选择性 / 组织特异性 τ / gnomAD 约束",
        "- 多结构 fpocket + 模态精修",
        "",
        "<details><summary>原始数据 (raw JSON)</summary>",
        "",
        "```json",
        json.dumps(raw, ensure_ascii=False, indent=2, default=str)[:6000],
        "```",
        "</details>",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="6 靶点深度可药性评估编排脚手架")
    parser.add_argument("--input", default=str(_REPO_ROOT / "data" / "druggability_targets.csv"))
    today = _dt.date.today().isoformat()
    parser.add_argument("--outdir", default=str(_REPO_ROOT / "output" / today / "druggability_6targets"))
    parser.add_argument("--structure", action="store_true", help="额外跑 fpocket 结构层 (需装 fpocket)")
    parser.add_argument("--offline", action="store_true", help="只生成脚手架, 不联网")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 个 (调试用)")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if args.limit > 0:
        df = df.head(args.limit)
    logger.info("loaded %d targets from %s", len(df), args.input)

    outdir = Path(args.outdir)
    (outdir / "reports").mkdir(parents=True, exist_ok=True)
    (outdir / "raw").mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        gene = str(row["gene_name"])
        logger.info("assessing %s ...", gene)
        out = assess_one(row, include_structure=args.structure, offline=args.offline)
        rec, raw = out["record"], out["raw"]
        records.append(rec)
        (outdir / "raw" / f"{gene}.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        if not args.offline:
            _write_report(rec, raw, outdir / "reports" / f"{gene}.md")

    matrix = pd.DataFrame(records)
    matrix_path = outdir / "deep_druggability_matrix.csv"
    matrix.to_csv(matrix_path, index=False)
    logger.info("wrote matrix: %s", matrix_path)
    logger.info("wrote %d reports + raw JSON to %s", len(records), outdir)

    # 终端速览
    cols = [c for c in ["gene_name", "gwas_trait", "genetics_score",
                        "tractability_best", "best_modality", "overall_score",
                        "recommendation"] if c in matrix.columns]
    print("\n" + matrix[cols].to_string(index=False))


if __name__ == "__main__":
    main()
