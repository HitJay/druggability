"""F1 (fixed): pocket map via PDBe mappings API — UniProt accession -> PDB entries."""
import json
import subprocess

BASE = "/das/user/QYJI/druggability/TSPO_assessment"
UA = "Mozilla/5.0 emapunil-f1b/1.0"

TARGETS = {
    "TSPO_h":   "P30536",
    "CAR":      "Q14994",
    "PXR":      "O75469",
    "GABRA1":   "P47869",
    "HDAC6":    "Q9UBN7",
    "TRHR":     "P34981",
    "NPSR":     "Q6W5P4",
    "MEN1":     "O00255",
    "TDP1":     "Q9NUW8",
    "ALDH1A1":  "P00352",
    "PMP22":    "Q01453",
    "HSD11B1":  "P28845",
    "SIGMAR1":  "Q99720",
    "ALOX15":   "P16050",
    "GRM2":     "Q14416",
    "CNR1":     "P21554",
    "OPRK1":    "P41145",
    "TMEM97":   "Q5BJF2",
    "OPRM1":    "P35372",
    "GRM5":     "P41574",
    "HRH3":     "Q9Y5N1",
}

map_out = {}
for name, acc in TARGETS.items():
    r = subprocess.run(["curl", "-sS", "--max-time", "60", "-A", UA,
                        f"https://www.ebi.ac.uk/pdbe/api/mappings/{acc}"],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        d = {}
    pdbs = []
    block = d.get(acc, {})
    for src, mappings in block.items():
        for pdb_id in mappings:
            if pdb_id not in pdbs:
                pdbs.append(pdb_id)
    pdbs.sort()
    map_out[name] = {"uniprot": acc, "pdb_entries": pdbs, "n": len(pdbs)}
    print(f"{name:9s} {acc}: n={len(pdbs)} | {pdbs[:12]}")

json.dump(map_out, open(f"{BASE}/data/emapunil_f1_pdb_map.json", "w"), indent=1)
print("\nsaved emapunil_f1_pdb_map.json")
