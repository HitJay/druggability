#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OCR_PYTHON="${OCR_PYTHON:-python3.10}"
OCR_ENV_DIR="${OCR_ENV_DIR:-$ROOT_DIR/.venv-chemocr}"
REQ_FILE="$ROOT_DIR/requirements-image2smiles.txt"
DOWNLOAD_CHECKPOINT="${DOWNLOAD_CHECKPOINT:-0}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-$ROOT_DIR/data/index/molscribe}"
CHECKPOINT_FILE="${CHECKPOINT_FILE:-swin_base_char_aux_1m.pth}"

if ! command -v "$OCR_PYTHON" >/dev/null 2>&1; then
  echo "[image2smiles] 未找到 Python: $OCR_PYTHON" >&2
  exit 1
fi

echo "[image2smiles] 创建 OCR 环境: $OCR_ENV_DIR"
"$OCR_PYTHON" -m venv "$OCR_ENV_DIR"
source "$OCR_ENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$REQ_FILE"

if [[ "$DOWNLOAD_CHECKPOINT" == "1" ]]; then
  mkdir -p "$CHECKPOINT_DIR"
  python - <<PY
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="yujieq/MolScribe",
    filename="$CHECKPOINT_FILE",
    local_dir=r"$CHECKPOINT_DIR",
)
print(path)
PY
else
  echo "[image2smiles] 跳过 checkpoint 预下载；首次推理会自动从 HuggingFace 拉取。"
fi

cat <<EOF
[image2smiles] OCR 环境已就绪: $OCR_ENV_DIR
[image2smiles] 默认 OCR Python: $OCR_ENV_DIR/bin/python
[image2smiles] 注意：主 CLI 默认使用当前环境中的 DECIMER；该脚本只为可选 MolScribe 后端准备独立环境。

[image2smiles] 示例：
  litkit image2smiles data/raw/structures --recursive \
    --backend molscribe \
    --csv data/parsed/image_to_smiles.csv \
    --sdf data/parsed/image_to_smiles.sdf

[image2smiles] 如需预下载模型：
  DOWNLOAD_CHECKPOINT=1 bash scripts/setup_image2smiles_env.sh
EOF