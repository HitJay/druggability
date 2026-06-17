"""
bbbkit.peptide.report 模块测试（非网络 / 非 LLM / 非 GPU）

运行: python -m pytest tests/test_report.py -v
说明: 固化"组合拳"的确定性逻辑——适用域标记、置信度、数字校验、模板拼装、
      产物无中文。所有 LLM 调用以 client=None 走优雅降级，不触发网络。
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bbbkit.peptide import report as R  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════
# 适用域标记（applicability_domain）
# ═══════════════════════════════════════════════════════════════════════

def test_domain_in_domain_short_peptide():
    dom, reason = R.applicability_domain(12, "", None)
    assert dom == "in-domain"
    assert "12" in reason


def test_domain_edge_at_training_max():
    dom, _ = R.applicability_domain(30, "", None)
    assert dom == "edge-extrapolation"


def test_domain_out_of_domain_length():
    dom, reason = R.applicability_domain(42, "", None)
    assert dom == "out-of-domain-length"
    assert "extrapolat" in reason.lower()


def test_domain_modification_takes_priority():
    # 即便长度域内，脂化修饰也应判为 OOD-modification
    dom, reason = R.applicability_domain(18, "C18 fatty-acid + PEG", 2200)
    assert dom == "out-of-domain-modification"
    assert "ESM-2" in reason


@pytest.mark.parametrize("mod", ["lipidation", "PEGylated", "cyclic", "D-Ala", "C18 diacid"])
def test_domain_modification_patterns(mod):
    dom, _ = R.applicability_domain(15, mod, None)
    assert dom == "out-of-domain-modification"


@pytest.mark.parametrize("mod", [
    "small molecule", "small-molecule", "non-peptide", "non peptide",
    "small molecule (non-peptide)", "SMILES input",
])
def test_domain_small_molecule_is_valid_not_ood(mod):
    # 非肽 / 小分子 → 有效的 small-molecule 类别（B3clf 专用工具），不是 OOD
    dom, reason = R.applicability_domain(None, mod, 405.0)
    assert dom == "small-molecule"
    assert "B3clf" in reason
    assert not dom.startswith("out-of-domain")


def test_domain_method_b3clf():
    # 显式 method=b3clf → small-molecule，即便没有 modification 关键词
    dom, reason = R.applicability_domain(None, "", 405.0, method="b3clf")
    assert dom == "small-molecule"
    assert "benchmark" in reason.lower()


def test_record_small_molecule_confidence_benchmarked():
    rec = R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf"})
    assert rec.domain == "small-molecule"
    assert rec.confidence == "benchmarked"


def test_domain_unsupported_modality_is_ood():
    # 抗体/寡核苷酸等无专用工具的模态 → 真正 OOD-modality
    dom, _ = R.applicability_domain(None, "antibody", 150000.0)
    assert dom == "out-of-domain-modality"


def test_assemble_small_molecule_uses_b3clf_label():
    rec = R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf"})
    fields = {"reading": "moderate B3clf BBB classification",
              "domain": "predicted by the benchmarked small-molecule tool",
              "caveat": "confirm with brain PK", "literature": ""}
    out = R._assemble_peptide_narrative(fields, rec)
    assert "B3clf" in out
    assert "41.1%" in out
    assert "ESM-2" not in out


def test_domain_native_label_not_flagged():
    # "native" / "none" 不应触发修饰判定
    dom, _ = R.applicability_domain(12, "native", None)
    assert dom == "in-domain"


def test_domain_reason_is_english_only():
    # 产物面向英文报告：reason 不得含中文
    for args in [(12, "", None), (30, "", None), (42, "", None),
                 (18, "C18 PEG", 2200), (12, "", 1600)]:
        _, reason = R.applicability_domain(*args)
        assert not re.search(r"[\u4e00-\u9fff]", reason), f"中文残留: {reason}"


# ═══════════════════════════════════════════════════════════════════════
# 置信度（confidence_from_ci）+ CI 解析
# ═══════════════════════════════════════════════════════════════════════

def test_confidence_levels_by_width():
    assert R.confidence_from_ci(80, 100)[0] == "high"      # width 20
    assert R.confidence_from_ci(40, 85)[0] == "medium"     # width 45
    assert R.confidence_from_ci(5, 99)[0] == "low"         # width 94
    assert R.confidence_from_ci(None, None)[0] == "unknown"


def test_parse_ci_from_string():
    assert R._parse_ci("[5.7, 99.8]") == (5.7, 99.8)
    assert R._parse_ci([10.0, 20.0]) == (10.0, 20.0)
    assert R._parse_ci(None) == (None, None)
    assert R._parse_ci("garbage") == (None, None)


# ═══════════════════════════════════════════════════════════════════════
# 记录规范化（PeptideRecord.from_dict）
# ═══════════════════════════════════════════════════════════════════════

def test_record_from_dict_infers_length_and_call():
    rec = R.PeptideRecord.from_dict({"name": "BRP", "sequence": "THRILRRLFNLC",
                                     "p_bbb": 87.5, "ci": "[21.2, 99.8]"})
    assert rec.length == 12
    assert rec.call == "BBB+"          # 推断自 p_bbb >= 50
    assert rec.domain == "in-domain"
    assert rec.ci_low == 21.2 and rec.ci_high == 99.8


def test_record_from_dict_esm_column_aliases():
    rec = R.PeptideRecord.from_dict({"name": "x", "sequence": "ACDEFGHIK",
                                     "ESM2_P(BBB+)%": 12.3, "ESM2_boot_90CI": "[1.0, 40.0]"})
    assert rec.p_bbb == 12.3
    assert rec.call == "BBB-"
    assert rec.ci_low == 1.0


def test_record_none_score_ood_modification():
    rec = R.PeptideRecord.from_dict({"name": "NN9161", "length": 18, "mw": 2200,
                                     "p_bbb": None, "modification": "C18 + PEG"})
    assert rec.p_bbb is None
    assert rec.domain == "out-of-domain-modification"


# ═══════════════════════════════════════════════════════════════════════
# 确定性校验（_validate_peptide_fields）—— 组合拳手段三
# ═══════════════════════════════════════════════════════════════════════

def _rec_in():
    return R.PeptideRecord.from_dict({"name": "a", "sequence": "ACDEFGHIK",
                                      "p_bbb": 80.0, "ci": "[60, 95]"})


def _rec_ood():
    return R.PeptideRecord.from_dict({"name": "b", "length": 18, "mw": 2200,
                                      "p_bbb": None, "modification": "C18 + PEG"})


def test_validate_accepts_good_fields():
    fields = {"reading": "high intrinsic propensity from backbone",
              "domain": "in-domain and trustworthy",
              "caveat": "propensity not exposure", "literature": ""}
    ok, _ = R._validate_peptide_fields(fields, _rec_in())
    assert ok


def test_validate_rejects_numeric_hallucination():
    # prose 含百分数 → 拒绝（数字必须归代码）
    fields = {"reading": "propensity is 88% high", "domain": "in-domain",
              "caveat": "propensity not exposure"}
    ok, reason = R._validate_peptide_fields(fields, _rec_in())
    assert not ok and "numeric" in reason


def test_validate_rejects_ci_in_prose():
    fields = {"reading": "propensity in range [60, 95]", "domain": "in-domain",
              "caveat": "propensity not exposure"}
    ok, _ = R._validate_peptide_fields(fields, _rec_in())
    assert not ok


def test_validate_requires_propensity_keyword():
    fields = {"reading": "high score", "domain": "trustworthy",
              "caveat": "score not exposure"}
    ok, reason = R._validate_peptide_fields(fields, _rec_in())
    assert not ok and "propensity" in reason


def test_validate_ood_requires_upper_bound_note():
    # OOD 条目必须点明 upper bound / out-of-domain / backbone
    weak = {"reading": "propensity looks fine", "domain": "trustworthy result",
            "caveat": "propensity not exposure"}
    ok, _ = R._validate_peptide_fields(weak, _rec_ood())
    assert not ok
    strong = {"reading": "backbone propensity only", "domain": "out-of-domain upper bound",
              "caveat": "propensity not exposure"}
    ok, _ = R._validate_peptide_fields(strong, _rec_ood())
    assert ok


def test_validate_rejects_missing_field():
    fields = {"reading": "propensity high", "domain": "in-domain"}  # 缺 caveat
    ok, reason = R._validate_peptide_fields(fields, _rec_in())
    assert not ok and "caveat" in reason


# ═══════════════════════════════════════════════════════════════════════
# 模板拼装（_assemble_peptide_narrative）—— 数字归代码
# ═══════════════════════════════════════════════════════════════════════

def test_assemble_injects_code_owned_numbers():
    rec = _rec_in()
    fields = {"reading": "propensity backbone", "domain": "in-domain",
              "caveat": "propensity not exposure", "literature": "known route X"}
    out = R._assemble_peptide_narrative(fields, rec)
    assert out.startswith("[MODEL]")
    assert "80.0%" in out                 # 代码注入的分数
    assert "[60.0, 95.0]" in out          # 代码注入的 CI
    assert "[CAVEAT]" in out
    assert "[LITERATURE] known route X" in out


def test_assemble_handles_unscored_ood():
    rec = _rec_ood()
    fields = {"reading": "backbone upper bound", "domain": "out-of-domain",
              "caveat": "propensity not exposure", "literature": ""}
    out = R._assemble_peptide_narrative(fields, rec)
    assert "not scored by the sequence model" in out
    assert "out-of-domain-modification" in out


# ═══════════════════════════════════════════════════════════════════════
# 优雅降级：client=None 时走确定性模板
# ═══════════════════════════════════════════════════════════════════════

def test_narrative_falls_back_without_client():
    rec = _rec_in()
    out = R.generate_peptide_narrative(None, rec)
    assert out.startswith("[MODEL]")
    assert "propensity" in out.lower()
    assert not re.search(r"[\u4e00-\u9fff]", out)   # 英文模板


def test_exec_summary_falls_back_without_client():
    recs = [_rec_in(), _rec_ood()]
    out = R.generate_exec_summary(None, recs)
    assert "peptide" in out.lower()
    assert not re.search(r"[\u4e00-\u9fff]", out)


# ═══════════════════════════════════════════════════════════════════════
# 自适应阅读注释（按模态 + 不确定性能力声明）
# ═══════════════════════════════════════════════════════════════════════

def test_adaptive_reading_note_peptide_only_mentions_bootstrap_ci():
    recs = [
        R.PeptideRecord.from_dict(
            {"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"}
        )
    ]
    note = R._adaptive_reading_note(recs).lower()
    assert "bootstrap 90% ci" in note
    assert "no calibrated per-compound confidence interval" not in note


def test_adaptive_reading_note_small_molecule_mentions_uncertainty_gap():
    recs = [R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf"})]
    note = R._adaptive_reading_note(recs).lower()
    assert "benchmark-level" in note
    assert "no calibrated per-compound confidence interval" in note


def test_adaptive_reading_note_mixed_mentions_both_branches():
    recs = [
        R.PeptideRecord.from_dict({"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"}),
        R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf"}),
    ]
    note = R._adaptive_reading_note(recs).lower()
    assert "mixed batch" in note
    assert "bootstrap 90% ci" in note
    assert "no calibrated per-compound ci yet" in note


def test_display_len_ci_for_small_molecule_are_explicit_not_dash():
    rec = R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf"})
    assert R._display_len(rec) == "SM"
    assert R._display_ci(rec) == "N/A (benchmarked)"


def test_display_len_ci_for_peptide_with_ci():
    rec = R.PeptideRecord.from_dict(
        {"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"}
    )
    assert R._display_len(rec) == "12"
    assert R._display_ci(rec) == "[21.2, 99.8]"


def test_parse_committee_votes_from_known_route_and_show_vote_ci():
    rec = R.PeptideRecord.from_dict(
        {
            "name": "SR3335",
            "p_bbb": 41.1,
            "method": "b3clf",
            "known_route": "B3clf 12-model consensus 5/12 BBB+ (strong borderline)",
        }
    )
    assert rec.committee_pos == 5
    assert rec.committee_n == 12
    ci = R._display_ci(rec)
    assert ci.startswith("Vote-CI90 [")
    assert "(5/12)" in ci


def test_parse_committee_votes_from_explicit_fields():
    rec = R.PeptideRecord.from_dict(
        {
            "name": "SR1001",
            "p_bbb": 20.3,
            "method": "b3clf",
            "vote_pos": 1,
            "vote_total": 12,
        }
    )
    assert rec.committee_pos == 1
    assert rec.committee_n == 12
    assert "Vote-CI90" in R._display_ci(rec)


def test_adaptive_ci_header_peptide_only():
    recs = [
        R.PeptideRecord.from_dict({"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"})
    ]
    assert R._adaptive_ci_header(recs) == "90% CI"


def test_adaptive_ci_header_small_molecule_only():
    recs = [
        R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf", "known_route": "5/12 BBB+"})
    ]
    assert R._adaptive_ci_header(recs) == "Vote-CI90"


def test_adaptive_ci_header_mixed():
    recs = [
        R.PeptideRecord.from_dict({"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"}),
        R.PeptideRecord.from_dict({"name": "SR3335", "p_bbb": 41.1, "method": "b3clf", "known_route": "5/12 BBB+"}),
    ]
    assert R._adaptive_ci_header(recs) == "Uncertainty (90% CI / Vote-CI90)"


# ═══════════════════════════════════════════════════════════════════════
# 端到端构建（模板模式）+ 产物无中文
# ═══════════════════════════════════════════════════════════════════════

def test_build_report_template_mode_no_chinese(tmp_path):
    preds = [
        {"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"},
        {"name": "NN9161", "length": 18, "mw": 2200, "p_bbb": None,
         "modification": "C18 fatty-acid + PEG"},
    ]
    bundle = R.build_bbb_report(preds, str(tmp_path), use_llm=False)
    # HTML 存在且无中文
    html = open(bundle.html_path, encoding="utf-8").read()
    assert not re.search(r"[\u4e00-\u9fff]", html), "HTML 不应含中文"
    # CSV 存在且无中文
    csv_txt = open(bundle.matrix_csv, encoding="utf-8").read()
    assert not re.search(r"[\u4e00-\u9fff]", csv_txt), "CSV 不应含中文"
    assert bundle.llm_status  # 有状态串


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pptx") is None,
    reason="python-pptx 未安装（可选依赖）")
def test_build_report_pptx_no_chinese(tmp_path):
    import zipfile

    preds = [{"name": "BRP", "sequence": "THRILRRLFNLC", "p_bbb": 87.5, "ci": "[21.2, 99.8]"}]
    bundle = R.build_bbb_report(preds, str(tmp_path), use_llm=False, pptx=True)
    assert bundle.pptx_path and os.path.exists(bundle.pptx_path)
    # PPTX 字节层面无中文（含主题字体清理）
    blob = ""
    with zipfile.ZipFile(bundle.pptx_path) as z:
        for n in z.namelist():
            if n.endswith(".xml"):
                blob += z.read(n).decode("utf-8", "ignore")
    assert not re.search(r"[\u4e00-\u9fff]", blob), "PPTX 不应含中文（含主题字体）"
