"""
bbbkit — 血脑屏障（BBB）通透性预测与药物设计工具包
"""

from pathlib import Path

# ── 自动加载 .env 文件（若存在）─────────────────────────────
# 模块只会被 import 一次，不需要额外的 "loaded" flag。


def _load_dotenv() -> None:
    """查找并加载 .env 文件（若存在）。python-dotenv 为可选依赖，缺失时静默跳过。"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

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


# Boltz-2 云端结构/亲和力预测（经 BioLib）；可选依赖 pybiolib
# 模块本身始终可 import（biolib 惰性导入），biolib_available 仅标记依赖是否就绪。
try:
    import biolib as _biolib  # noqa: F401

    from bbbkit import boltz as boltz  # noqa: F401

    boltz_available = True
except ImportError:
    boltz = None  # type: ignore[assignment]
    boltz_available = False


# DrugCLIP 虚拟筛选（本地仓库部署，Python 3.8 + Uni-Core + torch）
# 包装模块始终可 import；是否真正可用取决于环境是否已部署（见 drugclip.is_environment_ready）。
from bbbkit import drugclip as drugclip  # noqa: F401


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
    "boltz",
    "boltz_available",
    "drugclip",
    "__version__",
]