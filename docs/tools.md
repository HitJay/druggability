# 学术检索工具大全

> 整理于 2026-05-12，按场景分类。

---

## 一、AI 学术研究助手（Paperclip 同类）

| 工具 | 特点 | 适用场景 | 链接 |
|---|---|---|---|
| **Elicit** | 提问→自动综述、表格化抽取 | 系统性综述 | https://elicit.com |
| **Consensus** | 直接回答 Yes/No/Mixed | 快速验证科学结论 | https://consensus.app |
| **SciSpace** | Copilot 逐段解释论文+公式问答 | 精读外文论文 | https://typeset.io |
| **Scite.ai** | Smart Citations：支持/反驳/提及 | 判断学术影响 | https://scite.ai |
| **Undermind** | 多步深度搜索代理 | 小众/交叉领域 | https://undermind.ai |
| **ResearchRabbit** | 文献网络可视化 | 扩展阅读 | https://researchrabbit.ai |
| **Connected Papers** | 共引/共被引图谱 | 找"邻居"论文 | https://connectedpapers.com |
| **Inciteful** | 引文路径分析 | 文献网络 | https://inciteful.xyz |
| **Paperclip** | 国内团队 LLM 检索+管理 | 中文场景 | https://paperclip.gxl.ai |

---

## 二、传统学术数据库

| 工具 | 备注 |
|---|---|
| **Google Scholar** | 覆盖最广 |
| **Semantic Scholar** | AI 加持，免费 API |
| **PubMed / Europe PMC** | 生物医学必用 |
| **arXiv / bioRxiv / medRxiv / chemRxiv** | 预印本 |
| **OpenAlex** | 开源版 MAG，免费 API |
| **Web of Science / Scopus** | 机构订阅，SCI 计量 |
| **CORE / BASE / Lens.org** | 开放获取聚合 |
| **DBLP** | 计算机方向 |

---

## 三、可 pip install 的 Python 包

### 检索类
```bash
pip install pyalex              # OpenAlex 官方
pip install semanticscholar     # Semantic Scholar 官方
pip install arxiv               # arXiv 官方
pip install biopython           # Bio.Entrez → PubMed/PMC
pip install crossrefapi         # CrossRef
pip install habanero            # CrossRef (更活跃)
pip install paperscraper        # 一站式多源
```

### PDF 解析
```bash
pip install pymupdf             # 提取文本/图
pip install pdfplumber          # 表格场景更好
pip install grobid-client-python  # 配合 GROBID
pip install marker-pdf          # PDF→Markdown
```

### 生医 NLP
```bash
pip install scispacy            # 生医 NER
pip install chembl-webresource-client  # ChEMBL 数据
```

### RAG / 论文问答
```bash
pip install paper-qa            # 本地论文 RAG
```

---

## 四、免费 REST API

| API | 是否需 Key | 限制 |
|---|---|---|
| **OpenAlex** | 加邮箱即可 | 100k/天 |
| **Semantic Scholar** | 可选 | 100req/5min |
| **Europe PMC** | 无 | 全文检索 |
| **PubMed E-utilities** | 可选 NCBI key | 3→10 rps |
| **arXiv** | 无 | 1req/3s |
| **CrossRef** | 无 | 宽松 |
| **PubTator3** | 无 | 实体标注 |
| **Unpaywall** | 邮箱 | OA 检测 |
| **Open Targets** | 无 | GraphQL |
| **ChEMBL** | 无 | REST |

---

## 五、Docker 可部署服务

| 项目 | 命令 |
|---|---|
| **GROBID** | `sudo docker run -d -p 8070:8070 lfoppiano/grobid:0.8.0` |
| **paper-qa** | `pip install paper-qa` (本地 Python) |
| **Ollama** | `sudo docker run -d -p 11434:11434 ollama/ollama` |
| **Open WebUI** | 配合 Ollama 使用 |

---

## 六、Druggability 方向专用

### 知识库平台

| 工具/平台 | 用途 | 访问方式 | 特色 |
|---|---|---|---|
| **Open Targets Platform** | 靶点-疾病关联，三级 tractability 评估 | GraphQL API；完全开源 | 整合遗传学、化学探针、功能基因组学；SM/AB/PROTAC 三级打分 |
| **canSAR** | 多维 druggability 打分 + 3D 配体信息 | REST API | 含蛋白-配体 3D 结构匹配；癌症研究方向 |
| **TTD (Therapeutic Target Database)** | 临床阶段分级靶点注释 | 网站查询 | druggability 分级：approved / clinical / preclinical / literature |
| **ChEMBL** | 化合物-靶点活性数据库 | REST API (`chembl-webresource-client`) | 2.4M 化合物，18K+ 靶点；最全生物活性数据 |
| **DGIdb 4.0** | 药物-基因相互作用 | API + 网站 | 含 druggable genome 分类，文献挖掘证据 |
| **DrugBank** | 药物本体（需许可） | 网站/API | FDA 批准药物最全 |

### 口袋检测 & Druggability 打分工具

| 工具 | 类型 | 核心原理 | 推荐场景 |
|---|---|---|---|
| **fpocket** | 开源 CLI | Voronoi 镶嵌 + α-sphere → 口袋打分 | 批量口袋检测，黄金标准（1000+ 引用） |
| **DoGSiteScorer** | Web | 高斯差分滤波 → 子口袋分解 → 打分 | 交互式可视化（Proteins.plus 平台） |
| **PockDrug** | Web | 31 描述符逻辑回归 → druggability 打分 | 专为 druggability 打分优化 |
| **PUResNet** | DL (PyTorch) | 深度残差网络 + 3D 网格输入 | 最先进 AI 口袋检测精度（GPU 加速） |
| **pyKVFinder** | Python 包 | 3D 网格扫描 → 空腔检测 | Python 原生，易集成（Bioinformatics 2021） |
| **DrugEBIlity** | Web | 贝叶斯模型，仅需序列 | 无需 PDB 结构即可预测 druggability |
| **PocketDruggability** | 开源 Python | 13 个口袋描述符 → 结合亲和力预测 | 训练于 PDBbind |

### 靶点识别与 NER

| 工具 | 用途 | 链接 |
|---|---|---|
| **PubTator3** | 基因/疾病/化合物/细胞系/突变实体标注 | https://www.ncbi.nlm.nih.gov/research/pubtator3/ |
| **scispacy** | 生医 NER Python 库 | https://github.com/allenai/scispacy |
| **mygene** | 基因 ID 转换 (symbol/UniProt/Ensembl) | https://pypi.org/project/mygene/ |

### 本项目已集成的 druggability 模块

> 2026-06-29 更新：NN 内部 BioLib app 已作为可选 enrichment 层接入，详见 [BioLib 内部部署与 Druggability 接入记录](biolib-druggability-integration.md)。已验证 `@nn/SBTD/Target-Portal` 和 `@nn/DCD/Boltz-2`；`@nn/DCD/Automated-Tractability` 已接入但当前远端 app 在 DataHub/EDH 登录处失败。

```bash
# 这些已在 bbbkit/druggability/ 中实现
# 详见 README.md 或 docs/design-opentargets-expansion.md
├── src/bbbkit/druggability/
│   ├── __init__.py       # assess_druggability() 统一入口（五维评分）
│   ├── tractability.py   # Open Targets 全量靶点画像 (TargetProfile)
│   ├── ligandability.py  # ChEMBL ligandability
│   ├── pocket.py         # fpocket + AlphaFold
│   ├── batch.py          # 批量评估（并发 + CSV/JSON 输出）
│   └── utils.py          # ID 转换/缓存/异常
```

### Open Targets 全量数据集成（通过 GraphQL 单次查询）

通过 Open Targets Platform GraphQL API，一次查询即可获取以下维度的数据：

| 数据维度 | OT GraphQL 字段 | 上游来源 | 用途 |
|---|---|---|---|
| **Tractability** | `tractability { label modality }` | OT 自有 | SM/AB/PROTAC 三级评估 |
| **蛋白 ID & 分类** | `proteinIds`, `targetClass` | UniProt | 靶点分类 (Kinase/GPCR/…) |
| **亚细胞定位** | `subcellularLocations` | UniProt / HPA | 抗体/PROTAC 可达性判断 |
| **组织表达谱** | `expressions { tissue rna protein }` | HPA + GTEx | 表达特异性 (τ 值) + 脱靶风险 |
| **已知药物** | `knownDrugs { count rows { drug phase } }` | ChEMBL / DailyMed | 临床 precedence 打分 |
| **化学探针** | `chemicalProbes { id isHighQuality }` | SGC / Chemical Probes Portal | 工具化合物质量 |
| **TEP** | `tep { name uri }` | SGC | Target Enabling Package |
| **安全性** | `safetyLiabilities { event datasource }` | 多源汇总 | safety score → 参与综合评分 |
| **疾病关联** | `associatedDiseases { count rows { score disease } }` | OT 遗传学/文献 | 靶点-疾病证据强度 |
| **通路 / GO** | `pathways`, `geneOntology` | Reactome / GO | 生物学通路上下文 |
| **Cancer Hallmarks** | `hallmarks { cancerHallmarks { label impact } }` | 文献挖掘 | 肿瘤靶点评估 |
| **功能描述** | `functionDescriptions` | UniProt | 蛋白功能摘要 |

> **优势：** 无需分别调用 UniProt REST / HPA API / GTEx API，Open Targets 已将这些上游数据整合到单一 GraphQL endpoint，大幅降低网络请求数和维护成本。

### 五维综合评分体系

| 维度 | 权重 | 数据来源 | 打分逻辑 |
|---|---|---|---|
| **tractability** | 0.30 | Open Targets tractability | SM/AB/PROTAC 三 modality 取最高分 |
| **ligandability** | 0.25 | ChEMBL | 已知活性配体数 → 分段映射 |
| **structure** | 0.20 | fpocket | 最佳口袋 druggability score |
| **clinical** | 0.15 | Open Targets knownDrugs / probes / TEP | Phase 4→1.0, Phase 3→0.85, ... |
| **safety** | 0.10 | Open Targets safetyLiabilities | `max(1.0 - 0.2×n_events, 0.2)` |

详见 [设计文档](design-opentargets-expansion.md)。
