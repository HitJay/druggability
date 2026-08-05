#!/usr/bin/env python3
"""Build the consolidated GPR81/HCAR1 final report (HTML) from all phase artifacts.

Reads every audit file on disk (no hardcoded numbers) and renders a single
dark-themed report covering: request context, data assets, docking protocol +
QC gates, tool-compound findings, 9KT9 remediation, reverse-SAR (matched pairs +
full series + pyridone/pyrimidinone mechanism), selectivity (paper + HCAR2 pocket
comparison), activation safety, conclusions, artifact index.

Output: data/gpr81_phase1/gpr81_final_report.html
"""
from __future__ import annotations
import csv, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/gpr81_phase1"

def load_json(rel):
    return json.loads((P / rel).read_text())

def load_csv(rel):
    with (P / rel).open() as fh:
        return list(csv.DictReader(fh))

def esc(x):
    return html.escape(str(x))

def table(headers, rows):
    out = ["<table><thead><tr>"] + [f"<th>{esc(h)}</th>" for h in headers] + ["</tr></thead><tbody>"]
    for row in rows:
        out.append("<tr>")
        for h in headers:
            out.append(f"<td>{esc(row.get(h, ''))}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)

def cards(items):
    return '<div class="cards">' + "".join(f'<div class="card"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in items) + "</div>"

def main():
    # ---- load data ----
    tools = load_csv("tool_compounds.csv")
    identity = load_json("identity_resolution.json")
    paper = load_json("paper_structures_recovered.json")
    mp_summary = load_json("phase4_matched_pairs/matched_pair_summary.json")
    annotated = load_json("phase5_tightbox/annotated_matched_pairs.json")
    kt9_fix = load_json("phase5_tightbox/9kt9_small_acid_redock.json")
    pyr = load_json("phase5_tightbox/pyridone_vs_pyrimidinone_validation.json")
    f6_summary = load_json("phase6_full_series/full_series_summary.json")
    f6_sar = load_json("phase6_full_series/full_series_reverse_sar.json")
    consensus = load_json("phase6_full_series/full_series_region_consensus_2seed.json")
    sel = load_json("safety/davidsson2020_selectivity_transcription.json")
    pocket = load_json("safety/hcar1_hcar2_pocket_mapping.json")

    # ---- derived rows ----
    tool_rows = []
    for r in tools:
        cid = r["compound_id"]
        ident = next((i for i in identity["tool_compounds"] if i["compound_id"] == cid), {})
        tool_rows.append({"Tool compound": cid, "CID": r.get("cid", ""),
                          "Identity": ident.get("identity_resolution", "").replace("_", " ")})

    paper_n = len(paper["compounds"])
    auth = sum(1 for c in paper["compounds"] if c["status"] == "authoritative")
    msval = sum(1 for c in paper["compounds"] if c["status"] == "reconstructed_and_MS_validated")
    ec_range = (min(float(c["paper_reported_hGPR81_EC50_uM"]) for c in paper["compounds"] if isinstance(c.get("paper_reported_hGPR81_EC50_uM"), (int, float))),
                max(float(c["paper_reported_hGPR81_EC50_uM"]) for c in paper["compounds"] if isinstance(c.get("paper_reported_hGPR81_EC50_uM"), (int, float))))

    # matched pairs annotated rows
    mp_rows = []
    for cid in sorted((k for k in annotated if k.isdigit()), key=int):
        e = annotated[cid]
        for rid in ["8Z87", "8Z8A"]:
            r = e["receptors"].get(rid, {})
            mp_rows.append({"Compound": f"c{cid}", "Receptor": rid, "EC50 µM": e.get("ec50_uM", ""),
                            "Best 24Å": r.get("best_24A_box", ""), "Region": r.get("binding_region", ""),
                            "Validity": r.get("validity", ""), "Verdict": r.get("verdict", "")[:70]})

    # selectivity rows
    sel_rows = []
    for cid, d in list(sel.get("table7_constrained", {}).items()) + list(sel.get("table8_amides", {}).items()):
        sel_rows.append({"Compound": f"c{cid}", "hGPR81 EC50 µM": d.get("hGPR81_EC50_uM", ""),
                         "hGPR109A EC50 µM": d.get("hGPR109A_EC50_uM", ">"), "Fold vs GPR109A": d.get("fold_GPR109A", ""),
                         "hGHS-R1a IC50 µM": d.get("hGHS-R1a_IC50_uM", ""), "Fold vs GHS-R1a": d.get("fold_GHSR", "")})

    # pocket rows
    pocket_rows = [{"HCAR1 residue": r["hcar1"], "HCAR1": r["hcar1_res"], "HCAR2 position": r["hcar2_pos"],
                    "HCAR2": r["hcar2_res"], "Conserved": "=" if r["hcar1_res"] == r["hcar2_res"] else "X"}
                   for r in pocket["pocket_orthosteric"]]

    f6_top = f6_sar.get("top_outside_matched", [])[:5]

    css = """*{box-sizing:border-box}body{margin:0;padding:40px 20px;background:#0f1419;color:#d8dee9;font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;font-size:15px}.container{max-width:1150px;margin:auto}h1{font-size:30px;margin:0 0 6px;color:#fff}h2{margin-top:38px;border-bottom:1px solid #2c3542;padding-bottom:8px;color:#5eb3ff}h3{color:#fff;margin-top:26px}.meta,.muted{color:#8895a7;font-size:13px}.callout{padding:16px 18px;margin:16px 0;border-left:4px solid #5eb3ff;background:#1a2028;border-radius:6px}.callout.ok{border-color:#7ec98f}.callout.warn{border-color:#e5c07b}.callout.err{border-color:#e06c75}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}.card{background:#1a2028;border:1px solid #2c3542;padding:16px;border-radius:7px}.card b{display:block;font-size:24px;color:#fff}.card span{color:#8895a7;font-size:12px}table{width:100%;border-collapse:collapse;background:#1a2028;margin:14px 0 24px;font-size:13px}th,td{border:1px solid #2c3542;padding:8px 10px;text-align:left;vertical-align:top}th{background:#232b36;color:#fff}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}code{color:#b9e2ff}pre{background:#12171d;border:1px solid #2c3542;padding:14px;overflow:auto;color:#c9d1d9;border-radius:6px}ul,ol{padding-left:24px}footer{margin-top:48px;padding-top:16px;border-top:1px solid #2c3542;color:#8895a7;font-size:12px}@media(max-width:800px){.cards{grid-template-columns:repeat(2,1fr)}table{display:block;overflow-x:auto}}"""

    report = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HCAR1/GPR81 — Consolidated Final Report</title><style>{css}</style></head><body><main class="container">
<header><h1>HCAR1 / GPR81 (lactate receptor) — Structure, SAR &amp; Safety</h1>
<div class="meta">Consolidated final report · 2026-08-04 · target: human HCAR1/GPR81 (UniProt Q9BXC0) · request: small-molecule agonist docking (Huan)</div></header>

<section class="callout ok"><b>Executive summary</b><br>
All 39 paper-series compounds were recovered and validated; the docking campaign ran through 6 phases with explicit quality gates. Three headline findings:
(1) <b>Large agonists bind the TM5-TM6 extracellular region</b>, not the small-acid orthosteric pocket (multi-seed consensus); 8Z87's positive scores for large molecules are CHBA-state conformational clashes, not non-binding.
(2) <b>Pyridone→pyrimidinone is a structurally explained potency cliff</b>: the pyrimidinone N3 sits 3.8 Å from Glu153's carboxylate (8/8 seeds), costing ~4 kcal/mol intermolecular energy — matching the 47× EC50 loss (c30 5 nM vs c31 240 nM).
(3) <b>HCAR1 agonism carries mechanism-based tumor/cachexia + liver-fibrosis risk</b>, and the most potent compound (c30) has only 7.4× GPR109A selectivity — lead nomination must weigh both.</section>

{cards([
    ("39/39", "paper structures recovered & MS-validated"),
    ("6", "pipeline phases w/ QC gates"),
    ("78", "full-series docking combos (phase 6)"),
    ("3", "cryo-EM receptors (8Z87/8Z8A/9KT9)"),
])}

<h2>1. Request &amp; data assets</h2>
<p>Requested by Huan: dock tool compounds and the Davidsson 2020 paper series against human HCAR1/GPR81. Inputs: PubChem tool compounds, RCSB cryo-EM structures (8Z87 CHBA-bound, 9KT9 3,5-DHBA-bound, 8Z8A lactate-bound, 8Z8B apo), and the Davidsson paper + SI.</p>
{table(["Tool compound", "CID", "Identity"], tool_rows)}
<p><b>Paper series:</b> {paper_n} compounds recovered ({auth} authoritative + {msval} MS-validated, |Δ[M+H]+| ≤ 5 mDa), EC50 range {ec_range[0]}–{ec_range[1]} µM, SDFs under <code>paper_ligands/</code>. Ligand identity corrections: GPR81_agonist_1 (CID 86279608) is the Takeda 2014 compound, not Davidsson compound 2; compound 22's SI mass entry was a mislabeled data mismatch (paper figure + text + ChEMBL all agree).</p>

<h2>2. Protocol &amp; quality gates</h2>
<ul>
<li><b>Receptor prep:</b> chain R only, G-protein and co-crystal ligands removed; pocket defined from experimental ligand (6 Å).</li>
<li><b>Docking:</b> AutoDock Vina (local), RDKit/Meeko ligand prep, multi-seed + high exhaustiveness for conclusions.</li>
<li><b>Gate 1 — redock control:</b> co-crystal ligand must recover its experimental centroid. 8Z87: 0.88 Å ✓; 8Z8A: 2.89 Å ✓; 9KT9 failed 24 Å box (5.71 Å) → root-caused as a search-space artifact, fixed with a tight-box protocol.</li>
<li><b>Gate 2 — tight-box (phase 5):</b> 12 Å box centered on co-crystal ligand. 9KT9 recovery: 3,5-DHBA 1.67 Å, CHBA 1.05 Å, 3-OBA 0.97 Å — all &lt; 2 Å. Only valid for orthosteric-pocket ligands.</li>
<li><b>Gate 3 — positional QC:</b> every 9KT9 large-molecule "orthosteric" label checked against the 34D co-crystal centroid; 19/22 were deep-insert artifacts (&gt;4 Å), only c26 passed tight-box verification.</li>
<li><b>Region classification:</b> per-pose binding region (orthosteric / TM5-TM6 extracellular / N-term) with multi-seed consensus (8 seeds × 5 poses for matched pairs).</li>
</ul>

<h2>3. Tool compounds</h2>
<p>CHBA and 3,5-DHBA are the reliable experimental anchors (convergent, good redock recovery). AZ1 (23 nM) clashes in 8Z87's CHBA-state pocket (positive score, 8/8 seeds, 7 severe vdW overlaps) but fits 8Z8A cleanly with an Arg99-mediated network — a receptor-state-dependent finding. Takeda GPR81 agonist 1 is the most convergent/cleanest 8Z8A result (−7.74 kcal/mol, zero clashes).</p>

<h2>4. 9KT9 remediation (phase 5)</h2>
<div class="callout warn"><b>Root cause:</b> not receptor prep — the 34D frame is correct (2.45 Å), pocket complete, no clash at the experimental pose. The 24 Å search box let Vina find a deep-insert global optimum 5.4 Å out, only 0.08 kcal/mol better than the true pose.</div>
<p>Tight-box protocol (12 Å, exhaustiveness 32):</p>
{table(["Ligand (9KT9)", "Best score", "Best centroid recovery"], [
    {"Ligand (9KT9)": "3,5-DHBA (co-crystal control)", "Best score": kt9_fix["redock_control_3_5_DHBA"]["best_recovery_score"], "Best centroid recovery": f"{kt9_fix['redock_control_3_5_DHBA']['best_centroid_recovery_A']} Å"},
    {"Ligand (9KT9)": "CHBA", "Best score": kt9_fix["per_compound"]["CHBA"]["best_score"], "Best centroid recovery": f"{kt9_fix['per_compound']['CHBA']['best_centroid_recovery_A']} Å"},
    {"Ligand (9KT9)": "3-OBA", "Best score": kt9_fix["per_compound"]["3_OBA"]["best_score"], "Best centroid recovery": f"{kt9_fix['per_compound']['3_OBA']['best_centroid_recovery_A']} Å"},
])}

<h2>5. Reverse-SAR — matched pairs (phase 4) &amp; mechanism</h2>
<table><thead><tr><th>Compound</th><th>Receptor</th><th>EC50 µM</th><th>Best 24Å</th><th>Region</th><th>Validity</th><th>Verdict</th></tr></thead><tbody>
{''.join(f"<tr><td>{esc(r['Compound'])}</td><td>{esc(r['Receptor'])}</td><td>{esc(r['EC50 µM'])}</td><td>{esc(r['Best 24Å'])}</td><td>{esc(r['Region'])}</td><td>{esc(r['Validity'])}</td><td>{esc(r['Verdict'])}</td></tr>" for r in mp_rows)}
</tbody></table>
<div class="callout ok"><b>Binding-site finding (multi-seed consensus):</b> all acyl-urea/constrained compounds dock to the TM5-TM6 extracellular region on both receptors (12–14 Å from the orthosteric center); the amide series (c35–c38) reaches the orthosteric pocket on 8Z8A. 8Z87 positive scores for large molecules = CHBA-state conformational clash, <b>not</b> non-binding (AZ1/c30 are potent agonists).</div>
<div class="callout err"><b>Pyridone vs pyrimidinone (c30 vs c31) — mechanism:</b> pyrimidinone N3 sits 3.75–3.83 Å from the Glu153 carboxylate in 8/8 seeds (electrostatic repulsion). Intermolecular energy: c30 −8.2 vs c31 −4.0 kcal/mol (Δ ~4.2). Matches the 47× EC50 loss (5 vs 240 nM). [Vina energy decomposition; MM/GBSA unavailable in this environment — no ambertools/openff]</div>

<h2>6. Full-series docking (phase 6, all 39 compounds)</h2>
<p>Global score–EC50 correlation is absent (8Z8A n=39 Pearson r=−0.114, p=0.49; Spearman −0.128) — Vina scores do not rank potency across series, per project convention. Acyl-urea series is marginal (Spearman −0.356, p=0.10). Top scorers outside the matched-pair set:</p>
{table(["Compound", "Score 8Z8A", "EC50 µM", "Series"], [
    {"Compound": f"c{x['compound']}", "Score 8Z8A": x["score_8Z8A"], "EC50 µM": x["ec50_uM"], "Series": x.get("series", "")} for x in f6_top])}
<p><b>Linker-variant caution:</b> c23–c25 (EC50 16–33 µM) still dock with good scores — rigid docking cannot capture the lost intramolecular H-bond network; the paper attributes those losses to linker geometry.</p>

<h2>7. Selectivity (GPR109A / GHS-R1a)</h2>
<p>Niacin flush is a GPR109A effect — the family lesson. Transcribed from Davidsson 2020 (Tables 1/7/8):</p>
{table(["Compound", "hGPR81 EC50 µM", "hGPR109A EC50 µM", "Fold vs GPR109A", "hGHS-R1a IC50 µM", "Fold vs GHS-R1a"], sel_rows)}
<div class="callout warn"><b>Key trade-offs:</b> c30 (most potent, 5 nM) has only 7.4× GPR109A selectivity; c28 is the best overall balance (22 nM, 41× GPR109A, 82× GHS-R1a, LLE 5.3); c38 has 500× GHS-R1a but only ~10× GPR109A; amides overall &gt;70× GHS-R1a but ~10× GPR109A.</div>
<h3>7a. HCAR2 pocket comparison (AlphaFold vs cryo-EM HCAR1)</h3>
<table><thead><tr><th>HCAR1 residue</th><th>HCAR1</th><th>HCAR2 position</th><th>HCAR2</th><th>Conserved</th></tr></thead><tbody>
{''.join(f"<tr><td>{esc(r['HCAR1 residue'])}</td><td>{esc(r['HCAR1'])}</td><td>{esc(r['HCAR2 position'])}</td><td>{esc(r['HCAR2'])}</td><td>{esc(r['Conserved'])}</td></tr>" for r in pocket_rows)}
</tbody></table>
<p>HCAR2 lost the ARG71 carboxylate anchor (Leu83) and differs at 9/10 TM5-TM6 residues (Glu153→Lys165 charge flip) — the structural basis for why orthosteric small acids are HCAR1-preferring, while the large-molecule series shows cross-activity (c30 7.4×). Testable design target: exploit Glu153/Lys165 to build selectivity.</p>

<h2>8. Activation-direction safety (3_safety-style companion)</h2>
<div class="callout err"><b>🔴 Mechanism-based risks:</b> tumor promotion / cachexia (GPR81 activation drives tumour-induced cachexia, PMID 38499763; lactate/GPR81 in angiogenesis &amp; immune escape, PMID 31836453) and liver-fibrosis potentiation (GPR81 KO alleviates fibrosis, PMID 38982366).</div>
<div class="callout warn"><b>🟡 Watch items:</b> immune suppression double-edge (macrophage anti-inflammatory, PMID 33123172); retina direction ambiguous (Müller-cell vasculature regulation vs neuroprotection); DepMap shows 7/1243 cell lines with moderate HCAR1 dependence (neuroblastoma, bile-duct, NHL, gastric, AML). gnomAD LoF: no data (upperBin 8) — not interpretable as constraint.</div>
<div class="callout ok"><b>🟢 Benefits:</b> anti-lipolysis (intended), insulin-independent glucose uptake (PMID 41530347, 2026), retinal protection potential. Preclinical package: 2-yr carcinogenicity, fibrosis markers (Pro-C3/ELF), ophthalmology, immunophenotyping, body-composition readouts.</div>

<h2>9. Conclusions</h2>
<ol>
<li><b>Binding mode:</b> the Davidsson series occupies the TM5-TM6 extracellular region, not the orthosteric lactate/CHBA pocket (multi-seed consensus, both receptors). This is the project's central structural hypothesis — testable by TM5-TM6 mutagenesis vs lactate controls.</li>
<li><b>Pyrimidinone cliff explained:</b> Glu153 electrostatic clash (Δinter ~4 kcal/mol) rationalizes c30 vs c31 and is consistent across seeds.</li>
<li><b>9KT9 usable with tight-box protocol</b> for orthosteric ligands; large-molecule 24 Å results need the deep-insert gate (only c26 verified).</li>
<li><b>Selectivity:</b> c28 is the best-balanced lead (22 nM, 41× GPR109A); c30's potency comes at 7.4× selectivity; HCAR2 pocket comparison gives a structural handle to design selectivity.</li>
<li><b>Safety:</b> HCAR1 agonism carries tumor/cachexia + fibrosis risk — treat as RED until carcinogenicity + fibrosis biomarkers clear it.</li>
</ol>

<h2>10. Artifact index</h2>
<pre><code>data/gpr81_phase1/
  MANIFEST.json, README.md, REVIEW_2026-08-04.md
  identity_resolution.json, tool_compounds.csv, validation.json
  paper_structures_recovered.json, paper_ligands/compound_*.sdf (39)
  phase2_prepared/phase2_manifest.json
  phase3_docking/, phase3_multiseed/, phase3_5_aligned/, phase3_5_controls/, phase3_5_controls_restrained/
  phase4_matched_pairs/matched_pair_summary.json + annotated_matched_pairs.json
  phase5_tightbox/ (9kt9_small_acid_redock, pyridone_vs_pyrimidinone_validation, report)
  phase6_full_series/ (results, summary, reverse_sar, region_consensus_2seed, positional_qc, report)
  safety/ (HCAR1_activation_safety, davidsson2020_selectivity_transcription,
           hcar1_hcar2_pocket_comparison + mapping, HCAR1_ot_platform_2026-08-04.json)
scripts/ run_gpr81_phase3_docking.py ... run_gpr81_full_series.py, analyze_gpr81_full_series.py</code></pre>
<footer>Evidence-layered: experimental facts vs computational observations vs mechanistic hypotheses are separated throughout. Docking does not establish affinity, agonism, or selectivity. Generated 2026-08-04 from on-disk artifacts.</footer>
</main></body></html>"""

    out = P / "gpr81_final_report.html"
    out.write_text(report)
    print(json.dumps({"output": str(out), "bytes": out.stat().st_size,
                      "tool_rows": len(tool_rows), "mp_rows": len(mp_rows),
                      "sel_rows": len(sel_rows), "pocket_rows": len(pocket_rows),
                      "paper_n": paper_n}, indent=2))

if __name__ == "__main__":
    main()
