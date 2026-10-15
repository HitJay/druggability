"""Unit tests for WS2b DrugCLIP reverse-mode helper logic (no GPU needed)."""
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest

PROJ = Path("/das/user/QYJI/druggability")
sys.path.insert(0, str(PROJ / "TSPO_assessment" / "scripts"))

import ws2b_drugclip_reverse as rev  # noqa: E402


def test_write_all_pockets_roundtrip(tmp_path):
    pockets = [
        {"pocket": "p1", "pocket_atoms": ["N", "CA"], "pocket_coordinates": [[0.0, 0, 0], [1, 0, 0]]},
        {"pocket": "p2", "pocket_atoms": ["C"], "pocket_coordinates": [[2.0, 1, 0]]},
    ]
    out = rev.write_all_pockets(pockets, tmp_path / "p.lmdb")
    assert out.exists()
    import lmdb
    env = lmdb.open(str(out), subdir=False, readonly=True, lock=False)
    with env.begin() as txn:
        assert txn.stat()["entries"] == 2
        d0 = pickle.loads(txn.get(b"0"))
    env.close()
    assert d0["pocket"] == "p1"
    assert len(d0["pocket_atoms"]) == 2


def test_write_mol_lmdb_shape(tmp_path):
    entries = [("ligA", ["N", "C", "O"], [[0.0, 0, 0], [1.0, 0, 0], [0, 1.0, 0]])]
    out = rev.write_mol_lmdb(entries, tmp_path / "m.lmdb")
    import lmdb
    env = lmdb.open(str(out), subdir=False, readonly=True, lock=False)
    with env.begin() as txn:
        d0 = pickle.loads(txn.get(b"0"))
    env.close()
    assert d0["smi"] == "ligA"
    arr = np.asarray(d0["coordinates"])
    assert arr.ndim == 3          # [n_conformer=1, n_atoms, 3]
    assert arr.shape == (1, 3, 3)
    assert arr.dtype == np.float32


def test_ranking_transpose_logic():
    """The reverse ranking is a column-wise argsort of S[pocket, mol]."""
    S = np.array([[0.9, 0.1], [0.2, 0.8]])  # 2 pockets x 2 mols
    mols, pocks = ["molA", "molB"], ["pock1", "pock2"]
    result = {}
    for j, mn in enumerate(mols):
        order = np.argsort(-S[:, j])
        result[mn] = [(pocks[i], round(float(S[i, j]), 4)) for i in order]
    assert result["molA"][0][0] == "pock1"
    assert result["molB"][0][0] == "pock2"
    # decoy-vs-ligand gate check shape: values are (name, score) tuples
    assert isinstance(result["molA"][1][1], float)


def test_vina_gate_scores_file():
    f = PROJ / "TSPO_assessment/output/docking/validation_gate_results.json"
    if not f.exists():
        pytest.skip("docking results not present")
    r = json.loads(f.read_text())
    tspo = r["4RYI"]["vina_scores"][0]
    car = r["1XVP_D" if "1XVP_D" in r else "1XVP"]["vina_scores"][0]
    assert tspo < -8.0, "TSPO positive control must dock strongly"
    assert car < -8.0, "CAR recovery must dock strongly"


import json  # noqa: E402
