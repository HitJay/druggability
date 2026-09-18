#!/usr/bin/env python3
"""
CLI entry point for End-to-End Peptide Candidate Druggability Pipeline.

Runs complete multi-tier structural pharmacology assessment:
- Layer 1: PRODIGY contact affinity (ΔG, Kd, interface hotspots)
- Layer 2: In silico Alanine scanning (Critical hotspots vs Tolerant exit vectors)
- Layer 2b: Positional 20-amino-acid mutational matrix
- Layer 4: Dual-receptor subtype selectivity audit (differential contact fingerprint)
- Layer 3: GPU explicit-solvent Ensemble MM/GBSA (optional, A100 accelerated)
- Delivery: Standalone interactive 3Dmol.js HTML report

Usage examples:
  # 1. Full pipeline for OXT_Gly on OXTR with V2R counter-screen and Pos 7/8 deep scan:
  python scripts/run_peptide_assessment_pipeline.py \
      --complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb \
      --peptide-name OXT_Gly --target-name OXTR \
      --counter V2R=OXTR_assessment/structures/V2R_OXT_Gly_complex.pdb \
      --scan-positions 7 8

  # 2. Add GPU Ensemble MD (A100):
  python scripts/run_peptide_assessment_pipeline.py \
      --complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb \
      --ensemble-md --md-length 0.5 --gpu 0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Add project root src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from druggability.peptide.pipeline import assess_peptide_candidate


def parse_args():
    parser = argparse.ArgumentParser(
        description="End-to-End Peptide Druggability, Structural Pharmacology & Selectivity Pipeline"
    )
    parser.add_argument(
        "--complex",
        type=str,
        required=True,
        help="Path to primary complex PDB file",
    )
    parser.add_argument(
        "--peptide-name",
        type=str,
        default=None,
        help="Peptide candidate identifier (e.g., OXT_Gly)",
    )
    parser.add_argument(
        "--target-name",
        type=str,
        default="Primary_Target",
        help="Primary target receptor name (e.g., OXTR)",
    )
    parser.add_argument(
        "--counter",
        type=str,
        action="append",
        default=[],
        help="Counter-screen specification formatted as 'NAME=PATH_TO_PDB' (can repeat)",
    )
    parser.add_argument(
        "--scan-positions",
        type=int,
        nargs="+",
        default=None,
        help="Residue sequence numbers to run 20-amino-acid deep mutational matrix",
    )
    parser.add_argument(
        "--no-ala-scan",
        action="store_true",
        help="Skip full alanine scanning stage",
    )
    parser.add_argument(
        "--ensemble-md",
        action="store_true",
        help="Run GPU-accelerated explicit-solvent Ensemble MM/GBSA",
    )
    parser.add_argument(
        "--md-length",
        type=float,
        default=1.0,
        help="Ensemble MD production length in ns (default: 1.0)",
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=0,
        help="CUDA device index for GPU stages (default: 0)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory (defaults to output/<DATE>/pipeline_<PEP>_<TARGET>/)",
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

    counter_dict = {}
    for c_spec in args.counter:
        if "=" in c_spec:
            c_name, c_path = c_spec.split("=", 1)
            counter_dict[c_name.strip()] = Path(c_path.strip()).resolve()

    pep_name = args.peptide_name or complex_path.stem
    out_dir = args.out_dir
    if not out_dir:
        today_str = date.today().isoformat()
        out_dir = PROJECT_ROOT / "output" / today_str / f"pipeline_{pep_name}_{args.target_name}"

    print(f"[*] Starting End-to-End Peptide Assessment Pipeline")
    print(f"[*] Candidate: {pep_name} | Primary Target: {args.target_name}")
    print(f"[*] Output Directory: {out_dir}")

    report = assess_peptide_candidate(
        complex_pdb=complex_path,
        peptide_name=pep_name,
        target_name=args.target_name,
        counter_complexes=counter_dict,
        run_alanine_scan=not args.no_ala_scan,
        scan_positions=args.scan_positions,
        run_ensemble_md=args.ensemble_md,
        ensemble_md_length_ns=args.md_length,
        gpu_id=args.gpu,
        out_dir=out_dir,
    )

    if not report.ok:
        print(f"\n[!] Pipeline Failed: {report.error}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("\n" + report.summary_markdown())
        if report.html_report_path:
            print(f"\n[+] Standalone Interactive 3D HTML Dossier generated:")
            print(f"    {report.html_report_path}")


if __name__ == "__main__":
    main()
