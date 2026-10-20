import csv

for name in ["emapunil_tiered_targets_v1.csv", "fgin_tiered_targets_v1.csv"]:
    rows = list(csv.DictReader(open(f"output/{name}")))
    layers = set(r["layer"] for r in rows)
    anchors = [r for r in rows if r["layer"] == "anchor"]
    assert len(rows) == 23, name
    assert len(anchors) == 1 and anchors[0]["gene"] == "TSPO", name
    assert not (layers & {"computed-positive", "tier1", "tier2"}), name
    print(f"{name}: 23 rows OK | layers = {sorted(layers)}")

for f in ["email_reply_to_ZHCO_emapunil.txt", "email_reply_to_ZHCO_fgin.txt"]:
    txt = open(f"output/{f}").read()
    assert "**" not in txt and "```" not in txt and "`" not in txt, f
    assert "R:\\DT\\TDE_TV" in txt, f
    print(f"{f}: no markdown residue, R: path present OK")
print("ALL CONTENT CHECKS PASS")
