"""
bbbkit CLI — 快速检索、下载、解析、NER、druggability 评估

用法:
    bbbkit search <query> [--source openalex] [--limit 20]
    bbbkit download <doi> [--out-dir data/raw]
    bbbkit parse <pdf-path> [--method pymupdf]
    bbbkit ner <text> [--concept Gene,Disease,Chemical]
    bbbkit assess <target> [--gene-symbol]
    bbbkit batch --targets EGFR,BRAF,KRAS
    bbbkit image2smiles <image-or-dir> [<image-or-dir> ...] [--csv out.csv] [--sdf out.sdf]

环境变量:
    OPENALEX_EMAIL, NCBI_EMAIL, NCBI_API_KEY 等
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path


def _setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bbbkit",
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
    p_assess = sub.add_parser("assess", help="靶点可药性评估（单个靶点）")
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

    # ── batch ───────────────────────────────────────────────────────
    p_batch = sub.add_parser("batch", help="批量靶点可药性评估")
    input_group = p_batch.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--targets", "-t",
        help="逗号分隔的靶点列表，如 EGFR,BRAF,KRAS",
    )
    input_group.add_argument(
        "--file", "-f",
        help="从文件读取靶点列表（每行一个）",
    )
    input_group.add_argument(
        "--stdin", action="store_true",
        help="从 stdin 读取靶点列表（每行一个）",
    )
    p_batch.add_argument(
        "--type", "-T",
        dest="query_type",
        default="gene_symbol",
        choices=["gene_symbol", "ensembl_id", "uniprot_id"],
        help="标识符类型",
    )
    p_batch.add_argument("--workers", type=int, default=3, help="并发工作线程数")
    p_batch.add_argument("--delay", type=float, default=0.5, help="API 请求间隔（秒）")
    p_batch.add_argument("--no-progress", action="store_true", help="隐藏进度条")
    p_batch.add_argument("--json", action="store_true", help="输出 JSON 格式")
    p_batch.add_argument("--csv", action="store_true", help="输出 CSV 格式")

    # ── image2smiles ───────────────────────────────────────────────
    p_i2s = sub.add_parser("image2smiles", help="将结构图批量转换为 SMILES")
    p_i2s.add_argument("inputs", nargs="+", help="图片文件或目录")
    p_i2s.add_argument(
        "--backend",
        default="decimer",
        choices=["decimer", "molscribe"],
        help="OCR 后端（默认 decimer；molscribe 为可选重型后端）",
    )
    p_i2s.add_argument(
        "--ocr-python",
        help="OCR 后端对应的 Python 可执行文件；decimer 默认当前 Python，molscribe 默认 .venv-chemocr/bin/python",
    )
    p_i2s.add_argument("--checkpoint", help="MolScribe checkpoint 路径；默认自动从 HuggingFace 下载")
    p_i2s.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="MolScribe 推理设备（默认 cpu；DECIMER 忽略该参数）",
    )
    p_i2s.add_argument("--recursive", "-r", action="store_true", help="递归扫描目录")
    p_i2s.add_argument("--confidence", action="store_true", help="计算模型置信度")
    p_i2s.add_argument("--hand-drawn", action="store_true", help="启用 DECIMER 手绘结构模式")
    p_i2s.add_argument("--csv", help="保存 CSV 结果路径")
    p_i2s.add_argument("--sdf", help="保存 SDF 结果路径（仅成功分子）")
    p_i2s.add_argument("--json", action="store_true", help="打印 JSON 结果")

    return parser


def _cmd_search(args: argparse.Namespace) -> None:
    from bbbkit.search import search

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
    from bbbkit.fetch import download_pdf, fetch_unpaywall_pdf_url

    doi_or_url = args.doi_or_url
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

    from bbbkit.parse import extract_text_pymupdf, extract_text_pdfplumber

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
    from bbbkit.ner import annotate_with_pubtator

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
    from bbbkit.druggability import assess_druggability

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


def _cmd_batch(args: argparse.Namespace) -> None:
    """批量评估多个靶点"""
    from bbbkit.druggability.batch import assess_druggability_batch

    targets: list[str] = []
    if args.targets:
        targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    elif args.file:
        if not os.path.isfile(args.file):
            print(f"[batch] 文件不存在: {args.file}")
            sys.exit(1)
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("target"):
                    targets.append(line)
    elif args.stdin:
        for line in sys.stdin:
            line = line.strip()
            if line:
                targets.append(line)

    if not targets:
        print("[batch] 未读取到有效靶点列表")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Druggability Batch Assessment ({len(targets)} targets)")
    print(f"{'='*60}\n")

    results = assess_druggability_batch(
        targets,
        query_type=args.query_type,
        max_workers=args.workers,
        request_delay=args.delay,
        show_progress=not args.no_progress,
    )

    if args.json:
        print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
        return

    if args.csv:
        _output_batch_csv(results)
        return

    _output_batch_table(results)


def _cmd_image2smiles(args: argparse.Namespace) -> None:
    from bbbkit.image2smiles import (
        discover_image_paths,
        run_image_to_smiles_batch,
        write_results_csv,
        write_results_sdf,
    )

    try:
        image_paths = discover_image_paths(args.inputs, recursive=args.recursive)
    except FileNotFoundError as exc:
        print(f"[image2smiles] {exc}")
        sys.exit(1)

    if not image_paths:
        print("[image2smiles] 未发现支持的图片文件（支持 png/jpg/jpeg/tif/tiff/bmp/webp）")
        sys.exit(1)

    ocr_python = args.ocr_python
    if not ocr_python:
        if args.backend == "decimer":
            ocr_python = shutil.which("python") or sys.executable
        else:
            ocr_python = ".venv-chemocr/bin/python"

    print(f"[image2smiles] 准备处理 {len(image_paths)} 张图片")
    print(f"[image2smiles] Backend: {args.backend}")
    print(f"[image2smiles] OCR Python: {ocr_python}")

    try:
        results = run_image_to_smiles_batch(
            image_paths,
            backend=args.backend,
            ocr_python=ocr_python,
            checkpoint=args.checkpoint,
            device=args.device,
            compute_confidence=args.confidence,
            hand_drawn=args.hand_drawn,
        )
    except Exception as exc:
        print(f"[image2smiles] 运行失败: {exc}")
        if args.backend == "molscribe":
            print("[image2smiles] 如未配置 MolScribe 环境，可先运行: bash scripts/setup_image2smiles_env.sh")
        sys.exit(1)

    if args.csv:
        write_results_csv(results, args.csv)
        print(f"[image2smiles] CSV 已保存: {args.csv}")

    if args.sdf:
        write_results_sdf(results, args.sdf)
        print(f"[image2smiles] SDF 已保存: {args.sdf}")

    if args.json:
        print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
        return

    _output_image2smiles_table(results)


def _output_batch_table(results) -> None:
    """终端表格输出"""
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    header = f"{'Target':20s} {'Tractab':8s} {'Ligandab':8s} {'Overall':8s} {'Confidence':12s} {'Elapsed':8s}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    for r in succeeded:
        tract = f"{r.tractability_score:.3f}" if r.tractability_score is not None else "N/A"
        lig = f"{r.ligandability_score:.3f}" if r.ligandability_score is not None else "N/A"
        print(
            f"{r.query:20s} {tract:>8s} {lig:>8s} "
            f"{r.overall_score:>8.3f} {r.confidence:12s} {r.elapsed_seconds:>6.1f}s"
        )

    if failed:
        print()
        print(f"  Failed ({len(failed)}):")
        for r in failed:
            err = r.error[:60] if r.error else "unknown error"
            print(f"    {r.query:20s} {err}")

    total_elapsed = sum(r.elapsed_seconds for r in results)
    print(f"\n  {len(succeeded)}/{len(results)} succeeded in {total_elapsed:.1f}s total")


def _output_batch_csv(results) -> None:
    """CSV 格式输出"""
    writer = csv.writer(sys.stdout)
    writer.writerow([
        "query", "success", "overall_score", "confidence",
        "tractability_score", "ligandability_score",
        "ligandability_n_ligands", "elapsed_seconds", "error",
    ])
    for r in results:
        writer.writerow([
            r.query,
            r.success,
            r.overall_score,
            r.confidence,
            r.tractability_score or "",
            r.ligandability_score or "",
            r.ligandability_n_ligands,
            round(r.elapsed_seconds, 2),
            r.error or "",
        ])


def _output_image2smiles_table(results) -> None:
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    header = f"{'Image':36s} {'Status':10s} {'Confidence':10s} {'SMILES / Error'}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    for r in results:
        image_name = Path(r.image_path).name[:36]
        confidence = f"{r.confidence:.3f}" if r.confidence is not None else ""
        detail = r.canonical_smiles or (r.error or "")
        print(f"{image_name:36s} {r.status:10s} {confidence:10s} {detail[:80]}")

    print(f"\n  {len(succeeded)}/{len(results)} images yielded valid SMILES")
    if failed:
        print(f"  {len(failed)} image(s) failed or returned invalid SMILES")


def main() -> None:
    parser = _setup_parser()
    args = parser.parse_args()

    dispatch = {
        "search": _cmd_search,
        "download": _cmd_download,
        "parse": _cmd_parse,
        "ner": _cmd_ner,
        "assess": _cmd_assess,
        "batch": _cmd_batch,
        "image2smiles": _cmd_image2smiles,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()