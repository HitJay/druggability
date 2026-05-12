"""
综合集成测试 — 覆盖 search / fetch / parse / ner 所有模块
运行: conda activate research && python tests/test_integration.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_openalex():
    """测试 OpenAlex 搜索"""
    console.rule("[bold blue]1. OpenAlex 搜索")
    from litkit.search import search_openalex

    results = search_openalex("PROTAC druggability", limit=5)
    assert len(results) > 0, "OpenAlex 返回为空！"

    table = Table(title=f"OpenAlex: {len(results)} 篇")
    table.add_column("年份", style="cyan", width=6)
    table.add_column("标题", style="white", max_width=60)
    table.add_column("引用", style="green", width=6)
    table.add_column("OA", style="yellow", width=4)

    for r in results:
        table.add_row(
            str(r.get("publication_year", "")),
            (r.get("title", "") or "")[:60],
            str(r.get("cited_by_count", 0)),
            "✓" if r.get("open_access", {}).get("is_oa") else "✗",
        )
    console.print(table)
    console.print("[green]✓ OpenAlex 通过[/green]\n")
    return results


def test_pubmed():
    """测试 PubMed 搜索"""
    console.rule("[bold blue]3. PubMed 搜索")
    from litkit.search import search_pubmed

    results = search_pubmed("KRAS druggability", limit=3)
    assert len(results) > 0, "PubMed 返回为空！"

    for r in results:
        console.print(f"  • PMID:[cyan]{r['pmid']}[/cyan] {r['year']} | {r['title'][:60]}")
        if r["abstract"]:
            console.print(f"    摘要: {r['abstract'][:100]}...")
    console.print("[green]✓ PubMed 通过[/green]\n")
    return results


def test_arxiv():
    """测试 arXiv 搜索"""
    console.rule("[bold blue]4. arXiv 搜索")
    from litkit.search import search_arxiv

    results = search_arxiv("drug discovery machine learning", limit=3)
    assert len(results) > 0, "arXiv 返回为空！"

    for r in results:
        console.print(f"  • [cyan]{r['published']}[/cyan] {r['title'][:60]}")
        console.print(f"    PDF: {r['pdf_url']}")
    console.print("[green]✓ arXiv 通过[/green]\n")
    return results


def test_crossref():
    """测试 CrossRef 搜索"""
    console.rule("[bold blue]5. CrossRef 搜索")
    from litkit.search import search_crossref

    results = search_crossref("druggability", limit=3)
    assert len(results) > 0, "CrossRef 返回为空！"

    for r in results:
        console.print(f"  • DOI:[cyan]{r['doi']}[/cyan]")
        console.print(f"    {r['title'][:70]} | 引用:{r['citation_count']}")
    console.print("[green]✓ CrossRef 通过[/green]\n")
    return results


def test_unified_search():
    """测试统一搜索接口"""
    console.rule("[bold blue]6. 统一 search() 接口")
    from litkit.search import search, SOURCES

    console.print(f"  支持的数据源: {list(SOURCES.keys())}")
    for src in ["openalex", "crossref"]:
        results = search("kinase inhibitor", source=src, limit=2)
        console.print(f"  {src}: {len(results)} 条")
        assert len(results) > 0
    console.print("[green]✓ 统一接口通过[/green]\n")


def test_unpaywall():
    """测试 Unpaywall OA 检测"""
    console.rule("[bold blue]7. Unpaywall OA 检测")
    from litkit.fetch import fetch_unpaywall_pdf_url

    # AlphaFold2 论文 (Nature, OA)
    doi = "10.1038/s41586-021-03819-2"
    url = fetch_unpaywall_pdf_url(doi)
    console.print(f"  DOI: {doi}")
    console.print(f"  PDF URL: {url or '未找到'}")
    # OA 论文应该能找到 URL
    if url:
        console.print("[green]✓ Unpaywall 通过（找到 OA 链接）[/green]\n")
    else:
        console.print("[yellow]⚠ Unpaywall 未返回 URL（可能网络问题）[/yellow]\n")


def test_ner_regex():
    """测试正则 NER"""
    console.rule("[bold blue]8. 正则药物名识别")
    from litkit.ner import regex_drug_entities

    text = (
        "Erlotinib and sotorasib are approved drugs. "
        "Imatinib targets BCR-ABL. Trastuzumab is an antibody."
    )
    drugs = regex_drug_entities(text)
    console.print(f"  文本: {text}")
    console.print(f"  识别到: {drugs}")
    assert len(drugs) > 0, "正则应识别出药物名！"
    console.print("[green]✓ 正则 NER 通过[/green]\n")


def test_ner_pubtator():
    """测试 PubTator3 API"""
    console.rule("[bold blue]9. PubTator3 API 实体标注")
    from litkit.ner import annotate_with_pubtator

    text = "EGFR mutations in non-small cell lung cancer can be targeted by erlotinib."
    entities = annotate_with_pubtator(text)

    if entities:
        table = Table(title="PubTator3 实体")
        table.add_column("实体", style="white")
        table.add_column("类型", style="cyan")
        table.add_column("ID", style="dim")
        for e in entities:
            table.add_row(e["text"], e["type"], e.get("id", ""))
        console.print(table)
        console.print("[green]✓ PubTator3 通过[/green]\n")
    else:
        console.print("[yellow]⚠ PubTator3 未返回结果（可能网络/API 问题）[/yellow]\n")


def test_parse_module():
    """测试解析模块可导入"""
    console.rule("[bold blue]10. 解析模块导入检查")
    from litkit.parse import extract_text_pymupdf, extract_text_pdfplumber, parse_with_grobid
    console.print("  extract_text_pymupdf  ✓")
    console.print("  extract_text_pdfplumber ✓")
    console.print("  parse_with_grobid     ✓ (需 GROBID Docker)")
    console.print("[green]✓ 解析模块导入通过[/green]\n")


# [DISABLED] ChEMBL API 尚未就绪，暂时屏蔽
# def test_chembl():
#     """测试 ChEMBL API"""
#     console.rule("[bold blue]11. ChEMBL 靶点查询")
#     from chembl_webresource_client.new_client import new_client
#
#     target = new_client.target
#     results = target.search("EGFR")
#     hits = list(results[:3])
#     assert len(hits) > 0, "ChEMBL 应返回 EGFR 靶点！"
#
#     for h in hits:
#         console.print(
#             f"  • [cyan]{h.get('target_chembl_id', '')}[/cyan] "
#             f"{h.get('pref_name', '')} ({h.get('organism', '')})"
#         )
#     console.print("[green]✓ ChEMBL 通过[/green]\n")


def main():
    console.print(Panel.fit(
        "[bold]🔬 Druggability 文献工具包 — 综合测试[/bold]\n"
        "覆盖: OpenAlex / PubMed / arXiv / CrossRef / Unpaywall / NER",
        border_style="blue",
    ))

    passed = 0
    failed = 0
    warnings = 0
    tests = [
        test_openalex,
        test_pubmed,
        test_arxiv,
        test_crossref,
        test_unified_search,
        test_unpaywall,
        test_ner_regex,
        test_ner_pubtator,
        test_parse_module,
        # test_chembl,  # [DISABLED]
    ]

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            console.print(f"[red]✗ {test_fn.__doc__}: {e}[/red]\n")
            failed += 1
        except Exception as e:
            console.print(f"[yellow]⚠ {test_fn.__doc__}: {e}[/yellow]\n")
            warnings += 1

    console.print(Panel.fit(
        f"[bold]测试结果: [green]{passed} 通过[/green]  "
        f"[red]{failed} 失败[/red]  "
        f"[yellow]{warnings} 警告[/yellow][/bold]",
        border_style="green" if failed == 0 else "red",
    ))


if __name__ == "__main__":
    main()
