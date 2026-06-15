"""
bbbkit.peptide 模块测试（非网络）

运行: python -m pytest tests/test_peptide.py -v
说明: 这些测试只覆盖纯函数 / 注册表 / 导入安全性，不触发网络或 GPU。
      带 @pytest.mark.network 的端到端 benchmark 默认跳过。
"""

import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ═══════════════════════════════════════════════════════════════════════
# 任务注册表
# ═══════════════════════════════════════════════════════════════════════

def test_registry_keys_unique_and_present():
    from bbbkit.peptide import get_tasks

    tasks = get_tasks()
    keys = [t.key for t in tasks]
    assert len(keys) == len(set(keys)), "任务键应唯一"
    for expected in ("bbb", "acp_main", "acp_alternate", "toxicity", "amp", "hemolytic"):
        assert expected in keys


def test_registry_filter_by_keys():
    from bbbkit.peptide import get_tasks

    subset = get_tasks(["bbb", "amp"])
    assert [t.key for t in subset] == ["bbb", "amp"]


def test_every_task_has_provenance():
    from bbbkit.peptide import get_tasks

    for t in get_tasks():
        assert t.source and isinstance(t.source, str)
        assert isinstance(t.official_split, bool)
        assert isinstance(t.sota, dict)


def test_top_level_export():
    import bbbkit

    # peptide_tasks 应被暴露（即便可选依赖缺失，tasks 子模块也能导入）
    assert hasattr(bbbkit, "peptide_available")
    assert bbbkit.peptide_tasks is not None
    assert len(bbbkit.peptide_tasks()) >= 6


# ═══════════════════════════════════════════════════════════════════════
# 权重路径配置（config）
# ═══════════════════════════════════════════════════════════════════════

def test_config_defaults_and_known_models():
    from bbbkit.peptide import config

    assert config.DEFAULT_MODEL == "esm2_t30_150M_UR50D"
    assert config.DEFAULT_MODEL in config.KNOWN_MODELS
    assert config.KNOWN_MODELS["esm2_t30_150M_UR50D"] == 640


def test_config_model_dir_env_override(monkeypatch, tmp_path):
    from bbbkit.peptide import config

    monkeypatch.setenv("BBBKIT_MODEL_DIR", str(tmp_path / "weights"))
    assert config.model_dir() == tmp_path / "weights"


def test_config_resolve_ckpt_priority(monkeypatch, tmp_path):
    from bbbkit.peptide import config

    # 无任何来源时返回 None
    monkeypatch.delenv("ESM2_CKPT", raising=False)
    monkeypatch.setenv("BBBKIT_MODEL_DIR", str(tmp_path / "empty"))
    assert config.resolve_ckpt() is None

    # 显式参数（存在的文件）优先
    explicit = tmp_path / "explicit.pt"
    explicit.write_bytes(b"x")
    assert config.resolve_ckpt(explicit) == str(explicit)

    # 其次 ESM2_CKPT 环境变量
    env_ckpt = tmp_path / "from_env.pt"
    env_ckpt.write_bytes(b"x")
    monkeypatch.setenv("ESM2_CKPT", str(env_ckpt))
    assert config.resolve_ckpt() == str(env_ckpt)


def test_config_ensure_ckpt_no_download_raises(monkeypatch, tmp_path):
    from bbbkit.peptide import config

    monkeypatch.delenv("ESM2_CKPT", raising=False)
    monkeypatch.setenv("BBBKIT_MODEL_DIR", str(tmp_path / "none"))
    with pytest.raises(FileNotFoundError):
        config.ensure_ckpt(auto_download=False)


# ═══════════════════════════════════════════════════════════════════════
# 数据集解析（纯函数）
# ═══════════════════════════════════════════════════════════════════════

def test_clean_seq_filters_nonstandard_and_length():
    from bbbkit.peptide import datasets as D

    assert D.clean_seq("ACDEFG") == "ACDEFG"
    assert D.clean_seq("acdefg") == "ACDEFG"      # 大写化
    assert D.clean_seq("ACDB") is None             # B 非标准 + 太短
    assert D.clean_seq("A" * 60) is None           # 超长
    assert D.clean_seq("AC") is None               # 太短
    assert D.clean_seq("ACDXFG") is None           # X 非标准氨基酸


def test_parse_lines_and_fasta():
    from bbbkit.peptide import datasets as D

    lines = "ACDEFG\nKLMNPQ\n\nbadseq1\nRSTVWY\n"
    parsed = D._parse_lines(lines)
    assert "ACDEFG" in parsed and "KLMNPQ" in parsed and "RSTVWY" in parsed
    assert all(set(s) <= D.AA for s in parsed)

    fasta = ">p1\nACDEFG\n>p2\nKLMNPQ\nRSTVWY\n"
    pf = D._parse_fasta(fasta)
    assert "ACDEFG" in pf
    assert "KLMNPQRSTVWY" in pf  # 多行序列拼接


def test_dedup_preserves_order():
    from bbbkit.peptide import datasets as D

    assert D._dedup(["A", "B", "A", "C", "B"]) == ["A", "B", "C"]


def test_split_no_leak_removes_train_overlap():
    from bbbkit.peptide import datasets as D

    pte, nte = D._split_no_leak(["A", "B"], ["C"], ["A", "X"], ["C", "Y"])
    assert "A" not in pte and "X" in pte
    assert "C" not in nte and "Y" in nte


def test_write_and_load_split(tmp_path):
    from bbbkit.peptide import datasets as D

    D._write_csv(tmp_path / "demo" / "train.csv", ["ACDEFG", "KLMNPQ"], ["RSTVWY"])
    D._write_csv(tmp_path / "demo" / "test.csv", ["WYACDE"], ["FGHIKL"])
    (tr_seqs, ytr), (te_seqs, yte) = D.load_split(tmp_path, "demo")
    assert tr_seqs == ["ACDEFG", "KLMNPQ", "RSTVWY"]
    assert ytr == [1, 1, 0]
    assert te_seqs == ["WYACDE", "FGHIKL"]
    assert yte == [1, 0]


# ═══════════════════════════════════════════════════════════════════════
# 任务头（需要 scikit-learn）
# ═══════════════════════════════════════════════════════════════════════

def test_head_grid_keys():
    from bbbkit.peptide import heads

    assert set(heads._GRID) == {"linear", "mlp"}
    assert all(isinstance(g, list) and g for g in heads._GRID.values())


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("sklearn") is None,
    reason="scikit-learn 未安装（可选依赖）")
def test_head_fit_eval_on_synthetic():
    import numpy as np
    from bbbkit.peptide import heads

    rng = np.random.default_rng(0)
    # 两个可分的高斯簇
    Xtr = np.vstack([rng.normal(0, 1, (40, 8)), rng.normal(3, 1, (40, 8))])
    ytr = [0] * 40 + [1] * 40
    Xte = np.vstack([rng.normal(0, 1, (10, 8)), rng.normal(3, 1, (10, 8))])
    yte = [0] * 10 + [1] * 10
    _, m = heads.fit_eval(Xtr, ytr, Xte, yte, kind="linear")
    assert m["AUC"] > 0.9 and 0.0 <= m["ACC"] <= 1.0
    assert set(m) == {"ACC", "AUC", "MCC", "Sens", "Spec"}


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("sklearn") is None,
    reason="scikit-learn 未安装（可选依赖）")
def test_select_hparams_returns_grid_member():
    import numpy as np
    from bbbkit.peptide import heads

    rng = np.random.default_rng(1)
    X = np.vstack([rng.normal(0, 1, (30, 6)), rng.normal(2.5, 1, (30, 6))])
    y = [0] * 30 + [1] * 30
    params, auc = heads.select_hparams(X, y, "linear")
    assert params in heads._GRID["linear"]
    assert 0.0 <= auc <= 1.0
