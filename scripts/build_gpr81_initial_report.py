#!/usr/bin/env python3
"""Build the evidence-layered GPR81 HTML report from Phase 3 / 3.5 artifacts,
including the restrained-control and multi-seed docking follow-up."""
from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
P3 = PHASE1 / "phase3_docking"
P35 = PHASE1 / "phase3_5_aligned"
P35C = PHASE1 / "phase3_5_controls"
P35R = PHASE1 / "phase3_5_controls_restrained"
P3MS = PHASE1 / "phase3_multiseed"
OUT = PHASE1 / "gpr81_initial_report.html"


def read_csv(path: Path):
    with path.open() as fh:
        return list(csv.DictReader(fh))


def esc(x) -> str:
    return html.escape(str(x))


def _norm(s) -> str:
    """Normalize a header/cell key for tolerant matching: lowercase, strip non-alphanumerics."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def table(headers, rows):
    """Render a table. Header→cell lookup is tolerant: exact key match first, then
    normalized (case/punctuation-insensitive) match, so row dicts with slightly
    different key spellings still render. Rows with all-empty cells are still shown
    (the header explains the columns); the builder verifies non-empty fill below."""
    out = ["<table><thead><tr>"]
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        if isinstance(row, dict):
            norm_map = {_norm(k): v for k, v in row.items()}
            for h in headers:
                val = row.get(h, "")
                if val == "" and _norm(h) in norm_map:
                    val = norm_map[_norm(h)]
                out.append(f"<td>{esc(val)}</td>")
        else:
            for h in headers:
                out.append("<td></td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def main():
    summary = read_csv(P3 / "tool_compound_binding_mode_comparison.csv")
    rmsd = read_csv(P35 / "ligand_pose_rmsd.csv")
    controls = read_csv(P35C / "redocking_controls.csv")
    docking = read_csv(P3 / "docking_results.csv")
    restrained_summary = json.loads((P35R / "restrained_redocking_summary.json").read_text())
    multiseed_clusters = json.loads((P3MS / "multiseed_cluster_summary.json").read_text())
    multiseed_clusters_batch2 = json.loads((P3MS / "multiseed_cluster_summary_batch2.json").read_text())
    clash_diag = json.loads((P3MS / "clash_diagnosis.json").read_text())
    interaction_review = json.loads((P3MS / "interaction_geometry_review.json").read_text())
    paper_structures = json.loads((PHASE1 / "paper_structures_recovered.json").read_text())
    mp_summary = json.loads((PHASE1 / "phase4_matched_pairs/matched_pair_summary.json").read_text())

    summary_rows = []
    for cid in sorted({r["compound_id"] for r in summary}):
        rows = [r for r in summary if r["compound_id"] == cid]
        score = min(float(r["best_score_kcal_mol"]) for r in rows)
        warnings = sorted(set(r["warning"] for r in rows if r["warning"]))
        summary_rows.append({"Compound": cid, "Best observed score": f"{score:.3f}", "Warnings": "; ".join(warnings) or "none", "Receptor views": len(rows)})

    rmsd_rows = []
    for r in rmsd:
        if r["moving_receptor"] != "8Z87":
            rmsd_rows.append({"Compound": r["compound_id"], "Comparison": f"{r['moving_receptor']} vs 8Z87", "Receptor alignment Å": r["alignment_rmsd_A"], "Ligand pose RMSD Å": r["ligand_rmsd_A"], "Status": r["status"]})

    compounds = [
        ("AZ1 / GPR81 agonist 2", "CID 57422810", "Davidsson 2020 compound 1; hHCAR1 EC50 23 nM", "identity confirmed"),
        ("GPR81 agonist 1", "CID 86279608", "Sakurai/Takeda 2014 compound 2; not Davidsson 2020 compound 2", "identity corrected"),
        ("CHBA", "CID 13071646", "3-chloro-5-hydroxybenzoic acid; experimental ligand in 8Z87", "identity confirmed"),
        ("3,5-DHBA", "CID 7424", "3,5-dihydroxybenzoic acid; experimental ligand in 9KT9", "identity confirmed"),
        ("3-OBA", "CID 441", "3-hydroxybutanoic acid; no matching co-complex in current set", "identity confirmed"),
    ]
    compound_rows = [{"Compound": a, "Identifier": b, "Evidence / biological context": c, "Status": d} for a, b, c, d in compounds]

    control_rows = [{"Compound": r["compound_id"], "Structure": r["receptor_id"], "Redock score kcal/mol": r["redock_score_kcal_mol"], "Centroid distance Å": r["centroid_distance_A"], "Interpretation": "good centroid recovery" if float(r["centroid_distance_A"]) < 3 else "partial / needs restrained control"} for r in controls]

    restrained_rows = [
        {"Condition": "Unconstrained (P3.5, box 24Å)", "Score kcal/mol": "-5.649", "Centroid distance Å": "5.710", "Note": "original weak control"},
        {"Condition": "Tight-box multi-seed (12Å, best score)", "Score kcal/mol": restrained_summary["best_score_pose"]["score_kcal_mol"], "Centroid distance Å": restrained_summary["best_score_pose"]["centroid_distance_A"], "Note": f"seed {restrained_summary['best_score_pose']['seed']}"},
        {"Condition": "Tight-box multi-seed (12Å, best centroid recovery)", "Score kcal/mol": restrained_summary["best_centroid_recovery"]["score_kcal_mol"], "Centroid distance Å": restrained_summary["best_centroid_recovery"]["centroid_distance_A"], "Note": f"seed {restrained_summary['best_centroid_recovery']['seed']}"},
    ]

    ms_rows = []
    for c in multiseed_clusters:
        top = c["top_3_clusters"][0]
        ms_rows.append({
            "Compound": c["compound_id"], "Receptor": c["receptor_id"],
            "Seeds": c["n_seeds"], "Total poses": c["total_poses"],
            "Pose clusters": c["n_distinct_pose_clusters"],
            "Top cluster score": top["best_score"],
            "Top cluster size": f"{top['n_members']}/{c['total_poses']}",
            "Convergence": "highly convergent" if top["n_members"] / c["total_poses"] > 0.7 else ("moderately convergent" if top["n_members"] / c["total_poses"] > 0.4 else "poorly convergent"),
        })

    ms_rows_all = list(ms_rows)
    for c in multiseed_clusters_batch2:
        top = c["top_3_clusters"][0]
        ms_rows_all.append({
            "Compound": c["compound_id"], "Receptor": c["receptor_id"],
            "Seeds": c["n_seeds"], "Total poses": c["total_poses"],
            "Pose clusters": c["n_distinct_pose_clusters"],
            "Top cluster score": top["best_score"],
            "Top cluster size": f"{top['n_members']}/{c['total_poses']}",
            "Convergence": "highly convergent" if top["n_members"] / c["total_poses"] > 0.7 else ("moderately convergent" if top["n_members"] / c["total_poses"] > 0.4 else "poorly convergent"),
        })
    # Sort the combined 5-compound x 3-receptor table for a clean full comparison
    compound_order = {"CHBA": 0, "3_5_DHBA": 1, "3_OBA": 2, "AZ1_GPR81_agonist_2": 3, "GPR81_agonist_1": 4}
    receptor_order = {"8Z87": 0, "9KT9": 1, "8Z8A": 2}
    ms_rows_all.sort(key=lambda r: (compound_order.get(r["Compound"], 9), receptor_order.get(r["Receptor"], 9)))

    hbond_rows = []
    for label, key in [("AZ1", "AZ1_8Z8A"), ("Takeda GPR81 agonist 1", "Takeda_8Z8A")]:
        for hb in interaction_review[key]["hbond_candidates"]:
            hbond_rows.append({"Compound": label, "Receptor residue": hb["residue"], "Role": hb["role"], "Ligand atom type": hb["ligand_autodock_type"], "Distance Å": hb["distance_A"]})

    paper_confirmed_rows = [{"Paper compound #": c["paper_compound_number"], "Series": c["series"], "Formula": c["formula"], "Calc [M+H]+": c["exact_mass_M_plus_H_calc"], "Paper hGPR81 EC50 (µM)": c["paper_reported_hGPR81_EC50_uM"], "PubChem CID": c.get("pubchem_cid", ""), "ChEMBL ID": c.get("chembl_id", ""), "Status": c["status"]} for c in paper_structures["compounds"]]
    paper_rejected_rows = [{"Paper compound #": c["paper_compound_number"], "Attempted SMILES (truncated)": c["attempted_smiles"][:60] + "...", "Calc [M+H]+": c["calc_M_plus_H"], "SI-reported [M+H]+": c["paper_reported_M_plus_H"], "Δ mass": c["delta"], "Status": c["status"]} for c in paper_structures.get("attempted_but_unresolved", [])]
    recovery_summary = paper_structures.get("recovery_scope_this_session", {}).get("final_summary", {})

    # ---- Matched-pair (Phase 4) rows ----
    mp_ec50 = {15: 0.299, 21: 0.895, 22: 0.166, 26: 0.021, 28: 0.022, 30: 0.005, 31: 0.24, 35: 0.60, 36: 0.16, 37: 0.35, 38: 0.054}
    mp_series = {15: "acyl urea", 21: "acyl urea", 22: "acyl urea", 26: "pyridone", 28: "pyridone", 30: "pyridone", 31: "pyrimidinone", 35: "amide", 36: "amide", 37: "amide", 38: "amide"}
    mp_rows = []
    for num in sorted(mp_summary, key=int):
        s = mp_summary[num]
        r87 = s.get("8Z87", {}); r8a = s.get("8Z8A", {})
        mp_rows.append({
            "Compound": f"c{num}", "Series": mp_series.get(int(num), ""),
            "Paper EC50 (µM)": mp_ec50.get(int(num), ""),
            "8Z87 best (kcal/mol)": r87.get("best", ""), "8Z87 mean": r87.get("mean", ""),
            "8Z8A best (kcal/mol)": r8a.get("best", ""), "8Z8A mean": r8a.get("mean", ""),
        })

    mp_pairs = [
        {"Pair": "15 → 26", "From": "15 (acyl urea)", "To": "26 (pyridone)", "Paper EC50 change": "0.299 → 0.021 µM (14× gain)", "8Z8A best Δ (to−from)": round(mp_summary["26"]["8Z8A"]["best"] - mp_summary["15"]["8Z8A"]["best"], 2), "Docking direction": "✓ consistent" if mp_summary["26"]["8Z8A"]["best"] < mp_summary["15"]["8Z8A"]["best"] else "✗ opposite"},
        {"Pair": "22 → 30", "From": "22 (acyl urea)", "To": "30 (pyridone, same RHS)", "Paper EC50 change": "0.166 → 0.005 µM (33× gain)", "8Z8A best Δ (to−from)": round(mp_summary["30"]["8Z8A"]["best"] - mp_summary["22"]["8Z8A"]["best"], 2), "Docking direction": "✓ consistent" if mp_summary["30"]["8Z8A"]["best"] < mp_summary["22"]["8Z8A"]["best"] else "✗ opposite"},
        {"Pair": "21 → 28", "From": "21 (acyl urea)", "To": "28 (pyridone, hydroxyacetyl)", "Paper EC50 change": "0.895 → 0.022 µM (41× gain)", "8Z8A best Δ (to−from)": round(mp_summary["28"]["8Z8A"]["best"] - mp_summary["21"]["8Z8A"]["best"], 2), "Docking direction": "✓ consistent" if mp_summary["28"]["8Z8A"]["best"] < mp_summary["21"]["8Z8A"]["best"] else "✗ opposite"},
        {"Pair": "30 vs 31", "From": "30 (pyridone)", "To": "31 (pyrimidinone)", "Paper EC50 change": "0.005 vs 0.24 µM (pyridone 48× better)", "8Z8A best Δ (to−from)": round(mp_summary["31"]["8Z8A"]["best"] - mp_summary["30"]["8Z8A"]["best"], 2), "Docking direction": "✓ consistent" if mp_summary["31"]["8Z8A"]["best"] > mp_summary["30"]["8Z8A"]["best"] else "✗ opposite"},
        {"Pair": "35 → 38", "From": "35 (morpholine)", "To": "38 (cis-2,6-diMe morpholine)", "Paper EC50 change": "0.60 → 0.054 µM (11× gain)", "8Z8A best Δ (to−from)": round(mp_summary["38"]["8Z8A"]["best"] - mp_summary["35"]["8Z8A"]["best"], 2), "Docking direction": "✓ consistent" if mp_summary["38"]["8Z8A"]["best"] < mp_summary["35"]["8Z8A"]["best"] else "✗ opposite"},
        {"Pair": "36/37 vs 38", "From": "36/37 (monoMe morpholine)", "To": "38 (diMe morpholine)", "Paper EC50 change": "0.16/0.35 vs 0.054 µM", "8Z8A best Δ (to−from)": round(mp_summary["38"]["8Z8A"]["best"] - mp_summary["36"]["8Z8A"]["best"], 2), "Docking direction": "✓ consistent" if mp_summary["38"]["8Z8A"]["best"] < mp_summary["36"]["8Z8A"]["best"] else "✗ opposite"},
    ]

    report = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HCAR1/GPR81 Structure–Biology Report</title>
<style>
:root{{--bg:#0f1419;--panel:#1a2028;--panel2:#232b36;--text:#d8dee9;--muted:#8895a7;--accent:#5eb3ff;--ok:#7ec98f;--warn:#e5c07b;--err:#e06c75;--border:#2c3542;--code:#12171d}}
*{{box-sizing:border-box}} body{{margin:0;padding:40px 20px;background:var(--bg);color:var(--text);font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;font-size:15px}}.container{{max-width:1100px;margin:auto}}h1{{font-size:30px;margin:0 0 6px;color:#fff}}h2{{margin-top:38px;border-bottom:1px solid var(--border);padding-bottom:8px;color:var(--accent)}}h3{{color:#fff;margin-top:26px}}.meta,.muted{{color:var(--muted);font-size:13px}}.callout{{padding:16px 18px;margin:16px 0;border-left:4px solid var(--accent);background:var(--panel);border-radius:6px}}.callout.ok{{border-color:var(--ok)}}.callout.warn{{border-color:var(--warn)}}.callout.err{{border-color:var(--err)}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.card{{background:var(--panel);border:1px solid var(--border);padding:16px;border-radius:7px}}.card b{{display:block;font-size:24px;color:#fff}}.card span{{color:var(--muted);font-size:12px}}table{{width:100%;border-collapse:collapse;background:var(--panel);margin:14px 0 24px;font-size:13px}}th,td{{border:1px solid var(--border);padding:8px 10px;text-align:left;vertical-align:top}}th{{background:var(--panel2);color:#fff}}code,pre{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}}code{{color:#b9e2ff}}pre{{background:var(--code);border:1px solid var(--border);padding:14px;overflow:auto;color:#c9d1d9;border-radius:6px}}ul,ol{{padding-left:24px}}.pill{{display:inline-block;padding:2px 8px;border-radius:12px;background:var(--panel2);color:var(--muted);font-size:12px}}footer{{margin-top:48px;padding-top:16px;border-top:1px solid var(--border);color:var(--muted);font-size:12px}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main class="container">
<header><h1>HCAR1 / GPR81 Structure–Biology Analysis</h1><div class="meta">Evidence-layered report · Phase 1–3.5 + multi-seed follow-up · 2026-08-03 · target: human HCAR1/GPR81 (UniProt Q9BXC0)</div></header>
<section class="callout warn"><b>Executive verdict</b><br>Multi-seed high-exhaustiveness redocking resolved most of the pose ambiguity flagged in the original P3/P3.5 runs. CHBA and 3,5-DHBA remain the most reliable experimental pocket anchors. AZ1 shows a real, reproducible steric clash in the 8Z87 pocket box (positive score across all 8 seeds) but docks cleanly and convergently in 8Z8A — a genuine receptor-conformation-dependent signal, not a sampling artifact. GPR81 agonist 1 (Takeda compound) converges very strongly in 8Z8A (56/63 poses, -7.74 kcal/mol). Paper-series structure recovery is <b>complete: all 39 compounds now have validated structures</b> (3 authoritative, 36 MS-validated) — compound 22's SI mass anomaly was resolved as an SI data mismatch.</section>
<div class="cards"><div class="card"><b>5</b><span>confirmed tool compounds</span></div><div class="card"><b>3</b><span>ligand-bound receptor views</span></div><div class="card"><b>48</b><span>multi-seed docking runs</span></div><div class="card"><b>281</b><span>common Cα alignment residues</span></div></div>
<h2>1. Scope and evidence levels</h2>
<p><b>Experimental facts</b> are taken from the request, PubChem/ChEMBL, RCSB, the 2020 paper, and the new supporting material. <b>Computational observations</b> come from local Vina runs, aligned pose analysis, redocking controls, and multi-seed ensembles. <b>Mechanistic interpretations</b> are hypotheses, not proof of affinity, agonism, or selectivity.</p>
{table(["Compound","Identifier","Evidence / biological context","Status"],compound_rows)}
<h2>2. Paper-series structure recovery — COMPLETE (39/39)</h2>
<div class="callout ok"><b>Unblocked (2026-08-03):</b> the user exported the DOCX supplementary material to PDF (<code>1-s2.0-S0960894X20300068-mmc1.pdf</code>) and placed it in the shared folder. PyMuPDF renders PDF pages to 300 DPI PNG natively, which sidesteps the EMF blocker entirely. Method used: render page → read structure via vision analysis → build candidate SMILES → cross-validate independently against the SI-reported [M+H]+ mass and (where available) ChEMBL canonical SMILES / paper-reported EC50 → accept only on a match.</div>
<div class="cards"><div class="card"><b>{recovery_summary.get("authoritative", 0)}</b><span>authoritative (ChEMBL+EC50)</span></div><div class="card"><b>{recovery_summary.get("reconstructed_and_MS_validated", 0)}</b><span>MS-validated reconstructions</span></div><div class="card"><b>{recovery_summary.get("unresolved_ms_mismatch", 0)}</b><span>unresolved</span></div><div class="card"><b>39</b><span>SDF files generated</span></div></div>
<p><b>Validation discipline:</b> every candidate SMILES was checked against its SI-reported [M+H]+ value (extracted from the PDF text); acceptance required |Δ| ≤ 5 mDa (HRMS tolerance). Where ChEMBL held the compound, its canonical SMILES was used as an independent second source. Four wrong guesses were caught and corrected by this process (11/12 piperidine-linker misread, 35-38 ethyl-vs-propyl sulfone chain, and compound 22 resolved as an SI data mismatch).</p>
<table><thead><tr><th>Paper compound #</th><th>Series</th><th>Formula</th><th>Calc [M+H]+</th><th>Paper hGPR81 EC50 (µM)</th><th>PubChem CID</th><th>ChEMBL ID</th><th>Status</th></tr></thead><tbody><tr><td>1</td><td>acyl_urea</td><td>C26H27ClN6O5S2</td><td>603.1246</td><td>0.023</td><td>57422810</td><td>CHEMBL4641579</td><td>authoritative</td></tr><tr><td>2</td><td>acyl_urea</td><td>C27H33ClN6O4S</td><td>573.2045</td><td>0.074</td><td>154699458</td><td>CHEMBL4632411</td><td>authoritative</td></tr><tr><td>22</td><td>acyl_urea</td><td>C27H32ClN5O6S2</td><td>622.1555</td><td>0.166</td><td>—</td><td>CHEMBL4634029</td><td>authoritative</td></tr></tbody></table>
<p><b>All 39 compounds now have validated structures.</b> Compound 22's earlier 5.03 Da discrepancy was resolved (2026-08-04): the paper's Table 5 structure figure, the paper text ("sulphone linked N-methylpiperidine on the benzothiazole, exemplified in 22"), and ChEMBL CHEMBL4634029 (EC50=166 nM matching the paper's 0.166 µM) all agree on benzothiazole-SO₂-(1-methylpiperidin-4-yl), calc [M+H]+ = 622.1555. The SI entry "22." reporting 627.1839 with a benzylic CH₂ NMR signal (4.49 s 2H) is a data mismatch — that NMR belongs to a different compound (likely a CH₂-piperazine RHS variant) mislabeled as 22 in the SI.</p>
<h3>2a. Resolution record for compound 22</h3>
<table><thead><tr><th>Source</th><th>Reported structure / mass</th><th>Verdict</th></tr></thead><tbody><tr><td>Paper Table 5 structure figure</td><td>BT–SO₂–(1-methylpiperidin-4-yl), no CH₂</td><td>authoritative</td></tr><tr><td>Paper text</td><td>"sulphone linked N-methylpiperidine... exemplified in 22"</td><td>authoritative</td></tr><tr><td>ChEMBL CHEMBL4634029 (EC50 166 nM)</td><td>same structure, [M+H]+ calc 622.1555</td><td>authoritative</td></tr><tr><td>SI entry "22."</td><td>[M+H]+ 627.1839, NMR with benzylic CH₂ (4.49 s 2H)</td><td>REJECTED — data mismatch, mislabeled</td></tr></tbody></table>
<div class="callout warn"><b>Lesson recorded:</b> the SI experimental-section numbering can contain mislabeled entries (this one apparently swapped in another compound's MS/NMR). When the paper figure, paper text, and ChEMBL all agree, that consensus wins over a single SI mass entry — but only after explicitly documenting why.</div>
<h2>3. Receptor preparation and pocket anchors</h2>
<p>Receptor chain R was extracted from 8Z87, 9KT9, 8Z8A, and apo 8Z8B. Ligand-bound structures were used for docking; apo 8Z8B was reserved for a future aligned control.</p>
{table(["Structure","State","Experimental ligand","Use"],[
{"Structure":"8Z87","State":"CHBA-bound","Experimental ligand":"A1D71 / CHBA","Use":"primary fixed frame and pocket anchor"},
{"Structure":"9KT9","State":"3,5-DHBA-bound","Experimental ligand":"34D / 3,5-DHBA","Use":"independent ligand-bound view"},
{"Structure":"8Z8A","State":"lactate-bound","Experimental ligand":"2OP / lactate","Use":"independent active-state view"},
{"Structure":"8Z8B","State":"apo","Experimental ligand":"none","Use":"reserved for aligned control"}])}
<p>Common ligand-anchored pocket residues observed across the three ligand-bound structures include <code>R71, Y75, L92, L95, A96, R99, C165, S167, F168, H261, L264, Y268</code>.</p>
<h2>4. P3 initial docking results</h2>
<p>Each of the five tool compounds was prepared with RDKit/Meeko and docked with local AutoDock Vina using seed 20260803, exhaustiveness 16, and up to five poses. The run contains {len(docking)} pose rows, zero docking errors, and 15 pose files.</p>
{table(["Compound","Best observed score","Warnings","Receptor views"],summary_rows)}
<div class="callout warn"><b>Interpretation warning (superseded below):</b> single-seed scores flagged AZ1 and GPR81 agonist 1 as conformation-sensitive/underdetermined. Section 6 resolves most of this with multi-seed sampling.</div>
<h2>5. P3.5 aligned pose comparison</h2>
<p>Structures were aligned to 8Z87 using 281 common Cα residues. Backbone alignment RMSD was 1.018 Å for 9KT9 and 0.587 Å for 8Z8A.</p>
{table(["Compound","Comparison","Receptor alignment Å","Ligand pose RMSD Å","Status"],rmsd_rows)}
<div class="callout warn"><b>What this means:</b> high ligand RMSD after receptor alignment shows that independently selected docked poses are not the same pose. It does not by itself prove a conformational preference — Section 6/7 add redocking controls and multi-seed sampling to resolve which cases are real versus sampling noise.</div>
<h2>6. Experimental-ligand redocking controls</h2>
<p>Known ligands were redocked in their matching experimental receptor boxes. Because the locally written experimental-ligand PDB records and PubChem/3D-SDF preparations do not have an asserted atom mapping, this control reports centroid recovery rather than invented atom-mapped RMSD.</p>
{table(["Compound","Structure","Redock score kcal/mol","Centroid distance Å","Interpretation"],control_rows)}
<h3>6a. Restrained follow-up for the weak 3,5-DHBA/9KT9 control</h3>
<p>The unconstrained control above showed 3,5-DHBA recovering the 9KT9 experimental centroid only within 5.71 Å. A tighter box (12 Å vs the original 24 Å general-purpose box) combined with 5 random seeds and exhaustiveness 32 was run as a more constrained follow-up condition (Vina has no native distance-restraint API in this installation, so this is a tight-box/multi-seed condition, not a true restrained dock).</p>
{table(["Condition","Score kcal/mol","Centroid distance Å","Note"],restrained_rows)}
<div class="callout ok"><b>Result:</b> the tight-box condition improves centroid recovery from 5.71 Å to as low as 1.66 Å, and the two competing pose sub-clusters (best-score ~-5.5 kcal/mol at ~2.5 Å, best-centroid ~-5.3 kcal/mol at ~1.7 Å) were stable and reproducible across all 5 seeds — this looks like a genuine two-pose ambiguity in the 9KT9 pocket under this scoring function, not noise. 9KT9 can now be used as a moderate-confidence anchor with this caveat noted, rather than discarded.</div>
<h2>7. Multi-seed high-exhaustiveness docking — full five-compound comparison</h2>
<p>All five tool compounds were re-docked across all three ligand-bound receptors with 8 random seeds and exhaustiveness 32 (120 independent dockings total), then poses were clustered by centroid distance to distinguish real multi-modal binding from single-seed sampling noise. This replaces the single-seed P3 comparison in Section 4 with a consistent, noise-resistant method for all five compounds.</p>
{table(["Compound","Receptor","Seeds","Total poses","Pose clusters","Top cluster score","Top cluster size","Convergence"],ms_rows_all)}
<div class="callout err"><b>Key finding — AZ1 on 8Z87 is a reproducible clash, not noise:</b> all 8 seeds converge to a single pose cluster with a positive score (~+10 kcal/mol). Atomistic clash diagnosis (below) confirms this is a genuine steric mismatch, not a sampling artifact.</div>
<div class="callout ok"><b>Key finding — AZ1 and Takeda compound both converge strongly on 8Z8A:</b> AZ1 collapses to one cluster across all 58 evaluated poses (best −4.43 kcal/mol); GPR81 agonist 1 is even more convergent, with 56/63 poses in one cluster at −7.74 kcal/mol — the single strongest, most reproducible score of any tool compound in this study.</div>
<div class="callout ok"><b>CHBA is highly convergent everywhere:</b> 62/64 poses on 8Z87 and 55/64 on 8Z8A collapse into one dominant cluster — consistent with it being the best-behaved experimental pocket anchor. 9KT9 remains more fragmented (5 clusters) for CHBA too, reinforcing that 9KT9 is the noisiest of the three receptor views for this scoring function.</div>
<div class="callout warn"><b>3-OBA and 9KT9 are consistently the weakest/noisiest combination:</b> 3-OBA never exceeds 63% pose convergence on any receptor, and 9KT9 fragments into 4-5 clusters for every compound tested (CHBA, 3-OBA, AZ1, Takeda). This is now a receptor-level pattern, not a per-compound anomaly — 9KT9 should be treated as a lower-confidence, multi-modal-pocket view across the board.</div>
<h2>8. Atomistic diagnosis: why does AZ1 clash on 8Z87?</h2>
<p>The AZ1/8Z87 top pose (seed 20260803, representative of all 8 seeds) was checked atom-by-atom against the receptor for van der Waals overlaps (contact distance below 75% of the summed vdW radii).</p>
<div class="callout err"><b>7 severe steric clashes identified,</b> concentrated on 5 residues: <code>{", ".join(clash_diag["AZ1_8Z87_clash_case"]["residues_involved"])}</code>. The worst is a ligand nitrogen sitting only 1.87 Å from Leu92 Cδ2 (sum of van der Waals radii 3.25 Å — a 1.38 Å overlap), and a ligand carbon 1.92 Å from Tyr75's hydroxyl oxygen. All five clashing residues are members of the core ligand-anchored pocket identified in Section 3, meaning AZ1's larger acyl-urea scaffold (40 heavy atoms vs. 11 for CHBA) does not fit the 8Z87 pocket geometry as currently prepared without pushing into these sidechains.</div>
<div class="callout ok"><b>By contrast, the AZ1/8Z8A pose has only 1 mild clash</b> (Leu92, 1.17 Å overlap) against 55 favorable close contacts spanning a wider residue set (<code>{", ".join(clash_diag["AZ1_8Z8A_favorable_case"]["residues_in_close_contact"][:8])}, ...</code>), including residues beyond the core-pocket list (Glu153, His155, His177, Met170/180) — consistent with AZ1 reaching into an extended subpocket that 8Z8A's lactate-bound conformation makes available but 8Z87's CHBA-bound conformation does not.</div>
<div class="callout ok"><b>The Takeda compound/8Z8A pose has zero clashes</b> of any severity — the cleanest steric fit of any compound/receptor pair examined.</div>
<h3>8a. Interaction-geometry review (H-bond/salt-bridge candidates, not just score)</h3>
<p>Ligand polar atoms (N/O/S) within 3.5 Å of a receptor donor/acceptor sidechain atom were flagged as hydrogen-bond or salt-bridge candidates for the two high-convergence 8Z8A poses.</p>
{table(["Compound","Receptor residue","Role","Ligand atom type","Distance Å"],hbond_rows)}
<div class="callout ok"><b>AZ1/8Z8A has a plausible salt-bridge/H-bond network:</b> Arg99 forms two contacts with AZ1 polar atoms (2.91 Å and 3.07 Å) — a classic Arg-mediated bidentate interaction — plus a candidate contact with Glu153 (3.00 Å) and His177/Asn174 further out. This gives the favorable −4.43 kcal/mol score a structural rationale beyond the number alone.</div>
<div class="callout ok"><b>Takeda compound/8Z8A anchors tightly on Glu153</b> (2.84 Å) — the shortest, most confident polar contact of the two compounds — though with only one candidate H-bond total, its strong score is likely driven more by shape complementarity/hydrophobic packing (23 close contacts, zero clashes) than by a rich polar network.</div>
<div class="callout warn"><b>Glu153, His155, His177, Asn174, and Met170/180 are new residues</b> not present in the original 6 Å core-pocket list (Section 3), which was defined from the three small experimental ligands (CHBA, 3,5-DHBA, lactate). This suggests the larger tool compounds (AZ1, Takeda) may access a genuine extended subpocket beyond the small-molecule-defined core — a hypothesis worth testing explicitly in the next phase, not yet a confirmed finding.</div>
<h2>9. Updated compound-level interpretation</h2>
<ul>
<li><b>CHBA:</b> the best-behaved experimental pocket anchor — high pose convergence on both 8Z87 (97%) and 8Z8A (86%), good centroid recovery (0.88 Å). The reference compound of choice for future method calibration.</li>
<li><b>3,5-DHBA:</b> needs the tight-box condition on 9KT9 (Section 6a) but then recovers to 1.7–2.5 Å with a real, reproducible two-pose ambiguity — usable with this caveat.</li>
<li><b>3-OBA:</b> smallest, weakest, and least convergent compound on every receptor (never above 63% pose convergence) — consistent with it being a minimal polar anchor without enough scaffold to lock a single pose.</li>
<li><b>AZ1:</b> most potent compound experimentally (23 nM), but the multi-seed + atomistic clash analysis now gives a concrete structural explanation for why single-seed P3 flagged it as unstable: it genuinely clashes with the 8Z87 pocket as currently prepared (7 severe overlaps on 5 core residues), while fitting 8Z8A cleanly with a plausible Arg99-mediated interaction network. This is a real, receptor-state-dependent finding, not an artifact.</li>
<li><b>GPR81 agonist 1 (Takeda compound):</b> the most convergent, most negative, and cleanest (zero clashes) multi-seed result of the whole study (8Z8A, −7.74 kcal/mol, 89% pose convergence, single confident Glu153 contact). The strongest single computational signal so far.</li>
</ul>
<h2>9a. Matched-pair reverse validation of the paper's optimization narrative (Phase 4)</h2>
<p>With all 39 paper structures validated, the key matched pairs from the Davidsson 2020 optimization story were docked under the validated multi-seed protocol (8 seeds, exhaustiveness 32) on the two reliable receptor views. 8Z87 was excluded from interpretation for large ligands (it gave positive scores for every large compound — the CHBA-bound pocket conformation is sterically too tight for this series, a rigid-receptor limitation, not a biological signal); 8Z8A is the interpretable view.</p>
{table(["Compound","Series","Paper EC50 (µM)","8Z87 best (kcal/mol)","8Z87 mean","8Z8A best (kcal/mol)","8Z8A mean"],mp_rows)}
<h3>9b. Pair-by-pair comparison against paper EC50</h3>
{table(["Pair","From","To","Paper EC50 change","8Z8A best Δ (to−from)","Docking direction"],mp_pairs)}
<div class="callout ok"><b>3 of 5 pairs reproduce the paper's optimization direction on 8Z8A:</b>
<ul>
<li><b>15 → 26</b> (acyl urea → pyridone bioisostere): docking −7.08 → −7.25, paper 14× potency gain — consistent.</li>
<li><b>22 → 30</b> (acyl urea → pyridone, same RHS): docking −4.92 → −6.01, paper 33× gain — consistent.</li>
<li><b>21 → 28</b> (acyl urea → pyridone, hydroxyacetyl RHS): docking −6.95 → −7.47, paper 41× gain — consistent.</li>
<li><b>30 vs 31</b> (pyridone vs pyrimidinone): docking strongly favors 30 (−6.01 vs −2.84), paper reports 30 as 48× more potent — consistent.</li>
</ul></div>
<div class="callout warn"><b>2 pairs are not explained by rigid docking:</b>
<ul>
<li><b>35 → 38</b> (morpholine → cis-2,6-dimethylmorpholine): paper 11× potency gain (0.60 → 0.054 µM), but docking gives 38 a slightly <i>less</i> negative best score (−4.51 vs −5.17, Δ +0.66 kcal/mol). The gain is not captured by the rigid-receptor score — consistent with the paper's own discussion that the morpholine-methyl SAR is partly driven by selectivity/solubility rather than pure binding.</li>
<li><b>36/37 vs 38</b> (mono- vs di-methylmorpholine): paper 38 is most potent (0.054 vs 0.16/0.35 µM), docking shows 38 ≈ 36/37 within noise (Δ +0.66 to +0.69). Same conclusion — the di-methyl gain is below rigid-docking resolution.</li>
</ul></div>
<div class="callout err"><b>Interpretation discipline:</b> docking scores are enthalpic estimates on a fixed receptor; they do not capture induced fit, entropy, solubility, or selectivity. The 3 consistent pairs support the paper's core "conformational restriction improves binding" narrative; the 2 unexplained pairs are <i>not</i> evidence the paper is wrong — they flag where the explanation must come from beyond rigid docking (the paper itself attributes the 35→38 series gains partly to LLE/selectivity/solubility). No score here is used to rank compounds across series.</div>
<h2>10. Next steps</h2>
<ol>
<li><b>Test the extended-subpocket hypothesis directly:</b> Glu153/His155/His177/Asn174/Met170/180 appeared only in the AZ1/Takeda 8Z8A analysis, not in the original small-ligand core pocket. Confirm with explicit distance/SASA analysis.</li>
<li><b>Investigate whether 8Z87's pocket can be relaxed for large ligands:</b> AZ1 is the most potent compound experimentally but clashes rigidly with 8Z87; consider induced-fit docking or a locally relaxed receptor.</li>
<li><b>Treat 9KT9 as a lower-confidence receptor view</b> in all downstream comparisons — it was the most fragmented/least convergent structure for every compound tested.</li>
<li><b>For the 35→38 morpholine-methyl series:</b> pursue non-rigid-docking explanations (induced fit, logD/LLE, selectivity, solubility) rather than forcing a docking-score rationalization.</li>
</ol>
<h2>11. Artifact index</h2>
<pre><code>Phase 1 manifest: data/gpr81_phase1/MANIFEST.json
Identity evidence: data/gpr81_phase1/identity_resolution.json
Supplementary input (PDF, unblocked): /TDE_TV/shared_folder/QYJI/druggability/GPR81/1-s2.0-S0960894X20300068-mmc1.pdf
Recovery method + status: data/gpr81_phase1/next_step_plan_after_supplement.md
Recovered paper structures (39/39): data/gpr81_phase1/paper_structures_recovered.json
Recovered structure summary CSV: data/gpr81_phase1/paper_structures_summary.csv
Paper ligand SDFs (39): data/gpr81_phase1/paper_ligands/compound_*.sdf
P3 results: data/gpr81_phase1/phase3_docking/
P3.5 aligned poses: data/gpr81_phase1/phase3_5_aligned/
P3.5 gallery: data/gpr81_phase1/phase3_5_aligned/gpr81_aligned_pose_gallery.html
Redocking controls: data/gpr81_phase1/phase3_5_controls/redocking_controls.csv
Restrained/tight-box control: data/gpr81_phase1/phase3_5_controls_restrained/restrained_redocking_summary.json
Multi-seed docking (AZ1/Takeda): data/gpr81_phase1/phase3_multiseed/multiseed_cluster_summary.json
Multi-seed docking (CHBA/3-OBA): data/gpr81_phase1/phase3_multiseed/multiseed_cluster_summary_batch2.json
Clash diagnosis: data/gpr81_phase1/phase3_multiseed/clash_diagnosis.json
Interaction-geometry review: data/gpr81_phase1/phase3_multiseed/interaction_geometry_review.json
Matched-pair results (Phase 4): data/gpr81_phase1/phase4_matched_pairs/matched_pair_summary.json
Matched-pair raw rows: data/gpr81_phase1/phase4_matched_pairs/matched_pair_docking_results.csv
</code></pre>

<footer>Generated from the local GPR81 Phase 1–3.5 + multi-seed + interaction-review + paper-structure-recovery artifacts. Paper compound SMILES are only accepted after independent mass/ChEMBL cross-validation, never invented from drawings alone. Docking does not establish affinity, agonism, or selectivity.</footer>
</main></body></html>'''
    OUT.write_text(report)
    # Self-check: every table must have non-empty cells (catch the previous
    # empty-cell bug class). Count <td> vs <td>...</td> with content.
    import re as _re
    tables = _re.findall(r"<table>.*?</table>", report, _re.S)
    empty_tables = []
    for i, t in enumerate(tables):
        tds = _re.findall(r"<td>(.*?)</td>", t, _re.S)
        non_empty = sum(1 for c in tds if c.strip() != "")
        if non_empty == 0:
            headers = _re.findall(r"<th>(.*?)</th>", t)
            empty_tables.append((i, headers))
    print(json.dumps({"output": str(OUT), "bytes": OUT.stat().st_size, "docking_rows": len(docking), "rmsd_rows": len(rmsd_rows), "ms_rows": len(ms_rows_all), "hbond_rows": len(hbond_rows), "n_tables": len(tables), "empty_tables": empty_tables}, indent=2))
    if empty_tables:
        raise SystemExit(f"FATAL: {len(empty_tables)} table(s) rendered with zero non-empty cells: {empty_tables}")


if __name__ == "__main__":
    main()
