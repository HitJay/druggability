"""Aggregate FEP-A scanning TI results into a summary table + JSON.

Collects output/fep_a/scan_<pdb>_<ligand>.json for both ligands, emits:
  output/fep_a/fep_a_summary.json
  output/fep_a/fep_a_summary.csv
"""
import csv
import glob
import json

OUT = "/das/user/QYJI/druggability/TSPO_assessment/output/fep_a"

POCKET_LABEL = {
    "4RYI": "TSPO anchor (bacterial TSPO + PK11195)",
    "6X3X": "GABA-A benzodiazepine site",
    "4DKL": "OPRM1 orthosteric",
    "1XVP": "CAR ligand-binding domain",
    "5TGZ": "CNR1 orthosteric",
    "4DJH": "OPRK1 orthosteric",
    "4XAQ": "GRM2 negative-control pocket",
}

rows = []
for f in sorted(glob.glob(f"{OUT}/scan_*.json")):
    j = json.load(open(f))
    for anchor, d in j["anchors"].items():
        rows.append({
            "ligand": j["ligand"],
            "pdb": j["pdb"],
            "pocket": POCKET_LABEL[j["pdb"]],
            "anchor_residue": anchor,
            "ddG_kJmol": d["ddG_kJmol"],
            "ddG_kcalmol": d["ddG_kcalmol"],
            "native_IE_kJmol_t0": d["native_IE_kJmol_t0"],
        })

rows.sort(key=lambda r: (r["ligand"], -r["ddG_kJmol"]))
summary = {
    "method": ("computational alanine scanning: side-chain charge/epsilon annihilation "
               "vs ligand, thermodynamic integration over 8 lambda windows (2.5 ps eq + "
               "25 ps sampling each), amber14/protein.ff14SB + SMIRNOFF (openff-2.1.0, "
               "NAGL am1bcc, net charge 0), protein heavy atoms restrained 5 kcal/mol/A^2, "
               "ligand heavy atoms restrained 1 kcal/mol/A^2 to the relaxed pose, "
               "vacuum (no solvent), 300 K"),
    "sign_convention": ("positive ddG = annihilating the ligand-anchor side-chain "
                        "interaction costs binding free energy = the ligand USES this "
                        "residue; ~0 = no net contribution"),
    "caveats": [
        "short sampling (27.5 ps per window): ddG values are directional estimates, "
        "not converged free energies; treat as ranking evidence only",
        "vacuum protocol (no solvent/entropy): absolute values are not binding dG",
        "4XAQ is a negative-control pocket (docked pose is a surface site, not the "
        "orthosteric pocket): its nonzero ddG reflects that the ligand genuinely "
        "interacts with the surface site it was docked to, and confirms the protocol "
        "detects real interactions; it must NOT be read as specific binding",
        "1XVP/fgin required CUDA double precision (mixed precision diverged)",
        "6X3X required pre-minimisation (t0 clashes, +1.2e5 kJ/mol)",
    ],
    "rows": rows,
}
json.dump(summary, open(f"{OUT}/fep_a_summary.json", "w"), indent=1)

with open(f"{OUT}/fep_a_summary.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"{len(rows)} anchors aggregated")
for r in rows:
    print(f"{r['ligand']:9s} {r['pdb']:5s} {r['anchor_residue']:9s} "
          f"ddG={r['ddG_kJmol']:7.2f} kJ/mol ({r['ddG_kcalmol']:5.2f} kcal/mol)")
