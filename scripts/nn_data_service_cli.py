#!/usr/bin/env python3
"""CLI for Novo Nordisk Research Data Services (sc177 OData v4 + BioviaRendering).

Usage examples:
  # 1. Run unauthenticated smoke test (BioviaRendering PNG + NNExperiments GetTime + Swagger check)
  python scripts/nn_data_service_cli.py probe

  # 2. Authenticate via Azure AD Device Code (one-time browser login, caches refresh_token)
  python scripts/nn_data_service_cli.py login

  # 3. Query siRNA pools by gene symbol (for Imaging / vCell / HCS)
  python scripts/nn_data_service_cli.py sirna --gene INHBE

  # 4. Search internal co-crystal PDB structures (for Druggability / Docking / FEP)
  python scripts/nn_data_service_cli.py structures --query GLP1R

  # 5. Query internal wet-lab assay readouts by NNC number
  python scripts/nn_data_service_cli.py results --nnc 0113

  # 6. Search ELN experiments by keyword or experiment number
  python scripts/nn_data_service_cli.py eln --keyword "myotube"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from druggability.nn_data_service import NNDataServiceClient  # noqa: E402

SAMPLE_ASPIRIN_MOLBLOCK = """
  Mrv2014 010120260000          2D          

 13 13  0  0  0  0            999 V2000
   -1.2500    0.7217    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -1.2500   -0.7217    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000   -1.4434    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.2500   -0.7217    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.2500    0.7217    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    1.4434    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.5000    1.4434    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.7500    0.7217    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    2.5000    2.8868    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    2.5000   -1.4434    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    3.7500   -0.7217    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    5.0000   -1.4434    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.7500    0.7217    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  2  0  0  0  0
  2  3  1  0  0  0  0
  3  4  2  0  0  0  0
  4  5  1  0  0  0  0
  5  6  2  0  0  0  0
  6  1  1  0  0  0  0
  5  7  1  0  0  0  0
  7  8  1  0  0  0  0
  7  9  2  0  0  0  0
  4 10  1  0  0  0  0
 10 11  1  0  0  0  0
 11 12  1  0  0  0  0
 11 13  2  0  0  0  0
M  END
"""


def cmd_probe(client: NNDataServiceClient, out_png: str | None) -> int:
    print("[1/3] Checking BioviaRendering /healthz ...")
    health = client.check_biovia_health()
    print(f"      Status: {health}")

    print("[2/3] Querying NNExperiments /odata/GetTime() ...")
    server_time = client.get_server_time()
    print(f"      Server time: {server_time}")

    print("[3/3] Testing BioviaRendering 2D depiction (PNG) ...")
    png_bytes = client.render_molblock(SAMPLE_ASPIRIN_MOLBLOCK, image_format=1, width=320, height=320)
    print(f"      Rendered PNG: {len(png_bytes)} bytes (magic={png_bytes[:8]!r})")
    if out_png:
        out_path = Path(out_png)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(png_bytes)
        print(f"      Saved to: {out_path}")

    token = client.get_access_token()
    if token:
        print("[Auth] Valid cached/env OAuth2 token detected.")
    elif client.has_kerberos_ticket():
        print("[Auth] Active Kerberos TGT detected (`klist -s` OK) — SPNEGO Negotiate auth ready!")
    else:
        print(
            "[Auth] No active Kerberos ticket or OAuth2 token found. "
            "Run `kinit` in your HPC terminal (recommended, bypasses Azure AD device conditional access) "
            "to unlock authenticated OData queries."
        )
    return 0


def cmd_login(client: NNDataServiceClient) -> int:
    dc = client.start_device_code_flow()
    print("=" * 72)
    print("Azure AD Device Code Authentication for Novo Nordisk Data Services")
    print(f"  1. Open URL in browser : {dc.get('verification_uri')}")
    print(f"  2. Enter code          : {dc.get('user_code')}")
    print("=" * 72)
    print("Waiting for sign-in completion (timeout 15 min)...")
    payload = client.poll_device_code_flow(dc)
    print(f"Authentication succeeded! Token cached at {client.token_cache_path} (expires in {payload.get('expires_in')}s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Novo Nordisk sc177 Data Services CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="Run unauthenticated connectivity & BioviaRendering test")
    p_probe.add_argument("--out-png", default=None, help="Optional path to save rendered test PNG")

    sub.add_parser("login", help="Interactive Azure AD Device Code login (caches refresh token)")

    p_sirna = sub.add_parser("sirna", help="Search NNSamples siRNA pools by gene symbol")
    p_sirna.add_argument("--gene", required=True, help="Gene symbol (e.g. INHBE)")
    p_sirna.add_argument("--top", type=int, default=20)

    p_plate = sub.add_parser("plate", help="Fetch well-level sample metadata by plate barcode/label")
    p_plate.add_argument("--barcode", required=True, help="ContainerLabel / plate barcode")

    p_struct = sub.add_parser("structures", help="Search internal NNStructures co-crystal PDBs")
    p_struct.add_argument("--query", required=True, help="Target name, NNC number, or ELN number")
    p_struct.add_argument("--top", type=int, default=25)

    p_res = sub.add_parser("results", help="Fetch wet-lab assay readouts from NNResults by NNC number")
    p_res.add_argument("--nnc", required=True, help="NNC number or substring")
    p_res.add_argument("--top", type=int, default=50)

    p_eln = sub.add_parser("eln", help="Search ELN experiments in NNExperiments")
    p_eln.add_argument("--keyword", default=None, help="Keyword, title, or experiment number")
    p_eln.add_argument("--owner", default=None, help="Owner initials (e.g. IGWU, UHYG)")
    p_eln.add_argument("--top", type=int, default=25)

    p_entry = sub.add_parser("eln-entry", help="List entries or render an ELN entry to plain text")
    p_entry.add_argument("--exp-id", type=int, required=True, help="ELN Experiment Id")
    p_entry.add_argument("--entry-id", type=int, default=None, help="Optional Entry Id to render")

    args = parser.parse_args()
    client = NNDataServiceClient()

    if args.cmd == "probe":
        return cmd_probe(client, args.out_png)
    if args.cmd == "login":
        return cmd_login(client)
    if args.cmd == "sirna":
        print(json.dumps(client.search_sirna_pools(args.gene, top=args.top), indent=2))
        return 0
    if args.cmd == "plate":
        print(json.dumps(client.get_plate_samples(args.barcode), indent=2))
        return 0
    if args.cmd == "structures":
        print(json.dumps(client.search_internal_structures(args.query, top=args.top), indent=2))
        return 0
    if args.cmd == "results":
        print(json.dumps(client.get_compound_results(args.nnc, top=args.top), indent=2))
        return 0
    if args.cmd == "eln":
        print(
            json.dumps(
                client.search_eln_experiments(keyword=args.keyword, owner=args.owner, top=args.top),
                indent=2,
            )
        )
        return 0
    if args.cmd == "eln-entry":
        if args.entry_id is not None:
            print(client.render_eln_entry_text(args.exp_id, args.entry_id))
        else:
            print(json.dumps(client.get_eln_entries(args.exp_id), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
