#!/usr/bin/env python3 -u
"""Reverse retrieval for DrugCLIP: encode pockets + molecules, save full score matrix.

Adapted from official unimol/retrieval.py (MIT, DP Technology). Runs inside the
drugclip venv. Outputs <emb_dir>/reverse_matrix.pkl with S[pocket, mol] cosine.
"""
import os, sys, pickle
import numpy as np
import torch
from unicore import checkpoint_utils, options, tasks
import unicore
from tqdm import tqdm


def main():
    parser = options.get_validation_parser()
    parser.add_argument("--mol-path", type=str, default="")
    parser.add_argument("--pocket-path", type=str, default="")
    parser.add_argument("--emb-dir", type=str, default="")
    options.add_model_args(parser)
    args = options.parse_args_and_arch(parser)

    use_fp16 = args.fp16
    use_cuda = torch.cuda.is_available() and not args.cpu
    if use_cuda:
        torch.cuda.set_device(args.device_id)

    state = checkpoint_utils.load_checkpoint_to_cpu(args.path)
    task = tasks.setup_task(args)
    model = task.build_model(args)
    model.load_state_dict(state["model"], strict=False)
    if use_fp16:
        model.half()
    if use_cuda:
        model.cuda()
    model.eval()

    os.makedirs(args.emb_dir, exist_ok=True)

    # molecules (cached encode from official task)
    mol_reps, mol_names = task.encode_mols_once(model, args.mol_path, args.emb_dir, "atoms", "coordinates")

    # pockets (fresh encode, mirrors retrieve_mols pocket block)
    pocket_dataset = task.load_pockets_dataset(args.pocket_path)
    pocket_data = torch.utils.data.DataLoader(pocket_dataset, batch_size=8, collate_fn=pocket_dataset.collater)
    pocket_reps, pocket_names = [], []
    for _, sample in enumerate(tqdm(pocket_data)):
        sample = unicore.utils.move_to_cuda(sample)
        dist = sample["net_input"]["pocket_src_distance"]
        et = sample["net_input"]["pocket_src_edge_type"]
        st = sample["net_input"]["pocket_src_tokens"]
        pocket_padding_mask = st.eq(model.pocket_model.padding_idx)
        pocket_x = model.pocket_model.embed_tokens(st)
        n_node = dist.size(-1)
        gbf_feature = model.pocket_model.gbf(dist, et)
        gbf_result = model.pocket_model.gbf_proj(gbf_feature)
        graph_attn_bias = gbf_result
        graph_attn_bias = graph_attn_bias.permute(0, 3, 1, 2).contiguous()
        graph_attn_bias = graph_attn_bias.view(-1, n_node, n_node)
        pocket_outputs = model.pocket_model.encoder(pocket_x, padding_mask=pocket_padding_mask, attn_mask=graph_attn_bias)
        pocket_encoder_rep = pocket_outputs[0][:, 0, :]
        pocket_emb = model.pocket_project(pocket_encoder_rep)
        pocket_emb = pocket_emb / pocket_emb.norm(dim=-1, keepdim=True)
        pocket_reps.append(pocket_emb.detach().cpu().float().numpy())
        pocket_names.extend(sample["pocket_name"])
    pocket_reps = np.concatenate(pocket_reps, axis=0)

    S = pocket_reps @ np.asarray(mol_reps).T  # [n_pocket, n_mol] cosine
    out = os.path.join(args.emb_dir, "reverse_matrix.pkl")
    with open(out, "wb") as f:
        pickle.dump({"S": S, "mol_names": list(mol_names), "pocket_names": [str(p) for p in pocket_names]}, f)
    print("REVERSE_MATRIX_SAVED", out, S.shape)


if __name__ == "__main__":
    main()
