"""RORα BBB prediction — standalone script for bbb-predict conda env.
Uses b3clf directly (bypasses bbbkit.__init__ which needs dotenv).
"""
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from b3clf import b3clf

# ── Compounds ──
RORA_COMPOUNDS = {
    "SR3335": "O=S(C1=CC=CS1)(NC2=CC=C(C(C(F)(F)F)(C(F)(F)F)O)C=C2)=O",
    "SR1001": "CC(NC1=NC(C)=C(S(=O)(NC2=CC=C(C(C(F)(F)F)(O)C(F)(F)F)C=C2)=O)S1)=O",
    "SR1078": "O=C(NC1=CC=C(C(C(F)(F)F)(C(F)(F)F)O)C=C1)C2=CC=C(C(F)(F)F)C=C2",
}

ALL_CLASSIFIERS = [
    ("xgb", "classic_ADASYN"),
    ("xgb", "classic_SMOTE"),
    ("xgb", "common"),
    ("logreg", "classic_ADASYN"),
    ("logreg", "classic_SMOTE"),
    ("logreg", "common"),
    ("dtree", "classic_ADASYN"),
    ("dtree", "classic_SMOTE"),
    ("dtree", "common"),
    ("knn", "classic_ADASYN"),
    ("knn", "classic_SMOTE"),
    ("knn", "common"),
]


# ── CNS-MPO ──
def _t0_decrease(v, lo, hi):
    if v <= lo: return 1.0
    if v >= hi: return 0.0
    return 1.0 - (v - lo) / (hi - lo)

def _t0_tpsa(v):
    if 40 <= v <= 90: return 1.0
    if v < 40: return max(0.0, v / 40.0)
    return max(0.0, 1.0 - (v - 90) / 30.0)

def cns_mpo(clogp, clogd, mw, tpsa, hbd, pka):
    return round(
        _t0_decrease(clogp, 3, 5) + _t0_decrease(clogd, 2, 4) +
        _t0_decrease(mw, 360, 500) + _t0_tpsa(tpsa) +
        _t0_decrease(hbd, 0.5, 3.5) + _t0_decrease(pka, 8, 10), 2)


def main():
    print("=" * 80)
    print("RORα Tool Compounds — BBB Permeability Prediction (bbb-predict env)")
    print("B3clf (12 models) + CNS-MPO Scoring")
    print("=" * 80)

    # ── Physichem ──
    print("\n── Physicochemical Properties & CNS-MPO ──\n")
    print(f"{'Compound':<10} {'MW':>6} {'TPSA':>6} {'cLogP':>6} {'HBD':>4} {'HBA':>4} {'RotB':>5} {'CNS_MPO':>8}")
    print("-" * 60)

    props_all = {}
    for name, smi in RORA_COMPOUNDS.items():
        mol = Chem.MolFromSmiles(smi)
        mw = Descriptors.MolWt(mol)
        tpsa = Descriptors.TPSA(mol)
        clogp = Descriptors.MolLogP(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        rotb = rdMolDescriptors.CalcNumRotatableBonds(mol)
        clogd = clogp - 0.5 if hbd > 0 else clogp
        n_basic = smi.count("N") - smi.count("n") - smi.count("[NH]")
        pka_est = 8.5 if n_basic > 0 else 6.0
        mpo = cns_mpo(clogp, clogd, mw, tpsa, hbd, pka_est)
        props_all[name] = {"MW": round(mw,1), "TPSA": round(tpsa,1),
                           "cLogP": round(clogp,2), "HBD": hbd, "HBA": hba,
                           "RotBonds": rotb, "CNS_MPO": mpo}
        print(f"{name:<10} {mw:>6.1f} {tpsa:>6.1f} {clogp:>6.2f} {hbd:>4d} {hba:>4d} {rotb:>5d} {mpo:>8.2f}")

    # ── B3clf ──
    print("\n── Running B3clf 12-model ensemble ──")
    all_results = []
    for name, smi in RORA_COMPOUNDS.items():
        print(f"\n▶ {name}...", end=" ", flush=True)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".smi", delete=False, dir="/tmp")
        tmp.write(f"{smi}\t{name}\n")
        tmp.close()

        for clf_type, sampling in ALL_CLASSIFIERS:
            try:
                out_file = f"/tmp/b3clf_{name}_{clf_type}_{sampling}.xlsx"
                result_df = b3clf(
                    mol_in=tmp.name, clf=clf_type, sampling=sampling,
                    output=out_file, verbose=0)
                prob = result_df["B3clf_predicted_probability"].iloc[0]
                label = result_df["B3clf_predicted_label"].iloc[0]
                if os.path.exists(out_file):
                    os.remove(out_file)
                all_results.append({
                    "Compound": name, "Model": f"{clf_type}_{sampling}",
                    "P(BBB+)": round(float(prob), 4),
                    "Label": "BBB+" if label == 1 else "BBB-",
                    "MW": props_all[name]["MW"], "TPSA": props_all[name]["TPSA"],
                    "cLogP": props_all[name]["cLogP"], "HBD": props_all[name]["HBD"],
                    "CNS_MPO": props_all[name]["CNS_MPO"],
                })
            except Exception as e:
                all_results.append({
                    "Compound": name, "Model": f"{clf_type}_{sampling}",
                    "P(BBB+)": None, "Label": f"ERROR: {e}",
                    "MW": props_all[name]["MW"], "TPSA": props_all[name]["TPSA"],
                    "cLogP": props_all[name]["cLogP"], "HBD": props_all[name]["HBD"],
                    "CNS_MPO": props_all[name]["CNS_MPO"],
                })
        os.unlink(tmp.name)
        print("done")

    results_df = pd.DataFrame(all_results)

    # ── Consensus ──
    print("\n" + "=" * 80)
    print("CONSENSUS RESULTS (12-model vote)")
    print("=" * 80)
    consensus_rows = []
    for name in RORA_COMPOUNDS:
        grp = results_df[results_df["Compound"] == name]
        valid = grp[grp["P(BBB+)"].notna()]
        if valid.empty:
            continue
        avg_p = valid["P(BBB+)"].mean()
        n_pos = (valid["Label"] == "BBB+").sum()
        n_tot = len(valid)
        consensus = "BBB+" if n_pos > n_tot / 2 else "BBB-"
        consensus_rows.append({
            "Compound": name, "Avg_P(BBB+)": round(avg_p, 4),
            "Votes_BBB+": f"{n_pos}/{n_tot}", "Consensus": consensus,
            "MW": props_all[name]["MW"], "TPSA": props_all[name]["TPSA"],
            "cLogP": props_all[name]["cLogP"], "CNS_MPO": props_all[name]["CNS_MPO"],
        })

    cons_df = pd.DataFrame(consensus_rows)
    print(cons_df.to_string(index=False))

    # ── Save ──
    out_dir = "/home/QYJI/das/druggability/results"
    results_df.to_csv(f"{out_dir}/rora_bbb_predictions.csv", index=False)
    cons_df.to_csv(f"{out_dir}/rora_bbb_consensus.csv", index=False)
    print(f"\n✅ Results saved to results/rora_bbb_predictions.csv and results/rora_bbb_consensus.csv")

    # ── Interpretation ──
    print("\n── Interpretation ──")
    for _, row in cons_df.iterrows():
        name = row["Compound"]
        prob = row["Avg_P(BBB+)"]
        mpo = row["CNS_MPO"]
        consensus = row["Consensus"]
        if consensus == "BBB+" and mpo >= 4.0:
            interp = "Likely CNS-penetrant (high confidence)"
        elif consensus == "BBB+" and mpo >= 3.0:
            interp = "Likely CNS-penetrant (moderate confidence)"
        elif consensus == "BBB+":
            interp = "Possibly CNS-penetrant (low CNS-MPO, use caution)"
        elif consensus == "BBB-" and mpo < 3.0:
            interp = "Likely peripheral-restricted"
        else:
            interp = "Borderline — consider in vivo PK/PD confirmation"
        print(f"  {name}: {consensus} (P={prob:.3f}, CNS-MPO={mpo:.2f}) → {interp}")


if __name__ == "__main__":
    main()
