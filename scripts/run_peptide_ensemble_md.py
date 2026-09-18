#!/usr/bin/env python3
"""
CLI entry point for GPU-accelerated Peptide Ensemble MM/GBSA simulation.

Usage examples:
  # 1. Standard 1.0 ns production on A100 GPU:
  python scripts/run_peptide_ensemble_md.py --complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb --length 1.0 --gpu 0

  # 2. Quick smoke test (0.05 ns) to verify pipeline:
  python scripts/run_peptide_ensemble_md.py --complex OXTR_assessment/structures/OXTR_OXT_Gly_complex.pdb --length 0.05 --snapshots 5 --gpu 0

  # 3. Explicit output directory:
  python scripts/run_peptide_ensemble_md.py --complex complex.pdb --out-dir /path/to/runs/
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

from druggability.peptide.ensemble_md import run_ensemble_mmgbsa


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run explicit-solvent Short-MD and ensemble MM/GBSA on peptide-protein complex"
    )
    parser.add_argument(
        "--complex",
        type=str,
        required=True,
        help="Path to complex PDB file",
    )
    parser.add_argument(
        "--length",
        type=float,
        default=1.0,
        help="Simulation production length in ns (default: 1.0)",
    )
    parser.add_argument(
        "--snapshots",
        type=int,
        default=25,
        help="Number of trajectory snapshots for MM/GBSA (default: 25)",
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=0,
        help="CUDA device index (default: 0)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory (defaults to output/<DATE>/ensemble_md_<STEM>/)",
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

    out_dir = args.out_dir
    if not out_dir:
        today_str = date.today().isoformat()
        stem = complex_path.stem
        out_dir = PROJECT_ROOT / "output" / today_str / f"ensemble_md_{stem}"

    print(f"[*] Complex PDB: {complex_path.name}")
    print(f"[*] Production Length: {args.length} ns (Snapshots: {args.snapshots})")
    print(f"[*] Target GPU Device: {args.gpu}")
    print(f"[*] Output Directory: {out_dir}")

    res = run_ensemble_mmgbsa(
        complex_pdb=complex_path,
        length_ns=args.length,
        n_snapshots=args.snapshots,
        gpu_id=args.gpu,
        out_dir=out_dir,
        receptor_chain=args.rec_chain,
        peptide_chain=args.pep_chain,
    )

    if not res.ok:
        print(f"\n[!] Ensemble MD Failed: {res.error}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("\n" + res.summary_markdown())
        print(f"\n[+] Trajectory & System Assets:")
        print(f"    - Trajectory DCD: {res.production_dcd}")
        print(f"    - Solvated PDB:   {res.solvated_pdb}")
        print(f"    - Results JSON:   {res.result_json}")


if __name__ == "__main__":
    main()
