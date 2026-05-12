"""
litkit — 学术文献检索 + 解析 + 可药性评估工具包
用于 druggability 研究的文献挖掘流水线
"""

import os
from pathlib import Path

# ── 自动加载 .env 文件（若存在） ─────────────────────────────────
_env_loaded = False


def _load_dotenv() -> None:
    """查找并加载 .env 文件（从 CWD 或包目录向上递归）。"""
    from dotenv import load_dotenv

    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
    ]
    for p in candidates:
        if p.is_file():
            load_dotenv(p, override=False)
            break


if not _env_loaded:
    _load_dotenv()
    _env_loaded = True


__version__ = "0.1.0"

# ── 公开 API ─────────────────────────────────────────────────────
from litkit.search import search, search_openalex, search_pubmed, search_arxiv, search_crossref, search_semanticscholar

# 当 litkit.druggability 模块就绪时暴露
try:
    from litkit.druggability import assess_druggability  # type: ignore[import-untyped]

    druggability_available = True
except ImportError:
    assess_druggability = None  # type: ignore[assignment]
    druggability_available = False


__all__ = [
    "search",
    "search_openalex",
    "search_pubmed",
    "search_arxiv",
    "search_crossref",
    "search_semanticscholar",
    "assess_druggability",
    "druggability_available",
    "__version__",
]