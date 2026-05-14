"""
ChEMBL Local Database — 本地 SQLite 数据库查询模块

利用 chembl_downloader 下载和管理 ChEMBL 数据库，提供稳定的本地查询功能。
支持配置自定义镜像源和数据库路径。
"""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

from .utils import TargetNotFoundError

logger = logging.getLogger(__name__)

# 活性标准 type 列表（与原 API 保持一致）
ACTIVITY_TYPES = ["IC50", "EC50", "Ki", "Kd", "Potency", "ED50"]

# 支持的镜像源配置
MIRRORS = {
    "ebi": "ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases",
    "ebi_https": "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases",
    # 可添加其他镜像源，例如国内镜像
}

# 环境变量配置
ENV_MIRROR = "CHEMBL_MIRROR"
ENV_DB_PATH = "CHEMBL_DB_PATH"
ENV_DATA_DIR = "CHEMBL_DATA_DIR"


class ChemblLocalDB:
    """
    ChEMBL 本地数据库管理器
    """

    def __init__(
        self,
        version: str = "36",
        db_path: Optional[str | Path] = None,
        data_dir: Optional[str | Path] = None,
        mirror: Optional[str] = None,
    ):
        """
        初始化 ChEMBL 本地数据库管理器

        Args:
            version: ChEMBL 版本号，默认 "36"
            db_path: 数据库文件路径，如果为 None 则使用 chembl_downloader 默认路径
            data_dir: 数据存储目录（仅当 db_path 为 None 时有效）
            mirror: 镜像源名称（如 "ebi"、"ebi_https"），或自定义 URL（不含协议）
        """
        self.version = version
        self.db_path: Optional[Path] = Path(db_path) if db_path else None
        self.data_dir: Optional[Path] = Path(data_dir) if data_dir else None
        self.mirror = mirror
        self._conn: Optional[sqlite3.Connection] = None

        # 从环境变量加载默认值
        if self.db_path is None and os.environ.get(ENV_DB_PATH):
            self.db_path = Path(os.environ[ENV_DB_PATH])
        if self.data_dir is None and os.environ.get(ENV_DATA_DIR):
            self.data_dir = Path(os.environ[ENV_DATA_DIR])
        if self.mirror is None and os.environ.get(ENV_MIRROR):
            self.mirror = os.environ[ENV_MIRROR]

    def _ensure_db(self) -> Path:
        """
        确保数据库已下载，返回数据库路径
        """
        if self.db_path and self.db_path.exists():
            return self.db_path

        # 如果设置了 db_path 但文件不存在，或者没有设置，我们需要下载
        # 先尝试使用 chembl_downloader，如有必要则覆盖其镜像源
        if self.mirror:
            self._patch_chembl_downloader_mirror()

        try:
            import chembl_downloader
        except ImportError:
            raise ImportError(
                "chembl-downloader is required. Install with: "
                "pip install chembl-downloader"
            )

        if self.data_dir:
            os.environ.setdefault("CHEMBL_DATA_DIR", str(self.data_dir))

        if self.db_path is None:
            self.db_path = Path(chembl_downloader.download_extract_sqlite(version=self.version))
        else:
            if not self.db_path.exists():
                # 下载到临时位置，然后移动到指定路径
                downloaded = chembl_downloader.download_extract_sqlite(version=self.version)
                # 将下载的文件复制到目标位置
                import shutil
                shutil.copy(downloaded, self.db_path)

        return self.db_path

    def _patch_chembl_downloader_mirror(self):
        """临时修改 chembl_downloader 的镜像源"""
        try:
            import chembl_downloader.api
            # 保存原始值
            original_host = getattr(chembl_downloader.api, "_CHEMBL_HOST", None)
            
            # 设置新镜像源
            if self.mirror in MIRRORS:
                new_host = MIRRORS[self.mirror]
            else:
                new_host = self.mirror  # 直接使用自定义 URL
            
            chembl_downloader.api._CHEMBL_HOST = new_host
            logger.info(f"ChEMBL 镜像源已设置为: {new_host}")
            
            # 保存原始值，以便可能的恢复（虽然不需要）
            setattr(self, "_original_chembl_host", original_host)
        except Exception as e:
            logger.warning(f"设置镜像源失败: {e}，将使用默认源")

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器
        """
        db_path = self._ensure_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def search_target(
        self,
        query: str,
        organism: str = "Homo sapiens",
    ) -> Optional[dict[str, Any]]:
        """
        搜索 ChEMBL 靶点，返回最佳匹配

        Returns:
            dict with keys: target_chembl_id, pref_name, organism
        """
        with self.connect() as conn:
            cursor = conn.cursor()

            # Step 1: 精确搜索（基因别名）
            cursor.execute(
                """
                SELECT t.target_chembl_id, t.pref_name, t.organism, t.target_type
                FROM target_dictionary t
                JOIN target_synonyms ts ON t.tid = ts.tid
                WHERE ts.component_synonym LIKE ?
                """,
                (f"%{query}%",),
            )
            results = cursor.fetchall()

            # Step 2: 按人源和靶点类型过滤
            candidates = []
            for row in results:
                if (
                    row["organism"] == organism
                    and row["target_type"] in ("SINGLE PROTEIN", "PROTEIN COMPLEX", "PROTEIN FAMILY")
                ):
                    candidates.insert(0, dict(row))
                elif row["organism"] == organism:
                    candidates.append(dict(row))
                else:
                    candidates.append(dict(row))

            # Step 3: 如果没有匹配，尝试直接在 target_dictionary 中搜索
            if not candidates:
                cursor.execute(
                    """
                    SELECT target_chembl_id, pref_name, organism, target_type
                    FROM target_dictionary
                    WHERE pref_name LIKE ? OR target_chembl_id LIKE ?
                    """,
                    (f"%{query}%", f"%{query}%"),
                )
                results = cursor.fetchall()
                for row in results:
                    if (
                        row["organism"] == organism
                        and row["target_type"] in ("SINGLE PROTEIN", "PROTEIN COMPLEX", "PROTEIN FAMILY")
                    ):
                        candidates.insert(0, dict(row))
                    elif row["organism"] == organism:
                        candidates.append(dict(row))
                    else:
                        candidates.append(dict(row))

            if not candidates:
                return None

            best = candidates[0]
            return {
                "target_chembl_id": str(best["target_chembl_id"]),
                "pref_name": str(best["pref_name"]),
                "organism": str(best["organism"]),
            }

    def count_ligands(
        self,
        target_chembl_id: str,
    ) -> tuple[int, list[str]]:
        """
        统计靶点的已知配体数量并返回代表性化合物

        Returns:
            (n_unique_molecules, top_chembl_ids)
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ACTIVITY_TYPES)
            cursor.execute(
                f"""
                SELECT DISTINCT a.molecule_chembl_id
                FROM activities a
                WHERE a.target_chembl_id = ?
                  AND a.standard_type IN ({placeholders})
                  AND a.standard_value IS NOT NULL
                ORDER BY a.standard_value
                """,
                (target_chembl_id, *ACTIVITY_TYPES),
            )
            rows = cursor.fetchall()

        all_molecules = {str(row["molecule_chembl_id"]) for row in rows}
        top_molecules = sorted(all_molecules)[:5]
        return len(all_molecules), top_molecules

    def get_strongest_activity(
        self,
        target_chembl_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        获取靶点的最强活性数据（最低 IC50/EC50/Ki/Kd 值）
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ACTIVITY_TYPES)
            cursor.execute(
                f"""
                SELECT a.standard_type, a.standard_value, a.standard_units
                FROM activities a
                WHERE a.target_chembl_id = ?
                  AND a.standard_type IN ({placeholders})
                  AND a.standard_value IS NOT NULL
                ORDER BY a.standard_value
                LIMIT 1
                """,
                (target_chembl_id, *ACTIVITY_TYPES),
            )
            row = cursor.fetchone()

        if row and row["standard_value"] is not None:
            return {
                "type": str(row["standard_type"]),
                "value": float(row["standard_value"]),
                "unit": str(row["standard_units"]),
            }
        return None

    def count_approved_drugs(
        self,
        target_chembl_id: str,
    ) -> int:
        """
        统计靶点对应的已批准药物数量
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(DISTINCT dm.molecule_chembl_id) as count
                FROM drug_mechanism dm
                JOIN molecule_dictionary md ON dm.molecule_chembl_id = md.molecule_chembl_id
                WHERE dm.target_chembl_id = ?
                  AND md.max_phase = 4
                """,
                (target_chembl_id,),
            )
            row = cursor.fetchone()
            return int(row["count"]) if row else 0


# 全局实例，方便使用
_default_db: Optional[ChemblLocalDB] = None


def get_db(
    version: str = "36",
    db_path: Optional[str | Path] = None,
    data_dir: Optional[str | Path] = None,
    mirror: Optional[str] = None,
    reset: bool = False,
) -> ChemblLocalDB:
    """
    获取默认的 ChEMBL 本地数据库实例

    Args:
        version: ChEMBL 版本号
        db_path: 数据库文件路径
        data_dir: 数据存储目录
        mirror: 镜像源名称（如 "ebi"、"ebi_https"）
        reset: 是否重置全局实例

    Returns:
        ChemblLocalDB 实例
    """
    global _default_db
    if _default_db is None or reset:
        _default_db = ChemblLocalDB(
            version=version, db_path=db_path, data_dir=data_dir, mirror=mirror
        )
    return _default_db


def set_default_mirror(mirror: str):
    """
    全局设置默认的 ChEMBL 镜像源

    Args:
        mirror: 镜像源名称（如 "ebi"、"ebi_https"）或自定义 URL
    """
    os.environ[ENV_MIRROR] = mirror
    logger.info(f"全局 ChEMBL 镜像源已设置为: {mirror}")


# 便捷函数，无需显式创建 db 实例
def search_target(
    query: str,
    organism: str = "Homo sapiens",
    db: Optional[ChemblLocalDB] = None,
) -> Optional[dict[str, Any]]:
    """便捷函数：搜索靶点"""
    if db is None:
        db = get_db()
    return db.search_target(query, organism=organism)


def count_ligands(
    target_chembl_id: str,
    db: Optional[ChemblLocalDB] = None,
) -> tuple[int, list[str]]:
    """便捷函数：统计配体"""
    if db is None:
        db = get_db()
    return db.count_ligands(target_chembl_id)


def get_strongest_activity(
    target_chembl_id: str,
    db: Optional[ChemblLocalDB] = None,
) -> Optional[dict[str, Any]]:
    """便捷函数：获取最强活性"""
    if db is None:
        db = get_db()
    return db.get_strongest_activity(target_chembl_id)


def count_approved_drugs(
    target_chembl_id: str,
    db: Optional[ChemblLocalDB] = None,
) -> int:
    """便捷函数：统计已批准药物"""
    if db is None:
        db = get_db()
    return db.count_approved_drugs(target_chembl_id)
