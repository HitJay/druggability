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
│           ├── tractability.py   # Open Targets tractability (三级评估)
│           ├── ligandability.py  # ChEMBL 配体覆盖度 → ligandability 打分
│           ├── pocket.py         # fpocket 口袋检测 + AlphaFold 自动下载
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

# 查看综合报告
print(result["composite"]["overall_score"])        # 综合评分 0-1
print(result["tractability"]["small_molecule"])     # 小分子 tractability
print(result["ligandability"]["ligandability_score"]) # 配体能力打分
print(result["pocket_analysis"]["best_druggability_score"])  # 口袋质量
```

### 5. 跑测试

```bash
conda activate research
pip install pytest

# 搜索模块测试
python -m pytest tests/test_search.py -v

# 综合集成测试
python tests/test_integration.py
```

### 6. 打开 Notebook

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

### Druggability 三级评估流水线

```
输入: 靶点 (gene symbol / UniProt ID / Ensembl ID / PDB 文件)
                    │
                    ▼
┌───────────────────────────────────────────┐
│  Tier 1: 结构无关可药性扫描                  │
│  ├─ Open Targets tractability (SM/AB/PROTAC)│
│  └─ ChEMBL ligandability (已知配体覆盖度)     │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│  Tier 2: 结构口袋分析                       │
│  ├─ fpocket (Voronoi 镶嵌 + 几何打分)       │
│  └─ AlphaFold 自动下载 (无 PDB 时)          │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
        综合评估报告: 复合评分 + 置信度 + modality 推荐
```

## 📝 License

MIT