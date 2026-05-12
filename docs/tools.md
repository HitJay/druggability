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

- **Open Targets Platform** — 靶点-疾病关联 + GraphQL API
- **ChEMBL** — 化合物/活性数据
- **DrugBank** — 药物本体（需许可）
- **PubTator3** — 基因/疾病/化合物实体标注
- **BenchSci** — AI 辅助找抗体/试剂文献
- **Causaly** — 生医知识图谱检索
