"""
统一学术检索接口 — OpenAlex / Semantic Scholar / PubMed (Entrez) / arXiv / CrossRef
"""

from __future__ import annotations

import os
from typing import Any

import pyalex
from pyalex import Works
from semanticscholar import SemanticScholar
import arxiv
from Bio import Entrez
from crossref.restful import Works as CRWorks
from habanero import Crossref

# ── OpenAlex ───────────────────────────────────────────────────────────
# 设置 polite pool（加邮箱可获得更高速率）
pyalex.config.email = os.getenv("OPENALEX_EMAIL", "your@email.com")


def search_openalex(
    query: str,
    limit: int = 20,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """用 OpenAlex 搜索论文，返回字典列表。

    Args:
        query: 搜索关键词，如 "druggability AND kinase"
        limit: 最大返回数量
        fields: 需要的字段（None 返回全部）

    Returns:
        list[dict]: 每篇论文的元数据
    """
    results = []
    for page in Works().search(query).paginate(per_page=min(limit, 200)):
        for work in page:
            results.append(work)
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
    return results[:limit]


# ── Semantic Scholar ──────────────────────────────────────────────────
_s2_client: SemanticScholar | None = None


def _get_s2() -> SemanticScholar:
    global _s2_client
    if _s2_client is None:
        api_key = os.getenv("S2_API_KEY")
        _s2_client = SemanticScholar(api_key=api_key) if api_key else SemanticScholar()
    return _s2_client


def search_semantic_scholar(
    query: str,
    limit: int = 20,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """用 Semantic Scholar Graph API 搜索论文。

    Args:
        query: 搜索关键词
        limit: 最大返回数量
        fields: API 字段列表，默认 ['title','abstract','year','citationCount','externalIds']

    Returns:
        list[dict]
    """
    if fields is None:
        fields = ["title", "abstract", "year", "citationCount", "externalIds"]
    sch = _get_s2()
    results = sch.search_paper(query, limit=limit, fields=fields)
    return [r.raw_data for r in results] if results else []


# ── PubMed (Entrez) ──────────────────────────────────────────────────
Entrez.email = os.getenv("NCBI_EMAIL", "your@email.com")
Entrez.api_key = os.getenv("NCBI_API_KEY", None)


def search_pubmed(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """用 PubMed E-utilities 搜索论文，返回摘要级元数据。

    Args:
        query: PubMed 查询语句，如 "PROTAC druggability"
        limit: 最大返回数量

    Returns:
        list[dict]: 含 PMID, title, abstract 等
    """
    handle = Entrez.esearch(db="pubmed", term=query, retmax=limit)
    record = Entrez.read(handle)
    handle.close()

    pmids = record.get("IdList", [])
    if not pmids:
        return []

    handle = Entrez.efetch(db="pubmed", id=pmids, rettype="xml")
    records = Entrez.read(handle)
    handle.close()

    results = []
    for article in records.get("PubmedArticle", []):
        medline = article.get("MedlineCitation", {})
        art = medline.get("Article", {})
        abstract_parts = art.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(p) for p in abstract_parts)
        results.append(
            {
                "pmid": str(medline.get("PMID", "")),
                "title": str(art.get("ArticleTitle", "")),
                "abstract": abstract,
                "journal": str(
                    art.get("Journal", {}).get("Title", "")
                ),
                "year": str(
                    art.get("Journal", {})
                    .get("JournalIssue", {})
                    .get("PubDate", {})
                    .get("Year", "")
                ),
            }
        )
    return results


# ── arXiv ─────────────────────────────────────────────────────────────
def search_arxiv(
    query: str,
    limit: int = 20,
    sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
) -> list[dict[str, Any]]:
    """搜索 arXiv 论文。

    Args:
        query: arXiv 查询语句
        limit: 最大返回
        sort_by: 排序方式

    Returns:
        list[dict]
    """
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=limit, sort_by=sort_by)
    results = []
    for r in client.results(search):
        results.append(
            {
                "arxiv_id": r.entry_id,
                "title": r.title,
                "abstract": r.summary,
                "authors": [a.name for a in r.authors],
                "published": str(r.published.date()),
                "pdf_url": r.pdf_url,
                "categories": r.categories,
            }
        )
    return results


# ── CrossRef ──────────────────────────────────────────────────────────
def search_crossref(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """搜索 CrossRef（按 DOI 元数据检索）。

    Args:
        query: 检索关键词
        limit: 最大返回

    Returns:
        list[dict]
    """
    cr = Crossref()
    raw = cr.works(query=query, limit=limit)
    items = raw.get("message", {}).get("items", [])
    results = []
    for item in items:
        results.append(
            {
                "doi": item.get("DOI", ""),
                "title": " ".join(item.get("title", [])),
                "type": item.get("type", ""),
                "publisher": item.get("publisher", ""),
                "issued": item.get("issued", {}).get("date-parts", [[""]])[0],
                "citation_count": item.get("is-referenced-by-count", 0),
            }
        )
    return results


# ── 统一入口 ──────────────────────────────────────────────────────────
SOURCES = {
    "openalex": search_openalex,
    "s2": search_semantic_scholar,
    "pubmed": search_pubmed,
    "arxiv": search_arxiv,
    "crossref": search_crossref,
}


def search(
    query: str,
    source: str = "openalex",
    limit: int = 20,
    **kwargs,
) -> list[dict[str, Any]]:
    """统一检索入口。

    Args:
        query: 检索关键词
        source: 数据源名，openalex / s2 / pubmed / arxiv / crossref
        limit: 最大返回
        **kwargs: 传给对应数据源的额外参数

    Returns:
        list[dict]
    """
    fn = SOURCES.get(source)
    if fn is None:
        raise ValueError(f"Unknown source: {source!r}. Choose from {list(SOURCES)}")
    return fn(query, limit=limit, **kwargs)


if __name__ == "__main__":
    # 快速测试
    import json

    results = search_openalex("druggability", limit=3)
    for r in results:
        print(json.dumps({"title": r.get("title"), "doi": r.get("doi")}, indent=2))
