"""Unit tests for the FGIN-1-27 dataset deliverables (mirrors emapunil test logic)."""
import csv, json
import pytest
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")


@pytest.fixture(scope="module")
def tier_rows():
    with open(BASE / "output/fgin_tiered_targets_v1.csv") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def f2():
    return json.load(open(BASE / "output/docking/fgin_f2_docking.json"))


@pytest.fixture(scope="module")
def f4():
    return json.load(open(BASE / "output/docking/fgin_f4_summary.json"))


def test_tier_csv_exists_and_nonempty(tier_rows):
    assert len(tier_rows) == 23


def test_tier_csv_schema(tier_rows):
    need = {"target", "gene", "pk11195_evidence", "pocket_pdb", "gate",
            "fgin_dock", "pose_in_pocket_A", "md_sumIE_kJmol",
            "assessment", "layer"}
    assert need.issubset(tier_rows[0].keys())


def test_exactly_one_anchor_and_it_is_tspo(tier_rows):
    anchors = [r for r in tier_rows if r["layer"] == "anchor"]
    assert len(anchors) == 1
    assert anchors[0]["gene"] == "TSPO"


def test_computed_md_set(tier_rows):
    md = {r["gene"] for r in tier_rows if r["layer"] == "computed-md"}
    assert md == {"NR1I3", "CNR1"}


def test_no_computed_positive_layer_exists(tier_rows):
    bad = [r for r in tier_rows if r["layer"] in ("computed-positive", "tier1", "tier2")]
    assert bad == []


def test_negative_rows_have_poor_geometry_repulsion_or_drift(tier_rows):
    for r in tier_rows:
        if r["layer"] in ("computed-negative", "computed-neg"):
            d = r["pose_in_pocket_A"]
            s = r["fgin_dock"]
            assert (d and float(d) > 3.0) or (s and float(s) > 0) or "drift" in r["assessment"], r["gene"]


def test_untested_rows_have_no_dock_score(tier_rows):
    for r in tier_rows:
        if r["layer"] == "untested":
            assert r["fgin_dock"] == "" and r["pocket_pdb"] == "none"


def test_anchor_pose_quality(f2):
    # FGIN dock pose within 1.5 A of the crystal PKA ligand
    assert f2["4RYI"]["fgin_in_pocket_A_pka"] < 1.5


def test_negative_control_repelled(f2):
    assert f2["4XAQ"]["fgin_score"] > 0


def test_oprk1_marked_unstable(f4):
    assert f4["4DJH"]["md_stable"] is False


def test_f4_summary_covers_five_pockets(f4):
    assert {"4RYI", "1XVP", "5TGZ", "4DJH", "4XAQ"}.issubset(f4.keys())
