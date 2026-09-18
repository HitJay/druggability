"""
tests/test_peptide_pipeline.py — Tests for End-to-End Peptide Assessment Pipeline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from druggability.peptide.pipeline import (
    CandidateAssessmentReport,
    assess_peptide_candidate,
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


def test_assess_peptide_candidate_e2e(tmp_path: Path):
    assert SAMPLE_TARGET_PDB.exists() and SAMPLE_COUNTER_PDB.exists()

    report = assess_peptide_candidate(
        complex_pdb=SAMPLE_TARGET_PDB,
        peptide_name="OXT_Gly",
        target_name="OXTR",
        counter_complexes={"V2R": SAMPLE_COUNTER_PDB},
        run_alanine_scan=True,
        scan_positions=[7, 8],
        run_ensemble_md=False,  # Skip MD for quick unit test
        out_dir=tmp_path / "pipeline_run",
        html_report=True,
    )

    assert report.ok is True
    assert report.peptide_name == "OXT_Gly"
    assert report.target_name == "OXTR"
    assert report.affinity.ok is True
    assert report.affinity.delta_g < -8.0

    # Alanine scan verification
    assert report.ala_scan is not None
    assert report.ala_scan.ok is True
    assert len(report.ala_scan.entries) >= 9

    # Positional scans verification
    assert 7 in report.position_scans
    assert 8 in report.position_scans
    assert report.position_scans[7].ok is True
    assert report.position_scans[8].ok is True

    # Selectivity audit verification
    assert "V2R" in report.selectivity_audits
    assert report.selectivity_audits["V2R"].ok is True

    # HTML verification
    assert Path(report.html_report_path).exists()
    assert Path(report.html_report_path).stat().st_size > 1000

    # Markdown verification
    md = report.summary_markdown()
    assert "# End-to-End Peptide Druggability Assessment" in md
    assert "OXT_Gly" in md
    assert "OXTR" in md
    assert "Actionable Chemistry & Engineering Recommendations" in md


def test_assess_peptide_candidate_missing_complex():
    report = assess_peptide_candidate("non_existent_complex.pdb")
    assert report.ok is False
    assert "not found" in report.error
