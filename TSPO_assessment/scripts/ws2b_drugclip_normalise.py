"""Per-pocket normalisation of DrugCLIP reverse scores.

Runs the OFFICIAL 2.94M-molecule LMDB through the same encoders to get the
background score distribution per pocket, then z-scores the 7 query ligands
against their pocket's background. This is the plan's WS2.3 mitigation for
cross-pocket incomparability.

Runs INSIDE the drugclip venv (needs torch+unicore).
"""
import os, sys, pickle
import numpy as np
import torch
from unicore import checkpoint_utils, options, tasks
import unicore
from tqdm import tqdm

DC = "/das/user/QYJI/druggability/output/2026-07-02/drugclip_install_probe/DrugCLIP"
CKPT = "/das/user/QYJI/druggability/output/2026-07-02/drugclip_install_probe/checkpoints/drugclip_data/checkpoint_best.pt"
POCKETS = "/das/user/QYJI/druggability/TSPO_assessment/output/drugclip_reverse/pockets.lmdb"
QUERY = "/das/user/QYJI/druggability/TSPO_assessment/output/drugclip_reverse/ligands.lmdb"
MOLS = "/das/user/QYJI/druggability/output/2026-07-02/drugclip_install_probe/checkpoints/drugclip_data/retrieval/mols.lmdb"
EMB = "/das/user/QYJI/druggability/TSPO_assessment/output/drugclip_reverse/emb"
BATCH = 512


def encode_pockets(model, task, path):
    ds = task.load_pockets_dataset(path)
    dl = torch.utils.data.DataLoader(ds, batch_size=8, collate_fn=ds.collater)
    reps, names = [], []
    for sample in tqdm(dl):
        sample = unicore.utils.move_to_cuda(sample)
        dist = sample["net_input"]["pocket_src_distance"]
        et = sample["net_input"]["pocket_src_edge_type"]
        st = sample["net_input"]["pocket_src_tokens"]
        pm = st.eq(model.pocket_model.padding_idx)
        x = model.pocket_model.embed_tokens(st)
        n = dist.size(-1)
        gbf = model.pocket_model.gbf_proj(model.pocket_model.gbf(dist, et))
        attn = gbf.permute(0, 3, 1, 2).contiguous().view(-1, n, n)
        out = model.pocket_model.encoder(x, padding_mask=pm, attn_mask=attn)
        emb = model.pocket_project(out[0][:, 0, :])
        emb = emb / emb.norm(dim=-1, keepdim=True)
        reps.append(emb.detach().cpu().float().numpy())
        names.extend(str(p) for p in sample["pocket_name"])
    return np.concatenate(reps), names


def encode_mols(model, task, path, cache_name):
    reps, names = task.encode_mols_once(model, path, EMB, "atoms", "coordinates")
    return np.asarray(reps), list(names)


def main():
    sys.argv = [sys.argv[0], DC + "/data", "--user-dir", "./unimol", "--valid-subset", "test",
                "--num-workers", "8", "--ddp-backend", "c10d", "--batch-size", "8",
                "--task", "drugclip", "--loss", "in_batch_softmax", "--arch", "drugclip",
                "--max-pocket-atoms", "256", "--fp16", "--fp16-init-scale", "4",
                "--fp16-scale-window", "256", "--seed", "1", "--path", CKPT,
                "--log-interval", "500", "--log-format", "simple"]
    parser = options.get_validation_parser()
    options.add_model_args(parser)
    args = options.parse_args_and_arch(parser)

    state = checkpoint_utils.load_checkpoint_to_cpu(args.path)
    task = tasks.setup_task(args)
    model = task.build_model(args)
    model.load_state_dict(state["model"], strict=False)
    model.half()
    model.cuda()
    model.eval()

    poc_reps, poc_names = encode_pockets(model, task, POCKETS)
    q_reps, q_names = encode_mols(model, task, QUERY, "ligands")
    S_query = poc_reps @ q_reps.T  # [3, 7]

    # background: official mols.lmdb, subsample for speed
    ds = task.load_retrieval_mols_dataset(MOLS, "atoms", "coordinates")
    n_bg = len(ds)
    step = max(1, n_bg // 100000)
    idx = list(range(0, n_bg, step))[:100000]
    sub = torch.utils.data.Subset(ds, idx)
    dl = torch.utils.data.DataLoader(sub, batch_size=BATCH, collate_fn=ds.collater)
    bg_reps = []
    for sample in tqdm(dl):
        sample = unicore.utils.move_to_cuda(sample)
        dist = sample["net_input"]["mol_src_distance"]
        et = sample["net_input"]["mol_src_edge_type"]
        st = sample["net_input"]["mol_src_tokens"]
        pm = st.eq(model.mol_model.padding_idx)
        x = model.mol_model.embed_tokens(st)
        n = dist.size(-1)
        gbf = model.mol_model.gbf_proj(model.mol_model.gbf(dist, et))
        attn = gbf.permute(0, 3, 1, 2).contiguous().view(-1, n, n)
        out = model.mol_model.encoder(x, padding_mask=pm, attn_mask=attn)
        emb = model.mol_project(out[0][:, 0, :])
        emb = emb / emb.norm(dim=-1, keepdim=True)
        bg_reps.append(emb.detach().cpu().float().numpy())
    bg = np.concatenate(bg_reps)  # [100k, d]

    S_bg = poc_reps @ bg.T  # [3, 100k]
    out = {"pocket_names": poc_names, "query_names": q_names,
           "S_query": S_query.tolist(),
           "bg_mean": S_bg.mean(axis=1).tolist(), "bg_std": S_bg.std(axis=1).tolist(),
           "bg_percentiles": {p: np.percentile(S_bg, p, axis=1).tolist() for p in (50, 90, 95, 99)}}
    with open(os.path.join(EMB, "normalised_scores.pkl"), "wb") as f:
        pickle.dump(out, f)

    print("\n== per-pocket normalised ranking (z-score of cosine vs 100k background) ==")
    for j, mn in enumerate(q_names):
        vals = []
        for i, pn in enumerate(poc_names):
            z = (S_query[i, j] - out["bg_mean"][i]) / out["bg_std"][i]
            pct = (S_bg[i] < S_query[i, j]).mean() * 100
            vals.append((pn, round(float(z), 2), round(float(pct), 1)))
        vals.sort(key=lambda x: -x[1])
        print(f"{mn:18s} " + "  >  ".join(f"{n}(z={z}, pct{p})" for n, z, p in vals))


if __name__ == "__main__":
    main()
