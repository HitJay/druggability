"""
Druggability 评估模块测试

运行: conda activate research && python -m pytest tests/test_druggability.py -v

注意: 标记为 @pytest.mark.network 的测试依赖外部 API，默认跳过。
      手动执行: python -m pytest tests/test_druggability.py -v -m network
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ═══════════════════════════════════════════════════════════════════════
# Utils Tests
# ═══════════════════════════════════════════════════════════════════════


def test_resolve_ensembl_id_ensembl():
    """Ensembl ID 输入应原样返回。"""
    from litkit.druggability.utils import resolve_ensembl_id

    result = resolve_ensembl_id("ENSG00000146648", query_type="ensembl_id")
    assert result == "ENSG00000146648"


def test_resolve_ensembl_id_unknown_type():
    """未知 query_type 应抛出 ValueError。"""
    from litkit.druggability.utils import resolve_ensembl_id

    with pytest.raises(ValueError, match="Unknown query_type"):
        resolve_ensembl_id("EGFR", query_type="invalid")


def test_simple_cache():
    """SimpleCache 的 get/set 应正确工作。"""
    from litkit.druggability.utils import SimpleCache

    cache = SimpleCache(ttl=60, maxsize=10)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    assert cache.get("nonexistent") is None


def test_simple_cache_expiry():
    """SimpleCache 应过期。"""
    from litkit.druggability.utils import SimpleCache
    import time

    cache = SimpleCache(ttl=0.1, maxsize=10)
    cache.set("key", "val")
    time.sleep(0.15)
    assert cache.get("key") is None


def test_rate_limit_decorator():
    """rate_limit 装饰器应在调用间引入延迟。"""
    from litkit.druggability.utils import rate_limit
    import time

    call_count = 0

    @rate_limit(delay=0.1)
    def dummy():
        nonlocal call_count
        call_count += 1
        return call_count

    t0 = time.time()
    dummy()
    dummy()
    elapsed = time.time() - t0
    assert elapsed >= 0.1  # 至少有一次延迟


# ═══════════════════════════════════════════════════════════════════════
# Exceptions Tests
# ═══════════════════════════════════════════════════════════════════════


def test_druggability_error_hierarchy():
    """异常继承关系应正确。"""
    from litkit.druggability.utils import (
        DruggabilityError,
        TargetNotFoundError,
        NetworkError,
        FpocketNotFoundError,
    )

    assert issubclass(TargetNotFoundError, DruggabilityError)
    assert issubclass(NetworkError, DruggabilityError)
    assert issubclass(FpocketNotFoundError, DruggabilityError)


# ═══════════════════════════════════════════════════════════════════════
# Tractability Tests (P0 fix)
# ═══════════════════════════════════════════════════════════════════════


def test_label_to_score():
    """label_to_score 应正确映射已知和未知 label。"""
    from litkit.druggability.tractability import label_to_score

    assert label_to_score("Approved Drug") == 1.0
    assert label_to_score("Advanced Clinical") == 0.9
    assert label_to_score("Phase 1 Clinical") == 0.8
    assert label_to_score("High-Quality Pocket") == 0.6
    assert label_to_score("Druggable Family") == 0.4
    # 未知 label 应返回默认分
    assert label_to_score("SomeUnknownLabel") == 0.2


def test_modality_tractability_to_dict():
    """ModalityTractability.to_dict() 应包含所有字段。"""
    from litkit.druggability.tractability import ModalityTractability

    mt = ModalityTractability(
        modality="small_molecule",
        labels=["Approved Drug", "High-Quality Pocket"],
        top_label="Approved Drug",
        score=1.0,
    )
    d = mt.to_dict()
    assert d["modality"] == "small_molecule"
    assert len(d["labels"]) == 2
    assert d["top_label"] == "Approved Drug"
    assert d["score"] == 1.0


def test_tractability_result_to_dict():
    """TractabilityResult.to_dict() 应含所有 modality 和 best_score。"""
    from litkit.druggability.tractability import TractabilityResult, ModalityTractability

    r = TractabilityResult(
        ensembl_id="ENSG00000146648",
        symbol="EGFR",
        name="Epidermal growth factor receptor",
        small_molecule=ModalityTractability(
            modality="small_molecule",
            labels=["Approved Drug", "Structure with Ligand"],
            top_label="Approved Drug",
            score=1.0,
        ),
        antibody=ModalityTractability(
            modality="antibody",
            labels=["UniProt loc"],
            top_label="UniProt loc",
            score=0.5,
        ),
    )
    d = r.to_dict()
    assert d["ensembl_id"] == "ENSG00000146648"
    assert d["symbol"] == "EGFR"
    assert d["small_molecule"]["score"] == 1.0
    assert d["small_molecule"]["top_label"] == "Approved Drug"
    assert d["antibody"]["score"] == 0.5
    assert d["best_score"] == 1.0  # max(SM=1.0, AB=0.5, PROTAC=0.0)


def test_tractability_result_best_score_empty():
    """无任何 label 时 best_score 应为 0。"""
    from litkit.druggability.tractability import TractabilityResult

    r = TractabilityResult(symbol="UNKNOWN")
    assert r.best_score == 0.0


@pytest.mark.network
def test_query_tractability_egfr():
    """EGFR 的 tractability 查询应返回 small molecule 信息。"""
    from litkit.druggability.tractability import query_tractability

    try:
        result = query_tractability("EGFR", query_type="gene_symbol")
    except Exception as e:
        pytest.skip(f"Network-dependent test skipped: {e}")

    assert result.ensembl_id.startswith("ENSG")
    assert result.symbol == "EGFR"
    # SM modality 应有 labels
    d = result.to_dict()
    assert d["small_molecule"]["score"] > 0
    assert len(d["small_molecule"]["labels"]) > 0
    assert d["best_score"] > 0


@pytest.mark.network
def test_query_tractability_invalid_target():
    """无效靶点应抛出 TargetNotFoundError。"""
    from litkit.druggability.tractability import query_tractability
    from litkit.druggability.utils import TargetNotFoundError

    with pytest.raises(TargetNotFoundError):
        query_tractability("NONEXISTENT_GENE_XYZ", query_type="gene_symbol")


# ═══════════════════════════════════════════════════════════════════════
# Ligandability Tests
# ═══════════════════════════════════════════════════════════════════════


def test_score_from_ligand_count():
    """ligandability 分数映射应正确。"""
    from litkit.druggability.ligandability import _score_from_ligand_count

    assert _score_from_ligand_count(2000) == 1.0
    assert _score_from_ligand_count(500) == 0.8
    assert _score_from_ligand_count(75) == 0.6
    assert _score_from_ligand_count(25) == 0.4
    assert _score_from_ligand_count(5) == 0.2
    assert _score_from_ligand_count(0) == 0.0


@pytest.mark.network
def test_assess_ligandability_egfr():
    """EGFR 的 ligandability 评估应返回正数分数。"""
    from litkit.druggability.ligandability import assess_ligandability

    try:
        result = assess_ligandability("EGFR")
    except Exception as e:
        pytest.skip(f"Network-dependent test skipped: {e}")

    assert result.target_chembl_id.startswith("CHEMBL")
    assert result.n_known_ligands > 0
    assert result.ligandability_score > 0
    assert len(result.top_compounds) > 0


def test_ligandability_result_to_dict():
    """LigandabilityResult.to_dict() 应包含关键字段。"""
    from litkit.druggability.ligandability import LigandabilityResult

    r = LigandabilityResult(
        target_chembl_id="CHEMBL2034",
        pref_name="EGFR",
        n_known_ligands=100,
        ligandability_score=0.8,
    )
    d = r.to_dict()
    assert d["target_chembl_id"] == "CHEMBL2034"
    assert d["n_known_ligands"] == 100
    assert d["ligandability_score"] == 0.8


# ═══════════════════════════════════════════════════════════════════════
# Pocket Analysis Tests
# ═══════════════════════════════════════════════════════════════════════


def test_grade_druggability():
    """druggability 分级逻辑应正确。"""
    from litkit.druggability.pocket import _grade_druggability

    assert _grade_druggability(0.9) == "Highly druggable"
    assert _grade_druggability(0.6) == "Druggable"
    assert _grade_druggability(0.4) == "Marginal"
    assert _grade_druggability(0.1) == "Poor"


def test_pocket_info_to_dict():
    """PocketInfo.to_dict() 应包含所有字段。"""
    from litkit.druggability.pocket import PocketInfo

    p = PocketInfo(
        rank=1,
        score=0.5,
        druggability_score=0.78,
        num_alpha_spheres=42,
        volume=850.0,
        druggability_grade="Highly druggable",
    )
    d = p.to_dict()
    assert d["rank"] == 1
    assert d["druggability_score"] == 0.78
    assert d["volume"] == 850.0


def test_pocket_analysis_result_to_dict():
    """PocketAnalysisResult.to_dict() 应包含汇总统计。"""
    from litkit.druggability.pocket import PocketAnalysisResult, PocketInfo

    p = PocketInfo(rank=1, druggability_score=0.78, volume=850.0)
    r = PocketAnalysisResult(
        num_pockets=3,
        total_volume=1800.0,
        best_druggability_score=0.78,
        deepest_pocket_volume=850.0,
        pockets=[p],
        input_structure="test.pdb",
    )
    d = r.to_dict()
    assert d["num_pockets"] == 3
    assert d["best_druggability_score"] == 0.78
    assert len(d["pockets"]) == 1


def test_detect_pockets_no_fpocket(monkeypatch):
    """fpocket 本地二进制和 Docker 都不可用时应抛出 FpocketNotFoundError。"""
    import tempfile
    import os
    from unittest.mock import MagicMock

    from litkit.druggability.pocket import detect_pockets
    from litkit.druggability.utils import FpocketNotFoundError

    # Mock _check_fpocket 强制返回不可用
    def fake_check():
        raise FpocketNotFoundError("fpocket not found")

    tmp = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False, mode="w")
    tmp.write("ATOM      1  N   ALA A   1       1.000   1.000   1.000  1.00  0.00           N\n")
    tmp.write("ATOM      2  CA  ALA A   1       1.000   1.000   1.000  1.00  0.00           C\n")
    tmp.write("END\n")
    tmp.close()

    try:
        from litkit.druggability import pocket
        monkeypatch.setattr(pocket, "_check_fpocket", fake_check)
        with pytest.raises(FpocketNotFoundError):
            detect_pockets(tmp.name, auto_download=False)
    finally:
        os.unlink(tmp.name)


# ═══════════════════════════════════════════════════════════════════════
# Composite Score Tests (P0 fix — 核心修复测试)
# ═══════════════════════════════════════════════════════════════════════


class TestCompositeScore:
    """_compute_composite 综合评分逻辑测试。"""

    def test_empty_result(self):
        """所有维度都失败时应返回 0 分和 'none' 置信度。"""
        from litkit.druggability import _compute_composite

        result = {
            "tractability": {"error": "failed"},
            "ligandability": {"error": "failed"},
        }
        composite = _compute_composite(result)
        assert composite["overall_score"] == 0.0
        assert composite["confidence"] == "none"
        assert composite["dimensions_available"] == 0
        assert composite["contributing_scores"] == {}

    def test_tractability_only(self):
        """仅 tractability 成功时应有 low 置信度。"""
        from litkit.druggability import _compute_composite

        result = {
            "tractability": {
                "best_score": 0.9,
                "small_molecule": {"score": 0.9},
                "antibody": {"score": 0.0},
                "protac": {"score": 0.0},
            },
            "ligandability": {"error": "failed"},
        }
        composite = _compute_composite(result)
        assert composite["overall_score"] == 0.9
        assert composite["confidence"] == "low"
        assert composite["dimensions_available"] == 1
        assert "tractability" in composite["contributing_scores"]
        assert composite["contributing_scores"]["tractability"] == 0.9

    def test_two_dimensions(self):
        """两个维度成功时应有 medium 置信度。"""
        from litkit.druggability import _compute_composite

        result = {
            "tractability": {
                "best_score": 1.0,
                "small_molecule": {"score": 1.0},
                "antibody": {"score": 0.5},
                "protac": {"score": 0.0},
            },
            "ligandability": {
                "ligandability_score": 0.8,
            },
        }
        composite = _compute_composite(result)
        assert composite["confidence"] == "medium"
        assert composite["dimensions_available"] == 2
        assert "tractability" in composite["contributing_scores"]
        assert "ligandability" in composite["contributing_scores"]
        # 加权平均: (1.0*0.35 + 0.8*0.35) / (0.35+0.35) = 0.9
        assert abs(composite["overall_score"] - 0.9) < 0.01

    def test_three_dimensions(self):
        """三个维度成功时应有 high 置信度。"""
        from litkit.druggability import _compute_composite

        result = {
            "tractability": {
                "best_score": 1.0,
                "small_molecule": {"score": 1.0},
                "antibody": {"score": 0.0},
                "protac": {"score": 0.0},
            },
            "ligandability": {
                "ligandability_score": 0.8,
            },
            "pocket_analysis": {
                "best_druggability_score": 0.6,
            },
        }
        composite = _compute_composite(result)
        assert composite["confidence"] == "high"
        assert composite["dimensions_available"] == 3
        # 加权: (1.0*0.35 + 0.8*0.35 + 0.6*0.30) / (0.35+0.35+0.30)
        expected = (1.0 * 0.35 + 0.8 * 0.35 + 0.6 * 0.30) / 1.0
        assert abs(composite["overall_score"] - expected) < 0.01

    def test_no_pocket_analysis_key(self):
        """未包含 pocket_analysis key 时不应报错。"""
        from litkit.druggability import _compute_composite

        result = {
            "tractability": {"best_score": 0.5},
            "ligandability": {"ligandability_score": 0.4},
        }
        composite = _compute_composite(result)
        assert composite["dimensions_available"] == 2
        assert "structure" not in composite["contributing_scores"]

    def test_zero_scores_excluded(self):
        """分数为 0 的维度不应参与加权。"""
        from litkit.druggability import _compute_composite

        result = {
            "tractability": {
                "best_score": 0.0,  # 0 分不计入
                "small_molecule": {"score": 0.0},
                "antibody": {"score": 0.0},
                "protac": {"score": 0.0},
            },
            "ligandability": {
                "ligandability_score": 0.6,
            },
        }
        composite = _compute_composite(result)
        assert composite["dimensions_available"] == 1
        assert "tractability" not in composite["contributing_scores"]
        assert composite["contributing_scores"]["ligandability"] == 0.6


# ═══════════════════════════════════════════════════════════════════════
# assess_druggability Entry Point Tests (P0 fix)
# ═══════════════════════════════════════════════════════════════════════


def test_assess_druggability_default_no_structure():
    """默认不应跑结构分析（include_structure_analysis=False）。"""
    from litkit.druggability import assess_druggability

    # 使用无效靶点——不会真正查到，但不应触发结构分析
    result = assess_druggability(
        "INVALID_GENE_99999",
    )
    # 不应包含 pocket_analysis key（因为默认不跑结构）
    assert "pocket_analysis" not in result
    assert "composite" in result
    assert "overall_score" in result["composite"]


def test_assess_druggability_composite_present():
    """assess_druggability 应总是生成 composite。"""
    from litkit.druggability import assess_druggability

    result = assess_druggability(
        "INVALID_GENE_99999",
        include_structure_analysis=False,
    )
    assert "query" in result
    assert "tractability" in result
    assert "ligandability" in result
    assert "composite" in result
    comp = result["composite"]
    assert "overall_score" in comp
    assert "confidence" in comp
    assert "dimensions_available" in comp
    assert "contributing_scores" in comp


def test_resolve_structure_input_uniprot():
    """UniProt ID 类型应直接返回。"""
    from litkit.druggability import _resolve_structure_input

    assert _resolve_structure_input("P00533", "uniprot_id") == "P00533"


def test_resolve_structure_input_ensembl_raises():
    """Ensembl ID 目前不支持自动结构下载，应 raise。"""
    from litkit.druggability import _resolve_structure_input

    with pytest.raises(ValueError, match="not yet supported"):
        _resolve_structure_input("ENSG00000146648", "ensembl_id")


def test_resolve_structure_input_unknown_type_raises():
    """未知 query_type 应 raise ValueError。"""
    from litkit.druggability import _resolve_structure_input

    with pytest.raises(ValueError, match="Unknown query_type"):
        _resolve_structure_input("EGFR", "invalid_type")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
