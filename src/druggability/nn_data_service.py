"""Novo Nordisk Research Data Services (sc177 OData v4 + BioviaRendering) client.

Provides unified access to internal Novo Nordisk research data microservices hosted on
https://sc177.corp.novocorp.net (`novopy` backend services):
- BioviaRendering: unauthenticated 2D molecular depiction (PNG / JPEG / EMF) from Molblock
- NNSamples: siRNA / compound library pools (GeneSymbol, UniprotId, Sequence) and plate wells
- NNStructures: internal X-ray / NMR co-crystal structures and PDB files
- NNCompounds: internal registered molecules (NNCNo, Molfile, NNASProt, Nucleotides)
- NNResults & NNProtocols: wet-lab assay readouts and protocol metadata
- NNExperiments: Electronic Lab Notebook (ELN) experiments, entries, and HTML rendering

Authentication for OData services supports three channels (in order of precedence):
1. Explicit/cached OAuth2 Bearer token (~/.cache/druggability/nn_data_service_token.json)
   with automatic refresh_token renewal and interactive Azure AD Device Code login.
2. Environment variable `NN_DATA_SERVICE_TOKEN`.
3. Kerberos / SPNEGO ticket (`kinit`) if `requests-kerberos` or `requests-gssapi` is installed.
"""

from __future__ import annotations

import json
import os
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

DEFAULT_BASE_URL = "https://sc177.corp.novocorp.net"
AZURE_TENANT_ID = "fdfed7bd-9f6a-44a1-b694-6e39c468c150"
OAUTH_CLIENT_ID = "643ba961-8f41-4de3-acb5-be804de1d2d7"
OAUTH_SCOPE = f"api://{OAUTH_CLIENT_ID}/api_access offline_access"
CA_BUNDLE_PATH = "/etc/pki/tls/certs/ca-bundle.crt"
DEFAULT_TOKEN_CACHE = Path.home() / ".cache" / "druggability" / "nn_data_service_token.json"


def _build_ssl_context(ca_bundle: str | None = None) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    bundle = ca_bundle or os.environ.get("SSL_CERT_FILE") or CA_BUNDLE_PATH
    if bundle and os.path.exists(bundle):
        ctx.load_verify_locations(bundle)
    return ctx


def escape_odata_string(value: str) -> str:
    """Escape single quotes for safe inclusion in an OData string literal."""
    return value.replace("'", "''")


class NNDataServiceClient:
    """Client for Novo Nordisk sc177 OData v4 microservices and BioviaRendering."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: str | None = None,
        token_cache_path: Path | str = DEFAULT_TOKEN_CACHE,
        ca_bundle: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._explicit_token = token or os.environ.get("NN_DATA_SERVICE_TOKEN")
        self.token_cache_path = Path(token_cache_path)
        self.ssl_context = _build_ssl_context(ca_bundle)
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Authentication & Token Lifecycle
    # ------------------------------------------------------------------

    def get_access_token(self, auto_refresh: bool = True) -> str | None:
        """Return a valid Bearer access token from explicit arg, env, or local cache."""
        if self._explicit_token:
            return self._explicit_token

        if not self.token_cache_path.exists():
            return None

        try:
            cache = json.loads(self.token_cache_path.read_text(encoding="utf-8"))
        except Exception:
            return None

        expires_at = float(cache.get("expires_at", 0))
        access_token = cache.get("access_token")
        refresh_token = cache.get("refresh_token")

        if access_token and time.time() < expires_at - 60:
            return str(access_token)

        if auto_refresh and refresh_token:
            try:
                refreshed = self._refresh_oauth_token(str(refresh_token))
                return str(refreshed["access_token"])
            except Exception:
                return None

        return None

    def _save_token_cache(self, token_payload: dict[str, Any]) -> dict[str, Any]:
        expires_in = int(token_payload.get("expires_in", 3600))
        token_payload["expires_at"] = time.time() + expires_in
        self.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_cache_path.write_text(json.dumps(token_payload, indent=2), encoding="utf-8")
        os.chmod(self.token_cache_path, 0o600)
        return token_payload

    def _refresh_oauth_token(self, refresh_token: str) -> dict[str, Any]:
        url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
        data = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": OAUTH_CLIENT_ID,
                "refresh_token": refresh_token,
                "scope": OAUTH_SCOPE,
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return self._save_token_cache(payload)

    def start_device_code_flow(self) -> dict[str, Any]:
        """Initiate Azure AD OAuth2 Device Code flow and return verification details."""
        url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/devicecode"
        data = urllib.parse.urlencode(
            {
                "client_id": OAUTH_CLIENT_ID,
                "scope": OAUTH_SCOPE,
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def poll_device_code_flow(
        self,
        device_code_info: dict[str, Any],
        on_prompt: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Poll Azure AD until the user completes Device Code sign-in, then cache the token."""
        if on_prompt and "message" in device_code_info:
            on_prompt(str(device_code_info["message"]))

        url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
        interval = int(device_code_info.get("interval", 5))
        expires_in = int(device_code_info.get("expires_in", 900))
        deadline = time.time() + expires_in

        while time.time() < deadline:
            data = urllib.parse.urlencode(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": OAUTH_CLIENT_ID,
                    "device_code": device_code_info["device_code"],
                }
            ).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            try:
                with urllib.request.urlopen(
                    req, context=self.ssl_context, timeout=self.timeout
                ) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    return self._save_token_cache(payload)
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                except Exception:
                    raise RuntimeError(f"OAuth token poll failed: {err_body}") from exc
                err_code = err_json.get("error", "")
                if err_code == "authorization_pending":
                    time.sleep(interval)
                    continue
                if err_code == "slow_down":
                    interval += 5
                    time.sleep(interval)
                    continue
                raise RuntimeError(
                    f"Device code flow failed ({err_code}): {err_json.get('error_description')}"
                ) from exc

        raise TimeoutError("Device code flow timed out before user completed authentication.")

    # ------------------------------------------------------------------
    # Unauthenticated Services & Diagnostics
    # ------------------------------------------------------------------

    def check_biovia_health(self) -> dict[str, Any]:
        """Check health status of BioviaRendering service (no auth required)."""
        url = f"{self.base_url}/BioviaRendering/v1/healthz"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_server_time(self) -> str:
        """Query NNExperiments OData GetTime() function (no auth required)."""
        url = f"{self.base_url}/NNExperiments/v1/odata/GetTime()"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return str(payload.get("value", ""))

    def render_molblock(
        self,
        molblock: str,
        image_format: int = 1,
        width: int = 400,
        height: int = 400,
        auto_size: bool = False,
    ) -> bytes:
        """Render a V2000/V3000 Molblock into image bytes via BioviaRendering (no auth required).

        Args:
            molblock: Standard MDL Molfile / CTAB string.
            image_format: 1 = PNG, 2 = JPEG, 3 = EMF.
            width: Target image width in pixels.
            height: Target image height in pixels.
            auto_size: Whether Biovia should auto-scale dimensions.
        """
        if image_format not in (1, 2, 3):
            raise ValueError(f"image_format must be 1 (PNG), 2 (JPEG), or 3 (EMF); got {image_format}")

        query = urllib.parse.urlencode(
            {
                "format": image_format,
                "dimension.width": width,
                "dimension.height": height,
                "dimension.autoSize": str(auto_size).lower(),
            }
        )
        url = f"{self.base_url}/BioviaRendering/v1/render/from-string?{query}"
        body = json.dumps(molblock).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            return resp.read()

    def get_service_swagger(self, service_name: str) -> dict[str, Any]:
        """Fetch Swagger 2.0 specification JSON for a given sc177 service (no auth required)."""
        url = f"{self.base_url}/{service_name.strip('/')}/v1/swagger/docs/v1"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ------------------------------------------------------------------
    # Authenticated OData v4 Query Helpers (Bearer + Kerberos SPNEGO)
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_krb5ccname() -> None:
        """Auto-populate KRB5CCNAME if `/tmp/krb5cc_<uid>` exists."""
        if os.environ.get("KRB5CCNAME"):
            return
        default_cc = f"/tmp/krb5cc_{os.getuid()}"
        if os.path.exists(default_cc):
            os.environ["KRB5CCNAME"] = default_cc

    @staticmethod
    def has_kerberos_ticket() -> bool:
        """Return True if the current user has a valid Kerberos TGT (`klist -s`)."""
        NNDataServiceClient._ensure_krb5ccname()
        try:
            res = subprocess.run(
                ["klist", "-s"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
            return res.returncode == 0
        except Exception:
            return False

    def _curl_negotiate_get(self, url: str) -> dict[str, Any]:
        """Execute an HTTP GET using system `curl --http1.1 --negotiate -u :` (Kerberos SPNEGO)."""
        self._ensure_krb5ccname()
        bundle = os.environ.get("SSL_CERT_FILE") or CA_BUNDLE_PATH
        cmd = [
            "curl",
            "-sS",
            "-f",
            "--http1.1",
            "--negotiate",
            "-u",
            ":",
            "-H",
            "Accept: application/json",
            "--max-time",
            str(self.timeout),
        ]
        if bundle and os.path.exists(bundle):
            cmd.extend(["--cacert", bundle])
        cmd.append(url)

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise PermissionError(
                f"Kerberos SPNEGO request failed for {url} (exit={proc.returncode}): "
                f"{proc.stderr.strip() or proc.stdout[:200]}"
            )
        return json.loads(proc.stdout)

    def odata_get(
        self,
        service: str,
        entity_path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an authenticated OData v4 GET request against a sc177 microservice.

        Uses OAuth2 Bearer token if available; otherwise falls back automatically to
        Kerberos SPNEGO (`curl --negotiate -u :`) when `kinit` ticket is present.
        """
        clean_service = service.strip("/")
        clean_path = entity_path.lstrip("/")
        if not clean_path.startswith("odata/"):
            clean_path = f"odata/{clean_path}"

        url = f"{self.base_url}/{clean_service}/v1/{clean_path}"
        if params:
            query_str = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            url = f"{url}?{query_str}"

        token = self.get_access_token()
        if not token and self.has_kerberos_ticket():
            return self._curl_negotiate_get(url)

        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(
                req, context=self.ssl_context, timeout=self.timeout
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                if self.has_kerberos_ticket():
                    return self._curl_negotiate_get(url)
                raise PermissionError(
                    f"401 Unauthorized accessing {url}. Run `kinit` in your HPC terminal "
                    "(recommended, bypasses Azure AD device conditional access), or run "
                    "`python scripts/nn_data_service_cli.py login` on a Novo-managed device."
                ) from exc
            raise

    # ------------------------------------------------------------------
    # Domain Queries: Imaging (siRNA Pools & Samples), Druggability, Safety
    # ------------------------------------------------------------------

    def search_sirna_pools(
        self,
        gene_symbol: str,
        top: int = 50,
        expand_samples: bool = True,
    ) -> list[dict[str, Any]]:
        """Search NNSamples/Pools by human/mouse gene symbol (case-insensitive contains/eq)."""
        safe_gene = escape_odata_string(gene_symbol.strip())
        params: dict[str, Any] = {
            "$filter": f" toupper(GeneSymbol) eq '{safe_gene.upper()}'",
            "$top": top,
        }
        if expand_samples:
            params["$expand"] = "Samples"
        res = self.odata_get("NNSamples", "Pools", params=params)
        return list(res.get("value", []))

    def get_plate_samples(
        self,
        container_label: str,
        top: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch well-level sample layout from NNSamples/Samples for a plate barcode/label."""
        safe_label = escape_odata_string(container_label.strip())
        params: dict[str, Any] = {
            "$filter": f"ContainerLabel eq '{safe_label}'",
            "$expand": "Pool",
            "$top": top,
        }
        res = self.odata_get("NNSamples", "Samples", params=params)
        return list(res.get("value", []))

    def search_internal_structures(
        self,
        query: str,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """Search NNStructures/PDBFiles by target name, description, NNC number, or ELN number."""
        safe_q = escape_odata_string(query.strip())
        params: dict[str, Any] = {
            "$filter": (
                f"contains(Name,'{safe_q}') or contains(Description,'{safe_q}') "
                f"or contains(NncNo,'{safe_q}') or contains(ElnExperimentNo,'{safe_q}')"
            ),
            "$select": (
                "Id,Name,Description,NncNo,BatchNo1,BatchNo2,ElnExperimentNo,"
                "Method,XrayResolution,XrayR,XrayRFree,ExperimentDate,Chemist"
            ),
            "$top": top,
        }
        res = self.odata_get("NNStructures", "PDBFiles", params=params)
        return list(res.get("value", []))

    def download_internal_pdb(self, pdb_id: int) -> str:
        """Download raw PDB coordinates from NNStructures/PDBFiles({Id})."""
        res = self.odata_get("NNStructures", f"PDBFiles({int(pdb_id)})")
        return str(res.get("PdbFile", ""))

    def get_compound_results(
        self,
        nnc_no: str,
        top: int = 200,
    ) -> list[dict[str, Any]]:
        """Query wet-lab assay readouts from NNResults/Results by NNC compound number."""
        safe_nnc = escape_odata_string(nnc_no.strip())
        params: dict[str, Any] = {
            "$filter": f"contains(NNCNo,'{safe_nnc}') and Invalid ne 'Y'",
            "$expand": "ExperimentVarResults",
            "$top": top,
        }
        res = self.odata_get("NNResults", "Results", params=params)
        return list(res.get("value", []))

    def search_eln_experiments(
        self,
        keyword: str | None = None,
        owner: str | None = None,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """Search NNExperiments/Experiments by title/experiment number and/or owner initials."""
        clauses = ["IsRedacted eq false"]
        if keyword:
            safe_kw = escape_odata_string(keyword.strip())
            clauses.append(f"(contains(Name,'{safe_kw}') or contains(No,'{safe_kw}'))")
        if owner:
            safe_owner = escape_odata_string(owner.strip().upper())
            clauses.append(f"OwnedBy eq '{safe_owner}'")
        params: dict[str, Any] = {
            "$filter": " and ".join(clauses),
            "$select": "Id,No,Name,OwnedBy,Date,LatestEntryDate,HasProtocol",
            "$orderby": "Id desc",
            "$top": top,
        }
        res = self.odata_get("NNExperiments", "Experiments", params=params)
        return list(res.get("value", []))

    def get_eln_entries(self, experiment_id: int) -> list[dict[str, Any]]:
        """Fetch all entries and attached file metadata for an ELN Experiment ID."""
        params: dict[str, Any] = {
            "$select": "Id,No,Title,EntryTypeAbb,EnterDate,Remarks",
            "$expand": "AttachedFiles",
        }
        res = self.odata_get(
            "NNExperiments", f"Experiments({int(experiment_id)})/Entries", params=params
        )
        return list(res.get("value", []))

    def render_eln_entry_text(self, experiment_id: int, entry_id: int) -> str:
        """Render an ELN Entry via `/Render`, decode Base64 HTML, and extract plain text."""
        import base64
        import re

        res = self.odata_get(
            "NNExperiments",
            f"Experiments({int(experiment_id)})/Entries({int(entry_id)})/Render",
        )
        b64_html = str(res.get("Base64Html", ""))
        if not b64_html:
            return ""
        html = base64.b64decode(b64_html).decode("utf-8", errors="replace")
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", html)
        text = text.replace("&nbsp;", " ")
        return re.sub(r"\s+", " ", text).strip()
