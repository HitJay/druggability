#!/usr/bin/env python3
"""
Direction 4: Full 45-Compound Series Landscape
Classify all 45 compounds into:
1. Pure Orthosteric (Arg71 anchor)
2. Pure Allosteric / Ago-PAM (TM5-TM6 crevice)
3. Bitopic / Dualsteric (Dual pocket engagement)
"""

import os
import json
import pandas as pd

WORK_DIR = "/das/user/QYJI/druggability/data/gpr81_binding_modes"
SRC_CSV = "/das/user/QYJI/druggability/data/gpr81_phase1/followup_2026-08/data/gpr81_pocket_analysis_pairs.csv"

df = pd.read_csv(SRC_CSV)
df_8z8a = df[df["receptor"] == "8Z8A"].copy()

landscape = []
for _, row in df_8z8a.iterrows():
    cid = row["entry_id"]
    name = row["name"]
    series = row["series"]
    region = row["region"]
    ec50 = row["ec50_nM"]
    score = row["best_score_kcal_mol"]
    dist = row["pose_centroid_to_cocrystal_A"]
    pol = str(row["polar_contacts"])
    
    contacts_arg71 = "ARG71" in pol
    contacts_glu153 = "GLU153" in pol or "HIS177" in pol or "MET170" in pol

    # Classify
    if series in ["endogenous", "reference_acid"] or cid in ["lac", "t03", "t04", "t05"]:
        mode_class = "Pure Orthosteric"
        mech_role = "Endogenous metabolite / reference weak acid"
    elif series == "amide":
        mode_class = "Bitopic (Dualsteric Candidate)"
        mech_role = "Amide scaffold reaches both Arg71 core & TM5-TM6 crevice"
    elif contacts_arg71 and contacts_glu153:
        mode_class = "Bitopic (Dualsteric Candidate)"
        mech_role = "Dual contact with Arg71 and Glu153/His177"
    elif region == "TM56_EXTRACELLULAR" or contacts_glu153:
        mode_class = "Allosteric (TM5-TM6 Crevice / ago-PAM)"
        mech_role = "Vestibular crevice binder; aligns with HCAR2 9n site"
    else:
        mode_class = "Orthosteric Pocket"
        mech_role = "Deep core engagement"

    landscape.append({
        "entry_id": cid,
        "name": name,
        "series": series,
        "ec50_nM": float(ec50) if pd.notnull(ec50) else None,
        "docking_score": float(score),
        "distance_to_lactate_A": float(dist),
        "region": region,
        "contacts_arg71": contacts_arg71,
        "contacts_glu153": contacts_glu153,
        "mode_class": mode_class,
        "mechanistic_role": mech_role
    })

df_out = pd.DataFrame(landscape)
csv_out = os.path.join(WORK_DIR, "gpr81_45_compound_landscape.csv")
json_out = os.path.join(WORK_DIR, "gpr81_45_compound_landscape.json")

df_out.to_csv(csv_out, index=False)
with open(json_out, "w") as f:
    json.dump(landscape, f, indent=2)

print(f"Classified {len(landscape)} entries across GPR81 landscape:")
print(df_out["mode_class"].value_counts())
