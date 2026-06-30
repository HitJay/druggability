# BioLib 在 Druggability 工作流中的接入记录

> 日期: 2026-06-29  
> 工作区: `/home/QYJI/das/druggability`  
> 目的: 记录 NN 内部 BioLib 部署在本项目中的验证结果、成功功能、失败边界和复跑方法。

## 一句话结论

BioLib 平台本身已经可用，`pybiolib` 客户端、登录、作业提交和结果下载都验证通过。当前可稳定复用的功能是 `@nn/DCD/Boltz-2` 和 `@nn/SBTD/Target-Portal`；`@nn/DCD/Automated-Tractability` 已确认接口和输入格式，但远端 app 目前卡在 DataHub/EDH auth/network 依赖，能记录失败但还不能产出结果。

短期建议：**结构/亲和力走 BioLib Boltz-2，target evidence 走 BioLib Target-Portal；Automated-Tractability 先保留为可提交、可记录失败的候选，不纳入主评分。**

## 已接入文件

本次接入采用可选 enrichment 层，不改动现有 druggability composite score。

| 文件 | 用途 |
|---|---|
| `src/bbbkit/druggability/biolib_apps.py` | BioLib app wrapper，负责运行、保存输出、记录 job metadata/logs，并清理敏感 manifest 字段 |
| `scripts/run_biolib_druggability.py` | CSV target list 的 BioLib enrichment runner |
| `tests/test_biolib_apps.py` | 无网络单元测试，覆盖 trait 映射、gene list 写入、manifest token 清理 |
| `pyproject.toml` | 新增 optional dependency group: `biolib = ["pybiolib>=1.4"]` |

安装/环境要点：

```bash
source /home/QYJI/das/druggability/.venv/bin/activate
python -m pip install pybiolib
python -c "import biolib; biolib.login()"
```

注意：PyPI 上的 `biolib` 同名包不是这里需要的客户端。正确包是 `pybiolib`，导入模块名仍然是 `biolib`，并且应包含 `biolib.load()`。

## 功能验证矩阵

| 功能 | BioLib app / 路线 | 状态 | 说明 |
|---|---|---|---|
| BioLib Python client | `pybiolib` | 成功 | `biolib.__version__ = 1.4.184`，`biolib.load()` 可用 |
| BioLib 登录 | `biolib.login()` | 成功 | CLI/browser sign-in 后可提交 NN 内部 app job |
| Boltz-2 结构预测 | `@nn/DCD/Boltz-2:0.0.37` | 成功 | 单蛋白 smoke test 跑通，远端自动生成 MSA，输出 `.cif` 和 confidence JSON |
| Target biology evidence package | `@nn/SBTD/Target-Portal` | 成功 | ADORA1 + Obesity 跑通，生成完整 HTML 和 section JSON/plots |
| Automated target tractability | `@nn/DCD/Automated-Tractability` | 部分成功 | CLI/help 和输入格式确认，job 可提交，但远端 app 内部失败 |
| 本地 HPC Boltz | `boltz[cuda]==2.2.1` | 环境成功，权重下载失败 | CUDA/A100 可见，但 HuggingFace/Boltz model-gateway 被 web-use gateway 拦截 |

## Boltz-2 BioLib 部署

更完整的功能研究报告见：`output/2026-06-29/boltz_function_research/boltz2_function_research.md`。

BioLib 部署路径：

```python
import biolib

boltz = biolib.load('@nn/DCD/Boltz-2:0.0.37')
```

验证作业：

- Job: `8fce3169-5808-4a4e-8032-6a44d0d0748d`
- URL: `https://biolib.corp.novocorp.net/results/8fce3169-5808-4a4e-8032-6a44d0d0748d/`
- 输入: `output/2026-06-29/boltz_deployment/inputs/smoke_single_protein_biolib.yaml`
- 输出结构: `output/2026-06-29/boltz_deployment/runs/biolib_smoke/predictions/boltz/boltz_model_0.cif`
- 输出 confidence: `output/2026-06-29/boltz_deployment/runs/biolib_smoke/predictions/boltz/confidence_boltz_model_0.json`
- `confidence_score`: `0.5387585759162903`

关键踩坑：

- 本地 Boltz smoke YAML 里的 `msa: empty` 不能直接用于 BioLib 部署版。
- BioLib app 会把 `empty` 当作一个 MSA 文件名，因此报 `Could not find MSA empty for entry A`。
- 部署版 smoke input 应去掉 `msa` 字段，让远端自动生成 MSA。

本地 HPC 路线当前 blocker：

- `/home/QYJI/das/venvs/boltz-2` 已安装 `boltz==2.2.1`，Torch/CUDA 可见。
- 但首次推理需要下载 `/home/QYJI/das/models/boltz/mols.tar` 和 `boltz2_conf.ckpt`。
- HuggingFace 与 Boltz model-gateway 下载被 Novo web-use gateway 拦截，返回 Microsoft login HTML (`DEV_WEBUSE_DENIED`)。
- 当前建议优先使用 BioLib 部署版；本地 HPC 版等权重缓存文件手动补齐后再作为 backup。

## Target-Portal 接入

BioLib app：

```text
@nn/SBTD/Target-Portal
```

CLI 形式：

```bash
run.py -t <TARGET_BIOLOGY> -g "<GENE> - <ENSEMBL_ID>"
```

可选 target biology：

```text
Atherosclerosis, Kidney, HF, Obesity, T2D, Liver
```

本项目当前 trait 映射：

| 本项目 trait | Target-Portal biology |
|---|---|
| `T2D` | `T2D` |
| `WHRadjBMI` | `Obesity` |
| `BFPCT` | `Obesity` |
| `BMI` | `Obesity` |

验证作业：

- Target: `ADORA1 / ENSG00000163485`
- Biology: `Obesity`
- Job: `feb41c4e-ba0f-4df3-bd06-49c356591671`
- URL: `https://biolib.corp.novocorp.net/results/feb41c4e-ba0f-4df3-bd06-49c356591671/`
- 本地输出 HTML: `output/2026-06-29/biolib_druggability_probe/runs/target_portal_ADORA1/output.html`
- Summary: `output/2026-06-29/biolib_druggability_probe/biolib_summary.json`

成功生成的 section：

- Gene Annotation
- Genetics
- Target Tractability
- Gene/Protein Expression in General Population
- Gene/Protein Expression in Disease Context
- In-vitro Models
- Clinical Evidence
- Systems Biology

安全处理：

- Target-Portal 的 `manifest.json` 内含 `job_auth_token`。
- Wrapper 在写 summary 时会移除该字段，不写入 `biolib_summary.json`。

## Automated-Tractability 状态

BioLib app：

```text
@nn/DCD/Automated-Tractability
```

CLI help：

```text
usage: run.py [-h] [--genes GENES] [--outfile OUTFILE]
```

重要输入格式：

- `--genes` 需要的是基因列表文件路径，不是 `ADORA1,SSTR5` 或单个 symbol 字符串。
- 已验证单基因文件输入能被 app 读取并解析到 ADORA1。

当前失败模式：

- Job: `30845c48-180e-41ae-8a3b-9d49f671e8a4`
- URL: `https://biolib.corp.novocorp.net/results/30845c48-180e-41ae-8a3b-9d49f671e8a4/`
- 远端 app 先解析 gene 并连接到部分资源，但在 DataHub/EDH auth/network login 阶段报 `ConnectionResetError`。
- 随后 app 内部继续执行，触发 `UnboundLocalError: local variable 'mdf_buckets' referenced before assignment`。

当前结论：

- 接口已确认，可提交 job。
- Wrapper 已能捕获 `exit_code=1`、job URL、stdout/stderr log，不会拖垮整个流程。
- 但该 app 暂时不能作为生产可用 enrichment，需等远端 DataHub/EDH auth 或 app 内部错误修复。

## 复跑命令

运行 Target-Portal 单靶 smoke test：

```bash
/home/QYJI/das/druggability/.venv/bin/python scripts/run_biolib_druggability.py \
  --limit 1 \
  --apps target-portal
```

运行 Target-Portal + Automated-Tractability 组合探针：

```bash
/home/QYJI/das/druggability/.venv/bin/python scripts/run_biolib_druggability.py \
  --limit 1 \
  --apps target-portal,automated-tractability
```

运行 6 个靶点的 Target-Portal enrichment：

```bash
/home/QYJI/das/druggability/.venv/bin/python scripts/run_biolib_druggability.py \
  --apps target-portal
```

输出目录默认：

```text
output/<date>/biolib_druggability_probe/
├── biolib_summary.json
├── inputs/
├── logs/
├── runs/
└── summaries/
```

## 测试记录

本次接入后运行：

```bash
/home/QYJI/das/druggability/.venv/bin/python -m pytest \
  tests/test_biolib_apps.py tests/test_druggability.py -q
```

结果：

```text
30 passed, 3 deselected
```

仅有 pytest 对现有 `timeout` / `timeout_method` 配置的 warning，不影响功能。

## 后续候选 app

| App | 当前状态 | 可能用途 |
|---|---|---|
| `@nn/SBTD/Target-Portal` | 已验证成功 | target biology/evidence package |
| `@nn/DCD/Boltz-2` | 已验证成功 | structure + affinity prediction |
| `@nn/DCD/Automated-Tractability` | 已接入但远端失败 | target modality/tractability 自动注释 |
| `@nn/DCD/LiabilityLens` | 已确认 CLI help | protein/peptide sequence and structure liabilities |
| `@nn/Biophysics/ProteinBiophysics` | 已确认 CLI help | solubility, aggregation, structural and hydrodynamic properties |
| `@nn/DCD/SequenceLiability` | catalog 命中 | sequence liabilities |
| `@nn/SmallMolecules/AutoDock-Vina` | catalog 命中 | small-molecule docking baseline |
| `@nn/DCD/StructurePredictor` | catalog 命中 | standardized structure prediction/scoring workflow |
| `@nn/DCD/PepFuNN-properties` | catalog 命中 | peptide properties and developability |
| `@nn/MPIP/Peptide-albumin_binding` | catalog 命中 | peptide HSA binding / exposure-related signal |

## 建议的下一步

1. 将 Target-Portal 先作为 report supplement，而不是评分维度。
2. 跑完整 6 靶点 Target-Portal enrichment，保存 HTML 和 JSON section 供人工复核。
3. 等 Automated-Tractability 远端依赖修复后，再考虑把其输出映射到 modality-level tractability evidence。
4. 对 Boltz-2 建立一个更真实的 target-ligand affinity demo，例如 GPCR/tool compound 或已知 protein-ligand pair。
5. 本地 HPC Boltz 路线只需补齐 `mols.tar` 和 `boltz2_conf.ckpt` 后再验证；当前不应继续在 HPC 上反复触发下载。
