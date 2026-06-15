"""
bbbkit.peptide.tasks — 肽 benchmark 任务注册表

每个任务记录数据源、是否官方划分、以及已发表 SOTA 参考（注明出处，用于诚实对比）。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PeptideTask:
    key: str
    name: str
    prop: str
    source: str
    official_split: bool
    sota: dict = field(default_factory=dict)
    sota_src: str = ""


REGISTRY: list[PeptideTask] = [
    PeptideTask(
        "bbb", "BBB penetration", "blood-brain-barrier penetrating peptide",
        "B3Pred Dataset-1 (Kumar et al., Pharmaceutics 13(8):1206, 2021)",
        True, {"AUC": 0.87, "ACC": 0.85},
        "Kumar et al. 2021 (approx., main-model validation)"),
    PeptideTask(
        "acp_main", "Anticancer (main)", "anticancer peptide",
        "AntiCP 2.0 main (Agrawal et al., Brief Bioinform 22(3):bbaa153, 2021)",
        True, {"AUC": 0.82, "MCC": 0.51},
        "Agrawal et al. 2021 (main dataset, best model)"),
    PeptideTask(
        "acp_alternate", "Anticancer (alternate)", "anticancer peptide",
        "AntiCP 2.0 alternate (Agrawal et al., 2021)",
        True, {"AUC": 0.98, "MCC": 0.85},
        "Agrawal et al. 2021 (alternate dataset, best model)"),
    PeptideTask(
        "toxicity", "Toxicity", "toxic peptide",
        "ToxinPred v1 main + independent (Gupta et al., PLoS ONE 8(9):e73957, 2013)",
        True, {"AUC": 0.95, "MCC": 0.88, "ACC": 0.94},
        "Gupta et al. 2013 (approx., SVM main-dataset)"),
    PeptideTask(
        "amp", "Antimicrobial", "antimicrobial peptide",
        "LMPred / DRAMP 2.0 + UniProt (Dee, 2021; DRAMP 2.0 Kang et al. 2019)",
        True, {"AUC": 0.98, "ACC": 0.96},
        "Dee 2021 (LMPred CNN, test set)"),
    PeptideTask(
        "hemolytic", "Hemolytic", "hemolytic peptide",
        "HemoPI-1 (Chaudhary et al., Sci Rep 6:22843, 2016)",
        True, {"AUC": 0.95, "MCC": 0.73, "ACC": 0.87},
        "Chaudhary et al. 2016 (HemoPI-1, SVM, validation)"),
]

_BY_KEY = {t.key: t for t in REGISTRY}


def get_tasks(keys=None) -> list[PeptideTask]:
    if not keys:
        return list(REGISTRY)
    return [_BY_KEY[k] for k in keys if k in _BY_KEY]
