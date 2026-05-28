"""
bbbkit.druggability.batch — 批量评估测试
"""

from __future__ import annotations

import pytest

from bbbkit.druggability.batch import (
    BatchResult,
    assess_druggability_batch,
    _assess_single,
)


class TestBatchResult:
    """BatchResult 数据类测试"""

    def test_default_values(self):
        r = BatchResult(query="EGFR")
        assert r.query == "EGFR"
        assert r.success is False
        assert r.error is None
        assert r.overall_score == 0.0
        assert r.confidence == "none"
        assert r.tractability_score is None
        assert r.ligandability_score is None
        assert r.ligandability_n_ligands == 0

    def test_to_dict(self):
        r = BatchResult(
            query="BRAF",
            success=True,
            overall_score=0.75,
            confidence="medium",
            tractability_score=0.8,
            ligandability_score=0.7,
            ligandability_n_ligands=42,
            elapsed_seconds=3.2,
        )
        d = r.to_dict()
        assert d["query"] == "BRAF"
        assert d["success"] is True
        assert d["overall_score"] == 0.75
        assert d["confidence"] == "medium"
        assert d["tractability_score"] == 0.8
        assert d["elapsed_seconds"] == 3.2
        assert d["ligandability_n_ligands"] == 42
        assert d["error"] is None

    def test_to_dict_error(self):
        r = BatchResult(query="FAKE", error="Not found", success=False)
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"] == "Not found"

    def test_set_success(self):
        r = BatchResult(query="KRAS")
        r.success = True
        r.overall_score = 0.5
        r.confidence = "low"
        r.tractability_score = 0.4
        r.ligandability_score = 0.3
        assert r.success is True
        assert r.tractability_score == 0.4


class TestBatchAssessSingle:
    """_assess_single — 需要网络"""

    @pytest.mark.network
    def test_invalid_query_returns_error(self):
        r = _assess_single("__NONEXISTENT_TARGET_XYZ__")
        assert r.success is False
        assert r.error is not None
        assert r.overall_score == 0.0
        assert r.confidence == "none"

    @pytest.mark.network
    def test_elapsed_time_recorded(self):
        r = _assess_single("__NONEXISTENT_GENE__")
        assert r.elapsed_seconds > 0


class TestAssessDruggabilityBatch:
    """assess_druggability_batch 核心功能测试"""

    def test_empty_list_returns_empty(self):
        results = assess_druggability_batch([], show_progress=False)
        assert results == []

    @pytest.mark.network
    def test_single_target(self):
        results = assess_druggability_batch(["EGFR"], show_progress=False)
        assert len(results) == 1
        assert results[0].query == "EGFR"

    @pytest.mark.network
    def test_multiple_targets_order_preserved(self):
        targets = ["EGFR", "BRAF", "KRAS"]
        results = assess_druggability_batch(targets, show_progress=False)
        assert len(results) == len(targets)
        for i, r in enumerate(results):
            assert r.query == targets[i]

    @pytest.mark.network
    def test_partial_failure_continues(self):
        targets = ["EGFR", "__NONEXISTENT_1__", "BRAF", "__NONEXISTENT_2__"]
        results = assess_druggability_batch(targets, show_progress=False)
        assert len(results) == len(targets)

        succeeded = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(succeeded) >= 2
        assert len(failed) >= 2
        for r in failed:
            assert r.error is not None

    @pytest.mark.network
    def test_progress_callback(self):
        calls = []

        def cb(done, total):
            calls.append((done, total))

        targets = ["EGFR", "BRAF"]
        assess_druggability_batch(targets, show_progress=False, on_progress=cb)
        assert len(calls) == len(targets)
        for i, (done, total) in enumerate(calls):
            assert done == i + 1
            assert total == len(targets)

    @pytest.mark.network
    def test_tractability_score_extracted(self):
        results = assess_druggability_batch(["EGFR"], show_progress=False)
        r = results[0]
        if r.success:
            assert r.tractability_score is not None
            assert r.tractability_score > 0

    @pytest.mark.network
    def test_confidence_mapped(self):
        results = assess_druggability_batch(["EGFR"], show_progress=False)
        r = results[0]
        if r.success:
            assert r.confidence in ("high", "medium", "low", "none")

    @pytest.mark.network
    def test_output_to_dict_list(self):
        results = assess_druggability_batch(["EGFR"], show_progress=False)
        dicts = [r.to_dict() for r in results]
        assert len(dicts) == 1
        d = dicts[0]
        assert "query" in d
        assert "success" in d
        assert "overall_score" in d
        assert "elapsed_seconds" in d


@pytest.mark.network
class TestBatchNetwork:
    """真实网络环境下的批量评估"""

    @pytest.mark.timeout(120)
    def test_batch_known_targets(self):
        targets = ["EGFR", "BRAF", "TP53"]
        results = assess_druggability_batch(targets, show_progress=True)
        assert len(results) == len(targets)
        for r in results:
            assert r.success, f"{r.query} failed: {r.error}"
            assert r.overall_score > 0, f"{r.query} got zero score"

    @pytest.mark.timeout(120)
    def test_batch_mixed_success_failure(self):
        targets = ["EGFR", "THIS_DOES_NOT_EXIST_12345", "BRAF"]
        results = assess_druggability_batch(targets, show_progress=True)
        assert len(results) == 3
        succeeded = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(succeeded) >= 2
        assert len(failed) >= 1
        for r in failed:
            assert r.error is not None