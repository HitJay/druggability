"""
冒烟测试 — 验证 OpenAlex 检索功能基本可用
运行: conda activate research && python -m pytest tests/test_search.py -v
"""

import sys
import os

# 确保 src 在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_openalex_search_returns_results():
    """OpenAlex 搜索 'druggability' 应该返回非空结果。"""
    from litkit.search import search_openalex

    results = search_openalex("druggability", limit=3)
    assert isinstance(results, list), "返回类型应为 list"
    assert len(results) > 0, "搜索 'druggability' 应返回至少 1 条结果"
    # 每条结果应有 title
    for r in results:
        assert "title" in r, "每条结果应包含 title 字段"


def test_openalex_search_limit():
    """OpenAlex 搜索应尊重 limit 参数。"""
    from litkit.search import search_openalex

    results = search_openalex("kinase inhibitor", limit=5)
    assert len(results) <= 5, f"结果数量 {len(results)} 超过 limit=5"


def test_unified_search_interface():
    """统一 search() 接口应可正确路由。"""
    from litkit.search import search, SOURCES

    # 应支持 openalex
    assert "openalex" in SOURCES

    results = search("PROTAC", source="openalex", limit=2)
    assert isinstance(results, list)
    assert len(results) > 0


def test_unified_search_unknown_source():
    """未知数据源应抛出 ValueError。"""
    from litkit.search import search
    import pytest

    with pytest.raises(ValueError, match="Unknown source"):
        search("test", source="nonexistent")


def test_crossref_search():
    """CrossRef 搜索应返回含 DOI 的结果。"""
    from litkit.search import search_crossref

    results = search_crossref("druggability", limit=3)
    assert isinstance(results, list)
    if results:  # CrossRef 可能偶尔超时
        assert "doi" in results[0]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
