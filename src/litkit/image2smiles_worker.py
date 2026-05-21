"""独立 OCR worker：支持 DECIMER 和 MolScribe。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="image2smiles worker")
    parser.add_argument("--backend", default="decimer", choices=["decimer", "molscribe"])
    parser.add_argument("--images-file", required=True, help="图片路径列表文件，每行一个")
    parser.add_argument("--checkpoint", help="MolScribe checkpoint 路径")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--compute-confidence", action="store_true")
    parser.add_argument("--hand-drawn", action="store_true")
    return parser


def _load_checkpoint(checkpoint: str | None) -> str:
    if checkpoint:
        return checkpoint

    from huggingface_hub import hf_hub_download

    return hf_hub_download("yujieq/MolScribe", "swin_base_char_aux_1m.pth")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    images = [
        Path(line.strip()).expanduser().resolve()
        for line in Path(args.images_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if args.backend == "decimer":
        _run_decimer(images, compute_confidence=args.compute_confidence, hand_drawn=args.hand_drawn)
        return

    try:
        import torch
        from molscribe import MolScribe
    except Exception as exc:  # pragma: no cover - 依赖错误走集成路径
        print(f"worker import failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    checkpoint = _load_checkpoint(args.checkpoint)
    try:
        model = MolScribe(checkpoint, device=torch.device(args.device))
    except Exception as exc:
        print(f"worker model init failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    for image_path in images:
        record: dict[str, object] = {
            "image_path": str(image_path),
            "status": "failed",
        }
        try:
            output = model.predict_image_file(
                str(image_path),
                compute_confidence=args.compute_confidence,
                get_atoms_bonds=False,
            )
            smiles = output.get("smiles")
            if smiles:
                record["status"] = "ok"
                record["smiles"] = smiles
            else:
                record["error"] = "MolScribe 未返回 SMILES"

            if args.compute_confidence and "confidence" in output:
                record["confidence"] = output.get("confidence")
        except Exception as exc:  # pragma: no cover - 真实模型错误走集成路径
            record["error"] = f"{exc.__class__.__name__}: {exc}"

        print(json.dumps(record, ensure_ascii=False), flush=True)


def _run_decimer(images: list[Path], *, compute_confidence: bool, hand_drawn: bool) -> None:
    try:
        from DECIMER import predict_SMILES
    except Exception as exc:  # pragma: no cover - 依赖错误走集成路径
        print(f"worker import failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    for image_path in images:
        record: dict[str, object] = {
            "image_path": str(image_path),
            "status": "failed",
        }
        try:
            output = predict_SMILES(
                str(image_path),
                confidence=compute_confidence,
                hand_drawn=hand_drawn,
            )
            smiles, confidence = _normalize_decimer_output(output)
            if smiles:
                record["status"] = "ok"
                record["smiles"] = smiles
            else:
                record["error"] = "DECIMER 未返回 SMILES"
            if confidence is not None:
                record["confidence"] = confidence
        except Exception as exc:  # pragma: no cover - 真实模型错误走集成路径
            record["error"] = f"{exc.__class__.__name__}: {exc}"

        print(json.dumps(record, ensure_ascii=False), flush=True)


def _normalize_decimer_output(output) -> tuple[str | None, float | None]:
    if isinstance(output, tuple):
        smiles = str(output[0]) if output and output[0] else None
        confidence = _aggregate_confidence(output[1] if len(output) > 1 else None)
        return smiles, confidence

    if output:
        return str(output), None
    return None, None


def _aggregate_confidence(entries) -> float | None:
    if not entries:
        return None

    values: list[float] = []
    for entry in entries:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            try:
                values.append(float(entry[1]))
            except (TypeError, ValueError):
                continue
    if not values:
        return None
    return sum(values) / len(values)


if __name__ == "__main__":
    main()