# Open Targets 全量数据扩展 — 设计文档

> **日期:** 2026-05-13
> **状态:** Approved → 待实现
> **关联:** `src/bbbkit/druggability/tractability.py`

---

## 1. 背景与动机

当前 `druggability` 模块的 Open Targets 集成只查了 `tractability { label modality }` 这一小块，而 Open Targets Platform 的 GraphQL API 实际上已经整合了来自 **UniProt、HPA (Human Protein Atlas)、GTEx** 等多个上游数据源的丰富靶点信息。

**核心洞察：** 不需要分别对接 UniProt / HPA / GTEx 三个独立 API，Open Targets 的单次 GraphQL 查询即可覆盖全部所需数据维度。

### 现有 vs 目标

| 维度 | 现状 | 目标 |
|---|---|---|
| Tractability (SM/AB/PROTAC) | ✅ 已有 | 保留 |
| 蛋白基本信息 (UniProt IDs, target class) | ❌ | ✅ 从 OT `proteinIds` / `targetClass` 获取 |
| 亚细胞定位 (UniProt/HPA 来源) | ❌ | ✅ 从 OT `subcellularLocations` 获取 |
| 组织表达谱 (HPA + GTEx 来源) | ❌ | ✅ 从 OT `expressions` 获取 RNA/protein 表达 |
| 已知药物 / 化学探针 / TEP | ❌ | ✅ 从 OT `knownDrugs` / `chemicalProbes` / `tep` 获取 |
| 安全性信号 | ❌ | ✅ 从 OT `safetyLiabilities` 获取 |
| 疾病关联 | ❌ | ✅ 从 OT `associatedDiseases` 获取 top associations |
| 通路 / GO / Hallmarks | ❌ | ✅ 从 OT `pathways` / `geneOntology` / `hallmarks` 获取 |
| 功能描述 | ❌ | ✅ 从 OT `functionDescriptions` 获取 |

---

## 2. 技术方案

### 2.1 GraphQL Query 扩展

将现有的 `TRACTABILITY_QUERY` 扩展为 `TARGET_QUERY`：

```graphql
query TargetQuery($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    # ── 基本信息 ──
    id
    approvedSymbol
    approvedName
    biotype
    functionDescriptions
    proteinIds      { id source }
    synonyms        { label source }
    genomicLocation { chromosome start end strand }

    # ── 1. Tractability（已有，扩展 value 字段）──
    tractability { label modality value }

    # ── 2. UniProt 来源（OT 已整合）──
    subcellularLocations { location source termSL }
    targetClass          { id label level }

    # ── 3. HPA + GTEx 表达（OT 已整合）──
    expressions {
      tissue  { id label anatomicalSystems organs }
      rna     { value zscore level unit }
      protein { level reliability cellType { name reliability level } }
    }

    # ── 4. 临床 precedence ──
    knownDrugs {
      count
      uniqueDrugs
      uniqueDiseases
      rows {
        drug  { id name maximumClinicalTrialPhase }
        phase
        status
      }
    }
    chemicalProbes {
      id
      isHighQuality
      mechanismOfAction
      control
      drugId
    }
    tep { name uri description therapeuticArea }

    # ── 5. 安全性 ──
    safetyLiabilities {
      event
      eventId
      effects       { direction dosing }
      biosamples    { tissueLabel cellLabel }
      datasource
      literature
      url
    }

    # ── 6. 疾病关联 (top 10) ──
    associatedDiseases(page: { index: 0, size: 10 }) {
      count
      rows {
        score
        disease { id name therapeuticAreas { id name } }
      }
    }

    # ── 7. 通路 / GO / Hallmarks ──
    pathways     { pathwayId pathway topLevelTerm }
    geneOntology { term { id name } aspect evidence }
    hallmarks {
      attributes      { reference description name }
      cancerHallmarks { description impact label pmid }
    }
  }
}
```

> **注意：** 以上字段名基于 Open Targets Platform v24.x schema。实施前需通过 `__schema` introspection 或 [OT GraphQL Playground](https://api.platform.opentargets.org/api/v4/graphql/browser) 校对字段存在性和拼写，因为 OT 小版本更新可能调整字段名。

### 2.2 数据类重构

将 `TractabilityResult` 升级为 `TargetProfile`（保留别名向后兼容）：

```python
@dataclass
class TargetProfile:
    """Open Targets 靶点全量画像"""

    # ── 现有字段（不动）──
    ensembl_id: str = ""
    symbol: str = ""
    name: str = ""
    biotype: str = ""
    small_molecule: ModalityTractability = ...
    antibody: ModalityTractability = ...
    protac: ModalityTractability = ...

    # ── 新增：蛋白信息（UniProt 来源）──
    uniprot_ids: list[str] = field(default_factory=list)
    target_class: list[str] = field(default_factory=list)
    subcellular_locations: list[str] = field(default_factory=list)
    function_description: str = ""

    # ── 新增：表达谱（HPA + GTEx 来源）──
    expression_summary: list[dict] = field(default_factory=list)
    # 每项: {"tissue": str, "rna_value": float, "rna_level": str,
    #         "protein_level": str}
    tissue_specificity_score: float = 0.0  # τ 值，本地计算

    # ── 新增：临床 precedence ──
    n_known_drugs: int = 0
    max_clinical_phase: int = 0
    approved_drugs: list[str] = field(default_factory=list)
    n_chemical_probes: int = 0
    has_high_quality_probe: bool = False
    has_tep: bool = False

    # ── 新增：安全性 ──
    n_safety_events: int = 0
    safety_events: list[dict] = field(default_factory=list)
    # 每项: {"event": str, "datasource": str}

    # ── 新增：疾病关联 ──
    n_associated_diseases: int = 0
    top_diseases: list[dict] = field(default_factory=list)
    # 每项: {"name": str, "score": float, "therapeutic_area": str}
    max_disease_score: float = 0.0

    # ── 新增：通路 ──
    pathways: list[str] = field(default_factory=list)

    # ── 新增：Hallmarks ──
    cancer_hallmarks: list[dict] = field(default_factory=list)

    # ── 原始 ──
    raw: dict | None = None

# 向后兼容
TractabilityResult = TargetProfile
```

### 2.3 Composite Score 扩展

新增 2 个评分维度（数据全部来自同一个 OT 返回）：

```python
DEFAULT_WEIGHTS = {
    "tractability":   0.30,   # SM/AB/PROTAC 三 modality 最高分
    "ligandability":  0.25,   # ChEMBL 配体覆盖度
    "structure":      0.20,   # fpocket 口袋检测
    "clinical":       0.15,   # 新：known drugs / probes / TEP
    "safety":         0.10,   # 新：safety liabilities → 逆向打分
}
```

#### clinical 维度打分规则

```python
def _score_clinical(profile: TargetProfile) -> float:
    """
    临床 precedence 打分（0-1）。
    - 有已批准药物 (max_phase >= 4) → 1.0
    - 有 Phase 3 → 0.85
    - 有 Phase 2 → 0.7
    - 有 Phase 1 → 0.55
    - 有高质量化学探针 → 0.5
    - 有 TEP → 0.4
    - 都没有 → 0.0
    """
```

#### safety 维度打分规则

```python
def _score_safety(profile: TargetProfile) -> float:
    """
    安全性打分（0-1）：越安全越高分。
    - 0 个 safety events → 1.0（完美）
    - 1 个 → 0.8
    - 2 个 → 0.6
    - 3 个 → 0.4
    - 4+ 个 → 0.2（下限）

    公式: max(1.0 - 0.2 * n_events, 0.2)
    """
```

safety 参与综合决策，作为加权维度影响 `overall_score`。

### 2.4 τ (tau) 组织特异性指数

从 OT `expressions` 中的 RNA z-score 或 TPM 值计算 Yanai τ：

```
τ = Σ(1 - x̂_i) / (N - 1)
```

其中 `x̂_i = x_i / max(x)`，N 为组织数。τ ∈ [0, 1]：
- τ → 1：组织高度特异性（好 → 脱靶风险低）
- τ → 0：广泛表达（差 → 脱靶风险高）

此值存入 `tissue_specificity_score`，可作为 safety 维度的参考信号（当前版本暂不自动纳入 composite，但展示在输出中供人工判断）。

---

## 3. 文件改动清单

| 文件 | 改动类型 | 描述 |
|---|---|---|
| `src/bbbkit/druggability/tractability.py` | **重构** | 扩 GraphQL query → `TARGET_QUERY`；`TractabilityResult` → `TargetProfile`；解析所有新字段；保留 `TractabilityResult` 别名 |
| `src/bbbkit/druggability/__init__.py` | **扩展** | `DEFAULT_WEIGHTS` 增加 `clinical` / `safety`；`_compute_composite` 增加两个维度的解析分支；`assess_druggability` 无需改动（数据来自同一次 OT 调用） |
| `tests/test_druggability.py` | **扩展** | 新增 `TargetProfile` 解析测试；扩展 `TestCompositeScore` 覆盖 5 维；新增 mock fixture |
| `tests/fixtures/opentargets_egfr.json` | **新增** | EGFR 的真实 OT 响应存档，用于离线测试 |
| `docs/tools.md` | **更新** | 在 Druggability 专用一节补充 OT 全量数据说明 |
| `README.md` | **更新** | 三级评估图升级为五维评估；示例输出增加新字段 |

---

## 4. 向后兼容策略

| 场景 | 处理方式 |
|---|---|
| 旧代码 `from bbbkit.druggability.tractability import TractabilityResult` | ✅ `TractabilityResult = TargetProfile` 别名 |
| 旧代码 `result.to_dict()["best_score"]` | ✅ `TargetProfile` 保留 `best_score` property |
| 旧测试依赖 `query_tractability()` | ✅ 函数签名不变，返回类型变为超集 |
| `assess_druggability()` 返回值 | ✅ 新增 key 不影响旧 key 的存在和含义 |
| composite 评分数值变化 | ⚠️ 权重调整会导致同一靶点的 `overall_score` 微调，但差异通常 < 0.05 |

---

## 5. API 限制与容错

| API | 限制 | 容错 |
|---|---|---|
| Open Targets GraphQL | 无 key，无硬性 rate limit（推荐 ≤ 5 req/s） | `@rate_limit(0.2)` 已有；`timeout=30`；field 不存在时 GraphQL 返回 null 而非 error |
| 新增字段可能随 OT 版本变化 | OT 一年 ~2 次 major update | 解析逻辑对每个新字段做 `.get(field, default)` 防御性编程；整体包 try/except |

---

## 6. 实施步骤

1. **Introspection 校对**：`curl` 打 OT `__schema` 确认字段名
2. **`tractability.py` 重构**：扩 query + 新 dataclass + 解析逻辑
3. **抓 fixture**：存 EGFR 真实响应为 `tests/fixtures/opentargets_egfr.json`
4. **`__init__.py` 扩展**：composite 加 clinical / safety
5. **测试**：离线单测 + `@pytest.mark.network` 在线抽查
6. **文档更新**：README + tools.md

---

## 7. 输出示例（目标）

```python
result = assess_druggability("EGFR")
```

```json
{
  "query": "EGFR",
  "query_type": "gene_symbol",
  "tractability": {
    "ensembl_id": "ENSG00000146648",
    "symbol": "EGFR",
    "name": "epidermal growth factor receptor",
    "biotype": "protein_coding",
    "small_molecule": {"modality": "small_molecule", "labels": ["Approved Drug", "Structure with Ligand"], "top_label": "Approved Drug", "score": 1.0},
    "antibody": {"modality": "antibody", "labels": ["UniProt loc"], "top_label": "UniProt loc", "score": 0.5},
    "protac": {"modality": "protac", "labels": ["Small Molecule Binder"], "top_label": "Small Molecule Binder", "score": 0.3},
    "best_score": 1.0,

    "uniprot_ids": ["P00533"],
    "target_class": ["Enzyme", "Kinase"],
    "subcellular_locations": ["Cell membrane", "Endosome"],
    "function_description": "Receptor tyrosine kinase binding ligands...",

    "expression_summary": [
      {"tissue": "Skin", "rna_value": 45.2, "rna_level": "high", "protein_level": "High"},
      {"tissue": "Lung", "rna_value": 32.1, "rna_level": "medium", "protein_level": "Medium"}
    ],
    "tissue_specificity_score": 0.42,

    "n_known_drugs": 15,
    "max_clinical_phase": 4,
    "approved_drugs": ["Erlotinib", "Gefitinib", "Osimertinib"],
    "n_chemical_probes": 3,
    "has_high_quality_probe": true,
    "has_tep": false,

    "n_safety_events": 2,
    "safety_events": [
      {"event": "Skin rash", "datasource": "AE database"},
      {"event": "Diarrhea", "datasource": "AE database"}
    ],

    "n_associated_diseases": 156,
    "top_diseases": [
      {"name": "Non-small cell lung carcinoma", "score": 0.95, "therapeutic_area": "Oncology"},
      {"name": "Glioblastoma", "score": 0.82, "therapeutic_area": "Oncology"}
    ],
    "max_disease_score": 0.95,

    "pathways": ["EGFR signaling", "PI3K-AKT pathway", "MAPK signaling"],
    "cancer_hallmarks": [
      {"label": "proliferative signalling", "impact": "promotes"}
    ]
  },
  "ligandability": {
    "target_chembl_id": "CHEMBL203",
    "n_known_ligands": 2500,
    "ligandability_score": 1.0
  },
  "composite": {
    "overall_score": 0.876,
    "confidence": "medium",
    "dimensions_available": 4,
    "contributing_scores": {
      "tractability": 1.0,
      "ligandability": 1.0,
      "clinical": 1.0,
      "safety": 0.6
    }
  }
}
```

---

## 8. 未来扩展方向（不在本次范围）

- **τ 自动纳入 composite**：当表达谱数据充足时（≥ 30 tissues），将 τ 作为 safety 的 sub-signal
- **疾病关联作为独立维度**：`disease_relevance` 权重 0.10，用 max_disease_score
- **PROTAC 可行性深度评估**：E3 连接酶邻近性、linker 可行性、半衰期数据
- **多物种支持**：当前仅人源，未来可扩展 mouse / rat orthologs
