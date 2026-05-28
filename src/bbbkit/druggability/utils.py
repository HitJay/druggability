"""
共用工具函数 — ID 转换、缓存装饰器、异常定义
"""

from __future__ import annotations

import functools
import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ─── 异常定义 ─────────────────────────────────────────────────────────


class DruggabilityError(Exception):
    """所有 druggability 模块异常的基类"""


class TargetNotFoundError(DruggabilityError):
    """靶点在目标数据库中未找到"""


class NetworkError(DruggabilityError):
    """外部 API 请求失败"""


class FpocketNotFoundError(DruggabilityError):
    """fpocket 可执行文件未安装"""


class FpocketTimeoutError(DruggabilityError):
    """fpocket 执行超时"""


class InvalidStructureError(DruggabilityError):
    """输入结构文件无效或无法解析"""


class DependencyMissingError(DruggabilityError):
    """必需的依赖未安装"""


# ─── ID 转换 ──────────────────────────────────────────────────────────


@functools.lru_cache(maxsize=256)
def gene_symbol_to_ensembl(gene_symbol: str) -> str | None:
    """
    使用 mygene.info 将基因 symbol 转为 Ensembl gene ID。

    Parameters
    ----------
    gene_symbol : str
        基因符号，如 "EGFR", "BRCA2"

    Returns
    -------
    str | None
        Ensembl gene ID，如 "ENSG00000146648"
    """
    try:
        import mygene

        mg = mygene.MyGeneInfo()
        result = mg.query(gene_symbol, species="human", fields="ensembl.gene", size=1)
        hits = result.get("hits", [])
        if hits:
            ensg = hits[0].get("ensembl", {}).get("gene")
            if ensg:
                return str(ensg)
        logger.warning("No Ensembl ID found for gene symbol: %s", gene_symbol)
        return None
    except ImportError:
        raise DependencyMissingError(
            "mygene is required for gene symbol → Ensembl ID conversion. "
            "Install with: pip install mygene"
        )
    except Exception as e:
        logger.error("Error resolving gene symbol '%s': %s", gene_symbol, e)
        return None


@functools.lru_cache(maxsize=256)
def gene_symbol_to_uniprot(gene_symbol: str) -> str | None:
    """
    使用 mygene.info 将基因 symbol 转为 UniProt Swiss-Prot accession。

    Parameters
    ----------
    gene_symbol : str
        基因符号，如 "EGFR", "KRAS"

    Returns
    -------
    str | None
        UniProt accession，如 "P00533"
    """
    try:
        import mygene

        mg = mygene.MyGeneInfo()
        result = mg.query(
            gene_symbol, species="human", fields="uniprot.Swiss-Prot", size=1
        )
        hits = result.get("hits", [])
        if hits:
            uniprot = hits[0].get("uniprot", {})
            swissprot = uniprot.get("Swiss-Prot")
            if isinstance(swissprot, list):
                return str(swissprot[0])
            elif swissprot:
                return str(swissprot)
        logger.warning("No UniProt ID found for gene symbol: %s", gene_symbol)
        return None
    except ImportError:
        raise DependencyMissingError(
            "mygene is required for gene symbol → UniProt conversion. "
            "Install with: pip install mygene"
        )
    except Exception as e:
        logger.error("Error resolving gene symbol '%s' to UniProt: %s", gene_symbol, e)
        return None


@functools.lru_cache(maxsize=256)
def uniprot_to_ensembl(uniprot_id: str) -> str | None:
    """
    将 UniProt ID 转为 Ensembl gene ID。

    Parameters
    ----------
    uniprot_id : str
        UniProt accession，如 "P00533"（EGFR）

    Returns
    -------
    str | None
        Ensembl gene ID
    """
    try:
        import mygene

        mg = mygene.MyGeneInfo()
        result = mg.query(
            f"uniprot:{uniprot_id}", species="human", fields="ensembl.gene", size=1
        )
        hits = result.get("hits", [])
        if hits:
            ensg = hits[0].get("ensembl", {}).get("gene")
            if ensg:
                return str(ensg)
        return None
    except ImportError:
        raise DependencyMissingError(
            "mygene is required for UniProt → Ensembl ID conversion. "
            "Install with: pip install mygene"
        )
    except Exception as e:
        logger.error("Error resolving UniProt '%s': %s", uniprot_id, e)
        return None


def resolve_ensembl_id(query: str, query_type: str = "gene_symbol") -> str | None:
    """
    统一入口：将任意形式的靶点标识符转为 Ensembl ID。

    优先通过 Open Targets search（单次 GraphQL），查不到时降级到 mygene.info。
    """
    try:
        from .tractability import resolve_target_info
        info = resolve_target_info(query, query_type=query_type)
        return info.ensembl_id if info else None
    except Exception:
        pass

    if query_type == "ensembl_id":
        if query.startswith("ENSG"):
            return query
        return None
    elif query_type == "uniprot_id":
        return uniprot_to_ensembl(query)
    elif query_type == "gene_symbol":
        return gene_symbol_to_ensembl(query)
    else:
        raise ValueError(f"Unknown query_type: {query_type}")


# ─── 速率限制装饰器 ────────────────────────────────────────────────────


def rate_limit(delay: float = 0.5) -> Callable:
    """
    装饰器：保证被装饰函数两次调用之间至少间隔 ``delay`` 秒。

    带 ``threading.Lock`` 以在多线程环境（如 ThreadPoolExecutor）
    中仍能正确限速，避免竞态。
    """

    def decorator(func: Callable) -> Callable:
        lock = threading.Lock()
        last_call: list[float] = [0.0]  # 用 list 让闭包可变

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with lock:
                elapsed = time.time() - last_call[0]
                if elapsed < delay:
                    time.sleep(delay - elapsed)
                last_call[0] = time.time()
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ─── 缓存工具 ─────────────────────────────────────────────────────────


class SimpleCache:
    """
    简单的内存缓存，支持 TTL。

    Parameters
    ----------
    ttl : int
        缓存有效时间（秒），默认 300（5 分钟）
    maxsize : int
        最大缓存条目数，默认 128
    """

    def __init__(self, ttl: int | float = 300, maxsize: int = 128):
        self._cache: dict[str, tuple[float, Any]] = {}
        self.ttl = ttl
        self.maxsize = maxsize

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self.ttl:
                return val
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if len(self._cache) >= self.maxsize:
            # 删除最旧的条目
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), value)

    def clear(self) -> None:
        self._cache.clear()