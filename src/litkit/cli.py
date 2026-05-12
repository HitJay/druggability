"""
litkit CLI — 快速检索、下载、解析、NER、druggability 评估

用法:
    litkit search <query> [--source openalex] [--limit 20]
    litkit download <doi> [--out-dir data/raw]
    litkit parse <pdf-path> [--method pymupdf]
    litkit ner <text> [--concept Gene,Disease,Chemical]
    litkit assess <target> [--gene-symbol]

环境变量:
    OPENALEX_EMAIL, NCBI_EMAIL, NCBI_API_KEY 等
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="litkit",
        description="学术文献检索 + 解析 + 可药性评估工具包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── search ──────────────────────────────────────────────────────
    p_search = sub.add_parser("search", help="跨数据源检索论文")
    p_search.add_argument("query", help="检索关键词")
    p_search.add_argument(
        "--source", "-s",
        default="openalex",
        choices=["openalex", "pubmed", "arxiv", "crossref", "semanticscholar"],
        help="数据源（默认 openalex）",
    )
    p_search.add_argument("--limit", "-l", type=int, default=20, help="最大返回数")
    p_search.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # ── download ────────────────────────────────────────────────────
    p_dl = sub.add_parser("download", help="下载 PDF（支持 DOI / URL）")
    p_dl.add_argument("doi_or_url", help="DOI 或 PDF 直链")
    p_dl.add_argument("--out-dir", "-o", default="data/raw", help="保存目录")

    # ── parse ───────────────────────────────────────────────────────
    p_parse = sub.add_parser("parse", help="提取 PDF 文本")
    p_parse.add_argument("pdf_path", help="PDF 文件路径")
    p_parse.add_argument(
        "--method", "-m",
        default="pymupdf",
        choices=["pymupdf", "pdfplumber"],
        help="提取引擎",
    )
    p_parse.add_argument("--save", "-s", help="保存到 JSON 文件路径")

    # ── ner ─────────────────────────────────────────────────────────
    p_ner = sub.add_parser("ner", help="实体识别（PubTator3）")
    p_ner.add_argument("text", help="待标注文本")
    p_ner.add_argument(
        "--concept", "-c",
        default=None,
        help="逗号分隔的实体类型过滤，如 Gene,Disease,Chemical",
    )

    # ── assess ──────────────────────────────────────────────────────
    p_assess = sub.add_parser("assess", help="靶点可药性评估")
    p_assess.add_argument("target", help="靶点标识（gene symbol / Ensembl ID / UniProt ID）")
    p_assess.add_argument(
        "--type", "-t",
        dest="query_type",
        default="gene_symbol",
        choices=["gene_symbol", "ensembl_id", "uniprot_id"],
        help="标识符类型",
    )
    p_assess.add_argument("--no-structure", action="store_true", help="跳过结构分析")
    p_assess.add_argument("--json", action="store_true", help="输出 JSON 格式")

    return parser


def _cmd_search(args: argparse.Namespace) -> None:
    from litkit.search import search

    results = search(
        args.query,
        source=args.source,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        return

    print(f"\n{'='*60}")
    print(f"  [{args.source.upper()}] {args.query}")
    print(f"  {len(results)} result(s)")
    print(f"{'='*60}\n")
    for i, r in enumerate(results, 1):
        title = r.get("title", r.get("name", ""))
        print(f"  {i:3d}. {title[:120]}")
        if doi := r.get("doi"):
            print(f"       DOI: {doi}")
        if pid := r.get("pmid") or r.get("paper_id"):
            print(f"       ID:  {pid}")
        print()


def _cmd_download(args: argparse.Namespace) -> None:
    from litkit.fetch import download_pdf, fetch_unpaywall_pdf_url

    doi_or_url = args.doi_or_url
    # 如果是 DOI（不含 http），走 Unpaywall 获取 PDF URL
    if not doi_or_url.startswith("http"):
        print(f"[download] 通过 Unpaywall 解析 DOI: {doi_or_url}")
        url = fetch_unpaywall_pdf_url(doi_or_url)
        if not url:
            print(f"[download] Unpaywall 未找到 OA PDF: {doi_or_url}")
            return
        print(f"[download] PDF 链接: {url}")
        path = download_pdf(url, out_dir=args.out_dir, filename=f"{doi_or_url.replace('/', '_')}.pdf")
    else:
        path = download_pdf(doi_or_url, out_dir=args.out_dir)

    if path:
        print(f"[download] 已保存: {path}")
    else:
        print("[download] 下载失败")
        sys.exit(1)


def _cmd_parse(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf_path)
    if not pdf_path.is_file():
        print(f"[parse] 文件不存在: {pdf_path}")
        sys.exit(1)

    from litkit.parse import extract_text_pymupdf, extract_text_pdfplumber

    if args.method == "pymupdf":
        text = extract_text_pymupdf(pdf_path)
    else:
        text = extract_text_pdfplumber(pdf_path)

    if args.save:
        save_path = Path(args.save)
        save_path.write_text(text, encoding="utf-8")
        print(f"[parse] 已保存文本到: {save_path} ({len(text)} chars)")
    else:
        print(text)


def _cmd_ner(args: argparse.Namespace) -> None:
    from litkit.ner import annotate_with_pubtator

    concepts = args.concept.split(",") if args.concept else None
    entities = annotate_with_pubtator(args.text, concepts=concepts)

    if not entities:
        print("[ner] 未识别到实体")
        return

    print(f"\n  {'TYPE':12s} {'TEXT':30s} {'ID'}")
    print(f"  {'-'*12} {'-'*30} {'-'*20}")
    for e in entities:
        print(f"  {e['type']:12s} {e['text'][:30]:30s} {e.get('id', ''):20s}")
    print(f"\n  Total: {len(entities)} entities")


def _cmd_assess(args: argparse.Namespace) -> None:
    from litkit.druggability import assess_druggability

    result = assess_druggability(
        args.target,
        query_type=args.query_type,
        include_structure_analysis=not args.no_structure,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    print(f"\n{'='*60}")
    print(f"  Druggability Assessment: {args.target}")
    print(f"{'='*60}\n")

    composite = result.get("composite", {})
    overall = composite.get("overall_score", "N/A")
    print(f"  Overall Score:          {overall}")
    print(f"  Contributing Scores:")
    contrib = composite.get("contributing_scores", {})
    for k, v in contrib.items():
        print(f"    {k:20s} {v}")
    print()

    tract = result.get("tractability", {})
    if tract and "error" not in tract:
        print(f"  Tractability:")
        for mod in ["small_molecule", "antibody", "protac"]:
            info = tract.get(mod, {})
            if info:
                print(f"    {mod:20s} {info.get('category', info)}")
    print()

    lig = result.get("ligandability", {})
    if lig and "error" not in lig:
        print(f"  Ligandability: {lig.get('ligandability_score', 'N/A')}  ({lig.get('n_known_ligands', 0)} ligands)")
        compounds = lig.get("top_compounds", [])
        for c in compounds[:5]:
            print(f"    - {c.get('molecule_name', c.get('molecule_chembl_id', ''))}")

    pocket = result.get("pocket_analysis", {})
    if pocket and "error" not in pocket:
        print(f"\n  Pocket Analysis:")
        print(f"    Pockets found: {pocket.get('num_pockets', 0)}")
        print(f"    Best score:    {pocket.get('best_druggability_score', 'N/A')}")
        print(f"    Total volume:  {pocket.get('total_volume', 'N/A')}")


def main() -> None:
    parser = _setup_parser()
    args = parser.parse_args()

    dispatch = {
        "search": _cmd_search,
        "download": _cmd_download,
        "parse": _cmd_parse,
        "ner": _cmd_ner,
        "assess": _cmd_assess,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()