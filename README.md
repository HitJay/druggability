# 🔬 Druggability — 学术文献检索与靶点可药性评估工具包

基于 Python 的学术文献自动化检索、下载、解析、实体抽取及 **靶点可药性（druggability）评估** 流水线，面向药物研发研究。

## 📁 项目结构

```
druggability/
├── README.md               # 本文件
├── requirements.txt        # pip 依赖
├── .env.example            # API 配置模板 → 复制为 .env 填入你的信息
├── data/
│   ├── raw/                # 下载的 PDF / XML
│   ├── parsed/             # GROBID 解析结果 (JSON)
│   └── index/              # 向量库 / 缓存
├── docs/
│   ├── tools.md            # 学术检索工具大全 (50+ 工具整理)
│   └── deep-research/
│       └── target-druggability-assessment.md  # 靶点可药性深研报告
├── notebooks/
│   └── 00_quickstart.ipynb # 快速上手：搜索 → 下载 → 解析 → NER
├── src/
│   └── litkit/             # 核心工具包
│       ├── __init__.py
│       ├── search.py       # 统一检索 (OpenAlex/S2/PubMed/arXiv/CrossRef)
│       ├── fetch.py        # 下载 PDF / Europe PMC XML / Unpaywall
│       ├── parse.py        # PDF 解析 (PyMuPDF/pdfplumber/GROBID)
│       ├── ner.py          # 实体抽取 (PubTator3 API/正则/scispacy)
│       └── druggability/   # 🆕 靶点可药性评估核心模块
│           ├── __init__.py       # 统一入口 assess_druggability()
│           ├── tractability.py   # Open Targets 全量靶点画像 (TargetProfile)
│           │                     #   → tractability / expressions / knownDrugs
│           │                     #   → safetyLiabilities / chemicalProbes / TEP
│           │                     #   → subcellularLocations / pathways / GO
│           ├── ligandability.py  # ChEMBL 配体覆盖度 → ligandability 打分
│           ├── pocket.py         # fpocket 口袋检测 + AlphaFold 自动下载
│           ├── batch.py          # 批量靶点可药性评估（并发 + CSV/JSON 输出）
│           └── utils.py          # ID 转换 / 缓存 / 速率限制 / 异常定义
└── tests/
    ├── test_search.py              # 冒烟测试
    └── test_integration.py         # 综合集成测试
```

## 🚀 快速开始

### 1. 环境创建

```bash
# 已创建好 research 环境，直接激活
conda activate research

# 如需重建
mamba create -n research python=3.11 -y
conda activate research
pip install -r requirements.txt
```

### 2. 配置 API

```bash
cp .env.example .env
# 编辑 .env，至少填入邮箱（OpenAlex / NCBI 需要）
```

### 3. 跑一个搜索

```python
import sys; sys.path.insert(0, 'src')
from litkit.search import search

# OpenAlex 搜索
results = search("PROTAC druggability", source="openalex", limit=5)
for r in results:
    print(f"  {r['title']}")

# PubMed 搜索
results = search("KRAS druggability", source="pubmed", limit=5)
for r in results:
    print(f"  PMID:{r['pmid']} {r['title']}")

# 支持的数据源: openalex, s2, pubmed, arxiv, crossref
```

### 4. 评估一个靶点的可药性

```python
import sys; sys.path.insert(0, 'src')
from litkit.druggability import assess_druggability

# 只需基因符号，自动查询多个数据源
result = assess_druggability("EGFR")

# 结构分析需要 PDB 文件（或自动从 AlphaFold DB 下载）
result = assess_druggability("KRAS", structure_path="path/to/kras.pdb")

# 查看综合报告（五维评分）
print(result["composite"]["overall_score"])        # 综合评分 0-1
print(result["composite"]["contributing_scores"])  # 各维度分数

# ── 基础维度 ──
print(result["tractability"]["small_molecule"])     # 小分子 tractability
print(result["ligandability"]["ligandability_score"]) # 配体能力打分

# ── Open Targets 全量数据（新增）──
print(result["tractability"]["uniprot_ids"])         # UniProt IDs
print(result["tractability"]["target_class"])        # 靶点分类 (Kinase/GPCR...)
print(result["tractability"]["subcellular_locations"]) # 亚细胞定位 (UniProt/HPA)
print(result["tractability"]["expression_summary"])  # 组织表达谱 (HPA + GTEx)
print(result["tractability"]["n_known_drugs"])       # 已知药物数
print(result["tractability"]["approved_drugs"])      # 已批准药物列表
print(result["tractability"]["n_safety_events"])     # 安全性事件数
print(result["tractability"]["top_diseases"])        # 疾病关联 top 10
print(result["tractability"]["pathways"])            # 信号通路
```

### 5. 批量评估多个靶点

```python
import sys; sys.path.insert(0, 'src')
from litkit.druggability.batch import assess_druggability_batch

# 一次评估多个靶点（自动并发查询）
results = assess_druggability_batch(["EGFR", "BRAF", "KRAS"])

for r in results:
    if r.success:
        print(f"{r.query:20s} overall={r.overall_score:.3f} confidence={r.confidence}")
    else:
        print(f"{r.query:20s} ERROR: {r.error}")
```

或在终端使用 CLI：

```bash
# 逗号分隔
litkit batch --targets EGFR,BRAF,KRAS

# 从文件读取
litkit batch --file targets.txt

# 从 stdin 读取
echo -e "EGFR\nBRAF\nKRAS" | litkit batch --stdin

# 输出 JSON / CSV
litkit batch --targets EGFR,BRAF,KRAS --json
litkit batch --targets EGFR,BRAF,KRAS --csv > batch_results.csv
```

### 6. 跑测试

```bash
conda activate research
pip install pytest

# 搜索模块测试
python -m pytest tests/test_search.py -v

# druggability 模块测试（含批量评估）
python -m pytest tests/test_druggability.py tests/test_batch.py -v

# 综合集成测试
python tests/test_integration.py
```

### 7. 打开 Notebook

```bash
conda activate research
cd notebooks
jupyter lab
# 打开 00_quickstart.ipynb
```

## 📦 已安装的核心包

| 类别 | 包 |
|---|---|
| **检索** | pyalex, semanticscholar, arxiv, biopython, crossrefapi, habanero |
| **PDF 解析** | pymupdf, pdfplumber |
| **生医** | chembl-webresource-client, mygene |
| **可药性评估** | requests (Open Targets API), chembl-webresource-client (ligandability) |
| **工具** | jupyterlab, pandas, tqdm, python-dotenv, rich, requests |

## 🔌 可选扩展

```bash
# scispacy 生医 NER
pip install scispacy
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz

# paper-qa 论文问答 (需 LLM API key)
pip install paper-qa

# GROBID PDF 结构化解析 (Docker)
sudo docker run -d --name grobid -p 8070:8070 lfoppiano/grobid:0.8.0

# paperscraper 多源批量搜索+下载
pip install paperscraper

# PUResNet 深度学习口袋检测 (需 CUDA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
# PUResNet 仓库: https://github.com/krishnaswamylab/PUResNet

# fpocket 编译安装 (口袋检测核心)
# 官网: https://github.com/Discngine/fpocket
```

## 🔗 学术检索工具参考

详见 [docs/tools.md](docs/tools.md) — 整理了 50+ 工具，包括：

- AI 助手: Elicit, Consensus, SciSpace, Scite.ai, Undermind, ResearchRabbit
- 数据库: OpenAlex, Semantic Scholar, PubMed, arXiv, CrossRef
- Python 包: pyalex, semanticscholar, biopython, paper-qa
- API: OpenAlex API, S2 API, PubMed E-utilities, PubTator3
- Docker: GROBID, Ollama

## 📊 典型工作流

```
关键词 (e.g. "PROTAC druggability")
   ↓
search.py → OpenAlex / PubMed / S2 搜索
   ↓
fetch.py → 下载 OA PDF (Unpaywall) / Europe PMC XML
   ↓
parse.py → PyMuPDF 提取文本 / GROBID 结构化
   ↓
ner.py → PubTator3 实体标注 (Gene/Disease/Chemical)
   ↓                        ↓
ChEMBL API → 查靶点/化合物   druggability/ → 靶点可药性评估
   ↓                                   ↓
[可选] paper-qa → LLM 论文问答   tractability + ligandability + pocket
```

### Druggability 五维评估流水线

```
输入: 靶点 (gene symbol / UniProt ID / Ensembl ID / PDB 文件)
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│  Tier 1: Open Targets 全量靶点画像（单次 GraphQL）       │
│  ├─ Tractability (SM / AB / PROTAC 三 modality)         │
│  ├─ 蛋白信息: UniProt IDs / target class / 亚细胞定位    │
│  ├─ 组织表达谱: HPA + GTEx → RNA/protein + τ 特异性      │
│  ├─ 临床 precedence: knownDrugs / chemicalProbes / TEP  │
│  ├─ 安全性: safetyLiabilities → safety score             │
│  ├─ 疾病关联: top associated diseases + score            │
│  └─ 通路 / GO / Hallmarks                               │
├────────────────────────────────────────────────────────┤
│  Tier 1b: ChEMBL ligandability (已知配体覆盖度)          │
├────────────────────────────────────────────────────────┤
│  batch 并发聚合 → CSV/JSON 输出                          │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  Tier 2: 结构口袋分析（可选）                             │
│  ├─ fpocket (Voronoi 镶嵌 + 几何打分)                    │
│  └─ AlphaFold 自动下载 (无 PDB 时)                       │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
    综合评估报告: 五维加权评分 + 置信度 + modality 推荐
    ┌───────────────────────────────────────────┐
    │  维度           │ 权重  │ 数据来源         │
    │  tractability   │ 0.30  │ Open Targets     │
    │  ligandability  │ 0.25  │ ChEMBL           │
    │  structure      │ 0.20  │ fpocket          │
    │  clinical       │ 0.15  │ Open Targets     │
    │  safety         │ 0.10  │ Open Targets     │
    └───────────────────────────────────────────┘
```

## 📝 License

MIT