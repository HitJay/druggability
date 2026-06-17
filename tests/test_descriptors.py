"""
bbbkit.peptide.descriptors 测试（纯 Python，无 torch / 无网络 / 无 GPU）

固化 WS2 hybrid 基线的确定性逻辑：修饰解析、protraction 惩罚单调性、
apply_penalty 单向性与边界、天然肽零回归、NN9161 类假阳性修复。
运行: python -m pytest tests/test_descriptors.py -v
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bbbkit.peptide import descriptors as D  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════
# 修饰解析（parse_modification）
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("mod", ["", None, "none", "native", "unmodified", "L-backbone"])
def test_parse_native_is_empty(mod):
    d = D.parse_modification(mod)
    assert d.fa_chain_len == 0
    assert not d.is_protracted
    assert not d.is_lipidated


def test_parse_c18_diacid_peg():
    d = D.parse_modification("C18 diacid + PEG2")
    assert d.fa_chain_len == 18
    assert d.is_diacid
    assert d.has_peg
    assert d.is_lipidated and d.is_protracted


def test_parse_c16_liraglutide_style():
    d = D.parse_modification("C16 fatty-acid (palmitoyl)")
    assert d.fa_chain_len == 16
    assert not d.is_diacid
    assert d.is_lipidated


def test_parse_chain_priority_c20_over_c18():
    # 同时含 C20/C18 关键词时取更长链，避免子串误配
    d = D.parse_modification("C20 icosanedioic")
    assert d.fa_chain_len == 20


def test_parse_cyclic_and_daa():
    d = D.parse_modification("cyclic disulfide, D-Phe")
    assert d.is_cyclic
    assert d.has_d_aa
    # 仅环化/D-aa（无脂化/PEG/二酸）不算 protracted
    assert not d.is_protracted


# ═══════════════════════════════════════════════════════════════════════
# 惩罚单调性（protraction_penalty）
# ═══════════════════════════════════════════════════════════════════════

def _pen(mod):
    return D.protraction_penalty(D.parse_modification(mod))


def test_penalty_native_is_zero():
    assert _pen("") == 0.0
    assert _pen("native") == 0.0


def test_penalty_monotone_by_chain_length():
    assert _pen("C16") < _pen("C18") < _pen("C20")


def test_penalty_diacid_adds_on_top():
    assert _pen("C18 diacid") > _pen("C18")


def test_penalty_peg_adds():
    assert _pen("C18 + PEG") > _pen("C18")


def test_penalty_ordering_lira_vs_sema():
    # liraglutide(C16) < semaglutide(C18 diacid)
    assert _pen("C16") < _pen("C18 diacid")


def test_penalty_cyclic_daa_small():
    # 环化/D-aa 仅小权重，远小于脂化
    assert 0 < _pen("cyclic") < _pen("C16")
    assert 0 < _pen("D-Ala") < _pen("C16")


# ═══════════════════════════════════════════════════════════════════════
# 融合（apply_penalty）—— 单向、边界、零回归
# ═══════════════════════════════════════════════════════════════════════

def test_apply_penalty_zero_is_identity():
    assert D.apply_penalty(87.5, 0.0) == 87.5
    assert D.apply_penalty(12.3, 0.0) == 12.3


def test_apply_penalty_only_decreases():
    for p in (10.0, 50.0, 87.5, 98.0):
        for delta in (1.0, 3.0, 5.0):
            assert D.apply_penalty(p, delta) <= p


def test_apply_penalty_bounded():
    for p in (0.0, 50.0, 100.0):
        for delta in (0.0, 5.0, 50.0):
            v = D.apply_penalty(p, delta)
            assert 0.0 <= v <= 100.0


def test_apply_penalty_logit_correctness():
    # 手算校验：p=95.8%, delta=5.0 → sigmoid(logit(0.958)-5)
    p, delta = 95.8, 5.0
    logit = math.log(0.958 / 0.042)
    expected = 100.0 / (1.0 + math.exp(-(logit - delta)))
    assert abs(D.apply_penalty(p, delta) - round(expected, 1)) < 0.2


# ═══════════════════════════════════════════════════════════════════════
# 端到端（protraction_adjust）
# ═══════════════════════════════════════════════════════════════════════

def test_adjust_native_zero_regression():
    # 无修饰 → p_final == p_seq，delta == 0
    r = D.protraction_adjust(87.5, None)
    assert r["delta"] == 0.0
    assert r["p_final"] == 87.5
    assert not r["is_protracted"]


def test_adjust_none_score_stays_none():
    r = D.protraction_adjust(None, "C18 + PEG")
    assert r["p_final"] is None
    assert r["delta"] > 0


def test_adjust_gradient_lira_sema():
    # GLP-1 backbone 95.8% → liraglutide(C16) > semaglutide(C18 diacid) 的 p_final
    lira = D.protraction_adjust(95.8, "C16 fatty-acid")
    sema = D.protraction_adjust(95.8, "C18 diacid")
    assert lira["p_final"] > sema["p_final"]      # C16 下调更少
    assert lira["p_final"] < 95.8                  # 仍被下调
    assert sema["p_final"] < lira["p_final"]


def test_adjust_nn9161_false_positive_fixed():
    # NN9161 类：假设骨架高分（如 83% 旧假阳性）→ C18+PEG 强下调到 BBB-
    r = D.protraction_adjust(83.0, "C18 fatty-acid + PEG (~2200 Da)")
    assert r["is_protracted"]
    assert r["p_final"] < 50.0                     # 翻转假阳性
    assert r["p_final"] < r["p_seq"]
