"""
tests/test_druggability_cli_peptide.py — Tests for peptide CLI subcommands.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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


def test_cli_peptide_affinity():
    res = subprocess.run(
        [sys.executable, "-m", "druggability.cli", "peptide", "affinity", "--complex", str(SAMPLE_TARGET_PDB)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Peptide-Protein Binding Affinity Profile" in res.stdout
    assert "TYR2" in res.stdout


def test_cli_peptide_scan():
    res = subprocess.run(
        [sys.executable, "-m", "druggability.cli", "peptide", "scan", "--complex", str(SAMPLE_TARGET_PDB), "--mode", "ala"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "In Silico Alanine Scanning Profile" in res.stdout
    assert "LEU" in res.stdout


def test_cli_peptide_lipidation():
    res = subprocess.run(
        [sys.executable, "-m", "druggability.cli", "peptide", "lipidation", "--complex", str(SAMPLE_TARGET_PDB), "--pos", "8"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Lipidation & Protraction 3D Clearance Audit" in res.stdout
    assert "LEU8" in res.stdout


def test_cli_peptide_selectivity():
    res = subprocess.run(
        [
            sys.executable, "-m", "druggability.cli", "peptide", "selectivity",
            "--target-complex", str(SAMPLE_TARGET_PDB),
            "--counter-complex", str(SAMPLE_COUNTER_PDB),
            "--target-name", "OXTR",
            "--counter-name", "V2R",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Subtype Selectivity Audit" in res.stdout
    assert "OXTR" in res.stdout
    assert "V2R" in res.stdout
