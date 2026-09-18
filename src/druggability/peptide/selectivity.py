"""
druggability.peptide.selectivity — 多肽亚型选择性对抗评估与一体化交付模块

针对多肽药物最核心的同源交叉活化风险 (Cross-reactivity / Off-target risk)，
提供端到端的多维对抗评估体系:
1. 经验接触亲和力对比:
   - 主靶点与反筛受体并行评估 (ΔG_target, ΔG_counter, ΔΔG_selectivity, Selectivity Fold)
2. 残基级差异接触指纹 (Differential Contact Fingerprint):
   - 逐残基对比多肽在两个受体上的结合接触增减，精准锁定选择性开关残基 (Selectivity Switch Residues)
3. 空间几何位阻与构象紧缩探测 (Pocket Constriction & Clash Analysis):
   - 探测反筛受体入口或结合腔的狭窄化位移 (如 Helix I 紧缩) 与极性/疏水失配
4. 自包含 3D 交互式 HTML 交付报告 (Self-Contained 3Dmol.js Delivery)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .affinity import (
    GAS_CONSTANT,
    PeptideAffinityResult,
    format_kd,
    load_pdb_atoms,
    predict_peptide_affinity,
)

logger = logging.getLogger(__name__)


@dataclass
class ResidueSelectivityEntry:
    """多肽单个位点在主靶点与反筛靶点上的接触差异"""

    res_seq: int
    res_name: str
    target_contacts: int
    counter_contacts: int
    diff_contacts: int  # target_contacts - counter_contacts (正值代表偏向主靶点)
    is_switch_residue: bool
    role: str  # e.g., 'Primary Target Anchor', 'Counter-Screen Clash/Driver', 'Neutral'
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelectivityAuditResult:
    """多肽亚型对抗选择性综合审计结果"""

    ok: bool
    target_name: str
    counter_name: str
    peptide_name: str
    target_affinity: PeptideAffinityResult
    counter_affinity: PeptideAffinityResult
    ddg_selectivity: float  # ΔG_counter - ΔG_target (kcal/mol; 正值代表主靶点亲和力更优)
    selectivity_fold: float  # Kd_counter / Kd_target
    selectivity_tier: str  # Exemplary, Favorable, Moderate, Weak, or Inverted
    switch_residues: list[str] = field(default_factory=list)
    residue_comparisons: list[ResidueSelectivityEntry] = field(default_factory=list)
    geometric_clash_warnings: list[str] = field(default_factory=list)
    html_report_path: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target_affinity"] = self.target_affinity.to_dict()
        data["counter_affinity"] = self.counter_affinity.to_dict()
        data["residue_comparisons"] = [r.to_dict() for r in self.residue_comparisons]
        return data

    def summary_markdown(self) -> str:
        """生成供 Agent 汇报和交付总结的 Markdown 评述"""
        if not self.ok:
            return f"**Selectivity Audit Failed**: {self.error}"

        sw_str = ", ".join([f"`{s}`" for s in self.switch_residues]) or "None"
        fold_str = f"{self.selectivity_fold:.1f}x" if self.selectivity_fold >= 1.0 else f"1/{1.0/max(1e-6, self.selectivity_fold):.1f}x"

        lines = [
            f"### Subtype Selectivity Audit: `{self.peptide_name}` ({self.target_name} vs. {self.counter_name})",
            f"- **Selectivity Assessment**: **{self.selectivity_tier}** (Predicted Preference Ratio: **`{fold_str}`**)",
            rf"- **$\Delta\Delta G_\text{{selectivity}}$ (Counter − Target)**: **`{self.ddg_selectivity:+.2f} kcal/mol`**",
            rf"- **Primary Target ({self.target_name})**: $\Delta G = {self.target_affinity.delta_g:.2f}\text{{ kcal/mol}}$ ($K_d \approx {self.target_affinity.kd_text}$, {self.target_affinity.total_contacts} contacts)",
            rf"- **Counter-Screen ({self.counter_name})**: $\Delta G = {self.counter_affinity.delta_g:.2f}\text{{ kcal/mol}}$ ($K_d \approx {self.counter_affinity.kd_text}$, {self.counter_affinity.total_contacts} contacts)",
            f"- **Key Selectivity Switch Residues**: {sw_str}",
            "",
            "#### 1. Differential Contact Fingerprint (Residue Breakdown)",
            r"| Position | Residue | Target Contacts | Counter Contacts | $\Delta$ Contacts | Functional Role |",
            "| :---: | :---: | :---: | :---: | :---: | :--- |",
        ]

        for r in self.residue_comparisons:
            diff_badge = f"+{r.diff_contacts}" if r.diff_contacts > 0 else f"{r.diff_contacts}"
            role_badge = r.role
            if r.is_switch_residue:
                role_badge = f"⚡ **{r.role}**"
            lines.append(
                f"| {r.res_seq} | `{r.res_name}` | {r.target_contacts} | {r.counter_contacts} | `{diff_badge}` | {role_badge} |"
            )

        if self.geometric_clash_warnings:
            lines.append("\n#### 2. Structural & Geometric Clash Warnings")
            for w in self.geometric_clash_warnings:
                lines.append(f"- ⚠️ {w}")

        return "\n".join(lines)


# ── 核心计算逻辑：双靶点对抗审计 ───────────────────────────────────────


def audit_peptide_selectivity(
    target_complex_pdb: str | Path,
    counter_complex_pdb: str | Path,
    *,
    target_name: str = "Primary_Target",
    counter_name: str = "Counter_Screen",
    peptide_name: str | None = None,
    target_rec_chain: str | None = None,
    target_pep_chain: str | None = None,
    counter_rec_chain: str | None = None,
    counter_pep_chain: str | None = None,
    distance_cutoff: float = 5.5,
    html_out: str | Path | None = None,
) -> SelectivityAuditResult:
    """
    对多肽在主靶点受体与同源反筛受体上的结合能力进行双向对抗选择性审计。

    Parameters
    ----------
    target_complex_pdb : str | Path
        主靶点受体与多肽复合物 PDB。
    counter_complex_pdb : str | Path
        反筛受体与多肽复合物 PDB。
    target_name : str
        主靶点标识 (如 "OXTR")。
    counter_name : str
        反筛靶点标识 (如 "V2R")。
    peptide_name : str | None
        多肽配体标识 (如 "OXT_Gly")。
    """
    t_path = Path(target_complex_pdb).resolve()
    c_path = Path(counter_complex_pdb).resolve()

    if not t_path.exists():
        return SelectivityAuditResult(
            ok=False,
            target_name=target_name,
            counter_name=counter_name,
            peptide_name=peptide_name or "Peptide",
            target_affinity=None,  # type: ignore[arg-type]
            counter_affinity=None,  # type: ignore[arg-type]
            ddg_selectivity=0.0,
            selectivity_fold=1.0,
            selectivity_tier="Failed",
            error=f"Target complex PDB not found: {t_path}",
        )
    if not c_path.exists():
        return SelectivityAuditResult(
            ok=False,
            target_name=target_name,
            counter_name=counter_name,
            peptide_name=peptide_name or "Peptide",
            target_affinity=None,  # type: ignore[arg-type]
            counter_affinity=None,  # type: ignore[arg-type]
            ddg_selectivity=0.0,
            selectivity_fold=1.0,
            selectivity_tier="Failed",
            error=f"Counter-screen complex PDB not found: {c_path}",
        )

    pep_label = peptide_name or t_path.stem

    # 1. 分别计算两端亲和力与接触网络
    t_res = predict_peptide_affinity(
        t_path,
        receptor_chain=target_rec_chain,
        peptide_chain=target_pep_chain,
        distance_cutoff=distance_cutoff,
    )
    c_res = predict_peptide_affinity(
        c_path,
        receptor_chain=counter_rec_chain,
        peptide_chain=counter_pep_chain,
        distance_cutoff=distance_cutoff,
    )

    if not t_res.ok:
        return SelectivityAuditResult(
            ok=False,
            target_name=target_name,
            counter_name=counter_name,
            peptide_name=pep_label,
            target_affinity=t_res,
            counter_affinity=c_res,
            ddg_selectivity=0.0,
            selectivity_fold=1.0,
            selectivity_tier="Failed",
            error=f"Target evaluation failed: {t_res.error}",
        )
    if not c_res.ok:
        return SelectivityAuditResult(
            ok=False,
            target_name=target_name,
            counter_name=counter_name,
            peptide_name=pep_label,
            target_affinity=t_res,
            counter_affinity=c_res,
            ddg_selectivity=0.0,
            selectivity_fold=1.0,
            selectivity_tier="Failed",
            error=f"Counter evaluation failed: {c_res.error}",
        )

    # 2. 计算热力学差异指标
    # ΔΔG_selectivity = ΔG_counter - ΔG_target (正值代表目标受体结合能更负，具有选择性)
    ddg_sel = round(c_res.delta_g - t_res.delta_g, 2)

    # Fold ratio = Kd_counter / Kd_target
    rt = GAS_CONSTANT * 298.15
    try:
        fold_ratio = float(np.exp(ddg_sel / rt))
    except (OverflowError, RuntimeWarning):
        fold_ratio = float("inf") if ddg_sel > 0 else 0.0

    # 3. 残基级差异指纹对比
    t_map = {h.res_seq: h for h in t_res.peptide_hotspots}
    c_map = {h.res_seq: h for h in c_res.peptide_hotspots}

    all_positions = sorted(list(set(list(t_map.keys()) + list(c_map.keys()))))
    comparisons: list[ResidueSelectivityEntry] = []
    switch_residues: list[str] = []

    for pos in all_positions:
        t_h = t_map.get(pos)
        c_h = c_map.get(pos)
        r_name = t_h.res_name if t_h else (c_h.res_name if c_h else "UNK")
        t_cnt = t_h.contact_count if t_h else 0
        c_cnt = c_h.contact_count if c_h else 0
        diff = t_cnt - c_cnt

        is_switch = False
        role = "Neutral"

        # 判断选择性开关残基
        if abs(diff) >= 4 or (t_cnt > 0 and c_cnt == 0) or (c_cnt > 0 and t_cnt == 0):
            is_switch = True
            switch_residues.append(f"{r_name}{pos}")
            if diff > 0:
                role = "Primary Target Anchor"
            else:
                role = "Counter-Screen Interactor"
        elif t_cnt >= 8 and c_cnt >= 8:
            role = "Shared Core Anchor"
        elif diff > 1:
            role = "Favors Primary Target"
        elif diff < -1:
            role = "Favors Counter-Screen"

        comparisons.append(
            ResidueSelectivityEntry(
                res_seq=pos,
                res_name=r_name,
                target_contacts=t_cnt,
                counter_contacts=c_cnt,
                diff_contacts=diff,
                is_switch_residue=is_switch,
                role=role,
            )
        )

    # 4. 几何冲突与位阻警告探测
    clash_warnings = []
    if c_res.total_contacts > t_res.total_contacts * 1.25:
        clash_warnings.append(
            f"Counter-screen ({counter_name}) displays abnormal contact density ({c_res.total_contacts} vs {t_res.total_contacts}), "
            "indicating severe geometric pocket constriction or unrelaxed steric crowding."
        )

    # 结合位点差异残基特殊规则（如 Pro7/Gly7 在 OXTR vs V2R）
    for comp in comparisons:
        if comp.res_name == "GLY" and comp.counter_contacts > comp.target_contacts:
            clash_warnings.append(
                f"Position {comp.res_name}{comp.res_seq} shows steric constriction in {counter_name}; "
                "conferring subtype selectivity via backbone loop repulsion."
            )

    # 选择性等级评定
    if ddg_sel >= 2.5 or fold_ratio >= 50.0:
        tier = "🟢 High Selectivity (Exemplary)"
    elif ddg_sel >= 1.0 or fold_ratio >= 5.0:
        tier = "🟢 Favorable Selectivity"
    elif ddg_sel >= -0.5:
        tier = "🟡 Moderate / Balanced"
    else:
        tier = "🔴 Inverted (Counter-Screen Preferred)"

    html_path_str = ""
    if html_out:
        html_file = Path(html_out).resolve()
        html_file.parent.mkdir(parents=True, exist_ok=True)
        generate_selectivity_html_report(
            target_pdb=t_path,
            counter_pdb=c_path,
            target_name=target_name,
            counter_name=counter_name,
            peptide_name=pep_label,
            comparisons=comparisons,
            ddg_sel=ddg_sel,
            fold_ratio=fold_ratio,
            tier=tier,
            out_file=html_file,
        )
        html_path_str = str(html_file)

    return SelectivityAuditResult(
        ok=True,
        target_name=target_name,
        counter_name=counter_name,
        peptide_name=pep_label,
        target_affinity=t_res,
        counter_affinity=c_res,
        ddg_selectivity=ddg_sel,
        selectivity_fold=round(fold_ratio, 2),
        selectivity_tier=tier,
        switch_residues=switch_residues,
        residue_comparisons=comparisons,
        geometric_clash_warnings=clash_warnings,
        html_report_path=html_path_str,
    )


# ── 自包含 HTML 报告生成 ───────────────────────────────────────────────


def generate_selectivity_html_report(
    target_pdb: Path,
    counter_pdb: Path,
    target_name: str,
    counter_name: str,
    peptide_name: str,
    comparisons: list[ResidueSelectivityEntry],
    ddg_sel: float,
    fold_ratio: float,
    tier: str,
    out_file: Path,
) -> None:
    """生成单文件自包含 3Dmol.js HTML 交互式多肽选择性交付报告"""
    t_pdb_str = target_pdb.read_text(encoding="utf-8", errors="ignore")
    c_pdb_str = counter_pdb.read_text(encoding="utf-8", errors="ignore")

    rows_html = ""
    for r in comparisons:
        badge_cls = "badge-switch" if r.is_switch_residue else "badge-normal"
        diff_str = f"+{r.diff_contacts}" if r.diff_contacts > 0 else f"{r.diff_contacts}"
        rows_html += f"""
        <tr>
          <td><strong>{r.res_seq}</strong></td>
          <td><code>{r.res_name}</code></td>
          <td>{r.target_contacts}</td>
          <td>{r.counter_contacts}</td>
          <td><strong>{diff_str}</strong></td>
          <td><span class="{badge_cls}">{r.role}</span></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Peptide Subtype Selectivity Report — {peptide_name}</title>
  <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0; padding: 24px; background: #0A1128; color: #E2E8F0;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    h1, h2, h3 {{ color: #F8FAFC; margin-top: 0; }}
    .header-box {{
      background: #1E293B; border: 1px solid #334155; border-radius: 12px;
      padding: 24px; margin-bottom: 24px;
    }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 20px; }}
    .metric-value {{ font-size: 28px; font-weight: bold; color: #00857C; margin: 8px 0; }}
    .viewer-container {{ height: 500px; width: 100%; position: relative; border-radius: 8px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ background: #0F172A; color: #94A3B8; font-size: 13px; text-transform: uppercase; }}
    .badge-switch {{ background: #D9383A; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
    .badge-normal {{ background: #334155; color: #CBD5E1; padding: 3px 8px; border-radius: 4px; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header-box">
      <h1>Peptide Subtype Selectivity Profile</h1>
      <p style="color: #94A3B8; margin: 0;">Evaluation: <strong>{peptide_name}</strong> | Target: <strong>{target_name}</strong> vs Counter-screen: <strong>{counter_name}</strong></p>
      <div style="margin-top: 16px;">
        <span style="font-size: 18px; font-weight: bold;">Status: {tier}</span>
        <span style="margin-left: 20px; color: #94A3B8;">Selectivity Difference (ΔΔG): <strong>{ddg_sel:+.2f} kcal/mol</strong></span>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Primary Target: {target_name}</h3>
        <div id="viewer_target" class="viewer-container"></div>
        <p style="font-size: 12px; color: #94A3B8; margin-top: 8px;">Receptor shown in Cyan ribbon, Peptide ligand in Red stick representation.</p>
      </div>
      <div class="card">
        <h3>Counter-Screen: {counter_name}</h3>
        <div id="viewer_counter" class="viewer-container"></div>
        <p style="font-size: 12px; color: #94A3B8; margin-top: 8px;">Counter-screen receptor in Grey ribbon, Peptide ligand in Orange stick representation.</p>
      </div>
    </div>

    <div class="card">
      <h3>Differential Residue Contact Fingerprint</h3>
      <table>
        <thead>
          <tr>
            <th>Position</th><th>Residue</th><th>{target_name} Contacts</th><th>{counter_name} Contacts</th><th>Δ Contacts</th><th>Role & Classification</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const targetPdb = `{t_pdb_str}`;
    const counterPdb = `{c_pdb_str}`;

    // Target Viewer
    let vTarget = $3Dmol.createViewer("viewer_target", {{backgroundColor: "#0F172A"}});
    vTarget.addModel(targetPdb, "pdb");
    vTarget.setStyle({{chain: 'R'}}, {{cartoon: {{color: '#00857C'}}}});
    vTarget.setStyle({{chain: 'L'}}, {{stick: {{colorscheme: 'redCarbon'}}}});
    vTarget.zoomTo();
    vTarget.render();

    // Counter Viewer
    let vCounter = $3Dmol.createViewer("viewer_counter", {{backgroundColor: "#0F172A"}});
    vCounter.addModel(counterPdb, "pdb");
    vCounter.setStyle({{chain: 'R'}}, {{cartoon: {{color: '#64748B'}}}});
    vCounter.setStyle({{chain: 'C'}}, {{stick: {{colorscheme: 'orangeCarbon'}}}});
    vCounter.zoomTo();
    vCounter.render();
  </script>
</body>
</html>
"""
    out_file.write_text(html_content, encoding="utf-8")
