"""
fpocket Python Wrapper — 基于结构的口袋检测与 druggability 打分

封装 fpocket（Voronoi 镶嵌 + α-sphere 聚类）对 PDB 结构进行
结合口袋检测，并解析 druggability 评分。

支持：
- 本地 PDB 文件输入
- UniProt ID 自动下载 AlphaFold 结构
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from .utils import (
    FpocketNotFoundError,
    FpocketTimeoutError,
    InvalidStructureError,
    DruggabilityError,
)

logger = logging.getLogger(__name__)

# ─── 常量 ────────────────────────────────────────────────────────────

# AlphaFold DB 下载模板
ALPHAFOLD_URL_TEMPLATE = (
    "https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
)

# fpocket 可执行文件路径（项目内 fallback）
# 注意：不要在模块加载时调用 shutil.which，便于测试时 mock；
# 实际查找逻辑放在 _check_fpocket() 中。
FPOCKET_FALLBACK_PATH = Path(__file__).resolve().parents[3] / "tools" / "fpocket"

# fpocket 超时（秒）
FPOCKET_TIMEOUT = 120

# Druggability 分数分级
DRUGGABILITY_GRADES: list[tuple[float, str]] = [
    (0.8, "Highly druggable"),
    (0.5, "Druggable"),
    (0.3, "Marginal"),
    (0.0, "Poor"),
]


@dataclass
class PocketInfo:
    """单个口袋的分析结果"""

    rank: int = 0
    score: float = 0.0
    druggability_score: float = 0.0
    num_alpha_spheres: int = 0
    total_sasa: float = 0.0
    polar_sasa: float = 0.0
    apolar_sasa: float = 0.0
    volume: float = 0.0
    mean_alpha_sphere_radius: float = 0.0
    druggability_grade: str = "Unknown"

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "score": self.score,
            "druggability_score": self.druggability_score,
            "num_alpha_spheres": self.num_alpha_spheres,
            "total_sasa": self.total_sasa,
            "polar_sasa": self.polar_sasa,
            "apolar_sasa": self.apolar_sasa,
            "volume": self.volume,
            "mean_alpha_sphere_radius": self.mean_alpha_sphere_radius,
            "druggability_grade": self.druggability_grade,
        }


@dataclass
class PocketAnalysisResult:
    """完整口袋分析结果"""

    num_pockets: int = 0
    total_volume: float = 0.0
    best_druggability_score: float = 0.0
    deepest_pocket_volume: float = 0.0
    pockets: list[PocketInfo] = field(default_factory=list)
    input_structure: str = ""
    raw_output_dir: str | None = None

    def to_dict(self) -> dict:
        return {
            "num_pockets": self.num_pockets,
            "total_volume": self.total_volume,
            "best_druggability_score": self.best_druggability_score,
            "deepest_pocket_volume": self.deepest_pocket_volume,
            "pockets": [p.to_dict() for p in self.pockets],
            "input_structure": self.input_structure,
            "raw_output_dir": self.raw_output_dir,
        }


def _download_alphafold_structure(uniprot_id: str, output_dir: str) -> str:
    """
    从 AlphaFold DB 下载蛋白结构文件。

    Parameters
    ----------
    uniprot_id : str
        UniProt accession，如 "P00533"
    output_dir : str
        下载目录

    Returns
    -------
    str
        下载的 PDB 文件路径

    Raises
    ------
    DruggabilityError
        下载失败
    """
    url = ALPHAFOLD_URL_TEMPLATE.format(uniprot_id=uniprot_id)
    output_path = os.path.join(output_dir, f"AF-{uniprot_id}-F1-model_v4.pdb")

    try:
        logger.info("Downloading AlphaFold structure from: %s", url)
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(resp.content)

        # 验证文件是否为有效的 PDB（以 ATOM 开头）
        content = resp.content.decode("utf-8", errors="ignore")
        if "ATOM" not in content and "HETATM" not in content:
            raise DruggabilityError(
                f"Downloaded file does not appear to be a valid PDB structure "
                f"(missing ATOM records) for UniProt: {uniprot_id}"
            )

        logger.info("Structure saved to: %s", output_path)
        return output_path

    except requests.exceptions.HTTPError as e:
        raise DruggabilityError(
            f"Failed to download AlphaFold structure for {uniprot_id}: HTTP {e}"
        )
    except requests.exceptions.RequestException as e:
        raise DruggabilityError(
            f"Network error downloading AlphaFold structure for {uniprot_id}: {e}"
        )


def _check_fpocket() -> str:
    """
    定位 fpocket 可执行文件。

    查找顺序：
    1. PATH 环境变量中的 ``fpocket``
    2. 项目 ``tools/fpocket`` 兜底路径

    Raises
    ------
    FpocketNotFoundError
        两个位置都未找到可执行的 fpocket。
    """
    # 1) PATH 优先
    fpocket_path = shutil.which("fpocket")
    if fpocket_path:
        return fpocket_path

    # 2) 项目内 fallback
    if FPOCKET_FALLBACK_PATH.is_file() and os.access(
        FPOCKET_FALLBACK_PATH, os.X_OK
    ):
        return str(FPOCKET_FALLBACK_PATH)

    raise FpocketNotFoundError(
        "fpocket not found. Please install fpocket and place the binary at "
        f"{FPOCKET_FALLBACK_PATH}, or ensure 'fpocket' is in your PATH.\n"
        "  Download: https://github.com/Discngine/fpocket/releases"
    )


def _run_fpocket(pdb_path: str, output_dir: str) -> dict:
    """
    运行 fpocket 并解析输出。

    Parameters
    ----------
    pdb_path : str
        PDB 文件路径
    output_dir : str
        输出目录

    Returns
    -------
    dict
        解析后的口袋结果字典

    Raises
    ------
    FpocketTimeoutError
        执行超时
    InvalidStructureError
        PDB 结构无效
    """
    fpocket_path = _check_fpocket()
    logger.info("Running fpocket on: %s", pdb_path)

    try:
        result = subprocess.run(
            [fpocket_path, "-f", pdb_path],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=FPOCKET_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise FpocketTimeoutError(
            f"fpocket timed out after {FPOCKET_TIMEOUT}s on: {pdb_path}"
        )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or "Unknown error"
        raise InvalidStructureError(
            f"fpocket failed on {pdb_path}: {error_msg}"
        )

    # fpocket 输出在 pdb_path 同目录的 {basename}_out/ 中
    basename = os.path.splitext(os.path.basename(pdb_path))[0]
    out_dir = os.path.join(output_dir, f"{basename}_out")
    info_file = os.path.join(out_dir, f"{basename}_info.txt")

    if not os.path.isfile(info_file):
        raise InvalidStructureError(
            f"fpocket did not produce expected output file: {info_file}"
        )

    # 解析 info 文件
    pockets = _parse_info_file(info_file)

    # 汇总统计
    num_pockets = len(pockets)
    total_volume = sum(p.volume for p in pockets)
    best_druggability = max(
        (p.druggability_score for p in pockets), default=0.0
    )
    deepest_volume = max(
        (p.volume for p in pockets), default=0.0
    )

    return {
        "num_pockets": num_pockets,
        "total_volume": total_volume,
        "best_druggability_score": best_druggability,
        "deepest_pocket_volume": deepest_volume,
        "pockets": pockets,
        "out_dir": out_dir,
    }


def _parse_info_file(info_path: str) -> list[PocketInfo]:
    """
    解析 fpocket 的 *_info.txt 输出文件。
    """
    with open(info_path, "r") as f:
        content = f.read()

    pockets: list[PocketInfo] = []
    # 每个 Pocket N: 块用空行分隔
    pocket_blocks = re.split(r"\n\s*\n", content)

    for block in pocket_blocks:
        if not block.startswith("Pocket "):
            continue

        info = PocketInfo()
        lines = block.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Pocket 1 :  → rank
            m = re.match(r"Pocket\s+(\d+)\s*:", line)
            if m:
                info.rank = int(m.group(1))
                continue

            # Score : 0.456
            m = re.match(r"Score\s*:\s*([-\d.]+)", line)
            if m:
                info.score = float(m.group(1))
                continue

            # Druggability Score : 0.78
            m = re.match(r"Druggability\s+[Ss]core\s*:\s*([-\d.]+)", line)
            if m:
                info.druggability_score = float(m.group(1))
                continue

            # Number of Alpha Spheres : 42
            m = re.match(r"Number\s+of\s+Alpha\s+Spheres\s*:\s*(\d+)", line)
            if m:
                info.num_alpha_spheres = int(m.group(1))
                continue

            # Total SASA : 210.5
            m = re.match(r"Total\s+SASA\s*:\s*([-\d.]+)", line)
            if m:
                info.total_sasa = float(m.group(1))
                continue

            # Polar SASA : 45.2
            m = re.match(r"Polar\s+SASA\s*:\s*([-\d.]+)", line)
            if m:
                info.polar_sasa = float(m.group(1))
                continue

            # Apolar SASA : 165.3
            m = re.match(r"Apolar\s+SASA\s*:\s*([-\d.]+)", line)
            if m:
                info.apolar_sasa = float(m.group(1))
                continue

            # Volume : 850.3
            m = re.match(r"Volume\s*:\s*([-\d.]+)", line)
            if m:
                info.volume = float(m.group(1))
                continue

            # Mean alpha-sphere radius : 3.5
            m = re.match(
                r"Mean\s+alpha[- ]sphere\s+radius\s*:\s*([-\d.]+)", line
            )
            if m:
                info.mean_alpha_sphere_radius = float(m.group(1))
                continue

        # 根据 druggability_score 打分
        info.druggability_grade = _grade_druggability(info.druggability_score)
        pockets.append(info)

    return pockets


def _grade_druggability(score: float) -> str:
    """根据 druggability score 返回可读分级。"""
    for threshold, grade in DRUGGABILITY_GRADES:
        if score >= threshold:
            return grade
    return "Unknown"


def detect_pockets(
    structure_path: str,
    auto_download: bool = True,
    keep_output: bool = False,
) -> PocketAnalysisResult:
    """
    对蛋白结构进行口袋检测和 druggability 评估。

    Parameters
    ----------
    structure_path : str
        PDB 文件路径，或 UniProt ID（如 "P00533"）
    auto_download : bool
        如果 structure_path 是 UniProt ID，是否自动从 AlphaFold DB 下载。
        设为 False 且传入 UniProt ID 时会报错。
    keep_output : bool
        是否保留 fpocket 输出目录（默认删除临时文件）。

    Returns
    -------
    PocketAnalysisResult

    Raises
    ------
    FpocketNotFoundError
        fpocket 未安装
    InvalidStructureError
        结构文件无效
    FpocketTimeoutError
        fpocket 运行超时
    """
    # 创建临时工作目录
    work_dir = tempfile.mkdtemp(prefix="pocket_")

    try:
        # Step 1: 准备 PDB 文件
        if structure_path.endswith(".pdb") or structure_path.endswith(".ent"):
            if not os.path.isfile(structure_path):
                raise InvalidStructureError(
                    f"PDB file not found: {structure_path}"
                )
            pdb_path = structure_path
            input_label = structure_path
        else:
            # 当作 UniProt ID 处理
            if not auto_download:
                raise InvalidStructureError(
                    f"'{structure_path}' is not a PDB file path and "
                    f"auto_download is False"
                )
            uniprot_id = structure_path
            pdb_path = _download_alphafold_structure(uniprot_id, work_dir)
            input_label = f"UniProt:{uniprot_id} (AlphaFold)"

        # Step 2: 运行 fpocket
        raw_result = _run_fpocket(pdb_path, work_dir)

        # Step 3: 构建结果
        result = PocketAnalysisResult(
            num_pockets=raw_result["num_pockets"],
            total_volume=raw_result["total_volume"],
            best_druggability_score=raw_result["best_druggability_score"],
            deepest_pocket_volume=raw_result["deepest_pocket_volume"],
            pockets=raw_result["pockets"],
            input_structure=input_label,
        )

        if keep_output:
            result.raw_output_dir = raw_result["out_dir"]

        return result

    finally:
        # 清理临时文件
        if not keep_output:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception as e:
                logger.warning("Failed to clean up temp directory: %s", e)