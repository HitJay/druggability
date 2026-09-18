"""
tests/test_peptide_affinity.py — Tests for peptide-protein binding affinity module.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from druggability.peptide.affinity import (
    PeptideAffinityResult,
    format_kd,
    load_pdb_atoms,
    predict_peptide_affinity,
)

SAMPLE_COMPLEX_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "7QVM_active_complex.pdb"
)
SAMPLE_V2R_COMPLEX_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "7DW9_v2r_avp_complex.pdb"
)


def test_format_kd():
    assert format_kd(1e-12) == "1.00 pM"
    assert format_kd(1.5e-9) == "1.50 nM"
    assert format_kd(2.4e-6) == "2.40 µM"
    assert format_kd(3.1e-3) == "3.10 mM"
    assert format_kd(0.0) == "> 1 mM"
    assert format_kd(-1.0) == "> 1 mM"


def test_load_pdb_atoms():
    assert SAMPLE_COMPLEX_PDB.exists()
    atoms = load_pdb_atoms(SAMPLE_COMPLEX_PDB)
    assert len(atoms) > 1000
    # No hydrogens
    for a in atoms:
        assert not a.atom_name.startswith("H")
        assert a.element != "H"


def test_predict_peptide_affinity_oxtr():
    assert SAMPLE_COMPLEX_PDB.exists()
    res = predict_peptide_affinity(SAMPLE_COMPLEX_PDB)
    assert res.ok is True
    assert res.receptor_chain == "R"
    assert res.peptide_chain == "L"
    assert res.total_contacts > 40
    assert res.delta_g < -5.0  # Favorable binding
    assert res.kd_molar < 1e-6  # Sub-micromolar
    assert len(res.peptide_hotspots) > 0

    # Top hotspot should be Tyr2
    top = res.top_hotspots(1)[0]
    assert "TYR" in top.res_name

    # Check Markdown output
    md = res.summary_markdown()
    assert "### Peptide-Protein Binding Affinity Profile" in md
    assert "TYR2" in md


def test_predict_peptide_affinity_v2r():
    assert SAMPLE_V2R_COMPLEX_PDB.exists()
    res = predict_peptide_affinity(SAMPLE_V2R_COMPLEX_PDB)
    assert res.ok is True
    assert res.receptor_chain == "R"
    assert res.peptide_chain == "C"
    # AVP has Arg8 forming salt bridge with V2R
    assert res.salt_bridge_count_est >= 1
    assert res.delta_g < -10.0


def test_predict_peptide_affinity_missing_file():
    res = predict_peptide_affinity("non_existent_file.pdb")
    assert res.ok is False
    assert "File not found" in res.error
