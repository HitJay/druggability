# ChEMBL 本地数据库使用指南

## 为什么需要本地数据库？

原始的 ChEMBL API 存在以下问题：
- 网络不稳定导致查询失败
- API 限流导致查询速度慢
- 大量查询时容易超时
- 服务维护性差，需要良好的本地数据库方案解决了这些问题。

## 快速开始

### 1. 安装依赖

```bash
# 使用 pip 安装
pip install -e .
```

### 2. 基本使用（自动模式）

```python
from litkit.druggability import assess_ligandability

# 使用 auto 模式，优先本地数据库，失败时自动回退到 API
result = assess_ligandability("EGFR", backend="auto")
print(f"Ligandability 分数: {result.ligandability_score}")
print(f"使用的后端: {result.backend_used}")
```

## 配置说明

### 查询后端选项

- `backend` 参数可以设置：
- `"auto"` - (默认) 优先本地数据库，失败时回退到 API
- `"local"` - 强制使用本地数据库
- `"api"` - 强制使用在线 API

### 镜像源配置

为了解决 ChEMBL 数据库下载慢的问题，可以：

#### 方法 1: 使用环境变量

```python
import os
os.environ["CHEMBL_MIRROR"] = "ebi_https"

from litkit.druggability import chembl_local

# 使用镜像源配置会自动生效
db = chembl_local.get_db()
```

#### 方法 2: 直接传入配置

```python
from litkit.druggability import chembl_local

# 使用预定义的镜像源
db = chembl_local.ChemblLocalDB(mirror="ebi_https")

# 或者直接设置全局镜像源
# db = chembl_local.ChemblLocalDB(mirror="你的镜像地址")
```

#### 预定义镜像源：
- `ebi` - 原始 EBI FTP 源
- `ebi_https` - EBI HTTPS 源

### 手动下载数据库

如果网络太慢，可以手动下载：

1. 从以下网址下载：https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/
2. 选择对应版本的 SQLite 文件（如 `chembl_36_sqlite.tar.gz）
3. 解压得到 `chembl_36.db` 文件
4. 配置使用：

```python
from litkit.druggability import chembl_local

db = chembl_local.ChemblLocalDB(
    db_path="/path/to/chembl_36.db"
)
```

## 高级使用

### 综合评估时使用本地数据库

```python
from litkit.druggability import assess_druggability

result = assess_druggability(
    query="EGFR",
    chembl_backend="local"  # 强制使用本地数据库
)
```

### 高级查询示例

```python
from litkit.druggability import chembl_local

# 创建数据库实例
db = chembl_local.get_db()

# 查询靶点
target_info = db.search_target("EGFR")
print(target_info

# 统计配体
n_ligands, top_compounds = db.count_ligands(target_info["target_chembl_id"])
print(f"已知配体: {n_ligands}")
```

## 常见问题

### Q: 数据库下载需要多长时间？

A: 取决于网络速度。ChEMBL 36 约 5GB，高速网络约 1-2 小时。

### Q: 数据库占用多少空间？

A: 解压后约 8-10GB。

### Q: API 和 如何避免多次下载？

A: 设置数据缓存在 `~/.data/chembl` 目录下，重复使用。

### Q: 可以使用多个版本的 ChEMBL？

A: 是的！

```python
db_35 = chembl_local.ChemblLocalDB(version="35")
db_36 = chembl_local.ChemblLocalDB(version="36")
```
