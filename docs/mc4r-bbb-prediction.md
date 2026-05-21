# MC4R 激动剂血脑屏障通透性预测报告

> 分析日期：2026-05-21  
> 工具：BrainPepPass v2（本地复现）  
> 原始论文：*BrainPepPass: A framework based on supervised dimensionality reduction for predicting blood-brain barrier-penetrating peptides*  
> 结果文件：`results/mc4r_bbb_predictions.csv`

---

## 一、背景与目标

MC4R（黑皮质素4受体）是调控能量稳态、性功能和疼痛的关键 GPCR。针对 MC4R 的肽类/小分子药物是否能穿越血脑屏障（BBB）直接决定其中枢或外周作用机制，也影响给药途径设计。

本次分析尝试通过 **BrainPepPass** 和 **BBiPP** 两种预测工具对以下6个 MC4R 相关化合物进行 BBB 通透性评估。

---

## 二、目标化合物

| 化合物 | 别名 | 类型 | MoA | 研发状态 |
|---|---|---|---|---|
| **Setmelanotide** | RM-493, Imcivree | 环状肽（二硫键） | MC4R 激动剂 | ✅ 已上市（POMC/LEPR 缺陷性肥胖） |
| **Bremelanotide** | PT-141, Vyleesi | 环状肽（内酰胺） | MC4R 激动剂 | ✅ 已上市（HSDD） |
| **Afamelanotide** | Scenesse, CUV1647 | 线性肽（13肽） | MC1R/MC4R 激动剂 | ✅ 已上市（红细胞生成性原卟啉症） |
| **Bivamelagon** | LB54640 | 口服小分子 | MC4R 激动剂 | 🔬 在研（礼来） |
| **TCMCB07** | — | 环状肽 | **MC4R 拮抗剂** | 🔬 在研（缓解恶病质） |
| **NN9161** | LAMA2, 0070-0002-0453 | 脂化修饰肽 | MC4R 激动剂 | 🔬 在研（诺和诺德） |

> ⚠️ **TCMCB07 注意**：PubMed 文献（PMID 32544087, 35592439 等）明确显示 TCMCB07 是 MC4R **拮抗剂**，用于癌症/肾病恶病质，刻意设计为外周作用，**不穿越 BBB**。

---

## 三、工具说明

### 3.1 BrainPepPass v2

- **原理**：RDKit + mordred 分子描述符 → 监督式降维（3个 XGBRegressor Pattern Learning 模型）→ XGBClassifier
- **特征集（FC-4，19维）**：

| 特征组 | 特征 |
|---|---|
| FC-1（9维） | MW, TPSA, SLogP, nHBAcc, nHBDon, nN, nO, nN+nO, LogD（由LogD子模型预测） |
| FC-3（10维） | JGI9, nAcid, JGI5, RotRatio, JGI6, JGI7, Lipinski, EState_VSA5, GhoseFilter, GATS3d |

- **输出**：BBB+ / BBB−，附带概率
- **训练数据**：天然及化学修饰肽，包含环状结构，典型分子量 100–1200 Da
- **本地复现**：克隆 GitHub 模型文件（`/tmp/BrainPepPass/models/BrainPepPass_v2/*.xgb`），Python 3.10 + xgboost 3.0.2 + mordred

### 3.2 BBiPP（Monash ERC）

- **状态**：❌ **永久下线**（已核实）
- **核实方法**：
  - DNS 查询 `bbipp.erc.monash.edu` → **NXDOMAIN**（域名不存在）
  - DNS 查询父域 `erc.monash.edu` → **NXDOMAIN**（整个 ERC 子域已撤销）
  - `monash.edu` 及 `github.com` 均可正常解析，排除本地网络屏蔽
  - Wayback Machine 无任何存档快照
- **结论**：Monash ERC 子域名已从 DNS 撤销，服务器永久下线，非暂时不可达
- **处理**：本次分析无 BBiPP 结果

---

## 四、预测结果

### 4.1 BrainPepPass v2 预测

| 化合物 | BBB预测 | P(BBB+) | MW | TPSA | SLogP | LogD(pred) | HBD | HBA |
|---|---|---|---|---|---|---|---|---|
| Setmelanotide | **BBB−** | 2.8% | 1116 | 494.8 | −2.76 | −7.14 | 17 | 14 |
| Bremelanotide | **BBB−** | 18.3% | 1025 | 376.5 | −0.44 | −4.46 | 14 | 11 |
| Afamelanotide | **BBB+** | 99.3% | 1646 | 643.0 | −4.10 | −10.79 | 23 | 21 |
| Bivamelagon | **BBB−** | 10.2% | 628 | 73.4 | +5.39 | +3.96 | 0 | 5 |
| TCMCB07 | N/A | — | 结构未公开入库 | | | | | |
| NN9161 (LAMA2) | N/A | — | 结构未公开入库 | | | | | |

### 4.2 经典理化规则对照

| 化合物 | MW<500 | TPSA<90 Å² | HBD≤3 | cLogP 1–5 | BBB规则预测 |
|---|---|---|---|---|---|
| Setmelanotide | ❌ | ❌ | ❌ | ❌ | **不可能穿越（被动扩散）** |
| Bremelanotide | ❌ | ❌ | ❌ | ✅ | **不可能穿越（被动扩散）** |
| Afamelanotide | ❌ | ❌ | ❌ | ❌ | **不可能穿越（被动扩散）** |
| Bivamelagon | ❌(628) | ✅ | ✅ | ✅ | **可能穿越**（偏大但其余均达标） |

---

## 五、结果解读与局限性

### 5.1 Afamelanotide 假阳性（BBB+ 99.3%）

**反常**：Afamelanotide 是皮下植入剂（Scenesse），作用于皮肤 MC1R，无中枢用途。但模型预测 BBB+ 概率高达 99.3%。

**原因分析**：
- MW=1646、TPSA=643、HBD=23，从物化性质来看完全不具备被动穿越BBB的能力
- BrainPepPass 训练集以中小型肽为主（典型 < 1200 Da），对 MW > 1500 的超大线性肽泛化性不足
- **结论**：此预测结果为模型假阳性，应忽略

### 5.2 Bremelanotide 可能假阴性（BBB− 18.3%）

**反常**：Bremelanotide（Vyleesi）经鼻腔或皮下给药后确实产生中枢性性唤醒效应，提示其可进入 CNS。

**可能解释**：
1. 经受体介导或主动转运穿越 BBB（非被动扩散），模型无法捕捉主动转运机制
2. 鼻腔给药时部分药物通过嗅球直接进入 CNS，绕过血脑屏障
3. 下丘脑-垂体区域血脑屏障通透性本身较高（area postrema 等缺乏 BBB 区域）

### 5.3 Bivamelagon 可能假阴性（BBB− 10.2%）

**反常**：Bivamelagon 是口服小分子，TPSA=73.4、HBD=0、LogP=5.4，经典规则预测较易穿越 BBB。

**原因**：BrainPepPass **仅针对肽类**训练，Bivamelagon 作为非肽小分子超出训练域，预测结果不可靠。应使用专门的小分子 BBB 预测工具（如 B3clf、SwissADME、pkCSM）。

### 5.4 Setmelanotide（最可信结果）

BBB− (2.8%) 与现实一致：Setmelanotide 主要通过外周 MC4R 发挥部分作用，虽有报道显示某些情况下可进入中枢，但分子量大、极性强（TPSA=495，HBD=17）不利于被动穿越。

---

## 六、结构未知化合物说明

### TCMCB07
- **类型**：MC4R 拮抗剂，用于癌症/慢性肾病导致的恶病质
- **结构**：未在 ChEMBL / PubChem 公开收录；设计论文（Gruber et al., *ACS Pharmacol Transl Sci* 2022, PMID 35592439）描述了其为药样环肽
- **BBB设计意图**：刻意设计为**外周作用**，文献（Hu et al., *J Cachexia Sarcopenia Muscle* 2020, PMID 32725770）证实其经 OATP1A2 肠道吸收，但不穿越 BBB

### NN9161 (LAMA2, 0070-0002-0453)
- **类型**：Novo Nordisk MC4R 激动剂，含 C18 脂肪酸（四唑修饰）+ PEG 接头的脂化修饰肽（~13 残基），结构如附图
- **结构**：未在公共数据库（ChEMBL / PubChem）收录；需查阅诺和诺德专利申请
- **BBB 预期**：脂化修饰通常用于延长半衰期（类似 semaglutide），会显著增加 MW 和亲脂性，BBB 通透性预测意义存疑，且模型无法处理此类非典型修饰

---

## 七、推荐后续分析

| 分析 | 工具 | 适用对象 |
|---|---|---|
| 小分子 BBB 预测 | B3clf / SwissADME / pkCSM | Bivamelagon |
| 主动转运评估 | P-gp efflux 预测（pkCSM） | Bremelanotide |
| 脂肽 BBB 预测 | 无成熟工具，需实验验证 | NN9161 |
| 多参数优化评分 | CNS-MPO score（6维评分） | 所有化合物 |

---

## 八、参考文献

1. Oliveira EC et al. *BrainPepPass: A framework based on supervised dimensionality reduction for predicting blood-brain barrier-penetrating peptides.* 2022. GitHub: [ewerton-cristhian/BrainPepPass](https://github.com/ewerton-cristhian/BrainPepPass)
2. Gruber KA et al. *Development of a Therapeutic Peptide for Cachexia Suggests a Platform Approach for Drug-like Peptides.* ACS Pharmacol Transl Sci 2022;5(5):344–361. PMID 35592439
3. Hu Y et al. *Characterization of the cellular transport mechanisms for the anti-cachexia candidate compound TCMCB07.* J Cachexia Sarcopenia Muscle 2020;11(6):1677–1687. PMID 32725770
4. Zhu X et al. *Melanocortin-4 receptor antagonist TCMCB07 ameliorates cancer- and chronic kidney disease-associated cachexia.* J Clin Invest 2020;130(9):4921–4934. PMID 32544087
