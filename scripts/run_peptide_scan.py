#!/usr/bin/env python3
"""
CLI entry point for peptide mutational scanning:
- Mode 'ala': Full peptide in silico Alanine Scanning (Hotspot & Exit Vector mapping)
- Mode 'position': Single-position 20-amino-acid Deep Mutational Scanning (SAR substitutions)

Usage examples:
  # 1. Run full-chain Alanine scanning on complex:
  python scripts/run_peptide_scan.py --complex OXTR_assessment/structures/7QVM_active_complex.pdb --mode ala

  # 2. Run 20-amino-acid substitution scan on peptide residue position 7:
  python scripts/run_peptide_scan.py --complex OXTR_assessment/structures/7QVM_active_complex.pdb --mode position --pos 7

  # 3. Export JSON:
  python scripts/run_peptide_scan.py --complex complex.pdb --mode ala --json
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

from druggability.peptide.scan import run_alanine_scanning, scan_position_mutations


def parse_args():
    parser = argparse.ArgumentParser(
        description="Peptide mutational scanning and ΔΔG binding energy profiling"
    )
    parser.add_argument(
        "--complex",
        type=str,
        required=True,
        help="Path to complex PDB file",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["ala", "position"],
        default="ala",
        help="Scanning mode: 'ala' for full alanine scanning, 'position' for 20-AA substitution scan",
    )
    parser.add_argument(
        "--pos",
        type=int,
        default=None,
        help="Peptide residue sequence number (required when --mode position)",
    )
    parser.add_argument(
        "--rec-chain",
        type=str,
        default=None,
        help="Receptor chain ID (optional, auto-detected if omitted)",
    )
    parser.add_argument(
        "--pep-chain",
        type=str,
        default=None,
        help="Peptide chain ID (optional, auto-detected if omitted)",
    )
    parser.add_argument(
        "--cutoff",
        type=float,
        default=5.5,
        help="Interface contact heavy-atom distance cutoff in Angstroms (default: 5.5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output instead of Markdown",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    complex_path = Path(args.complex).resolve()
    if not complex_path.exists():
        print(f"Error: Complex PDB file not found: {complex_path}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "ala":
        res = run_alanine_scanning(
            complex_pdb=complex_path,
            receptor_chain=args.rec_chain,
            peptide_chain=args.pep_chain,
            distance_cutoff=args.cutoff,
        )
    elif args.mode == "position":
        if args.pos is None:
            print("Error: --pos <int> is required when --mode position", file=sys.stderr)
            sys.exit(1)
        res = scan_position_mutations(
            complex_pdb=complex_path,
            res_seq=args.pos,
            receptor_chain=args.rec_chain,
            peptide_chain=args.pep_chain,
            distance_cutoff=args.cutoff,
        )
    else:
        print(f"Error: Unsupported mode: {args.mode}", file=sys.stderr)
        sys.exit(1)

    if not res.ok:
        print(f"Error: Scanning failed: {res.error}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(res.summary_markdown())


if __name__ == "__main__":
    main()
