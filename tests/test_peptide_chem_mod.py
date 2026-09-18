"""
tests/test_peptide_chem_mod.py — Tests for peptide chemical modifications and lipidation audit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from druggability.peptide.chem_mod import (
    LipidationAuditResult,
    NcAAScanResult,
    audit_peptide_lipidation,
    get_ncaa_info,
)

SAMPLE_COMPLEX_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "OXTR_OXT_Gly_complex.pdb"
)


def test_audit_peptide_lipidation_exit_vector_pos8():
    assert SAMPLE_COMPLEX_PDB.exists()
    res = audit_peptide_lipidation(
        SAMPLE_COMPLEX_PDB,
        res_seq=8,
        protraction_type="C18_diacid_gammaGlu",
        target_name="OXTR",
    )
    assert res.ok is True
    assert res.res_seq == 8
    assert res.orig_res == "LEU"
    assert "Unobstructed Exit Vector" in res.clearance_status
    assert "Low" in res.potency_loss_risk
    assert res.receptor_atoms_in_cone <= 5

    md = res.summary_markdown()
    assert "### Lipidation & Protraction 3D Clearance Audit" in md
    assert "LEU8" in md
    assert "Octadecanedioic acid" in md


def test_audit_peptide_lipidation_clashing_pos2():
    assert SAMPLE_COMPLEX_PDB.exists()
    res = audit_peptide_lipidation(
        SAMPLE_COMPLEX_PDB,
        res_seq=2,
        protraction_type="C18_diacid_gammaGlu",
        target_name="OXTR",
    )
    assert res.ok is True
    assert res.res_seq == 2
    assert res.orig_res == "TYR"
    assert "Severely Obstructed" in res.clearance_status
    assert "High / Disruptive" in res.potency_loss_risk
    assert res.receptor_atoms_in_cone > 20


def test_get_ncaa_info():
    aib = get_ncaa_info("AIB")
    assert aib is not None
    assert aib.canonical_analog == "ALA"
    assert "DPP-4" in aib.biological_role

    nle = get_ncaa_info("Nle")
    assert nle is not None
    assert nle.canonical_analog == "LEU"

    unknown = get_ncaa_info("UNKNOWN_XYZ")
    assert unknown is None
