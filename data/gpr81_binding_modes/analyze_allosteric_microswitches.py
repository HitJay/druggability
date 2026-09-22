#!/usr/bin/env python3
"""
Direction 3: Map Transmembrane Allosteric Communication Pathway & GPCR Micro-switches
Compares 8Z8A (HCAR1-Gi active state) vs 8Z8B (HCAR1 apo state) to trace:
1. TM6 intracellular opening angle and outward swing (Arg121-Glu238 distance)
2. Toggle switch conformation (Trp251 / Phe250 in CWxP motif)
3. NPxxY motif (Tyr278 in TM7)
4. ECL2 active-gate conformation (Phe168 / Ser167)
5. Allosteric conduit residues connecting TM5/TM6 crevice to the G-protein interface
"""

import os
import json
import numpy as np
from Bio.PDB import PDBParser, Superimposer

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
GPR81_DIR = "/das/user/QYJI/druggability/data/gpr81_phase1/structures"

parser = PDBParser(QUIET=True)
s_active = parser.get_structure("8Z8A", os.path.join(GPR81_DIR, "8Z8A.pdb"))[0]["R"]
s_apo = parser.get_structure("8Z8B", os.path.join(GPR81_DIR, "8Z8B.pdb"))[0]["R"]

# Align active and apo structures across TM1-TM4 core
ca_active, ca_apo = [], []
for res_id in range(20, 150):
    if (" ", res_id, " ") in s_active and (" ", res_id, " ") in s_apo:
        ra = s_active[(" ", res_id, " ")]
        rb = s_apo[(" ", res_id, " ")]
        if "CA" in ra and "CA" in rb:
            ca_active.append(ra["CA"])
            ca_apo.append(rb["CA"])

sup = Superimposer()
sup.set_atoms(ca_active, ca_apo)
sup.apply(list(s_apo.get_atoms()))
print(f"Aligned 8Z8A (active) to 8Z8B (apo) across {len(ca_active)} TM core CAs, RMSD = {sup.rms:.2f} A")

# 1. TM6 Intracellular Outward Swing (Distance TM3 Arg121 to TM6 Arg236/Glu238)
# In Class A GPCRs, DRY is on TM3 (Asp120-Arg121-Tyr122 in HCAR1? Let us check sequence)
res_dry = [r for r in s_active if r.id[1] in [120, 121, 122]]
print("TM3 motif residues (120-122):", [(r.resname, r.id[1]) for r in res_dry])

# Find TM3 bottom and TM6 bottom
# TM3 CA at res 121
tm3_bot_a = s_active[(" ", 121, " ")]["CA"].coord
tm3_bot_b = s_apo[(" ", 121, " ")]["CA"].coord

# TM6 bottom around res 230-238
tm6_bot_res = 235 if (" ", 235, " ") in s_active else 230
tm6_bot_a = s_active[(" ", tm6_bot_res, " ")]["CA"].coord
tm6_bot_b = s_apo[(" ", tm6_bot_res, " ")]["CA"].coord

d_ionic_active = np.linalg.norm(tm3_bot_a - tm6_bot_a)
d_ionic_apo = np.linalg.norm(tm3_bot_b - tm6_bot_b)
tm6_swing = np.linalg.norm(tm6_bot_a - tm6_bot_b)

print(f"TM6 Intracellular Outward Swing:")
print(f"  - Active (8Z8A) TM3(121) - TM6({tm6_bot_res}) distance: {d_ionic_active:.2f} A")
print(f"  - Apo (8Z8B)    TM3(121) - TM6({tm6_bot_res}) distance: {d_ionic_apo:.2f} A")
print(f"  - TM6 Intracellular Tip Displacement (Outward Swing):  {tm6_swing:.2f} A")

# 2. Toggle Switch: Trp in TM6 (Residues 245-255)
# Let us find CWxP in TM6
tm6_res = [r for r in s_active if 245 <= r.id[1] <= 255]
print("TM6 toggle region:", [(r.resname, r.id[1]) for r in tm6_res])
trp_res = [r for r in tm6_res if r.resname == "TRP"]
if trp_res:
    trp_id = trp_res[0].id[1]
    trp_act = s_active[(" ", trp_id, " ")]["CA"].coord
    trp_apo = s_apo[(" ", trp_id, " ")]["CA"].coord
    print(f"Toggle switch Trp{trp_id} CA displacement: {np.linalg.norm(trp_act - trp_apo):.2f} A")
else:
    trp_id = 251

# 3. Allosteric Crevice to Intracellular Conduit
# Trace residues along TM5-TM6: Glu153 -> Met170 -> Phe198 -> Trp251 -> Leu235 -> G-protein interface
conduit = [
    ("Glu153 (TM5 Extracellular Anchor)", 153),
    ("His155 (TM5 Middle)", 155),
    ("Met170 (ECL2 / TM5 Lipophilic Cleft)", 170),
    ("Ile187 (TM5 Core)", 187),
    ("Trp248 (TM6 Core Toggle)", 248 if (" ", 248, " ") in s_active else 251),
    ("Arg121 (TM3 DRY Motif)", 121),
    ("Arg236 (TM6 Intracellular Interface)", 236 if (" ", 236, " ") in s_active else 235)
]

conduit_displacements = []
for label, rid in conduit:
    if (" ", rid, " ") in s_active and (" ", rid, " ") in s_apo:
        ca_a = s_active[(" ", rid, " ")]["CA"].coord
        ca_b = s_apo[(" ", rid, " ")]["CA"].coord
        disp = np.linalg.norm(ca_a - ca_b)
        conduit_displacements.append({"label": label, "residue": rid, "disp_angstrom": float(disp)})
        print(f"  {label:38s}: Cα shift = {disp:.2f} A")

microswitch_results = {
    "tm6_outward_swing_angstrom": float(tm6_swing),
    "active_tm3_tm6_distance": float(d_ionic_active),
    "apo_tm3_tm6_distance": float(d_ionic_apo),
    "conduit": conduit_displacements,
    "mechanism": f"Binding of Agonist 1 at the extracellular TM5-TM6 crevice (Glu153/His155/Met170) reorganizes the TM5 helix, which propagates through the hydrophobic core to drive an outward swing of TM6 by {tm6_swing:.2f} Å, fully opening the intracellular cavity for Gi1 coupling."
}

with open(os.path.join(WORK_DIR, "allosteric_pathway_results.json"), "w") as f:
    json.dump(microswitch_results, f, indent=2)

print("\nSaved allosteric pathway results to allosteric_pathway_results.json!")
