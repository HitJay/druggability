#!/usr/bin/env python3
"""
CLI entry point for peptide subtype selectivity audit & cross-reactivity profiling.

Usage examples:
  # 1. Compare OXTR vs V2R for OXT_Gly with auto-generated HTML report:
  python scripts/run_peptide_selectivity.py \
      --target-complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb \
      --counter-complex OXTR_assessment/structures/V2R_OXT_Gly_complex.pdb \
      --target-name OXTR --counter-name V2R --peptide-name OXT_Gly \
      --html output/oxt_gly_selectivity.html

  # 2. Output JSON format:
  python scripts/run_peptide_selectivity.py \
      --target-complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb \
      --counter-complex OXTR_assessment/structures/V2R_OXT_Gly_complex.pdb \
      --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from druggability.peptide.selectivity import audit_peptide_selectivity


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit peptide subtype selectivity and cross-reactivity between target and counter-screen receptors"
    )
    parser.add_argument(
        "--target-complex",
        type=str,
        required=True,
        help="Path to primary target complex PDB",
    )
    parser.add_argument(
        "--counter-complex",
        type=str,
        required=True,
        help="Path to counter-screen receptor complex PDB",
    )
    parser.add_argument(
        "--target-name",
        type=str,
        default="Primary_Target",
        help="Name of primary target receptor (e.g., OXTR)",
    )
    parser.add_argument(
        "--counter-name",
        type=str,
        default="Counter_Screen",
        help="Name of counter-screen receptor (e.g., V2R)",
    )
    parser.add_argument(
        "--peptide-name",
        type=str,
        default=None,
        help="Name of evaluated peptide ligand (e.g., OXT_Gly)",
    )
    parser.add_argument(
        "--html",
        type=str,
        default=None,
        help="Path to save self-contained 3Dmol.js interactive HTML deliverable",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output instead of Markdown",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    t_path = Path(args.target_complex).resolve()
    c_path = Path(args.counter_complex).resolve()

    if not t_path.exists():
        print(f"Error: Target complex PDB not found: {t_path}", file=sys.stderr)
        sys.exit(1)
    if not c_path.exists():
        print(f"Error: Counter-screen complex PDB not found: {c_path}", file=sys.stderr)
        sys.exit(1)

    res = audit_peptide_selectivity(
        target_complex_pdb=t_path,
        counter_complex_pdb=c_path,
        target_name=args.target_name,
        counter_name=args.counter_name,
        peptide_name=args.peptide_name,
        html_out=args.html,
    )

    if not res.ok:
        print(f"Error: Selectivity audit failed: {res.error}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(res.summary_markdown())
        if res.html_report_path:
            print(f"\n[+] Interactive 3D HTML deliverable generated at:")
            print(f"    {res.html_report_path}")


if __name__ == "__main__":
    main()
