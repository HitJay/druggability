#!/usr/bin/env python3
"""
Internal worker for DrugCLIP inference under isolated drugclip venv.
Invoked by bbbkit.druggability.drugclip.screen_drugclip via subprocess.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("drugclip_worker")


def parse_args():
    parser = argparse.ArgumentParser(description="DrugCLIP retrieval worker")
    parser.add_argument("--drugclip-repo", type=str, required=True, help="Path to DrugCLIP repository")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint_best.pt")
    parser.add_argument("--pocket-lmdb", type=str, required=True, help="Path to pocket LMDB file")
    parser.add_argument("--mol-lmdb", type=str, required=True, help="Path to molecule LMDB file")
    parser.add_argument("--emb-dir", type=str, required=True, help="Directory to cache mol embeddings")
    parser.add_argument("--output-json", type=str, required=True, help="Output JSON file for results")
    parser.add_argument("--top-k", type=int, default=100, help="Number of top compounds to retrieve")
    parser.add_argument("--device-id", type=int, default=0, help="CUDA device index")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for inference")
    parser.add_argument("--num-workers", type=int, default=2, help="DataLoader workers")
    return parser.parse_args()


def main():
    start_time = time.time()
    args = parse_args()

    # Add DrugCLIP repo to sys.path
    repo_path = Path(args.drugclip_repo).resolve()
    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))

    import torch
    from unicore import checkpoint_utils, options, tasks

    use_cuda = torch.cuda.is_available()
    if use_cuda:
        torch.cuda.set_device(args.device_id)
        logger.info("Using CUDA device: %d (%s)", args.device_id, torch.cuda.get_device_name(args.device_id))
    else:
        logger.warning("CUDA not available, running on CPU")

    user_dir = str(repo_path / "unimol")
    data_dir = str(repo_path / "data")

    # Build unicore CLI arguments
    parser = options.get_validation_parser()
    parser.add_argument("--mol-path", type=str, default="")
    parser.add_argument("--pocket-path", type=str, default="")
    parser.add_argument("--emb-dir", type=str, default="")
    options.add_model_args(parser)

    unicore_args_list = [
        "--user-dir", user_dir,
        data_dir,
        "--valid-subset", "test",
        "--results-path", str(Path(args.output_json).parent),
        "--num-workers", str(args.num_workers),
        "--ddp-backend", "c10d",
        "--batch-size", str(args.batch_size),
        "--task", "drugclip",
        "--loss", "in_batch_softmax",
        "--arch", "drugclip",
        "--max-pocket-atoms", "256",
        "--fp16",
        "--seed", "1",
        "--path", args.checkpoint,
        "--mol-path", args.mol_lmdb,
        "--pocket-path", args.pocket_lmdb,
        "--emb-dir", args.emb_dir,
    ]

    unicore_args = options.parse_args_and_arch(parser, unicore_args_list)

    logger.info("Loading model weights from %s", args.checkpoint)
    state = checkpoint_utils.load_checkpoint_to_cpu(args.checkpoint)
    task = tasks.setup_task(unicore_args)
    model = task.build_model(unicore_args)
    model.load_state_dict(state["model"], strict=False)

    if unicore_args.fp16:
        model.half()
    if use_cuda:
        model.cuda()
    model.eval()

    logger.info("Retrieving Top-%d compounds...", args.top_k)
    names, scores = task.retrieve_mols(
        model,
        args.mol_lmdb,
        args.pocket_lmdb,
        args.emb_dir,
        args.top_k,
    )

    hits = []
    for rank, (name, score) in enumerate(zip(names, scores), start=1):
        hits.append({
            "rank": rank,
            "smi": str(name),
            "score": float(score),
        })

    elapsed = time.time() - start_time
    logger.info("Retrieval completed in %.2fs. Top score: %.4f, Lowest retrieved score: %.4f",
                elapsed, hits[0]["score"] if hits else 0.0, hits[-1]["score"] if hits else 0.0)

    # Save structured results
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_data = {
        "ok": True,
        "hits_count": len(hits),
        "top_k": args.top_k,
        "elapsed_seconds": round(elapsed, 3),
        "checkpoint": args.checkpoint,
        "mol_lmdb": args.mol_lmdb,
        "pocket_lmdb": args.pocket_lmdb,
        "emb_dir": args.emb_dir,
        "hits": hits,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    # Also save a standard ranked_compounds.tsv
    tsv_path = out_path.with_suffix(".tsv")
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write("rank\tsmiles\tdrugclip_score\n")
        for h in hits:
            f.write(f"{h['rank']}\t{h['smi']}\t{h['score']:.6f}\n")

    logger.info("Saved results to %s and %s", out_path, tsv_path)


if __name__ == "__main__":
    main()
