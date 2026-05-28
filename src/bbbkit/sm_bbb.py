"""
Small-molecule BBB permeability prediction using B3clf + CNS-MPO scoring.

Dependencies:
    - b3clf (installed from GitHub: theochem/B3clf, relaxed sklearn version)
    - padelpy + Java 6+ (for PaDEL descriptors)
    - rdkit (for SMILES → 3D geometry)

Usage:
    from bbbkit.sm_bbb import predict_sm_bbb, cns_mpo_score
    results = predict_sm_bbb({"bivamelagon": "CC(C)..."})
"""

import os
import tempfile
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# ── CNS-MPO Score ────────────────────────────────────────────────────────────
# Reference: Wager TT et al. ACS Chem Neurosci. 2010;1(6):420-434.

def _t0_monotone_decrease(value, lower, upper):
    """Piecewise linear transform: 1 at ≤lower, 0 at ≥upper, linear between."""
    if value <= lower:
        return 1.0
    elif value >= upper:
        return 0.0
    else:
        return 1.0 - (value - lower) / (upper - lower)


def _t0_tpsa(value):
    """TPSA has a desirability window: 40-90 optimal, drops off outside."""
    if 40 <= value <= 90:
        return 1.0
    elif value < 40:
        return max(0.0, value / 40.0)
    else:  # > 90
        return max(0.0, 1.0 - (value - 90) / 30.0)


def cns_mpo_score(clogp, clogd, mw, tpsa, hbd, pka):
    """Compute CNS Multi-Parameter Optimization score (0-6).

    Parameters
    ----------
    clogp : float - calculated LogP
    clogd : float - calculated LogD at pH 7.4
    mw : float - molecular weight
    tpsa : float - topological polar surface area
    hbd : int - hydrogen bond donor count
    pka : float - most basic pKa

    Returns
    -------
    float : CNS-MPO score (0-6, ≥4 desirable for CNS drugs)
    """
    score = (
        _t0_monotone_decrease(clogp, 3.0, 5.0) +
        _t0_monotone_decrease(clogd, 2.0, 4.0) +
        _t0_monotone_decrease(mw, 360.0, 500.0) +
        _t0_tpsa(tpsa) +
        _t0_monotone_decrease(hbd, 0.5, 3.5) +
        _t0_monotone_decrease(pka, 8.0, 10.0)
    )
    return round(score, 2)


def compute_physichem(smiles):
    """Compute physicochemical properties for CNS-MPO from SMILES.

    Returns dict with keys: MW, TPSA, cLogP, HBD, HBA, RotBonds, cLogD_est, pKa_est
    """
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mw = Descriptors.MolWt(mol)
    tpsa = Descriptors.TPSA(mol)
    clogp = Descriptors.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    rotbonds = rdMolDescriptors.CalcNumRotatableBonds(mol)

    # Estimate LogD ≈ LogP - 0.5 (rough approximation at pH 7.4 for neutral molecules)
    # For basic amines, LogD is typically lower than LogP
    clogd_est = clogp - 0.5 if hbd > 0 else clogp

    # pKa estimation: very rough heuristic (proper: use Epik/ChemAxon)
    # If contains basic nitrogen, assume pKa ~ 8-9
    n_basic = smiles.count("N") - smiles.count("n") - smiles.count("N(C(=O)")
    pka_est = 8.5 if n_basic > 0 else 6.0

    return {
        "MW": round(mw, 1),
        "TPSA": round(tpsa, 1),
        "cLogP": round(clogp, 2),
        "cLogD_est": round(clogd_est, 2),
        "HBD": hbd,
        "HBA": hba,
        "RotBonds": rotbonds,
        "pKa_est": round(pka_est, 1),
    }


# ── B3clf Wrapper ────────────────────────────────────────────────────────────

def predict_sm_bbb(compounds, classifiers=None):
    """Run B3clf prediction for a set of small molecules.

    Parameters
    ----------
    compounds : dict
        {name: SMILES} mapping
    classifiers : list of (clf, sampling) tuples, optional
        Default uses available compatible models.

    Returns
    -------
    pd.DataFrame with columns: Compound, SMILES, clf_model, P(BBB+), Label, MW, TPSA, cLogP, CNS_MPO
    """
    from b3clf import b3clf

    if classifiers is None:
        classifiers = [
            ("logreg", "classic_ADASYN"),
            ("logreg", "classic_SMOTE"),
            ("logreg", "common"),
            ("knn", "classic_SMOTE"),
        ]

    results = []

    for name, smiles in compounds.items():
        # Compute physichem
        props = compute_physichem(smiles)
        if props is None:
            print(f"⚠️  Cannot parse SMILES for {name}, skipping")
            continue

        mpo = cns_mpo_score(
            clogp=props["cLogP"],
            clogd=props["cLogD_est"],
            mw=props["MW"],
            tpsa=props["TPSA"],
            hbd=props["HBD"],
            pka=props["pKa_est"],
        )

        # Write temp SMI file
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".smi", delete=False, dir="/tmp"
        )
        tmp.write(f"{smiles}\t{name}\n")
        tmp.close()

        for clf_type, sampling in classifiers:
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
                # Clean up output
                if os.path.exists(out_file):
                    os.remove(out_file)

                results.append({
                    "Compound": name,
                    "SMILES": smiles,
                    "Model": f"{clf_type}_{sampling}",
                    "P(BBB+)": round(prob, 4),
                    "Label": "BBB+" if label == 1 else "BBB-",
                    "MW": props["MW"],
                    "TPSA": props["TPSA"],
                    "cLogP": props["cLogP"],
                    "HBD": props["HBD"],
                    "CNS_MPO": mpo,
                })
            except Exception as e:
                results.append({
                    "Compound": name,
                    "SMILES": smiles,
                    "Model": f"{clf_type}_{sampling}",
                    "P(BBB+)": None,
                    "Label": f"ERROR: {e}",
                    "MW": props["MW"],
                    "TPSA": props["TPSA"],
                    "cLogP": props["cLogP"],
                    "HBD": props["HBD"],
                    "CNS_MPO": mpo,
                })

        os.unlink(tmp.name)

    return pd.DataFrame(results)


def consensus_prediction(df):
    """Compute consensus BBB prediction from multi-model results.

    Parameters
    ----------
    df : pd.DataFrame from predict_sm_bbb()

    Returns
    -------
    pd.DataFrame: one row per compound with consensus vote + probability
    """
    consensus = []
    for name, group in df.groupby("Compound"):
        valid = group[group["P(BBB+)"].notna()]
        if valid.empty:
            continue
        avg_prob = valid["P(BBB+)"].mean()
        n_positive = (valid["Label"] == "BBB+").sum()
        n_total = len(valid)
        consensus.append({
            "Compound": name,
            "Avg_P(BBB+)": round(avg_prob, 4),
            "Votes_BBB+": f"{n_positive}/{n_total}",
            "Consensus": "BBB+" if n_positive > n_total / 2 else "BBB-",
            "MW": valid["MW"].iloc[0],
            "TPSA": valid["TPSA"].iloc[0],
            "cLogP": valid["cLogP"].iloc[0],
            "CNS_MPO": valid["CNS_MPO"].iloc[0],
        })
    return pd.DataFrame(consensus)
