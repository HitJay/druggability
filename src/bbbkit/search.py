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


# ── Paperclip（生物医学论文 CLI）────────────────────────────────────
def _parse_paperclip_output(output: str, limit: int = 20) -> list[dict[str, Any]]:
    """解析 paperclip 搜索结果的文本输出格式。
    
    格式示例：
        1. Title of paper
           Author Names
           ID · Source · Date
           https://url.com
           "Abstract text here"
        
        2. Another title
           ...

    Args:
        output: paperclip search 命令的原始输出
        limit: 最大返回论文数

    Returns:
        list[dict]: 标准化的论文元数据列表
    """
    import re

    papers = []
    lines = output.split("\n")
    i = 0
    
    while i < len(lines) and len(papers) < limit:
        line = lines[i].strip()
        
        # 找到论文编号行（如 "1. Title" 或 "  1. Title"）
        match = re.match(r'^\s*\d+\.\s+(.+)$', line)
        if match:
            title = match.group(1).strip()
            authors = ""
            paper_id = ""
            source = ""
            pub_date = ""
            url = ""
            abstract = ""
            
            # 读取接下来的行来提取元数据
            i += 1
            while i < len(lines):
                current_line = lines[i]
                stripped = current_line.strip()
                
                # 如果遇到下一个论文编号或空行太多，停止
                if re.match(r'^\s*\d+\.\s+', current_line):
                    break
                
                # 空行或注释行，跳过
                if not stripped or stripped.startswith("[") or stripped.startswith("💡") or stripped.startswith("Tip:"):
                    i += 1
                    if not stripped:
                        # 连续空行可能表示论文结束
                        next_i = i
                        while next_i < len(lines) and not lines[next_i].strip():
                            next_i += 1
                        if next_i < len(lines) and not re.match(r'^\s*\d+\.\s+', lines[next_i]):
                            i = next_i
                        else:
                            break
                    continue
                
                # 作者行（通常是缩进的）
                if authors == "" and current_line.startswith("     ") and not any(c in stripped for c in ["·", "http", "@"]):
                    authors = stripped
                    i += 1
                    continue
                
                # ID · Source · Date 行（包含 ·）
                if "·" in stripped:
                    parts = stripped.split("·")
                    if len(parts) >= 3:
                        paper_id = parts[0].strip()
                        source = parts[1].strip()
                        pub_date = parts[2].strip() if len(parts) > 2 else ""
                    i += 1
                    continue
                
                # URL 行
                if stripped.startswith("http"):
                    url = stripped
                    i += 1
                    continue
                
                # 摘要行（通常用引号包围）
                if stripped.startswith('"') and stripped.endswith('"'):
                    abstract = stripped.strip('"')
                    i += 1
                    break  # 论文结束
                
                i += 1
            
            # 只有在有标题的情况下才添加
            if title:
                papers.append(
                    {
                        "title": title,
                        "authors": authors,
                        "paper_id": paper_id,
                        "source": source,
                        "publication_date": pub_date,
                        "url": url,
                        "abstract": abstract,
                        "database": "paperclip",
                    }
                )
        else:
            i += 1
    
    return papers[:limit]


def search_paperclip(
    query: str,
    limit: int = 20,
    source_db: str | None = None,
    timeout: int = 60,
    use_wsl: bool = True,
) -> list[dict[str, Any]]:
    """用 Paperclip 搜索生物医学论文。

    需要先在 WSL/Unix 中安装 paperclip:
        wsl -d Ubuntu
        curl -fsSL https://paperclip.gxl.ai/install.sh | bash

    在 Windows 中运行本函数时，会自动通过 WSL 调用 paperclip。

    Args:
        query: 搜索关键词，如 "PROTAC druggability"
        limit: 最大返回数量（paperclip 会根据可用性返回）
        source_db: 指定数据源，如 'pmc', 'medline', 'fda' 等（可选）
        timeout: 命令执行超时秒数
        use_wsl: 在 Windows 上是否通过 WSL 调用 paperclip（推荐）

    Returns:
        list[dict]: 包含 title, abstract, url, source 等字段

    Raises:
        RuntimeError: paperclip 命令不存在或执行失败
        ValueError: 查询为空
    """
    import json
    import subprocess
    import shutil
    import platform

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # 尝试找到 paperclip 命令
    paperclip_path = shutil.which("paperclip")
    is_windows = platform.system() == "Windows"

    # 如果在 Windows 上且找不到 paperclip，尝试通过 WSL
    if is_windows and not paperclip_path and use_wsl:
        # 检查 wsl 命令是否可用
        if shutil.which("wsl"):
            # 在 WSL 中，paperclip 通常在 ~/.local/bin/paperclip
            # 构建 WSL 命令版本，使用完整路径
            cmd_parts = ["~/.local/bin/paperclip", "search", query]
            if source_db:
                cmd_parts.extend(["-s", source_db])
            # 通过 bash -c 来处理 ~ 扩展和 PATH
            bash_cmd = " ".join(f'"{p}"' if " " in p else p for p in cmd_parts)
            cmd = ["wsl", "-d", "Ubuntu", "bash", "-c", bash_cmd]
        else:
            raise RuntimeError(
                "paperclip not found on Windows and WSL is not available. "
                "Install WSL (wsl --install) and paperclip (in WSL: curl -fsSL https://paperclip.gxl.ai/install.sh | bash)"
            )
    elif paperclip_path or (not is_windows):
        # 直接调用 paperclip（Unix/Linux 或 Windows 上找到了）
        cmd = ["paperclip", "search", query]
        if source_db:
            cmd.extend(["-s", source_db])
    else:
        raise RuntimeError(
            "paperclip not found. Install it with: "
            "wsl -d Ubuntu && curl -fsSL https://paperclip.gxl.ai/install.sh | bash"
        )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, encoding="utf-8", errors="replace",
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            # 只要搜索返回结果（即使空的），也不算错误
            stderr = result.stderr.strip()
            stdout = result.stdout if result.stdout else ""
            if stderr and "not found" in stderr.lower():
                raise RuntimeError(
                    f"paperclip search failed: {stderr}"
                )
            # 返回空列表而不是抛出异常
            if not stdout:
                return []

        # 解析输出（paperclip 返回格式化的文本，每篇论文几行）
        output = result.stdout if result.stdout else ""
        if not output:
            return []

        results = _parse_paperclip_output(output, limit)
        return results

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"paperclip search timed out after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError("paperclip or wsl executable not found")


# ── 统一入口 ──────────────────────────────────────────────────────────
SOURCES = {
    "openalex": search_openalex,
    "pubmed": search_pubmed,
    "arxiv": search_arxiv,
    "crossref": search_crossref,
    "semanticscholar": search_semanticscholar,
    "paperclip": search_paperclip,
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
