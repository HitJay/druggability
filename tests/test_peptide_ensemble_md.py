"""
tests/test_peptide_ensemble_md.py — Tests for GPU-accelerated Peptide Ensemble MM/GBSA module.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from druggability.peptide.ensemble_md import (
    DEFAULT_OPENMM_PYTHON,
    EnsembleMDResult,
    run_ensemble_mmgbsa,
)

SAMPLE_COMPLEX_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "OXTR_OXT_Gly_complex.pdb"
)


def test_ensemble_md_result_dataclass():
    res = EnsembleMDResult(
        ok=True,
        complex_name="test_complex",
        receptor_chain="A",
        peptide_chain="B",
        length_ns=1.0,
        n_snapshots=5,
        mean_delta_g=-25.4,
        std_delta_g=2.1,
        min_delta_g=-28.0,
        max_delta_g=-22.0,
        delta_g_trajectory=[-25.0, -26.0, -24.0, -27.0, -25.0],
        mean_pep_rmsd=1.2,
        final_pep_rmsd=1.4,
        is_stable_binder=True,
        ns_per_day=150.0,
    )
    assert res.ok is True
    assert res.mean_delta_g == -25.4
    assert res.is_stable_binder is True
    md = res.summary_markdown()
    assert "### Short-MD Ensemble MM/GBSA" in md
    assert "-25.40" in md
    assert "Stable Binder" in md

    df = res.to_df()
    assert len(df) == 5
    assert "delta_g_kcal_mol" in df.columns


@pytest.mark.skipif(
    not (DEFAULT_OPENMM_PYTHON.exists() and SAMPLE_COMPLEX_PDB.exists()),
    reason="OpenMM python or sample complex PDB missing",
)
def test_run_ensemble_mmgbsa_fast_smoke(tmp_path: Path):
    # Fast smoke test: 0.02 ns (10000 steps) on GPU 0
    res = run_ensemble_mmgbsa(
        complex_pdb=SAMPLE_COMPLEX_PDB,
        length_ns=0.02,
        n_snapshots=3,
        gpu_id=0,
        out_dir=tmp_path / "smoke_run",
        timeout=300,
    )
    assert res.ok is True, f"Ensemble MD run failed: {res.error}"
    assert res.n_snapshots == 3
    assert len(res.delta_g_trajectory) == 3
    assert Path(res.production_dcd).exists()
    assert Path(res.solvated_pdb).exists()
    assert Path(res.result_json).exists()
    assert res.mean_pep_rmsd >= 0.0

    # P2 assertions: per-residue decomposition & dynamic hbonds
    assert len(res.per_residue_decomposition) > 0
    assert len(res.hbond_persistence) > 0
    top_anchor = res.per_residue_decomposition[0]
    assert hasattr(top_anchor, "res_label")
    assert hasattr(top_anchor, "mean_energy_kcal_mol")
