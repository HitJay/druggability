"""Tests for druggability.marjorie HPC & NNEDH biodata helpers."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from druggability import cli, marjorie


def test_estimate_cost_gpu_spot():
    est = marjorie.estimate_cost("gpu-spot", hours=2.0)
    assert est.instance_type == "g6.2xlarge"
    assert est.spot is True
    assert est.gpu_hours == 2.0
    assert est.cpu_hours == 8.0
    assert est.estimated_usd_upper == pytest.approx(1.9552, rel=1e-4)
    assert 0 < est.pct_of_monthly_budget < 1.0


def test_estimate_cost_g6e_multi_gpu():
    est = marjorie.estimate_cost("g6e", hours=1.5, nodes=1, instance_type="g6e.24xlarge")
    assert est.gpus_per_node == 4
    assert est.gpu_hours == 6.0
    assert est.estimated_usd_upper == pytest.approx(15.06559 * 1.5, rel=1e-4)


def test_estimate_cost_invalid_inputs():
    with pytest.raises(ValueError, match="hours"):
        marjorie.estimate_cost("gpu-spot", hours=0)
    with pytest.raises(ValueError, match="Unknown partition"):
        marjorie.estimate_cost("nonexistent", hours=1.0)
    with pytest.raises(ValueError, match="Unknown instance_type"):
        marjorie.estimate_cost("gpu-spot", hours=1.0, instance_type="bad.type")


def test_render_sbatch_with_modules():
    script = marjorie.render_sbatch(
        job_name="md_test",
        command=".venv/bin/python run_md.py",
        partition="gpu-spot",
        hours=1.5,
        modules=["openmm", "duckdb"],
    )
    assert "#SBATCH --job-name=md_test" in script
    assert "#SBATCH --partition=gpu-spot" in script
    assert "#SBATCH --gres=gpu:l4:1" in script
    assert "#SBATCH --time=01:30:00" in script
    assert "module load openmm/8.1.1-spk duckdb/1.3.0-spk" in script
    assert "MARJORIE_SCRATCH_DIR" in script
    assert ".venv/bin/python run_md.py" in script


def test_list_biodata(tmp_path):
    (tmp_path / "chembl_latest").mkdir()
    (tmp_path / "drugbank_latest").mkdir()
    (tmp_path / "readme.txt").write_text("ignore")

    all_ds = marjorie.list_biodata(root=str(tmp_path))
    assert all_ds == ["chembl_latest", "drugbank_latest"]
    assert marjorie.list_biodata(root=str(tmp_path), pattern="chem") == ["chembl_latest"]


def test_query_chembl_compounds_mocked(tmp_path):
    part0 = tmp_path / "chembl_latest" / "Subsets" / "ChemblCompound" / "part-0"
    part0.mkdir(parents=True)
    fake_rows = [{"compound_chembl_id": "CHEMBL25", "max_phase": 4, "full_mwt": 180.16}]

    with (
        patch("shutil.which", return_value="/usr/bin/duckdb"),
        patch(
            "subprocess.run",
            return_value=SimpleNamespace(stdout=json.dumps(fake_rows), returncode=0),
        ) as mock_run,
    ):
        rows = marjorie.query_chembl_compounds(
            where="max_phase = 4", limit=5, root=str(tmp_path)
        )

    assert rows == fake_rows
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == "/usr/bin/duckdb"
    assert "-json" in called_cmd
    assert "LIMIT 5;" in called_cmd[-1]


def test_query_chembl_guards(tmp_path):
    with pytest.raises(ValueError, match="semicolon|contain ';'"):
        marjorie.query_chembl_compounds(where="1=1; DROP TABLE x", root=str(tmp_path))
    with pytest.raises(ValueError, match="limit"):
        marjorie.query_chembl_compounds(limit=99999, root=str(tmp_path))


def test_cli_marjorie_estimate(capsys):
    parser = cli._setup_parser()
    args = parser.parse_args(["marjorie", "estimate", "--partition", "gpu-spot", "--hours", "2", "--json"])
    cli._cmd_marjorie(args)
    out = json.loads(capsys.readouterr().out)
    assert out["partition"] == "gpu-spot"
    assert out["gpu_hours"] == 2.0
