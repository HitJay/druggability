"""
tests/test_interface_variants.py — 界面致病突变映射模块的独立单元测试

测试范围 (全部离线, 不打网络):
- UniProt flat-file 解析 (VARIANT/DISEASE/序列)
- 双证据 pathogenic 规则
- AM 证据合并
- SAV 序列 QC (等长直比 + 滑窗)
- 界面残基判定 (合成 PDB, 精确值对拍)
- InterfaceVariantResult 汇总指标
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from druggability.interface_variants import (
    InterfaceVariantResult,
    SavRecord,
    _model_seq_from_pdb,
    _parse_ft_blocks,
    find_interface_residues,
    merge_am_evidence,
    parse_uniprot_savs,
    qc_sequence_match,
    summarize_for_target,
)


# ─── fixtures: 合成数据 ───────────────────────────────────────────────


@pytest.fixture
def uniprot_txt(tmp_path: Path) -> str:
    """模拟 UniProt flat file: 3 个 VARIANT (1 个致病), 1 条 DISEASE comment"""
    return textwrap.dedent("""\
        ID   TEST_HUMAN              Reviewed;        120 AA.
        SQ   SEQUENCE   120 AA;  13000 MW;
        MAAABBBBBB CCCCCCCCCC DDDDDDDDDD EEEEEEEEEE FFFFFFFFFF GGGGGGGGGG
        HHHHHHHHHH IIIIIIIIII JJJJJJJJJJ KKKKKKKKKK LLLLLLLLLL MMMMMMMMMM
        //
        CC   -!- DISEASE: Test syndrome (TS); a rare disorder affecting the
        CC       heart and kidney. Note=The disease is caused by variants
        CC       affecting the gene represented in this entry.
        FT   VARIANT         15
        FT                   /note=\"A -> T (in TS; dbSNP:rs123)\"
        FT                   /id=\"VAR_000001\"
        FT   VARIANT         45
        FT                   /note=\"F -> L (in dbSNP:rs456; benign polymorphism)\"
        FT                   /id=\"VAR_000002\"
        FT   VARIANT         60..65
        FT                   /note=\"Missing (in TS)\"
        FT                   /id=\"VAR_000003\"
        FT   VARIANT         80
        FT                   /note=\"E -> K (in TS; decreases signaling)\"
        FT                   /id=\"VAR_000004\"
    """)


@pytest.fixture
def synthetic_complex_pdb(tmp_path: Path) -> Path:
    """
    合成二元复合物: 链 A (残基 1-120) 与链 B (残基 1-100), CA 坐标手工布置,
    让 A 链残基 14-16 与 B 链残基 20-22 明确接触 (<6Å), 其余远离 (>10Å)。
    """
    lines = []
    # chain A: 逐残基 x = i*3.8, y=0, z=0  -> 相邻 3.8Å, 隔 2 残基 ~7.6Å
    aas = "MAACCCCCCDDDDDDDEEEEEEEEFFGGHHIIKKLLMMNNPPQQRRSSTTUVWXYZGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
    for i in range(1, 121):
        aa = aas[(i - 1) % len(aas)]
        three = {"A": "ALA", "C": "CYS", "D": "ASP", "E": "GLU", "F": "PHE", "G": "GLY",
                 "H": "HIS", "I": "ILE", "K": "LYS", "L": "LEU", "M": "MET", "N": "ASN",
                 "P": "PRO", "Q": "GLN", "R": "ARG", "S": "SER", "T": "THR", "V": "VAL",
                 "W": "TRP", "Y": "TYR", "U": "ALA", "X": "ALA", "Z": "ALA",
                 "B": "ALA", "J": "ALA", "O": "ALA"}.get(aa, "ALA")
        x, y, z = i * 3.8, 0.0, 0.0
        lines.append(
            f"ATOM  {i:5d}  CA  {three} A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C")
    # chain B: 让残基 21 的 CA 落在 A 链残基 15 附近 (x=57, y=5, z=0), 距 ~5Å
    for i in range(1, 101):
        if i == 21:
            x, y, z = 57.0, 5.0, 0.0     # A15 是 x=57 (15*3.8=57) -> CA 距离 5Å <6
        elif i == 22:
            x, y, z = 60.8, 5.0, 0.0     # A16 x=60.8 -> 距离 5Å
        else:
            x, y, z = i * 3.8, 60.0, 0.0  # 其余远在 y=60, 距离 >>6Å
        lines.append(
            f"ATOM  {i:5d}  CA  ALA B{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C")
    pdb = tmp_path / "complex.pdb"
    pdb.write_text("\n".join(lines) + "\nEND\n")
    return pdb


# ─── UniProt 解析 ─────────────────────────────────────────────────────


class TestUniprotParsing:
    def test_ft_blocks(self, uniprot_txt):
        blocks = _parse_ft_blocks(uniprot_txt)
        types = [t for t, _ in blocks]
        assert types.count("VARIANT") == 4
        assert types.count("DISEASE") == 0  # DISEASE 在 CC 行, 不在 FT

    def test_parse_savs(self, uniprot_txt):
        savs, seq = parse_uniprot_savs(uniprot_txt)
        # 3 个点突变 (60..65 Missing 被排除)
        assert len(savs) == 3
        #致病: 15 (in TS), 80 (in TS); 良性: 45
        path = [s for s in savs if s.uniprot_pathogenic]
        assert {s.position for s in path} == {15, 80}
        benign = [s for s in savs if not s.uniprot_pathogenic]
        assert benign[0].position == 45
        # 序列解析
        assert len(seq) == 120

    def test_sav_fields(self, uniprot_txt):
        savs, _ = parse_uniprot_savs(uniprot_txt)
        s15 = next(s for s in savs if s.position == 15)
        assert (s15.wt, s15.mut) == ("A", "T")
        assert "UniProt" in s15.sources


# ─── 双证据规则 ────────────────────────────────────────────────────────


class TestEvidenceRules:
    def test_two_evidence_required(self):
        s = SavRecord(position=10, wt="A", mut="T",
                      am_pathogenic=True, uniprot_pathogenic=True)
        assert s.is_pathogenic and s.n_evidence == 2

    def test_one_evidence_insufficient(self):
        s1 = SavRecord(position=10, wt="A", mut="T", am_pathogenic=True)
        s2 = SavRecord(position=11, wt="A", mut="T", uniprot_pathogenic=True)
        assert not s1.is_pathogenic and not s2.is_pathogenic

    def test_zero_evidence(self):
        s = SavRecord(position=10, wt="A", mut="T")
        assert not s.is_pathogenic

    def test_merge_am(self):
        savs = [SavRecord(position=15, wt="A", mut="T"),
                SavRecord(position=45, wt="F", mut="L")]
        am = {"A15T": (0.91, "LP"), "F45L": (0.01, "LBen")}
        merge_am_evidence(savs, am)
        assert savs[0].am_pathogenic is True
        assert savs[0].am_prob == 0.91
        assert "AlphaMissense" in savs[0].sources
        assert savs[1].am_pathogenic is False

    def test_merge_am_threshold(self):
        # bulk-TSV 回退路径: 无 class, 仅概率
        savs = [SavRecord(position=5, wt="C", mut="G")]
        am = {"C5G": (0.7, "")}
        merge_am_evidence(savs, am)
        assert savs[0].am_pathogenic is True  # prob >= 0.5

    def test_merge_am_missing_variant(self):
        savs = [SavRecord(position=7, wt="W", mut="R")]
        merge_am_evidence(savs, {"C5G": (0.9, "LP")})
        assert savs[0].am_pathogenic is False
        assert savs[0].am_prob is None


# ─── SAV QC ────────────────────────────────────────────────────────────


class TestSequenceQC:
    def test_identical(self):
        frac, ok = qc_sequence_match("MAAV", "MAAV")
        assert frac == 0.0 and ok

    def test_within_tolerance(self):
        # 4% mismatch (< 5% 阈值)
        ref = "MAAVAGST" * 10  # 80 aa
        model = list(ref)
        model[3] = "X" if model[3] != "X" else "Y"
        model[5] = "X" if model[5] != "X" else "Y"
        model[7] = "X" if model[7] != "X" else "Y"
        frac, ok = qc_sequence_match("".join(model), ref)
        assert ok and frac <= 0.05

    def test_beyond_tolerance(self):
        ref = "MAAVAGST" * 10
        model = "XXXXXXXX" * 10
        frac, ok = qc_sequence_match(model, ref)
        assert not ok and frac > 0.05

    def test_offset_window(self):
        # 模型在首端截断 2 aa -> 滑窗应找到偏移 2 的完美匹配
        ref = "XXMAAVAGSTQQ" + "Y" * 8
        model = "MAAVAGSTQQ"
        frac, ok = qc_sequence_match(model, ref)
        assert ok

    def test_empty(self):
        frac, ok = qc_sequence_match("", "MAAV")
        assert not ok and frac == 1.0


# ─── 界面残基判定 ──────────────────────────────────────────────────────


class TestInterfaceDetection:
    def test_ca_readout(self, synthetic_complex_pdb):
        seq_a = _model_seq_from_pdb(synthetic_complex_pdb, "A")
        assert len(seq_a) == 120

    def test_interface_pairs(self, synthetic_complex_pdb):
        ia, ib = find_interface_residues(synthetic_complex_pdb, "A", "B", cutoff_a=6.0)
        # A15/A16 与 B21/B22 设计为 <6Å 接触
        assert 15 in ia and 16 in ia
        assert 21 in ib and 22 in ib
        # 远端残基不进界面
        assert 50 not in ia
        assert 90 not in ib

    def test_cutoff_sensitivity(self, synthetic_complex_pdb):
        # 收紧到 4Å 应该滤掉 CA-距离 5Å 的接触对 (CB 近似下可能也滤掉)
        ia4, ib4 = find_interface_residues(synthetic_complex_pdb, "A", "B", cutoff_a=4.0)
        ia6, ib6 = find_interface_residues(synthetic_complex_pdb, "A", "B", cutoff_a=6.0)
        assert len(ia4) <= len(ia6)
        assert len(ib4) <= len(ib6)

    def test_chain_swap_symmetry(self, synthetic_complex_pdb):
        # 换主客视角, 界面集合交换
        ia1, ib1 = find_interface_residues(synthetic_complex_pdb, "A", "B")
        ia2, ib2 = find_interface_residues(synthetic_complex_pdb, "B", "A")
        assert ia1 == ib2 and ib1 == ia2


# ─── 汇总指标 ──────────────────────────────────────────────────────────


class TestResultSummary:
    def test_richness(self):
        r = InterfaceVariantResult(uniprot_a="P1", uniprot_b="P2")
        r.interface_res_a = {15, 16, 17}
        r.interface_res_b = {21}
        s = SavRecord(position=15, wt="A", mut="T", am_pathogenic=True,
                      uniprot_pathogenic=True)
        r.interface_pathogenic_a = [s]
        assert r.n_interface_pathogenic == 1
        assert abs(r.interface_mutation_richness - 1 / 4) < 1e-9

    def test_richness_zero_div(self):
        r = InterfaceVariantResult(uniprot_a="P1", uniprot_b="P2")
        assert r.interface_mutation_richness == 0.0

    def test_to_dict_roundtrip(self):
        r = InterfaceVariantResult(uniprot_a="P1", uniprot_b="P2")
        d = r.to_dict()
        assert d["uniprot_a"] == "P1"
        assert d["n_interface_pathogenic"] == 0
        assert isinstance(d["interface_pathogenic_a"], list)

    def test_summarize_sorts_by_hits(self, monkeypatch, synthetic_complex_pdb):
        # summarize_for_target 的排序逻辑 (monkeypatch 掉网络调用)
        from druggability import interface_variants as iv

        def fake_map(a, b, complex_pdb=None, **kw):
            r = InterfaceVariantResult(uniprot_a=a, uniprot_b=b)
            if b == "P_HOT":
                s = SavRecord(position=15, wt="A", mut="T",
                              am_pathogenic=True, uniprot_pathogenic=True)
                r.interface_pathogenic_a = [s]
                r.interface_res_a = {15, 16}
                r.interface_res_b = {21}
            return r

        monkeypatch.setattr(iv, "map_pathogenic_to_interface", fake_map)
        res = summarize_for_target("Q_TARGET", ["P_COLD", "P_HOT"])
        assert res[0].uniprot_b == "P_HOT"
        assert res[0].n_interface_pathogenic == 1
        assert res[1].n_interface_pathogenic == 0
