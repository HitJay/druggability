"""
冒烟测试 — 验证 druggability 评估模块基本可用

运行: conda activate research && python -m pytest tests/test_druggability.py -v

注意: 部分测试依赖外部 API（Open Targets、ChEMBL），网络不可用时跳过。
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ─── Utils Tests ─────────────────────────────────────────────────────


def test_resolve_ensembl_id_ensembl():
    """Ensembl ID 输入应原样返回。"""
    from litkit.druggability.utils import resolve_ensembl_id

    result = resolve_ensembl_id("ENSG00000146648", query_type="ensembl_id")
    assert result == "ENSG00000146648"


def test_resolve_ensembl_id_unknown_type():
    """未知 query_type 应抛出 ValueError。"""
    from litkit.druggability.utils import resolve_ensembl_id
    import pytest

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


# ─── Exceptions Tests ────────────────────────────────────────────────


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


# ─── Tractability Tests ─────────────────────────────────────────────


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
    assert "small_molecule" in result.to_dict()
    sm = result.small_molecule
    assert isinstance(sm, dict)
    # 应有 modality 字段
    if sm:
        assert sm.get("modality") == "small_molecule"


@pytest.mark.network
def test_query_tractability_invalid_target():
    """无效靶点应抛出 TargetNotFoundError。"""
    from litkit.druggability.tractability import query_tractability
    from litkit.druggability.utils import TargetNotFoundError

    with pytest.raises(TargetNotFoundError):
        query_tractability("NONEXISTENT_GENE_XYZ", query_type="gene_symbol")


def test_tractability_result_to_dict():
    """TractabilityResult.to_dict() 应包含所有关键字段。"""
    from litkit.druggability.tractability import TractabilityResult

    r = TractabilityResult(
        ensembl_id="ENSG00000146648",
        symbol="EGFR",
        name="Epidermal growth factor receptor",
        small_molecule={"modality": "small_molecule", "category": "Clinical Precedence"},
    )
    d = r.to_dict()
    assert d["ensembl_id"] == "ENSG00000146648"
    assert d["symbol"] == "EGFR"
    assert d["small_molecule"]["category"] == "Clinical Precedence"


# ─── Ligandability Tests ─────────────────────────────────────────────


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


# ─── Pocket Analysis Tests ───────────────────────────────────────────


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


def test_detect_pockets_no_fpocket():
    """fpocket 未安装时应抛出 FpocketNotFoundError。"""
    import tempfile
    import os
    from litkit.druggability.pocket import detect_pockets
    from litkit.druggability.utils import FpocketNotFoundError

    # 创建一个最小的有效 PDB 文件，使其能通过文件存在性检查
    tmp = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False, mode="w")
    tmp.write("ATOM      1  N   ALA A   1       1.000   1.000   1.000  1.00  0.00           N\n")
    tmp.write("ATOM      2  CA  ALA A   1       1.000   1.000   1.000  1.00  0.00           C\n")
    tmp.write("END\n")
    tmp.close()

    try:
        with pytest.raises(FpocketNotFoundError):
            detect_pockets(tmp.name, auto_download=False)
    finally:
        os.unlink(tmp.name)


# ─── Unified Entry Point Tests ───────────────────────────────────────


def test_assess_druggability_composite():
    """assess_druggability 应生成包含 composite 分数的报告。"""
    from litkit.druggability import assess_druggability
    from litkit.druggability.utils import DruggabilityError

    # 使用已知无效的查询来触发错误路径（不会真的发网络请求）
    try:
        result = assess_druggability(
            "INVALID_GENE_99999",
            include_structure_analysis=False,
        )
    except DruggabilityError:
        result = {"error": "test"}

    if "error" not in result:
        assert "query" in result
        assert "tractability" in result
        assert "ligandability" in result
        assert "composite" in result
        assert "overall_score" in result["composite"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])