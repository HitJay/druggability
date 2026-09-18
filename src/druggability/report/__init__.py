"""
bbbkit.report — 可药性评估报告生成 (LLM 叙述 + HTML + PPTX)

入口:
    from bbbkit.report import build_report
    build_report(targets, outdir, ...)

子模块:
    llm           — OpenAI 兼容 LLM 客户端 (读 .env MARKETPLACE_*)
    render_html   — Jinja2 HTML 报告
    render_pptx   — python-pptx 幻灯片
    builder       — 编排: 评估 → LLM 叙述 → 渲染 HTML + PPTX
"""

from __future__ import annotations

from .builder import build_report, ReportBundle

__all__ = ["build_report", "ReportBundle"]
