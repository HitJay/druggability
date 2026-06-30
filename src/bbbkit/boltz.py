"""
bbbkit.boltz — Boltz-2 云端结构/亲和力预测（基于 BioLib）

把 Boltz-2（结构生物学基础模型，支持复合物结构预测 + 小分子结合亲和力预测）
通过 BioLib 部署到云端 GPU 执行，本地无需 GPU / 权重，仅用 ``pybiolib`` SDK 提交
YAML 输入、轮询任务、下载 .cif / affinity JSON 结果。

参考:
    - Notebook: ``Boltz-2.ipynb``（本仓库根目录）
    - Boltz 文档: https://github.com/jwohlwend/boltz/blob/main/docs/prediction.md
    - BioLib SDK: https://github.com/biolib/biolib-python

可选依赖（``pip install 'bbbkit[biolib]'`` 即 ``pybiolib>=1.4``）。
缺失时本模块仍可 import，但调用预测函数会抛 ``RuntimeError``。

典型用法:
    from bbbkit.boltz import predict_affinity, get_affinity, save_results

    job = predict_affinity(
        protein_sequence="MVTPEGNVSL...",
        ligand_smiles="N[C@@H](Cc1ccc(O)cc1)C(=O)O",
        binder="B",
    )
    print(get_affinity(job))           # {'affinity_pred_value': ...}
    save_results(job, "boltz-output")  # .cif 落到 boltz-output/predictions/boltz/

环境变量:
    BIOLIB_API_URL     BioLib API 端点（企业私有实例），如未设置用公网默认
    BOLTZ_APP_URI      Boltz-2 app URI，默认 @nn/DCD/Boltz-2:0.0.37
    BIOLIB_API_TOKEN   可选：直接用 token 认证（免交互 login）
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅用于类型提示，运行时不导入
    from biolib._result.result import Result

# ── 默认配置 ────────────────────────────────────────────────────────
DEFAULT_APP_URI = "@nn/DCD/Boltz-2:0.0.37"
AFFINITY_JSON_PATH = "predictions/boltz/affinity_boltz.json"

# Boltz-2 run() 默认参数（与 Notebook 一致）
DEFAULT_RECYCLING_STEPS = "3"
DEFAULT_DIFFUSION_SAMPLES = "1"
DEFAULT_SAMPLING_STEPS = "200"


# ── 优雅降级：biolib 是否可用 ───────────────────────────────────────
def _check_biolib() -> None:
    """确保 pybiolib 已安装，否则给出清晰报错。"""
    try:
        import biolib  # noqa: F401
    except ImportError as exc:  # pragma: no cover - 环境依赖
        raise RuntimeError(
            "pybiolib 未安装。请运行: pip install 'bbbkit[biolib]'  (即 pybiolib>=1.4)"
        ) from exc


def _get_biolib():
    """惰性返回 biolib 模块，并按环境变量配置端点。"""
    _check_biolib()
    import biolib

    # 企业私有实例端点（如 https://biolib.corp.novocorp.net ）
    api_url = os.environ.get("BIOLIB_API_URL")
    if api_url:
        biolib.set_api_base_url(api_url)

    # 可选：直接用 token 认证，免交互 login
    token = os.environ.get("BIOLIB_API_TOKEN")
    if token:
        biolib.set_api_token(token)

    return biolib


# ── 认证 ───────────────────────────────────────────────────────────
def login() -> None:
    """交互式登录 BioLib（已在 ~/.biolib 缓存凭据时直接返回）。

    若设置了 ``BIOLIB_API_TOKEN`` 环境变量，则用 token 认证，无需交互。
    """
    biolib = _get_biolib()
    if os.environ.get("BIOLIB_API_TOKEN"):
        # set_api_token 已在 _get_biolib 中调用
        return
    biolib.login()


def set_endpoint(api_url: str) -> None:
    """显式设置 BioLib API 端点（企业私有实例）。

    例: set_endpoint("https://biolib.corp.novocorp.net")
    """
    biolib = _get_biolib()
    biolib.set_api_base_url(api_url)


# ── 加载 app ───────────────────────────────────────────────────────
def load_boltz(app_uri: str | None = None):
    """加载 Boltz-2 BioLib app。

    Args:
        app_uri: app URI，默认取 ``BOLTZ_APP_URI`` 环境变量或 ``@nn/DCD/Boltz-2:0.0.37``。

    Returns:
        biolib BioLibApp 实例（调用其 .run(**kwargs) 提交云端任务）。
    """
    biolib = _get_biolib()
    uri = app_uri or os.environ.get("BOLTZ_APP_URI", DEFAULT_APP_URI)
    return biolib.load(uri)


# ── 通用预测 ───────────────────────────────────────────────────────
def predict(
    input: str | Path,
    *,
    recycling_steps: str = DEFAULT_RECYCLING_STEPS,
    diffusion_samples: str = DEFAULT_DIFFUSION_SAMPLES,
    sampling_steps: str = DEFAULT_SAMPLING_STEPS,
    templates: str | Path | None = None,
    biolib_files: list[str | Path] | None = None,
    app_uri: str | None = None,
) -> "Result":
    """提交一个 Boltz-2 云端预测任务并阻塞等待完成。

    Args:
        input:          Boltz YAML 输入文件路径（参考 docs/prediction.md）。
        recycling_steps: 大复合物可调大，默认 '3'。
        diffusion_samples: 扩散采样数，默认 '1'。
        sampling_steps:   扩散步数，默认 '200'。
        templates:      模板目录路径（YAML 中引用 templates/ 时传入）。
        biolib_files:   额外随任务上传的文件（如自定义 MSA .a3m）。
        app_uri:        覆盖默认 Boltz-2 app URI。

    Returns:
        biolib Result 对象，可用 save_results() / get_affinity() 进一步处理。
    """
    boltz = load_boltz(app_uri)

    kwargs: dict[str, Any] = {
        "input": str(input),
        "recycling_steps": str(recycling_steps),
        "diffusion_samples": str(diffusion_samples),
        "sampling_steps": str(sampling_steps),
    }
    if templates is not None:
        kwargs["templates"] = str(templates)
    if biolib_files:
        kwargs["biolib_files"] = [str(f) for f in biolib_files]

    return boltz.run(**kwargs)


# ── 便捷：结构预测 ─────────────────────────────────────────────────
def predict_structure(
    *,
    protein_sequence: str,
    protein_id: str | list[str] = "A",
    ligands: list[dict] | None = None,
    templates_dir: str | Path | None = None,
    recycling_steps: str = DEFAULT_RECYCLING_STEPS,
    diffusion_samples: str = DEFAULT_DIFFUSION_SAMPLES,
    sampling_steps: str = DEFAULT_SAMPLING_STEPS,
    yaml_path: str | Path = "input.yaml",
    output_dir: str | Path = "boltz-output",
    app_uri: str | None = None,
) -> "Result":
    """端到端结构预测：构建 YAML → 提交云端 → 保存 .cif 结果。

    Args:
        protein_sequence: 蛋白氨基酸序列（单字母大写）。
        protein_id:       链 ID，默认 'A'；多链用列表。
        ligands:          配体列表，每项形如
                          ``{'id': ['C','D'], 'ccd': 'SAH'}`` 或
                          ``{'id': 'E', 'smiles': 'N[C@@H](...)'}``。
        templates_dir:    模板目录（YAML 中引用 templates/*.cif 时传入）。
        yaml_path:        写出的 YAML 路径（默认 input.yaml）。
        output_dir:       结果保存目录，.cif 落到 ``<output_dir>/predictions/boltz/``。
        app_uri:          覆盖默认 Boltz-2 app URI。

    Returns:
        biolib Result 对象。
    """
    yaml_path = Path(yaml_path)
    build_structure_yaml(
        protein_sequence=protein_sequence,
        protein_id=protein_id,
        ligands=ligands,
        yaml_path=yaml_path,
    )
    job = predict(
        yaml_path,
        recycling_steps=recycling_steps,
        diffusion_samples=diffusion_samples,
        sampling_steps=sampling_steps,
        templates=templates_dir,
        app_uri=app_uri,
    )
    save_results(job, output_dir)
    return job


# ── 便捷：亲和力预测 ───────────────────────────────────────────────
def predict_affinity(
    *,
    protein_sequence: str,
    ligand_smiles: str,
    protein_id: str = "A",
    ligand_id: str = "B",
    binder: str | None = None,
    recycling_steps: str = DEFAULT_RECYCLING_STEPS,
    diffusion_samples: str = DEFAULT_DIFFUSION_SAMPLES,
    sampling_steps: str = DEFAULT_SAMPLING_STEPS,
    yaml_path: str | Path = "affinity.yaml",
    output_dir: str | Path = "boltz-output",
    app_uri: str | None = None,
) -> "Result":
    """端到端亲和力预测：构建 YAML → 提交云端 → 返回 Result（含 affinity JSON）。

    Args:
        protein_sequence: 蛋白氨基酸序列。
        ligand_smiles:    小分子配体 SMILES。
        protein_id:       蛋白链 ID，默认 'A'。
        ligand_id:        配体链 ID，默认 'B'。
        binder:           亲和力预测的 binder 链 ID，默认取 ligand_id。
        yaml_path:        写出的 YAML 路径。
        output_dir:       .cif 结果保存目录。
        app_uri:          覆盖默认 Boltz-2 app URI。

    Returns:
        biolib Result 对象，可用 get_affinity(job) 取亲和力数值。
    """
    yaml_path = Path(yaml_path)
    build_affinity_yaml(
        protein_sequence=protein_sequence,
        ligand_smiles=ligand_smiles,
        protein_id=protein_id,
        ligand_id=ligand_id,
        binder=binder or ligand_id,
        yaml_path=yaml_path,
    )
    job = predict(
        yaml_path,
        recycling_steps=recycling_steps,
        diffusion_samples=diffusion_samples,
        sampling_steps=sampling_steps,
        app_uri=app_uri,
    )
    save_results(job, output_dir)
    return job


# ── 结果处理 ───────────────────────────────────────────────────────
def save_results(job: "Result", output_dir: str | Path = "boltz-output") -> Path:
    """把云端任务的全部输出文件下载到本地目录。

    .cif 结构文件会落在 ``<output_dir>/predictions/boltz/`` 下。

    Returns:
        输出目录 Path。
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    job.save_files(str(out))
    return out


def get_affinity(job: "Result") -> dict:
    """从已完成的 affinity 任务中解析亲和力预测结果。

    返回字典形如::

        {
          'affinity_pred_value': 2.608,            # 预测 pKd
          'affinity_probability_binary': 0.403,     # 二分类置信度
          'affinity_pred_value1': 2.793, 'affinity_probability_binary1': 0.371,
          'affinity_pred_value2': 2.424, 'affinity_probability_binary2': 0.435,
        }

    若任务未含 affinity 输出则抛 KeyError。
    """
    affinity_file = job.get_output_file(AFFINITY_JSON_PATH)
    with affinity_file.get_file_handle() as fh:
        return json.load(fh)


def list_output_files(job: "Result") -> list[str]:
    """列出云端任务的所有输出文件相对路径。"""
    return list(job.list_output_files())


# ── YAML 构建器 ────────────────────────────────────────────────────
def _as_id_list(id_: str | list[str]) -> list[str]:
    if isinstance(id_, str):
        return [id_]
    return list(id_)


def build_structure_yaml(
    *,
    protein_sequence: str,
    protein_id: str | list[str] = "A",
    ligands: list[dict] | None = None,
    constraints: list[dict] | None = None,
    templates: list[dict] | None = None,
    yaml_path: str | Path = "input.yaml",
) -> Path:
    """构建 Boltz-2 结构预测 YAML 并写出。

    Args:
        protein_sequence: 蛋白序列。
        protein_id:       链 ID。
        ligands:          配体列表，每项 ``{'id': ..., 'ccd': ...}`` 或 ``{'id': ..., 'smiles': ...}``。
        constraints:      约束列表（contact/pocket/bond），原样写入 YAML。
        templates:        模板列表，每项 ``{'cif': ..., 'chain_id': ...}``。
        yaml_path:        输出 YAML 路径。

    Returns:
        写出的 YAML Path。
    """
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("需要 PyYAML: pip install pyyaml") from exc

    doc: dict[str, Any] = {
        "version": 1,
        "sequences": [
            {"protein": {"id": _as_id_list(protein_id), "sequence": protein_sequence}},
        ],
    }
    for lig in ligands or []:
        doc["sequences"].append({"ligand": dict(lig)})
    if constraints:
        doc["constraints"] = list(constraints)
    if templates:
        doc["templates"] = list(templates)

    yaml_path = Path(yaml_path)
    yaml_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return yaml_path


def build_affinity_yaml(
    *,
    protein_sequence: str,
    ligand_smiles: str,
    protein_id: str = "A",
    ligand_id: str = "B",
    binder: str | None = None,
    yaml_path: str | Path = "affinity.yaml",
) -> Path:
    """构建 Boltz-2 亲和力预测 YAML 并写出。

    Args:
        protein_sequence: 蛋白序列。
        ligand_smiles:    配体 SMILES。
        protein_id:       蛋白链 ID。
        ligand_id:        配体链 ID。
        binder:           亲和力 binder 链 ID，默认取 ligand_id。
        yaml_path:        输出 YAML 路径。

    Returns:
        写出的 YAML Path。
    """
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("需要 PyYAML: pip install pyyaml") from exc

    doc = {
        "version": 1,
        "sequences": [
            {"protein": {"id": protein_id, "sequence": protein_sequence}},
            {"ligand": {"id": ligand_id, "smiles": ligand_smiles}},
        ],
        "properties": [{"affinity": {"binder": binder or ligand_id}}],
    }
    yaml_path = Path(yaml_path)
    yaml_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return yaml_path


__all__ = [
    "DEFAULT_APP_URI",
    "login",
    "set_endpoint",
    "load_boltz",
    "predict",
    "predict_structure",
    "predict_affinity",
    "save_results",
    "get_affinity",
    "list_output_files",
    "build_structure_yaml",
    "build_affinity_yaml",
]
