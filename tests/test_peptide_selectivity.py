"""
tests/test_peptide_selectivity.py — Tests for peptide subtype selectivity audit module.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from druggability.peptide.selectivity import (
    SelectivityAuditResult,
    audit_peptide_selectivity,
)

SAMPLE_TARGET_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "OXTR_OXT_Gly_complex.pdb"
)
SAMPLE_COUNTER_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "V2R_OXT_Gly_complex.pdb"
)


def test_audit_peptide_selectivity_end_to_end(tmp_path: Path):
    assert SAMPLE_TARGET_PDB.exists() and SAMPLE_COUNTER_PDB.exists()

    html_file = tmp_path / "selectivity_report.html"
    res = audit_peptide_selectivity(
        target_complex_pdb=SAMPLE_TARGET_PDB,
        counter_complex_pdb=SAMPLE_COUNTER_PDB,
        target_name="OXTR",
        counter_name="V2R",
        peptide_name="OXT_Gly",
        html_out=html_file,
    )

    assert res.ok is True
    assert res.target_name == "OXTR"
    assert res.counter_name == "V2R"
    assert res.target_affinity.ok is True
    assert res.counter_affinity.ok is True
    assert len(res.residue_comparisons) >= 9
    assert len(res.geometric_clash_warnings) > 0

    # Verify HTML deliverable was created
    assert html_file.exists()
    assert html_file.stat().st_size > 1000
    html_text = html_file.read_text(encoding="utf-8")
    assert "OXTR" in html_text
    assert "V2R" in html_text
    assert "3Dmol" in html_text

    # Verify Markdown summary
    md = res.summary_markdown()
    assert "### Subtype Selectivity Audit" in md
    assert "OXTR" in md
    assert "V2R" in md


def test_audit_peptide_selectivity_missing_file():
    res = audit_peptide_selectivity(
        target_complex_pdb="missing_target.pdb",
        counter_complex_pdb=SAMPLE_COUNTER_PDB,
    )
    assert res.ok is False
    assert "not found" in res.error
