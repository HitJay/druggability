#!/usr/bin/env python
"""Run optional internal BioLib enrichments for druggability targets."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from bbbkit.druggability.biolib_apps import (  # noqa: E402
    infer_target_biology,
    run_automated_tractability,
    run_target_portal,
    write_gene_list,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="BioLib druggability enrichment probe")
    parser.add_argument("--input", default=str(_REPO_ROOT / "data" / "druggability_targets.csv"))
    today = _dt.date.today().isoformat()
    parser.add_argument(
        "--outdir",
        default=str(_REPO_ROOT / "output" / today / "biolib_druggability_probe"),
    )
    parser.add_argument(
        "--apps",
        default="target-portal",
        help="Comma-separated: target-portal,automated-tractability",
    )
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N targets")
    parser.add_argument("--target-biology", default="", help="Override Target-Portal biology")
    parser.add_argument("--stream-logs", action="store_true", help="Stream BioLib app logs")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    inputs_dir = outdir / "inputs"
    runs_dir = outdir / "runs"
    logs_dir = outdir / "logs"
    summaries_dir = outdir / "summaries"
    for directory in (inputs_dir, runs_dir, logs_dir, summaries_dir):
        directory.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    if args.limit > 0:
        df = df.head(args.limit)

    apps = {app.strip() for app in args.apps.split(",") if app.strip()}
    summary: dict[str, Any] = {"input": args.input, "n_targets": int(len(df)), "apps": sorted(apps)}

    if "automated-tractability" in apps:
        genes_file = write_gene_list(df["gene_name"].tolist(), inputs_dir / "genes.txt")
        result = run_automated_tractability(
            genes_file,
            out_dir=runs_dir / "automated_tractability",
            log_dir=logs_dir,
            stream_logs=args.stream_logs,
        )
        summary["automated_tractability"] = result.to_dict()
        (summaries_dir / "automated_tractability.json").write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if "target-portal" in apps:
        target_portal_results = []
        for row in df.to_dict("records"):
            gene = str(row.get("gene_name") or row.get("gene") or "")
            ensembl = str(row.get("gene_id") or row.get("ensembl_id") or "")
            trait = str(row.get("gwas_trait") or row.get("genetics_traits") or "")
            target_biology = args.target_biology or infer_target_biology(trait)
            result = run_target_portal(
                gene,
                ensembl,
                target_biology=target_biology,
                out_dir=runs_dir / f"target_portal_{gene}",
                log_dir=logs_dir,
                stream_logs=args.stream_logs,
            )
            target_portal_results.append(result.to_dict())
            (summaries_dir / f"target_portal_{gene}.json").write_text(
                json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        summary["target_portal"] = target_portal_results

    summary_path = outdir / "biolib_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {summary_path}")
    if "target_portal" in summary:
        for result in summary["target_portal"]:
            metadata = result.get("metadata") or {}
            print(
                "target-portal",
                metadata.get("gene_name"),
                metadata.get("target_biology"),
                "exit=",
                result.get("exit_code"),
                result.get("result_url", ""),
            )
    if "automated_tractability" in summary:
        result = summary["automated_tractability"]
        print("automated-tractability", "exit=", result.get("exit_code"), result.get("result_url", ""))


if __name__ == "__main__":
    main()