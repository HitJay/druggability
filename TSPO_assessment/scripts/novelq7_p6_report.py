"""ws7 P6: self-contained dark-theme HTML report for the FGIN-1-27 novel-pocket round."""
import csv, glob, json

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
rows = list(csv.DictReader(open(f"{BASE}/output/novelq7_tiered_targets_v1.csv")))
by_tag = {r["pocket_tag"]: r for r in rows}
hit = json.load(open(f"{BASE}/output/docking/novelq7_p2_fgin_hittier.json"))
md7 = {}
for f in glob.glob(f"{BASE}/output/docking/novelq7_p3_*.json"):
    j = json.load(open(f)); md7[j["tag"]] = j
ti = {}
for f in sorted(glob.glob(f"{BASE}/output/fep_a7/scan7_*.json")):
    j = json.load(open(f)); ti[(j["tag"], j["ligand"])] = j


def ti_rows(lig):
    out = []
    for (t, l), j in sorted(ti.items()):
        if l != lig:
            continue
        for a, v in j["anchors"].items():
            out.append((t, a, v["ddG_kJmol"], v["ddG_kcalmol"], v["native_IE_kJmol_t0"]))
    return sorted(out, key=lambda x: -x[2])


def ti_table(lig):
    trs = []
    for t, a, dd, kkal, nat in ti_rows(lig):
        note = ""
        if t == "4XAQ":
            note = ""
        cls = "pos" if dd > 0 else "neg"
        trs.append(f"<tr><td>{t}</td><td>{a}</td><td class='num {cls}'>{dd:+.1f}</td>"
                   f"<td class='num'>{kkal:+.2f}</td><td class='num'>{nat:.1f}</td></tr>")
    return "\n".join(trs)


FGIN_TI = ti_table("fgin")
EMAP_TI = ti_table("emapunil")

md_stable = [t for t, j in sorted(md7.items()) if j.get("verdict") == "md-stable"]
md_unstable = [t for t, j in sorted(md7.items()) if j.get("verdict") == "md-unstable"]

tier_rows = []
for r in rows:
    if r["fgin_layer"] == "skipped" and r["emapunil_layer"] == "skipped":
        continue
    tier_rows.append(
        f"<tr><td>{r['pocket_tag']}</td><td>{r['gene']}</td>"
        f"<td class='num'>{r['fgin_scan_best']}</td><td class='num'>{r['fgin_hittier_best3']}</td>"
        f"<td>{r['fgin_md_verdict']}</td><td class='num'>{r['fgin_ti_top_ddG_kJmol']}</td>"
        f"<td class='num'>{r['emapunil_scan_best']}</td><td>{r['emapunil_md_verdict']}</td>"
        f"<td class='num'>{r['emapunil_ti_top_ddG_kJmol']}</td><td>{r['fgin_layer']}</td></tr>")
TIER = "\n".join(tier_rows)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ws7 — FGIN-1-27 across fpocket novel pockets: docking, MD stability, annihilation TI</title>
<style>
:root {{ --bg:#0f1419; --panel:#1a2028; --panel2:#232b36; --text:#d8dee9; --muted:#8895a7;
        --accent:#5eb3ff; --ok:#7ec98f; --warn:#e5c07b; --err:#e06c75; --border:#2c3542; }}
body {{ margin:0; padding:40px 20px; background:var(--bg); color:var(--text); line-height:1.6;
       font-size:15px; font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif; }}
.container {{ max-width:1060px; margin:0 auto; }}
h1 {{ font-size:22px; }} h2 {{ font-size:18px; border-bottom:1px solid var(--border); padding-bottom:6px; }}
code {{ background:#12171d; padding:1px 5px; border-radius:3px; }}
table {{ border-collapse:collapse; width:100%; margin:14px 0; font-size:13.5px; }}
th {{ background:var(--panel2); text-align:left; padding:6px 8px; border:1px solid var(--border); }}
td {{ padding:5px 8px; border:1px solid var(--border); }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.pos {{ color:var(--ok); }} .neg {{ color:var(--err); }}
.callout {{ border-left:4px solid var(--accent); background:var(--panel); padding:10px 14px; margin:14px 0; border-radius:0 6px 6px 0; }}
.callout.warn {{ border-color:var(--warn); }} .callout.ok {{ border-color:var(--ok); }}
.muted {{ color:var(--muted); font-size:13px; }}
footer {{ margin-top:30px; border-top:1px solid var(--border); padding-top:10px; color:var(--muted); font-size:12.5px; }}
</style>
</head>
<body><div class="container">
<h1>FGIN-1-27 across the fpocket novel-pocket set — docking, MD pose-stability, annihilation TI</h1>
<p class="muted">Request (Z. Cao, 2026-10-19): run the fpocket novel pockets on the PK11195 target list for FGIN-1-27,
docking + MD, then FEP on prioritized pockets; emapunil reuses the ws6 campaign as the cross-ligand comparator.
All numbers on this page are computational supporting evidence, not proof of binding.</p>

<div class="callout ok"><b>Verdict.</b> FGIN-1-27 engages the novel-pocket set as broadly as emapunil
(15/29 scan-engaged both), confirms <b>16/17</b> at the 3-seed hit tier (emapunil: 10/10 on its shortlist),
and survives pose-stability MD on <b>13/16</b>. Annihilation TI on the top-3 side-chain anchors of every
docking+MD survivor (13 pockets, FGIN; 6-pocket cross-set, emapunil) shows every confirmed pocket is held by
real side-chain interactions (top ddG +3.6 to +20.0 kJ/mol). The headline novel pocket remains
<b>4RYI_p26 — the TSPO dimer-interface second pocket</b>: FGIN -9.17 kcal/mol (best seed, 3-seed stable),
emapunil -7.64, both ligands md-stable, TI top anchors +7.6 (FGIN LEU58B) / +7.7 (emapunil MET1A) kJ/mol.</p></div>

<h2>1. Layers and gates (identical protocol across both ligands)</h2>
<table>
<tr><th>Layer</th><th>Protocol</th><th>Gate</th></tr>
<tr><td>Scan docking</td><td>Vina exh16, 5 poses, 24 Å box on fpocket centroid</td><td>engaged: best ≤ −7.0 kcal/mol and pose1 centroid offset ≤ 6 Å</td></tr>
<tr><td>Hit tier</td><td>3 independent runs × exh32 (seed sensitivity)</td><td>confirmed: best-of-seeds ≤ −7.0 and offset ≤ 6 Å</td></tr>
<tr><td>MD pose-stability</td><td>250 ps LangevinMiddle 300 K, all protein heavy atoms restrained 5 kcal/mol/Å²</td><td>md-stable: ligand centroid drift ≤ 4 Å</td></tr>
<tr><td>Annihilation TI</td><td>top-3 side-chain anchors per pocket, q/ε × (1−λ), 8 λ windows, 27.5 ps/window, protein 5 + ligand 1 kcal/mol/Å² restraints</td><td>ddG &gt; 0 ⇒ ligand uses that side chain (loss of binding energy on annihilation)</td></tr>
</table>
<p class="muted">MD drift is the decisive verdict for borderline docks — the score stage liked 6HUG_p114 (−8.45),
the dynamics stage killed it (4.6 Å drift). Report vocabulary stays capped: computed-dock / computed-md /
computed-ti / computed-negative / skipped; no "computed-positive".</p>

<h2>2. FGIN-1-27 results by pocket (all layers)</h2>
<table>
<tr><th>Pocket</th><th>Target</th><th>scan best</th><th>hit best3</th><th>MD verdict</th><th>TI top ddG (kJ/mol)</th><th>emap scan</th><th>emap MD</th><th>emap TI top</th><th>layer</th></tr>
{TIER}
</table>
<p class="muted">Rejections are findings, not failures: 6HUG_p114, 7F61_p15, 7M93_p8 docked ≤ −7.8 but drifted
4.6–8.5 Å in MD (computed-negative). 4DKL_p2 (OPRM1) confirmed for emapunil but not for FGIN (−6.69).
4DJH_p53 (OPRK1) is demoted-adjacent to the orthosteric pocket in the novelty gate and keeps its data inline.</p>

<h2>3. Annihilation TI — side-chain usage per pocket</h2>
<h3>FGIN-1-27 (13 md-stable pockets × top-3 anchors)</h3>
<table><tr><th>Pocket</th><th>Anchor</th><th>ddG (kJ/mol)</th><th>ddG (kcal/mol)</th><th>native IE t0</th></tr>
{FGIN_TI}
</table>
<h3>emapunil (6-pocket cross-set where both ligands are md-stable)</h3>
<table><tr><th>Pocket</th><th>Anchor</th><th>ddG (kJ/mol)</th><th>ddG (kcal/mol)</th><th>native IE t0</th></tr>
{EMAP_TI}
</table>
<p class="muted">Positive ddG = annihilating that side chain costs binding free energy = the ligand uses it.
Near-zero rows with near-zero native IE (e.g. 7M93_p18 emapunil PHE72A/GLU69A) are anchors whose t0 contact is
negligible — they were carried by the ws6 IE ranking but the TI layer shows no side-chain dependency.
Units: kJ/mol throughout, Coulomb constant 138.935 kJ·nm/e² (the corrected convention; ws6 IE numbers are not
directly comparable — see §4).</p>

<h2>4. Caveats</h2>
<div class="callout warn">
<ul>
<li>Computational scores are supporting evidence, not proof of binding; only measured data can enter Tier 1–2 of the target assessment.</li>
<li>TI here annihilates side chains at the docked/relaxed geometry (computational alanine scanning). It answers
"does the ligand use this side chain", not absolute affinity; ε/q scaling only, σ fixed.</li>
<li>12 anchors in the first parallel sweep silently returned exact-zero windows (a mixed-precision CUDA artifact
observed under 4-GPU contention). All suspect jobs were re-run sequentially in double precision; every reported
number passes the non-zero-window test in <code>tests/test_novelq7_dataset.py</code>.</li>
<li>MD is 250 ps per pocket — pose-stability timescale only, not residence time or binding kinetics.</li>
<li>IE/TI share the no-desolvation limitation: charged contacts are overstated; ranking use only.</li>
<li>Residue numbering follows the pdbfixer-processed complexes (chain-suffixed), self-consistent within this round.</li>
</ul>
</div>

<h2>5. Provenance</h2>
<p class="muted">Scripts: <code>scripts/novelq7_p1_fgin_docking.py</code>, <code>novelq7_p3_md_stability.py</code>,
<code>novelq7_p4_fep.py</code> + <code>novelq7_p4_runner.py</code>, <code>novelq7_p5_tier_csv.py</code>, this page
<code>novelq7_p6_report.py</code>. Data: <code>output/docking/novelq7_p1_fgin_scan.jsonl</code>,
<code>novelq7_p2_fgin_hittier.json</code>, <code>novelq7_p3_*.json</code>, <code>output/fep_a7/scan7_*.json</code>,
tier CSV <code>output/novelq7_tiered_targets_v1.csv</code>. Tests: 55 passed (11 in
<code>tests/test_novelq7_dataset.py</code>). Ligand identity: FGIN-1-27, PubChem CID 132496,
InChIKey VUWXAQFLTSBUDB-UHFFFAOYSA-N. Environment: openfe-md (openfe 1.12.0 / openmm 8.4 / openff 0.18), CUDA.</p>

<footer>ws7 novel-pocket round for the TSPO ligand-target campaign (RIC-408 series) — generated 2026-10-20.
Self-contained; no external assets. Companion files: novelq7_tiered_targets_v1.csv, email draft.</footer>
</div></body></html>
"""
out = f"{BASE}/output/fep_a7/novelq7_novel_pockets_fgin_report.html"
open(out, "w").write(html)
print(out, len(html), "bytes")
