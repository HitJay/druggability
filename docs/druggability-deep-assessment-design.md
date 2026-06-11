# 6 靶点深度可药性评估 — 项目开发设计

> **日期:** 2026-06-11
> **状态:** Draft → 待评审
> **输入数据:** [data/druggability_targets.csv](../data/druggability_targets.csv)
> **关联代码:** [src/bbbkit/druggability/](../src/bbbkit/druggability/)
> **关联设计:** [docs/design-opentargets-expansion.md](design-opentargets-expansion.md)、[docs/deep-research/target-druggability-assessment.md](deep-research/target-druggability-assessment.md)

---

## 0. TL;DR

只有 **6 个**遗传学证据靶点，所以不做"批量筛选"，做"**逐靶深挖**"。核心三点：

1. **加一根新支柱 — genetics（遗传学验证）**。这 6 个靶点的共同点就是都有 GWAS 证据（WHRadjBMI / T2D / BFPCT），而现有评分体系完全没有这一维度。遗传学证据是临床成功最强的单一预测因子，必须作为评估的"第一轴"。
2. **从单一 composite 分数 → 二维画像（Validation × Tractability）+ 模态分解**。这 6 个靶点横跨 GPCR / 整合素 / 细胞因子受体 / 黏蛋白，可药性差异极大；用一个数字排名会严重误导，必须按**模态（SM / 抗体 / PROTAC / 多肽）分别打分**。
3. **N=6 才负担得起的"深"**：对每个靶点跑全部可用 PDB + AlphaFold 结构的 fpocket、解析 GWAS 方向/效应量与共定位、人工复核口袋与选择性——这些在筛 100 个靶点时做不了，6 个可以。

---

## 1. 背景：为什么 N=6 改变方法论

| | 批量筛选模式（现有 `batch.py`） | 深度评估模式（本设计） |
|---|---|---|
| 目标 | 吞吐量，从 N 个里挑 top-k | 把 6 个吃透，出可执行的立项结论 |
| 每靶成本 | 低（串行 API + 简单加权） | 高（多结构 fpocket + 遗传学深挖 + 人工复核） |
| 评分 | 单一 composite | 二维（验证×可药）+ 模态分解 + 证据明细 |
| 结构分析 | 默认关闭 | 默认开启，跑全部结构 |
| 遗传学 | ❌ 无 | ✅ 第一支柱 |
| 输出 | 一行 CSV | 每靶 one-pager + 对比矩阵 + 组合图 |

### 1.1 这 6 个靶点

| Gene | Ensembl | 靶点类别 | GWAS 性状 | 经典模态直觉 |
|---|---|---|---|---|
| **ADORA1** | ENSG00000163485 | Class A GPCR（腺苷 A1 受体） | WHRadjBMI | 小分子（激动/拮抗剂丰富） |
| **SSTR5** | ENSG00000162009 | Class A GPCR（生长抑素受体 5） | T2D | 小分子 + 多肽（帕瑞肽先例） |
| **PTGFR** | ENSG00000122420 | Class A GPCR（前列腺素 F 受体 FP） | WHRadjBMI | 小分子（**已有获批药** latanoprost/travoprost FP 激动剂） |
| **ITGB6** | ENSG00000115221 | 整合素 β6（αvβ6） | BFPCT | 抗体 / 多肽（RGD）/ 部分小分子（纤维化在研） |
| **IFNAR2** | ENSG00000159110 | I 型细胞因子受体 | WHRadjBMI | 生物制剂为主（PPI 界面） |
| **MUC1** | ENSG00000185499 | 黏蛋白（高度糖基化、无序） | BFPCT | 抗体 / ADC / 疫苗（**非经典小分子靶点**） |

> **观察：** 3 个 GPCR（小分子友好）、1 个整合素（PPI/黏附）、1 个细胞因子受体（生物制剂）、1 个黏蛋白（最难）。这种异质性正是"必须模态感知"的原因——把 MUC1 和 ADORA1 用同一把小分子可药性尺子比，毫无意义。

> **方向性是关键未知量：** 6 条都是常见变异 GWAS 关联，**保护性等位基因是增功能还是减功能**决定了你要做激动剂还是拮抗剂/降解剂。深度评估必须解析每条关联的 **direction of effect**——这直接决定模态与策略，不能跳过。

---

## 2. 评估框架：两轴 + 模态分解

### 2.1 双轴定位（组合视图）

```
        高  ┤  [Hard but worth it]        [Priority / Fast-follow]
            │   高验证 + 难成药              高验证 + 易成药
  Validation│   → 需要模态创新               → 直接立项
   (遗传/疾病)│
            │   [Deprioritize]            [Easy but weak rationale]
        低  ┤   低验证 + 难成药              低验证 + 易成药
            └────────────────────────────────────────────────
              低                                            高
                          Tractability（可药性，模态最优分）
```

6 个靶点遗传学都过关（Y 轴普遍偏高），所以**真正区分它们的是 X 轴（可药性）和模态适配**。基于领域知识的预期落位（须由实跑确认）：

- **右上（直接立项）：** PTGFR（FP 激动剂已获批）、ADORA1（GPCR 药理学成熟）
- **偏右：** SSTR5（GPCR，多肽+小分子，帕瑞肽先例）
- **中部：** ITGB6（纤维化领域抗体/多肽/小分子在研）
- **左中（生物制剂倾向）：** IFNAR2（PPI，小分子困难）
- **左（仅抗体/ADC/疫苗）：** MUC1（无序、糖基化，小分子几乎不可行）

### 2.2 六维打分卡（每靶）

| 轴 | 维度 | 子指标 | 主要数据源 | 现状 |
|---|---|---|---|---|
| **验证** | **A. 遗传学验证** ⭐新 | GWAS 关联强度、L2G、效应方向、共定位(eQTL/pQTL)、稀有/编码变异、等位基因序列 | Open Targets（evidences/associations）、GWAS Catalog、gnomAD 约束 | ❌ 待建 |
| 验证 | B. 疾病/通路相关性 | top 疾病关联分、治疗领域、通路 | OT `associatedDiseases`/`pathways` | ◐ 设计未实现 |
| **可药** | C. Tractability（**模态分解**） | SM / 抗体 / PROTAC / 多肽 各自 bucket | OT `tractability` | ✅ 已有（SM/AB/PROTAC） |
| 可药 | D. Ligandability（化学） | 已知配体数、最强活性、获批药、化学探针/TEP | ChEMBL、OT `knownDrugs`/`chemicalProbes`/`tep` | ◐ 部分（仅配体计数） |
| 可药 | E. 结构可药性 | 全部 PDB+AlphaFold 的 fpocket 最佳口袋、体积/疏水性/分级、隐蔽口袋 | RCSB + AlphaFold DB → fpocket | ✅ 已有（需多结构编排） |
| **去风险** | F. 安全/选择性 | 组织特异性 τ、安全信号、旁系同源选择性、gnomAD 约束(LOEUF)、（可选）DepMap 必需性 | OT `expressions`/`safetyLiabilities`、gnomAD | ◐ 设计未实现 |

### 2.3 评分公式

**遗传学验证分 A（0–1，证据阶梯）：**

```
A = clamp(
      0.40                                   # 存在 GWAS 关联（6 个都满足，地板分）
    + 0.30 * L2G_or_assoc_score              # OT 关联/L2G 分（0–1）
    + 0.10 * has_QTL_coloc                    # 与相关组织 eQTL/pQTL 共定位
    + 0.15 * has_rare_or_coding_evidence      # 稀有/编码变异或等位基因序列
    + 0.05 * direction_resolved,              # 方向已明确（可定激动/拮抗）
    0, 1)
```

附带 **direction flag**（↑/↓ 功能 → 激动/拮抗）与 **gnomAD LOEUF**（约束→抑制安全性提示）。

**模态可药分（不汇成一个数，按模态各出一个）：**

```
Tract_SM      = f(OT_SM_bucket, fpocket_best, ligandability)
Tract_Ab      = f(OT_Ab_bucket, 胞外可及性/定位)
Tract_PROTAC  = f(OT_PROTAC_bucket, 泛素化证据, 胞内口袋)
Tract_peptide = f(GPCR/整合素天然配体, 已知多肽)
最优可药分 = max(各模态)，并记录 best_modality
```

**安全分 F（0–1，逆向）：** 沿用 OT 扩展设计 `max(1 - 0.2·n_safety_events, 0.2)`，叠加 τ 组织特异性与 LOEUF 作为人工参考。

**综合（仅用于排序参考，主表仍展示二维 + 模态）：**

```
DEEP_WEIGHTS = {
  "genetics":      0.25,   # 新支柱
  "tractability":  0.25,   # 最优模态分
  "ligandability": 0.15,
  "structure":     0.15,
  "clinical":      0.10,   # known drugs / probes / TEP
  "safety":        0.10,
}
```

> 与现有 `DEFAULT_WEIGHTS`（tract .35 / lig .35 / struct .30）的关系：深度模式用独立的 `DEEP_WEIGHTS`，**不改动 batch 模式默认权重**，向后兼容。

---

## 3. 针对 6 个靶点的特异性考量

| 靶点 | 类别决定的评估重点 | 易踩的坑 |
|---|---|---|
| **ADORA1** | GPCR 正构/别构口袋；A1/A2A/A2B/A3 旁系选择性是核心风险 | 腺苷受体家族高度同源 → τ 与旁系选择性必须看 |
| **SSTR5** | SST1–5 家族选择性；多肽（帕瑞肽偏 SSTR5）vs 小分子 | 别只看小分子；多肽模态可能更优 |
| **PTGFR** | **已有获批 FP 激动剂** → clinical precedence 拉满；前列腺素受体 EP/FP/DP 选择性 | 临床先例会主导分数，注意区分"靶点可药"与"该适应症可药" |
| **ITGB6** | αvβ6 异二聚体，RGD 结合口袋；抗体/多肽/小分子三选 | 单看 β6 单体会漏掉 αv 配对的真实结合界面 |
| **IFNAR2** | 细胞因子受体 PPI 界面，平坦、难成小分子；胞外域→抗体友好 | fpocket 对 PPI 界面假阴性高，别因"无口袋"误判为不可药——应转抗体轴 |
| **MUC1** | 高度糖基化、VNTR 无序区，经典小分子几乎不可行；抗体/ADC/疫苗领域 | AlphaFold 对无序区 pLDDT 低、fpocket 假阳性高——结构分要降权、看定位 |

**两个跨靶提醒：**
- **GPCR / 膜蛋白结构口袋**：fpocket 跑全长含跨膜区可能命中脂质腔等假阳性，需聚焦正构口袋区域。
- **CNS 衔接（可选）**：若任一靶点走中枢食欲调控路线，可串联本仓已有的 BBB 模块（`bbb_prediction.py` / `sm_bbb.py`）评估候选分子的脑暴露——但这些 GWAS 性状（WHR/体脂/T2D）以**外周代谢**为主，默认按外周评估。

---

## 4. 与现有代码的关系

| 模块 | 现状 | 本项目动作 |
|---|---|---|
| [tractability.py](../src/bbbkit/druggability/tractability.py) | 最小 GraphQL，仅 tractability/proteinIds；只有 `TargetInfo` | **落地 OT 扩展**（见 design-opentargets-expansion）→ `TargetProfile`，新增 clinical/safety/expression/disease 字段 |
| [ligandability.py](../src/bbbkit/druggability/ligandability.py) | ChEMBL 配体计数 → 分 | 扩展：potency 分布、获批药、化学探针 |
| [pocket.py](../src/bbbkit/druggability/pocket.py) | 单结构 fpocket | 新增**多结构编排**：枚举 PDB + AlphaFold，逐一跑，取最佳 |
| [\_\_init\_\_.py](../src/bbbkit/druggability/__init__.py) | 3 维 composite | 新增 `genetics` 解析分支 + `DEEP_WEIGHTS`（不动 batch 默认） |
| [batch.py](../src/bbbkit/druggability/batch.py) | 串行批量 | 不动；深度模式用新 runner |
| genetics（新模块） | ❌ | **新建** `genetics.py`：OT 遗传学证据 + 方向 + 共定位 + gnomAD 约束 |

---

## 5. 开发计划（分阶段）

> 输出产物遵循约定：`output/2026-06-11/druggability_6targets/`（日期下命名子目录）。

### Phase 0 — 数据与脚手架 ✅（本次）
- [x] 输入 CSV：[data/druggability_targets.csv](../data/druggability_targets.csv)
- [x] 编排 runner：`scripts/run_deep_druggability.py`（复用现有 `assess_druggability` + 自包含 OT 遗传学富集，已跑通 6 靶）
- [x] 输出目录 + README：`output/2026-06-11/druggability_6targets/`
- [x] **修复 tractability 关键 bug**（见 §9）：OT 返回的每个 bucket 带 `value` 布尔，原解析未过滤 → 所有靶点 SM/Ab 全部满分。已加 `value` 字段 + 过滤。

#### Phase 0 实跑结果（修复后）

| 靶点 | genetics | tract(best) | 模态 | overall | 结论 |
|---|---|---|---|---|---|
| ADORA1 | 0.638 | 1.00 | 小分子 | 0.768 | Priority |
| ITGB6 | 0.653 | 0.90 | **抗体** | 0.736 | Priority |
| PTGFR | 0.400 | 1.00 | 小分子 | 0.677 | Tractable but verify |
| MUC1 | 0.639 | 0.90 | **抗体** | 0.638 | Priority |
| SSTR5 | 0.400 | 0.65 | 小分子 | 0.542 | Tractable but verify |
| IFNAR2 | 0.662 | 0.50 | 小分子 | 0.447 | **Hard but worth it** |

> 模态感知奏效：MUC1（黏蛋白）、ITGB6（整合素）正确路由到**抗体**；IFNAR2（PPI 细胞因子受体）可药性最低（0.50）落入"难但值得"象限。
> ⚠️ **方向性全为 unresolved** + genetics 仅地板分/OT 关联分 → 这是 Phase 2 要补的核心。

### Phase 1 — OT 全量画像落地（keystone）
- 按 [design-opentargets-expansion.md](design-opentargets-expansion.md) 把 `TRACTABILITY_QUERY` 扩成 `TARGET_QUERY`，`TractabilityResult → TargetProfile`（保留别名）。
- 一次 GraphQL 拿到 clinical / safety / expression / disease，喂给 D/F/B 维度。
- 文件：`tractability.py`、`__init__.py`、`tests/`。

### Phase 2 — Genetics 支柱（核心增量）
- 新建 `src/bbbkit/druggability/genetics.py`：
  - 性状 → EFO 映射（WHRadjBMI→EFO_0007788、T2D→MONDO_0005148、BFPCT→EFO_0007800 等，需校对）。
  - OT 靶点-疾病 evidence 查询：L2G/关联分、lead variant、**beta/OR 方向**。
  - 共定位标记（eQTL/pQTL，相关组织：脂肪/胰腺/肠/下丘脑）。
  - gnomAD 约束（LOEUF/pLI）→ 约束标记。
  - 输出 `GeneticsResult` + `genetics_score` + `direction_flag`。
- 在 `__init__.py` 接入 `DEEP_WEIGHTS` 的 genetics 维度。

### Phase 3 — 多结构 fpocket 编排
- `pocket.py` 新增 `detect_pockets_multi(uniprot_id)`：枚举 RCSB 实验结构 + AlphaFold 模型，逐一跑 fpocket，聚合最佳口袋；对无序区/PPI 标注低置信。
- 依赖：`tools/fpocket` 可执行（未装则该维度优雅缺省，置信度降级）。

### Phase 4 — 模态感知 composite + 报告生成
- 模态分解评分（SM/Ab/PROTAC/peptide）+ 模态推荐决策树（基于定位 + 口袋 + 泛素化）。
- 每靶 markdown one-pager + 对比矩阵 CSV/Parquet。

### Phase 5 — 可视化
- 二维组合图（Validation × Tractability，标注模态）。
- 每靶雷达图（6 维）。
- 汇总 PPTX/HTML（可选）。

---

## 6. 输出产物

```
output/2026-06-11/druggability_6targets/
├── README.md                      # 本批次说明 + 运行方式
├── deep_druggability_matrix.csv   # 6×全维度对比矩阵（主交付）
├── reports/
│   ├── ADORA1.md  SSTR5.md  PTGFR.md
│   ├── ITGB6.md   IFNAR2.md  MUC1.md   # 每靶 one-pager
├── raw/                           # 各靶 OT/ChEMBL/fpocket 原始 JSON（可复现）
└── figures/
    ├── portfolio_2d.png           # 验证×可药 组合图
    └── radar_<gene>.png
```

**对比矩阵列（建议）：**
`gene_name, gene_id, target_class, gwas_trait, genetics_score, direction, tractability_best, best_modality, tract_SM, tract_Ab, tract_PROTAC, ligandability_score, n_known_ligands, n_approved_drugs, structure_score, best_pocket_grade, clinical_score, safety_score, tau_specificity, loeuf, overall_score, confidence, recommendation`

---

## 7. 风险与依赖

| 风险 | 影响 | 缓解 |
|---|---|---|
| OT GraphQL schema 漂移 | 字段取不到 | 每字段 `.get(default)`；先 `__schema` introspection 校对 |
| fpocket 未安装 | 结构维度缺失 | 优雅降级（confidence 降级）；文档给安装指引 |
| PPI/无序靶点假阴性（IFNAR2/MUC1） | 误判"不可药" | 模态感知：转抗体轴，结构维度降权 |
| GWAS 方向解析失败 | 不知激动/拮抗 | evidence 层取 beta/OR；取不到则标 "direction unresolved" 待人工 |
| EFO 映射不准 | 拿错疾病证据 | 映射表人工校对 + 记录在 raw/ |
| 网络受限 | 在线 API 失败 | 每维度 try/except + 缓存到 raw/，可离线复跑 |

---

## 8. 待评审决策点

1. **范围**：先评审本设计再实现，还是直接进 Phase 1–2？（本次默认：交付设计 + 可运行脚手架）
2. **结构层**：是否安装 fpocket 跑结构维度？（默认：设计开启，运行时优雅降级）
3. **语境**：默认外周代谢评估；是否需要对走中枢路线的靶点串联 BBB 模块？
4. **遗传学深度**：是否扩展到 OT 之外（GWAS Catalog 原始 beta、MR、共定位数据集）？
5. **权重**：`DEEP_WEIGHTS` 是否认可，或按业务调整（如更重 genetics）？

---

## 9. 验证期发现的问题

### 9.1 已修复 — tractability 全满分 bug（高影响）
- **现象：** Phase 0 首跑，6 个靶点的 `tract_SM` 与 `tract_Ab` **全部 = 1.0**（含 MUC1 黏蛋白、IFNAR2 零配体），明显错误。
- **根因：** [tractability.py](../src/bbbkit/druggability/tractability.py) 的 `TRACTABILITY_QUERY` 未取 OT 每个 bucket 的 `value` 布尔；解析循环把**全部可能 bucket**（含 "Approved Drug"）都计入 → 每个 modality 必满分。
- **修复：** query 增加 `value` 字段；解析处 `if not t.get("value"): continue`。修复后分数恢复区分度（见 Phase 0 实跑表）。
- **教训：** OT tractability 必须按 `value:true` 过滤；Phase 1 落地 OT 扩展时同理。

### 9.2 待修 — ligandability 获批药计数（预存，Phase 1）
- **现象：** ADORA1/SSTR5 `n_approved_drugs=2996`（疑为 ChEMBL 全库获批药总数，非靶点特异）；其余靶点因 12s 超时显示 0。
- **影响：** 仅影响展示字段，不入 composite（composite 用 `ligandability_score`），暂不阻塞。
- **归属：** 核心 `ligandability._count_approved_drugs` 的旧行为 → Phase 1 ligandability 精修一并处理（potency 分布 + 获批药 + 化学探针）。
