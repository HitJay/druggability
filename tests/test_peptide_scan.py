"""
tests/test_peptide_scan.py — Tests for peptide mutational scanning module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from druggability.peptide.scan import (
    AlaScanResult,
    PositionScanResult,
    run_alanine_scanning,
    scan_position_mutations,
)

SAMPLE_COMPLEX_PDB = (
    Path(__file__).resolve().parent.parent
    / "OXTR_assessment"
    / "structures"
    / "7QVM_active_complex.pdb"
)


def test_run_alanine_scanning():
    assert SAMPLE_COMPLEX_PDB.exists()
    res = run_alanine_scanning(SAMPLE_COMPLEX_PDB)

    assert res.ok is True
    assert res.receptor_chain == "R"
    assert res.peptide_chain == "L"
    assert len(res.entries) >= 9

    # Find Tyr2 entry
    tyr2_entry = next((e for e in res.entries if e.res_seq == 2), None)
    assert tyr2_entry is not None
    assert tyr2_entry.orig_res == "TYR"
    assert tyr2_entry.ddg > 0.8  # Strong hotspot loss
    assert tyr2_entry.lost_contacts >= 5

    # Find Leu8 entry (tolerant vector)
    leu8_entry = next((e for e in res.entries if e.res_seq == 8), None)
    assert leu8_entry is not None
    assert leu8_entry.orig_res == "LEU"
    assert leu8_entry.is_tolerant_exit_vector is True

    # Test Markdown output
    md = res.summary_markdown()
    assert "### In Silico Alanine Scanning Profile" in md
    assert "TYR" in md


def test_scan_position_mutations_pro7():
    assert SAMPLE_COMPLEX_PDB.exists()
    res = scan_position_mutations(SAMPLE_COMPLEX_PDB, res_seq=7)

    assert res.ok is True
    assert res.orig_res == "PRO"
    assert len(res.candidates) == 20

    # Gly mutation should be present and tolerant
    gly_cand = next((c for c in res.candidates if c.mutant_res == "GLY"), None)
    assert gly_cand is not None
    assert gly_cand.pred_delta_g < -8.0  # Still good binding
    assert "loop adaptation" in gly_cand.note

    # Clashing bulky aromatics
    trp_cand = next((c for c in res.candidates if c.mutant_res == "TRP"), None)
    assert trp_cand is not None
    assert "Clashing" in trp_cand.compatibility

    # Check Markdown
    md = res.summary_markdown()
    assert "### Position Mutational Scanning" in md
    assert "PRO7" in md


def test_scan_position_mutations_invalid_pos():
    res = scan_position_mutations(SAMPLE_COMPLEX_PDB, res_seq=999)
    assert res.ok is False
    assert "not found" in res.error
