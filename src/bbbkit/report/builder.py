"""
bbbkit.report.builder — 报告编排

把"评估 → LLM 叙述 → 渲染 HTML + PPTX + 落盘"串成一步。

用法:
    from bbbkit.report import build_report
    bundle = build_report(
        [{"gene_name": "ADORA1", "gene_id": "ENSG00000163485", "gwas_trait": "WHRadjBMI"}],
        outdir="output/2026-06-11/my_report",
    )
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..druggability.deep import assess_targets
from .llm import LLMClient, generate_executive_summary, generate_target_narrative
from .render_html import render_html
from .render_pptx import render_pptx

logger = logging.getLogger(__name__)


@dataclass
class ReportBundle:
    """报告产物路径集合。"""

    outdir: str
    html_path: str = ""
    pptx_path: str = ""
    matrix_csv: str = ""
    raw_dir: str = ""
    records: list[dict[str, Any]] = field(default_factory=list)
    llm_status: str = ""

    def to_dict(self) -> dict:
        return {
            "outdir": self.outdir,
            "html_path": self.html_path,
            "pptx_path": self.pptx_path,
            "matrix_csv": self.matrix_csv,
            "raw_dir": self.raw_dir,
            "n_targets": len(self.records),
            "llm_status": self.llm_status,
        }


def build_report(
    targets: list[dict[str, Any]],
    outdir: str,
    *,
    title: str = "靶点深度可药性评估报告",
    include_structure: bool = False,
    offline: bool = False,
    use_llm: bool = True,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> ReportBundle:
    """
    端到端生成报告 (HTML + PPTX)。

    Parameters
    ----------
    targets : list[dict]
        每项含 gene_name + gene_id; 可选 gwas_trait / genetics(bool)。
    outdir : str
        输出目录 (会创建)。
    include_structure : bool
        是否跑 fpocket 结构层 (需装 fpocket)。
    offline : bool
        不联网 (仅脚手架占位)。
    use_llm : bool
        是否调用 LLM 生成叙述 (False 或无配置时回退模板)。

    Returns
    -------
    ReportBundle
    """
    out = Path(outdir)
    (out / "raw").mkdir(parents=True, exist_ok=True)

    # ── 1. 评估 ──
    logger.info("assessing %d targets ...", len(targets))
    results = assess_targets(
        targets,
        include_structure=include_structure,
        offline=offline,
        on_progress=on_progress,
    )
    records = [r["record"] for r in results]

    # 落盘原始 JSON
    for r in results:
        gene = r["record"].get("gene_name", "target")
        (out / "raw" / f"{gene}.json").write_text(
            json.dumps(r["raw"], ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )

    # ── 2. LLM 叙述 ──
    client = LLMClient() if use_llm else _DisabledLLM()
    llm_status = client.status
    logger.info("LLM: %s", llm_status)

    exec_summary = generate_executive_summary(client, records) if not offline else "(offline: 未生成叙述)"
    for rec in records:
        if offline:
            rec["_narrative"] = "(offline: 未生成叙述)"
        else:
            rec["_narrative"] = generate_target_narrative(client, rec)

    # ── 3. 矩阵 CSV ──
    matrix_csv = out / "deep_druggability_matrix.csv"
    _write_matrix_csv(records, matrix_csv)

    # ── 4. 渲染 HTML + PPTX ──
    html_path = out / "report.html"
    html_str = render_html(records, title=title, exec_summary=exec_summary, llm_status=llm_status)
    html_path.write_text(html_str, encoding="utf-8")

    pptx_path = out / "report.pptx"
    try:
        render_pptx(records, str(pptx_path), title=title, exec_summary=exec_summary)
    except Exception as e:  # noqa: BLE001
        logger.error("PPTX 渲染失败: %s", e)
        pptx_path = Path("")

    bundle = ReportBundle(
        outdir=str(out),
        html_path=str(html_path),
        pptx_path=str(pptx_path),
        matrix_csv=str(matrix_csv),
        raw_dir=str(out / "raw"),
        records=records,
        llm_status=llm_status,
    )
    logger.info("report written to %s", out)
    return bundle


def _write_matrix_csv(records: list[dict[str, Any]], path: Path) -> None:
    import csv

    if not records:
        path.write_text("", encoding="utf-8")
        return
    # 排除内部字段 (_narrative 等)
    cols: list[str] = []
    for r in records:
        for k in r:
            if not k.startswith("_") and k not in cols:
                cols.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k) for k in cols})


class _DisabledLLM:
    """use_llm=False 时的占位，强制回退模板。"""

    enabled = False
    status = "LLM disabled (--no-llm) — fallback to templates"

    def chat(self, *a, **k):  # noqa: D401, ANN002, ANN003
        return None
