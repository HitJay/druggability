#!/usr/bin/env python3
"""
CLI entry point for peptide-protein binding affinity & interface analysis.

Usage examples:
  # 1. Automatic chain identification:
  python scripts/run_peptide_affinity.py --complex OXTR_assessment/structures/7QVM_active_complex.pdb

  # 2. Explicit chains:
  python scripts/run_peptide_affinity.py --complex complex.pdb --rec-chain R --pep-chain L

  # 3. Export structured JSON:
  python scripts/run_peptide_affinity.py --complex complex.pdb --json
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

from druggability.peptide.affinity import predict_peptide_affinity


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predict peptide-protein binding affinity and analyze interface contacts (PRODIGY model)"
    )
    parser.add_argument(
        "--complex",
        type=str,
        required=True,
        help="Path to complex PDB file (containing protein receptor and peptide)",
    )
    parser.add_argument(
        "--rec-chain",
        type=str,
        default=None,
        help="Receptor chain ID (optional, auto-detected by length if omitted)",
    )
    parser.add_argument(
        "--pep-chain",
        type=str,
        default=None,
        help="Peptide chain ID (optional, auto-detected by length if omitted)",
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
        print(f"Error: Complex PDB not found: {complex_path}", file=sys.stderr)
        sys.exit(1)

    result = predict_peptide_affinity(
        complex_pdb=complex_path,
        receptor_chain=args.rec_chain,
        peptide_chain=args.pep_chain,
        distance_cutoff=args.cutoff,
    )

    if not result.ok:
        print(f"Error: Affinity calculation failed: {result.error}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(result.summary_markdown())


if __name__ == "__main__":
    main()
