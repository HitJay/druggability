"""
litkit — 学术文献检索 + 解析 + 可药性评估工具包
用于 druggability 研究的文献挖掘流水线
"""

from pathlib import Path

# ── 自动加载 .env 文件（若存在）─────────────────────────────
# 模块只会被 import 一次，不需要额外的 "loaded" flag。


def _load_dotenv() -> None:
    """查找并加载 .env 文件（优先 CWD，其次仓库根目录）。"""
    from dotenv import load_dotenv

    candidates = (
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    )
    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return


_load_dotenv()


__version__ = "0.1.0"

# ── 公开 API ─────────────────────────────────────────────────────
from litkit.search import search, search_openalex, search_pubmed, search_arxiv, search_crossref, search_semanticscholar, search_paperclip

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
    "search_paperclip",
    "assess_druggability",
    "druggability_available",
    "__version__",
]