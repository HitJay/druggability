"""
bbbkit.peptide.descriptors — 修饰/PK 描述符 + protraction 惩罚（WS2 Option A 基线）

把"缺的那条轴"——修饰/PK——补进 BBB 预测：序列塔给骨架内在通透倾向 p_seq（上界），
本模块从修饰字符串解析描述符并施加 **protraction 惩罚** Δ（只降不升），融合为：

    p_final = sigmoid(logit(p_seq) - Δ)

设计原则（见 docs/bbb-hybrid-protracted.md）：
- **纯 Python，无 torch**：描述符与惩罚均规则化，可在任意环境（含 .venv）单测。
- **物理先验，非拟合数**：方向（长效化降低入脑）是已确立药理学；惩罚幅度是透明、可调、
  集中定义的启发式常量，明确标注为 prior，不冒充已训练的定量模型。
- **零回归**：天然/无修饰肽 Δ=0 → p_final == p_seq。

诚实边界：p_final 是"经长效化下调的上界"，仍非体内脑暴露；惩罚来自修饰**字符串**而非
完整分子图，幅度待内部 PK 数据校准（计划 P4）。
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

# ── 关键词模式（大小写不敏感）──
_FA_C16 = re.compile(r"c16|palmit", re.IGNORECASE)
_FA_C18 = re.compile(r"c18|stear|octadecan", re.IGNORECASE)
_FA_C20 = re.compile(r"c20|icosan|eicosan", re.IGNORECASE)
_DIACID = re.compile(r"diacid|gamma-?glu.*diacid|γglu", re.IGNORECASE)
_PEG = re.compile(r"\bpeg\d*\b|pegylat|\boeg\d*\b", re.IGNORECASE)
_CYCLIC = re.compile(r"cycl|lactam|disulf|staple|head-to-tail", re.IGNORECASE)
_D_AA = re.compile(r"d-?ala|d-?phe|d-?amino|d-?trp|d-?lys", re.IGNORECASE)

# ── 惩罚常量（logit 单位，物理先验；集中定义、可调）──
# 链越长 → 白蛋白结合越强、游离分数越低 → 入脑越少（单调递增）。
_PEN_FA = {16: 3.0, 18: 3.5, 20: 4.0}
_PEN_DIACID = 1.5     # 二酸连接子显著增强白蛋白结合（如 semaglutide）
_PEN_PEG = 1.5        # PEG 增大有效尺寸 + 亲水
_PEN_CYCLIC = 0.3     # 环化主要影响稳定性而非入脑 → 小权重
_PEN_D_AA = 0.2       # D-氨基酸同上 → 小权重

_EPS = 1e-3           # logit 数值保护，避免 p=0/1 时无穷


@dataclass
class ModificationDescriptors:
    """从修饰字符串解析出的结构化描述符。"""

    fa_chain_len: int = 0          # 0 / 16 / 18 / 20
    is_diacid: bool = False
    has_peg: bool = False
    is_cyclic: bool = False
    has_d_aa: bool = False
    raw: str = ""

    @property
    def is_lipidated(self) -> bool:
        return self.fa_chain_len > 0

    @property
    def is_protracted(self) -> bool:
        """是否含任何会降低入脑的长效化/修饰特征。"""
        return self.is_lipidated or self.has_peg or self.is_diacid

    def to_dict(self) -> dict[str, Any]:
        return {
            "fa_chain_len": self.fa_chain_len,
            "is_diacid": self.is_diacid,
            "has_peg": self.has_peg,
            "is_cyclic": self.is_cyclic,
            "has_d_aa": self.has_d_aa,
            "is_lipidated": self.is_lipidated,
            "is_protracted": self.is_protracted,
        }


def parse_modification(modification: str | None) -> ModificationDescriptors:
    """把修饰字符串（如 'C18 diacid + PEG'）规则解析为描述符。

    无修饰 / 'none' / 'native' → 全零描述符（→ 零惩罚 → 不改变 p_seq）。
    """
    mod = (modification or "").strip()
    if not mod or mod.lower() in {"none", "native", "-", "l-backbone", "unmodified"}:
        return ModificationDescriptors(raw=mod)

    # 脂肪酸链长：优先匹配更长的链（C20 > C18 > C16），避免子串误配
    fa = 0
    if _FA_C20.search(mod):
        fa = 20
    elif _FA_C18.search(mod):
        fa = 18
    elif _FA_C16.search(mod):
        fa = 16

    return ModificationDescriptors(
        fa_chain_len=fa,
        is_diacid=bool(_DIACID.search(mod)),
        has_peg=bool(_PEG.search(mod)),
        is_cyclic=bool(_CYCLIC.search(mod)),
        has_d_aa=bool(_D_AA.search(mod)),
        raw=mod,
    )


def protraction_penalty(desc: ModificationDescriptors) -> float:
    """描述符 → protraction 惩罚 Δ（logit 单位，≥0；越大下调越多）。

    天然/无修饰 → 0。脂化/二酸/PEG 按物理先验叠加；环化/D-aa 小权重。
    """
    delta = 0.0
    if desc.fa_chain_len in _PEN_FA:
        delta += _PEN_FA[desc.fa_chain_len]
        if desc.is_diacid:
            delta += _PEN_DIACID
    if desc.has_peg:
        delta += _PEN_PEG
    if desc.is_cyclic:
        delta += _PEN_CYCLIC
    if desc.has_d_aa:
        delta += _PEN_D_AA
    return round(delta, 3)


def apply_penalty(p_seq_pct: float, delta: float) -> float:
    """融合：p_final% = sigmoid(logit(p_seq) - Δ) * 100。

    只降不升（Δ≥0），结果钳制到 [0,100]。p_seq 先钳到 (0,1) 避免 logit 无穷。
    """
    p = min(max(p_seq_pct / 100.0, _EPS), 1.0 - _EPS)
    logit = math.log(p / (1.0 - p))
    p_final = 1.0 / (1.0 + math.exp(-(logit - max(delta, 0.0))))
    return round(p_final * 100.0, 1)


def protraction_adjust(p_seq_pct: float | None,
                       modification: str | None) -> dict[str, Any]:
    """端到端：p_seq + 修饰串 → {p_seq, p_final, delta, descriptors}。

    p_seq 为 None（序列未打分）时，p_final 也为 None（不臆造）。
    """
    desc = parse_modification(modification)
    delta = protraction_penalty(desc)
    if p_seq_pct is None:
        p_final = None
    else:
        p_final = apply_penalty(p_seq_pct, delta) if delta > 0 else round(float(p_seq_pct), 1)
    return {
        "p_seq": p_seq_pct,
        "p_final": p_final,
        "delta": delta,
        "is_protracted": desc.is_protracted,
        "descriptors": desc.to_dict(),
    }
