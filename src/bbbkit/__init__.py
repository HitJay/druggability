"""
bbbkit — 血脑屏障（BBB）通透性预测与药物设计工具包
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
from bbbkit.search import search, search_openalex, search_pubmed, search_arxiv, search_crossref, search_semanticscholar, search_paperclip

# 当 bbbkit.druggability 模块就绪时暴露
try:
    from bbbkit.druggability import assess_druggability  # type: ignore[import-untyped]

    druggability_available = True
except ImportError:
    assess_druggability = None  # type: ignore[assignment]
    druggability_available = False


# 肽性质预测平台（ESM-2 基座 + 轻量任务头）；可选依赖 torch/fair-esm/sklearn
try:
    from bbbkit.peptide import get_tasks as peptide_tasks  # type: ignore[import-untyped]

    peptide_available = True
except ImportError:
    peptide_tasks = None  # type: ignore[assignment]
    peptide_available = False


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
    "peptide_tasks",
    "peptide_available",
    "__version__",
]