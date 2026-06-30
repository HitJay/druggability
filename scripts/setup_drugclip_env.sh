#!/usr/bin/env bash
# 部署 DrugCLIP 运行环境（CPU，无需 GPU / conda）
#
# DrugCLIP 官方要求 Python 3.8 + rdkit + Uni-Mol(Uni-Core) + torch。本脚本用 uv
# 拉起一个独立 Python 3.8 venv，装 CPU 版 torch，从源码构建 Uni-Core（禁用 CUDA ext），
# 并克隆 DrugCLIP 仓库。无 GPU 也能跑 retrieval/test（去掉 --fp16，见 run_drugclip_cpu.sh）。
#
# 用法:
#   bash scripts/setup_drugclip_env.sh            # 默认 CPU
#   FORCE_CUDA=1 bash scripts/setup_drugclip_env.sh  # 有 GPU 时装 CUDA 版 torch
#
# 产出:
#   $DRUGCLIP_ROOT/DrugCLIP        代码仓库
#   $DRUGCLIP_VENV                 Python 3.8 venv（torch 2.0.1 + unicore + rdkit）
#
# 注意: 模型权重 + retrieval 示例数据需从 Google Drive 手动下载（见脚本末尾说明），
#       某些沙箱网络环境屏蔽 drive.google.com 文件夹页面，需在有访问权限的机器上执行。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRUGCLIP_ROOT="${DRUGCLIP_ROOT:-$ROOT_DIR}"
DRUGCLIP_VENV="${DRUGCLIP_VENV:-$ROOT_DIR/drugclip-venv}"
UNICORE_DIR="${UNICORE_DIR:-$ROOT_DIR/Uni-Core}"
FORCE_CUDA="${FORCE_CUDA:-0}"

echo "[drugclip] ROOT_DIR=$ROOT_DIR  VENV=$DRUGCLIP_VENV"

# ── 1. uv（用于管理 Python 3.8 + venv，单文件免 root）─────────────
if ! command -v uv >/dev/null 2>&1; then
  echo "[drugclip] 安装 uv ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
export UV_LINK_MODE=copy  # 避免跨文件系统 hardlink 警告

# ── 2. Python 3.8 + venv ─────────────────────────────────────────
uv python install 3.8
uv venv "$DRUGCLIP_VENV" --python 3.8
# shellcheck disable=SC1091
source "$DRUGCLIP_VENV/bin/activate"

# ── 3. torch（CPU 或 CUDA）────────────────────────────────────────
if [[ "$FORCE_CUDA" == "1" ]]; then
  echo "[drugclip] 安装 CUDA 版 torch 2.0.1 ..."
  uv pip install torch==2.0.1
else
  echo "[drugclip] 安装 CPU 版 torch 2.0.1（如需 GPU: FORCE_CUDA=1 重跑）"
  uv pip install torch==2.0.1+cpu --index-url https://download.pytorch.org/whl/cpu
fi

# ── 4. DrugCLIP 其余依赖 ──────────────────────────────────────────
# 注意: lmdb 必须从源码构建（py3.8 上 2.x 的预编译 wheel 有 Py_SET_REFCNT ABI 不兼容）
uv pip install --force-reinstall --no-binary lmdb "lmdb==1.4.1"
uv pip install rdkit selfies tqdm scikit-learn numpy "pandas<2.1" ipython gdown \
  "tokenizers>=0.11,<0.16" ml_collections scipy tensorboardX cffi

# ── 5. Uni-Core（Uni-Mol 框架，CPU 构建禁用 CUDA ext）────────────
if [[ ! -d "$UNICORE_DIR" ]]; then
  git clone --depth 1 https://github.com/dptech-corp/Uni-Core.git "$UNICORE_DIR"
fi
pushd "$UNICORE_DIR" >/dev/null
# --no-deps: 避免 unicore 的 torch>=2.0.0 依赖把 CPU torch 升级成 CUDA 版
uv pip install . --no-build-isolation --no-deps
popd >/dev/null

# ── 6. DrugCLIP 仓库 ──────────────────────────────────────────────
if [[ ! -d "$DRUGCLIP_ROOT/DrugCLIP" ]]; then
  git clone --depth 1 https://github.com/bowen-gao/DrugCLIP.git "$DRUGCLIP_ROOT/DrugCLIP"
fi

# ── 7. 验证 ───────────────────────────────────────────────────────
python - <<'PY'
import torch, rdkit, lmdb, unicore
print(f"[drugclip] torch={torch.__version__} cuda={torch.cuda.is_available()}")
print(f"[drugclip] rdkit={rdkit.__version__} lmdb={lmdb.__version__} unicore OK")
PY

echo
echo "[drugclip] 环境就绪: source $DRUGCLIP_VENV/bin/activate"
echo "[drugclip] 验证管线: cd DrugCLIP && python unimol/retrieval.py --user-dir ./unimol --help"
echo
echo "[drugclip] 还需手动下载权重 + 示例数据（Google Drive 文件夹可能被部分网络屏蔽）:"
echo "    https://drive.google.com/drive/folders/1zW1MGpgunynFxTKXC2Q4RgWxZmg6CInV"
echo "    取回后放入 DrugCLIP/: checkpoint_best.pt, mols.lmdb, pocket.lmdb"
echo "    然后运行: bash scripts/run_drugclip_cpu.sh retrieval"
