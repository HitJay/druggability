"""
PDF 解析模块 — PyMuPDF 本地提取 + GROBID 结构化解析
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


# ── PyMuPDF 本地提取 ──────────────────────────────────────────────────
def extract_text_pymupdf(pdf_path: str | Path) -> str:
    """用 PyMuPDF 提取 PDF 全文文本。

    Args:
        pdf_path: PDF 文件路径

    Returns:
        提取的纯文本
    """
    import pymupdf  # PyMuPDF

    doc = pymupdf.open(str(pdf_path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text_pdfplumber(pdf_path: str | Path) -> str:
    """用 pdfplumber 提取 PDF 全文文本（表格场景更好）。

    Args:
        pdf_path: PDF 文件路径

    Returns:
        提取的纯文本
    """
    import pdfplumber

    text_parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


# ── GROBID 结构化解析 ─────────────────────────────────────────────────
GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")


def parse_with_grobid(
    pdf_path: str | Path,
    grobid_url: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """调用 GROBID 服务解析 PDF 为结构化数据。

    需要先启动 GROBID Docker：
        sudo docker run -d --name grobid -p 8070:8070 lfoppiano/grobid:0.8.0

    Args:
        pdf_path: PDF 文件路径
        grobid_url: GROBID 服务地址
        timeout: 请求超时

    Returns:
        dict: 含 title, abstract, sections, references 等
    """
    if grobid_url is None:
        grobid_url = GROBID_URL

    url = f"{grobid_url}/api/processFulltextDocument"

    with open(str(pdf_path), "rb") as f:
        resp = requests.post(
            url,
            files={"input": f},
            data={"consolidateHeader": "1", "consolidateCitations": "1"},
            timeout=timeout,
        )
    resp.raise_for_status()

    tei_xml = resp.text
    return _parse_tei_simple(tei_xml)


def _parse_tei_simple(tei_xml: str) -> dict[str, Any]:
    """简单解析 GROBID TEI XML，提取关键字段。"""
    import xml.etree.ElementTree as ET

    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    root = ET.fromstring(tei_xml)

    # Title
    title_el = root.find(".//tei:titleStmt/tei:title", ns)
    title = title_el.text.strip() if title_el is not None and title_el.text else ""

    # Abstract
    abstract_el = root.find(".//tei:profileDesc/tei:abstract", ns)
    abstract = ""
    if abstract_el is not None:
        abstract = " ".join(abstract_el.itertext()).strip()

    # Sections
    sections = []
    for div in root.findall(".//tei:body/tei:div", ns):
        head_el = div.find("tei:head", ns)
        head = head_el.text.strip() if head_el is not None and head_el.text else ""
        text = " ".join(div.itertext()).strip()
        sections.append({"heading": head, "text": text})

    # References
    references = []
    for bibl in root.findall(".//tei:listBibl/tei:biblStruct", ns):
        ref_title_el = bibl.find(".//tei:title", ns)
        ref_title = (
            ref_title_el.text.strip()
            if ref_title_el is not None and ref_title_el.text
            else ""
        )
        references.append(ref_title)

    return {
        "title": title,
        "abstract": abstract,
        "sections": sections,
        "references": references,
        "tei_xml": tei_xml,
    }


def save_parsed(parsed: dict[str, Any], out_path: str | Path) -> Path:
    """保存解析结果为 JSON。"""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 不保存 tei_xml 到 JSON（太大）
    data = {k: v for k, v in parsed.items() if k != "tei_xml"}
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse.py <pdf_path>")
        sys.exit(1)

    pdf = sys.argv[1]
    print("=== PyMuPDF 提取 ===")
    text = extract_text_pymupdf(pdf)
    print(text[:500])
