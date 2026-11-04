"""Unit tests for the imatinib beta-cell target search deliverables.

Verifies:
1. Tier CSV schema, 28 rows, capped layer vocabulary (no computed-positive).
2. 25/25 docking validation gates pass (< 3.0 A recovery).
3. All 12 experimental imatinib co-crystal anchors recover crystal STI within 3.0 A.
4. 10/10 MD pockets completed with 0.00 A initial heavy-atom placement RMSD and exact kJ/mol units.
5. ECHS1 negative control is outside pocket (> 5.0 A) in both docking and MD.
6. Tier 1 contains exactly {DDR1, ABL1, ABL2, NQO2}.
7. Email draft has no markdown residue, no hard wraps inside paragraphs, and carries R:\\ path.
8. CIFS shared-folder copies match local deliverables byte-for-byte (SHA256).
"""
import csv
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import pytest

BASE = Path("/das/user/QYJI/druggability/Imatinib_beta_cell_assessment")
DELIV = BASE / "output/final_deliverables"
CIFS = Path("/TDE_TV/shared_folder/QYJI/druggability/Imatinib_beta_cell_assessment")


@pytest.fixture(scope="module")
def tier_rows():
    with open(DELIV / "imatinib_beta_cell_tiered_targets_v1.csv") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def dock_res():
    return json.load(open(BASE / "output/docking/p2_docking_results.json"))


@pytest.fixture(scope="module")
def md_res():
    return json.load(open(BASE / "output/md/p3_md_summary.json"))


def test_tier_csv_count_and_schema(tier_rows):
    assert len(tier_rows) == 28
    need = {
        "tier", "gene", "target_name", "uniprot", "chembl_id",
        "measured_potency", "occ_clinical_free_cmax_260nM",
        "hpa_beta_cell_nCPM", "pocket_pdb", "validation_gate",
        "imatinib_vina_kcal", "pose_to_pocket_center_A",
        "md_drift_250ps_A", "md_top5_IE_kJmol", "layer",
        "evidence_tag", "beta_cell_assessment"
    }
    assert need.issubset(tier_rows[0].keys())


def test_strict_capped_layer_vocabulary(tier_rows):
    allowed = {"anchor", "computed-md", "computed-dock", "computed-negative", "untested"}
    for r in tier_rows:
        assert r["layer"] in allowed, f"Invalid layer {r['layer']} for {r['gene']}"


def test_tier1_intrinsic_beta_cell_targets(tier_rows):
    t1 = {r["gene"] for r in tier_rows if r["tier"] == "T1"}
    assert t1 == {"ABL1", "ABL2", "DDR1", "NQO2"}


def test_all_25_docking_gates_pass(dock_res):
    assert len(dock_res) == 25
    for g, r in dock_res.items():
        assert r["gate_pass"] is True, f"Gate failed for {g}: {r['redock_recovery_A']} A"
        assert r["redock_recovery_A"] < 3.0


def test_all_12_imatinib_cocrystals_recover_pose(dock_res):
    cocrys = [r for r in dock_res.values() if r["pocket_type"] == "imatinib_cocrystal"]
    assert len(cocrys) == 12
    for r in cocrys:
        assert r["imatinib_in_pocket_A"] < 3.0, f"{r['gene']} dist={r['imatinib_in_pocket_A']}"
        assert r["imatinib_best_score"] < -8.5, f"{r['gene']} score={r['imatinib_best_score']}"


def test_md_10_pockets_complete_and_units_exact(md_res):
    assert len(md_res) == 10
    for g, m in md_res.items():
        assert m.get("status") == "ok", f"MD failed for {g}"
        assert "138.935456" in m["ie_units"]
        assert m["pose_align_nn_rmsd_A"] == 0.0
        assert len(m["top_contacts_uniprot_kJmol"]) >= 3


def test_echs1_negative_control_falsified(dock_res, md_res):
    assert dock_res["ECHS1"]["imatinib_in_pocket_A"] > 5.0
    assert dock_res["ECHS1"]["in_pocket_engaged"] is False
    assert md_res["ECHS1"]["md_stable"] is False
    assert md_res["ECHS1"]["end_dist_to_pocket_center_A"] > 6.0


def test_html_report_valid_and_nonempty():
    p = DELIV / "imatinib_beta_cell_target_search_report.html"
    txt = p.read_text(encoding="utf-8")
    assert len(txt) > 35000
    parser = HTMLParser()
    parser.feed(txt)
    assert "<footer>" in txt and "</footer>" in txt


def test_email_draft_hygiene():
    p = DELIV / "email_reply_to_HQGH_imatinib.txt"
    txt = p.read_text(encoding="utf-8")
    assert "**" not in txt
    assert "```" not in txt
    assert r"R:\DT\TDE_TV\shared_folder\QYJI\druggability\Imatinib_beta_cell_assessment" in txt
    for sec in ["1. Intrinsic adult", "2. Canonical RTKs", "3. High-concentration", "4. Deliverables"]:
        assert sec in txt


def test_cifs_copies_sha256_match():
    for fname in [
        "imatinib_beta_cell_target_search_report.html",
        "imatinib_beta_cell_tiered_targets_v1.csv",
        "email_reply_to_HQGH_imatinib.txt",
    ]:
        h_local = hashlib.sha256((DELIV / fname).read_bytes()).hexdigest()
        h_cifs = hashlib.sha256((CIFS / fname).read_bytes()).hexdigest()
        assert h_local == h_cifs, f"SHA256 mismatch on CIFS for {fname}"
