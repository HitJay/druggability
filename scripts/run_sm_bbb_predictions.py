"""Phase 1.3/1.4: Full SM BBB prediction with B3clf (all 12 models) + CNS-MPO"""
import os
import sys
import tempfile
import warnings

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from b3clf import b3clf

# ── Validated compound SMILES ──
COMPOUNDS = {
    "Bivamelagon": "CC(C)C(=O)N([C@H]1C[C@@H](C(=O)N2CCOCC2)N(C(=O)[C@@H]2CCN(C(C)(C)C)[C@H]2c2ccc(Cl)cc2)C1)[C@H]1CC[C@@H](C)CC1",
    "Lorcaserin": "O=C1NC2=CC(Cl)=CC=C2CCC1",
    "Naltrexone": "C1CC1CN2CCC34C5C(=O)CCC3(OC6=C4C(=CC=C6C2C5)O)O",
    "Bupropion": "CC(NC(C)(C)C)C(=O)C1=CC(Cl)=CC=C1",
    "Topiramate": "CC1(C)OC2COC3(COS(N)(=O)=O)OC(C)(C)OC3C2O1",
    "Phentermine": "CC(N)(C)CC1=CC=CC=C1",
    "Orlistat": "CCCCCCCCCCCCC(CC1OC(=O)C1CCCCCC)OC(=O)C(CC(C)C)NC=O",
    "MK-0493": "C[C@@H](Nc1nc(Nc2ccc(C(F)(F)F)cc2)nc(n1)N3CCN(C)[C@@H](C(N)=O)C3)c4ccc(Cl)cc4Cl",
    "Celastrol": "C[C@@H]1C(=O)C=C2[C@@]3(C)CC[C@@]4(C)C(CC=C5[C@@]4(C)CC[C@H](C)[C@H]5C(=O)O)=C3CC=C2[C@@]1(C)O",
    "Diazoxide": "CC1=NS(=O)(=O)C2=CC(Cl)=CC=C2N1",
    "GSK-598809": "FC1=CC(CN2CCC(C3=NC4=C(N3)C=CC(=C4)OC(F)(F)F)CC2)=CC=C1",
}

# Known BBB status for validation
KNOWN_BBB = {
    "Bivamelagon": "BBB+",   # oral MC4R agonist, CNS-active
    "Lorcaserin": "BBB+",    # CNS drug (5-HT2C)
    "Naltrexone": "BBB+",    # opioid antagonist, CNS
    "Bupropion": "BBB+",     # NDRI, CNS
    "Topiramate": "BBB+",    # anticonvulsant, CNS
    "Phentermine": "BBB+",   # sympathomimetic, CNS
    "Orlistat": "BBB-",      # lipase inhibitor, peripheral only
    "MK-0493": "BBB+",       # oral MC4R agonist, CNS
    "Celastrol": "BBB+",     # leptin sensitizer, CNS evidence
    "Diazoxide": "BBB-",     # KATP opener, primarily peripheral
    "GSK-598809": "BBB+",    # DRD3 antagonist, PET-confirmed CNS
}


# ── CNS-MPO functions ──
def _t0_decrease(v, lo, hi):
    if v <= lo:
        return 1.0
    if v >= hi:
        return 0.0
    return 1.0 - (v - lo) / (hi - lo)


def _t0_tpsa(v):
    if 40 <= v <= 90:
        return 1.0
    if v < 40:
        return max(0.0, v / 40.0)
    return max(0.0, 1.0 - (v - 90) / 30.0)


def cns_mpo(clogp, clogd, mw, tpsa, hbd, pka):
    return round(
        _t0_decrease(clogp, 3, 5)
        + _t0_decrease(clogd, 2, 4)
        + _t0_decrease(mw, 360, 500)
        + _t0_tpsa(tpsa)
        + _t0_decrease(hbd, 0.5, 3.5)
        + _t0_decrease(pka, 8, 10),
        2,
    )


def main():
    # ── Compute physichem + CNS-MPO for all compounds ──
    print("=" * 80)
    print("PHASE 1.3/1.4: Small Molecule BBB Prediction (B3clf 12 models + CNS-MPO)")
    print("=" * 80)

    props_data = []
    for name, smi in COMPOUNDS.items():
        mol = Chem.MolFromSmiles(smi)
        mw = Descriptors.MolWt(mol)
        tpsa = Descriptors.TPSA(mol)
        clogp = Descriptors.MolLogP(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        # Estimate LogD and pKa
        clogd = clogp - 0.5 if hbd > 0 else clogp
        n_basic = smi.count("N") - smi.count("n") - smi.count("[NH]")
        pka_est = 8.5 if n_basic > 0 else 6.0
        mpo = cns_mpo(clogp, clogd, mw, tpsa, hbd, pka_est)
        props_data.append(
            {
                "Compound": name,
                "MW": round(mw, 1),
                "TPSA": round(tpsa, 1),
                "cLogP": round(clogp, 2),
                "HBD": hbd,
                "HBA": hba,
                "CNS_MPO": mpo,
                "Known_BBB": KNOWN_BBB[name],
            }
        )

    props_df = pd.DataFrame(props_data)
    print("\n── Physicochemical Properties & CNS-MPO ──")
    print(props_df.to_string(index=False))

    # ── B3clf 12-model predictions ──
    CLASSIFIERS = [
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

    all_results = []
    for name, smi in COMPOUNDS.items():
        print(f"\n▶ Running B3clf for {name}...", end=" ", flush=True)
        # Write temp SMI file
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".smi", delete=False, dir="/tmp"
        )
        tmp.write(f"{smi}\t{name}\n")
        tmp.close()

        for clf_type, sampling in CLASSIFIERS:
            try:
                out_file = f"/tmp/b3clf_{name}_{clf_type}_{sampling}.xlsx"
                result_df = b3clf(
                    mol_in=tmp.name,
                    clf=clf_type,
                    sampling=sampling,
                    output=out_file,
                    verbose=0,
                )
                prob = result_df["B3clf_predicted_probability"].iloc[0]
                label = result_df["B3clf_predicted_label"].iloc[0]
                if os.path.exists(out_file):
                    os.remove(out_file)
                all_results.append(
                    {
                        "Compound": name,
                        "Model": f"{clf_type}_{sampling}",
                        "P_BBBplus": round(prob, 4),
                        "Predicted": "BBB+" if label == 1 else "BBB-",
                    }
                )
            except Exception as e:
                all_results.append(
                    {
                        "Compound": name,
                        "Model": f"{clf_type}_{sampling}",
                        "P_BBBplus": None,
                        "Predicted": "ERROR",
                    }
                )
        os.unlink(tmp.name)
        print("done")

    results_df = pd.DataFrame(all_results)

    # ── Consensus ──
    print("\n" + "=" * 80)
    print("CONSENSUS RESULTS (12-model vote)")
    print("=" * 80)
    consensus_rows = []
    for name in COMPOUNDS:
        grp = results_df[results_df["Compound"] == name]
        valid = grp[grp["P_BBBplus"].notna()]
        if valid.empty:
            continue
        avg_p = valid["P_BBBplus"].mean()
        n_pos = (valid["Predicted"] == "BBB+").sum()
        n_tot = len(valid)
        consensus = "BBB+" if n_pos > n_tot / 2 else "BBB-"
        known = KNOWN_BBB[name]
        correct = "✅" if consensus == known else "❌"
        consensus_rows.append(
            {
                "Compound": name,
                "Avg_P(BBB+)": round(avg_p, 4),
                "Votes": f"{n_pos}/{n_tot}",
                "Consensus": consensus,
                "Known": known,
                "Match": correct,
            }
        )

    consensus_df = pd.DataFrame(consensus_rows)
    print(consensus_df.to_string(index=False))

    # ── Accuracy ──
    n_correct = sum(1 for r in consensus_rows if r["Match"] == "✅")
    n_total = len(consensus_rows)
    print(
        f"\n📊 Overall Accuracy: {n_correct}/{n_total} ({100*n_correct/n_total:.1f}%)"
    )

    # ── Best model (xgb_classic_ADASYN) results ──
    print("\n── XGBoost classic_ADASYN (recommended default) ──")
    xgb_best = results_df[results_df["Model"] == "xgb_classic_ADASYN"].copy()
    xgb_best = xgb_best.merge(
        pd.DataFrame(
            {
                "Compound": list(KNOWN_BBB.keys()),
                "Known": list(KNOWN_BBB.values()),
            }
        )
    )
    xgb_best["Match"] = xgb_best.apply(
        lambda r: "✅" if r["Predicted"] == r["Known"] else "❌", axis=1
    )
    print(
        xgb_best[["Compound", "P_BBBplus", "Predicted", "Known", "Match"]].to_string(
            index=False
        )
    )
    n_correct_xgb = (xgb_best["Predicted"] == xgb_best["Known"]).sum()
    print(
        f"\nXGB Accuracy: {n_correct_xgb}/{len(xgb_best)} ({100*n_correct_xgb/len(xgb_best):.1f}%)"
    )

    # ── Save full results ──
    os.makedirs("results", exist_ok=True)
    full_df = results_df.merge(
        props_df[["Compound", "MW", "TPSA", "cLogP", "HBD", "CNS_MPO", "Known_BBB"]]
    )
    full_df.to_csv("results/sm_bbb_predictions.csv", index=False)
    consensus_df_out = pd.DataFrame(consensus_rows)
    consensus_df_out = consensus_df_out.merge(props_df[["Compound", "MW", "CNS_MPO"]])
    consensus_df_out.to_csv("results/sm_bbb_consensus.csv", index=False)
    print(
        "\n✅ Results saved to results/sm_bbb_predictions.csv and results/sm_bbb_consensus.csv"
    )


if __name__ == "__main__":
    main()
