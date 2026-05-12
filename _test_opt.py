"""Temporary: test Open Targets API connectivity"""
import requests

# Test tractability with only valid fields
r = requests.post(
    "https://api.platform.opentargets.org/api/v4/graphql",
    json={
        "query": """query {
  target(ensemblId: "ENSG00000146648") {
    id approvedSymbol approvedName biotype
    tractability { label modality }
  }
}"""
    },
    timeout=30,
)
print(f"Status: {r.status_code}")
print(r.text[:2000])