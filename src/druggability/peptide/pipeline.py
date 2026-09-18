"""
druggability.peptide.pipeline — 多肽与中分子治疗管线端到端一键评估编排器 (Pipeline Orchestrator)

实现从多肽/靶点输入到全套结构可药性交付物的一键式流水线:
Stage 1: 结构获取/预测 (实验复合物 PDB 或 Boltz-2 预测 + CIF清洗)
Stage 2: 接触亲和力深度评估 (PRODIGY 界面接触网络, ΔG, Kd, Hotspots)
Stage 3: 突变热力学扫描 (全序列 Ala 扫描定位功能热点与修饰出射向量)
Stage 4: 亚型对抗选择性审计 (与同源反筛受体并行对抗, 差异指纹与位阻警告)
Stage 5: GPU 动力学系综 MM/GBSA (可选, A100 显式水采样消除单构象空洞伪影)
Stage 6: 一体化自包含交互式交付物生成 (Markdown + 3Dmol.js HTML)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from .affinity import PeptideAffinityResult, predict_peptide_affinity
from .ensemble_md import EnsembleMDResult, run_ensemble_mmgbsa
from .scan import (
    AlaScanResult,
    PositionScanResult,
    run_alanine_scanning,
    scan_position_mutations,
)
from .selectivity import SelectivityAuditResult, audit_peptide_selectivity

logger = logging.getLogger(__name__)


@dataclass
class CandidateAssessmentReport:
    """多肽候选分子端到端综合评估报告对象"""

    ok: bool
    peptide_name: str
    target_name: str
    complex_pdb: str
    affinity: PeptideAffinityResult
    boltz_iptm: float | None = None
    ala_scan: AlaScanResult | None = None
    position_scans: dict[int, PositionScanResult] = field(default_factory=dict)
    selectivity_audits: dict[str, SelectivityAuditResult] = field(default_factory=dict)
    ensemble_md: EnsembleMDResult | None = None
    verdict: str = ""
    recommendations: list[str] = field(default_factory=list)
    html_report_path: str = ""
    elapsed_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["affinity"] = self.affinity.to_dict() if self.affinity else None
        data["ala_scan"] = self.ala_scan.to_dict() if self.ala_scan else None
        data["position_scans"] = {
            pos: res.to_dict() for pos, res in self.position_scans.items()
        }
        data["selectivity_audits"] = {
            name: audit.to_dict() for name, audit in self.selectivity_audits.items()
        }
        data["ensemble_md"] = self.ensemble_md.to_dict() if self.ensemble_md else None
        return data

    def summary_markdown(self) -> str:
        """生成供 Agent 与科研决策交付的高保真全景 Markdown 报告"""
        if not self.ok:
            return f"**Peptide Candidate Assessment Failed**: {self.error}"

        aff = self.affinity
        lines = [
            f"# End-to-End Peptide Druggability Assessment: `{self.peptide_name}` on `{self.target_name}`",
            f"- **Overall Assessment Verdict**: **{self.verdict}**",
            rf"- **Predicted Affinity ($\Delta G$)**: **`{aff.delta_g:.2f} kcal/mol`** (Estimated $K_d \approx$ **`{aff.kd_text}`**)",
            f"- **Interface Total Contacts (ICs)**: **{aff.total_contacts}** ({aff.hbond_count_est} H-bonds, {aff.salt_bridge_count_est} Salt-bridges)",
            f"- **Structure Origin**: `{Path(self.complex_pdb).name}`"
            + (f" (Boltz-2 ipTM = `{self.boltz_iptm:.3f}`)" if self.boltz_iptm else ""),
            f"- **Total Assessment Runtime**: `{self.elapsed_seconds:.2f}s`",
            "",
            "## 1. Key Interface Hotspots & Functional Drivers",
        ]

        top_hotspots = aff.top_hotspots(4)
        for h in top_hotspots:
            rec_str = ", ".join(h.interacting_receptor_residues[:4])
            lines.append(f"- **`{h.label}`**: {h.contact_count} contacts (Interacting with: {rec_str})")

        if self.ala_scan and self.ala_scan.ok:
            lines.extend([
                "",
                "## 2. Mutational Tolerance & Permissive Exit Vectors",
                rf"- **Critical Hotspots ($\Delta\Delta G \ge 1.5\text{{ kcal/mol}}$)**: "
                + (", ".join([f"`{h}`" for h in self.ala_scan.critical_hotspots]) or "None"),
                rf"- **Tolerant Exit Vectors ($\Delta\Delta G \le 0.5\text{{ kcal/mol}}$, suitable for Lipidation/Stapling)**: "
                + (", ".join([f"`{v}`" for v in self.ala_scan.tolerant_exit_vectors]) or "None"),
            ])

        if self.selectivity_audits:
            lines.extend([
                "",
                "## 3. Cross-Reactivity & Subtype Selectivity Profile",
                r"| Counter-Screen | Selectivity Tier | $\Delta\Delta G_\text{selectivity}$ | Fold Preference | Key Switch Residues |",
                "| :--- | :---: | :---: | :---: | :--- |",
            ])
            for c_name, audit in self.selectivity_audits.items():
                if audit.ok:
                    sw_str = ", ".join([f"`{s}`" for s in audit.switch_residues[:3]]) or "None"
                    lines.append(
                        f"| **{c_name}** | {audit.selectivity_tier} | `{audit.ddg_selectivity:+.2f} kcal/mol` | {audit.selectivity_fold:.1f}x | {sw_str} |"
                    )

        if self.ensemble_md and self.ensemble_md.ok:
            lines.extend([
                "",
                "## 4. GPU-Accelerated Dynamic Stability (A100 Explicit Solvent MD)",
                rf"- **Ensemble $\langle \Delta G_\text{{bind}} \rangle$**: **`{self.ensemble_md.mean_delta_g:.2f} ± {self.ensemble_md.std_delta_g:.2f} kcal/mol`**",
                f"- **Peptide Backbone RMSD**: Mean = **`{self.ensemble_md.mean_pep_rmsd:.2f} Å`**, Final = **`{self.ensemble_md.final_pep_rmsd:.2f} Å`**",
                f"- **Dynamic Assessment**: "
                + ("🟢 **Stable Bound Conformation**" if self.ensemble_md.is_stable_binder else "🟡 **Dynamic Flexibility**"),
            ])

        if self.recommendations:
            lines.extend([
                "",
                "## 5. Actionable Chemistry & Engineering Recommendations",
            ])
            for rec in self.recommendations:
                lines.append(f"- 💡 {rec}")

        return "\n".join(lines)


# ── 一键流水线核心函数 ───────────────────────────────────────────────────


def assess_peptide_candidate(
    complex_pdb: str | Path,
    *,
    peptide_name: str | None = None,
    target_name: str = "Target",
    counter_complexes: dict[str, str | Path] | None = None,
    run_alanine_scan: bool = True,
    scan_positions: Sequence[int] | None = None,
    run_ensemble_md: bool = False,
    ensemble_md_length_ns: float = 1.0,
    gpu_id: int = 0,
    out_dir: str | Path | None = None,
    html_report: bool = True,
) -> CandidateAssessmentReport:
    """
    一键式执行多肽候选分子的全层级可药性评估。

    Parameters
    ----------
    complex_pdb : str | Path
        靶点受体与多肽候选分子的复合物 PDB。
    peptide_name : str | None
        多肽分子名称 (如 "OXT_Gly")。若为空则采用文件名 stem。
    target_name : str
        主靶点标识 (如 "OXTR")。
    counter_complexes : dict[str, str | Path] | None
        同源反筛受体复合物字典 (例如 {"V2R": "path/to/V2R_complex.pdb"})。
    run_alanine_scan : bool, default True
        是否执行全序列丙氨酸扫描 (定位热点残基与修饰出射向量)。
    scan_positions : Sequence[int] | None
        需要进一步扫描 20 种氨基酸替换矩阵的关键位点列表 (例如 [7, 8])。
    run_ensemble_md : bool, default False
        是否在 NVIDIA A100 GPU 上跑短轨迹动力学系综 MM/GBSA (1.0~2.0 ns)。
    gpu_id : int, default 0
        CUDA 设备索引。
    out_dir : str | Path | None
        结果与报告导出目录。
    html_report : bool, default True
        是否自动生成自包含交互式 3D HTML 报告。
    """
    t_start = time.time()
    pdb_path = Path(complex_pdb).resolve()
    if not pdb_path.exists():
        return CandidateAssessmentReport(
            ok=False,
            peptide_name=peptide_name or "Peptide",
            target_name=target_name,
            complex_pdb=str(complex_pdb),
            affinity=None,  # type: ignore[arg-type]
            error=f"Complex PDB file not found: {pdb_path}",
        )

    pep_label = peptide_name or pdb_path.stem

    if out_dir:
        work_dir = Path(out_dir).resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = pdb_path.parent / f"assessment_{pep_label}"
        work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting candidate assessment for %s on %s...", pep_label, target_name)

    # ── Stage 1: 接触亲和力深度评估 (Layer 1) ──
    logger.info("Executing Layer 1: PRODIGY Interface & Affinity profiling...")
    affinity_res = predict_peptide_affinity(pdb_path)
    if not affinity_res.ok:
        return CandidateAssessmentReport(
            ok=False,
            peptide_name=pep_label,
            target_name=target_name,
            complex_pdb=str(pdb_path),
            affinity=affinity_res,
            error=f"Affinity evaluation failed: {affinity_res.error}",
        )

    # ── Stage 2: 突变热力学与出射向量扫描 (Layer 2) ──
    ala_res = None
    if run_alanine_scan:
        logger.info("Executing Layer 2: In Silico Alanine Scanning...")
        ala_res = run_alanine_scanning(
            pdb_path,
            receptor_chain=affinity_res.receptor_chain,
            peptide_chain=affinity_res.peptide_chain,
        )

    pos_scans = {}
    if scan_positions:
        for pos in scan_positions:
            logger.info("Executing Layer 2: 20-AA Mutational matrix at position %d...", pos)
            p_res = scan_position_mutations(
                pdb_path,
                res_seq=pos,
                receptor_chain=affinity_res.receptor_chain,
                peptide_chain=affinity_res.peptide_chain,
            )
            if p_res.ok:
                pos_scans[pos] = p_res

    # ── Stage 3: 亚型对抗选择性审计 (Layer 4) ──
    selectivity_audits = {}
    if counter_complexes:
        for c_name, c_pdb in counter_complexes.items():
            logger.info("Executing Layer 4: Counter-screen audit against %s...", c_name)
            sel_html = work_dir / f"selectivity_{c_name}.html" if html_report else None
            audit_res = audit_peptide_selectivity(
                target_complex_pdb=pdb_path,
                counter_complex_pdb=Path(c_pdb),
                target_name=target_name,
                counter_name=c_name,
                peptide_name=pep_label,
                html_out=sel_html,
            )
            if audit_res.ok:
                selectivity_audits[c_name] = audit_res

    # ── Stage 4: GPU 动力学系综 MM/GBSA (Layer 3, 可选) ──
    ensemble_res = None
    if run_ensemble_md:
        logger.info("Executing Layer 3: GPU Short-MD Ensemble MM/GBSA on A100...")
        md_dir = work_dir / "ensemble_md"
        ensemble_res = run_ensemble_mmgbsa(
            complex_pdb=pdb_path,
            length_ns=ensemble_md_length_ns,
            gpu_id=gpu_id,
            out_dir=md_dir,
            receptor_chain=affinity_res.receptor_chain,
            peptide_chain=affinity_res.peptide_chain,
        )

    # ── Stage 5: 综合药理学裁决与工程建议生成 ──
    recommendations = []
    verdict = "🟢 Highly Potent & Favorable"

    if affinity_res.delta_g < -9.5:
        recommendations.append(
            f"High predicted target binding affinity (ΔG = {affinity_res.delta_g:.2f} kcal/mol, Kd ≈ {affinity_res.kd_text}); sufficient for nanomolar in vitro functional potency."
        )
    else:
        verdict = "🟡 Moderate Binding Affinity"
        recommendations.append(
            f"Moderate target binding affinity (ΔG = {affinity_res.delta_g:.2f} kcal/mol); optimize interface contacts to enhance potency."
        )

    if ala_res and ala_res.tolerant_exit_vectors:
        rec_vectors = ", ".join([f"`{v}`" for v in ala_res.tolerant_exit_vectors])
        recommendations.append(
            f"Identified permissive exit vectors at {rec_vectors}. These positions tolerate sidechain substitution and represent ideal anchors for fatty-acid acylation (protraction), PEGylation, or stapling."
        )

    if ala_res and ala_res.critical_hotspots:
        rec_hotspots = ", ".join([f"`{h}`" for h in ala_res.critical_hotspots])
        recommendations.append(
            f"Conserve primary pharmacophore core at {rec_hotspots} (ΔΔG ≥ 1.5 kcal/mol upon truncation); modifications here carry severe potency penalty risk."
        )

    if selectivity_audits:
        for c_name, aud in selectivity_audits.items():
            if "Inverted" in aud.selectivity_tier:
                recommendations.append(
                    f"Cross-reactivity warning on {c_name}: static model indicates counter-screen preference. Audit steric clash warnings or inspect dynamic loop repulsion before finalizing design."
                )
            elif "High" in aud.selectivity_tier or "Favorable" in aud.selectivity_tier:
                recommendations.append(
                    f"Favorable subtype selectivity verified against {c_name} (ΔΔG = {aud.ddg_selectivity:+.2f} kcal/mol, {aud.selectivity_fold:.1f}x preference)."
                )

    # ── Stage 6: 生成一体化 HTML 报告 ──
    html_path_str = ""
    if html_report:
        html_file = work_dir / f"{pep_label}_{target_name}_assessment_report.html"
        _render_candidate_html(
            complex_pdb=pdb_path,
            pep_label=pep_label,
            target_name=target_name,
            affinity_res=affinity_res,
            ala_res=ala_res,
            selectivity_audits=selectivity_audits,
            ensemble_res=ensemble_res,
            verdict=verdict,
            recommendations=recommendations,
            out_file=html_file,
        )
        html_path_str = str(html_file)

    elapsed = round(time.time() - t_start, 2)
    return CandidateAssessmentReport(
        ok=True,
        peptide_name=pep_label,
        target_name=target_name,
        complex_pdb=str(pdb_path),
        affinity=affinity_res,
        ala_scan=ala_res,
        position_scans=pos_scans,
        selectivity_audits=selectivity_audits,
        ensemble_md=ensemble_res,
        verdict=verdict,
        recommendations=recommendations,
        html_report_path=html_path_str,
        elapsed_seconds=elapsed,
    )


def _render_candidate_html(
    complex_pdb: Path,
    pep_label: str,
    target_name: str,
    affinity_res: PeptideAffinityResult,
    ala_res: AlaScanResult | None,
    selectivity_audits: dict[str, SelectivityAuditResult],
    ensemble_res: EnsembleMDResult | None,
    verdict: str,
    recommendations: list[str],
    out_file: Path,
) -> None:
    """生成单文件自包含的一体化多肽可药性 HTML 交付报告"""
    pdb_str = complex_pdb.read_text(encoding="utf-8", errors="ignore")

    hotspots_html = ""
    for h in affinity_res.top_hotspots(5):
        hotspots_html += f"<li><strong>`{h.label}`</strong>: {h.contact_count} contacts ({', '.join(h.interacting_receptor_residues[:4])})</li>"

    recs_html = "".join([f"<li>💡 {r}</li>" for r in recommendations])

    ala_table_html = ""
    if ala_res and ala_res.ok:
        for e in ala_res.entries:
            badge = "Critical Hotspot" if e.is_hotspot else ("Tolerant Exit Vector" if e.is_tolerant_exit_vector else "Neutral")
            ala_table_html += f"<tr><td>{e.res_seq}</td><td><code>{e.orig_res}</code></td><td>{e.mut_delta_g:.2f}</td><td>{e.ddg:+.2f}</td><td>{badge}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Peptide Druggability Dossier: {pep_label} ({target_name})</title>
  <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0; padding: 24px; background: #0A1128; color: #E2E8F0; line-height: 1.5;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header-box {{
      background: #1E293B; border: 1px solid #334155; border-radius: 12px;
      padding: 24px; margin-bottom: 24px;
    }}
    h1, h2, h3 {{ color: #F8FAFC; margin-top: 0; }}
    .badge-verdict {{ font-size: 18px; font-weight: bold; color: #00857C; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
    .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 20px; }}
    .viewer {{ width: 100%; height: 480px; position: relative; border-radius: 8px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }}
    th {{ background: #0F172A; color: #94A3B8; text-transform: uppercase; font-size: 12px; }}
    ul {{ padding-left: 20px; margin: 8px 0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header-box">
      <h1>Peptide Druggability & Structural Pharmacology Dossier</h1>
      <p style="color: #94A3B8; margin: 0;">Evaluation: <strong>{pep_label}</strong> on <strong>{target_name}</strong></p>
      <div style="margin-top: 16px;">
        <span class="badge-verdict">{verdict}</span>
        <span style="margin-left: 24px; color: #94A3B8;">Predicted Affinity (&Delta;G): <strong>{affinity_res.delta_g:.2f} kcal/mol</strong> (K<sub>d</sub> &approx; <strong>{affinity_res.kd_text}</strong>)</span>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>3D Structural Interaction View</h3>
        <div id="viewer_3d" class="viewer"></div>
        <p style="font-size: 12px; color: #94A3B8; margin-top: 8px;">Receptor shown in Cyan ribbon, Peptide ligand shown in Red stick representation.</p>
      </div>

      <div class="card">
        <h3>Primary Interface Hotspots</h3>
        <ul>{hotspots_html}</ul>
        <h3 style="margin-top: 20px;">Chemistry & Engineering Takeaways</h3>
        <ul>{recs_html}</ul>
      </div>
    </div>

    <div class="card">
      <h3>Alanine Scanning & Residue Permissiveness Map</h3>
      <table>
        <thead>
          <tr><th>Pos</th><th>WT</th><th>&Delta;G<sub>mut</sub> (kcal/mol)</th><th>&Delta;&Delta;G (kcal/mol)</th><th>Classification</th></tr>
        </thead>
        <tbody>
          {ala_table_html}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    let viewer = $3Dmol.createViewer("viewer_3d", {{backgroundColor: "#0F172A"}});
    viewer.addModel(`{pdb_str}`, "pdb");
    viewer.setStyle({{chain: '{affinity_res.receptor_chain}'}}, {{cartoon: {{color: '#00857C'}}}});
    viewer.setStyle({{chain: '{affinity_res.peptide_chain}'}}, {{stick: {{colorscheme: 'redCarbon'}}}});
    viewer.zoomTo();
    viewer.render();
  </script>
</body>
</html>
"""
    out_file.write_text(html, encoding="utf-8")
