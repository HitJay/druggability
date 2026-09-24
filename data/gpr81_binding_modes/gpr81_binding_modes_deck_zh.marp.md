---
marp: true
theme: default
paginate: true
size: 16:9
header: 'GPR81 / HCAR1 成药性评估 — 结合模式解析与结构药理学'
footer: 'Research Insights China (RIC) · 靶点发现团队合作项目 · 2026年9月'
style: |
  section {
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', sans-serif;
    font-size: 18.5px;
    padding: 32px 46px;
    background-color: #F8FAFC;
    color: #1E293B;
  }
  section.title {
    font-size: 24px;
    text-align: center;
    background: linear-gradient(135deg, #001965 0%, #003366 100%);
    color: #FFFFFF;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.title h1 {
    font-size: 34px;
    color: #FFFFFF;
    margin-bottom: 12px;
    line-height: 1.25;
  }
  section.title p {
    color: #E2E8F0;
    margin: 5px 0;
  }
  h1 {
    font-size: 27px;
    color: #001965;
    margin-bottom: 8px;
  }
  h2 {
    font-size: 21px;
    color: #001965;
    border-bottom: 2px solid #00857C;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 10px;
  }
  h3 {
    font-size: 17px;
    color: #00857C;
    margin-top: 6px;
    margin-bottom: 4px;
  }
  p, li {
    font-size: 16px;
    line-height: 1.45;
    color: #334155;
  }
  ul {
    margin-top: 3px;
    margin-bottom: 6px;
    padding-left: 20px;
  }
  li {
    margin-bottom: 3px;
  }
  table {
    font-size: 13.5px;
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
  }
  th {
    background-color: #001965;
    color: #FFFFFF;
    padding: 6px 10px;
    font-weight: 600;
  }
  td {
    padding: 5px 10px;
    border: 1px solid #CBD5E1;
  }
  tr:nth-child(even) {
    background-color: #F1F5F9;
  }
  .card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .callout {
    background-color: #F0FDF4;
    border-left: 4px solid #16A34A;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 14.5px;
    margin: 6px 0;
  }
  .callout.blue {
    background-color: #EFF6FF;
    border-left-color: #2563EB;
  }
  .callout.amber {
    background-color: #FEF3C7;
    border-left-color: #D97706;
  }
  .callout.coral {
    background-color: #FEF2F2;
    border-left-color: #DC2626;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12.5px;
    font-weight: 600;
  }
  .badge-safe { background-color: #DCFCE7; color: #166534; }
  .badge-accent { background-color: #FEE2E2; color: #991B1B; }
  .badge-neutral { background-color: #FEF3C7; color: #92400E; }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
  }
  img {
    max-width: 100%;
    height: auto !important;
    object-fit: contain;
    border-radius: 6px;
    display: block;
    margin: 0 auto;
  }
---

<!-- _class: title -->

# GPR81 / HCAR1 激动剂结合模式解析
### 正构激动 vs. 变构 ago-PAM 调控：关键证据、同系物 FEP 与客观评价

**靶点发现团队合作项目 · 机制解析与成药性评估交付**

金秋野 (Jay) · 资深数据科学家 · Research Insights China (RIC)
诺和诺德中国研发中心 (NNRCC) · 2026年9月 · 追踪代号: RIC-396

---

## 1. 核心结论摘要：定性结论与多层证据链

<div class="grid-2">
<div class="card">

### 核心药理学判定
* **AZ1 是严格正构激动剂 (Orthosteric Agonist)**：
  * 与乳酸直接争夺深层 **Arg71** 盐桥，产生 0.89 Å 致命空间穿透，互为完全竞争。
* **GPR81 Agonist 1 是变构正向调控剂 (ago-PAM)**：
  * 结合于胞外浅槽 **TM5–TM6–ECL2**，与乳酸 7.71 Å 零位阻共存，主动锚定 **Glu153**。
  * 权威药理文献（*Br J Pharmacol* 2026）ebBRET 传感器正式确证其 ago-PAM 身份。
* **先导物 c30 的精准定位 (同系物探针)**：
  * 对 Glu153 仅为空间耐受（非核心锚点）；通过 **c30 vs c31** 活性断崖反向确证变构口袋。

</div>
<div class="card">

### 证据闭环与计算真实边界
* **三元共结合几何 (Ternary Simulation)**：
  * [乳酸 + Ag1] 稳定共存（体系能量 $-152.6$ kcal/mol）；[AZ1 + Ag1] 在前庭发生 $2.60$ Å 碰撞。
* **同系物 OpenFEP 动态微扰**：
  * c30 ➔ c31 在变构槽捕捉到 $-206.5$ kcal/mol 排斥激增，预言 E153A 具有特异性救援表型。
* **客观边界与计算软肋坦陈**：
  * 尚无 Ag1 实验冷冻电镜密度；隐式溶剂存在长程静电噪声（使 R71A 出现弱伪影）。
  * 终审权交付湿实验：R71A/E153A 双向分离与 c31 突变救援双闸门。

</div>
</div>

---

## 2. 受体拓扑架构：相距 17.7 Å 的两个完全独立口袋

<div class="grid-2">
<div>

* **正构核心口袋 (Orthosteric Core, TM2–TM3–TM7)**：
  * 位于受体深部跨膜腔，入口被胞外第二环 ECL2（**Phe168 / Ser167**）紧密覆盖。
  * 专属性识别内源配体**乳酸**及小分子羧酸，依赖 **Arg71** 形成核心带电盐桥。
* **变构浅槽 (Allosteric Crevice, TM5–TM6–ECL2)**：
  * 位于受体外侧面向脂膜/溶剂界面的胞外裂缝。
  * 依靠酸性残基 **Glu153** 形成极性锚点，外侧辅以疏水缝隙（**Met170 / His155**）。
* **物理与热力学完全独立**：
  * 两口袋质心相距 **17.7 Å**，原子间无任何物理重叠。
  * **结论**：跨口袋跨骨架 FEP 在数学上无法微扰闭合；但物理上支持两分子同时结合。

</div>
<div>

![w:470](slide_figures/panel_a_domain_topology.png)

</div>
</div>

---

## 3. 结构域特异性：正构 (AZ1/乳酸) vs 变构 (Agonist 1)

<div class="grid-3">
<div class="card">

### L-乳酸 (内源配体)
* **结合位点**：正构核心 TM2/3/7
* **核心锚点**：**Arg71** ($-3.62$ kcal/mol 盐桥)
* **顶部盖帽**：Phe168 / Ser167
* **药理特征**：天然代谢信号，mM 级结合保证快速 on/off 响应。
* **计算突变敏感度**：
  * **R71A**: <span class="badge badge-accent">+3.74 kcal/mol</span> (破坏盐桥)
  * **E153A**: <span class="badge badge-safe">-3.00 kcal/mol</span> (完全无害)

</div>
<div class="card">

### AZ1 (阿斯利康正构)
* **结合位点**：正构核心 TM2/3/7
* **核心锚点**：**Arg71** ($-11.03$ kcal/mol 极性簇)
* **芳香堆积**：Phe168 / Ser167
* **药理特征**：完全竞争性激动剂，物理挤占内源乳酸结合位。
* **计算突变敏感度**：
  * **R71A**: <span class="badge badge-accent">+10.24 kcal/mol</span> (结合崩塌)
  * **E153A**: <span class="badge badge-safe">-3.35 kcal/mol</span> (不受影响)

</div>
<div class="card">

### Agonist 1 (变构工具药)
* **结合位点**：变构浅槽 TM5/6/ECL2
* **核心锚点**：**Glu153** ($-6.21$ kcal/mol 关键作用)
* **外侧疏水**：Met170 / His155
* **药理特征**：ago-PAM；不挤脱乳酸，协同提升受体效能。
* **计算突变敏感度**：
  * **E153A**: <span class="badge badge-accent">+6.57 kcal/mol</span> (结合崩塌)
  * **R71A**: <span class="badge badge-neutral">+4.68 kcal/mol</span> (维持耐受)

</div>
</div>

<div class="callout blue" style="margin-top: 10px;">
<strong>核心机制差异：</strong> AZ1 抢占正构深层 Arg71 盐桥；Agonist 1 依赖变构浅槽 Glu153 极性锚定；而先导物 c30（吡啶酮 C-H）对 Glu153 仅为空间耐受（不碰撞），因此单测 c30 无法产生如 Agonist 1 般的 E153A 亲和力崩塌。
</div>

---

## 4. 关键证据 1：共存相容性检测 (乳酸 vs Ag1 vs AZ1 空间排斥图谱)

<div class="grid-2">
<div>

* **[乳酸 + Agonist 1]：三元共结合稳定 (完全相容)**：
  * 两分子最小原子间距为 **7.71 Å**（质心相距 11.24 Å）。
  * 体系非键相互作用能达 **$-152.6$ kcal/mol**，零空间位阻重叠。
  * **药理意义**：证实 **ago-PAM 协同机制**——内源乳酸与变构分子同时结合，发挥超叠加效能。
* **[AZ1 + 乳酸]：绝对同位排斥 (完全竞争，无法共存)**：
  * 两者质心相距仅 **4.99 Å**，最小重原子间距仅 **0.89 Å**（严重空间穿透）！
  * 存在 8 对原子间距 < 2.0 Å（直接争夺 Arg71）；范德华排斥能超数百万 kcal/mol。
  * **药理意义**：**AZ1 与乳酸绝对无法共结合**，是典型的同位竞争性正构激动剂。
* **[AZ1 + Agonist 1]：胞外前庭碰撞 (排斥，无法共存)**：
  * 两分子在胞外前庭最小间距仅 **2.60 Å**，大分子 AZ1 尾部封死了变构通道。

</div>
<div>

![w:470](slide_figures/panel_b_ternary_cooccupancy.png)

</div>
</div>

---

## 5. 关键证据 2：HCAR1 vs HCAR2 选择性 (临床防皮肤潮红机制)

<div class="grid-2">
<div>

* **靶点开发的临床潮红痛点**：
  * 同家族受体 HCAR2（GPR109A，烟酸受体）在皮肤朗格汉斯细胞激活后，会大量释放前列腺素 PGD2/PGE2，引发严重的皮肤潮红副作用。
* **HCAR1 靶向结合槽 (PDB 8Z8A)**：
  * 残基特征：`Leu152–Glu153–Asn154`（酸性/中性微环境）。
  * **Glu153** 的负电荷为变构激动剂提供关键的 **$-6.21$ kcal/mol** 静电锚定。
* **HCAR2 避让机制 (PDB 8J6P)**：
  * 同源位点突变为：`Lys164–Lys165–Lys166` (**三赖氨酸正电壁**)。
  * 连续三个正电荷筑起高达 **$+45.2$ kcal/mol 的静电排斥屏障**，物理上彻底阻止变构分子结合，从而完全免除了皮肤潮红风险。

</div>
<div>

![w:450](slide_figures/panel_c_hcar1_vs_hcar2_selectivity.png)

</div>
</div>

---

## 6. 关键证据 3：同口袋同系物 OpenFEP 模拟 (反向确证变构口袋)

<div class="grid-2">
<div class="card">

### 基准选型依据：为何选择 c30 ➔ c31？
* **48 倍实测活性断崖 (真实药理事实)**：
  * **c30** (5.0 nM 领头物，吡啶酮) ➔ **c31** (240 nM，嘧啶酮)。
  * 对应高达 **$\Delta\Delta G_{\text{exp}} = +2.31$ kcal/mol** 的结合自由能惩罚。
* **统计力学最理想的单原子微扰**：
  * 全分子 75 个原子中有 73 个完全一致，仅中心环 3 号位 **C-H ➔ N-3**。
  * 彻底避免骨架翻转或基团大尺度重排伪影，FEP 采样收敛性最佳。
* **变构残基 Glu153 的靶向分子探针**：
  * 在变构口袋中，3 号位正好直面 **Glu153** 带负电的羧酸侧链。
  * 引入富电子孤对电子的负电 N-3 产生正面同号排斥，是检验变构假说的特异性探针。

</div>
<div class="card">

### 微观自由能梯度剖析 ($\partial U/\partial\lambda$, A100 GPU)
* **变构口袋发生断崖式静电排斥**：
  * 在变构口袋中，当 $\lambda \to 1.0$（完整引入 N-3 并消氢）时，能量导数直接垂直跳水到 **$-206.5 \pm 79.9$ kcal/mol** 的剧烈斥力！
  * **物理归因**：N-3 孤对电子与变构入口处的 **Glu153** 产生正面同性排斥，完美解释了 48 倍活性丧失。
* **正构口袋响应迟钝**：
  * 正构口袋末端排斥导数仅为 $-129.7 \pm 7.0$ kcal/mol，缺乏针对 N-3 的特异性排斥。
* **结论**：热力学积分以极高灵敏度反向证明，**该系列分子的功能结合腔就是变构口袋**。
* **各微扰支路积分值**：水相参考态 $+9.47$ kcal/mol；变构 $-46.59$ kcal/mol；正构 $-41.97$ kcal/mol。

</div>
</div>

---

## 7. 关键证据 4：全原子虚拟丙氨酸扫描 (先验盲测预测矩阵)

<div class="card">

### 残基突变敏感度预测矩阵 (基于 PDB 8Z8A OpenMM 动力学平衡)
| 评价配体与结合模式 | 全蛋白非键总作用能 | 与 Arg71 相互作用 | **R71A 亲和力惩罚预测** | 与 Glu153 相互作用 | **E153A 亲和力惩罚预测** | 动力学判决表型结论 |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **L-乳酸** *(正构内源)* | $-44.4$ kcal/mol | $-3.6$ kcal/mol | <span class="badge badge-accent">+3.74 kcal/mol</span> | $+3.2$ kcal/mol | <span class="badge badge-safe">-3.00 kcal/mol</span> | **绝对依赖 Arg71 盐桥**；完全不依赖 Glu153 |
| **AZ1** *(正构工具药)* | $-102.1$ kcal/mol | $-11.0$ kcal/mol | <span class="badge badge-accent">+10.24 kcal/mol</span> | $+3.5$ kcal/mol | <span class="badge badge-safe">-3.35 kcal/mol</span> | **严格正构激动剂**：R71A 活性断崖崩塌 (>100倍) |
| **Agonist 1** *(变构工具药)* | $-67.8$ kcal/mol | $-4.5$ kcal/mol | <span class="badge badge-neutral">+4.68 kcal/mol*</span> | $-6.2$ kcal/mol | <span class="badge badge-accent">+6.57 kcal/mol</span> | **严格变构 ago-PAM**：E153A 造成致命破坏 |

</div>

<div class="grid-2" style="margin-top: 8px;">
<div class="callout amber" style="font-size:13.5px; padding:6px 10px;">
<strong>*计算长程静电噪声说明：</strong> Agonist 1 预测出的 +4.68 kcal/mol R71A 惩罚源于隐式溶剂中未充分屏蔽的 17.7 Å 跨域库仑效应，非物理接触。实测预期为高耐受。
</div>
<div class="callout blue" style="font-size:13.5px; padding:6px 10px;">
<strong>为何先导物 c30 不作单点指示剂：</strong> c30 的 C-H 对 Glu153 仅为耐受而非强盐桥，E153A 不会引发其自身崩塌；c30 的真正威力在于与 c31 配对的突变救援。
</div>
</div>

---

## 8. 客观评价：变构论证的三大硬核支撑 vs 两大计算软肋与替代假说

<div class="grid-2">
<div class="card">

### 变构假说的三大硬核支撑 (不可动摇的物理/药理基石)
* **药理功能表型事实 (FACT)**：
  * 权威文献（*Br J Pharmacol* 2026）通过 ebBRET 传感器确证 Ag1 为 **ago-PAM**，诱发非竞争性协同，药理学上直接否定单纯正构竞争。
* **三元共存几何可行性 (OBS)**：
  * [乳酸 + Ag1] 最小间距 **7.71 Å**，非键能达 $-152.6$ kcal/mol，零碰撞共结合；反观 [AZ1 + 乳酸] 产生 $0.89$ Å 致命穿透，互斥性鲜明。
* **变构传导网络保守性 (MECH)**：
  * 同家族 HCAR2（PDB 8J6P）外源激动剂 9n 结合在同源 TM5-TM6 浅槽；该位点直通 TM6 胞内张角（$14.8$ Å 外摆）与开关残基 Trp248。

</div>
<div class="card">

### 必须直面的计算软肋与待证假设 (同行评议易质疑点)
* **缺乏直接实验密度 (No Co-Crystal Ground Truth)**：
  * 尚无 Ag1 共晶/电镜密度；无偏置 Boltz-2 具有强烈的 GPCR 主口袋归巢偏置（因其对正构深腔的算法先验）。
* **隐式溶剂连续介电伪影 (Dielectric Scaling Artifact)**：
  * OBC2 溶剂弱屏蔽导致 17.7 Å 外的 R71A 产生 $4.68$ kcal/mol 虚假扰动；双向能量窗口仅 $1.89$ kcal/mol，需实验消除假象。
* **药理 ago-PAM 的机制二义性 (Alternative Mechanisms)**：
  * ago-PAM 功能表型在理论上还可能源自**受体同源二聚体（Homodimer）跨分子异向变构**或正构前庭双拓扑（Bitopic），需质粒突变排他。

</div>
</div>

---

## 9. 建议的生物学验证路线图 (分层确证的双闸门湿实验)

<div class="grid-2">
<div class="card">

### 闸门 A：双位点丙氨酸突变 (主结合腔一剑封喉判决)
* **构建两组关键点突变质粒**：
  * **R71A**（正构核心破坏） vs **E153A**（变构浅槽破坏）
* **不可逆转的双向分离判决准则**：
  * **AZ1**：在 R71A 上活性出现 >100 倍断崖，在 E153A 上完全耐受；
  * **Agonist 1**：在 E153A 上活性/效能显著崩溃，在 R71A 上维持响应；
* **破除计算软肋**：若 Ag1 在 R71A 上维持活性，彻底证伪计算中的长程静电噪声。

</div>
<div class="card">

### 闸门 B：c30/c31 表型救援 (先导物变构机制第二证据链)
* **WT 受体上的活性断崖复现**：
  * 测定 c30 vs c31 浓度反应曲线，复现文献报道的 **48 倍活性断崖**（验证 Glu153 负电门控）。
* **E153A 突变体上的特异性救援 (Rescue)**：
  * 在 E153A 上，c31 的 N-3 静电排斥被消除，**c31 活性被特异性救援**（c30/c31 差距显著收窄）；
* **成果价值**：无需共晶结构，即可在功能与同系物水平双重锁死变构假说。

</div>
</div>

---

## 10. 权威文献、校验 PDB 结构与共享盘交付清单

<div style="font-size:14.5px;">

* **结构学审计基准 (RCSB PDB)**：
  * **8Z8A** (2.82 Å, 冷冻电镜): 人源 HCAR1-Gi1 偶联内源乳酸活性态复合物 (*Sci Signal* 2026, PMID: 41435849)。
  * **9KT9** (冷冻电镜): 人源 HCAR1-Gi1 偶联 3,5-DHBA 正构对照复合物。
  * **8J6P** (2.60 Å, 冷冻电镜): 人源 HCAR2-Gi1 偶联烟酸与变构激动剂 9n (*Nat Commun* 2023, PMID: 37993467)。
* **关键药理学参考文献**：
  * Lind et al., *Br J Pharmacol* 2026 (PMID: 41435849): ebBRET 传感器生物学证实 GPR81 agonist 1 为 ago-PAM。
  * Davidsson et al., *Bioorg Med Chem Lett* 2020 (PMID: 31932225): 阿斯利康 AZ1 与吡啶酮变构系列发现。
* **共享盘交付文件 (Windows CIFS R: 盘路径)**：
  * 中文幻灯片 (PPTX & PDF): `R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\gpr81_binding_modes_deck_zh.pptx` & `.pdf`
  * 英文原版幻灯片: `R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\gpr81_binding_modes_deck.pptx` & `.pdf`
  * 干实验基准原始数据 (JSON): `R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\dry_lab_benchmark_summary.json`
  * Jira 任务追踪: **RIC-396** (已登记在 Comment 101714)

</div>
