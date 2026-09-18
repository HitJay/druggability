#!/usr/bin/env python3
"""
CLI entry point for DrugCLIP virtual screening.

Usage examples:
  # 1. Screen against a pocket PDB:
  python scripts/run_drugclip_screen.py --pocket data/pocket.pdb --top-k 100

  # 2. Screen against a full receptor PDB using a reference ligand to define pocket:
  python scripts/run_drugclip_screen.py --pocket receptor.pdb --ligand ligand.pdb --top-k 50 --gpu 0

  # 3. Screen using a small test molecule database:
  python scripts/run_drugclip_screen.py --pocket pocket.pdb --mols /tmp/test_mols.lmdb --top-k 10
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Add project root src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bbbkit.druggability.drugclip import screen_drugclip


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run DrugCLIP contrastive virtual screening against target binding pocket"
    )
    parser.add_argument(
        "--pocket",
        type=str,
        required=True,
        help="Target pocket PDB file, receptor PDB, or pocket.lmdb",
    )
    parser.add_argument(
        "--ligand",
        type=str,
        default=None,
        help="Optional reference ligand PDB (used when --pocket is a full receptor)",
    )
    parser.add_argument(
        "--center",
        type=float,
        nargs=3,
        default=None,
        help="Optional pocket center coordinates: X Y Z",
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=8.0,
        help="Pocket cutoff radius in Angstroms (default: 8.0)",
    )
    parser.add_argument(
        "--mols",
        type=str,
        default=None,
        help="Molecules LMDB file (defaults to official 2.94M mols.lmdb)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help="Number of top scoring hits to retrieve (default: 50)",
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
        help="Directory to save screening results",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pocket_path = Path(args.pocket).resolve()
    if not pocket_path.exists():
        print(f"Error: Pocket file not found: {pocket_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir
    if not out_dir:
        today_str = date.today().isoformat()
        pocket_stem = pocket_path.stem
        out_dir = PROJECT_ROOT / "output" / today_str / f"drugclip_screen_{pocket_stem}"

    print(f"[*] Target Pocket: {pocket_path.name}")
    print(f"[*] Top-K Requested: {args.top_k}")
    print(f"[*] GPU Device: {args.gpu}")
    print(f"[*] Output Directory: {out_dir}")

    result = screen_drugclip(
        pocket_input=pocket_path,
        ligand_pdb=args.ligand,
        center=args.center,
        radius=args.radius,
        mol_lmdb=args.mols,
        top_k=args.top_k,
        device_id=args.gpu,
        output_dir=out_dir,
    )

    if not result.ok:
        print(f"\n[!] Screening Failed: {result.error}", file=sys.stderr)
        sys.exit(2)

    print("\n" + result.summary_markdown(top_n=min(args.top_k, 20)))
    print(f"\n[+] Full results saved to:")
    print(f"    - JSON: {result.result_json}")
    print(f"    - TSV:  {result.result_tsv}")


if __name__ == "__main__":
    main()
