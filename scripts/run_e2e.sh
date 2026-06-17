#!/usr/bin/env bash
# run_e2e.sh — BBB 端到端自动报告（序列 → ESM-2 GPU 预测 → Opus 解读 → HTML/PPTX）
#
# 为什么是两段式：本仓库没有任何单一环境同时具备 GPU 栈与 LLM SDK——
#   · miniforge3 base (/data/user/QYJI/miniforge3/bin/python): torch + fair-esm(pretrained) + CUDA，但无 openai
#   · 仓库 .venv: openai SDK（Opus 网关），但无 torch/fair-esm
# 故 Stage 1 用 miniforge3 在 A100 上做 ESM-2 预测（输出含 p_bbb 的 CSV），
#    Stage 2 用 .venv 读该 CSV 调 Opus 生成报告（CSV 含 p_bbb 时 CLI 跳过预测，无需 torch）。
#
# 用法:
#   bash scripts/run_e2e.sh <sequences.csv> <outdir> [--pptx] [--no-llm] [--bootstrap N]
# 示例:
#   bash scripts/run_e2e.sh output/2026-06-16/bbb_auto_report/demo_sequences.csv \
#        output/2026-06-16/bbb_e2e_full --pptx
#
# 输入 CSV 至少含 name,sequence 两列（可选 modification,known_route）。
set -euo pipefail

# ── 参数 ──
if [[ $# -lt 2 ]]; then
  echo "usage: bash scripts/run_e2e.sh <sequences.csv> <outdir> [--pptx] [--no-llm] [--bootstrap N]" >&2
  exit 2
fi
SEQ_CSV="$1"; OUTDIR="$2"; shift 2
EXTRA_PPTX=""; NO_LLM=""; BOOTSTRAP="200"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pptx) EXTRA_PPTX="--pptx"; shift;;
    --no-llm) NO_LLM="1"; shift;;
    --bootstrap) BOOTSTRAP="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

# ── 仓库根目录（脚本在 scripts/ 下）──
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# ── 环境与资源（见 repo memory: peptide-esm-platform.md）──
MF_PY="/data/user/QYJI/miniforge3/bin/python"          # GPU 栈：torch + fair-esm(pretrained)
VENV_PY="$REPO/.venv/bin/python"                        # LLM 栈：openai SDK
CKPT="$REPO/output/2026-06-15/brp_bbb_prediction/models/esm2/esm2_t30_150M_UR50D.pt"
EMB_CACHE="$REPO/output/2026-06-15/peptide_esm_platform/cache"   # 复用 11967 个嵌入，免重算
PRED_CSV="$OUTDIR/bbb_predictions_matrix.csv"

mkdir -p "$OUTDIR"
[[ -f "$SEQ_CSV" ]] || { echo "input not found: $SEQ_CSV" >&2; exit 1; }
[[ -x "$MF_PY"  ]] || { echo "miniforge3 python not found: $MF_PY" >&2; exit 1; }
[[ -f "$CKPT"   ]] || { echo "ESM-2 ckpt not found: $CKPT" >&2; exit 1; }

echo "════════════════════════════════════════════════════════════"
echo " Stage 1/2 · ESM-2 GPU prediction (miniforge3 + A100)"
echo "════════════════════════════════════════════════════════════"
# --no-llm：第一段只做预测（写出含 p_bbb 的 matrix CSV），不调 LLM
PYTHONPATH=src "$MF_PY" -m bbbkit.cli peptide report \
  -i "$SEQ_CSV" -o "$OUTDIR" \
  --ckpt "$CKPT" --cache-dir "$EMB_CACHE" --bootstrap "$BOOTSTRAP" --no-llm

[[ -f "$PRED_CSV" ]] || { echo "Stage 1 did not produce $PRED_CSV" >&2; exit 1; }
echo "Stage 1 OK -> $PRED_CSV"

if [[ -n "$NO_LLM" ]]; then
  echo "（--no-llm：跳过 Opus 解读，Stage 1 的模板报告即最终产物）"
  echo "DONE -> $OUTDIR/bbb_auto_report.html"
  exit 0
fi

echo "════════════════════════════════════════════════════════════"
echo " Stage 2/2 · Opus interpretation + report (.venv)"
echo "════════════════════════════════════════════════════════════"
[[ -x "$VENV_PY" ]] || { echo ".venv python not found: $VENV_PY" >&2; exit 1; }
# 载入 .env（export 格式）使 LLMClient 读到 Opus 网关凭据
[[ -f "$REPO/.env" ]] && { set -a; source "$REPO/.env"; set +a; }
# 第二段读 Stage 1 的 matrix CSV（含 p_bbb → CLI 走"直接报告"分支，不需 torch），调 Opus
PYTHONPATH=src "$VENV_PY" -m bbbkit.cli peptide report \
  -i "$PRED_CSV" -o "$OUTDIR" $EXTRA_PPTX

echo "════════════════════════════════════════════════════════════"
echo " DONE"
echo "   HTML : $OUTDIR/bbb_auto_report.html"
[[ -n "$EXTRA_PPTX" ]] && echo "   PPTX : $OUTDIR/bbb_auto_report.pptx"
echo "   CSV  : $PRED_CSV"
echo "════════════════════════════════════════════════════════════"
