"""Unit tests for the ws6 novel-pocket round deliverables (run BEFORE sending
the CSV/report to the user — same discipline as test_emapunil_dataset.py).
"""
import csv, json
from pathlib import Path

import pytest

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")


@pytest.fixture(scope="module")
def tier_rows():
    with open(BASE / "output/novel_pockets_tiered_targets_v1.csv") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def hittier():
    return json.load(open(BASE / "output/docking/novelq_p5c_hittier.json"))


@pytest.fixture(scope="module")
def v2():
    return json.load(open(BASE / "data/novelq_p4c_novel_v2.json"))


def test_tier_csv_exists_and_nonempty(tier_rows):
    assert len(tier_rows) >= 30


def test_tier_csv_schema(tier_rows):
    need = {"pocket_tag", "target", "gene", "structure", "pocket_id", "fpocket_ds",
            "volume_A3", "novelty_basis", "emapunil_scan_best", "scan_verdict",
            "hittier_3seeds", "hittier_confirmed", "layer", "assessment"}
    for r in tier_rows:
        missing = need - set(r)
        assert not missing, f"row {r.get('pocket_tag')} missing {missing}"


CAP = {"computed-md", "computed-dock", "computed-negative", "error"}


def test_layer_vocabulary_capped(tier_rows):
    for r in tier_rows:
        assert r["layer"] in CAP, f"{r['pocket_tag']}: layer '{r['layer']}' outside capped vocabulary"


def test_no_computed_positive_label(tier_rows):
    for r in tier_rows:
        assert "computed-positive" not in r["layer"], "vocabulary leak"


def test_every_novel_v2_pocket_appears(tier_rows, v2):
    tags = {r["pocket_tag"] for r in tier_rows}
    for r in v2["novel_v2"]:
        tag = f"{r['pdb']}_p{r['pocket_id']}"
        assert tag in tags, f"novel_v2 pocket {tag} missing from tier CSV"


def test_novel_pockets_are_disjoint_from_known(tier_rows, v2):
    """every tier row must trace to a pocket whose residues do not recover the
    co-crystal (literature-reported) pocket in its own structure"""
    raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))
    known = {}
    for pdb, d in raw.items():
        kr = set()
        for p in d.get("pockets", []):
            if p["recovers_known"]:
                kr |= {tuple(x) for x in p["residues"]}
        known[pdb] = kr
    v2tags = {f"{r['pdb']}_p{r['pocket_id']}" for r in v2["novel_v2"]}
    for r in tier_rows:
        if r["pocket_tag"] not in v2tags:
            continue
        pdb, pid = r["structure"], int(r["pocket_id"])
        p = [x for x in raw[pdb]["pockets"] if x["pocket_id"] == pid][0]
        assert not p["recovers_known"], f"{r['pocket_tag']} recovers the known pocket!"
        pres = {tuple(x) for x in p["residues"]}
        assert len(pres & known[pdb]) / max(1, len(pres)) < 0.30


def test_hittier_confirmed_requires_3seeds_and_gate(hittier):
    for tag, h in hittier.items():
        assert len(h["seed_scores"]) == 3, f"{tag}: hit tier must have 3 seeds"
        if h["confirmed"]:
            assert min(s[0] for s in h["seed_scores"]) <= -7.0
            assert h["pose1_offset_A"] <= 6.0


def test_controls_qc_pass():
    ctrl = json.load(open(BASE / "output/docking/novelq_p5_controls.json"))
    redocks = [c for c in ctrl if c["tag"].startswith("redock_")]
    assert len(redocks) == 3
    for c in redocks:
        assert c["qc"] == "PASS", f"{c['tag']} redock QC {c['qc']} (offset {c['offset_A']} A)"


def test_md_rows_have_drift_and_contacts(tier_rows):
    md_rows = [r for r in tier_rows if r["layer"] == "computed-md"]
    assert md_rows, "no computed-md rows at all — MD step did not contribute"
    for r in md_rows:
        assert r["md_drift_A"] != "" and float(r["md_drift_A"]) <= 4.0
        assert r["md_sumIE_kJmol"] != ""


def test_literature_inventory_present():
    lit = json.load(open(BASE / "data/novelq_p3_literature_pockets.json"))
    assert len(lit) >= 15
    for gene, e in lit.items():
        assert "hits" in e


def test_fpocket_recovered_known_pockets_everywhere():
    raw = json.load(open(BASE / "data/novelq_p2_fpocket_pockets.json"))
    for pdb, d in raw.items():
        if "error" in d:
            continue
        assert any(p["recovers_known"] for p in d["pockets"]), \
            f"{pdb}: fpocket did NOT recover the known pocket — screening unreliable for this structure"
