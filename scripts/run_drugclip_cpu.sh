#!/usr/bin/env bash
# 在 CPU 上运行 DrugCLIP 推理（retrieval 虚拟筛选 / test benchmark 评测）
#
# 官方 retrieval.sh / test.sh 默认带 --fp16 且 CUDA_VISIBLE_DEVICES="1"（需 GPU）。
# 本脚本去掉 --fp16、强制 CPU、调小 batch，使无 GPU 机器也能跑。
#
# 前置:
#   1. bash scripts/setup_drugclip_env.sh 已执行
#   2. 从 Google Drive 下载并放入 DrugCLIP/:
#        checkpoint_best.pt   （训练好的权重）
#        mols.lmdb, pocket.lmdb （retrieval 模式）/ 或 DUD-E|PCBA 测试集（test 模式）
#
# 用法:
#   bash scripts/run_drugclip_cpu.sh retrieval [--batch-size 2]
#   bash scripts/run_drugclip_cpu.sh test      --task PCBA|DUDE [--batch-size 2]
set -euo pipefail

MODE="${1:-retrieval}"
shift || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRUGCLIP_DIR="${DRUGCLIP_DIR:-$ROOT_DIR/DrugCLIP}"
DRUGCLIP_VENV="${DRUGCLIP_VENV:-$ROOT_DIR/drugclip-venv}"
RESULTS_PATH="${RESULTS_PATH:-$DRUGCLIP_DIR/test}"
BATCH_SIZE="${BATCH_SIZE:-2}"
WEIGHT_PATH="${WEIGHT_PATH:-$DRUGCLIP_DIR/checkpoint_best.pt}"
NUM_WORKERS="${NUM_WORKERS:-0}"

if [[ ! -f "$WEIGHT_PATH" ]]; then
  echo "[drugclip] 缺少权重: $WEIGHT_PATH" >&2
  echo "[drugclip] 请先从 Google Drive 下载 checkpoint_best.pt 放入 DrugCLIP/" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$DRUGCLIP_VENV/bin/activate"
cd "$DRUGCLIP_DIR"

# 强制 CPU、去掉 --fp16
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

case "$MODE" in
  retrieval)
    MOL_PATH="${MOL_PATH:-$DRUGCLIP_DIR/mols.lmdb}"
    POCKET_PATH="${POCKET_PATH:-$DRUGCLIP_DIR/pocket.lmdb}"
    echo "[drugclip] retrieval（CPU, batch=$BATCH_SIZE）"
    python ./unimol/retrieval.py --user-dir ./unimol ./data --valid-subset test \
      --results-path "$RESULTS_PATH" \
      --num-workers "$NUM_WORKERS" --ddp-backend=c10d --batch-size "$BATCH_SIZE" \
      --task drugclip --loss in_batch_softmax --arch drugclip \
      --max-pocket-atoms 256 --seed 1 \
      --path "$WEIGHT_PATH" \
      --log-interval 100 --log-format simple \
      --mol-path "$MOL_PATH" --pocket-path "$POCKET_PATH" \
      --emb-dir ./data/emb "$@"
    ;;
  test)
    TASK="${TASK:-PCBA}"
    echo "[drugclip] test $TASK（CPU, batch=$BATCH_SIZE）"
    python ./unimol/test.py --user-dir ./unimol ./data --valid-subset test \
      --results-path "$RESULTS_PATH" \
      --num-workers "$NUM_WORKERS" --ddp-backend=c10d --batch-size "$BATCH_SIZE" \
      --task drugclip --loss in_batch_softmax --arch drugclip \
      --seed 1 \
      --path "$WEIGHT_PATH" \
      --log-interval 100 --log-format simple \
      --max-pocket-atoms 511 \
      --test-task "$TASK" "$@"
    ;;
  *)
    echo "用法: $0 {retrieval|test} [额外 unicore 参数]" >&2
    exit 1
    ;;
esac
