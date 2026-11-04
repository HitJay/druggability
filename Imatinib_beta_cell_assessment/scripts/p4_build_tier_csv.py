"""P4: Build tiered CSV + unit test inputs for the imatinib beta-cell target search.

Output:
  output/final_deliverables/imatinib_beta_cell_tiered_targets_v1.csv
"""
import csv
import json
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/Imatinib_beta_cell_assessment")
DATA = BASE / "data"
DOCK = BASE / "output/docking"
MD_OUT = BASE / "output/md"
DELIV = BASE / "output/final_deliverables"
DELIV.mkdir(parents=True, exist_ok=True)

candidates = json.load(open(DATA / "p1_candidate_targets.json"))
dock_res = json.load(open(DOCK / "p2_docking_results.json"))
md_res = json.load(open(MD_OUT / "p3_md_summary.json"))

# Explicit biological tier assignments grounded in:
# (a) measured potency vs clinical free Cmax (260 nM),
# (b) HPA human beta-cell scRNA-seq (c-10) & islet endocrine (c-3) expression + IHC,
# (c) knockout / knockdown / mutagenesis directional evidence in beta cells.
TIER_MAP = {
    "ABL1":   ("T1", "Primary intrinsic beta-cell target [FACT/OBS]: Kd/Ki 1.0 nM (54-99% occ at free Cmax); expressed in beta cells (5.8 nCPM) & islets (80.8 nCPM); c-Abl translocates to ER under stress to hyperactivate IRE1a RNase, and c-Abl siRNA phenocopies imatinib beta-cell survival & NKX2-2/GLUT2/insulin induction (PMID:28380378, 17135364, 24835010)."),
    "ABL2":   ("T1", "Co-primary intrinsic beta-cell target [FACT/OBS]: Kd 6.0-12.9 nM (95.3% occ at free Cmax); high islet endocrine expression (92.8 nCPM, beta 9.4 nCPM); redundantly scaffolds & hyperactivates IRE1a at the ER membrane alongside ABL1 (PMID:28380378)."),
    "DDR1":   ("T1", "Dominant beta-cell RTK target [FACT/OBS]: Kd 0.7-43 nM (85.9% occ at free Cmax); #1 highest-expressed nanomolar imatinib kinase target in human beta cells (81.4 nCPM, IHC medium, >10x ABL1/KIT/PDGFR) and #1 Vina score (-12.46 kcal/mol, 0.42 A); regulates islet ECM/collagen remodeling & beta-cell regeneration (PMID:18938156, 21947380, 31207434)."),
    "NQO2":   ("T1", "Primary non-kinase intrinsic beta-cell target [FACT/OBS]: Ki 38.9 nM (85.9% occ at free Cmax); expressed in human beta cells (13.8 nCPM) & islets (45.3 nCPM); stacks over FAD in homodimer pocket (3FW1, -9.79 kcal/mol, MD-stable), modulating quinone redox cycling and oxidative stress (PMID:19531561, 39085384)."),
    "PDGFRA": ("T2", "Islet stromal/juvenile target (disfavoured as adult intrinsic beta-cell target) [FACT/OBS]: Ki 2.0-95.5 nM (73.1% occ), but epigenetically silenced in adult human beta cells (0.24 nCPM, IHC negative); beta-cell Pdgfra KO WORSENS beta-cell apoptosis & glucose intolerance (PMID:21993628, 41234234) — benefit is mediated via islet stroma/vascular remodeling (PMID:19015530)."),
    "PDGFRB": ("T2", "Islet pericyte/stromal target [FACT]: Ki 14.1-240 nM (52.0% occ); minimal adult beta-cell expression (0.72 nCPM, IHC negative), enriched in islet pericytes/vasculature; assessed structurally via 82%-identical paralog PDGFRA (6JOL)."),
    "KIT":    ("T2", "Progenitor/vascular RTK (disfavoured in adult beta cells) [FACT/OBS]: Ki 12.6-263 nM (49.7% occ); 0.00 nCPM in adult sorted human beta cells (IHC negative); Kit loss-of-function (Kit^Wv) impairs islet vasculature & beta-cell function, and anti-c-Kit mAb failed to reverse NOD T1D (PMID:19015530, 26253609)."),
    "CSF1R":  ("T2", "Islet macrophage paracrine target [FACT/OBS]: Ki 10-158 nM (62.1% occ); 0.00 nCPM in beta cells, but high on islet-resident macrophages where inhibition depletes diacritically inflammatory macrophages in diabetes (PMID:30595478, 31648183)."),
    "DDR2":   ("T2", "Islet stellate/fibroblast collagen receptor [FACT/OBS]: Kd 15.1-141 nM (64.8% occ); low in beta cells (1.21 nCPM), enriched in pancreatic stellate cells driving islet fibrosis (PMID:18938156, 22998750)."),
    "LCK":    ("T2", "Autoimmune T-cell target in T1D insulitis [FACT/OBS]: Kd/Ki 40-158 nM (62.1% occ); 0.24 nCPM in beta cells; dampens infiltrating cytotoxic T cells rather than intrinsic beta-cell signaling (PMID:16873671)."),
    "CA2":    ("T2", "Exocrine ductal enzyme (non-beta-cell) [FACT/OBS]: Ki 30.2 nM (single stopped-flow report); 0.72 nCPM in beta cells (IHC negative in islets vs medium in exocrine ducts); imatinib docked 4.69 A outside the deep Zn2+ sulfonamide pocket."),
    "SLC47A1":("T2", "Hepatic/renal MATE1 transporter [FACT/OBS]: IC50 40-50 nM (83.8% occ); 0.00 nCPM in beta cells; mediates systemic metformin/cation clearance DDI rather than intrinsic islet action."),
    "LYN":    ("T3", "Secondary sub-micromolar Src-family kinase [FACT/OBS]: IC50/Kd 200-890 nM (22.6% occ at free Cmax); expressed in beta cells (4.11 nCPM) & islets (25.5 nCPM); partial engagement at clinical dose, higher at 3-10 uM in vitro."),
    "FRK":    ("T3", "Beta-cell Src-homology kinase (Bsk/GTK) [FACT]: Kd 0.32-1.5 uM (14.7% occ at free Cmax, ~87% at 10 uM in vitro); expressed in beta cells (3.14 nCPM); promotes cytokine-induced beta-cell apoptosis (PMID:15186217, 17416457). No experimental PDB structure exists for P42685."),
    "KCNJ11": ("T3", "In-vitro micromolar KATP channel target [FACT/OBS]: patch-clamp IC50 9.4 uM (PMID:33857840); 2.7% occ at clinical free Cmax (0.26 uM) but ~52% inhibition at 10 uM in vitro; docks into Kir6.2 ATP site (6C3O, -8.91 kcal/mol, MD-stable on LYS39/LYS185/GLU179)."),
    "ERN1":   ("T3", "Indirect ER-stress effector (weak direct binding) [FACT/OBS]: direct IRE1a kinase Kd is 10-30 uM (0.9% occ at clinical Cmax), proving imatinib spares beta cells primarily upstream via ABL1/ABL2 scaffolding blockade rather than direct IRE1a ATP-pocket inhibition (PMID:28380378)."),
    "PPARG":  ("T3", "Systemic insulin-sensitizing target (absent in beta cells) [FACT/OBS]: blocks CDK5-mediated Ser273 phosphorylation at IC50 ~1-3 uM (co-crystal 6KTN, -11.68 kcal/mol, MD-stable on LYS265/GLU295/SER342, PMID:26740599, 31581474), but 0.00 nCPM in human beta cells."),
    "MAPK10": ("T3", "Micromolar JNK3 stress kinase [FACT/OBS]: Kd 1.0-3.1 uM (7.8% occ at free Cmax); highly expressed in beta cells (57.5 nCPM, islet 370 nCPM); docked pose sits 3.21 A from pocket center (2O0U) — JNK suppression in islets is mainly downstream of ABL1/IRE1a."),
    "MAPK8":  ("T3", "Micromolar JNK1 stress kinase [FACT/OBS]: Kd 2.5-5.0 uM (4.9% occ at free Cmax); beta-cell 4.83 nCPM (islet 114 nCPM); weak direct binding."),
    "MAPK14": ("T3", "Micromolar p38a kinase [FACT/OBS]: Kd 3.2-10 uM (2.5% occ at free Cmax); co-crystal 3HEC (-11.09 kcal/mol), beta-cell 4.11 nCPM (IHC medium), exposure-incompatible in vivo."),
    "FYN":    ("T3", "Micromolar Src-family kinase [FACT/OBS]: Kd 3.1-4.0 uM (6.1% occ at free Cmax); beta-cell 11.84 nCPM."),
    "ABCG2":  ("T3", "Efflux transporter (BCRP) [FACT/OBS]: IC50 0.50-3.7 uM (6.5% occ at free Cmax); cryo-EM co-crystal 6VXH (-10.58 kcal/mol, 0.68 A); 0.24 nCPM in beta cells."),
    "ABCB1":  ("T3", "Efflux transporter (P-gp) [FACT/OBS]: IC50 0.58-7.2 uM (3.5% occ at free Cmax); islet 77.8 nCPM (beta 3.62 nCPM); docks 3.63 A from taxol centroid in 6QEX."),
    "FLT3":   ("T3", "Hematopoietic RTK [FACT/OBS]: WT Kd 10 uM (2.5% occ at free Cmax; 132 nM only on leukemic ITD/mutant); 0.24 nCPM in beta cells."),
    "SYK":    ("T3", "Micromolar cis-amide kinase off-target [FACT/OBS]: Ki 1.6-5.0 uM (4.9% occ at free Cmax); co-crystal 1XBB (-8.88 kcal/mol); 0.24 nCPM in beta cells."),
    "BLK":    ("T3", "MODY11 locus kinase (absent in adult beta cells) [FACT]: Kd 525 nM (33.1% occ); 0.00 nCPM in adult sorted beta cells (0.02 nCPM islet); BLK loss-of-function causes diabetes (opposite of imatinib effect); no PDB structure."),
    "INSR":   ("T4", "Selectivity counter-screen (spared) [FACT/OBS]: Kd 5.0-10 uM (2.5% occ at free Cmax, >1000x selective vs ABL1/DDR1); docked pose displaced 4.51 A outside INSR ATP pocket (5HHW), confirming physiological beta-cell insulin receptor signaling is spared."),
    "ECHS1":  ("T4", "Falsified mitochondrial hypothesis [HYP/OBS]: proposed in PMID:34569605 (462.3 nCPM in beta cells), but unmeasured biochemically; Vina pose landed 5.11 A outside the octanoyl-CoA site (8ZRW) and drifted 4.37 A (to 6.57 A from pocket center) in 250 ps MD — direct orthosteric binding disfavoured."),
}

rows = []
for c in candidates:
    gene = c["gene"]
    pdb = c["pocket_pdb"]
    tier, assessment = TIER_MAP[gene]

    if pdb is None:
        layer = "untested"
        gate_str = "no_pdb_structure"
        vina_score = ""
        vina_inter = ""
        pose_dist = ""
        md_drift = ""
        md_ie = ""
        md_contacts = ""
    else:
        dr = dock_res[gene]
        gate_str = f"redock {dr['redock_score']:+.2f} kcal/mol / {dr['redock_recovery_A']:.2f} A ({'PASS' if dr['gate_pass'] else 'FAIL'})"
        vina_score = f"{dr['imatinib_best_score']:+.2f}"
        vina_inter = f"{dr['imatinib_inter_kcal']:+.2f}"
        pose_dist = f"{dr['imatinib_in_pocket_A']:.2f}"

        if gene in md_res:
            mr = md_res[gene]
            md_drift = f"{mr['centroid_drift_A']:.2f}"
            md_ie = f"{mr['sum_top5_IE_kJmol']:.1f}"
            top3 = list(mr["top_contacts_uniprot_kJmol"].items())[:3]
            md_contacts = "; ".join(f"{k}({v:+.1f})" for k, v in top3)
            if not dr["in_pocket_engaged"] or not mr["md_stable"]:
                layer = "computed-negative"
            elif c["pocket_type"] == "imatinib_cocrystal":
                layer = "anchor"
            else:
                layer = "computed-md"
        else:
            md_drift = ""
            md_ie = ""
            md_contacts = ""
            if not dr["in_pocket_engaged"]:
                layer = "computed-negative"
            elif c["pocket_type"] == "imatinib_cocrystal":
                layer = "anchor"
            else:
                layer = "computed-dock"

    occ_free = f"{c['occ_at_free_cmax_pct']:.1f}%" if c["occ_at_free_cmax_pct"] is not None else "unmeasured"
    med_nm = c["measured_median_nM"]
    occ_10uM = f"{(10000.0 / (10000.0 + med_nm)) * 100.0:.1f}%" if med_nm is not None else "unmeasured"

    rows.append({
        "tier": tier,
        "gene": gene,
        "target_name": c["target_name"],
        "target_class": c["target_class"],
        "uniprot": c["uniprot"],
        "chembl_id": c["chembl_id"],
        "measured_potency": c["measured_type"],
        "best_potency_nM": c["measured_potency_nM"] if c["measured_potency_nM"] is not None else "",
        "median_potency_nM": med_nm if med_nm is not None else "",
        "occ_clinical_free_cmax_260nM": occ_free,
        "occ_invitro_10uM": occ_10uM,
        "hpa_beta_cell_nCPM": f"{c['hpa_beta_cell_ncpm']:.2f}",
        "hpa_islet_endocrine_nCPM": f"{c['hpa_islet_c3_ncpm']:.2f}",
        "hpa_pancreas_nTPM": f"{c['hpa_pancreas_ntpm']:.1f}",
        "hpa_endocrine_IHC": c["hpa_endocrine_ihc"],
        "pocket_pdb": pdb or "none",
        "pocket_type": c["pocket_type"],
        "validation_gate": gate_str,
        "imatinib_vina_kcal": vina_score,
        "imatinib_inter_kcal": vina_inter,
        "pose_to_pocket_center_A": pose_dist,
        "md_drift_250ps_A": md_drift,
        "md_top5_IE_kJmol": md_ie,
        "md_top_contacts_kJmol": md_contacts,
        "layer": layer,
        "evidence_tag": c["evidence_tag"],
        "beta_cell_assessment": assessment,
    })

tier_order = {"T1": 0, "T2": 1, "T3": 2, "T4": 3}
layer_order = {"anchor": 0, "computed-md": 1, "computed-dock": 2, "computed-negative": 3, "untested": 4}
rows.sort(key=lambda r: (tier_order[r["tier"]], layer_order[r["layer"]], float(r["best_potency_nM"] or 1e9)))

fields = list(rows[0].keys())
out_csv = DELIV / "imatinib_beta_cell_tiered_targets_v1.csv"
with open(out_csv, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows -> {out_csv}")
for r in rows:
    print(f"{r['tier']} | {r['gene']:8s} | {r['layer']:17s} | beta_nCPM={r['hpa_beta_cell_nCPM']:6s} | occ_260nM={r['occ_clinical_free_cmax_260nM']:6s} | dock={r['imatinib_vina_kcal']:6s} ({r['pose_to_pocket_center_A']:4s} A) | md_drift={r['md_drift_250ps_A']:4s}")
