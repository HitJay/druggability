#!/usr/bin/env python3
"""
scripts/register_jira_oxtr.py

Create and register the OXTR Individual Target ticket on Jira (RIC board),
configure required fields, assign to QYJI, and transition to In Progress.
"""

import os
import json
import time
import subprocess

TOKEN = open(os.path.expanduser("~/.config/jira/token")).read().strip()
BASE_URL = "https://jira.novonordisk.com/rest/api/2"

def jira_post(endpoint, payload):
    r = subprocess.run([
        "curl", "-sS", "-X", "POST",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        f"{BASE_URL}/{endpoint}"
    ], capture_output=True, text=True, check=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return r.stdout

def jira_put(endpoint, payload):
    r = subprocess.run([
        "curl", "-sS", "-X", "PUT",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        f"{BASE_URL}/{endpoint}"
    ], capture_output=True, text=True, check=True)
    return r.stdout

def jira_get(endpoint):
    r = subprocess.run([
        "curl", "-sS",
        "-H", f"Authorization: Bearer {TOKEN}",
        f"{BASE_URL}/{endpoint}"
    ], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)

def main():
    print("Step 1: Creating RIC issue for OXTR...")
    description = """h2. Background

OXTR (Oxytocin Receptor, UniProt P30559) is a Class A Gq-coupled neuroendocrine GPCR. Native oxytocin (OXT) suppresses appetite and promotes metabolic benefits, but is hampered by a short circulatory half-life (<30 min) and cross-activation of vasopressin receptors (AVPR1A/V1a, AVPR1B/V1b, AVPR2/V2) causing acute vasoconstriction/hypertension and kaliuresis.

Requested by Mingyue Wu (MUEW): assess OXTR druggability, structural mechanisms of Lilly's long-acting selective analog (acylated-OXT_Gly), benchmark computational tools on subtype selectivity, and formulate wet-lab validation recommendations.

h2. Scope & Structures

* Active Cryo-EM OXTR structure: PDB 7QVM (3.25 A, bound to OXT 9-mer + Go/q chimera; Pluckthun 2022) & 7RYC (2.90 A, bound to OXT + Gq; Zhou 2022).
* Inactive X-ray OXTR structure: PDB 6TPK (3.20 A, bound to small-molecule antagonist Retosiban).
* Counter-screen subtype comparison: PDB 7DW9 (2.80 A, active vasopressin V2R bound to AVP + Gs).
* Peptide analogs evaluated: OXT (CYIQNCPLG-NH2), OXT_Gly (CYIQNCGLG-NH2), AVP (CYFQNCPRG-NH2).

h2. Methods

* Structural superposition and TM1-TM4 core alignment.
* Vina grid box segmentation (Full Orthosteric, Core Sub-pocket, Vestibule Exit) and redocking QC benchmark on Retosiban (6TPK).
* Residue microenvironment analysis (ECL3 Lys306 vs Leu302, Helix I inward shift).
* OpenMM MM/GBSA (Amber14SB + GBn2 with SD+L-BFGS minimization) binding free energy profiling.
* Boltz-2 / AlphaFold-Multimer 12-complex input matrix generation.
* Interactive 3D visualization platform (3Dmol.js) and high-DPI summary diagram.

h2. Key Findings

* Acylation Exit Vector confirmed: Leu8 projects 100% into extracellular solvent, validating Lilly's Lys8 fatty-acid acylation (Lys-(AEEA)2-(gE)2-C18) for half-life extension without perturbing 7TM binding.
* Modality Selection: Small molecules occupy only the lower cavity (Retosiban 6TPK); peptide agonists remain the primary modality to induce the essential TM7 kink (Leu316 H-bond with Tyr2).
* Computational Selectivity Audit: Boltz-2/AlphaFold predict high interface confidence (iptm > 0.82) indiscriminately across all GPCR-peptide pairs due to 7TM homology; rigid MM/GBSA suffers static lattice void artifacts on Pro7Gly point mutation.
* Physical Selectivity Driver: V2R exhibits a 3.51 A inward shift of Helix I that constricts the vestibule, combined with an ECL3 hydrophobic/electrostatic mismatch (OXTR Lys306 vs V2R Leu302), explaining why flexible Gly7 is excluded from V2R.

h2. Deliverables & Data Locations

Working directory: /das/user/QYJI/druggability/OXTR_assessment (local compute)
Windows shared drive paths:
{noformat}
R:\DT\TDE_TV\shared_folder\QYJI\druggability\OXTR_assessment\
  reports/
    OXTR_druggability_and_structure_report.html   (interactive 3D viewer)
    OXTR_druggability_summary.png                 (high-DPI summary diagram)
    redocking_benchmark.json                      (Retosiban QC: 0.54 A centroid recovery)
    selectivity_computational_benchmark.json      (energy & metric breakdown)
  structures/                                     (standardized PDBs)
  grids/                                          (Vina grid box parameters)
  boltz_inputs/                                   (12 Boltz-2 complex YAMLs)
{noformat}

h2. Related

* Sibling individual target assessment tickets on RIC board: RIC-396 (GPR81 / HCAR1), RIC-392 / RIC-393 (GHSR).
"""

    create_payload = {
        "fields": {
            "project": {"key": "RIC"},
            "issuetype": {"name": "Task"},
            "summary": "OXTR individual target assessment — structural pharmacology, druggability & selectivity benchmarking",
            "description": description,
            "components": [{"name": "Individual Target"}],
            "customfield_12903": {"name": "MUEW"}  # Requester: Mingyue Wu
        }
    }

    res_create = jira_post("issue", create_payload)
    key = res_create.get("key")
    if not key:
        print("Create failed:", res_create)
        return
    print(f"Created issue: {key}")

    # Step 2: PUT custom fields
    print("Step 2: Updating workflow fields via PUT...")
    update_payload = {
        "fields": {
            "customfield_14819": "2026-10-31",                  # Expected Delivery
            "customfield_20611": [{"value": "AI/ML"}],          # Skill
            "customfield_20612": {"value": "Supporting path"},   # Criticality
            "customfield_20300": {"value": "1-3 days"}          # Estimated Effort
        }
    }
    jira_put(f"issue/{key}", update_payload)

    # Step 3: Assign to QYJI
    print("Step 3: Assigning to QYJI...")
    jira_put(f"issue/{key}/assignee", {"name": "QYJI"})

    # Step 4: Walk transitions To Do -> Analysis (11) -> In Progress (21)
    print("Step 4: Transitioning issue to Analysis (11)...")
    jira_post(f"issue/{key}/transitions", {"transition": {"id": "11"}})
    time.sleep(1)

    # Check available transitions for next hop
    trans_info = jira_get(f"issue/{key}/transitions")
    ip_trans = next((t for t in trans_info.get("transitions", []) if t["to"]["name"] == "In Progress"), None)
    if ip_trans:
        print(f"Transitioning issue to In Progress ({ip_trans['id']})...")
        jira_post(f"issue/{key}/transitions", {"transition": {"id": ip_trans["id"]}})
    else:
        print("In Progress transition not found in list:", [t["to"]["name"] for t in trans_info.get("transitions", [])])
    time.sleep(1)

    # Step 5: Ensure Assignee is retained
    jira_put(f"issue/{key}/assignee", {"name": "QYJI"})

    # Step 6: Post initial milestone comment
    comment_body = """h3. Initial Delivery — Structural Pharmacology, Druggability & Selectivity Audit

* Analysis complete for human OXTR active (7QVM / 7RYC) vs inactive (6TPK) structures, and subtype comparison with vasopressin V2R (7DW9).
* Pro7Gly selectivity mechanism resolved: V2R 3.51 A Helix I constriction + ECL3 Leu302 hydrophobic mismatch shuts off V2R binding.
* Leu8 confirmed as solvent-exposed exit vector for fatty-acid acylation (Lys8).
* Full deliverables generated: self-contained 3D HTML interactive report, high-DPI summary diagram, Vina docking grid definitions, and 12 Boltz-2 YAML configurations.

Deliverables path on shared drive:
{noformat}
R:\DT\TDE_TV\shared_folder\QYJI\druggability\OXTR_assessment\reports\OXTR_druggability_and_structure_report.html
R:\DT\TDE_TV\shared_folder\QYJI\druggability\OXTR_assessment\reports\OXTR_druggability_summary.png
{noformat}
"""
    jira_post(f"issue/{key}/comment", {"body": comment_body})
    print("Posted initial milestone comment.")

    # Step 7: Verification
    final_issue = jira_get(f"issue/{key}?fields=summary,status,assignee,components,customfield_12903")
    print("\n=== Verified Jira Issue Details ===")
    print(f"Key:         {key}")
    print(f"Summary:     {final_issue['fields']['summary']}")
    print(f"Status:      {final_issue['fields']['status']['name']}")
    print(f"Assignee:    {final_issue['fields']['assignee']['displayName']}")
    print(f"Requester:   {final_issue['fields']['customfield_12903']['displayName']}")
    print(f"Component:   {final_issue['fields']['components'][0]['name']}")
    print(f"URL:         https://jira.novonordisk.com/browse/{key}")

if __name__ == "__main__":
    main()
