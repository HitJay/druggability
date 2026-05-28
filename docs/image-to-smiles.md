# Image-to-SMILES 工作流

这个仓库内置了一条批量 `image -> SMILES` 流程，适合后续统一处理结构图截图、专利附图或 PPT 中的化学结构。

## 设计原则

- 默认后端是 DECIMER，直接运行在当前 `bbbkit` 环境。
- 可选后端是 MolScribe，运行在独立 `.venv-chemocr` 中，避免与主环境冲突。
- 主流程负责目录扫描、调度 OCR worker、输出 CSV / SDF。

## 1. 默认使用 DECIMER

标准安装后即可直接使用：

```bash
bbbkit image2smiles data/raw/structures --recursive \
  --csv data/parsed/image_to_smiles.csv \
  --sdf data/parsed/image_to_smiles.sdf
```

如果图片来自手绘或板书，可加：

```bash
bbbkit image2smiles data/raw/handdrawn --recursive --hand-drawn
```

## 2. 初始化可选 MolScribe 环境

```bash
bash scripts/setup_image2smiles_env.sh
```

默认行为：

- 使用 `python3.10` 创建 `.venv-chemocr`
- 安装 `numpy<2`, `molscribe`, `huggingface_hub`, `pillow`
- 不主动下载模型；首次推理时自动从 HuggingFace 拉取

如果你希望初始化时就把模型下好：

```bash
DOWNLOAD_CHECKPOINT=1 bash scripts/setup_image2smiles_env.sh
```

模型默认保存或缓存到：

- HuggingFace 默认缓存目录
- 或 `CHECKPOINT_DIR` 指定的位置（开启 `DOWNLOAD_CHECKPOINT=1` 时）

## 3. 处理单张图片

```bash
bbbkit image2smiles data/raw/example.png --csv data/parsed/example.csv
```

## 4. 批量处理整个目录

```bash
bbbkit image2smiles data/raw/structures --recursive \
  --csv data/parsed/image_to_smiles.csv \
  --sdf data/parsed/image_to_smiles.sdf
```

## 5. 指定 MolScribe 后端、OCR Python 或 checkpoint

```bash
bbbkit image2smiles data/raw/structures --recursive \
  --backend molscribe \
  --ocr-python .venv-chemocr/bin/python \
  --checkpoint data/index/molscribe/swin_base_char_aux_1m.pth \
  --csv data/parsed/image_to_smiles.csv
```

## 6. 输出字段

CSV 字段：

- `image_path`
- `status`
- `success`
- `predicted_smiles`
- `canonical_smiles`
- `inchikey`
- `confidence`
- `error`

SDF 属性：

- `IMAGE_PATH`
- `STATUS`
- `PREDICTED_SMILES`
- `CANONICAL_SMILES`
- `INCHIKEY`
- `CONFIDENCE`

## 7. 常见问题

### 默认到底用 DECIMER 还是 MolScribe

默认是 DECIMER，直接用当前 `bbbkit` 环境。只有当你显式传入 `--backend molscribe` 时，才会调用独立 `.venv-chemocr`。

### MolScribe 在主 `.venv` 里装不上

这是预期现象。当前主环境是 Python 3.12，而 MolScribe 依赖链在这个版本上容易碰到 `torch / rdkit / numpy` 兼容问题，所以流程默认使用独立 `.venv-chemocr`。

### 为什么单独固定 `numpy<2`

MolScribe 及其依赖中的部分二进制包仍按 NumPy 1.x ABI 编译。在独立 OCR 环境里固定 `numpy<2` 可以避免 `_ARRAY_API not found` 这类错误。

### SDF 为什么只包含成功分子

SDF 需要可解析的分子图结构。对于 OCR 失败或输出了无效 SMILES 的图片，信息会保留在 CSV 的 `status/error` 中，但不会写入 SDF。