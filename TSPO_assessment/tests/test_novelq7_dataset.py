"""ws7 unit tests: dataset invariants for the novel-pocket FGIN round (p1-p5).

Run with the repo venv pytest. Catches: vocabulary leaks, stale counts, unit labels,
zero-anchor TI artifacts, demoted-adjacent handling.
"""
import csv, glob, json, math

BASE = "/das/user/QYJI/druggability/TSPO_assessment"

ALLOWED_LAYERS = {"anchor", "computed-md", "computed-dock", "computed-negative",
                  "computed-ti", "skipped", "untested"}


def _rows():
    return list(csv.DictReader(open(f"{BASE}/output/novelq7_tiered_targets_v1.csv")))


def test_scan_file_complete():
    rows = [json.loads(l) for l in open(f"{BASE}/output/docking/novelq7_p1_fgin_scan.jsonl")]
    assert len(rows) == 29
    assert not any("error" in r for r in rows)


def test_hittier_gate():
    hit = json.load(open(f"{BASE}/output/docking/novelq7_p2_fgin_hittier.json"))
    for tag, h in hit.items():
        if h["confirmed"]:
            assert h["best_of_seeds"] <= -7.0 and h["pose1_offset_A"] <= 6.0, tag


def test_md_coverage_matches_confirmed():
    hit = json.load(open(f"{BASE}/output/docking/novelq7_p2_fgin_hittier.json"))
    confirmed = {t for t, h in hit.items() if h["confirmed"]}
    done = set()
    for f in glob.glob(f"{BASE}/output/docking/novelq7_p3_*.json"):
        j = json.load(open(f))
        if "error" not in j:
            done.add(j["tag"])
    assert confirmed <= done, confirmed - done


def test_md_verdict_vocabulary():
    for f in glob.glob(f"{BASE}/output/docking/novelq7_p3_*.json"):
        j = json.load(open(f))
        if "error" in j:
            continue
        assert j["verdict"] in ("md-stable", "md-unstable"), j["tag"]
        if j["verdict"] == "md-stable":
            assert j["md_drift_A"] <= 4.0, j["tag"]
        assert "kJ/mol" in j.get("ie_units", ""), j["tag"]


def test_ti_no_zero_anchors():
    """The transient mixed-precision zero-artifact must not survive in outputs."""
    for f in glob.glob(f"{BASE}/output/fep_a7/scan7_*.json"):
        j = json.load(open(f))
        for a, v in j.get("anchors", {}).items():
            ws = [w["minus_dUdlam_kJmol"] for w in v["windows"]]
            assert not all(abs(x) < 1e-6 for x in ws), f"{j['tag']}/{j['ligand']}/{a}"
            assert not math.isnan(v["ddG_kJmol"]), f"{j['tag']}/{j['ligand']}/{a}"


def test_ti_sign_semantics():
    """native IE at t0 must be nonzero for any anchor with meaningful ddG."""
    for f in glob.glob(f"{BASE}/output/fep_a7/scan7_*.json"):
        j = json.load(open(f))
        for a, v in j.get("anchors", {}).items():
            if abs(v["ddG_kJmol"]) > 2.0:
                assert abs(v["native_IE_kJmol_t0"]) > 1.0, f"{j['tag']}/{j['ligand']}/{a}"


def test_csv_layer_vocabulary():
    for r in _rows():
        base_layer = r["fgin_layer"].split("+")[0]
        assert base_layer in ALLOWED_LAYERS, r["pocket_tag"]
        base_layer_e = r["emapunil_layer"].split("+")[0]
        assert base_layer_e in ALLOWED_LAYERS, r["pocket_tag"]


def test_csv_no_computed_positive():
    blob = open(f"{BASE}/output/novelq7_tiered_targets_v1.csv").read().lower()
    assert "computed-positive" not in blob


def test_demoted_adjacent_keeps_data():
    for r in _rows():
        if "demoted-adjacent" in r["fgin_layer"]:
            assert r["fgin_hittier_best3"] != "", r["pocket_tag"]


def test_row_count_matches_pocket_universe():
    rows = _rows()
    assert len(rows) == 35  # 29 novel_v2 + 6 adjacent/demoted from all_rows


def test_headline_numbers_stable():
    rows = {r["pocket_tag"]: r for r in _rows()}
    # TSPO dimer-interface pocket: both ligands confirm + TI supports
    r = rows["4RYI_p26"]
    assert float(r["fgin_hittier_best3"]) <= -9.0
    assert r["fgin_md_verdict"] == "md-stable"
    assert float(r["fgin_ti_top_ddG_kJmol"]) > 5.0
    # the two FGIN md-unstable rejections survived into the CSV
    for t in ("6HUG_p114", "7F61_p15", "7M93_p8"):
        assert rows[t]["fgin_md_verdict"] == "md-unstable", t
