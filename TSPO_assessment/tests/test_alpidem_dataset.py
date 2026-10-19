"""Unit test for the alpidem ligand-target-search dataset (tests/data, not network)."""
import csv
import json
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")


def test_curation_records_present():
    d = json.load(open(BASE / "data/alpidem_ws0_curation.json"))
    props = d["pubchem"]["alpidem"]["PropertyTable"]["Properties"][0]
    assert props["CID"] == 54897
    assert props["InChIKey"] == "JRTIDHTUMYMPRU-UHFFFAOYSA-N"
    assert props["MolecularFormula"] == "C21H23Cl2N3O"
    # ChEMBL resolved by InChIKey/SMILES/synonym (name search alone fails)
    d2 = json.load(open(BASE / "data/alpidem_ws0b_chembl_resolve.json"))
    assert d2["alpidem_inchembl"][0]["chembl_id"] == "CHEMBL54349"
    assert any("SL 80.0342" in s for s in d2["alpidem_inchembl"][0]["synonyms"])


def test_pubchem_activity_surface():
    d = json.load(open(BASE / "data/alpidem_pubchem_actives_summary.json"))
    assert d["n_total"] == 966
    assert len(d["active"]) == 117
    aids = {a["aid"] for a in d["active"]}
    # anchor assays: TSPO binding, CBR binding, PK, BSEP
    for aid in ["40374", "42319", "1209455", "1209457", "1443992"]:
        assert aid in aids


def test_gene_map_covers_backbone():
    m = json.load(open(BASE / "data/alpidem_gene_symbols.json"))
    syms = {v["symbol"] for v in m.values() if v["symbol"]}
    assert {"TSPO", "Tspo", "Gabra1", "ABCB11", "NR1I2", "ALB"} <= syms
    assert m["24230"]["symbol"] == "Tspo" and m["24230"]["org"] == "Rattus norvegicus"
    assert m["706"]["symbol"] == "TSPO" and m["706"]["org"] == "Homo sapiens"


def test_similarity_closure_boundary():
    d = json.load(open(BASE / "data/alpidem_ws2_analogue_target_tally.json"))
    assert d["n_analogues"] == 11
    # the analogue neighbourhood must contain TSPO + GABA-A and nothing else strong
    prefs = {v["pref"] for v in d["tally"].values() if v["n"] >= 3}
    assert any("Translocator" in p for p in prefs)
    assert any("GABA-A" in p for p in prefs)
    assert not any(("Sigma" in p) or ("LXR" in p) or ("NR1I3" in p) for p in prefs)


def test_zolpidem_comparator_separation():
    z = json.load(open(BASE / "data/alpidem_zolpidem_target_tally.json"))
    tspo = z["CHEMBL4552"]  # Translocator protein
    assert tspo["best"] is None or tspo["best"] >= 4000  # zolpidem weak at TSPO (nM)
    gab = z["CHEMBL2094121"]  # alpha1/beta3/gamma2
    assert gab["best"] <= 30  # zolpidem potent at BZD site


def test_docking_gate():
    d = json.load(open(BASE / "output/docking/alpidem_ws4_docking.json"))
    # positive control: TSPO pocket must be strong for alpidem
    assert d["4RYI_alpidem"]["scores"][0] <= -7.5
    # PXR measured off-target recovered
    assert d["2QNV_alpidem"]["scores"][0] <= -7.0
    g = json.load(open(BASE / "output/docking/alpidem_ws4b_gabaa_matrix.json"))
    # alpidem and zolpidem both present at the diazepam pocket
    assert g["results"]["alpidem"][0] <= -6.5
    assert g["results"]["zolpidem"][0] <= -6.5
    dz = json.load(open(BASE / "output/docking/alpidem_ws4c_diazepam_control.json"))
    assert dz["diazepam"][0] <= -7.0  # own co-crystal pocket control


def test_tiered_csv_shape_and_tiers():
    rows = list(csv.DictReader(open(BASE / "output/alpidem_tiered_targets_v1.csv")))
    assert len(rows) == 12
    tiers = {r["target"]: r["tier"] for r in rows}
    # T1 rows must be exposure-compatible and FACT-graded
    for r in rows:
        if r["tier"].startswith("T1"):
            assert r["evidence_grade"] in ("FACT", "OBS")
    assert "High" in tiers.get("TSPO (PBR) — rat P16257 / human P30536", "") \
        or any("TSPO" in r["target"] and r["tier"] == "T1" for r in rows)
    names = {r["target"] for r in rows}
    assert any("PXR" in n for n in names)
    assert any("BSEP" in n for n in names)
    assert any("α1-acid glycoprotein" in n for n in names)
    assert any("Albumin" in n for n in names)
