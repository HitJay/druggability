"""Fetch the complete 4RYI TSPO construct sequence from RCSB (at runtime, per sequence rule).

Fixes the truncated 40-aa sequence in output/boltz/tspo_pka.yaml (fetch_seq stopped at the
FLAG-tag). Writes the corrected YAML files for the local Boltz-2 runs and validates the
affinity-ckpt integrity in the background.
"""
import json
import subprocess
import threading

BASE = "/das/user/QYJI/druggability/TSPO_assessment"

# 1) runtime fetch — never hand-transcribe
r = subprocess.run(
    ["curl", "-sS", "--max-time", "60",
     "https://data.rcsb.org/rest/v1/core/polymer_entity/4RYI/1"],
    capture_output=True, text=True, timeout=90)
d = json.loads(r.stdout)
seq = d["entity_poly"]["pdbx_seq_one_letter_code_can"]
len_desc = d["entity_poly"].get("pdbx_strand_id", "")
desc = d.get("rcsb_polymer_entity", {}).get("pdbx_description", "")
print(f"fetched: len={len(seq)} entity={desc} strands={len_desc}")

# 2) rewrite both YAMLs with the full construct + affinity block
LIG = "CCC(C)N(C)C(=O)c1cc2cccc(-c3ccccc3Cl)c2cn1"  # PK11195 (ChEMBL481537)
for name in ("tspo_pka", "car_pka"):
    yml = f"{BASE}/output/boltz/{name}.yaml"
    open(yml, "w").write(
        "version: 1\nsequences:\n"
        "  - protein:\n      id: A\n      sequence: " + seq + "\n"
        "  - ligand:\n      id: L\n      smiles: '" + LIG + "'\n"
        "properties:\n  - affinity:\n      binder: L\n")
    print(f"rewrote {yml}")

# 3) integrity-check the affinity checkpoint in the background (slow, ~2 GB load)
def ck():
    try:
        import torch
        sd = torch.load("/home/QYJI/das/models/boltzgen/boltz2_aff.ckpt",
                        map_location="cpu", weights_only=False)
        n = sum(1 for _ in sd["state_dict"].keys()) if isinstance(sd, dict) and "state_dict" in sd else -1
        open(f"{BASE}/output/boltz/ckpt_check.log", "w").write(f"OK state_dict keys={n}\n")
    except Exception as e:
        open(f"{BASE}/output/boltz/ckpt_check.log", "w").write(f"FAIL {type(e).__name__}: {e}\n")

threading.Thread(target=ck, daemon=True).start()
print("ckpt check started in background")
