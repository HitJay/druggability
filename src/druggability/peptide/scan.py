"""
druggability.peptide.scan — 多肽全序列单点突变扫描与 ΔΔG 热力学亲和力分析模块

提供工业级多肽药物化学评估能力：
1. In Silico Alanine Scanning (丙氨酸扫描):
   - 自动遍历多肽每一个氨基酸，将其侧链截断为 Ala (保留主链及 Cβ)，重算界面原子接触网络；
   - 测定结合亲和力变化 ΔΔG = ΔG_mut - ΔG_wt (kcal/mol)；
   - 自动识别核心功能热点 (Critical Hotspots, ΔΔG >> 0) 与修饰耐受出射向量 (Permissive Exit Vectors, ΔΔG ≈ 0)。
2. Deep Position Mutational Scanning (指定位点 20 种氨基酸替换矩阵):
   - 针对指定多肽位点，预测替换为全部 20 种天然氨基酸后的亲和力变化；
   - 综合静电匹配、极性互补、疏水堆积与空间位阻 (Steric Clash) 给出改造排序。
"""

from __future__ import annotations

import copy
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .affinity import (
    GAS_CONSTANT,
    MAX_SASA_TIEN,
    RESIDUE_CLASSES,
    AtomRecord,
    format_kd,
    load_pdb_atoms,
    predict_peptide_affinity,
)

# 标准氨基酸范德华半径/体积粗估参考 (用于位阻探测)
RESIDUE_VOLUMES = {
    "GLY": 60.1,
    "ALA": 88.6,
    "SER": 89.0,
    "CYS": 108.5,
    "ASP": 111.1,
    "PRO": 112.7,
    "ASN": 114.1,
    "THR": 116.1,
    "GLU": 138.4,
    "VAL": 140.0,
    "GLN": 143.8,
    "HIS": 153.2,
    "MET": 162.9,
    "ILE": 166.7,
    "LEU": 166.7,
    "LYS": 168.6,
    "ARG": 173.4,
    "PHE": 189.9,
    "TYR": 193.6,
    "TRP": 227.8,
}

ALL_20_AMINO_ACIDS = [
    "ALA", "ARG", "ASN", "ASP", "CYS",
    "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO",
    "SER", "THR", "TRP", "TYR", "VAL",
]


@dataclass
class AlaScanEntry:
    """单个残基的丙氨酸突变分析结果"""

    res_seq: int
    orig_res: str
    wt_delta_g: float
    mut_delta_g: float
    ddg: float  # ΔΔG = ΔG_mut - ΔG_wt (kcal/mol; 正值代表突变后亲和力受损)
    lost_contacts: int
    classification: str  # Critical Hotspot, Moderate Contributor, Neutral, Tolerant Exit Vector
    is_hotspot: bool
    is_tolerant_exit_vector: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AlaScanResult:
    """多肽全长丙氨酸扫描结果集合"""

    ok: bool
    complex_name: str
    receptor_chain: str
    peptide_chain: str
    wt_delta_g: float
    wt_kd_text: str
    entries: list[AlaScanEntry] = field(default_factory=list)
    critical_hotspots: list[str] = field(default_factory=list)
    tolerant_exit_vectors: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entries"] = [e.to_dict() for e in self.entries]
        return data

    def to_df(self):
        """转为 pandas DataFrame 格式"""
        import pandas as pd

        return pd.DataFrame([e.to_dict() for e in self.entries])

    def summary_markdown(self) -> str:
        """生成供 Agent 汇报和交付总结的 Markdown 表格"""
        if not self.ok:
            return f"**Alanine Scanning Failed**: {self.error}"

        hotspots_str = ", ".join([f"`{h}`" for h in self.critical_hotspots]) or "None detected"
        vectors_str = ", ".join([f"`{v}`" for v in self.tolerant_exit_vectors]) or "None detected"

        lines = [
            f"### In Silico Alanine Scanning Profile: `{self.complex_name}`",
            rf"- **Wild-Type Binding Energy ($\Delta G_\text{{wt}}$)**: **`{self.wt_delta_g:.2f} kcal/mol`** ($K_d \approx {self.wt_kd_text}$)",
            f"- **Receptor / Peptide Chains**: `{self.receptor_chain}` / `{self.peptide_chain}`",
            rf"- **Critical Hotspots ($\Delta\Delta G \ge 1.5\text{{ kcal/mol}}$)**: {hotspots_str}",
            rf"- **Tolerant Exit Vectors ($\Delta\Delta G \le 0.5\text{{ kcal/mol}}$, Modification-friendly)**: {vectors_str}",
            "",
            r"| Position | WT Residue | $\Delta G_\text{mut}$ (kcal/mol) | $\Delta\Delta G$ (kcal/mol) | Lost Contacts | Role / Classification |",
            "| :---: | :---: | :---: | :---: | :---: | :--- |",
        ]

        for e in self.entries:
            ddg_str = f"+{e.ddg:.2f}" if e.ddg > 0 else f"{e.ddg:.2f}"
            badge = ""
            if e.is_hotspot:
                badge = "🔴 **Critical Hotspot**"
            elif e.is_tolerant_exit_vector:
                badge = "🟢 **Tolerant / Exit Vector**"
            elif e.classification == "Moderate Contributor":
                badge = "🟡 Moderate Contributor"
            else:
                badge = "⚪ Neutral"

            lines.append(
                f"| {e.res_seq} | `{e.orig_res}` | {e.mut_delta_g:.2f} | {ddg_str} | -{e.lost_contacts} | {badge} |"
            )

        return "\n".join(lines)


@dataclass
class MutationCandidate:
    """单点特定氨基酸替换的预测条目"""

    mutant_res: str
    mutant_class: str
    pred_delta_g: float
    ddg: float
    pred_kd_text: str
    rank: int
    compatibility: str  # Favorable, Neutral, Tolerant, Clashing / Disruptive
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PositionScanResult:
    """多肽单点 20 种氨基酸替换扫描结果"""

    ok: bool
    complex_name: str
    res_seq: int
    orig_res: str
    wt_delta_g: float
    candidates: list[MutationCandidate] = field(default_factory=list)
    best_substitutions: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [c.to_dict() for c in self.candidates]
        return data

    def to_df(self):
        import pandas as pd

        return pd.DataFrame([c.to_dict() for c in self.candidates])

    def summary_markdown(self) -> str:
        if not self.ok:
            return f"**Position Mutational Scanning Failed**: {self.error}"

        best_str = ", ".join([f"`{b}`" for b in self.best_substitutions]) or "None"

        lines = [
            f"### Position Mutational Scanning: `{self.complex_name}` at `{self.orig_res}{self.res_seq}`",
            rf"- **Wild-Type Residual**: `{self.orig_res}{self.res_seq}` ($\Delta G_\text{{wt}} = {self.wt_delta_g:.2f}\text{{ kcal/mol}}$)",
            f"- **Top Recommended Substitutions**: {best_str}",
            "",
            r"| Rank | Mutation | Class | Pred $\Delta G$ | $\Delta\Delta G$ | Pred $K_d$ | Assessment | Notes |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ]

        for c in self.candidates:
            ddg_str = f"+{c.ddg:.2f}" if c.ddg > 0 else f"{c.ddg:.2f}"
            lines.append(
                f"| {c.rank} | **`{c.mutant_res}`** | {c.mutant_class} | {c.pred_delta_g:.2f} | {ddg_str} | {c.pred_kd_text} | {c.compatibility} | {c.note} |"
            )

        return "\n".join(lines)


# ── 核心计算逻辑：In Silico 丙氨酸扫描 ─────────────────────────────────


def _calculate_contacts_and_delta_g(
    rec_atoms: list[AtomRecord],
    pep_atoms: list[AtomRecord],
    pct_nis_apolar: float = 35.0,
    distance_cutoff: float = 5.5,
) -> tuple[float, int, dict[str, int]]:
    """内部轻量计算两链界面的 ICs 与结合能 ΔG"""
    rec_coords = np.stack([a.coord for a in rec_atoms])
    pep_coords = np.stack([a.coord for a in pep_atoms])

    diff = pep_coords[:, None, :] - rec_coords[None, :, :]
    dists = np.linalg.norm(diff, axis=-1)
    contact_mask = dists <= distance_cutoff

    contacting_pairs = set()
    pep_indices, rec_indices = np.where(contact_mask)
    for p_idx, r_idx in zip(pep_indices, rec_indices):
        pa = pep_atoms[p_idx]
        ra = rec_atoms[r_idx]
        pair = ((pa.res_seq, pa.res_name), (ra.res_seq, ra.res_name))
        contacting_pairs.add(pair)

    ics = {
        "charged_charged": 0,
        "charged_polar": 0,
        "charged_apolar": 0,
        "polar_polar": 0,
        "polar_apolar": 0,
        "apolar_apolar": 0,
    }

    for (p_seq, p_res), (r_seq, r_res) in contacting_pairs:
        p_class = RESIDUE_CLASSES.get(p_res, "apolar")
        r_class = RESIDUE_CLASSES.get(r_res, "apolar")

        classes = sorted([p_class, r_class])
        if classes == ["charged", "charged"]:
            ics["charged_charged"] += 1
        elif classes == ["charged", "polar"]:
            ics["charged_polar"] += 1
        elif classes == ["apolar", "charged"]:
            ics["charged_apolar"] += 1
        elif classes == ["polar", "polar"]:
            ics["polar_polar"] += 1
        elif classes == ["apolar", "polar"]:
            ics["polar_apolar"] += 1
        elif classes == ["apolar", "apolar"]:
            ics["apolar_apolar"] += 1

    total_ics = len(contacting_pairs)
    delta_g_contacts = -(
        0.15 * ics["charged_charged"]
        + 0.12 * ics["charged_polar"]
        + 0.14 * ics["charged_apolar"]
        + 0.16 * ics["polar_polar"]
        + 0.13 * ics["polar_apolar"]
        + 0.18 * ics["apolar_apolar"]
    )
    delta_g = delta_g_contacts - 2.5 + (0.02 * pct_nis_apolar)
    return delta_g, total_ics, ics


def run_alanine_scanning(
    complex_pdb: str | Path,
    *,
    receptor_chain: str | None = None,
    peptide_chain: str | None = None,
    distance_cutoff: float = 5.5,
) -> AlaScanResult:
    """
    对多肽链执行全序列丙氨酸扫描 (In Silico Alanine Scanning)。

    遍历多肽链上的每个残基：
    - 若非 ALA/GLY，将其侧链截断至 Cβ (模拟突变为 Ala)，重算界面接触与结合自由能；
    - 计算 ΔΔG = ΔG_mut - ΔG_wt (kcal/mol)；
    - 判定残基是核心热点 (Critical Hotspot) 还是修饰耐受区 (Tolerant Exit Vector)。
    """
    pdb_path = Path(complex_pdb).resolve()
    if not pdb_path.exists():
        return AlaScanResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            receptor_chain="",
            peptide_chain="",
            wt_delta_g=0.0,
            wt_kd_text="N/A",
            error=f"File not found: {pdb_path}",
        )

    # 1. 计算野生型野生基线
    wt_res = predict_peptide_affinity(
        pdb_path,
        receptor_chain=receptor_chain,
        peptide_chain=peptide_chain,
        distance_cutoff=distance_cutoff,
    )
    if not wt_res.ok:
        return AlaScanResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            receptor_chain="",
            peptide_chain="",
            wt_delta_g=0.0,
            wt_kd_text="N/A",
            error=wt_res.error,
        )

    rec_chain = wt_res.receptor_chain
    pep_chain = wt_res.peptide_chain
    wt_dg = wt_res.delta_g
    pct_nis_apolar = wt_res.nis_properties.get("pct_nis_apolar", 35.0)

    all_atoms = load_pdb_atoms(pdb_path)
    rec_atoms = [a for a in all_atoms if a.chain_id == rec_chain]
    pep_atoms = [a for a in all_atoms if a.chain_id == pep_chain]

    # 获取多肽上所有的残基列表 (序号, 残基名)
    pep_res_list = []
    seen_res = set()
    for a in pep_atoms:
        if (a.res_seq, a.res_name) not in seen_res:
            seen_res.add((a.res_seq, a.res_name))
            pep_res_list.append((a.res_seq, a.res_name))
    pep_res_list.sort(key=lambda x: x[0])

    entries: list[AlaScanEntry] = []
    critical_hotspots: list[str] = []
    tolerant_exit_vectors: list[str] = []

    # 2. 逐位点进行丙氨酸截断
    for res_seq, orig_res in pep_res_list:
        if orig_res in ["ALA", "GLY"]:
            # 本身是 Ala 或 Gly，无侧链截断差异
            entries.append(
                AlaScanEntry(
                    res_seq=res_seq,
                    orig_res=orig_res,
                    wt_delta_g=wt_dg,
                    mut_delta_g=wt_dg,
                    ddg=0.0,
                    lost_contacts=0,
                    classification="Neutral",
                    is_hotspot=False,
                    is_tolerant_exit_vector=True if res_seq in [pep_res_list[0][0], pep_res_list[-1][0]] else False,
                    notes=f"Native {orig_res} (baseline)",
                )
            )
            continue

        # 构建突变多肽原子集：将当前 res_seq 的原子仅保留主链 (N, CA, C, O) 和 CB
        mut_pep_atoms = []
        for a in pep_atoms:
            if a.res_seq == res_seq:
                if a.atom_name in ["N", "CA", "C", "O", "CB"]:
                    # 修改残基名为 ALA
                    mut_atom = copy.deepcopy(a)
                    mut_atom.res_name = "ALA"
                    mut_pep_atoms.append(mut_atom)
            else:
                mut_pep_atoms.append(a)

        mut_dg, mut_ics_tot, _ = _calculate_contacts_and_delta_g(
            rec_atoms, mut_pep_atoms, pct_nis_apolar, distance_cutoff
        )

        ddg = round(mut_dg - wt_dg, 2)
        lost_contacts = max(0, wt_res.total_contacts - mut_ics_tot)

        # 判定级别
        is_hotspot = False
        is_tolerant = False
        classification = "Neutral"

        if ddg >= 1.5:
            classification = "Critical Hotspot"
            is_hotspot = True
            critical_hotspots.append(f"{orig_res}{res_seq}")
        elif ddg >= 0.7:
            classification = "Moderate Contributor"
        elif ddg <= 0.4:
            classification = "Tolerant / Exit Vector"
            is_tolerant = True
            tolerant_exit_vectors.append(f"{orig_res}{res_seq}")
        else:
            classification = "Neutral"

        entries.append(
            AlaScanEntry(
                res_seq=res_seq,
                orig_res=orig_res,
                wt_delta_g=wt_dg,
                mut_delta_g=round(mut_dg, 2),
                ddg=ddg,
                lost_contacts=lost_contacts,
                classification=classification,
                is_hotspot=is_hotspot,
                is_tolerant_exit_vector=is_tolerant,
                notes=f"Lost {lost_contacts} contacts upon truncating to Ala",
            )
        )

    return AlaScanResult(
        ok=True,
        complex_name=str(pdb_path.stem),
        receptor_chain=rec_chain,
        peptide_chain=pep_chain,
        wt_delta_g=wt_dg,
        wt_kd_text=wt_res.kd_text,
        entries=entries,
        critical_hotspots=critical_hotspots,
        tolerant_exit_vectors=tolerant_exit_vectors,
    )


# ── 核心计算逻辑：多肽单点 20 种氨基酸突变扫描 ──────────────────────────


def scan_position_mutations(
    complex_pdb: str | Path,
    *,
    res_seq: int,
    receptor_chain: str | None = None,
    peptide_chain: str | None = None,
    distance_cutoff: float = 5.5,
) -> PositionScanResult:
    """
    针对多肽链上的指定位点 (res_seq)，扫描全部 20 种天然氨基酸替换后的结合力表现。

    综合考虑：
    - 相互作用性质变化 (带电配对/盐桥 vs 同号排斥)
    - 侧链体积与局部微环境位阻容纳性
    - 构象柔性贡献 (如 Pro/Gly 替换)
    """
    pdb_path = Path(complex_pdb).resolve()
    if not pdb_path.exists():
        return PositionScanResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            res_seq=res_seq,
            orig_res="",
            wt_delta_g=0.0,
            error=f"File not found: {pdb_path}",
        )

    wt_res = predict_peptide_affinity(
        pdb_path,
        receptor_chain=receptor_chain,
        peptide_chain=peptide_chain,
        distance_cutoff=distance_cutoff,
    )
    if not wt_res.ok:
        return PositionScanResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            res_seq=res_seq,
            orig_res="",
            wt_delta_g=0.0,
            error=wt_res.error,
        )

    rec_chain = wt_res.receptor_chain
    pep_chain = wt_res.peptide_chain
    wt_dg = wt_res.delta_g

    all_atoms = load_pdb_atoms(pdb_path)
    pep_atoms = [a for a in all_atoms if a.chain_id == pep_chain]
    target_atoms = [a for a in pep_atoms if a.res_seq == res_seq]

    if not target_atoms:
        return PositionScanResult(
            ok=False,
            complex_name=str(pdb_path.stem),
            res_seq=res_seq,
            orig_res="",
            wt_delta_g=wt_dg,
            error=f"Residue sequence number {res_seq} not found in peptide chain '{pep_chain}'",
        )

    orig_res = target_atoms[0].res_name
    orig_vol = RESIDUE_VOLUMES.get(orig_res, 120.0)

    # 找到与该位点残基接触的受体残基列表
    hotspot_info = next((h for h in wt_res.peptide_hotspots if h.res_seq == res_seq), None)
    interacting_receptors = hotspot_info.interacting_receptor_residues if hotspot_info else []

    # 提取周围受体残基属性 (是否有酸性/碱性残基)
    rec_charged_chars = set()
    for r_label in interacting_receptors:
        r_name = "".join([c for c in r_label if c.isalpha()])
        if r_name in ["ASP", "GLU"]:
            rec_charged_chars.add("negative")
        elif r_name in ["ARG", "LYS", "HIS"]:
            rec_charged_chars.add("positive")

    candidates: list[MutationCandidate] = []

    # 评估 20 种突变
    for aa in ALL_20_AMINO_ACIDS:
        if aa == orig_res:
            candidates.append(
                MutationCandidate(
                    mutant_res=aa,
                    mutant_class=RESIDUE_CLASSES.get(aa, "apolar"),
                    pred_delta_g=wt_dg,
                    ddg=0.0,
                    pred_kd_text=wt_res.kd_text,
                    rank=0,
                    compatibility="Native (Wild-Type)",
                    note="Wild-type reference",
                )
            )
            continue

        aa_class = RESIDUE_CLASSES.get(aa, "apolar")
        aa_vol = RESIDUE_VOLUMES.get(aa, 120.0)
        vol_ratio = aa_vol / max(1.0, orig_vol)

        delta_score = 0.0
        notes_list = []
        compatibility = "Neutral"

        # 1. 电荷相互作用评估
        if aa in ["ARG", "LYS"]:
            if "negative" in rec_charged_chars:
                delta_score -= 1.2  # 形成有利盐桥
                notes_list.append("Potential salt bridge with nearby acidic residues")
                compatibility = "Favorable"
            elif "positive" in rec_charged_chars:
                delta_score += 1.8  # 同号排斥
                notes_list.append("Electrostatic clash with nearby basic residues")
                compatibility = "Clashing / Disruptive"

        elif aa in ["ASP", "GLU"]:
            if "positive" in rec_charged_chars:
                delta_score -= 1.2  # 形成有利盐桥
                notes_list.append("Potential salt bridge with nearby basic residues")
                compatibility = "Favorable"
            elif "negative" in rec_charged_chars:
                delta_score += 1.8  # 同号排斥
                notes_list.append("Electrostatic clash with nearby acidic residues")
                compatibility = "Clashing / Disruptive"

        # 2. 体积与位阻评估
        if vol_ratio > 1.6 and len(interacting_receptors) >= 5:
            # 紧密结合腔内换入超大残基 (如 Gly/Ala -> Trp/Phe)
            delta_score += 2.2
            notes_list.append(f"Severe steric clash penalty (volume ratio {vol_ratio:.1f}x)")
            compatibility = "Clashing / Disruptive"
        elif vol_ratio < 0.6 and len(interacting_receptors) >= 5:
            # 紧密疏水腔内大换小，失去范德华接触
            loss = (1.0 - vol_ratio) * 1.5
            delta_score += loss
            notes_list.append(f"Loss of packing vdW contacts (volume ratio {vol_ratio:.1f}x)")

        # 3. 极性互补与疏水匹配
        if aa_class == "apolar" and orig_res in ["ARG", "LYS", "ASP", "GLU"]:
            if not rec_charged_chars:
                delta_score -= 0.6
                notes_list.append("Hydrophobic packing improved in non-polar subcavity")
                compatibility = "Favorable"

        # 4. 特殊残基修正 (Gly / Pro)
        if aa == "GLY" and orig_res == "PRO":
            delta_score += 0.7  # 丢失构象刚性限制，但增加环区柔性
            notes_list.append("Relieves conformational rigidity, allows dynamic loop adaptation")
            compatibility = "Tolerant"
        elif aa == "PRO" and orig_res != "PRO":
            delta_score += 0.5  # 刚性约束可能扭曲主链
            notes_list.append("Proline ring induces backbone kink constraints")

        pred_dg = round(wt_dg + delta_score, 2)
        ddg = round(delta_score, 2)

        # 估算换算后的 Kd
        rt = GAS_CONSTANT * 298.15
        try:
            kd_m = math.exp(pred_dg / rt)
        except OverflowError:
            kd_m = float("inf") if pred_dg > 0 else 0.0

        if not notes_list:
            notes_list.append("Tolerant substitution")
            if abs(ddg) <= 0.3:
                compatibility = "Tolerant"

        candidates.append(
            MutationCandidate(
                mutant_res=aa,
                mutant_class=aa_class,
                pred_delta_g=pred_dg,
                ddg=ddg,
                pred_kd_text=format_kd(kd_m),
                rank=0,
                compatibility=compatibility,
                note="; ".join(notes_list),
            )
        )

    # 按预测亲和力 (ΔG 越负越优先) 排序
    candidates.sort(key=lambda x: x.pred_delta_g)
    for idx, c in enumerate(candidates, start=1):
        c.rank = idx

    best_substitutions = [
        f"{c.mutant_res} ({c.pred_delta_g:.2f} kcal/mol, {c.compatibility})"
        for c in candidates[:3]
        if c.compatibility in ["Favorable", "Tolerant", "Native (Wild-Type)"]
    ]

    return PositionScanResult(
        ok=True,
        complex_name=str(pdb_path.stem),
        res_seq=res_seq,
        orig_res=orig_res,
        wt_delta_g=wt_dg,
        candidates=candidates,
        best_substitutions=best_substitutions,
    )
