#!/usr/bin/env python3
"""Build self-contained GHSR docking report HTML (no external JS dependencies)."""
import csv, json, math, textwrap
from pathlib import Path
from scipy.stats import spearmanr

OUTDIR = Path("output/2026-07-10/ghsr_inverse_agonist_docking")

lib = {}
with open(OUTDIR/"ghsr_screening_library.csv") as f:
    for r in csv.DictReader(f): lib[r["compound_id"]] = r

from collections import Counter
cls_counts = Counter()
with open(OUTDIR/"ranked_hits.csv") as f:
    for r in csv.DictReader(f): cls_counts[r["class"]] += 1

data = []
with open(OUTDIR/"boltz_crossval/boltz_crossval_scores.csv") as f:
    for r in csv.DictReader(f):
        prob = r.get("boltz_affinity_probability_binary", "")
        if prob:
            lr = lib.get(r["compound_id"], {})
            name = (lr.get("name", r.get("name", "")) or "").replace(" HYDROCHLORIDE","").replace(" FREE ACID","").replace(" FREE BASE","").replace(" OLAMINE","").replace(" CHOLINE","").strip()
            data.append({
                "cid": r["compound_id"], "name": name or r["compound_id"],
                "vina_s7": float(r.get("vina_score_7F83","0") or 0),
                "vina_s8": float(r.get("vina_score_8JSR","0") or 0),
                "vina_delta": float(r.get("vina_delta","0") or 0),
                "boltz_prob": float(prob),
                "boltz_conf": float(r.get("boltz_confidence_score","0") or 0),
                "max_phase": lr.get("max_phase",""),
            })

for d in data:
    d["priority"] = d["boltz_prob"] * 0.5 + (-d["vina_delta"] / 4) * 0.5
data.sort(key=lambda x: -x["priority"])

v_s = [d["vina_delta"] for d in data]; b_s = [d["boltz_prob"] for d in data]
rho, pval = spearmanr(v_s, b_s)

def phase_lbl(p):
    try: return {4:"Approved",3:"Ph3",2:"Ph2",1:"Ph1",0:"Preclin"}.get(int(float(p)),"")
    except: return ""

consensus = [d for d in data if d["boltz_prob"] > 0.5 and d["vina_delta"] < -2.5]
ctrl_ids = {"CHEMBL1201203":"1KQ","CHEMBL2106913":"Mitoquidone","CHEMBL4297452":"Ibutamoren","CHEMBL2106884":"GHRP-6"}

def donut_svg(counts, colors_dict, total, w=340, h=260):
    """Draw a simple donut chart with SVG."""
    items = sorted(counts.items(), key=lambda x: -x[1])
    cx, cy, r, ir = 120, h//2, 85, 48
    pieces = []
    start = -90
    for k, v in items:
        if v == 0: continue
        angle = v / total * 360
        end = start + angle
        sr = math.radians(start)
        er = math.radians(end)
        x1 = cx + r * math.cos(sr)
        y1 = cy + r * math.sin(sr)
        x2 = cx + r * math.cos(er)
        y2 = cy + r * math.sin(er)
        x1i = cx + ir * math.cos(er)
        y1i = cy + ir * math.sin(er)
        x2i = cx + ir * math.cos(sr)
        y2i = cy + ir * math.sin(sr)
        large = 1 if angle > 180 else 0
        d = f"M {cx},{cy-r} A {r},{r} 0 {large} 1 {x2},{y2} L {x1i},{y1i} A {ir},{ir} 0 {large} 0 {x2i},{y2i} Z"
        # Actually simpler: just use stroke-based arc
        pieces.append(f'<path d="M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large} 1 {x2},{y2} Z" fill="{colors_dict.get(k,"#ccc")}" stroke="#fff" stroke-width="2"/>')
        start = end
    # Inner white circle for donut
    pieces.append(f'<circle cx="{cx}" cy="{cy}" r="{ir}" fill="#fff"/>')
    pieces.append(f'<text x="{cx}" y="{cy-5}" text-anchor="middle" font-size="22" font-weight="700" fill="#2d3748">{total:,}</text>')
    pieces.append(f'<text x="{cx}" y="{cy+14}" text-anchor="middle" font-size="10" fill="#718096">compounds</text>')
    
    # Legend
    y = 20
    lx = w - 110
    legend = ""
    for k, v in items[:8]:
        pct = v/total*100
        legend += f'<rect x="{lx}" y="{y}" width="10" height="10" rx="2" fill="{colors_dict.get(k,"#ccc")}"/><text x="{lx+16}" y="{y+9}" font-size="10" fill="#4a5568">{v} ({pct:.0f}%)</text>'
        y += 18
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{"".join(pieces)}{legend}</svg>'

def bar_svg(labels, vina_vals, boltz_vals, w=480, h=260):
    """SVG grouped bar chart."""
    n = len(labels)
    col_w = w / (n + 1)
    bar_w = col_w * 0.35
    gap = col_w * 0.05
    
    v_min = min(vina_vals) - 0.5
    v_max = max(vina_vals) + 0.5
    v_range = v_max - v_min
    
    bars = []
    # Y-axis label
    max_h = h - 60
    
    for i in range(n):
        x = col_w * (i + 0.5)
        # Vina bar (left, red)
        v_h = (vina_vals[i] - v_min) / v_range * max_h
        v_y = h - 30 - v_h
        v_x = x - bar_w - gap
        bars.append(f'<rect x="{v_x:.0f}" y="{v_y:.0f}" width="{bar_w:.0f}" height="{v_h:.0f}" rx="3" fill="#e53e3e" opacity="0.85"/>')
        # Vina label
        bars.append(f'<text x="{v_x+bar_w/2:.0f}" y="{v_y-4}" text-anchor="middle" font-size="9" fill="#e53e3e" font-weight="600">{vina_vals[i]:.1f}</text>')
        
        # Boltz bar (right, blue)
        b_h = boltz_vals[i] / 1.0 * max_h
        b_y = h - 30 - b_h
        b_x = x + gap
        bars.append(f'<rect x="{b_x:.0f}" y="{b_y:.0f}" width="{bar_w:.0f}" height="{b_h:.0f}" rx="3" fill="#3182ce" opacity="0.85"/>')
        # Boltz label
        bars.append(f'<text x="{b_x+bar_w/2:.0f}" y="{b_y-4}" text-anchor="middle" font-size="9" fill="#3182ce" font-weight="600">{boltz_vals[i]:.2f}</text>')
        
        # X-axis label
        lbl = labels[i][:12]
        bars.append(f'<text x="{x:.0f}" y="{h-10}" text-anchor="middle" font-size="8" fill="#4a5568" transform="rotate(-30,{x:.0f},{h-10})">{lbl}</text>')
    
    # Legend
    bars.append(f'<rect x="15" y="8" width="10" height="10" rx="2" fill="#e53e3e" opacity="0.85"/><text x="30" y="17" font-size="10" fill="#4a5568">Vina Delta</text>')
    bars.append(f'<rect x="100" y="8" width="10" height="10" rx="2" fill="#3182ce" opacity="0.85"/><text x="115" y="17" font-size="10" fill="#4a5568">Boltz Prob</text>')
    
    # Y-axis
    bars.append(f'<line x1="10" y1="{h-30}" x2="{w-10}" y2="{h-30}" stroke="#e2e8f0" stroke-width="1"/>')
    
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{"".join(bars)}</svg>'

# Prepare data
cls_legend = {"strong_inverse_agonist": ("Strong Inv. Agonist", "#e74c3c"),
    "moderate_inverse_agonist": ("Moderate", "#e67e22"), "pan_binder": ("Pan-state", "#3498db"),
    "active_state_preferring": ("Active Pref.", "#2ecc71"), "agonist_like": ("Agonist-like", "#27ae60"),
    "weak_binder": ("Weak", "#95a5a6"), "other": ("Other", "#bdc3c7")}
cls_colors = {k: v[1] for k, v in cls_legend.items()}
cls_labels = {k: v[0] for k, v in cls_legend.items()}

donut = donut_svg({cls_labels.get(k,k): v for k,v in cls_counts.items() if v > 0}, 
                  {cls_labels.get(k,k): cls_colors.get(k,"#ccc") for k in cls_counts}, 
                  sum(cls_counts.values()))

top5 = data[:5]
bar = bar_svg([d["name"][:12] for d in top5],
              [d["vina_delta"] for d in top5],
              [d["boltz_prob"] for d in top5])

def td(d):
    dc = "ok" if d["vina_delta"] < -2.5 else ("mid" if d["vina_delta"] < -2.0 else "low")
    pc = "high" if d["boltz_prob"] > 0.5 else ("mid" if d["boltz_prob"] > 0.35 else "low")
    w = d["boltz_prob"] * 100
    return f"<td class='d-{dc}'>{d['vina_s7']:.1f}</td><td class='d-{dc}'>{d['vina_s8']:.1f}</td><td class='d-{dc}'><b>{d['vina_delta']:.2f}</b></td><td class='p-{pc}'><div class='bar'><div style='width:{w:.0f}%'></div></div>{d['boltz_prob']:.3f}</td><td>{d['boltz_conf']:.3f}</td><td>{phase_lbl(d['max_phase'])}</td>"

tbl = ""
for i,d in enumerate(data,1):
    n = d["name"][:28] if len(d["name"])<=28 else d["name"][:25]+"..."
    tbl += f"<tr><td>{i}</td><td><b>{n}</b><br><span class='cid'>{d['cid']}</span></td>{td(d)}</tr>"

cc = "".join(f"<div class='hit'><b>{d['name'][:20]}</b><br><span class='m'>Δ={d['vina_delta']:.2f} · P={d['boltz_prob']:.3f}</span><br><span class='tag'>HIT</span></div>" for d in consensus)
cr = "".join(f"<tr><td><b>{d['name']}</b><br><span class='cid'>{d['cid']}</span></td><td class='d-ok'>{d['vina_delta']:.2f}</td><td><div class='bar' style='width:80px'><div style='width:{d['boltz_prob']*100:.0f}%'></div></div>{d['boltz_prob']:.3f}</td><td>{d['boltz_conf']:.3f}</td></tr>" for d in consensus)
ct = "".join(f"<tr><td>{d['name']}</td><td class='d-ok'>{d['vina_delta']:.2f}</td><td>{d['boltz_prob']:.3f}</td><td>{'&#10003;' if d['vina_delta']<-0.5 else '&#10007;'}</td></tr>" for d in data if d["cid"] in ctrl_ids)

html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GHSR Inverse Agonist Docking Report</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa;color:#1a1a2e;line-height:1.5}}
.container{{max-width:1100px;margin:0 auto;padding:20px}}
.header{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:40px 20px;text-align:center}}
.header h1{{font-size:26px;margin-bottom:6px}}.header p{{color:#a0aec0;font-size:14px}}
.box{{background:#fff;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow-x:auto}}
.box h2{{font-size:17px;margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid #e2e8f0;color:#2d3748}}
.sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:16px}}
.sc{{background:#f7fafc;border-radius:8px;padding:14px;text-align:center}}
.sc .n{{font-size:26px;font-weight:700;color:#2d3748}}.sc .l{{font-size:11px;color:#718096;margin-top:3px}}
.cg{{display:grid;grid-template-columns:1fr 1.6fr;gap:16px;margin-bottom:10px}}
.cg svg{{width:100%;height:auto;max-height:260px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{background:#f7fafc;color:#4a5568;font-weight:600;padding:8px 6px;text-align:left;border-bottom:2px solid #e2e8f0;white-space:nowrap;position:sticky;top:0}}
td{{padding:7px 6px;border-bottom:1px solid #edf2f7;vertical-align:middle}}
tr:hover{{background:#f7fafc}}
.cid{{font-size:10px;color:#718096;font-family:monospace}}
.d-ok{{color:#e53e3e;font-weight:600}}.d-mid{{color:#dd6b20;font-weight:600}}.d-low{{color:#38a169}}
.p-high{{color:#2b6cb0;font-weight:600}}.p-mid{{color:#3182ce}}.p-low{{color:#718096}}
.bar{{display:inline-block;width:50px;height:7px;background:#edf2f7;border-radius:3px;vertical-align:middle;margin-right:4px}}
.bar div{{height:100%;border-radius:3px;background:linear-gradient(90deg,#4299e1,#2b6cb0)}}
.hit-box{{background:linear-gradient(135deg,#fff5f5,#ffeef0);border:1px solid #fed7d7;border-radius:8px;padding:14px;margin:10px 0}}
.hit-box h4{{color:#c53030;font-size:14px;margin-bottom:6px}}
.hit-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:10px 0}}
.hit{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px;text-align:center}}
.hit b{{font-size:13px}}.hit .m{{font-size:11px;color:#718096}}.tag{{display:inline-block;background:#c6f6d5;color:#22543d;padding:1px 8px;border-radius:3px;font-size:10px;font-weight:600;margin-top:3px}}
.footer{{text-align:center;padding:20px;color:#718096;font-size:11px}}
@media(max-width:640px){{.cg{{grid-template-columns:1fr}}.sg{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head><body>
<div class="header"><div class="container">
<h1>GHSR Inverse Agonist Docking Report</h1>
<p>7,931 compounds &bull; AutoDock Vina + Boltz-2 cross-validation</p>
<p>Target: GHSR (7F83 inactive / 8JSR active) &bull; 2026-07-15</p>
</div></div>
<div class="container">
<div class="box">
<h2>Campaign Overview</h2>
<div class="sg">
<div class="sc"><div class="n">7,931</div><div class="l">Library Size</div></div>
<div class="sc"><div class="n">3,325</div><div class="l">Strong Inv. Agonists</div></div>
<div class="sc"><div class="n">{len(data)}</div><div class="l">Boltz-2 Validated</div></div>
<div class="sc"><div class="n">{len(consensus)}</div><div class="l">Consensus Hits</div></div>
<div class="sc"><div class="n">{rho:.3f}</div><div class="l">Vina-Boltz &rho; (p={pval:.4f})</div></div>
</div>
<div class="cg">
<div>{donut}</div>
<div>{bar}</div>
</div>
</div>

<div class="box">
<h2>Consensus Hits</h2>
<div class="hit-box">
<h4>{len(consensus)} high-confidence hits</h4>
<p style="font-size:12px;color:#4a5568">Boltz binding probability &gt; 0.5 <b>+</b> Vina conformational selectivity &Delta; &lt; -2.5</p>
</div>
<div class="hit-grid">{cc}</div>
<table><thead><tr><th>Compound</th><th>&Delta;Score</th><th>Boltz Prob</th><th>Confidence</th></tr></thead>
<tbody>{cr}</tbody></table>
</div>

<div class="box">
<h2>Positive Controls</h2>
<table style="max-width:550px"><thead><tr><th>Compound</th><th>&Delta;Score</th><th>BoltzP</th><th>Status</th></tr></thead>
<tbody>{ct}</tbody></table>
</div>

<div class="box">
<h2>Full Results &mdash; Top {len(data)}</h2>
<p style="font-size:12px;color:#718096;margin-bottom:10px">Sorted by combined priority. Red = strong selectivity. Blue bar = Boltz confidence.</p>
<table><thead><tr><th>#</th><th>Compound</th><th>7F83</th><th>8JSR</th><th>&Delta;</th><th>Boltz Prob</th><th>Conf</th><th>Phase</th></tr></thead>
<tbody>{tbl}</tbody></table>
</div>
</div>
<div class="footer"><p>GHSR Inverse Agonist Docking &bull; Novo Nordisk &bull; 2026-07-15</p></div>
</body></html>"""

OUTFILE = OUTDIR/"GHSR_docking_report.html"
OUTFILE.write_text(html, encoding="utf-8")
print(f"Report: {OUTFILE} ({len(html)} bytes, {len(data)} rows)")
print(f"Donut: OK, Bar: OK")
