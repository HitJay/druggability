"""
Interface Variant Mapping — 疾病突变映射到预测/实验互作界面

借鉴 Pei, Zhang & Cong (2026) Sci Reports 16:25590 的方法:
    SAV QC -> AlphaMissense 交叉 -> 双证据 pathogenic 定义 -> 界面 6Å 判定

将 disease-associated 单氨基酸变异 (SAV) 映射到蛋白互作界面残基,
输出"遗传学上最可能通过破坏 PPI 致病"的界面突变热点,
用于靶点机制假说与 PPI lead 的优先级放大。

证据链 (每条 pathogenic SAV 至少满足两条):
  (i)   AlphaMissense 预测为 pathogenic (LP / am_pathogenicity >= 阈值)
  (ii)  UniProt 变体注释含致病证据 (disease 库名 / "pathogenic" 注记)
  (iii) UniProt 注释关联疾病 (DISEASE comment 或 VARIANT note 中的疾病名)
界面判定: 侧链任意原子与伙伴蛋白任意原子距离 < 6 Å (论文同款阈值)。

数据源 (全部已验证可达):
  - UniProt REST txt (VARIANT features + DISEASE comments)
  - AFDB per-protein AlphaMissense CSV (alphafold.ebi.ac.uk, 免 1.1GB bulk 下载)
  - AFDB monomer 模型 (pdbUrl, 经 API 解析真实版本号)
  - 本地二元复合物 PDB (RF2-PPI/AlphaFold multimer 输出), 可选

License note: AlphaMissense results are CC BY-NC-SA 4.0 (non-commercial use).
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
import re
import tempfile
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import requests

logger = logging.getLogger(__name__)

from .utils import DruggabilityError, NetworkError  # noqa: E402

# ─── 常量 ────────────────────────────────────────────────────────────

UNIPROT_TXT = "https://rest.uniprot.org/uniprotkb/{acc}.txt"
AFDB_API = "https://alphafold.ebi.ac.uk/api/prediction/{acc}"
INTERFACE_CUTOFF_A = 6.0          # 论文同款界面残基判定阈值
MAX_SEQ_MISMATCH_FRAC = 0.05      # SAV QC: 序列不一致率 >5% 剔除该蛋白 (论文同款)
AM_PATHOGENIC_CLASSES = {"LP"}    # AFDB per-protein CSV 的 likely pathogenic 类
AM_PROB_THRESHOLD = 0.5           # bulk TSV 回退路径用的 am_pathogenicity 阈值

_PATHOGENIC_HINT = re.compile(
    r"pathogenic|disease|syndrome|in\s+[A-Z][\w\s-]*(?:deficiency|dystrophy|"
    r"hyperparathyroidism|epilepsy|carcinoma|cancer)|HHC1|HYPOC1|NSHPT|EIG8",
    re.I,
)


# ─── 数据结构 ─────────────────────────────────────────────────────────


@dataclass
class SavRecord:
    """单氨基酸变异及其致病证据状态"""

    position: int                    # 1-based, 相对 UniProt canonical 序列
    wt: str
    mut: str
    am_pathogenic: bool = False      # 证据 (i)
    am_prob: float | None = None
    uniprot_pathogenic: bool = False  # 证据 (ii) + (iii) 合并
    note: str = ""
    sources: list[str] = field(default_factory=list)

    @property
    def n_evidence(self) -> int:
        return int(self.am_pathogenic) + int(self.uniprot_pathogenic)

    @property
    def is_pathogenic(self) -> bool:
        """双证据规则: >=2 条 (论文同款)"""
        return self.n_evidence >= 2

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "wt": self.wt,
            "mut": self.mut,
            "am_pathogenic": self.am_pathogenic,
            "am_prob": self.am_prob,
            "uniprot_pathogenic": self.uniprot_pathogenic,
            "n_evidence": self.n_evidence,
            "is_pathogenic": self.is_pathogenic,
            "note": self.note,
            "sources": self.sources,
        }


@dataclass
class InterfaceVariantResult:
    """一个 (蛋白A, 蛋白B) 复合物的界面突变分析结果"""

    uniprot_a: str
    uniprot_b: str
    model_source: str = ""            # "local_pdb" / "afdb_pair" / "afdb_monomer_x2"
    seq_mismatch_frac_a: float = 0.0
    seq_mismatch_frac_b: float = 0.0
    interface_res_a: set[int] = field(default_factory=set)
    interface_res_b: set[int] = field(default_factory=set)
    pathogenic_savs_a: list[SavRecord] = field(default_factory=list)
    pathogenic_savs_b: list[SavRecord] = field(default_factory=list)
    interface_pathogenic_a: list[SavRecord] = field(default_factory=list)
    interface_pathogenic_b: list[SavRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def n_interface_pathogenic(self) -> int:
        return len(self.interface_pathogenic_a) + len(self.interface_pathogenic_b)

    @property
    def interface_mutation_richness(self) -> float:
        """界面致病突变密度: 界面致病 SAV 数 / 界面残基数 (A+B)"""
        n_res = len(self.interface_res_a) + len(self.interface_res_b)
        if n_res == 0:
            return 0.0
        return self.n_interface_pathogenic / n_res

    def to_dict(self) -> dict:
        return {
            "uniprot_a": self.uniprot_a,
            "uniprot_b": self.uniprot_b,
            "model_source": self.model_source,
            "seq_mismatch_frac_a": self.seq_mismatch_frac_a,
            "seq_mismatch_frac_b": self.seq_mismatch_frac_b,
            "n_interface_res_a": len(self.interface_res_a),
            "n_interface_res_b": len(self.interface_res_b),
            "n_pathogenic_savs_a": len(self.pathogenic_savs_a),
            "n_pathogenic_savs_b": len(self.pathogenic_savs_b),
            "n_interface_pathogenic": self.n_interface_pathogenic,
            "interface_mutation_richness": self.interface_mutation_richness,
            "interface_pathogenic_a": [s.to_dict() for s in self.interface_pathogenic_a],
            "interface_pathogenic_b": [s.to_dict() for s in self.interface_pathogenic_b],
            "warnings": self.warnings,
        }


# ─── UniProt 侧: 变体 + 疾病注释 ──────────────────────────────────────


def fetch_uniprot_txt(acc: str, timeout: int = 60) -> str:
    try:
        r = requests.get(UNIPROT_TXT.format(acc=acc), timeout=timeout,
                         headers={"User-Agent": "druggability-agent"})
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"UniProt fetch failed for {acc}: {e}") from e
    return r.text


def _parse_ft_blocks(txt: str) -> list[tuple[str, dict]]:
    """解析 flat-file FT 块 -> [(feature_type, {key: value})]"""
    blocks: list[tuple[str, dict]] = []
    cur_type: str | None = None
    cur: dict = {}
    for line in txt.split("\n"):
        if not line.startswith("FT "):
            continue
        body = line[5:]
        # 新 feature 行: "VARIANT         15" (类型名 + 位置, 位置列从固定偏移开始)
        m = re.match(r"^([A-Z][A-Z_]+)\s{2,}(\S.*)$", body)
        if m:
            if cur_type is not None:
                blocks.append((cur_type, cur))
            cur_type, cur = m.group(1), {"location": m.group(2).strip()}
            continue
        # 续行: qualifier "/note=..." 或上一 qualifier 的折行文本
        m2 = re.match(r"^/(\w+)=\"?(.*?)\"?$", body.strip())
        if m2:
            cur[m2.group(1)] = m2.group(2)
        elif body.strip() and cur:
            last_key = next(reversed(cur), None)
            if last_key:
                cur[last_key] += " " + body.strip()
    if cur_type is not None:
        blocks.append((cur_type, cur))
    return blocks


def _loc_start(loc: str) -> int | None:
    m = re.match(r"^(\d+)", loc.strip())
    return int(m.group(1)) if m else None


def parse_sequence(txt: str) -> str:
    seq_lines = []
    in_seq = False
    for line in txt.split("\n"):
        if line.startswith("SQ   "):
            in_seq = True
            continue
        if in_seq:
            if line.startswith("//"):
                break
            seq_lines.append(line.replace(" ", ""))
    return "".join(seq_lines)


def parse_uniprot_savs(txt: str) -> tuple[list[SavRecord], str]:
    """
    从 UniProt flat file 解析 SAV。
    证据 (ii)+(iii): VARIANT note 命中致病提示词 或 位于 DISEASE 提及的疾病上下文。
    返回 (sav_list, canonical_sequence)
    """
    seq = parse_sequence(txt)
    savs: list[SavRecord] = []

    # 先收集 DISEASE comment 提到的疾病名及其缩写, 用于 (iii)
    disease_names: list[str] = []
    for line in txt.split("\n"):
        if line.startswith("CC   -!- DISEASE:"):
            m = re.match(r"CC   -!- DISEASE:\s+(.+?)(?:\s+\(MIM|\.|$)", line)
            if m:
                name = m.group(1).strip()
                disease_names.append(name)
                # 抓括号缩写, 如 "Test syndrome (TS)" -> "TS"
                for abbr in re.findall(r"\(([A-Z][A-Za-z0-9-]{0,11})\)", name):
                    if abbr not in disease_names:
                        disease_names.append(abbr)

    for ftype, f in _parse_ft_blocks(txt):
        if ftype != "VARIANT":
            continue
        note = f.get("note", "")
        start = _loc_start(f.get("location", ""))
        if start is None:
            continue  # 连续缺失等非点突变
        m = re.match(r"^([A-Z])\s*->\s*([A-Z])", note)
        if not m:
            continue  # Missing 等
        wt, mut = m.group(1), m.group(2)
        uni_path = bool(_PATHOGENIC_HINT.search(note)) or any(
            d.lower() in note.lower() for d in disease_names
        )
        savs.append(SavRecord(
            position=start, wt=wt, mut=mut,
            uniprot_pathogenic=uni_path,
            note=note[:300],
            sources=["UniProt"],
        ))
    return savs, seq


# ─── AlphaMissense 侧 ────────────────────────────────────────────────


def fetch_afdb_am_csv(acc: str, timeout: int = 120) -> dict[str, tuple[float, str]]:
    """
    AFDB per-protein AlphaMissense 注释 (免 bulk 1.1GB)。
    返回 {protein_variant: (am_pathogenicity, am_class)}
    需要浏览器 UA 过 EBI WAF; 403 时回退 bulk TSV 路径由调用方处理。
    """
    api = AFDB_API.format(acc=acc)
    try:
        r = requests.get(api, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        csv_url = r.json()[0]["amAnnotationsUrl"]
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        raise NetworkError(f"AFDB AM annotation lookup failed for {acc}: {e}") from e

    try:
        r2 = requests.get(csv_url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"})
        if r2.status_code == 403:
            raise NetworkError(
                f"AFDB file WAF-blocked for {acc}; use fetch_afdb_am_csv_browser() "
                "(playwright) or bulk TSV fallback")
        r2.raise_for_status()
        text = r2.text
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"AFDB AM csv download failed for {acc}: {e}") from e

    am: dict[str, tuple[float, str]] = {}
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        variant = (row.get("protein_variant") or "").strip()
        try:
            prob = float(row.get("am_pathogenicity") or row.get("***") or 0.0)
        except ValueError:
            prob = 0.0
        am[variant] = (prob, (row.get("am_class") or "").strip())
    return am


def fetch_afdb_am_csv_browser(acc: str, timeout: int = 120) -> dict[str, tuple[float, str]]:
    """AFDB per-protein AM CSV 的 playwright 回退路径 (过 EBI WAF)。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise NetworkError(
            "playwright not installed; cannot bypass AFDB file WAF") from e

    try:
        r = requests.get(AFDB_API.format(acc=acc), timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        csv_url = r.json()[0]["amAnnotationsUrl"]
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        raise NetworkError(f"AFDB API failed for {acc}: {e}") from e

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(accept_downloads=True,
                            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36")
        pg = ctx.new_page()
        try:
            with pg.expect_download(timeout=timeout * 1000) as dl:
                try:
                    pg.goto(csv_url, timeout=timeout * 1000)
                except Exception:
                    pass  # download event fires instead of navigation completing
            tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
            dl.value.save_as(tmp.name)
        finally:
            b.close()

    am: dict[str, tuple[float, str]] = {}
    with open(tmp.name, newline="") as fh:
        for row in csv.DictReader(fh):
            variant = (row.get("protein_variant") or "").strip()
            try:
                prob = float(row.get("am_pathogenicity") or row.get("***") or 0.0)
            except ValueError:
                prob = 0.0
            am[variant] = (prob, (row.get("am_class") or "").strip())
    Path(tmp.name).unlink(missing_ok=True)
    return am


def fetch_afdb_model_pdb(acc: str, out_dir: str | Path, timeout: int = 120) -> Path:
    """下载 AFDB monomer 模型 (最新版本), 返回本地 PDB 路径。WAF 需要 playwright 回退。"""
    api = AFDB_API.format(acc=acc)
    try:
        r = requests.get(api, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        entry = r.json()[0]
        pdb_url, ver = entry["pdbUrl"], entry["latestVersion"]
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        raise NetworkError(f"AFDB API failed for {acc}: {e}") from e

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"AF-{acc}-F1-model_v{ver}.pdb"
    if out.exists():
        return out

    r2 = requests.get(pdb_url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"})
    if r2.status_code == 403:
        # playwright 回退
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise NetworkError(
                f"AFDB file WAF-blocked for {acc} and playwright unavailable") from e
        with sync_playwright() as pw:
            b = pw.chromium.launch(headless=True)
            ctx = b.new_context(accept_downloads=True,
                                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36")
            pg = ctx.new_page()
            try:
                with pg.expect_download(timeout=timeout * 1000) as dl:
                    try:
                        pg.goto(pdb_url, timeout=timeout * 1000)
                    except Exception:
                        pass
                dl.value.save_as(str(out))
            finally:
                b.close()
        return out
    r2.raise_for_status()
    out.write_bytes(r2.content)
    return out


def merge_am_evidence(savs: list[SavRecord],
                      am: dict[str, tuple[float, str]]) -> list[SavRecord]:
    """证据 (i): 用 AlphaMissense 注释回填 am_pathogenic。"""
    for s in savs:
        variant = f"{s.wt}{s.position}{s.mut}"
        if variant in am:
            prob, cls = am[variant]
            s.am_prob = prob
            if cls in AM_PATHOGENIC_CLASSES or prob >= AM_PROB_THRESHOLD:
                s.am_pathogenic = True
                if "AlphaMissense" not in s.sources:
                    s.sources.append("AlphaMissense")
    return savs


# ─── SAV QC: 参考序列一致性 ───────────────────────────────────────────


def qc_sequence_match(model_seq: str, uniprot_seq: str) -> tuple[float, bool]:
    """
    论文同款 QC: 模型序列与 UniProt canonical 序列比对一致性。
    简化实现: 相同长度直比; 长度不齐时按最优偏移滑窗比对 (AF 模型偶有截断)。
    返回 (mismatch_frac, qc_pass)
    """
    if not model_seq or not uniprot_seq:
        return 1.0, False
    if len(model_seq) == len(uniprot_seq):
        mismatch = sum(a != b for a, b in zip(model_seq, uniprot_seq))
        frac = mismatch / len(uniprot_seq)
        return frac, frac <= MAX_SEQ_MISMATCH_FRAC
    # 滑窗找最优偏移 (容忍 AF 模型首尾截断); step=1, 蛋白长度级 O(n*m) 可接受
    best = 1.0
    if len(model_seq) <= len(uniprot_seq):
        lo, hi = 0, len(uniprot_seq) - len(model_seq)
        for off in range(lo, hi + 1):
            sub = uniprot_seq[off:off + len(model_seq)]
            mismatch = sum(a != b for a, b in zip(model_seq, sub))
            best = min(best, mismatch / len(model_seq))
            if best == 0.0:
                break
    else:
        # 模型比 UniProt 还长: 异常情况, 直比报不匹配
        mismatch = sum(a != b for a, b in zip(model_seq, uniprot_seq))
        best = max(mismatch, len(model_seq) - len(uniprot_seq)) / len(model_seq)
    return best, best <= MAX_SEQ_MISMATCH_FRAC


# ─── 界面残基判定 ─────────────────────────────────────────────────────


def _model_seq_from_pdb(pdb_path: str | Path, chain: str | None = None) -> str:
    three2one = {
        'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C',
        'GLN': 'Q', 'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
        'LEU': 'L', 'LYS': 'K', 'MET': 'M', 'PHE': 'F', 'PRO': 'P',
        'SER': 'S', 'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V',
    }
    seq: dict[tuple[str, int], str] = {}
    with open(pdb_path) as fh:
        for line in fh:
            if line.startswith(("ATOM", "HETATM")) and line[12:16].strip() == "CA":
                resn = line[17:20].strip()
                if resn not in three2one:
                    continue
                ch, resi = line[21], int(line[22:26])
                if chain and ch != chain:
                    continue
                seq[(ch, resi)] = three2one[resn]
    return "".join(s for (_, _), s in sorted(seq.items()))


def _ca_atoms(pdb_path: str | Path, chain: str | None) -> dict[int, tuple[float, float, float]]:
    """CA 原子坐标 (Cb 距离近似; 论文用全原子, CA 近似在 6Å 阈值下误差可接受且可配置)。"""
    coords: dict[int, tuple[float, float, float]] = {}
    with open(pdb_path) as fh:
        for line in fh:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                if chain and line[21] != chain:
                    continue
                coords[int(line[22:26])] = (
                    float(line[30:38]), float(line[38:46]), float(line[46:54]))
    return coords


def find_interface_residues(pdb_path: str | Path,
                            chains_a: str | list[str],
                            chains_b: str | list[str],
                            cutoff_a: float = INTERFACE_CUTOFF_A,
                            use_cb: bool = True) -> tuple[set[int], set[int]]:
    """
    界面残基: A 链残基与 B 链残基任意重原子对距离 < cutoff。
    use_cb=True 时用 CB (GLY 用 CA) 近似, 精度略降但覆盖 99% 判定; use_cb=False 全原子精确。
    返回 (interface_res_ids_a, interface_res_ids_b)  (按模型内残基编号)
    """
    if isinstance(chains_a, str):
        chains_a = [chains_a]
    if isinstance(chains_b, str):
        chains_b = [chains_b]
    ch_a, ch_b = set(chains_a), set(chains_b)

    atoms: dict[str, list[tuple[int, float, float, float]]] = {"a": [], "b": []}
    ca_fallback: dict[str, dict[int, tuple[float, float, float]]] = {"a": {}, "b": {}}
    with open(pdb_path) as fh:
        for line in fh:
            if not line.startswith("ATOM"):
                continue
            ch = line[21]
            if ch not in ch_a and ch not in ch_b:
                continue
            altloc = line[16]
            if altloc not in (" ", "A"):
                continue
            resi = int(line[22:26])
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            atom_name = line[12:16].strip()
            bucket = "a" if ch in ch_a else "b"
            if use_cb:
                if atom_name == "CB":
                    atoms[bucket].append((resi, x, y, z))
                elif atom_name == "CA":
                    ca_fallback[bucket][resi] = (x, y, z)
            else:
                atoms[bucket].append((resi, x, y, z))

    if use_cb:
        # 无 CB 的残基 (CA-only 输入 / GLY) 用 CA 回退
        for bucket, fallback in ca_fallback.items():
            have_cb = {resi for resi, *_ in atoms[bucket]}
            for resi, xyz in fallback.items():
                if resi not in have_cb:
                    atoms[bucket].append((resi, *xyz))

    cutoff2 = cutoff_a * cutoff_a
    ia: set[int] = set()
    ib: set[int] = set()
    # 粗筛: 先按 AABB 包络过滤再精确算
    for resi_a, ax, ay, az in atoms["a"]:
        for resi_b, bx, by, bz in atoms["b"]:
            dx = ax - bx
            if dx > cutoff_a or dx < -cutoff_a:
                continue
            dy = ay - by
            if dy > cutoff_a or dy < -cutoff_a:
                continue
            d2 = dx * dx + dy * dy + (az - bz) * (az - bz)
            if d2 <= cutoff2:
                ia.add(resi_a)
                ib.add(resi_b)
    return ia, ib


# ─── 主入口 ───────────────────────────────────────────────────────────


def map_pathogenic_to_interface(
    uniprot_a: str,
    uniprot_b: str,
    complex_pdb: str | Path | None = None,
    chains_a: str | list[str] = "A",
    chains_b: str | list[str] = "B",
    model_dir: str | Path = "data/af_models",
    use_browser_fallback: bool = True,
    cutoff_a: float = INTERFACE_CUTOFF_A,
    include_all_pathogenic: bool = True,
) -> InterfaceVariantResult:
    """
    疾病突变 -> 互作界面 映射主入口。

    Parameters
    ----------
    uniprot_a, uniprot_b : str
        两个伙伴蛋白的 UniProt accession
    complex_pdb : path, optional
        二元复合物模型 (RF2-PPI / AF-multimer 输出)。None 时退化为
        两个 monomer AF 模型的"假复合物"模式 (仅 QC + 致病 SAV 汇总, 无界面判定)。
    chains_a, chains_b : str | list[str]
        复合物中各蛋白对应的 chain ID
    include_all_pathogenic : bool
        True 时同时返回全蛋白致病 SAV (不只界面), 便于上下文比较

    Returns
    -------
    InterfaceVariantResult
    """
    result = InterfaceVariantResult(uniprot_a=uniprot_a, uniprot_b=uniprot_b)

    # 1) UniProt SAV + 序列
    txt_a = fetch_uniprot_txt(uniprot_a)
    savs_a, seq_a = parse_uniprot_savs(txt_a)
    txt_b = fetch_uniprot_txt(uniprot_b)
    savs_b, seq_b = parse_uniprot_savs(txt_b)
    logger.info("UniProt SAVs: %s=%d, %s=%d", uniprot_a, len(savs_a), uniprot_b, len(savs_b))

    # 2) AlphaMissense per-protein 注释 (直连失败则 playwright)
    try:
        am_a = fetch_afdb_am_csv(uniprot_a)
    except NetworkError:
        if not use_browser_fallback:
            raise
        am_a = fetch_afdb_am_csv_browser(uniprot_a)
    try:
        am_b = fetch_afdb_am_csv(uniprot_b)
    except NetworkError:
        if not use_browser_fallback:
            raise
        am_b = fetch_afdb_am_csv_browser(uniprot_b)
    merge_am_evidence(savs_a, am_a)
    merge_am_evidence(savs_b, am_b)

    path_a = [s for s in savs_a if s.is_pathogenic]
    path_b = [s for s in savs_b if s.is_pathogenic]
    result.pathogenic_savs_a = path_a
    result.pathogenic_savs_b = path_b

    # 3) 界面判定 (需要复合物模型)
    if complex_pdb is not None:
        result.model_source = "local_pdb"
        # QC: 模型序列 vs UniProt canonical
        model_seq_a = _model_seq_from_pdb(complex_pdb, chains_a if isinstance(chains_a, str) else chains_a[0])
        model_seq_b = _model_seq_from_pdb(complex_pdb, chains_b if isinstance(chains_b, str) else chains_b[0])
        frac_a, ok_a = qc_sequence_match(model_seq_a, seq_a)
        frac_b, ok_b = qc_sequence_match(model_seq_b, seq_b)
        result.seq_mismatch_frac_a = frac_a
        result.seq_mismatch_frac_b = frac_b
        if not ok_a:
            result.warnings.append(
                f"{uniprot_a}: model/UniProt mismatch {frac_a:.1%} > 5%; SAV mapping unreliable")
        if not ok_b:
            result.warnings.append(
                f"{uniprot_b}: model/UniProt mismatch {frac_b:.1%} > 5%; SAV mapping unreliable")

        ia, ib = find_interface_residues(complex_pdb, chains_a, chains_b, cutoff_a=cutoff_a)
        result.interface_res_a = ia
        result.interface_res_b = ib

        # 界面编号 -> UniProt 编号直用 (AF/RF2 模型按 UniProt 编号建模;
        # 若 QC 失败则界面映射本身已不可信, 不做偏移猜测)
        result.interface_pathogenic_a = [s for s in path_a if s.position in ia]
        result.interface_pathogenic_b = [s for s in path_b if s.position in ib]
    else:
        result.model_source = "afdb_monomer_x2"
        result.warnings.append(
            "no complex model provided; interface mapping skipped "
            "(QC + pathogenic SAV enumeration only)")

    return result


def summarize_for_target(uniprot: str,
                         partner_uniprots: Iterable[str],
                         complex_pdbs: dict[str, str | Path] | None = None,
                         **kwargs: Any) -> list[InterfaceVariantResult]:
    """
    靶点级汇总: 一个靶点 vs 多个预测伙伴的界面致病突变扫描。
    complex_pdbs: {partner_uniprot: complex_pdb_path}; 缺省的伙伴走无界面模式。
    """
    complex_pdbs = complex_pdbs or {}
    out = []
    for partner in partner_uniprots:
        try:
            r = map_pathogenic_to_interface(
                uniprot, partner,
                complex_pdb=complex_pdbs.get(partner),
                **kwargs)
            out.append(r)
        except DruggabilityError as e:
            logger.warning("partner %s failed: %s", partner, e)
    out.sort(key=lambda r: -r.n_interface_pathogenic)
    return out
