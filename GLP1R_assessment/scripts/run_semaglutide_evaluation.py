#!/usr/bin/env python3
"""
GLP1R_assessment/scripts/run_semaglutide_evaluation.py

Full multi-tier druggability and structural pharmacology assessment of Semaglutide on GLP-1R (PDB: 6X18).
"""

import json
from pathlib import Path
from druggability.peptide.affinity import predict_peptide_affinity
from druggability.peptide.scan import run_alanine_scanning, scan_position_mutations
from druggability.peptide.chem_mod import audit_peptide_lipidation, get_ncaa_info

base_dir = Path("/das/user/QYJI/druggability")
complex_path = base_dir / "GLP1R_assessment/structures/GLP1R_Semaglutide_complex.pdb"
native_path = base_dir / "GLP1R_assessment/structures/GLP1R_Native_complex.pdb"
out_dir = base_dir / "output/2026-09-18/semaglutide_full_case"
out_dir.mkdir(parents=True, exist_ok=True)

print("=== Step 1: Layer 1 Contact Affinity (Semaglutide vs GLP-1R) ===")
aff_sema = predict_peptide_affinity(complex_path, receptor_chain="R", peptide_chain="P")
print(f"Semaglutide ΔG : {aff_sema.delta_g:.2f} kcal/mol | Kd : {aff_sema.kd_text}")
print(f"Total Contacts : {aff_sema.total_contacts} | Breakdown: {aff_sema.contact_breakdown}")

print("\n=== Step 2: Layer 1 Contact Affinity (Native GLP-1 vs GLP-1R) ===")
aff_nat = predict_peptide_affinity(native_path, receptor_chain="R", peptide_chain="P")
print(f"Native GLP-1 ΔG: {aff_nat.delta_g:.2f} kcal/mol | Kd : {aff_nat.kd_text}")
print(f"Total Contacts : {aff_nat.total_contacts} | Breakdown: {aff_nat.contact_breakdown}")

print("\n=== Step 3: Layer 2 Alanine Scanning across Sequence ===")
ala_res = run_alanine_scanning(complex_path, receptor_chain="R", peptide_chain="P")
sorted_entries = sorted(ala_res.entries, key=lambda x: x.ddg, reverse=True)
print(f"Top 8 Residues by ΔΔG on GLP-1R:")
for h in sorted_entries[:8]:
    print(f"  - Pos {h.res_seq:2d} {h.orig_res}: ΔΔG = +{h.ddg:.2f} kcal/mol ({h.lost_contacts} contacts lost, Role: {h.classification})")

print("\n=== Step 4: Position 34 (Lys -> Arg) Substitution Scan ===")
scan34 = scan_position_mutations(complex_path, res_seq=34, receptor_chain="R", peptide_chain="P")
arg34 = next((m for m in scan34.candidates if m.mutant_res == "ARG"), None)
if arg34:
    print(f"Lys34 -> Arg34 ΔΔG: {arg34.ddg:+.2f} kcal/mol (Compatibility: {arg34.compatibility})")
    print(f"Note: {arg34.note}")

print("\n=== Step 5: 3D Cone Steric Audit for Lipidation (Lys26 vs Others) ===")
cone26 = audit_peptide_lipidation(complex_path, res_seq=26, protraction_type="C18_diacid_gammaGlu", receptor_chain="R", peptide_chain="P")
print(f"Pos 26 (Lys26): {cone26.clearance_status} | Clash Atoms: {cone26.receptor_atoms_in_cone} | d_min: {cone26.min_receptor_distance:.2f} Å | Advice: {cone26.engineering_advice}")

cone34 = audit_peptide_lipidation(complex_path, res_seq=34, protraction_type="C18_diacid_gammaGlu", receptor_chain="R", peptide_chain="P")
print(f"Pos 34 (Arg34): {cone34.clearance_status} | Clash Atoms: {cone34.receptor_atoms_in_cone} | d_min: {cone34.min_receptor_distance:.2f} Å")

cone7 = audit_peptide_lipidation(complex_path, res_seq=7, protraction_type="C18_diacid_gammaGlu", receptor_chain="R", peptide_chain="P")
print(f"Pos 7  (His7) : {cone7.clearance_status} | Clash Atoms: {cone7.receptor_atoms_in_cone} | d_min: {cone7.min_receptor_distance:.2f} Å")

cone12 = audit_peptide_lipidation(complex_path, res_seq=12, protraction_type="C18_diacid_gammaGlu", receptor_chain="R", peptide_chain="P")
print(f"Pos 12 (Phe12): {cone12.clearance_status} | Clash Atoms: {cone12.receptor_atoms_in_cone} | d_min: {cone12.min_receptor_distance:.2f} Å")

print("\n=== Step 6: Non-Canonical Aib8 Enzymatic Profile ===")
aib_info = get_ncaa_info("AIB")
if aib_info:
    print(f"Residue: {aib_info.full_name} ({aib_info.res_name})")
    print(f"Biological Role: {aib_info.biological_role}")
    print(f"DPP-4 Resistance Profile: {aib_info.dpp4_resistance} (Canonical: {aib_info.canonical_analog})")

# Save aggregated results
summary_data = {
    "target": "GLP-1R (PDB: 6X18)",
    "candidate": "Semaglutide",
    "native_reference": "Native GLP-1(7-37) (PDB: 5VAI)",
    "affinity_semaglutide": aff_sema.to_dict(),
    "affinity_native": aff_nat.to_dict(),
    "alanine_scan": ala_res.to_dict(),
    "position_34_scan": scan34.to_dict(),
    "lipidation_cone_pos26": cone26.to_dict(),
    "lipidation_cone_pos34": cone34.to_dict(),
    "lipidation_cone_pos7": cone7.to_dict(),
    "lipidation_cone_pos12": cone12.to_dict(),
    "aib8_profile": aib_info.to_dict() if aib_info else None
}

with open(out_dir / "semaglutide_assessment_data.json", "w") as f:
    json.dump(summary_data, f, indent=2)

print(f"\nAll results saved to: {out_dir / 'semaglutide_assessment_data.json'}")
