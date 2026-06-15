"""
bbbkit.peptide — ESM-2 肽序列性质预测平台（一个基座，多个轻量任务头）

把蛋白质语言模型（ESM-2）的序列嵌入计算一次并缓存，随后被多个下游肽性质任务头复用
（BBB / 抗癌 / 毒性 / 抗菌 / 溶血 …）。每个头是几秒可训练的轻量分类器。

公开 API：
    embed(sequences)                          —— 取（带缓存的）ESM-2 嵌入
    get_tasks([keys])                         —— 内置 benchmark 任务注册表
    run_benchmark(data_dir, [keys])           —— 端到端多任务评估
    datasets.download(data_dir, [keys])       —— 下载并规范化已发表 benchmark

可选依赖（`pip install 'bbbkit[peptide]'`）：torch、fair-esm、scikit-learn。
"""

from __future__ import annotations

from . import config as config  # noqa: F401  (stdlib-only, always import-safe)
from . import tasks as tasks  # noqa: F401  (always import-safe)
from .tasks import PeptideTask, get_tasks, REGISTRY  # noqa: F401

# embed / heads / benchmark 依赖 torch / sklearn，做优雅降级
try:
    from . import embed as embed  # noqa: F401
    from .embed import embed as embed_sequences  # noqa: F401
    from . import heads as heads  # noqa: F401
    from . import datasets as datasets  # noqa: F401
    from . import benchmark as benchmark  # noqa: F401
    from .benchmark import run_benchmark, run_task  # noqa: F401

    peptide_available = True
except ImportError:  # pragma: no cover - 缺少可选依赖时
    embed = None  # type: ignore[assignment]
    heads = None  # type: ignore[assignment]
    benchmark = None  # type: ignore[assignment]
    run_benchmark = None  # type: ignore[assignment]
    run_task = None  # type: ignore[assignment]
    peptide_available = False

# datasets 仅依赖 curl + 标准库，单独尝试导出（即便没有 torch 也能下载数据）
try:
    from . import datasets as datasets  # noqa: F401,F811
except ImportError:  # pragma: no cover
    datasets = None  # type: ignore[assignment]


__all__ = [
    "PeptideTask",
    "get_tasks",
    "REGISTRY",
    "tasks",
    "config",
    "embed",
    "embed_sequences",
    "heads",
    "datasets",
    "benchmark",
    "run_benchmark",
    "run_task",
    "peptide_available",
]
