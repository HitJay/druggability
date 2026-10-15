# Druggability 未来开发路线图（2026-10 草案）

状态：草案。依据是对目录结构、`pyproject.toml`、README、`src/druggability/__init__.py::_compute_composite` 的阅读，尚未逐模块审查或运行；落地前每项需先做盘点确认。

原则：先清技术债，再建新能力；每个模块必须有独立单元测试；默认 human-in-the-loop，不 fire-and-forget；结论区分 FACT/OBS/MECH/HYP。

---

## 1. 技术债（Phase 0，最先做）

| ID | 问题 | 证据 | 动作 |
|----|------|------|------|
| D1 | 包重复且已分叉 | `src/bbbkit/druggability/` 与 `src/druggability/` 的 `__init__.py` 不同；`peptide/`、`cli.py`、`fetch.py`、`ner.py` 等只在后者；`pyproject` 两个 console script 都指向 `druggability.cli` | 以 `src/druggability` 为唯一源；`bbbkit` 缩为 re-export shim + DeprecationWarning；确认无引用后删除 |
| D2 | 仓库根目录杂物 | `bbb_prediction.py`、`test_paperclip_*.py`、`Boltz-2.ipynb`、`image copy.png`、各靶点 assessment 目录 | 归入 `examples/`、`tests/`、`reports/`；改名去空格 |
| D3 | `scripts/` 50+ 个按靶点一次性脚本，`data/gpr81_*` 内混有代码 | `run_gpr81_*`、`submit_ghsr_*`、`rebuild_csv_from_docked.py` 等 | 见 A3（campaign runner）；迁移前先归档到 `legacy/` |
| D4 | `__pycache__` 入库风险 | `src/*/__pycache__` 存在 | 确认 `.gitignore`，清理已跟踪文件 |
| D5 | ruff/mypy 已配置但未在 CI 强制 | `pyproject.toml` | 加 CI：ruff + mypy + pytest |

## 2. 算法（Phase 1，可与 Phase 0 后半并行）

### 2.1 综合评分修正（优先级最高）
- **缺失 vs 真 0**：`_compute_composite` 用 `score > 0` 判定维度存在，真实 0 分（如无配体）被当缺失并从加权平均中剔除，会抬高总分。改为 `None` 表示缺失，0 参与计算。
- **权重校准**：`DEFAULT_WEIGHTS` 为固定值。用批准药物靶点 vs 已知失败靶点建标注集，报告 AUROC + bootstrap CI；权重变更需过回归基线。
- **不确定度**：用缺失维度数与各维度来源质量输出区间，取代 high/medium/low 三档。
- 验收：新增单测覆盖「某维度=0」「某维度=None」「全缺失」；golden 靶点（EGFR、KRAS 等）分数基线入库。

### 2.2 口袋与结构
- 对比 fpocket 与 P2Rank、PocketMiner（隐性口袋）的召回，在已知配体口袋数据集上评估。
- GPCR 等柔性靶点：多构象 / MD 系综口袋评分，替代单张 AlphaFold 静态结构。

### 2.3 虚拟筛选与结合评估
- 分层：Vina 粗筛 → DrugCLIP 表征 → Boltz-2 亲和力 → MM-GBSA（仅过滤）→ FEP。
- 每个 campaign 的准入门槛：redocking RMSD、已知活性/decoy 富集因子（EF/AUC）、cross-pocket 负对照。
- 输出校准概率；可选 conformal prediction 给覆盖保证。

### 2.4 自由能
- 标准化 congeneric 相对 FEP：cycle closure、误差估计、重复种子；非同系物探索 ABFE。
- 与 GPR81/OXTR 现有 OpenFEP/OpenMM pilot 对齐为同一流程。

### 2.5 多维靶点证据
- 遗传学：pQTL/PheWAS（cis 判定 chr±1Mb）、gnomAD LOEUF 约束。
- 安全性：与 `3_safety` 共享靶点安全画像接口，避免两边各算一套。
- 新模态：分子胶、PROTAC、肽并入统一 modality 推荐器（现 `deep.recommend_modality`）。

### 2.6 肽模块
- 在 ESM-2 + 轻量 head 基线上对比 ESM-C / ProtT5。
- 加入化学修饰感知表示（脂化、非天然氨基酸）。
- 评估改用 scaffold / target-held-out split，防泄漏。

### 2.7 文献
- 检索 + GROBID + NER 之上加 RAG（paper-qa），结论带引用片段。
- 建小型 gold set 评估抽取准确率。

## 3. 架构（Phase 2）

### A1 数据契约
- pydantic 模型：`TargetProfile`、`PocketResult`、`LigandabilityResult` 等，带 schema 版本号，导出 JSON Schema；报告层与 agent 层只依赖模型。

### A2 Evidence Graph
- `Evidence(claim, source, retrieved_at, source_version, method, tier, raw_ref)`，tier ∈ {FACT, OBS, MECH, HYP}。
- 存 sqlite/duckdb，兼作缓存；报告从图渲染，每句可追溯。

### A3 Campaign runner + 可续跑 DAG
- YAML 描述 target、结构、配体集、阶段；单一 runner 执行；靶点只剩配置。
- step 以输入内容哈希做缓存，自带断点续传；每次 run 写 manifest（输入哈希、环境、种子、工具版本）。
- 将 GPR81 / GHSR / OXTR 脚本迁入，迁移后结果须与旧脚本输出做一致性对照。

### A4 Backend 抽象
- 统一 `local-venv / docker / BioLib / remote` 接口（现有 DECIMER、MolScribe、DrugCLIP、BioLib 各自为政），每个 backend 提供 mock 供单测。

### A5 Agent 层（最后做）
- 现有能力注册为带 JSON Schema 的 typed tools；planner/executor 产出 plan，**人工确认后**执行。
- 通过 MCP server 暴露同一批工具。
- 前置条件：A1、A2、A3 完成，否则 agent 只是在不稳定接口上叠层。

## 4. 工程质量
- `addopts = -m 'not network'` 导致外部数据源解析基本无覆盖：用 vcrpy / responses 录制回放。
- golden-run 回归：固定若干靶点评分，评分逻辑变更须显式更新基线。
- 每个新模块配独立 unit test（用户既定标准）。

## 5. 推荐顺序
D1 → D2/D4/D5 → 2.1 → A1 → A2 → A3（含 D3 迁移）→ A4 → 2.2–2.7 按需 → A5

## 6. 已知局限
- 本草案未运行任何代码，未核对各模块实际引用关系；D1 需先盘点 import 依赖再动手。
- 2.2 的工具对比、2.6 的新 embedding 是假设性改进（HYP），需基准实验验证后再采纳。
