"""FGIN f0: curation — identity + measured-layer summary for FGIN-1-27.

FGIN-1-27 (CID 132496, InChIKey VUWXAQFLTSBUDB-UHFFFAOYSA-N):
N,N-dihexyl-2-[2-(4-fluorophenyl)-1H-indol-3-yl]acetamide.
Classic high-affinity TSPO agonist ligand (the FGIN indole-acetamide family);
known secondary pharmacology in the literature: central benzodiazepine receptor
interaction reported at high concentrations (Romeo et al. 1992 Eur J Pharmacol;
other FGIN analogues cross-react with the BZD site).
"""
import json

BASE = "/das/user/QYJI/druggability/TSPO_assessment"

FGIN = {
    "name": "FGIN-1-27",
    "cid": 132496,
    "inchikey": "VUWXAQFLTSBUDB-UHFFFAOYSA-N",
    "smiles": "CCCCCCN(CCCCCC)C(=O)CC1=C(NC2=CC=CC=C21)C3=CC=C(C=C3)F",
    "formula": "C28H37FN2O",
    "iupac": "2-[2-(2-(4-fluorophenyl)-1H-indol-3-yl)acetyl]-N,N-dihexylamine".replace(
        "2-[2", "N,N-dihexyl-2-[2"),  # readable label
    "note": ("indole-3-acetamide TSPO agonist; dihexyl amide = high lipophilicity; "
             "literature secondary pharmacology: BZD-site cross-reactivity at high "
             "concentrations (to verify against measured layer)"),
}
json.dump(FGIN, open(f"{BASE}/data/fgin_f0_identity.json", "w"), indent=1)
print(json.dumps(FGIN, indent=1))
