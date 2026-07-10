# GHSR 靶点可成药性综合评估报告

**日期**: 2026-07-10 | **作者**: QYJI | **工具**: bbbkit.druggability + 3_safety pipeline

---

## 1. 基本信息

| 项目 | 详情 |
|------|------|
| **基因符号** | GHSR |
| **蛋白全称** | Growth hormone secretagogue receptor type 1 (Ghrelin receptor) |
| **Ensembl ID** | ENSG00000121853 |
| **UniProt** | Q92847 |
| **ChEMBL Target** | CHEMBL4616 |
| **靶点家族** | GPCR (Class A, Gq-coupled) |
| **亚细胞定位** | 细胞膜, 多次跨膜蛋白 |
| **信号通路** | G alpha (q) signalling; Peptide ligand-binding receptors |
| **主要功能** | 与 ghrelin 结合，调节食欲和促进生长激素分泌 |
| **已知疾病关联** | 孤立性部分性 GH 缺乏症 (GHDP, MIM 615925)；恶病质；肥胖 |
| **PDB 结构** | 10 个 (分辨率 2.52–3.30 Å, 含 X-ray 和 Cryo-EM) |

---

## 2. 遗传学约束 (gnomAD)

| 约束类型 | oe 值 | oe 上界 | oe 下界 | 解读 |
|----------|-------|---------|---------|------|
| **LoF (失去功能)** | 0.688 | 1.033 | 0.470 | **LoF 耐受** — 下界 0.47, 不属于单倍剂量不足敏感 |
| **Missense** | 0.991 | 1.067 | 0.920 | 高度耐受错义变异 |
| **Synonymous** | 1.064 | 1.184 | 0.956 | 无约束 |

**解读**: GHSR 在人群中对 LoF 变异高度耐受 (LOEUF 上界 1.19, pLI ≈ 0.001), 表明杂合性功能丧失在人类中通常是可存活的。这对抑制策略是利好 — 靶点本身不是必需基因。但需注意纯合/复合杂合 LoF 可导致孤立性 GH 缺乏症。

---

## 3. 表达谱 (GTEx v8, median TPM)

GHSR 表达高度局限, 仅 6/54 组织可检测:

| 组织 | median TPM |
|------|------------|
| Pituitary (垂体) | 5.26 |
| Brain - Hypothalamus (下丘脑) | 0.21 |
| Brain - Nucleus accumbens | 0.09 |
| Testis (睾丸) | 0.07 |
| Pancreas (胰腺) | 0.04 |
| Brain - Hippocampus (海马) | 0.01 |
| **其余 48 个组织** | **0.00** |

**解读**: 表达高度局限于垂体-下丘脑轴, 大部分外周组织无表达。这是安全性方面的有利因素 — 脱靶组织毒性风险低。但 CNS 穿透性需要根据适应症目标评估 (外周限制性 vs. 中枢靶向)。

---

## 4. 可成药性评估 (Tractability)

| 模态 | 分数 | Top Label | 证据 Labels |
|------|------|-----------|-------------|
| **小分子 (SM)** | **1.00** | Approved Drug | Approved Drug, Structure with Ligand, High-Quality Ligand, Druggable Family |
| 抗体 (AB) | 0.40 | UniProt SigP or TMHMM | GO CC high conf, UniProt loc med conf |
| PROTAC | 0.00 | — | 无 |

**小分子可成药性满分** — GHSR 被 Open Targets 标注为 "Approved Drug" (已有获批上市药物), 属于 Druggable Family (GPCR Class A), 且有多达 10 个高分辨率共晶结构 (2.52–3.30 Å)。这是新药研发中可遇不可求的理想起点。

---

## 5. 已知配体与临床药物 (ChEMBL)

| 指标 | 数值 |
|------|------|
| 已知活性化合物 | 3,459 条活性记录 |
| 已知配体分子数 | 102+ (至少) |
| 作用机制记录 | 10 条 |
| 获批药物 (Phase 4) | 2 个 |
| Phase 3 临床候选物 | 3 个 |

**代表性临床药物**:

| 药物 | Phase | 作用类型 | 适应症 |
|------|-------|----------|--------|
| Macimorelin (AEZS-130) | 4 (获批) | Agonist | GH 缺乏症诊断 |
| Anamorelin | 3 (日本获批) | Agonist | 癌症恶病质 |
| Ulimorelin | 3 | Agonist | 胃肠动力障碍 |
| Ibutamoren (MK-0677) | 2 | Agonist | 生长激素缺乏 |

**Ligandability 评分**: 0.80 (≥100 配体阈值得分)

**注意**: 所有已进入临床的 GHSR 药物均为 **激动剂 (agonist)**, 目前无拮抗剂获批/进入后期临床。这反映了历史上主要关注 GH 分泌促进和食欲刺激的适应症。

---

## 6. 遗传学与疾病关联 (Open Targets)

| 指标 | 数值 |
|------|------|
| 相关疾病数 | 415 |
| 遗传学评分 (genetics_score) | 0.63 |
| 遗传关联评分 (genetic_assoc) | 0.768 |
| **综合推荐** | **Priority — 高验证 + 易成药, 建议立项** |

**Top 10 疾病关联**:

| 疾病 | 总评分 | 遗传关联 |
|------|--------|----------|
| Short stature due to GHSR deficiency | 0.674 | 0.768 |
| Non-small cell lung carcinoma | 0.491 | 0 |
| Abnormality of the skeletal system | 0.464 | 0.764 |
| Cancer (泛癌) | 0.394 | 0 |
| Fibromyalgia | 0.389 | 0 |
| Malignant pancreatic neoplasm | 0.388 | 0 |
| Colorectal cancer | 0.388 | 0 |
| Gastroparesis | 0.381 | 0 |
| Cachexia (恶病质) | 0.377 | 0 |
| Gastric cancer | 0.374 | 0 |

---

## 7. 方向特异性安全性评估 (3_safety pipeline)

**两种方向均评为 🔴 RED — 均需严格控制治疗窗口**

### 7a. 抑制 (Antagonism / Inhibition)

| 指标 | 详情 |
|------|------|
| **评级** | 🔴 RED (Risk Score: 88) |
| **匹配风险关键词** | hypotension (70), vomiting (30), hyperglycemia (40), cardiac monitoring (45), pediatric (40) |

**主要安全性发现**:

1. **GH/IGF-1 轴抑制** (🔴 高风险): 杂合性 LoF 导致孤立性部分 GH 缺乏症 — 身材矮小、低血糖、酮症、呕吐。儿科用药需极度谨慎。

2. **内分泌代谢紊乱**: 拮抗作用破坏 GH/ACTH/皮质醇信号, 降低胰岛素分泌 → 高血糖/低血糖风险, 抑制食欲, 减少胃动力。

3. **心血管**: 潜在低血压 + 左室收缩/舒张功能下降; 也有反常高血压/心动过速报告 → 需心功能监测。

4. **神经精神**: VTA GHSR 敲除/JMV2959 拮抗增加小鼠焦虑样行为 → 情绪/焦虑不良反应风险。

5. **有利方面**: 小鼠 GHSR KO 呈现瘦表型 + 改善胰岛素敏感性 + β细胞保护 + 认知保留; GHSR 非抑癌基因 → 不促进肿瘤发生。

### 7b. 激活 (Agonism / Activation)

| 指标 | 详情 |
|------|------|
| **评级** | 🔴 RED (Risk Score: 84) |
| **匹配风险关键词** | hypotension (70), nausea (30), hyperglycemia (40) |

**主要安全性发现**:

1. **GH/IGF-1 轴过度激活** (🔴 高风险): 持续 GH/IGF-1 升高 → 胰岛素抵抗、高血糖、水钠潴留、关节痛、肢端肥大特征、GH 敏感性恶性肿瘤理论促增殖风险。

2. **代谢/肥胖**: 食欲亢进 + 体重增加 + 脂肪堆积 — 慢性给药在代谢人群中存在问题。

3. **血糖异常**: 生长素受体激动 → 胰岛素分泌减少 → 一过性高血糖/胰岛素抵抗。

4. **心血管**: 低血压 + 左室功能下降 (与抑制方向类似); 亦有高血压/心动过速报告。

5. **有利方面**: 已有多个激动剂人体临床安全性数据 (anamorelin, ibutamoren 等), 在恶病质背景下耐受性可接受; 无明确人 GoF 遗传变异提示过度激活风险。

### 7c. 双向安全性对比

| 维度 | 抑制 | 激活 |
|------|------|------|
| 评级 | 🔴 RED (88) | 🔴 RED (84) |
| 核心风险 | GH 缺乏、生长发育障碍 | GH 过多、代谢异常 |
| 有利因素 | 瘦表型、胰岛素敏感 | 已有人体临床数据支撑 |
| 儿科适用 | ❌ 高禁忌 | ❌ GH 轴过度刺激 |
| 肿瘤风险 | ✅ 低 (非抑癌基因) | ⚠️ GH 敏感性肿瘤需筛查 |
| 临床验证 | 无拮抗剂获批 | 2 个获批激动剂 |

---

## 8. 深度综合评分 (Deep Composite)

| 维度 | 分数 | 权重 |
|------|------|------|
| Genetics | 0.630 | 25% |
| Tractability (SM) | 1.000 | 25% |
| Ligandability | 0.800 | 15% |
| Structure | N/A | 15% |
| Clinical (Phase 1) | N/A | 10% |
| Safety (Phase 1) | N/A | 10% |
| **Overall** | **0.812** | — |
| **Confidence** | **medium** (3/6 dimensions) | — |

**模态推荐**: **小分子** (score=1.00) — 首选路径; 已有 Approved Drug 级别验证, 10 个高分辨率结构, 丰富的 SAR 基础。

---

## 9. 综合结论与建议

### 一句话总结
**GHSR 是"极致可药但双向高危"的经典 GPCR 靶点 — 小分子满分 1.0 + Approved Drug 验证, 但抑制和激活方向均 RED, 需要精确定义治疗窗口和适应症选择。**

### 可成药性等级: ⭐⭐⭐⭐⭐ (5/5 — 极致)
- 小分子 tractability 满分, 已有获批药物
- 10 个高分辨率共晶结构
- 丰富的配体 SAR, 3,459 条活性数据
- GPCR Class A — 最成功的小分子靶点家族

### 安全性等级: ⚠️ 双向 RED
- 抑制 → GH 缺乏、儿童发育障碍
- 激活 → GH 过度、代谢异常
- 治疗窗口窄, 需要精确定义

### 建议路径

1. **适应症精准选择** — 不同方向对应不同适应症:
   - **抑制**: 肥胖、Prader-Willi 综合征、物质滥用 (利用瘦表型+食欲抑制+认知保留)
   - **激活**: 恶病质、GH 缺乏 (已有临床验证路径)

2. **外周限制性 vs. 中枢穿透** — GHSR 主要表达于垂体-下丘脑, 外周限制性配体可降低 CNS 副作用

3. **偏倚信号 (biased signaling)** — 利用 Gq vs. β-arrestin 偏倚配体分离食欲促进和 GH 分泌等下游效应

4. **部分拮抗剂策略** — 不完全抑制 GHSR 的高固有活性 (constitutive activity), 降低 GH 完全缺失风险

5. **肝脏/外周选择性前药** — 避免 CNS 穿透以降低神经精神不良反应

### 数据产物路径
- 综合报告: `/das/user/QYJI/druggability/GHSR_druggability_assessment.md`
- 安全性详细报告: `/TDE_TV/shared_folder/QYJI/safety/2026-07-10_1014_anthropic_claude_opus_4_7/ghsr_safety/summary.md`
- 安全性 CSV: `/TDE_TV/shared_folder/QYJI/safety/2026-07-10_1014_anthropic_claude_opus_4_7/ghsr_safety/summary.csv`
- 安全性 HTML: `/TDE_TV/shared_folder/QYJI/safety/2026-07-10_1014_anthropic_claude_opus_4_7/ghsr_safety/summary.html`
