"""
bbbkit.peptide.datasets — 已发表肽 benchmark 数据集的下载与规范化

将多个公开 benchmark 解析为统一的 ``{train,test}.csv``（列：sequence,label），
并严格保留各数据集的**官方 train/test 划分**。

Benchmark 完整性约定：
- 仅采用已发表数据集；有官方划分的逐字沿用，测试集不参与训练/选型。
- 仅 20 种标准氨基酸，肽长 5–50；跨集去重（防泄漏）。

数据源（均为 GitHub raw，可经 curl 获取；部分环境 HuggingFace 不可达）：
- BBB:        raghavagps/B3Pred（Kumar 2021）
- 抗癌 ACP:   raghavagps/anticp2（Agrawal 2021），main / alternate 两套官方划分
- 毒性:       raghavagps/toxinpred v1（Gupta 2013），独立测试集
- 抗菌 AMP:   williamdee1/LMPred_AMP_Prediction（DRAMP 2.0）
- 溶血:       raghavagps/hemopi（Chaudhary 2016，HemoPI-1）
"""

from __future__ import annotations

import csv
import io
import subprocess
from pathlib import Path

AA = set("ACDEFGHIKLMNPQRSTVWY")
LEN_MIN, LEN_MAX = 5, 50

ANTICP = "https://raw.githubusercontent.com/raghavagps/anticp2/master/datasets"
TOXIN = "https://raw.githubusercontent.com/raghavagps/toxinpred/master"
HEMOPI = "https://raw.githubusercontent.com/raghavagps/hemopi/master/HemoPI/HemoPI"
LMPRED = "https://raw.githubusercontent.com/williamdee1/LMPred_AMP_Prediction/main/LM_Pred_Dataset"


def fetch(url: str, timeout: int = 40) -> str:
    """经 curl 获取文本（部分环境 Python ssl 因企业自签根证书失败，curl 走系统 CA）。"""
    out = subprocess.run(
        ["curl", "-sS", "--connect-timeout", "8", "-m", str(timeout), url],
        capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout:
        raise RuntimeError(
            f"下载失败（{out.returncode}）: {url}\n{out.stderr[:160]}")
    return out.stdout


def clean_seq(s: str) -> str | None:
    s = "".join(c for c in s.strip().upper() if c.isalpha())
    if not s or set(s) - AA or not (LEN_MIN <= len(s) <= LEN_MAX):
        return None
    return s


def _parse_lines(text: str) -> list[str]:
    """一行一条序列（anticp2 / toxinpred v1）。"""
    return [c for c in (clean_seq(ln) for ln in text.splitlines()) if c]


def _parse_fasta(text: str) -> list[str]:
    out, cur = [], []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith(">"):
            if cur:
                c = clean_seq("".join(cur))
                if c:
                    out.append(c)
                cur = []
        elif ln:
            cur.append(ln)
    if cur:
        c = clean_seq("".join(cur))
        if c:
            out.append(c)
    return out


def _dedup(seqs: list[str]) -> list[str]:
    seen, out = set(), []
    for s in seqs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _write_csv(path: Path, pos: list[str], neg: list[str]) -> tuple[int, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sequence", "label"])
        for s in pos:
            w.writerow([s, 1])
        for s in neg:
            w.writerow([s, 0])
    return len(pos), len(neg)


def _split_no_leak(ptr, ntr, pte, nte):
    train = set(ptr) | set(ntr)
    return [s for s in pte if s not in train], [s for s in nte if s not in train]


# ─── 各任务 onboarding ──────────────────────────────────────────────

def onboard_acp(data_dir: Path, variant: str = "main"):
    f = {k: f"{ANTICP}/{k}_{variant}" for k in
         ("pos_train", "neg_train", "pos_test", "neg_test")}
    d = {k: _dedup(_parse_lines(fetch(u))) for k, u in f.items()}
    pte, nte = _split_no_leak(d["pos_train"], d["neg_train"], d["pos_test"], d["neg_test"])
    _write_csv(data_dir / f"acp_{variant}" / "train.csv", d["pos_train"], d["neg_train"])
    _write_csv(data_dir / f"acp_{variant}" / "test.csv", pte, nte)


def onboard_toxicity(data_dir: Path):
    g = lambda n: _dedup(_parse_lines(fetch(f"{TOXIN}/{n}.txt")))
    ptr, ntr = g("pos-maindataset-1"), g("neg-maindataset-1")
    pte, nte = g("pos-indep-1"), g("neg-indep-1")
    pte, nte = _split_no_leak(ptr, ntr, pte, nte)
    _write_csv(data_dir / "toxicity" / "train.csv", ptr, ntr)
    _write_csv(data_dir / "toxicity" / "test.csv", pte, nte)


def onboard_hemolytic(data_dir: Path):
    ptr = _dedup(_parse_fasta(fetch(f"{HEMOPI}/pos.fa.txt")))
    ntr = _dedup(_parse_fasta(fetch(f"{HEMOPI}/neg.fa.txt")))
    pte = _dedup(_parse_fasta(fetch(f"{HEMOPI}/pos.fa_val.txt")))
    nte = _dedup(_parse_fasta(fetch(f"{HEMOPI}/neg.fa._val.txt")))
    pte, nte = _split_no_leak(ptr, ntr, pte, nte)
    _write_csv(data_dir / "hemolytic" / "train.csv", ptr, ntr)
    _write_csv(data_dir / "hemolytic" / "test.csv", pte, nte)


def _parse_lmpred(x_url: str, y_url: str):
    rows = list(csv.DictReader(io.StringIO(fetch(x_url))))
    yraw = [ln.strip() for ln in fetch(y_url).splitlines() if ln.strip()]
    labels = yraw if (yraw and yraw[0] in ("0", "1")) else yraw[1:]
    pos, neg = [], []
    for row, lab in zip(rows, labels):
        s = clean_seq(row.get("Sequence", ""))
        if not s:
            continue
        (pos if str(lab).strip() in ("1", "1.0") else neg).append(s)
    return _dedup(pos), _dedup(neg)


def onboard_amp(data_dir: Path):
    ptr, ntr = _parse_lmpred(f"{LMPRED}/X_train.csv", f"{LMPRED}/y_train.csv")
    pte, nte = _parse_lmpred(f"{LMPRED}/X_test.csv", f"{LMPRED}/y_test.csv")
    pte, nte = _split_no_leak(ptr, ntr, pte, nte)
    _write_csv(data_dir / "amp" / "train.csv", ptr, ntr)
    _write_csv(data_dir / "amp" / "test.csv", pte, nte)


_ONBOARD = {
    "acp_main": lambda d: onboard_acp(d, "main"),
    "acp_alternate": lambda d: onboard_acp(d, "alternate"),
    "toxicity": onboard_toxicity,
    "hemolytic": onboard_hemolytic,
    "amp": onboard_amp,
}


def download(data_dir: str | Path, keys=None) -> list[str]:
    """下载并规范化指定任务（默认全部内置任务，BBB 除外——见 tasks 注册表）。"""
    data_dir = Path(data_dir)
    keys = list(keys) if keys else list(_ONBOARD)
    done = []
    for k in keys:
        if k not in _ONBOARD:
            continue
        _ONBOARD[k](data_dir)
        done.append(k)
    return done


def load_split(data_dir: str | Path, task_key: str):
    """读取某任务的 (train, test)，各为 (sequences, labels)。"""
    data_dir = Path(data_dir)

    def read(split):
        seqs, labels = [], []
        with open(data_dir / task_key / f"{split}.csv") as fh:
            for r in csv.DictReader(fh):
                seqs.append(r["sequence"])
                labels.append(int(r["label"]))
        return seqs, labels

    return read("train"), read("test")
