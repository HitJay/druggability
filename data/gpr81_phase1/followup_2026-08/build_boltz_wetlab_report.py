#!/usr/bin/env python3
"""
GPR81 follow-up: three-layer compound report — Vina docking layer vs Boltz-2
structure/affinity layer vs wet-lab benchmark plan.

Layer 1 (Vina, DONE): multi-seed docking scores + region + tier A/B/C from
gpr81_compound_scorecard.json (8Z8A primary receptor).
Layer 2 (Boltz-2, PENDING): affinity_probability_binary + confidence_score +
ligand_iptm from data/boltz_results.csv (BioLib run via run_gpr81_boltz_45.py).
Boltz tier = data-driven tertiles of affinity probability (top = A), gated by
confidence_score (conf < 0.5 -> downgrade one tier). Thresholds marked
provisional until the 45-compound distribution is available.
Layer 3 (Wet-lab, PLANNED): benchmark protocol comparing each computational
layer against measured EC50/Emax (Spearman, tier confusion matrix, threshold
calibration); columns reserved in the table.

Output: gpr81_boltz_wetlab_report.html (self-contained; figures not needed).
"""
import csv, json, os
from pathlib import Path
import html as H

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
COMPOUNDS = sc["compounds"]

# ---- Boltz results (may be absent -> all PENDING)
boltz = {}
csv_path = DATA / "boltz_results.csv"
if csv_path.exists():
    for r in csv.DictReader(open(csv_path)):
        boltz[r["entry_id"]] = r


def esc(x):
    return H.escape(str(x)) if x is not None else ""


def boltz_tier(prob, conf):
    """Provisional rule: tertile cutoffs applied to the full set after the run;
    per-row here we only gate on confidence when prob is available."""
    if prob is None:
        return None
    if conf is not None and float(conf) < 0.5:
        return "C (low conf)"
    return None  # tertile assigned post-hoc


def fmt(x, nd=3):
    if x is None or x == "":
        return "—"
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def build_table():
    rows_html = []
    ranked = sorted([c for c in COMPOUNDS if c.get("potency_rank")],
                    key=lambda c: c["potency_rank"])
    unranked = [c for c in COMPOUNDS if not c.get("potency_rank")]

    def row_html(c):
        bid = c["entry_id"]
        b = boltz.get(bid, {})
        prob = b.get("boltz_affinity_probability_binary")
        conf = b.get("boltz_confidence_score")
        has_boltz = bool(prob or conf)
        # wet-lab columns: paper EC50 exists; measured EC50 reserved
        wetlab = f"{fmt(c.get('ec50_nM'), 3)} nM" if c.get("ec50_nM") is not None else "—"
        emax = f"{c['emax_pct']}%" if c.get("emax_pct") is not None else "—"
        v_tier = c.get("tier") or "—"
        # highlight: tier A rows light green, Boltz-ready rows with a marker
        return (
            f"<tr><td>{esc(c.get('potency_rank') or '—')}</td>"
            f"<td><b>{esc(bid)}</b></td><td>{esc(c['series'])}</td>"
            f"<td>{wetlab}</td><td>{emax}</td>"
            f"<td>{fmt(c.get('dock_8Z8A_best'))}</td><td>{esc(c.get('region_8Z8A') or '—')}</td><td>{v_tier}</td>"
            f"<td>{fmt(prob) if prob else 'PENDING'}</td>"
            f"<td>{fmt(conf) if conf else 'PENDING'}</td>"
            f"<td>{fmt(b.get('boltz_ligand_iptm')) if b.get('boltz_ligand_iptm') else 'PENDING'}</td>"
            f"<td>—</td><td>—</td>"
            f"<td class='stat'>{'Boltz run' if has_boltz else 'waiting'}</td></tr>"
        )

    for c in ranked:
        rows_html.append(row_html(c))
    for c in unranked:
        rows_html.append(row_html(c))
    return ("<table id='layers'><thead><tr>"
            "<th rowspan='2'>Rank</th><th rowspan='2'>ID</th><th rowspan='2'>Series</th>"
            "<th colspan='2'>Wet-lab (paper)</th>"
            "<th colspan='3'>Layer 1 · Vina (done)</th>"
            "<th colspan='3'>Layer 2 · Boltz-2 (pending run)</th>"
            "<th colspan='2'>Layer 3 · Wet-lab benchmark (planned)</th>"
            "<th rowspan='2'>Status</th></tr><tr>"
            "<th>EC50 nM</th><th>Emax</th>"
            "<th>8Z8A score</th><th>Region</th><th>Tier</th>"
            "<th>aff. prob</th><th>conf</th><th>ligand iptm</th>"
            "<th>measured EC50</th><th>consistency</th></tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody></table>")


def build_benchmark_plan():
    return """
<h3>Goal</h3>
<p>Calibrate the two computational layers (Vina docking score, Boltz-2 affinity probability)
against measured hGPR81 EC50/Emax so future tier assignments rest on experimentally
validated signals, not model assumptions.</p>
<h3>Protocol (proposed)</h3>
<ul>
<li><b>Compound subset:</b> full 45 if feasible, otherwise a stratified pick — all tier-A/B
leads (c03,c04,c07,c10,c11,c26,c28,c29,c30,c38...) + boundary compounds + 4 reference
ligands (CHBA, 3,5-DHBA, 3-OBA, lactate) as assay controls.</li>
<li><b>Assay:</b> functional hGPR81 agonism (cAMP inhibition or β-arrestin), EC50 + Emax;
GPR109A + GHS-R1a counterscreens for every measured analog.</li>
<li><b>Evaluation metrics:</b>
  <ul>
  <li>Spearman rank correlation of each layer's signal vs log10(EC50) — global and
  within acyl-urea / constrained / amide series.</li>
  <li>Tier confusion matrix: computed tier (A/B/C) vs experimental tertiles
  (potent &le; 10 nM / moderate 10–100 nM / weak &gt; 100 nM).</li>
  <li>Partial-agonist flagging: does either layer separate full (Emax &ge; 80%) from
  partial (Emax &lt; 60%) compounds? (c5–c8 are the natural test set.)</li>
  </ul></li>
<li><b>Threshold calibration:</b> if a layer's signal correlates with EC50, derive
operational cutoffs from the benchmark distribution; otherwise keep that layer as
binding-mode evidence only (current convention for Vina).</li>
<li><b>Deliverable:</b> this table updated with measured EC50/Emax + a benchmark
summary section (correlations, confusion matrix, calibration plot).</li>
</ul>
<h3>Layer 2 run instructions (Boltz-2)</h3>
{noformat}
# 1. log in to BioLib once (browser OAuth):
cd /das/user/QYJI/druggability && .venv/bin/biolib login
# 2. run the 45-compound Boltz-2 cross-validation (resumable, incremental CSV):
cd /das/user/QYJI/druggability/data/gpr81_phase1/followup_2026-08
/das/user/QYJI/druggability/.venv/bin/python run_gpr81_boltz_45.py --parallel 3
# 3. rebuild this report once results exist:
/das/user/QYJI/druggability/.venv/bin/python build_boltz_wetlab_report.py
{noformat}
<p class="muted">Boltz layer caveat: affinity_probability / ligand_iptm are structural-model
estimates, not measured affinities (same discipline as Vina scores). Boltz tier cutoffs are
provisional and will be set as tertiles of the observed distribution, gated by confidence_score.</p>
"""


def main():
    css = """
    body{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#f4f6f8;color:#222}
    .wrap{max-width:1400px;margin:0 auto;padding:18px}
    header{background:#0f3b5e;color:#fff;padding:22px 28px;border-radius:10px;margin-bottom:18px}
    header h1{margin:0 0 6px;font-size:25px}
    header p{margin:2px 0;color:#cfe0ef;font-size:13px}
    h2{color:#0f3b5e;border-bottom:2px solid #0f3b5e;padding-bottom:4px;margin-top:26px}
    h3{color:#14537e;margin:14px 0 6px}
    table{border-collapse:collapse;width:100%;background:#fff;font-size:11.5px}
    th,td{border:1px solid #d5dbe1;padding:3px 5px;text-align:left}
    th{background:#0f3b5e;color:#fff}
    th[colspan]{text-align:center}
    tr:nth-child(even){background:#f0f4f7}
    td.stat{color:#8a6d3b;font-style:italic}
    .note{background:#fff8e1;border-left:4px solid #f0ad4e;padding:10px 14px;border-radius:4px;font-size:13px}
    .fact{background:#e8f4fd;border-left:4px solid #2e86c1;padding:8px 12px;border-radius:4px;font-size:12.5px;margin:8px 0}
    ul{margin:4px 0 10px 20px;font-size:13.5px}
    li{margin:3px 0}
    code,pre{font-family:Consolas,monospace;font-size:12px}
    pre{background:#f0f3f5;border:1px solid #d5dbe1;border-radius:5px;padding:10px;overflow-x:auto}
    .muted{color:#777;font-size:12px}
    """
    table_html = build_table()
    plan_html = build_benchmark_plan()
    n_boltz = sum(1 for r in COMPOUNDS if boltz.get(r["entry_id"]) and
                  (boltz[r["entry_id"]].get("boltz_affinity_probability_binary") or
                   boltz[r["entry_id"]].get("boltz_confidence_score")))
    status_line = (f"Boltz-2 layer: {n_boltz}/45 compounds computed (PENDING until run)"
                   if n_boltz == 0 else f"Boltz-2 layer: {n_boltz}/45 compounds computed")

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>GPR81 (HCAR1) three-layer ranking — Vina · Boltz-2 · wet-lab benchmark plan</title>
<style>{css}</style></head><body><div class="wrap">
<header>
<h1>GPR81 (HCAR1) compound ranking — computational layers &amp; wet-lab benchmark</h1>
<p>45 compounds (39 Davidsson 2020 + 5 leads + lactate) · Layer 1 Vina docking (done) ·
Layer 2 Boltz-2 structure/affinity (pending) · Layer 3 wet-lab benchmark (planned)</p>
<p>Generated 2026-08-05 · audit files: gpr81_compound_scorecard.json · data/boltz_results.csv ·
run_gpr81_boltz_45.py · build_boltz_wetlab_report.py</p>
</header>

<h2>1 · Three-layer comparison table</h2>
<div class="note"><b>{esc(status_line)}.</b> Layer 1 (Vina) is complete; Layer 2 requires a
BioLib login + one script run (instructions in §3); Layer 3 columns fill in after wet-lab
measurements. Boltz values are structural-model estimates — never read them as measured
affinities.</div>
{table_html}

<h2>2 · Boltz-2 tier rule (provisional)</h2>
<ul>
<li>Primary signal: <b>affinity_probability_binary</b> (Boltz-2's binder probability).</li>
<li>Tier assignment: data-driven <b>tertiles</b> of the 45-compound distribution once the run
finishes — top tertile = A, middle = B, bottom = C; compounds with confidence_score &lt; 0.5
downgraded one tier (low structural confidence).</li>
<li>Supporting columns: confidence_score (structure confidence), ligand_iptm (interface
quality).</li>
<li>This rule mirrors the Vina tier transparency: thresholds are explicit and will be
re-calibrated against wet-lab data in Layer 3.</li>
</ul>

<h2>3 · Wet-lab benchmark plan</h2>
{plan_html}

<p class="muted" style="margin-top:16px">Companion files in the same folder:
gpr81_followup_report.html (full 46-pair pocket analysis, Vina layer) ·
gpr81_optimization_recommendations.md · run_gpr81_boltz_45.py (Layer 2 runner).</p>
</div></body></html>"""

    out = BASE / "gpr81_boltz_wetlab_report.html"
    out.write_text(html, encoding="utf-8")
    # self-check: tables must have non-empty cells
    import re
    for m in re.finditer(r"<table[^>]*>.*?</table>", html, re.S):
        cells = re.findall(r"<t[dh][^>]*>([^<]*)</t[dh]>", m.group(0))
        if not any(c.strip() for c in cells):
            raise SystemExit("FAIL: empty table")
    print("wrote", out, f"({out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
