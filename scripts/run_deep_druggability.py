#!/usr/bin/env python
"""
6 靶点深度可药性评估 — 薄壳 CLI (编排逻辑见 bbbkit.druggability.deep)

设计文档: docs/druggability-deep-assessment-design.md

用法:
    python scripts/run_deep_druggability.py                      # 默认: data/druggability_targets.csv
    python scripts/run_deep_druggability.py --structure          # 额外跑 fpocket 结构层 (需装 fpocket)
    python scripts/run_deep_druggability.py --offline            # 不联网, 仅生成脚手架
    python scripts/run_deep_druggability.py --outdir /tmp/x      # 自定义输出目录

注: 富文本报告 (HTML + PPTX, 含 LLM 叙述) 请用 `bbbkit report` 子命令。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# ── 让脚本能直接运行 (python scripts/...) 也能在装好包时运行 ──
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from bbbkit.druggability.deep import assess_targets  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("deep_druggability")


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
    parser = argparse.ArgumentParser(description="6 靶点深度可药性评估 (薄壳)")
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

    def _progress(done: int, total: int, gene: str) -> None:
        logger.info("[%d/%d] assessing %s ...", done, total, gene)

    results = assess_targets(
        df.to_dict("records"),
        include_structure=args.structure,
        offline=args.offline,
        on_progress=_progress,
    )

    records: list[dict[str, Any]] = []
    for out in results:
        rec, raw = out["record"], out["raw"]
        records.append(rec)
        gene = rec["gene_name"]
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

    cols = [c for c in ["gene_name", "gwas_trait", "genetics_score",
                        "tractability_best", "best_modality", "overall_score",
                        "recommendation"] if c in matrix.columns]
    print("\n" + matrix[cols].to_string(index=False))


if __name__ == "__main__":
    main()
