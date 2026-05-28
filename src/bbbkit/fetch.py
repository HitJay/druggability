"""
文献下载模块 — 根据 DOI / URL 下载 PDF 或全文 XML
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _safe_filename(doi_or_id: str) -> str:
    """把 DOI / arXiv ID 转成安全文件名。"""
    return doi_or_id.replace("/", "_").replace(":", "_").replace(" ", "_")


def download_pdf(
    url: str,
    out_dir: str | Path = "data/raw",
    filename: str | None = None,
    timeout: int = 60,
) -> Path | None:
    """下载单个 PDF 文件。

    Args:
        url: PDF 直链
        out_dir: 输出目录
        filename: 文件名（不含路径），None 则自动生成
        timeout: 请求超时秒数

    Returns:
        保存路径，失败返回 None
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = url.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename += ".pdf"

    out_path = out_dir / filename
    if out_path.exists():
        return out_path

    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        with open(out_path, "wb") as f:
            with tqdm(total=total, unit="B", unit_scale=True, desc=filename) as pbar:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        return out_path
    except requests.exceptions.Timeout:
        logger.warning("下载超时 %s (timeout=%ss)", url, timeout)
        if out_path.exists():
            out_path.unlink()
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning("下载失败 HTTP %s: %s", url, e)
        if out_path.exists():
            out_path.unlink()
        return None
    except OSError as e:
        logger.error("下载失败 (磁盘/文件错误) %s: %s", url, e)
        if out_path.exists():
            out_path.unlink()
        return None
    except Exception as e:
        logger.error("下载失败 (未知错误) %s: %s", url, e)
        if out_path.exists():
            out_path.unlink()
        return None


def download_pdfs(
    items: list[dict[str, Any]],
    out_dir: str | Path = "data/raw",
    url_key: str = "pdf_url",
    id_key: str = "doi",
) -> list[Path]:
    """批量下载 PDF。

    Args:
        items: 论文元数据列表（需含 url_key 和 id_key 字段）
        out_dir: 输出目录
        url_key: 字典中 PDF 链接的 key
        id_key: 字典中 ID 的 key（用于文件名）

    Returns:
        成功下载的路径列表
    """
    paths = []
    for item in items:
        url = item.get(url_key)
        if not url:
            continue
        name = _safe_filename(item.get(id_key, "unknown")) + ".pdf"
        p = download_pdf(url, out_dir=out_dir, filename=name)
        if p:
            paths.append(p)
    return paths


def fetch_unpaywall_pdf_url(doi: str, email: str | None = None) -> str | None:
    """通过 Unpaywall API 获取论文的 OA PDF 链接。

    Args:
        doi: 论文 DOI
        email: Unpaywall 要求的邮箱

    Returns:
        PDF URL 或 None
    """
    if email is None:
        email = os.getenv("OPENALEX_EMAIL", "your@email.com")
    try:
        resp = requests.get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": email},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        best = data.get("best_oa_location", {})
        return best.get("url_for_pdf") if best else None
    except requests.exceptions.Timeout:
        logger.warning("Unpaywall 请求超时 DOI=%s", doi)
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("Unpaywall 请求失败 DOI=%s: %s", doi, e)
        return None


def fetch_europe_pmc_xml(pmid: str, out_dir: str | Path = "data/raw") -> Path | None:
    """从 Europe PMC 获取全文 XML (仅 OA 文章)。

    Args:
        pmid: PubMed ID
        out_dir: 输出目录

    Returns:
        保存路径或 None
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"PMC_{pmid}.xml"

    if out_path.exists():
        return out_path

    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmid}/fullTextXML"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        out_path.write_text(resp.text, encoding="utf-8")
        return out_path
    except requests.exceptions.Timeout:
        logger.warning("Europe PMC 请求超时 PMID=%s", pmid)
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("Europe PMC XML 获取失败 PMID=%s: %s", pmid, e)
        return None


if __name__ == "__main__":
    # 测试 Unpaywall
    doi = "10.1038/s41586-021-03819-2"  # AlphaFold2 paper
    url = fetch_unpaywall_pdf_url(doi)
    print(f"Unpaywall PDF for {doi}: {url}")
