---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TSPO 配体 – 靶点搜索评估'
footer: 'RIC-408 · Computational Sciences · 2026-10-16'
style: |
  @font-face { font-family: 'Noto Sans SC'; src: local('Noto Sans CJK SC'); }
  section { font-size: 20px; font-family: 'Noto Sans CJK SC', 'Noto Sans SC', sans-serif; padding: 40px 60px; }
  section.title { font-size: 30px; text-align: center; }
  section.title h1 { font-size: 44px; }
  h1 { font-size: 32px; margin-bottom: 8px; color: #003a70; }
  h2 { font-size: 25px; color: #003a70; border-bottom: 2px solid #003a70; padding-bottom: 4px; }
  h3 { font-size: 21px; color: #00518a; }
  table { font-size: 15px; border-collapse: collapse; margin: 8px 0; }
  th { background: #003a70; color: #fff; padding: 4px 8px; }
  td { padding: 3px 8px; border: 1px solid #ccc; }
  blockquote { font-size: 17px; color: #555; border-left: 4px solid #003a70; }
  code { background: #f0f0f0; padding: 1px 4px; }
  ul, ol { margin: 4px 0; }
  li { margin: 2px 0; }
  .highlight { color: #c0392b; font-weight: bold; }
  .good { color: #27ae60; font-weight: bold; }
  .warn { color: #e67e22; font-weight: bold; }
  .fact { color: #27ae60; font-weight: bold; }
  .obs { color: #e67e22; font-weight: bold; }
  .hyp { color: #c0392b; font-weight: bold; }
  .small table { font-size: 13px; }
---

<!-- _class: title -->

# TSPO 配体
## 靶点搜索 – 代谢表型究竟由哪个靶点驱动？

**需求方**：ZHCO，Group 3 TSPO proposal
**分析日期**：2026-10-14（报告 v0.2）· slide 2026-10-16
**RIC-408** · 分析：Jin Qiuye (Computational Sciences)

配体：**PK11195** · **Emapunil (XBD173)** · **Etifoxine** · Ro5-4864（对照）

完整报告：`tspo_ligand_target_search_report.html` — 全部结论按 <span class="fact">FACT</span> / <span class="obs">OBS</span> / <span class="hyp">MECH / HYP</span> 分级并逐行标注来源

<!-- Note (CN): 开场——这次不讲算法，讲一个药理学问题：三个"TSPO配体"的代谢表型到底是不是TSPO介导的。结论先行：PK11195指向肝脏CAR，emapunil是唯一干净的TSPO故事但代谢证据空缺，etifoxine在临床暴露下TSPO排除、大概率走肠道菌群。 -->

---

## 1. 背景与目标

**TSPO**（转位蛋白，18 kDa）是线粒体外膜蛋白：

- 参与胆固醇转运；经典 **PET 神经炎症标志物**
- 人组织表达（GTEx）：**脂肪组织**最高，其次结肠 / 肝 / 下丘脑
- Open Targets 人类遗传学：TSPO **未**被标记为 T2D 或肥胖驱动基因

立项引用了三个临床 TSPO 配体的代谢获益：

<div class="small">

| 配体 | 报道的代谢表型 | 来源 |
|---|---|---|
| **PK11195** | 降葡萄糖、抗脂肪肝（临床前） | PMID:23201900 |
| **Emapunil** | T2D 获益（引用待补） | — |
| **Etifoxine** | 高脂饮食小鼠减重 | PMID:32679124 |

</div>

> **问题**：对每个配体，该表型在**真实暴露量**下究竟能通过哪个靶点实现？
> **本分析**：实测结合数据（ChEMBL + PubChem）× 文献 × 组织表达 × 疾病遗传学 × 分子对接验证门。

<!-- Note (CN): 立项假设是TSPO介导代谢获益，我们做无偏靶点搜索来压力测试。TSPO背景一句话带过；关键铺垫：遗传学不支持TSPO作为T2D/肥胖驱动基因。 -->

---

## 2. 方法 — 证据图谱：五个方法家族，一条证据阶梯

**检验的主张**："这个配体能结合 X" 与 "X 能解释表型" 之间，需要 <span class="highlight">独立确认 + 暴露量合理性</span>。五个方法家族汇入两级证据阶梯：

<div class="small">

| 方法家族（测什么） | 能做 / 不能做 | 在阶梯中的角色 |
|---|---|---|
| ① 实测结合 — ChEMBL + PubChem（生化 / 细胞 / qHTS） | 给出每个靶点的真实 K<sub>i</sub>/IC<sub>50</sub>；不能说明体内相关性 | Gate 1（结合，亚µM） |
| ② 文献挖掘 — Europe PMC（表型 + KO 反向证据） | 捕捉效应方向与基因敲除反证；非系统性 | Gate 1 + 方向 |
| ③ 组织表达（GTEx）+ 疾病遗传学（Open Targets） | 把靶点放到正确的器官与疾病语境；仅关联性 | Gate 1 + 语境 |
| ④ 分子对接（Vina，验证门）+ 相似性（SwissTargetPrediction） | 独立的结构 / 化学型确认；效价排序不可靠 | 仅 Gate 1 确认 |
| ⑤ 暴露量 / 占据率计算（游离 C<sub>max</sub> vs K<sub>i</sub>） | 区分"试管里能结合"与"病人体内被占据" | Gate 2（占据） |

</div>

**两级阶梯**：<span class="good">Gate 1</span> = 独立确认的亚µM 结合 + 正确的组织 / 疾病语境 → 进入靶点短名单 · <span class="good">Gate 2</span> = 在有记录的临床 / 动物暴露量下占据可行 → 该靶点才能真正承载表型。

> 流程内质量控制：对接**验证门**（将 PK11195 重对接回 TSPO 自身共晶口袋 — PASS）· DrugCLIP 反向模式**未通过 decoy 门**（decoy 排名高于真配体）→ 已从所有结论中排除 · 每条结论按 FACT / OBS / MECH / HYP 分级并逐行标注来源。

<!-- Note (CN): 方法页——五家族证据图谱：①实测结合(ChEMBL+PubChem)②文献挖掘(EPMC+KO反向证据)③组织表达GTEx+遗传学OT④对接验证门+SwissTarget相似性⑤暴露量/占据率计算。两级门：Gate1=独立确认的亚微摩尔结合+正确组织/疾病语境→进短名单；Gate2=真实暴露下占据可行→才能承载表型。质量控制：对接验证门PASS；DrugCLIP反向门禁失败（decoy排名高于真配体）→排除出结论；每条结论带FACT/OBS/MECH/HYP标签。 -->

---

## 3. PK11195 — 表型指向 CAR，而非 TSPO

<span class="fact">FACT</span> **CAR（NR1I3，肝核受体）是最强的非 TSPO 靶点** — 四个独立方法家族一致确认：

| 证据 | 结果 | 来源 |
|---|---|---|
| CAR 结合（生化 + 细胞） | 拮抗 **25–56 nM**；反向激动 245–390 nM | ChEMBL（2 个 assay 家族） |
| CAR 结合（qHTS） | 0.025–0.39 µM 活性 | PubChem |
| 分子对接，CAR LBD | **−10.89** kcal/mol（TSPO 自身共晶口袋 −9.42） | Vina 验证门：PASS |
| 相似性预测 | CAR 排名 **第2**（0.888），仅次于 TSPO（0.899） | SwissTargetPrediction |

> 在肝细胞中，代谢将 PK11195 从 CAR **拮抗剂**转化为 CAR **激动剂**，诱导 CYP2B6 / CYP3A4（PMID:28442602）。CAR 表达高度肝特异：**肝 98.7 TPM，其余组织 <1**（GTEx）。

**两条独立证据反对 TSPO 介导的获益：**

- <span class="obs">OBS</span> TSPO 基因敲除大鼠高脂饮食后脂肪变和胰岛素抵抗**更重**（PMID:40195072）
- <span class="obs">OBS</span> PK11195 **抑制**离体胰岛的葡萄糖诱导胰岛素分泌（PMID:10935532）

> **核心发现**：PK11195 的代谢表型最符合 <span class="highlight">肝脏 CAR 激活 + 类禁食状态</span> — 引用它作为 TSPO 证据不成立。

<!-- Note (CN): 核心页，多停留。CAR四来源验证（ChEMBL生化+细胞、PubChem qHTS、Vina、SwissTarget），肝细胞代谢翻转成激动剂。KO大鼠反向+胰岛分泌抑制是主动跑反向假说的结果。被追问docking细节就指向报告第8-9节。 -->

---

## 4. Emapunil 与 Etifoxine — 两种不同结论

<div class="small">

| | **Emapunil (XBD173)** | **Etifoxine** |
|---|---|---|
| TSPO 亲和力 | Ki **6.4 nM** WT / 31.3 nM A147T；选择性 >1,000× | Ki **7.8 µM**（人） |
| 临床剂量游离血浆浓度 | **1.0 nM**（90 mg qd） | **0.31 nM**（50 mg tid） |
| TSPO 占据率 | ~13% WT / ~3% A147T ✅ | **<0.01%** ❌（约 4 个数量级差距） |
| 其他可测靶点 | 无（GABA-A 中枢位点 8.4 µM） | GABA-A TBPS 位点 6.7 µM；CYP / DRD2 µM 区带 |
| 代谢证据 | 公共数据中**未找到** T2D / 肥胖研究 ⚠️ | 减重表型追踪**肠道菌群 / 胆汁酸轴**（PMID 32679124, 38075272） |

</div>

- **Emapunil** — 干净的 TSPO 故事：占据率成立，认知效应已证实 TSPO 依赖（TSPO-KO 小鼠，PMID:37891168）；但代谢获益本身未证实。<span class="hyp">HYP</span> 间接路线：内源性 **DBI / endozepine 轴**（肝 / 脂肪 / 下丘脑高表达；胰岛素触发，PMID:40976282）
- **Etifoxine** — 小鼠减重剂量（50 mg/kg i.p.）按异速换算与临床暴露同量级 → TSPO 路线难以成立；相关 GABA-A 亚基**仅限中枢**（GTEx），无外周代谢路线

> <span class="good">Emapunil</span>：TSPO 占据可行，表型引用缺失 · <span class="highlight">Etifoxine</span>：真实暴露下 TSPO 被排除

<!-- Note (CN): emapunil干净但代谢证据空缺，需要ZHCO给引用；rs6971 A147T携带者Ki掉约5倍(6.4→31.3 nM)，occupancy从13.5%掉到3.1%。etifoxine关键数字：Ki 7.8 µM vs 游离血浆0.31 nM，差4个数量级；人5天交叉试验有菌群变化，是唯一人体证据。 -->

---

## 5. 对 Proposal 的结论

| 配体 | 表型最可能的驱动者 | 真实暴露下的 TSPO | 判定 |
|---|---|---|---|
| **PK11195** | **CAR 激活（肝）** + 类禁食肝状态 | 结合成立；获益归因有争议 | <span class="warn">⚠️ 不可作为 TSPO 证据引用</span> |
| **Emapunil** | TSPO — 但代谢效应未证实；DBI 轴假说 | 成立（~13% WT / ~3% A147T） | <span class="good">✅ 唯一可检验的 TSPO 故事</span> |
| **Etifoxine** | 肠道菌群 / 胆汁酸轴 | 不成立（<0.01%） | <span class="highlight">❌ 真实暴露下 TSPO 被排除</span> |
| Ro5-4864 | TSPO 选择性对照，与 PK11195 共表型 | — | 对照配体 |

**对 proposal 的三点修改建议**

1. 不要引用 PK11195 的降糖 / 抗脂肪肝表型作为 TSPO 证据 — **CAR** 才是有证据支撑的路线。
2. Emapunil 是唯一一个 TSPO 介导的代谢效应既占据可行、又可干净检验的配体。
3. Etifoxine 的减重读出不能用作 TSPO 证据 — 暴露量永远达不到 TSPO。

> **需要团队提供**：emapunil / PK11195 的 T2D 引用 · proposal 假设的 PK11195 对映体 · 内部胰岛 / 脂肪 TSPO 表达或 PET 数据

<!-- Note (CN): 收尾三句话：PK11195别默认归因TSPO；emapunil是唯一可检验的TSPO代谢故事；etifoxine的减重读出不能当TSPO证据。要三样东西：两篇T2D引用、对映体假设、内部表达/PET数据。全表在ws4_tiered_targets_v0.3.csv，逐行证据在报告HTML。 -->
