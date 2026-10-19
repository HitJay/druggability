"""Unit tests for the emapunil emapunil dataset deliverables.

Covers: tier CSV schema + strict tier logic (anchor only TSPO; computed-md only the
4 MD-stable candidates; no computed-positive inflation), F4 summary consistency with
per-pdb JSONs, and the 4RYI corrected in-pocket distance record.
"""
import csv, json, math
import pytest
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")


@pytest.fixture(scope="module")
def tier_rows():
    with open(BASE / "output/emapunil_tiered_targets_v1.csv") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def f2():
    return json.load(open(BASE / "output/docking/emapunil_f2_docking.json"))


@pytest.fixture(scope="module")
def f4():
    return json.load(open(BASE / "output/docking/emapunil_f4_summary.json"))


def test_tier_csv_exists_and_nonempty(tier_rows):
    assert len(tier_rows) == 23


def test_tier_csv_schema(tier_rows):
    need = {"target", "gene", "pk11195_evidence", "pocket_pdb", "gate",
            "emapunil_dock", "pose_in_pocket_A", "md_sumIE_kJmol",
            "assessment", "layer"}
    assert need.issubset(tier_rows[0].keys())


def test_exactly_one_anchor_and_it_is_tspo(tier_rows):
    anchors = [r for r in tier_rows if r["layer"] == "anchor"]
    assert len(anchors) == 1
    assert anchors[0]["gene"] == "TSPO"


def test_computed_md_is_exactly_the_four_md_stable_pockets(tier_rows):
    md = {r["gene"] for r in tier_rows if r["layer"] == "computed-md"}
    assert md == {"NR1I3", "GABRA1/2,GABRB2,GABRG2", "OPRM1"}


def test_no_computed_positive_layer_exists(tier_rows):
    # tier vocabulary is strictly capped: computation never asserts binding
    bad = [r for r in tier_rows if r["layer"] in ("computed-positive", "tier1", "tier2")]
    assert bad == []


def test_computed_negative_rows_all_have_poor_geometry_or_repulsion(tier_rows):
    for r in tier_rows:
        if r["layer"] in ("computed-negative", "computed-neg"):
            d = r["pose_in_pocket_A"]
            s = r["emapunil_dock"]
            assert (d and float(d) > 3.0) or (s and float(s) > 0), r["gene"]


def test_untested_rows_have_no_dock_score(tier_rows):
    for r in tier_rows:
        if r["layer"] == "untested":
            assert r["emapunil_dock"] == "" and r["pocket_pdb"] == "none"


def test_tspo_anchor_corrected_distance_recorded(f2):
    # the multi-copy-centroid bug is documented in the JSON
    assert "emapunil_in_pocket_A_corrected" in f2["4RYI"]
    assert abs(f2["4RYI"]["emapunil_in_pocket_A_corrected"] - 1.09) < 0.05


def test_f4_summary_covers_five_pockets(f4):
    assert set(f4.keys()) == {"4RYI", "6X3X", "4DKL", "1XVP", "4XAQ"}


def test_negative_control_stayed_out_of_pocket_in_md(f2):
    # GRM2 4XAQ: docked +3.54 (repelled); MD confirms ligand outside pocket
    assert f2["4XAQ"]["emapunil_score"] > 0
    assert f2["4XAQ"]["emapunil_in_pocket_A"] > 10.0


def test_anchor_pose_matches_crystal_pka(f2):
    # anchor quality gate: emapunil pose within 2 A of the crystal PKA ligand
    assert f2["4RYI"]["emapunil_in_pocket_A_corrected"] < 2.0
