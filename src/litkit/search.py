"""
统一学术检索接口 — OpenAlex / PubMed (Entrez) / arXiv / CrossRef
"""

from __future__ import annotations

import os
from typing import Any


# ── OpenAlex ───────────────────────────────────────────────────────────
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
    import pyalex
    from pyalex import Works

    pyalex.config.email = os.getenv("OPENALEX_EMAIL", "your@email.com")

    # 同时传 per_page 和 n_max：
    # - per_page 限制单页大小（最大 200）
    # - n_max 限制 pyalex 总拉取量，避免在 limit 较大时被动拉几十万条。
    per_page = min(limit, 200)
    results: list[dict[str, Any]] = []
    for page in Works().search(query).paginate(per_page=per_page, n_max=limit):
        for work in page:
            results.append(work)
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
    return results[:limit]


# ── PubMed (Entrez) ──────────────────────────────────────────────────
def search_pubmed(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """用 PubMed E-utilities 搜索论文，返回摘要级元数据。

    Args:
        query: PubMed 查询语句，如 "PROTAC druggability"
        limit: 最大返回数量

    Returns:
        list[dict]: 含 PMID, title, abstract 等
    """
    from Bio import Entrez

    Entrez.email = os.getenv("NCBI_EMAIL", "your@email.com")
    Entrez.api_key = os.getenv("NCBI_API_KEY", None)

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
    sort_by: Any = None,
) -> list[dict[str, Any]]:
    """搜索 arXiv 论文。

    Args:
        query: arXiv 查询语句
        limit: 最大返回
        sort_by: 排序方式

    Returns:
        list[dict]
    """
    import arxiv

    if sort_by is None:
        sort_by = arxiv.SortCriterion.Relevance

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


# ── Semantic Scholar ─────────────────────────────────────────────────
def search_semanticscholar(
    query: str,
    limit: int = 20,
    min_citation_count: int | None = None,
    fields: list[str] | None = None,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """搜索 Semantic Scholar（直接 HTTP API 调用，避免 asyncio 在 Windows 上的问题）。

    需要设置环境变量 S2_API_KEY 以获得更高限速。
    免费层：1 req/s（无 API key），带 key 时提升至 10 req/s。

    Args:
        query: 检索关键词
        limit: 最大返回
        min_citation_count: 最小引用数过滤
        fields: 需要的字段（None 返回默认字段）
        timeout: 请求超时秒数

    Returns:
        list[dict]
    """
    import os
    import time

    import requests

    api_key = os.environ.get("S2_API_KEY", "")
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    if fields is None:
        fields = [
            "title", "abstract", "externalIds", "url",
            "citationCount", "publicationDate", "venue",
            "authors", "fieldsOfStudy", "openAccessPdf",
        ]

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": ",".join(fields),
    }

    resp = requests.get(url, params=params, headers=headers, timeout=timeout)

    if resp.status_code == 429:
        import warnings
        warnings.warn(
            f"Semantic Scholar rate limited (429). "
            f"Set S2_API_KEY env var for higher limits."
        )
        return []

    resp.raise_for_status()
    data = resp.json()
    items = data.get("data", [])

    if api_key:
        time.sleep(0.15)
    else:
        time.sleep(1.1)

    results = []
    for item in items:
        if min_citation_count is not None:
            cit = item.get("citationCount", 0) or 0
            if cit < min_citation_count:
                continue
        authors_raw = item.get("authors") or []
        results.append(
            {
                "paper_id": item.get("paperId", ""),
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
                "url": item.get("url", ""),
                "venue": item.get("venue", ""),
                "publication_date": str(item.get("publicationDate") or ""),
                "citation_count": item.get("citationCount", 0),
                "authors": [
                    a.get("name", str(a)) for a in authors_raw
                ],
                "fields_of_study": item.get("fieldsOfStudy") or [],
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
    from habanero import Crossref

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
    "pubmed": search_pubmed,
    "arxiv": search_arxiv,
    "crossref": search_crossref,
    "semanticscholar": search_semanticscholar,
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
        source: 数据源名，openalex / pubmed / arxiv / crossref
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