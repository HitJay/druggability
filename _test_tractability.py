"""Verify tractability fix"""
import sys
sys.path.insert(0, "d:\\vscode\\druggability\\src")
from litkit.druggability.tractability import query_tractability

r = query_tractability("EGFR", query_type="gene_symbol")
print(f"OK: {r.symbol}, {r.ensembl_id}")
d = r.to_dict()
print(f"small_molecule: {d['small_molecule']}")
print(f"antibody: {d['antibody']}")
print(f"protac: {d['protac']}")