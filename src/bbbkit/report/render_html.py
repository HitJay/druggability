"""
bbbkit.report.render_html — Jinja2 HTML 报告渲染

自包含 (模板内嵌，不依赖外部文件)。包含:
  - 执行摘要 (LLM 叙述)
  - 二维定位图 (validation × tractability，纯 Python 生成 inline SVG，零额外依赖)
  - 对比矩阵表
  - 每靶卡片 (LLM 叙述 + 维度明细)
"""

from __future__ import annotations

import datetime as _dt
import html
from typing import Any

import markdown as _md
from jinja2 import Environment, select_autoescape

# ─── 二维定位 SVG (validation × tractability) ────────────────────────


def _portfolio_svg(records: list[dict[str, Any]], width: int = 720, height: int = 460) -> str:
    """纯 Python 生成散点 SVG: x=tractability_best, y=genetics_score。"""
    pad = 60
    x0, y0 = pad, height - pad
    x1, y1 = width - pad, pad
    plot_w, plot_h = x1 - x0, y0 - y1

    def sx(v: float) -> float:
        return x0 + plot_w * max(0.0, min(1.0, v))

    def sy(v: float) -> float:
        return y0 - plot_h * max(0.0, min(1.0, v))

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        'font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="12">'
    ]
    # 象限背景 (阈值 0.55 / 0.6)
    xt, yt = sx(0.6), sy(0.55)
    parts.append(f'<rect x="{xt}" y="{y1}" width="{x1-xt}" height="{yt-y1}" fill="#e8f5e9"/>')   # 右上 Priority
    parts.append(f'<rect x="{x0}" y="{y1}" width="{xt-x0}" height="{yt-y1}" fill="#fff8e1"/>')   # 左上 Hard
    parts.append(f'<rect x="{xt}" y="{yt}" width="{x1-xt}" height="{y0-yt}" fill="#e3f2fd"/>')   # 右下 Tractable
    parts.append(f'<rect x="{x0}" y="{yt}" width="{xt-x0}" height="{y0-yt}" fill="#fafafa"/>')   # 左下 Watch
    # 轴
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#999"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#999"/>')
    parts.append(f'<text x="{(x0+x1)/2}" y="{height-18}" text-anchor="middle" fill="#555">Tractability (可药性，最优模态分) →</text>')
    parts.append(f'<text x="18" y="{(y0+y1)/2}" text-anchor="middle" fill="#555" transform="rotate(-90 18 {(y0+y1)/2})">Genetics validation (遗传学验证) →</text>')
    # 象限标签
    parts.append(f'<text x="{xt+8}" y="{y1+16}" fill="#2e7d32">Priority</text>')
    parts.append(f'<text x="{x0+8}" y="{y1+16}" fill="#f9a825">Hard but worth it</text>')
    parts.append(f'<text x="{xt+8}" y="{y0-8}" fill="#1565c0">Tractable but verify</text>')
    parts.append(f'<text x="{x0+8}" y="{y0-8}" fill="#999">Watch</text>')
    # 数据点
    for r in records:
        gx, gy = r.get("tractability_best"), r.get("genetics_score")
        if gx is None or gy is None:
            continue
        cx, cy = sx(float(gx)), sy(float(gy))
        color = {"small_molecule": "#1565c0", "antibody": "#c62828", "protac": "#6a1b9a"}.get(
            r.get("best_modality", ""), "#555"
        )
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{color}" fill-opacity="0.75" stroke="#fff"/>')
        parts.append(f'<text x="{cx+10:.1f}" y="{cy+4:.1f}" fill="#222" font-weight="600">{html.escape(str(r.get("gene_name","")))}</text>')
    # 图例
    legend = [("small_molecule", "#1565c0", "小分子"), ("antibody", "#c62828", "抗体"), ("protac", "#6a1b9a", "PROTAC")]
    lx = x1 - 130
    for i, (_, c, lbl) in enumerate(legend):
        ly = y1 + 6 + i * 18
        parts.append(f'<circle cx="{lx}" cy="{ly}" r="6" fill="{c}"/>')
        parts.append(f'<text x="{lx+12}" y="{ly+4}" fill="#444">{lbl}</text>')
    parts.append("</svg>")
    return "".join(parts)


# ─── HTML 模板 ───────────────────────────────────────────────────────

_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{{ title }}</title>
<style>
  :root { --fg:#1a1a1a; --muted:#666; --line:#e3e3e3; --accent:#1565c0; }
  * { box-sizing: border-box; }
  body { margin:0; color:var(--fg); font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif; line-height:1.6; background:#f7f8fa; }
  .wrap { max-width:980px; margin:0 auto; padding:32px 24px 80px; }
  header h1 { margin:0 0 4px; font-size:26px; }
  .sub { color:var(--muted); font-size:14px; }
  h2 { margin-top:40px; padding-bottom:6px; border-bottom:2px solid var(--accent); font-size:20px; }
  .card { background:#fff; border:1px solid var(--line); border-radius:10px; padding:20px 22px; margin:18px 0; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .summary { background:#fff; border-left:4px solid var(--accent); }
  table { width:100%; border-collapse:collapse; font-size:13px; background:#fff; }
  th, td { padding:8px 10px; border-bottom:1px solid var(--line); text-align:left; }
  th { background:#f0f3f7; font-weight:600; }
  tr:hover td { background:#fafbfc; }
  .badge { display:inline-block; padding:2px 10px; border-radius:12px; font-size:12px; font-weight:600; }
  .b-priority { background:#e8f5e9; color:#2e7d32; }
  .b-hard { background:#fff8e1; color:#f9a825; }
  .b-tract { background:#e3f2fd; color:#1565c0; }
  .b-watch { background:#eee; color:#777; }
  .b-other { background:#f3e5f5; color:#6a1b9a; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:12px 0; }
  .metric { background:#f7f9fb; border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
  .metric .k { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
  .metric .v { font-size:18px; font-weight:600; }
  .narr { margin-top:10px; }
  .narr p { margin:6px 0; }
  .fig { text-align:center; margin:16px 0; }
  footer { margin-top:48px; color:var(--muted); font-size:12px; text-align:center; }
  code { background:#f0f3f7; padding:1px 5px; border-radius:4px; font-size:.92em; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{{ title }}</h1>
    <div class="sub">生成日期 {{ date }} · {{ records|length }} 个靶点 · {{ llm_status }}</div>
  </header>

  <h2>执行摘要</h2>
  <div class="card summary"><div class="narr">{{ exec_summary_html|safe }}</div></div>

  <h2>二维定位 (遗传学验证 × 可药性)</h2>
  <div class="card"><div class="fig">{{ portfolio_svg|safe }}</div></div>

  <h2>对比矩阵</h2>
  <div class="card" style="overflow-x:auto;">
  <table>
    <thead><tr>
      <th>靶点</th><th>GWAS</th><th>类别</th><th>genetics</th><th>tract(best)</th>
      <th>模态</th><th>ligand</th><th>structure</th><th>overall</th><th>结论</th>
    </tr></thead>
    <tbody>
    {% for r in records %}
      <tr>
        <td><b>{{ r.gene_name }}</b><br/><code>{{ r.gene_id }}</code></td>
        <td>{{ r.gwas_trait }}</td>
        <td>{{ r.target_class or '—' }}</td>
        <td>{{ r.genetics_score if r.genetics_score is not none else '—' }}</td>
        <td>{{ r.tractability_best if r.tractability_best is not none else '—' }}</td>
        <td>{{ modality_label(r.best_modality) }}</td>
        <td>{{ r.ligandability_score if r.ligandability_score is not none else '—' }}
            {% if r.n_known_ligands is not none %}<span class="sub">({{ r.n_known_ligands }})</span>{% endif %}</td>
        <td>{{ r.structure_score if r.structure_score is not none else '—' }}</td>
        <td><b>{{ r.overall_score if r.overall_score is not none else '—' }}</b></td>
        <td>{{ verdict_badge(r.recommendation)|safe }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  </div>

  <h2>逐靶分析</h2>
  {% for r in records %}
  <div class="card">
    <h3 style="margin:0 0 4px;">{{ r.gene_name }} · <span class="sub">{{ r.gene_id }}</span> {{ verdict_badge(r.recommendation)|safe }}</h3>
    <div class="sub">GWAS: {{ r.gwas_trait }} ({{ r.gwas_trait_label }}) · 类别: {{ r.target_class or '—' }} · top 疾病: {{ r.top_disease or '—' }}</div>
    <div class="grid">
      <div class="metric"><div class="k">Genetics</div><div class="v">{{ r.genetics_score if r.genetics_score is not none else '—' }}</div></div>
      <div class="metric"><div class="k">Tractability</div><div class="v">{{ r.tractability_best if r.tractability_best is not none else '—' }}</div></div>
      <div class="metric"><div class="k">最优模态</div><div class="v" style="font-size:14px;">{{ modality_label(r.best_modality) }}</div></div>
      <div class="metric"><div class="k">Ligandability</div><div class="v">{{ r.ligandability_score if r.ligandability_score is not none else '—' }}</div></div>
      <div class="metric"><div class="k">Overall</div><div class="v">{{ r.overall_score if r.overall_score is not none else '—' }}</div></div>
    </div>
    <div class="narr">{{ r._narrative_html|safe }}</div>
  </div>
  {% endfor %}

  <footer>bbbkit · druggability deep assessment · {{ date }}</footer>
</div>
</body>
</html>
"""


def _modality_label(m: str | None) -> str:
    return {"small_molecule": "小分子", "antibody": "抗体", "protac": "PROTAC/降解剂",
            "unknown": "未知", "(offline)": "—"}.get(m or "", m or "—")


def _verdict_badge(rec: str | None) -> str:
    rec = rec or ""
    cls = "b-other"
    if rec.startswith("Priority"):
        cls = "b-priority"
    elif rec.startswith("Hard"):
        cls = "b-hard"
    elif rec.startswith("Tractable"):
        cls = "b-tract"
    elif rec.startswith("Watch"):
        cls = "b-watch"
    short = rec.split("—")[0].strip() or "—"
    return f'<span class="badge {cls}">{html.escape(short)}</span>'


def render_html(
    records: list[dict[str, Any]],
    *,
    title: str = "靶点深度可药性评估报告",
    exec_summary: str = "",
    llm_status: str = "",
) -> str:
    """渲染完整 HTML 报告字符串。records 中可含 `_narrative` (markdown 叙述)。"""
    env = Environment(autoescape=select_autoescape(["html"]))
    env.globals["modality_label"] = _modality_label
    env.globals["verdict_badge"] = _verdict_badge
    tmpl = env.from_string(_TEMPLATE)

    # 把 markdown 叙述转 HTML
    enriched = []
    for r in records:
        rr = dict(r)
        narr = rr.get("_narrative", "")
        rr["_narrative_html"] = _md.markdown(narr) if narr else ""
        enriched.append(rr)

    return tmpl.render(
        title=title,
        date=_dt.date.today().isoformat(),
        records=enriched,
        exec_summary_html=_md.markdown(exec_summary) if exec_summary else "",
        portfolio_svg=_portfolio_svg(records),
        llm_status=llm_status,
    )
