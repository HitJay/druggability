# Paperclip 集成指南

## 概述

Paperclip 是一个强大的生物医学论文搜索工具，现已集成到 druggability 项目中。

**文献来源**:
- PubMed Central (PMC)
- bioRxiv / medRxiv / arXiv
- FDA 数据库
- 其他学术资源

## 安装

### 1. WSL 环境设置

Paperclip 需要在 WSL（Windows Subsystem for Linux）中运行：

```bash
# Windows PowerShell
wsl --install -d Ubuntu

# 进入 WSL
wsl -d Ubuntu
```

### 2. 安装 Paperclip

在 WSL 中运行：

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
```

### 3. 首次登录

```bash
~/.local/bin/paperclip login
# 或
paperclip login  # 如果 ~/.local/bin 在 PATH 中
```

## 使用方法

### Python API 使用

#### 方法 1：直接调用 `search_paperclip()`

```python
import sys
sys.path.insert(0, 'src')
from litkit.search import search_paperclip

# 基础搜索
results = search_paperclip("PROTAC druggability", limit=10)

for paper in results:
    print(paper['title'])
    print(f"  作者: {paper['authors']}")
    print(f"  URL: {paper['url']}")
    print(f"  摘要: {paper['abstract'][:100]}...")
    print()
```

#### 方法 2：使用统一接口 `search()`

```python
from litkit import search

# 指定 paperclip 作为数据源
results = search("protein design", source="paperclip", limit=5)

for paper in results:
    print(f"- {paper['title']}")
```

#### 方法 3：指定具体数据库

```python
# 搜索 PubMed Central
results = search_paperclip("druggability", source_db="pmc", limit=20)

# 搜索 bioRxiv/medRxiv
results = search_paperclip("novel biomarker", source_db="biorxiv")

# 搜索摘要库（覆盖范围更广）
results = search_paperclip("KRAS inhibitor", source_db="abstracts")
```

### 返回数据格式

```python
{
    "title": "Learning the language of protein-protein interactions",
    "authors": "Varun Ullanat, Bowen Jing, Samuel Sledzieski, Bonnie Berger",
    "paper_id": "bio_d900ea5f6fb2",
    "source": "bioRxiv",
    "publication_date": "2025-03-09",
    "url": "https://doi.org/10.1101/2025.03.09.642188",
    "abstract": "MINT, a protein language model, was developed to represent sets of interacting proteins...",
    "database": "paperclip"
}
```

### 命令行使用（直接在 WSL 中）

```bash
# 基础搜索
paperclip search "PROTAC druggability"

# 指定数据源
paperclip search -s pmc "protein design"

# 创建和管理论文集合
paperclip init my-project "Drug discovery research"
paperclip checkout my-project
paperclip search "target validation"

# 查看已保存的结果
paperclip results
```

## 常见问题

### Q: 在 Windows 中运行时出现 "paperclip not found"

**A**: 这是正常的。paperclip 安装在 WSL 中，Python 代码会自动通过 WSL 调用它。

```bash
# 验证 WSL 中的安装
wsl -d Ubuntu
~/.local/bin/paperclip --version
```

### Q: 搜索返回结果为空

**可能原因**:
1. 需要首先登录: `paperclip login`
2. 网络连接问题
3. 搜索关键词太具体

**解决方法**:
```bash
# 在 WSL 中测试搜索
wsl -d Ubuntu
paperclip search "protein"  # 使用简单关键词测试
```

### Q: 如何保存搜索结果到本地？

```python
import json
from litkit import search_paperclip

results = search_paperclip("druggability", limit=100)

# 保存为 JSON
with open('papers.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# 保存为 CSV
import csv
with open('papers.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
    writer.writeheader()
    writer.writerows(results)
```

### Q: 如何在 WSL 中查看已保存的论文？

```bash
paperclip cat bio_d900ea5f6fb2
```

## 配合其他数据源使用

```python
from litkit import search

# 搜索多个来源
sources = ["openalex", "paperclip", "pubmed"]

for source in sources:
    try:
        results = search("PROTAC", source=source, limit=5)
        print(f"\n{source.upper()}: {len(results)} 篇论文")
    except Exception as e:
        print(f"{source.upper()}: {e}")
```

## 系统要求

- **Windows 版本**: Windows 10/11 with WSL2
- **Python**: 3.10+
- **WSL2**: Ubuntu 或其他 Linux 发行版
- **网络**: 需要网络连接以访问论文数据库

## 项目集成

### 在项目中的文件

- `src/litkit/search.py` - 包含 `search_paperclip()` 和文本解析器
- `src/litkit/__init__.py` - 导出 `search_paperclip` 公开 API
- `example_paperclip_usage.py` - 使用示例
- `test_paperclip_integration.py` - 集成测试

### 调用链

```
Python (Windows) 
  ↓
search() / search_paperclip()
  ↓
subprocess.run() + wsl -d Ubuntu
  ↓
~/.local/bin/paperclip search
  ↓
Paper results (parsed as structured text)
  ↓
dict[] with standardized format
```

## 参考资源

- [Paperclip 官方网站](https://paperclip.gxl.ai/)
- [Paperclip CLI 文档](https://paperclip.gxl.ai/docs)
- [Druggability 项目](../README.md)

## 更新日志

- **2025-05-18**: 初步集成 paperclip，支持文本输出解析
- 支持通过 WSL 在 Windows 中调用
- 支持指定数据库（pmc, abstracts, fda 等）
