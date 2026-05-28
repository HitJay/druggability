"""Phase 1.3/1.4: Optimized SM BBB prediction — compute PaDEL descriptors ONCE per compound."""
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

# B3clf internal imports
from b3clf.geometry_opt import geometry_optimize
from b3clf.descriptor_padel import compute_descriptors
from b3clf.utils import get_descriptors, select_descriptors, scale_descriptors, predict_permeability

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

KNOWN_BBB = {
    "Bivamelagon": "BBB+",
    "Lorcaserin": "BBB+",
    "Naltrexone": "BBB+",
    "Bupropion": "BBB+",
    "Topiramate": "BBB+",
    "Phentermine": "BBB+",
    "Orlistat": "BBB-",
    "MK-0493": "BBB+",
    "Celastrol": "BBB+",
    "Diazoxide": "BBB-",
    "GSK-598809": "BBB+",
}

CLASSIFIERS = [
    ("xgb", "classic_ADASYN"), ("xgb", "classic_SMOTE"), ("xgb", "common"),
    ("logreg", "classic_ADASYN"), ("logreg", "classic_SMOTE"), ("logreg", "common"),
    ("dtree", "classic_ADASYN"), ("dtree", "classic_SMOTE"), ("dtree", "common"),
    ("knn", "classic_ADASYN"), ("knn", "classic_SMOTE"), ("knn", "common"),
]


# ── CNS-MPO ──
def _t0_dec(v, lo, hi):
    if v <= lo: return 1.0
    if v >= hi: return 0.0
    return 1.0 - (v - lo) / (hi - lo)

def _t0_tpsa(v):
    if 40 <= v <= 90: return 1.0
    if v < 40: return max(0.0, v / 40.0)
    return max(0.0, 1.0 - (v - 90) / 30.0)

def cns_mpo(clogp, clogd, mw, tpsa, hbd, pka):
    return round(_t0_dec(clogp, 3, 5) + _t0_dec(clogd, 2, 4) + _t0_dec(mw, 360, 500)
                 + _t0_tpsa(tpsa) + _t0_dec(hbd, 0.5, 3.5) + _t0_dec(pka, 8, 10), 2)


def main():
    print("=" * 80, flush=True)
    print("PHASE 1.3/1.4: SM BBB Prediction (B3clf 12 models + CNS-MPO) [OPTIMIZED]", flush=True)
    print("=" * 80, flush=True)

    # ── Step 1: Physichem + CNS-MPO ──
    props_data = []
    for name, smi in COMPOUNDS.items():
        mol = Chem.MolFromSmiles(smi)
        mw = Descriptors.MolWt(mol)
        tpsa = Descriptors.TPSA(mol)
        clogp = Descriptors.MolLogP(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        clogd = clogp - 0.5 if hbd > 0 else clogp
        n_basic = smi.count("N") - smi.count("n") - smi.count("[NH]")
        pka_est = 8.5 if n_basic > 0 else 6.0
        mpo = cns_mpo(clogp, clogd, mw, tpsa, hbd, pka_est)
        props_data.append({
            "Compound": name, "MW": round(mw, 1), "TPSA": round(tpsa, 1),
            "cLogP": round(clogp, 2), "HBD": hbd, "HBA": hba,
            "CNS_MPO": mpo, "Known_BBB": KNOWN_BBB[name]
        })
    props_df = pd.DataFrame(props_data)
    print("\n── Physicochemical Properties & CNS-MPO ──", flush=True)
    print(props_df.to_string(index=False), flush=True)

    # ── Step 2: Compute descriptors per compound (1 PaDEL call each) ──
    print("\n── Computing PaDEL descriptors per compound... ──", flush=True)
    workdir = tempfile.mkdtemp(prefix="b3clf_batch_", dir="/tmp")

    all_results = []
    failed_compounds = []

    for name, smi in COMPOUNDS.items():
        print(f"  ▶ {name}...", end=" ", flush=True)
        # Write single-compound SMI file
        smi_file = os.path.join(workdir, f"{name}.smi")
        with open(smi_file, "w") as f:
            f.write(f"{smi}\t{name}\n")

        sdf_file = os.path.join(workdir, f"{name}_3d.sdf")
        features_file = os.path.join(workdir, f"{name}_padel.xlsx")

        try:
            # Geometry optimization (with fallback for difficult molecules)
            try:
                geometry_optimize(input_fname=smi_file, output_sdf=sdf_file, sep="\t")
            except ValueError:
                # Fallback: use random coords for molecules that fail standard embedding
                from rdkit.Chem import AllChem, rdmolfiles
                mol = Chem.MolFromSmiles(smi)
                mol = Chem.AddHs(mol)
                AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
                if mol.GetNumConformers() == 0:
                    params = AllChem.ETKDGv3()
                    params.useRandomCoords = True
                    AllChem.EmbedMolecule(mol, params)
                AllChem.MMFFOptimizeMolecule(mol)
                writer = rdmolfiles.SDWriter(sdf_file)
                mol.SetProp("_Name", name)
                writer.write(mol)
                writer.close()

            # PaDEL descriptors
            compute_descriptors(sdf_file=sdf_file, excel_out=features_file, output_csv=None, timeout=None)

            # Get and process descriptors
            X_features, info_df = get_descriptors(df=features_file)
            X_features = select_descriptors(df=X_features)
            X_features = scale_descriptors(df=X_features)

            # Apply all 12 classifiers (fast - no more Java calls)
            for clf_type, sampling in CLASSIFIERS:
                result_df = predict_permeability(
                    clf_str=clf_type,
                    sampling_str=sampling,
                    mol_features=X_features.copy(),
                    info_df=info_df.copy(),
                    threshold="none",
                )
                prob = result_df["B3clf_predicted_probability"].iloc[0]
                label = result_df["B3clf_predicted_label"].iloc[0]
                all_results.append({
                    "Compound": name,
                    "Model": f"{clf_type}_{sampling}",
                    "P_BBBplus": round(prob, 4),
                    "Predicted": "BBB+" if label == 1 else "BBB-",
                })
            n_pos = sum(1 for r in all_results[-12:] if r["Predicted"] == "BBB+")
            print(f"done ({n_pos}/12 BBB+)", flush=True)

        except Exception as e:
            print(f"FAIL: {e}", flush=True)
            failed_compounds.append(name)
            for clf_type, sampling in CLASSIFIERS:
                all_results.append({
                    "Compound": name,
                    "Model": f"{clf_type}_{sampling}",
                    "P_BBBplus": None,
                    "Predicted": "ERROR",
                })

    if failed_compounds:
        print(f"\n⚠️  Failed compounds: {failed_compounds}", flush=True)

    results_df = pd.DataFrame(all_results)

    # ── Step 4: Consensus ──
    print("\n" + "=" * 80, flush=True)
    print("CONSENSUS RESULTS (12-model vote)", flush=True)
    print("=" * 80, flush=True)
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
        consensus_rows.append({
            "Compound": name,
            "Avg_P(BBB+)": round(avg_p, 4),
            "Votes": f"{n_pos}/{n_tot}",
            "Consensus": consensus,
            "Known": known,
            "Match": correct,
        })

    consensus_df = pd.DataFrame(consensus_rows)
    print(consensus_df.to_string(index=False), flush=True)

    n_correct = sum(1 for r in consensus_rows if r["Match"] == "✅")
    n_total = len(consensus_rows)
    print(f"\n📊 Consensus Accuracy: {n_correct}/{n_total} ({100*n_correct/n_total:.1f}%)", flush=True)

    # ── XGBoost best model ──
    print("\n── XGBoost classic_ADASYN (paper's recommended default) ──", flush=True)
    xgb_best = results_df[results_df["Model"] == "xgb_classic_ADASYN"].copy()
    xgb_best = xgb_best.merge(pd.DataFrame({"Compound": list(KNOWN_BBB.keys()), "Known": list(KNOWN_BBB.values())}))
    xgb_best["Match"] = xgb_best.apply(lambda r: "✅" if r["Predicted"] == r["Known"] else "❌", axis=1)
    print(xgb_best[["Compound", "P_BBBplus", "Predicted", "Known", "Match"]].to_string(index=False), flush=True)
    n_correct_xgb = (xgb_best["Predicted"] == xgb_best["Known"]).sum()
    print(f"\nXGB Accuracy: {n_correct_xgb}/{len(xgb_best)} ({100*n_correct_xgb/len(xgb_best):.1f}%)", flush=True)

    # ── Save results ──
    os.makedirs("results", exist_ok=True)
    full_df = results_df.merge(props_df[["Compound", "MW", "TPSA", "cLogP", "HBD", "CNS_MPO", "Known_BBB"]])
    full_df.to_csv("results/sm_bbb_predictions.csv", index=False)
    consensus_df_out = pd.DataFrame(consensus_rows)
    consensus_df_out = consensus_df_out.merge(props_df[["Compound", "MW", "CNS_MPO"]])
    consensus_df_out.to_csv("results/sm_bbb_consensus.csv", index=False)
    print(f"\n✅ Saved: results/sm_bbb_predictions.csv ({len(full_df)} rows)", flush=True)
    print(f"✅ Saved: results/sm_bbb_consensus.csv ({len(consensus_df_out)} rows)", flush=True)

    # Cleanup
    import shutil
    shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
