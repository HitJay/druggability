"""
tests/test_druggability_namespace.py — Tests for the top-level druggability package namespace.
"""

from __future__ import annotations

import subprocess
import sys


def test_import_druggability_top_level():
    import druggability

    assert hasattr(druggability, "assess_druggability")
    assert hasattr(druggability, "assess_druggability_batch")
    assert hasattr(druggability, "query_tractability")
    assert hasattr(druggability, "assess_ligandability")
    assert hasattr(druggability, "detect_pockets")
    assert hasattr(druggability, "screen_drugclip")
    assert hasattr(druggability, "DEFAULT_WEIGHTS")


def test_import_druggability_submodules():
    from druggability import peptide, report, search
    from druggability.peptide import descriptors, tasks

    assert peptide is not None
    assert search is not None
    assert report is not None
    assert hasattr(descriptors, "parse_modification")
    assert hasattr(tasks, "REGISTRY")


def test_cli_entrypoints():
    res = subprocess.run(
        [sys.executable, "-m", "druggability.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "druggability" in res.stdout or "bbbkit" in res.stdout
