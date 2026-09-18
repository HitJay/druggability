#!/usr/bin/env python3
"""
CLI entry point for 3D peptide lipidation & protraction clearance audit.

Evaluates 3D exit vector clearance, receptor collision risks, and PK extension:
- Calculates conical clearance aperture (15 Å, 60° cone) along the residue sidechain vector
- Flags steric obstruction by extracellular loops (ECL2/ECL3)
- Predicts target potency loss risk (< 3-fold vs > 100-fold)
- Estimates albumin binding affinity and human PK half-life extension

Usage examples:
  # 1. Audit Position 8 for Semaglutide-type C18 diacid-γGlu on OXTR:
  python scripts/run_peptide_lipidation_audit.py \
      --complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb \
      --pos 8 --mod C18_diacid_gammaGlu --target-name OXTR

  # 2. Audit Position 2 (inner pocket, should trigger severe clash):
  python scripts/run_peptide_lipidation_audit.py \
      --complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb \
      --pos 2 --mod C18_diacid_gammaGlu
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

from druggability.peptide.chem_mod import audit_peptide_lipidation


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit 3D spatial clearance and steric collision risks for peptide lipid protraction"
    )
    parser.add_argument(
        "--complex",
        type=str,
        required=True,
        help="Path to complex PDB file",
    )
    parser.add_argument(
        "--pos",
        type=int,
        required=True,
        help="Peptide residue sequence number to evaluate (e.g., 8)",
    )
    parser.add_argument(
        "--mod",
        type=str,
        default="C18_diacid_gammaGlu",
        choices=["C16_monoacid", "C18_diacid_gammaGlu", "C20_diacid_gammaGlu_2xOEG"],
        help="Lipid protraction type (default: C18_diacid_gammaGlu)",
    )
    parser.add_argument(
        "--target-name",
        type=str,
        default="Target",
        help="Target receptor name (e.g., OXTR)",
    )
    parser.add_argument(
        "--cone-angle",
        type=float,
        default=60.0,
        help="Clearance cone angle in degrees (default: 60.0)",
    )
    parser.add_argument(
        "--cone-length",
        type=float,
        default=15.0,
        help="Clearance cone probe depth in Angstroms (default: 15.0)",
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

    result = audit_peptide_lipidation(
        complex_pdb=complex_path,
        res_seq=args.pos,
        protraction_type=args.mod,
        target_name=args.target_name,
        cone_angle_deg=args.cone_angle,
        cone_length_angstrom=args.cone_length,
    )

    if not result.ok:
        print(f"Error: Lipidation audit failed: {result.error}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(result.summary_markdown())


if __name__ == "__main__":
    main()
