"""
tests/test_drugclip.py — Tests for DrugCLIP virtual screening agent tool.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from bbbkit.druggability.drugclip import (
    DEFAULT_CHECKPOINT,
    DEFAULT_DRUGCLIP_PYTHON,
    DrugCLIPHit,
    DrugCLIPResult,
    extract_pocket_from_pdb,
    parse_pdb_atoms,
    screen_drugclip,
    write_pocket_lmdb,
)

SAMPLE_REC_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "7QVM_active_receptor.pdb"
)
SAMPLE_LIG_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "7QVM_oxt_ligand.pdb"
)
TEST_MOLS_LMDB = Path("/tmp/test_mols.lmdb")


def test_parse_pdb_atoms():
    assert SAMPLE_REC_PDB.exists(), f"Sample PDB not found: {SAMPLE_REC_PDB}"
    atoms, coords, residues = parse_pdb_atoms(SAMPLE_REC_PDB)
    assert len(atoms) > 1000
    assert len(coords) == len(atoms)
    assert len(residues) == len(atoms)
    assert isinstance(coords[0][0], float)
    assert "CA" in atoms


def test_extract_pocket_from_pdb_with_ligand():
    assert SAMPLE_REC_PDB.exists() and SAMPLE_LIG_PDB.exists()
    pocket_data = extract_pocket_from_pdb(
        SAMPLE_REC_PDB,
        ligand_pdb=SAMPLE_LIG_PDB,
        radius=8.0,
        pocket_name="OXTR_pocket",
    )
    assert pocket_data["pocket"] == "OXTR_pocket"
    assert len(pocket_data["pocket_atoms"]) > 100
    assert len(pocket_data["pocket_coordinates"]) == len(pocket_data["pocket_atoms"])


def test_extract_pocket_from_pdb_with_center():
    # Centroid of ligand approximate: (0, 0, 0) or arbitrary probe
    pocket_data = extract_pocket_from_pdb(
        SAMPLE_REC_PDB,
        center=(100.0, 100.0, 100.0),
        radius=5.0,
        pocket_name="center_probe",
    )
    assert pocket_data["pocket"] == "center_probe"
    assert "pocket_atoms" in pocket_data
    assert "pocket_coordinates" in pocket_data


def test_write_pocket_lmdb(tmp_path: Path):
    pocket_data = {
        "pocket": "test_pocket",
        "pocket_atoms": ["CA", "CB", "N"],
        "pocket_coordinates": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
    }
    lmdb_path = tmp_path / "pocket.lmdb"
    out = write_pocket_lmdb(pocket_data, lmdb_path)
    assert out.exists()
    assert out.stat().st_size > 0


def test_drugclip_result_dataclass():
    hit1 = DrugCLIPHit(rank=1, smi="CC1=CC=CC=C1", score=0.85)
    hit2 = DrugCLIPHit(rank=2, smi="CCN(CC)CC", score=0.42)
    res = DrugCLIPResult(
        ok=True,
        pocket_name="test_target",
        hits=[hit1, hit2],
        top_k=2,
        elapsed_seconds=1.23,
    )
    assert res.hit_count == 2
    assert len(res.top(1)) == 1
    assert res.top(1)[0].rank == 1
    md = res.summary_markdown()
    assert "### DrugCLIP Virtual Screening Summary" in md
    assert "0.8500" in md


@pytest.mark.skipif(
    not (
        DEFAULT_DRUGCLIP_PYTHON.exists()
        and DEFAULT_CHECKPOINT.exists()
        and TEST_MOLS_LMDB.exists()
    ),
    reason="DrugCLIP venv or test checkpoint/database missing",
)
def test_screen_drugclip_end_to_end(tmp_path: Path):
    result = screen_drugclip(
        pocket_input=SAMPLE_REC_PDB,
        ligand_pdb=SAMPLE_LIG_PDB,
        mol_lmdb=TEST_MOLS_LMDB,
        top_k=3,
        device_id=0,
        output_dir=tmp_path / "screen_run",
    )
    assert result.ok is True, f"Screen failed: {result.error}"
    assert result.hit_count == 3
    assert result.hits[0].rank == 1
    assert result.hits[0].score >= result.hits[1].score
    assert Path(result.result_json).exists()
    assert Path(result.result_tsv).exists()
