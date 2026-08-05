#!/usr/bin/env python3
"""
GPR81 follow-up: build the consolidated self-contained HTML report.

Sections:
  1. Scope & provenance (45 compounds / 46 ligand-receptor pairs accounting)
  2. Overall ranking (scorecard, tier A/B/C)
  3. Pocket analysis: 46 pair cards (embedded figure + binding parameters)
  4. Optimization & development recommendations (condensed)
  5. Methodology & caveats

All images are base64-inlined so the single .html file is portable.
Build-time self-check: every rendered table must contain non-empty cells.
Output: gpr81_followup_report.html
"""
import base64, json, html as H
from pathlib import Path

BASE = Path(__file__).resolve().parent
FIGDIR = BASE / "figures"

sc = json.load(open(BASE / "gpr81_compound_scorecard.json"))
pairs = json.load(open(BASE / "data/gpr81_pocket_analysis_pairs.json"))["pairs"]

COMPOUNDS = sc["compounds"]
# read recommendations MD for section 4
rec_md = (BASE / "gpr81_optimization_recommendations.md").read_text(encoding="utf-8")


def esc(x):
    return H.escape(str(x)) if x is not None else ""


def img_b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


# ---------------------------------------------------------------- tables
def build_ranking_table():
    ranked = sorted([c for c in COMPOUNDS if c.get("potency_rank")],
                    key=lambda c: c["potency_rank"])
    unranked = [c for c in COMPOUNDS if not c.get("potency_rank")]
    rows_html = []
    for c in ranked:
        tier_cls = {"A": "tierA", "B": "tierB", "C": "tierC"}.get(c["tier"], "")
        rows_html.append(
            "<tr class='%s'><td>%s</td><td><b>%s</b></td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                tier_cls, esc(c.get("potency_rank")), esc(c["entry_id"]),
                esc(c["series"]),
                ("%.3g" % c["ec50_nM"]) if c.get("ec50_nM") is not None else "—",
                esc(c.get("emax_pct") or "—"),
                ("%.1f" % c["gpr109a_fold"]) if c.get("gpr109a_fold") is not None else "—",
                ("%.0f" % c["ghsr_fold"]) if c.get("ghsr_fold") is not None else "—",
                ("%.1f" % c["lle"]) if c.get("lle") is not None else "—",
                ("%.2f" % c["dock_8Z8A_best"]) if c.get("dock_8Z8A_best") is not None else "—",
                esc(c.get("region_8Z8A") or "—"),
                ("%.2f" % c["dock_9KT9_best"]) if c.get("dock_9KT9_best") is not None else "—",
                esc(c["tier"])))
    for c in unranked:
        rows_html.append(
            "<tr><td>—</td><td><b>%s</b></td><td>%s</td><td>—</td><td>%s</td><td>—</td>"
            "<td>—</td><td>—</td><td>—</td><td>%s</td><td>%s</td><td>%s</td><td>—</td></tr>" % (
                esc(c["entry_id"]), esc(c["series"]),
                esc(c.get("ec50_source") or "reference ligand (no potency assay)"),
                ("%.2f" % c["dock_8Z8A_best"]) if c.get("dock_8Z8A_best") is not None else "—",
                esc(c.get("region_8Z8A") or "—"),
                ("%.2f" % c["dock_9KT9_best"]) if c.get("dock_9KT9_best") is not None else "—"))
    return ("<table id='ranking'><thead><tr><th>Rank</th><th>ID</th><th>Series</th>"
            "<th>EC50 nM</th><th>Emax%%</th><th>GPR109A x</th><th>GHSR x</th><th>LLE</th>"
            "<th>8Z8A score</th><th>8Z8A region</th><th>9KT9 score</th><th>Tier</th></tr></thead>"
            "<tbody>%s</tbody></table>" % "\n".join(rows_html))


def build_pair_cards():
    cards = []
    for pr in pairs:
        fig = FIGDIR / f"pocket_{pr['pair_id']}.png"
        img_html = (f"<img src='{img_b64(fig)}' alt='{esc(pr['pair_id'])}' "
                    f"style='width:100%;border:1px solid #ddd;border-radius:6px;'>"
                    if fig.exists() else "<p class='muted'>figure missing</p>")
        ec = ("%.3g nM" % pr["ec50_nM"]) if pr.get("ec50_nM") is not None else "—"
        if pr.get("emax_pct"):
            ec += f" (Emax {pr['emax_pct']}%)"
        sel = []
        if pr.get("gpr109a_fold") is not None:
            sel.append(f"GPR109A {pr['gpr109a_fold']:.0f}×")
        if pr.get("ghsr_fold") is not None:
            sel.append(f"GHSR {pr['ghsr_fold']:.0f}×")
        if pr.get("lle") is not None:
            sel.append(f"LLE {pr['lle']:.1f}")
        params = [
            ("Entry", f"{esc(pr['entry_id'])} · {esc(pr['name'])}"),
            ("Role", esc(pr["role"])),
            ("Receptor", esc(pr["receptor"])),
            ("Best Vina score", f"{pr['best_score_kcal_mol']:.2f} kcal/mol"),
            ("Protocol", esc(pr["protocol"])),
            ("Binding region", f"<b>{esc(pr['region'])}</b>"),
            ("Pose centroid vs co-crystal", f"{pr['pose_centroid_to_cocrystal_A']} Å"),
            ("Polar contacts", f"{pr['n_polar_contacts']} — {esc(pr['polar_contacts'] or '—')}"),
            ("Hydrophobic contacts", f"{pr['n_hydrophobic_contacts']} (res {esc(pr['hydrophobic_residues'] or '—')})"),
            ("EC50 (paper)", ec),
            ("Selectivity / LLE", "; ".join(sel) or "—"),
        ]
        rows = "\n".join(f"<tr><th>{esc(k)}</th><td>{v}</td></tr>" for k, v in params)
        cards.append(
            f"<div class='card' id='pair-{esc(pr['pair_id'])}'>"
            f"<div class='card-fig'>{img_html}</div>"
            f"<div class='card-params'><table class='params'><tbody>{rows}</tbody></table></div>"
            f"<div style='clear:both'></div></div>")
    return "\n".join(cards)


def build_recommendations_html():
    """Condensed recommendations section (kept short; full text in the MD)."""
    return """
<h3>1 · Lead nomination</h3>
<ul>
<li><b>c28</b> (22 nM, 41× GPR109A, 82× GHS-R1a, LLE 5.3) is the best-balanced lead;
c26, c29 and c38 (amide series, sol 95 µM) are backups.</li>
<li><b>c30</b> (5 nM) is the most potent but only 7.4× GPR109A-selective — the
"most potent = least selective" trap; potency alone must not nominate.</li>
<li>c5 (0.74 nM) is a <b>partial agonist (Emax 47%)</b> — rank ≠ lead.</li>
</ul>
<h3>2 · Chemistry strategy</h3>
<ul>
<li><b>Pyridone, not pyrimidinone</b>: the pyrimidinone N3 sits 3.8 Å from Glu153
(negative–negative repulsion) — a 47× potency cliff (c30 vs c31; c26 vs c27).</li>
<li><b>Keep the constrained template</b> (Table 7 pyridone): the acyclic acyl-urea
linker loses its intramolecular H-bond network (c23–25 → 16–33 µM).</li>
<li><b>Exploit Glu153 (HCAR1) vs Lys165 (HCAR2)</b>: a vector contacting the
negative Glu153 carboxylate becomes repulsive at positive Lys165 — a built-in
selectivity handle; validate by docking into the HCAR2 model.</li>
<li>Stereochemistry pays: cis-2,6-dimethylmorpholine c38 (54 nM, 500× GHS-R1a,
sol 95 µM) vs trans c37 (350 nM).</li>
<li>Design caps: MW ≤ 550, clogP ≤ 4, LLE ≥ 5 (c28 = 5.3 is the bar).</li>
</ul>
<h3>3 · Selectivity & safety</h3>
<ul>
<li>Counterscreen every analog at GPR109A (niacin-flush liability) and GHS-R1a
(both assayed in the Davidsson paper); the HTS hits c1/c2 are GHS-R1a
cross-reactive — constrained chemotypes fixed this (62–667×).</li>
<li>HCAR1 agonism carries mechanism-based tumor/cachexia + liver-fibrosis risk;
consider tuned partial agonism (Emax 47–70% window) and Gαi vs β-arrestin bias
profiling as mitigation.</li>
</ul>
<h3>4 · Computational workflow (validated config)</h3>
<ul>
<li>Primary docking model: <b>8Z8A</b> (lactate-bound); 9KT9 orthosteric labels
need the deep-insert gate; 8Z87 is clash-incompatible for large ligands.</li>
<li>Extend with induced-fit/MD (Boltz-2) before committing to TM5–TM6 interactions.</li>
</ul>
"""


# ---------------------------------------------------------------- self-check
def check_tables(html: str):
    import re
    bad = []
    for m in re.finditer(r"<table[^>]*id='([^']+)'.*?</table>", html, re.S):
        tid, body = m.group(1), m.group(0)
        cells = re.findall(r"<t[dh][^>]*>([^<]*)</t[dh]>", body)
        non_empty = sum(1 for c in cells if c.strip())
        if non_empty == 0:
            bad.append(tid)
    if bad:
        raise SystemExit(f"FAIL: empty tables {bad}")
    return True


# ---------------------------------------------------------------- assemble
def main():
    ranking_html = build_ranking_table()
    cards_html = build_pair_cards()
    rec_html = build_recommendations_html()

    css = """
    body{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#f4f6f8;color:#222}
    .wrap{max-width:1280px;margin:0 auto;padding:18px}
    header{background:#0f3b5e;color:#fff;padding:22px 28px;border-radius:10px;margin-bottom:18px}
    header h1{margin:0 0 6px;font-size:26px}
    header p{margin:2px 0;color:#cfe0ef;font-size:13px}
    h2{color:#0f3b5e;border-bottom:2px solid #0f3b5e;padding-bottom:4px;margin-top:28px}
    h3{color:#14537e;margin-bottom:6px}
    table{border-collapse:collapse;width:100%;background:#fff;font-size:12.5px}
    th,td{border:1px solid #d5dbe1;padding:4px 7px;text-align:left}
    th{background:#0f3b5e;color:#fff;font-weight:600}
    tr:nth-child(even){background:#f0f4f7}
    tr.tierA{background:#e6f4ea}
    tr.tierB{background:#fdf6e3}
    tr.tierC{background:#fbeaea}
    .card{background:#fff;border:1px solid #d5dbe1;border-radius:8px;padding:10px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,.06)}
    .card-fig{float:left;width:72%}
    .card-params{float:right;width:26%}
    .card-params table.params{font-size:11px}
    .card-params th{width:42%;background:#e8eef4;color:#14537e}
    .card-params th,.card-params td{border:1px solid #dfe5ea;padding:3px 5px}
    .muted{color:#888}
    .note{background:#fff8e1;border-left:4px solid #f0ad4e;padding:10px 14px;border-radius:4px;font-size:13px}
    .fact{background:#e8f4fd;border-left:4px solid #2e86c1;padding:8px 12px;border-radius:4px;font-size:12.5px;margin:8px 0}
    ul{margin:4px 0 10px 20px;font-size:13.5px}
    li{margin:3px 0}
    .legend{font-size:12px;color:#555;margin:6px 0}
    @media (max-width:900px){.card-fig,.card-params{float:none;width:100%}}
    """

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>GPR81 (HCAR1) follow-up: 45-compound ranking · 46 pocket analyses · optimization strategy</title>
<style>{css}</style></head><body><div class="wrap">

<header>
<h1>GPR81 (HCAR1) druggability follow-up</h1>
<p>Overall ranking of 45 compounds · binding-pocket analyses of 46 ligand–receptor pairs · optimization strategy</p>
<p>Compounds: 39 from Davidsson et al. 2020 (BMCL 30:126953) + 5 lead/tool compounds + L-lactate (endogenous).
Receptors: 8Z8A (lactate-bound), 9KT9 (3,5-DHBA-bound), 8Z87 (CHBA-bound) active-state HCAR1–Gi structures.</p>
<p>Generated 2026-08-05 · computational companion to the paper's experimental data · audit files in the same folder (CSV/JSON/MD/scripts)</p>
</header>

<h2>1 · Overall ranking of all 45 compounds</h2>
<div class="fact"><b>Ranking basis:</b> primary rank = reported experimental hGPR81 EC50 (ascending).
Vina docking scores are structural <i>context</i>, not affinity predictions (global score–EC50 correlation is absent at n=39, r≈−0.11).
Tier rule: <b>A</b> = EC50 ≤ 50 nM &amp; Emax ≥ 80% &amp; GPR109A ≥ 25× &amp; GHSR ≥ 50× (where measured);
<b>B</b> = EC50 ≤ 100 nM with an unmet A-criterion (liability noted); <b>C</b> = EC50 &gt; 100 nM.
Reference ligands without a comparable potency assay (CHBA, 3,5-DHBA, 3-OBA, lactate) are listed last — rank n/a.</div>
{ranking_html}
<div class="legend">Rows highlighted: <span style="background:#e6f4ea">tier A</span> ·
<span style="background:#fdf6e3">tier B</span> · <span style="background:#fbeaea">tier C</span>.
"n.d." = not determined in the paper's selectivity panel. 8Z8A/9KT9 scores = best multi-seed Vina score on that receptor.</div>

<h2>2 · Binding-pocket analyses — 46 ligand–receptor pairs</h2>
<div class="note"><b>Pair-universe accounting (46 = 45 compound entries + 1):</b>
39 paper compounds × 8Z8A (primary, control-passing receptor) + 5 lead compounds × 8Z8A + L-lactate × 8Z8A (cognate)
+ L-lactate × 9KT9 (tight-box cross-structure control, this follow-up).
Compound 1 (AZ1) is listed in both the Davidsson series and the lead table and contributes two distinct docking runs
(phase-6 paper run and phase-3 lead run), which closes the 45→46 count.
Figures: 2D structure (left) + PCA-projected pocket view (right; green = ligand, gray = pocket residues,
yellow dashed = polar-contact candidates, labels = residue contacts).</div>
{cards_html}

<h2>3 · Recommendations for future optimization &amp; development</h2>
{rec_html}
<p class="muted">Full narrative with evidence-level tags: <code>gpr81_optimization_recommendations.md</code>.</p>

<h2>4 · Methodology &amp; caveats</h2>
<ul>
<li><b>Evidence separation:</b> [FACT] db/paper-verified · [OBS] direct computation · [MECH] mechanistic interpretation · [HYP] unresolved hypothesis. Docking does not prove agonism, affinity, or selectivity.</li>
<li><b>Controls passed:</b> CHBA→8Z87 redock centroid 0.88 Å; 3,5-DHBA→9KT9 tight-box 1.67 Å; lactate→8Z8A 2.89 Å; lactate→9KT9 tight-box 2.79 Å (this follow-up).</li>
<li><b>Protocols:</b> papers = phase-6 scan (24 Å box, 2 seeds × ex16 × 5 poses, 8Z8A+9KT9); leads = phase-3 (5 poses); lactate×9KT9 = tight box (12 Å on 34D, ex32, 3 seeds). Matched pairs carry 8-seed × ex32 phase-4 data.</li>
<li><b>Region taxonomy:</b> ORTHO_POCKET {71,75,92,95,96,99,165,167,168,261,264,268} · TM56_EXTRACELLULAR {153,155,157,164,166,169,170,171,174,177} · NTERM_SURFACE {6,7,8,9,79} (HCAR1 numbering, 4.5 Å contact cutoff, fraction ≥ 0.4).</li>
<li><b>9KT9 caveat:</b> 24 Å-box orthosteric labels on 9KT9 carry a deep-insert artifact history; only tight-box-verified compounds (c26; weak c29) count as genuine 9KT9 orthosteric binders. 8Z87 scores large ligands systematically positive (conformational clash in the CHBA-bound state) — classified counter-screen for large molecules, not evidence of non-binding.</li>
<li><b>Data provenance:</b> structures = 39/39 recovered and MS-validated (3 authoritative incl. compound 22 resolved SI mislabel; 36 reconstructed + MS-validated). EC50 from the paper tables (transcribed, cross-checked); the compound index CSV has inconsistent EC50 units and was used only for Emax annotations — the recovered JSON is the numeric source of truth.</li>
</ul>

<p class="muted" style="margin-top:20px">Companion files: gpr81_compound_scorecard.csv/.json ·
gpr81_pocket_analysis_pairs.csv/.json · gpr81_optimization_recommendations.md ·
gpr81_ranking_summary.md · figures/pocket_*.png (46) · build_*.py scripts · run_lactate_9kt9_tightbox.py + data/lactate_9kt9_tightbox.*</p>
</div></body></html>"""

    out = BASE / "gpr81_followup_report.html"
    out.write_text(html, encoding="utf-8")
    check_tables(html)
    print("wrote", out, f"({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
