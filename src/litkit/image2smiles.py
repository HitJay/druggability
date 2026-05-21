"""
image2smiles — 批量结构图转 SMILES。

设计要点：
- 默认使用当前环境中的 DECIMER，开箱即可做批处理。
- 可选使用独立 MolScribe 环境，避免重型依赖与主环境冲突。
- 主进程负责文件发现、结果整形、CSV/SDF 输出。
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from rdkit import Chem
from rdkit.Chem import AllChem

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
SUPPORTED_BACKENDS = {"decimer", "molscribe"}


@dataclass
class ImageToSmilesResult:
    image_path: str
    status: str
    predicted_smiles: str | None = None
    canonical_smiles: str | None = None
    inchikey: str | None = None
    confidence: float | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return bool(self.canonical_smiles)

    def to_dict(self) -> dict[str, object]:
        return {
            "image_path": self.image_path,
            "status": self.status,
            "success": self.success,
            "predicted_smiles": self.predicted_smiles,
            "canonical_smiles": self.canonical_smiles,
            "inchikey": self.inchikey,
            "confidence": self.confidence,
            "error": self.error,
        }


def discover_image_paths(inputs: Sequence[str], recursive: bool = False) -> list[Path]:
    """从文件或目录收集待处理图片。"""
    discovered: list[Path] = []
    seen: set[str] = set()

    for raw_input in inputs:
        candidate = Path(raw_input).expanduser()
        if candidate.is_file():
            paths = [candidate]
        elif candidate.is_dir():
            pattern = "**/*" if recursive else "*"
            paths = [path for path in candidate.glob(pattern) if path.is_file()]
        else:
            raise FileNotFoundError(f"输入不存在: {raw_input}")

        for path in paths:
            if path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            resolved = path.resolve()
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            discovered.append(resolved)

    return discovered


def run_image_to_smiles_batch(
    image_paths: Sequence[Path],
    *,
    backend: str = "decimer",
    ocr_python: str | None = None,
    checkpoint: str | None = None,
    device: str = "cpu",
    compute_confidence: bool = False,
    hand_drawn: bool = False,
) -> list[ImageToSmilesResult]:
    """调用独立 worker 执行 OCR，并在主环境中完成结果标准化。"""
    if not image_paths:
        return []

    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}")

    requested_python = ocr_python or _default_ocr_python(backend)
    python_executable = _resolve_python_executable(requested_python, backend)
    worker_entry, worker_cwd = _resolve_worker_launch(python_executable)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
        for image_path in image_paths:
            handle.write(f"{image_path.resolve()}\n")
        image_list_path = handle.name

    cmd = [
        python_executable,
        worker_entry,
        "--backend",
        backend,
        "--images-file",
        image_list_path,
        "--device",
        device,
    ]
    if checkpoint:
        cmd.extend(["--checkpoint", checkpoint])
    if compute_confidence:
        cmd.append("--compute-confidence")
    if hand_drawn:
        cmd.append("--hand-drawn")

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=worker_cwd)
    finally:
        os.unlink(image_list_path)

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(stderr.splitlines()[-1])

    raw_records = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        raw_records.append(json.loads(line))

    record_by_path = {
        str(Path(str(record["image_path"])).resolve()): record
        for record in raw_records
        if record.get("image_path")
    }

    results: list[ImageToSmilesResult] = []
    for image_path in image_paths:
        key = str(image_path.resolve())
        record = record_by_path.get(key)
        if record is None:
            results.append(
                ImageToSmilesResult(
                    image_path=key,
                    status="failed",
                    error="OCR worker 未返回该图片的结果",
                )
            )
            continue
        results.append(_normalize_worker_record(record))

    return results


def write_results_csv(results: Sequence[ImageToSmilesResult], output_path: str | os.PathLike[str]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_path",
                "status",
                "success",
                "predicted_smiles",
                "canonical_smiles",
                "inchikey",
                "confidence",
                "error",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())


def write_results_sdf(results: Sequence[ImageToSmilesResult], output_path: str | os.PathLike[str]) -> None:
    """将成功预测的分子写入 SDF。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(path))
    writer.SetKekulize(False)
    try:
        for result in results:
            if not result.canonical_smiles:
                continue
            mol = Chem.MolFromSmiles(result.canonical_smiles)
            if mol is None:
                continue
            AllChem.Compute2DCoords(mol)
            mol.SetProp("_Name", Path(result.image_path).stem)
            mol.SetProp("IMAGE_PATH", result.image_path)
            mol.SetProp("STATUS", result.status)
            mol.SetProp("PREDICTED_SMILES", result.predicted_smiles or "")
            mol.SetProp("CANONICAL_SMILES", result.canonical_smiles)
            mol.SetProp("INCHIKEY", result.inchikey or "")
            if result.confidence is not None:
                mol.SetProp("CONFIDENCE", f"{result.confidence:.6f}")
            writer.write(mol)
    finally:
        writer.close()


def _default_ocr_python(backend: str) -> str:
    if backend == "decimer":
        return shutil.which("python") or sys.executable
    return ".venv-chemocr/bin/python"


def _resolve_python_executable(ocr_python: str, backend: str) -> str:
    expanded = Path(ocr_python).expanduser()
    if expanded.is_file():
        return str(expanded.absolute())

    resolved = shutil.which(ocr_python)
    if resolved:
        return resolved

    if backend == "molscribe":
        raise FileNotFoundError(
            f"未找到 MolScribe OCR Python: {ocr_python}。请先运行 bash scripts/setup_image2smiles_env.sh"
        )
    raise FileNotFoundError(f"未找到 OCR Python: {ocr_python}")


def _resolve_worker_launch(python_executable: str) -> tuple[str, str | None]:
    relative_worker = Path("src/litkit/image2smiles_worker.py")
    candidate_roots: list[Path] = []

    cwd = Path.cwd()
    candidate_roots.append(cwd)

    python_path = Path(python_executable).expanduser()
    if len(python_path.parents) >= 3:
        candidate_roots.append(python_path.parents[2])

    candidate_roots.append(Path(__file__).resolve().parents[2])

    seen: set[str] = set()
    for root in candidate_roots:
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        if (root / relative_worker).is_file():
            return str(relative_worker), str(root)

    return str(Path(__file__).with_name("image2smiles_worker.py")), None


def _normalize_worker_record(record: dict[str, object]) -> ImageToSmilesResult:
    image_path = str(Path(str(record["image_path"])).resolve())
    predicted_smiles = record.get("smiles")
    confidence = _coerce_float(record.get("confidence"))
    error = record.get("error")
    status = str(record.get("status") or ("ok" if predicted_smiles else "failed"))

    if predicted_smiles:
        raw_smiles = str(predicted_smiles)
        mol = Chem.MolFromSmiles(raw_smiles)
        if mol is None:
            return ImageToSmilesResult(
                image_path=image_path,
                status="invalid_smiles",
                predicted_smiles=raw_smiles,
                confidence=confidence,
                error="RDKit 无法解析 OCR 输出的 SMILES",
            )
        canonical_smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
        inchikey = Chem.MolToInchiKey(mol)
        return ImageToSmilesResult(
            image_path=image_path,
            status="ok",
            predicted_smiles=raw_smiles,
            canonical_smiles=canonical_smiles,
            inchikey=inchikey,
            confidence=confidence,
        )

    return ImageToSmilesResult(
        image_path=image_path,
        status=status,
        confidence=confidence,
        error=str(error or "OCR 未返回 SMILES"),
    )


def _coerce_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "IMAGE_SUFFIXES",
    "ImageToSmilesResult",
    "SUPPORTED_BACKENDS",
    "discover_image_paths",
    "run_image_to_smiles_batch",
    "write_results_csv",
    "write_results_sdf",
]