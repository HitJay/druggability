#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${CLAUDE_MARKETPLACE_ENV:-$REPO_ROOT/.env}"
PORT="${CLAUDE_MARKETPLACE_PROXY_PORT:-18080}"
HOST="127.0.0.1"
LOG_FILE="${CLAUDE_MARKETPLACE_LOG:-/tmp/claude-marketplace-proxy.log}"
PYTHON_BIN="${PYTHON:-python3}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

MARKETPLACE_MODEL_NAME="${CLAUDE_MARKETPLACE_MODEL_NAME:-anthropic_claude_opus_latest}"

: "${MARKETPLACE_API_KEY:?MARKETPLACE_API_KEY is required in $ENV_FILE}"
: "${MARKETPLACE_API_BASE_URL:?MARKETPLACE_API_BASE_URL is required in $ENV_FILE}"
: "${MARKETPLACE_MODEL_NAME:?MARKETPLACE_MODEL_NAME is required in $ENV_FILE}"

"$PYTHON_BIN" "$SCRIPT_DIR/claude_marketplace_proxy.py" \
  --env "$ENV_FILE" \
  --host "$HOST" \
  --port "$PORT" \
  >"$LOG_FILE" 2>&1 &
PROXY_PID=$!

cleanup() {
  kill "$PROXY_PID" >/dev/null 2>&1 || true
  wait "$PROXY_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

READY=0
for _ in {1..50}; do
  if curl -fsS "http://$HOST:$PORT/healthz" >/dev/null 2>&1; then
    READY=1
    break
  fi
done

if [[ "$READY" != "1" ]]; then
  echo "Claude Marketplace proxy failed to start. Log: $LOG_FILE" >&2
  sed -n '1,120p' "$LOG_FILE" >&2 || true
  exit 1
fi

export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-local-proxy-key}"
export ANTHROPIC_BASE_URL="http://$HOST:$PORT"
export ANTHROPIC_MODEL="$MARKETPLACE_MODEL_NAME"

HAS_MODEL=0
for arg in "$@"; do
  if [[ "$arg" == "--model" || "$arg" == --model=* ]]; then
    HAS_MODEL=1
    break
  fi
done

CLAUDE_ARGS=("$@")
HAS_BARE=0
for arg in "${CLAUDE_ARGS[@]}"; do
  if [[ "$arg" == "--bare" ]]; then
    HAS_BARE=1
    break
  fi
done

if [[ "${CLAUDE_MARKETPLACE_NO_BARE:-0}" != "1" && "$HAS_BARE" == "0" ]]; then
  CLAUDE_ARGS=(--bare "${CLAUDE_ARGS[@]}")
fi

if [[ "$HAS_MODEL" == "0" ]]; then
  CLAUDE_ARGS=(--model "$MARKETPLACE_MODEL_NAME" "${CLAUDE_ARGS[@]}")
fi

echo "Claude Code via Novo Marketplace proxy: model=$MARKETPLACE_MODEL_NAME base=http://$HOST:$PORT" >&2
claude "${CLAUDE_ARGS[@]}"