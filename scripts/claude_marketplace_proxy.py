#!/usr/bin/env python3
"""Local Anthropic-compatible proxy for Claude Code via Novo Marketplace."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def marketplace_url(request_path: str) -> str:
    base = os.environ.get("MARKETPLACE_API_BASE_URL", "").rstrip("/")
    if not base:
        raise RuntimeError("MARKETPLACE_API_BASE_URL is required")

    base_parts = urllib.parse.urlsplit(base)
    path = urllib.parse.urlsplit(request_path).path or "/"
    if base_parts.path.rstrip("/").endswith("/v1") and path.startswith("/v1/"):
        path = path[len("/v1") :]
    return f"{base}{path}"


def sanitize_payload(raw_body: bytes) -> bytes:
    if not raw_body:
        return raw_body

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        return raw_body

    if not isinstance(payload, dict):
        return raw_body

    strip_fields = os.environ.get(
        "CLAUDE_MARKETPLACE_STRIP_FIELDS", "context_management"
    ).split(",")
    for field in strip_fields:
        field = field.strip()
        if field:
            payload.pop(field, None)

    force_model = os.environ.get("CLAUDE_MARKETPLACE_FORCE_MODEL", "1").lower()
    model_name = os.environ.get("MARKETPLACE_MODEL_NAME")
    if model_name and force_model not in {"0", "false", "no"}:
        payload["model"] = model_name

    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class MarketplaceProxyHandler(BaseHTTPRequestHandler):
    server_version = "ClaudeMarketplaceProxy/0.1"

    def do_GET(self) -> None:
        if self.path in {"/", "/health", "/healthz"}:
            self.send_response(200)
            self.send_header("content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        api_key = os.environ.get("MARKETPLACE_API_KEY")
        if not api_key:
            self.send_error(500, "MARKETPLACE_API_KEY is required")
            return

        content_length = int(self.headers.get("content-length", "0") or "0")
        raw_body = self.rfile.read(content_length)
        body = sanitize_payload(raw_body)

        headers = {
            "content-type": self.headers.get("content-type", "application/json"),
            "x-api-key": api_key,
            "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
        }
        for header_name in ("accept", "anthropic-beta"):
            header_value = self.headers.get(header_name)
            if header_value:
                headers[header_name] = header_value

        try:
            request = urllib.request.Request(
                marketplace_url(self.path), data=body, headers=headers, method="POST"
            )
            timeout = float(os.environ.get("API_TIMEOUT", "120"))
            with urllib.request.urlopen(request, timeout=timeout) as response:
                self.send_response(response.status)
                for name, value in response.headers.items():
                    if name.lower() not in HOP_BY_HOP_HEADERS:
                        self.send_header(name, value)
                self.end_headers()
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as error:
            error_body = error.read()
            self.send_response(error.code)
            content_type = error.headers.get("content-type", "application/json")
            self.send_header("content-type", content_type)
            self.end_headers()
            self.wfile.write(error_body)
        except Exception as error:  # pragma: no cover - defensive CLI boundary
            self.send_response(502)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(error)}).encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("CLAUDE_MARKETPLACE_VERBOSE"):
            super().log_message(format, *args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default=".env", help="Path to the Marketplace .env file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args(argv)

    load_env_file(Path(args.env))
    server = ThreadingHTTPServer((args.host, args.port), MarketplaceProxyHandler)
    print(f"Claude Marketplace proxy listening on http://{args.host}:{args.port}", file=sys.stderr)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())