"""
MC4R Agonist Blood-Brain Barrier Permeability Prediction
Uses BrainPepPass v2 pipeline (XGBoost + mordred descriptors)
Reference: https://github.com/ewerton-cristhian/BrainPepPass
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from rdkit import Chem
from mordred import (Calculator, TopoPSA, SLogP, Weight, Lipinski,
                     TopologicalCharge, AcidBase, RotatableBond, MoeType,
                     AtomCount)
from mordred.Autocorrelation import GATS as GATS_cls

# Build a single combined calculator once (much faster than per-descriptor calls)
_COMBINED_CALC = Calculator(
    list(Calculator(Weight).descriptors) +
    list(Calculator(SLogP).descriptors) +
    list(Calculator(TopoPSA).descriptors) +
    list(Calculator(AtomCount).descriptors) +
    list(Calculator(Lipinski.HBondDonor).descriptors) +
    list(Calculator(Lipinski.HBondAcceptor).descriptors) +
    list(Calculator(TopologicalCharge).descriptors) +
    list(Calculator(AcidBase).descriptors) +
    list(Calculator(RotatableBond).descriptors) +
    list(Calculator(MoeType).descriptors) +
    list(Calculator(Lipinski).descriptors) +
    [GATS_cls(3, 'd')]
)
from xgboost import XGBClassifier, XGBRegressor

# ── Compound SMILES ──────────────────────────────────────────────────────────
# 5 compounds with known SMILES (ChEMBL / PubChem)
# TCMCB07 structure not publicly available in standard DBs
# NN9161: PubChem CID 70686774, CAS 1228015-10-8
COMPOUNDS = {
    "setmelanotide": {
        "smiles": "CC(=O)N[C@@H](CCCNC(=N)N)C(=O)N[C@H]1CSSC[C@@H](C(N)=O)NC(=O)[C@H](Cc2c[nH]c3ccccc23)NC(=O)[C@H](CCCNC(=N)N)NC(=O)[C@@H](Cc2ccccc2)NC(=O)[C@H](Cc2c[nH]cn2)NC(=O)[C@@H](C)NC1=O",
        "type": "cyclic peptide (disulfide)",
        "moa": "MC4R agonist",
        "note": "Approved for obesity (POMC/LEPR deficiency); peripheral + CNS",
    },
    "bremelanotide": {
        "smiles": "CCCC[C@H](NC(C)=O)C(=O)N[C@H]1CC(=O)NCCCC[C@@H](C(=O)O)NC(=O)[C@H](Cc2c[nH]c3ccccc23)NC(=O)[C@H](CCCNC(=N)N)NC(=O)[C@@H](Cc2ccccc2)NC(=O)[C@H](Cc2c[nH]cn2)NC1=O",
        "type": "cyclic peptide (lactam)",
        "moa": "MC4R agonist",
        "note": "Approved for HSDD; CNS-acting",
    },
    "afamelanotide": {
        "smiles": "CCCC[C@H](NC(=O)[C@H](CO)NC(=O)[C@H](Cc1ccc(O)cc1)NC(=O)[C@H](CO)NC(C)=O)C(=O)N[C@@H](CCC(=O)O)C(=O)N[C@@H](Cc1c[nH]cn1)C(=O)N[C@H](Cc1ccccc1)C(=O)N[C@@H](CCCNC(=N)N)C(=O)N[C@@H](Cc1c[nH]c2ccccc12)C(=O)NCC(=O)N[C@@H](CCCCN)C(=O)N1CCC[C@H]1C(=O)N[C@H](C(N)=O)C(C)C",
        "type": "linear peptide",
        "moa": "MC1R/MC4R agonist",
        "note": "Approved for erythropoietic protoporphyria; peripheral (subcutaneous implant)",
    },
    "bivamelagon": {
        "smiles": "CC(C)C(=O)N([C@H]1C[C@@H](C(=O)N2CCOCC2)N(C(=O)[C@@H]2CCN(C(C)(C)C)[C@H]2c2ccc(Cl)cc2)C1)[C@H]1CC[C@@H](C)CC1",
        "type": "small molecule",
        "moa": "MC4R agonist",
        "note": "Oral MC4R agonist in development (Lilly); small molecule → may cross BBB",
    },
    "TCMCB07": {
        "smiles": None,
        "type": "cyclic peptide",
        "moa": "MC4R antagonist",
        "note": "Anti-cachexia; peripheral MC4R antagonist; structure not in public DB",
    },
    "NN9161_LAMA2": {
        "smiles": "CCCC[C@@H](C(=O)N[C@H]1CCC(=O)NCCCC[C@H](NC(=O)[C@@H](NC(=O)[C@@H](NC(=O)[C@H](NC(=O)[C@@H]2C[C@H](CN2C1=O)O)CC3=CC=CC=C3)CCCNC(=N)N)CC4=CNC5=CC=CC=C54)C(=O)N)NC(=O)[C@H](CNC(=O)CN(CC(=O)O)CC(=O)O)NC(=O)[C@H](CC6=CN=CN6)NC(=O)[C@H](CCC(=O)N)NC(=O)[C@H](CO)NC(=O)CNC(=O)COCCOCCNC(=O)CCCCCCCCCCCCCCCC7=NN=NN7",
        "type": "lipidated peptide",
        "moa": "MC4R agonist",
        "note": "Novo Nordisk investigational; C18 fatty acid (tetrazole bioisostere) + PEG linker + cyclic peptide core; "
                "PubChem CID 70686774; MW ~2200 Da; designed for SC injection / peripheral action",
    },
}

MODEL_DIR = "/tmp/BrainPepPass/models/BrainPepPass_v2"


def load_models():
    """Load BrainPepPass v2 XGBoost models (JSON format, compatible with xgboost ≥3.1)."""
    pl_models = []
    for i in [1, 2, 3]:
        m = XGBRegressor()
        m.load_model(f"{MODEL_DIR}/PL{i}_model.json")
        pl_models.append(m)

    clf = XGBClassifier()
    clf.load_model(f"{MODEL_DIR}/classifier_model.json")

    logd = XGBRegressor()
    logd.load_model(f"{MODEL_DIR}/LogD_model.json")

    return pl_models, clf, logd


def calculate_descriptors(mol, logd_model):
    """
    Compute FC-4 feature vector (19 features) used by BrainPepPass v2.
    FC-1: MW, TPSA, LogP, nHBAcc, nHBDon, nN, nO, nN+nO, LogD(predicted)
    FC-3: JGI9, nAcid, JGI5, RotRatio, JGI6, JGI7, Lipinski, EState_VSA5, GhoseFilter, GATS3d
    """
    # Single-pass calculation (fast!)
    r = _COMBINED_CALC(mol)

    MW = round(float(r["MW"]), 3)
    LogP = round(float(r["SLogP"]), 3)
    TPSA = round(float(r["TopoPSA"]), 3)
    nN = round(int(r["nN"]), 3)
    nO = round(int(r["nO"]), 3)
    nNO = nN + nO
    HBD = round(int(r["nHBDon"]), 3)
    HBA = round(int(r["nHBAcc"]), 3)

    # Predict LogD from FC-1 base features
    logd_input = np.array([MW, TPSA, LogP, HBA, HBD, nN, nO, nNO]).reshape(1, -1)
    LogD = round(float(logd_model.predict(logd_input)[0]), 3)

    fc1 = [MW, TPSA, LogP, HBA, HBD, nN, nO, nNO, LogD]

    # FC-3 features
    JGI5 = round(float(r["JGI5"]), 3)
    JGI6 = round(float(r["JGI6"]), 3)
    JGI7 = round(float(r["JGI7"]), 3)
    JGI9 = round(float(r["JGI9"]), 3)
    nAcid = round(float(r["nAcid"]), 3)
    RotRatio = round(float(r["RotRatio"]), 3)
    EState_VSA5 = round(float(r["EState_VSA5"]), 3)
    GATS3d = round(float(r["GATS3d"]), 3)
    Lip_flag = float(1 if r["Lipinski"] is True else 0)
    Ghose_flag = float(1 if r["GhoseFilter"] is True else 0)

    fc3 = [JGI9, nAcid, JGI5, RotRatio, JGI6, JGI7, Lip_flag, EState_VSA5, Ghose_flag, GATS3d]

    return np.array(fc1 + fc3).reshape(1, -1)


def bpp_predict(features, pl_models, clf):
    """Run BrainPepPass prediction pipeline."""
    # Supervised dimensionality reduction: 19-D → 3-D
    pl_proj = np.concatenate([
        m.predict(features).reshape(-1, 1) for m in pl_models
    ], axis=1)

    label = clf.predict(pl_proj)[0]
    proba = clf.predict_proba(pl_proj)[0]

    return ("BBB+" if label == 1 else "BBB-"), proba


def main():
    print("Loading BrainPepPass v2 models...")
    pl_models, clf, logd = load_models()
    print("Models loaded.\n")

    rows = []
    descriptor_rows = []

    for name, info in COMPOUNDS.items():
        smiles = info["smiles"]
        if smiles is None:
            rows.append({
                "Compound": name,
                "Type": info["type"],
                "MoA": info["moa"],
                "BBB_Prediction": "N/A",
                "BBB+_Prob(%)": "N/A",
                "Note": info["note"],
            })
            print(f"[SKIP] {name}: {info['note']}")
            continue

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"[ERROR] {name}: invalid SMILES")
            continue

        try:
            feats = calculate_descriptors(mol, logd)
        except Exception as e:
            print(f"[ERROR] {name}: descriptor calculation failed — {e}")
            rows.append({
                "Compound": name,
                "Type": info["type"],
                "MoA": info["moa"],
                "BBB_Prediction": "ERROR",
                "BBB+_Prob(%)": str(e),
                "Note": info["note"],
            })
            continue

        # Check for NaN in features
        if np.isnan(feats).any():
            nan_idx = np.where(np.isnan(feats))[1]
            print(f"[WARN] {name}: NaN in features at indices {nan_idx}, replacing with 0")
            feats = np.nan_to_num(feats, nan=0.0)

        label, proba = bpp_predict(feats, pl_models, clf)
        prob_bbb_plus = round(proba[1] * 100, 1)

        rows.append({
            "Compound": name,
            "Type": info["type"],
            "MoA": info["moa"],
            "BBB_Prediction": label,
            "BBB+_Prob(%)": prob_bbb_plus,
            "Note": info["note"],
        })

        # Store descriptors for interpretation
        feat_names = ["MW", "TPSA", "SLogP", "nHBAcc", "nHBDon", "nN", "nO",
                      "nN+nO", "LogD(pred)", "JGI9", "nAcid", "JGI5", "RotRatio",
                      "JGI6", "JGI7", "Lipinski", "EState_VSA5", "GhoseFilter", "GATS3d"]
        descriptor_rows.append({"Compound": name} | dict(zip(feat_names, feats[0].round(3))))

        print(f"[{label}] {name:20s} | P(BBB+)={prob_bbb_plus:5.1f}% | "
              f"MW={feats[0,0]:.0f}, TPSA={feats[0,1]:.1f}, LogP={feats[0,2]:.2f}, "
              f"LogD={feats[0,8]:.2f}")

    print("\n" + "=" * 80)
    df = pd.DataFrame(rows)
    print("\nBrainPepPass v2 — BBB Permeability Summary:")
    print(df.to_string(index=False))

    if descriptor_rows:
        df_desc = pd.DataFrame(descriptor_rows)
        print("\nKey Physicochemical Descriptors:")
        print(df_desc.to_string(index=False))

    # Save results
    output_path = "/home/QYJI/das/druggability/results/mc4r_bbb_predictions.csv"
    df.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")

    return df


if __name__ == "__main__":
    main()
