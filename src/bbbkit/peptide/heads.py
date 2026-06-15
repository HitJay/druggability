"""
bbbkit.peptide.heads — 冻结 ESM-2 嵌入之上的轻量任务头

- ``make_head(kind)``：'linear'（标准化逻辑回归基线）或 'mlp'（小型非线性头）。
- ``cross_validate``：训练集上的 5 折分层 CV。
- ``select_hparams``：仅用训练集 CV 的 ROC-AUC 选超参（绝不接触测试集）。
- ``fit_eval``：全训练集拟合 + 留出测试集单次评估。

需要 scikit-learn（`pip install bbbkit[peptide]`）。
"""

from __future__ import annotations

import numpy as np

RNG = 42

# 超参网格——仅由训练集 CV 选择
_GRID = {
    "linear": [{"C": c} for c in (0.1, 1.0, 10.0)],
    "mlp": [{"hidden": h, "alpha": a}
            for h in ((128,), (256,)) for a in (1e-3, 1e-2)],
}


def make_head(kind: str = "linear", C: float = 1.0,
              hidden=(256,), alpha: float = 1e-3):
    """构造一个任务头管线（标准化 + 分类器）。"""
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline

    if kind == "mlp":
        from sklearn.neural_network import MLPClassifier
        return make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=hidden, alpha=alpha,
                          activation="relu", solver="adam", max_iter=300,
                          early_stopping=True, n_iter_no_change=15,
                          random_state=RNG))
    from sklearn.linear_model import LogisticRegression
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=5000, C=C, class_weight="balanced"))


def _metrics(y, proba, thr: float = 0.5) -> dict:
    from sklearn.metrics import (roc_auc_score, accuracy_score,
                                 matthews_corrcoef, confusion_matrix)
    pred = (proba >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    sens = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "ACC": round(float(accuracy_score(y, pred)), 4),
        "AUC": round(float(roc_auc_score(y, proba)), 4),
        "MCC": round(float(matthews_corrcoef(y, pred)), 4),
        "Sens": round(float(sens), 4),
        "Spec": round(float(spec), 4),
    }


def cross_validate(X, y, kind: str = "linear", n_splits: int = 5, **kw) -> dict:
    from sklearn.model_selection import StratifiedKFold
    y = np.asarray(y)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RNG)
    aucs, accs, mccs = [], [], []
    for tr, va in skf.split(X, y):
        clf = make_head(kind, **kw).fit(X[tr], y[tr])
        m = _metrics(y[va], clf.predict_proba(X[va])[:, 1])
        aucs.append(m["AUC"]); accs.append(m["ACC"]); mccs.append(m["MCC"])
    return {
        "AUC": round(float(np.mean(aucs)), 4),
        "AUC_sd": round(float(np.std(aucs)), 4),
        "ACC": round(float(np.mean(accs)), 4),
        "MCC": round(float(np.mean(mccs)), 4),
    }


def select_hparams(X, y, kind: str, n_splits: int = 5):
    """仅用训练集 CV 的 ROC-AUC 选超参，返回 (best_params, best_cv_auc)。"""
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    y = np.asarray(y)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RNG)
    best, best_auc = None, -1.0
    for params in _GRID[kind]:
        auc = float(np.mean(cross_val_score(
            make_head(kind, **params), X, y, cv=skf, scoring="roc_auc")))
        if auc > best_auc:
            best_auc, best = auc, params
    return best, round(best_auc, 4)


def fit_eval(Xtr, ytr, Xte, yte, kind: str = "linear", **kw):
    """全训练集拟合 + 留出测试集单次评估，返回 (clf, metrics)。"""
    clf = make_head(kind, **kw).fit(Xtr, np.asarray(ytr))
    return clf, _metrics(np.asarray(yte), clf.predict_proba(Xte)[:, 1])
