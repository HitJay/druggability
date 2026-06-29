import json
from pathlib import Path


def test_infer_target_biology():
    from bbbkit.druggability.biolib_apps import infer_target_biology

    assert infer_target_biology("T2D") == "T2D"
    assert infer_target_biology("WHRadjBMI") == "Obesity"
    assert infer_target_biology("BFPCT") == "Obesity"
    assert infer_target_biology("unknown") == "Obesity"


def test_write_gene_list(tmp_path: Path):
    from bbbkit.druggability.biolib_apps import write_gene_list

    path = write_gene_list([" ADORA1 ", "", "SSTR5"], tmp_path / "genes.txt")

    assert path.read_text(encoding="utf-8") == "ADORA1\nSSTR5\n"


def test_target_portal_manifest_summary_sanitizes_token(tmp_path: Path):
    from bbbkit.druggability.biolib_apps import _target_portal_manifest_summary

    manifest = tmp_path / "build" / "manifest.json"
    manifest.parent.mkdir()
    manifest.write_text(
        json.dumps(
            {
                "params": {"gene_symbol": "ADORA1", "job_auth_token": "secret"},
                "sections": [{"key": "GENETICS", "title": "Genetics"}],
            }
        ),
        encoding="utf-8",
    )

    summary = _target_portal_manifest_summary(tmp_path)

    assert summary["target_portal_params"] == {"gene_symbol": "ADORA1"}
    assert summary["target_portal_sections"] == [{"key": "GENETICS", "title": "Genetics"}]