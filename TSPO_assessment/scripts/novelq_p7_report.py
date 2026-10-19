"""ws6 P7: self-contained HTML report for the novel-pocket round (English,
verdict-first, matches the TSPO assessment house style: FACT/OBS/MECH/HYP
separation, no method overclaim — docking + MD pose-stability, no FEP)."""
import base64, json
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
DOCK = BASE / "output/docking"

scan = [json.loads(l) for l in open(DOCK / "novelq_p5_emapunil_novel_pockets.jsonl")]
v2j = json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))
v2 = v2j["novel_v2"]
v2_by_tag = {f"{r['pdb']}_p{r['pocket_id']}": r for r in v2j["all_rows"]}
hit = json.load(open(DOCK / "novelq_p5c_hittier.json"))
ctrl = json.load(open(DOCK / "novelq_p5_controls.json"))
cross = json.load(open(BASE / "data/novelq_p4b_novelty_crosscheck.json"))
cross_by_tag = {f"{r['pdb']}_p{r['pocket_id']}": r for r in cross}
raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))

def md_for(tag):
    p = DOCK / f"novelq_p6_{tag}.json"
    return json.load(open(p)) if p.exists() else {}

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

rows_html = []
for s in scan:
    if "error" in s:
        rows_html.append(f"<tr class='neg'><td>{esc(s['tag'])}</td><td colspan='9'>error: {esc(s['error'])}</td></tr>")
        continue
    tag = s["tag"]
    v = v2_by_tag[tag]
    cx = cross_by_tag[tag]
    h = hit.get(tag, {})
    md = md_for(tag)
    seeds = " / ".join(f"{x[0]:.2f}" for x in h["seed_scores"]) if h else ""
    if md and "error" not in md:
        layer = "computed-md" if md.get("verdict") == "md-stable" else "computed-negative (MD-unstable)"
        mdcell = f"drift {md['md_drift_A']} A; sumIE {md['sum_IE_kJmol']}; top {esc(list(md.get('top_contacts',{}))[:1] and list(md['top_contacts'])[0] or '-')}"
    elif h:
        layer, mdcell = "computed-dock", "MD not run"
    else:
        layer, mdcell = ("computed-negative", "MD not run") if s["verdict_scan"] == "not-engaged" else ("computed-dock", "MD not run")
    cls = "md" if "md-stable" in layer else ("neg" if "negative" in layer else "")
    flags = []
    if cx.get("is_interface"): flags.append("interface")
    if cx.get("het_within_6A"): flags.append("lipid-adjacent")
    if v["gene"] == "TMEM97": flags.append("recurs 7M93/9ZIR")
    rows_html.append(
        f"<tr class='{cls}'><td>{esc(tag)}</td><td>{esc(v['gene'])}</td>"
        f"<td>{v['ds']:.2f}</td><td>{round(v['volume'])}</td>"
        f"<td>{s['best']:.2f}</td><td>{seeds or s['verdict_scan']}</td>"
        f"<td>{h.get('pose1_offset_A', s.get('pose1_offset_A','-'))}</td>"
        f"<td>{esc(mdcell)}</td><td>{esc(', '.join(flags) or '-')}</td>"
        f"<td>{esc(layer)}</td></tr>")

ctrl_html = "".join(
    f"<tr><td>{esc(c['tag'])}</td><td>{c['scores'][0]:.2f}</td><td>{c['offset_A']} A</td>"
    f"<td>{esc('PASS' if c.get('qc','')=='PASS' else ('in pocket' if c.get('in_pocket') else 'out of pocket'))}</td></tr>"
    for c in ctrl)

n_novel = len(v2)
n_engaged = sum(1 for s in scan if s.get("verdict_scan") == "engaged")
n_conf = sum(1 for h in hit.values() if h.get("confirmed"))
n_md_stable = sum(1 for t in hit if (md_for(t) or {}).get("verdict") == "md-stable")

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>TSPO binder list — novel pocket screening + emapunil docking/MD (2026-10-19)</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;max-width:1180px;margin:24px auto;padding:0 16px;color:#1a1a2e;line-height:1.45}}
h1{{color:#001965;border-bottom:3px solid #00857C;padding-bottom:8px}}
h2{{color:#001965;margin-top:28px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0}}
th{{background:#001965;color:#fff;padding:6px 8px;text-align:left;position:sticky;top:0}}
td{{border-bottom:1px solid #dde;padding:5px 8px}}
tr.md td{{background:#e8f5f1}}
tr.neg td{{background:#fafafa;color:#666}}
.verdict{{background:#f0f7f6;border-left:5px solid #00857C;padding:14px 18px;margin:14px 0}}
.warn{{background:#fdf3f0;border-left:5px solid #D9383A;padding:12px 18px;margin:14px 0}}
.tag{{display:inline-block;background:#00857C;color:#fff;border-radius:10px;padding:1px 9px;font-size:11.5px;margin-right:6px}}
.tag.red{{background:#D9383A}} .tag.blue{{background:#001965}}
code{{background:#f0f0f5;padding:1px 5px;border-radius:3px;font-size:12px}}
.small{{font-size:11.5px;color:#555}}
</style></head><body>
<h1>Novel-pocket screening on the PK11195 binder-list proteins, with emapunil docking + MD in the new pockets</h1>
<p class="small">TSPO ligand target search, request from Zheng Cao, 2026-10-19 &middot; Round ws6 &middot; follow-up to the 2026-10-19 PK11195 binder list (21 distinct proteins)</p>

<div class="verdict"><b>Verdict.</b> fpocket screening of all 17 usable experimental structures behind the
binder list finds <b>{n_novel} pocket candidates that are disjoint from every literature/co-crystal-reported pocket</b>.
Emapunil docks into {n_engaged} of them at scan tier; {n_conf} survive 3-seed confirmation;
{n_md_stable} of the 10 MD-run pockets hold their pose through 250&nbsp;ps restrained MD.
The strongest novel site is <b>on TSPO itself</b>: a second, druggability-score-0.99 cavity (4RYI pocket 26,
~1300&nbsp;A^3, zero residue overlap with the PK11195 pocket, interface of the dimeric crystal) that binds
emapunil at −7.6&nbsp;kcal/mol and stays within 1.4&nbsp;A through MD. All computational evidence;
no free-energy claims are made.</div>

<h2>1. What was screened</h2>
<p>Every protein on the 29-row PK11195 binder list with at least one experimental structure
(verified against UniProt/RCSB cross-references, not memory): 14 structures already carrying controls from the
emapunil/FGIN campaigns, plus new structural coverage found this round — <b>GRM5</b> (human 7TM, 4OO9),
<b>TMEM97/sigma-2</b> (bovine; human has no structure; 7M93/PB28 and 9ZIR/zervimesine), and re-checks confirming
<b>NPSR, PMP22, ALOX15-human have no experimental structure at all</b> (screening impossible; recorded as gaps, not skipped),
and TSPO-human P30536 still has no PDB entry (BcTSPO 4RYI remains the anchor model).</p>
<p>fpocket 4.0 recovered the known (co-crystal) pocket in <b>17/17 structures</b> — the method control that
makes "no pocket found / new pocket found" statements meaningful on this receptor set.</p>

<h2>2. How "novel" was decided</h2>
<p><span class="tag blue">exclusion</span>A pocket is only called novel when (a) its residues do not recover the
co-crystal (literature-reported) pocket of its own structure (&lt;30% residue overlap, centroid &gt;3&nbsp;A from every copy
of the pocket-defining ligand — this also kills the "same site on the other protomer" false positives);
(b) druggability score &ge;0.20; (c) volume &ge;250&nbsp;A^3; (d) &ge;20 alpha spheres on &ge;12 residues.
Pockets within 3&nbsp;A of a bound lipid (OLA/OLC/MPG...) are tagged <i>lipid-adjacent</i> rather than excluded —
they may be the lipid-facing cavities already discussed in the literature, so their novelty claim is weaker.
Independent literature inventory: Europe PMC pocket-structure queries per target
(18 targets, PMIDs saved to <code>novelq_p3_literature_pockets.json</code>); no candidate pocket matches a
reported pocket in that inventory.</p>

<h2>3. Emapunil results in the novel pockets</h2>
<p>Scan tier: exhaustiveness 16 (30 pockets). Hit tier (10 pockets, top per family): 3 independent seeds x
exhaustiveness 32. MD: 250&nbsp;ps restrained (all protein heavy atoms, 5&nbsp;kcal/mol/A^2), OBC2 implicit,
double-precision CUDA, protocol identical to the 2026-10-19 emapunil anchor campaign (4RYI anchor: drift 1.09&nbsp;A).</p>
<table><thead><tr><th>Pocket</th><th>Target</th><th>fpocket DS</th><th>Vol A^3</th>
<th>scan best</th><th>hit tier (3 seeds)</th><th>pose1 off A</th><th>MD 250 ps</th><th>flags</th><th>layer</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table>

<h2>4. Controls run this round</h2>
<table><thead><tr><th>Control</th><th>Score</th><th>Pose recovery</th><th>Status</th></tr></thead>
<tbody>{ctrl_html}</tbody></table>
<p class="small">Redocks place each structure's own co-crystal ligand back into its pocket (tight box 14&nbsp;A):
0.3-1.4&nbsp;A recovery on all three new structures. Known-pocket emapunil docking on the new structures
(4OO9 -6.21, 7M93 -7.39, 9ZIR -6.45) gives the per-structure reference band; every novel-pocket hit above is
<i>stronger</i> than its own structure's known-pocket reference, so the hits are not a box-size artifact.</p>

<h2>5. Reading the headline pockets</h2>
<ul>
<li><b>4RYI pocket 26 (TSPO)</b> <span class="tag">computed-md</span> — the most decision-relevant finding for the TSPO project.
DS 0.985 / 1301&nbsp;A^3, formed at the <i>dimer interface</i> of the BcTSPO crystal (residues from both chains:
TM1/TM2/TM3 on one face, helix-helix groove on the other), zero overlap with the PK11195 pocket.
Emapunil: -7.64 scan, -7.60/-7.64/-7.65 hit tier, MD drift 1.44&nbsp;A, dominant contact MET1-region hydrophobics.
<b>Caveat (MECH, not FACT):</b> the site only exists as detected in the dimeric crystal packing; whether the equivalent
cleft is accessible in monomeric membrane TSPO is exactly what a longer all-atom membrane MD would test —
recommended as the follow-up before any wet-lab probe design.</li>
<li><b>TMEM97 (sigma-2) pockets</b> <span class="tag">computed-md</span> — 7M93 pocket 18 (MD-stable, drift 2.09&nbsp;A,
top contact ARG155, -126 kcal-equiv) is the clean TMEM97 result; the corresponding site on 9ZIR (pocket 11,
same TM2/TM5-TM6 region, docking confirmed -7.56..-7.58) came out <b>MD-unstable</b> (drift 5.7&nbsp;A) —
the dynamics stage rejected it, so 7M93_p18 alone carries the claim. Neither is the PB28/zervimesine orthosteric
pocket; the region recurs across two independent crystal forms, which is what makes it worth reporting.</li>
<li><b>7F61 pocket 15 (HRH3)</b> <span class="tag">computed-md</span> — intracellular-side cavity, best raw score of the
round (-9.23), MD drift 3.98&nbsp;A (stable but at the threshold; treat as borderline).
<b>4WB9 pocket 1 (ALDH1A1)</b> — docks at -8.76 but the MD interaction energy is net <i>positive</i>
(+455.8, LYS105 electrostatics dominating): the pose survives but the contact pattern is electrostatically unfavourable;
report as docking-only evidence, not a binder candidate.</li>
<li><b>GABA-A 6X3X pockets 78/128</b> — both MD-stable (drift 1.75/1.77&nbsp;A); p128 is the a/g-interface TMD cavity
adjacent to the known neurosteroid site literature (lipid-adjacent flag). <b>4DJH p53 (OPRK1)</b> — -9.09 docking,
MD-stable (2.30&nbsp;A, top ALA417); worth noting because OPRK1 was the canonical score-vs-MD disagreement case in the
anchor round — this pocket passes both gates. <b>4DKL p2 / 6HUG p114</b> — docking engaged but MD-unstable
(drift 5.9/5.2&nbsp;A): the dynamics stage rejected what the score liked, exactly as in the OPRK1 precedent.</li>
</ul>

<h2>6. Scope and limitations (read before citing)</h2>
<div class="warn">
<ul>
<li><b>No FEP / no binding free energies.</b> Deliverable is docking (ranked, seed-confirmed) + 250&nbsp;ps restrained-MD
pose stability + interaction-energy decomposition. IE sums are raw Coulomb+vdW without desolvation — ranking use only.</li>
<li>fpocket sees <i>one</i> conformation per structure. Pockets that open only in other states (or in membrane context)
are invisible to this screen; "no novel pocket found on X" means "none detectable in the screened structure(s)".</li>
<li>Interface pockets (4RYI p26, GABA-A pockets, 4DJH p53) depend on the crystal's oligomer packing.</li>
<li>Bovine TMEM97 (94% identity) stands in for the structure-less human sigma-2; A147T-analogous species caveats apply as in the anchor round.</li>
<li>Emapunil is a neutral, fairly rigid ligand; its docking success in a cavity does not transfer to bulkier TSPO ligands.</li>
</ul></div>

<h2>7. Files</h2>
<p class="small">Screening/gating: <code>novelq_p2_fpocket_pockets.json</code>, <code>novelq_p4_novel_candidates.json</code>,
<code>novelq_p4b_novelty_crosscheck.json</code>, <code>novelq_p4c_novel_v2.json</code> (data/).
Docking: <code>docking/novelq_p5_emapunil_novel_pockets.jsonl</code>, <code>docking/novelq_p5c_hittier.json</code>,
<code>docking/novelq_p5_controls.json</code>. MD: <code>docking/novelq_p6_*.json</code>.
Tier table: <code>output/novel_pockets_tiered_targets_v1.csv</code>. Scripts: <code>scripts/novelq_p*.py</code>;
tests: <code>tests/test_novel_pockets_dataset.py</code>.</p>
</body></html>"""

out = BASE / "output/novel_pockets_round_report.html"
out.write_text(HTML)
print(f"wrote {out} ({len(HTML)//1024} KB)")
print(f"novel={n_novel} engaged={n_engaged} confirmed={n_conf} md_stable={n_md_stable}")
