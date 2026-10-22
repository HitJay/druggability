---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TSPO Ligands – Target Search Assessment'
footer: 'RIC-408 · Computational Sciences · 2026-10-22'
style: |
  section { font-size: 22px; padding: 40px 60px; }
  section.title { font-size: 30px; text-align: center; }
  section.title h1 { font-size: 44px; }
  h1 { font-size: 32px; margin-bottom: 8px; color: #003a70; }
  h2 { font-size: 26px; color: #003a70; border-bottom: 2px solid #003a70; padding-bottom: 4px; }
  h3 { font-size: 22px; color: #00518a; }
  table { font-size: 16px; border-collapse: collapse; margin: 8px 0; }
  th { background: #003a70; color: #fff; padding: 4px 8px; }
  td { padding: 3px 8px; border: 1px solid #ccc; }
  blockquote { font-size: 18px; color: #555; border-left: 4px solid #003a70; }
  code { background: #f0f0f0; padding: 1px 4px; }
  ul, ol { margin: 4px 0; }
  li { margin: 2px 0; }
  .highlight { color: #c0392b; font-weight: bold; }
  .good { color: #27ae60; font-weight: bold; }
  .warn { color: #e67e22; font-weight: bold; }
  .fact { color: #27ae60; font-weight: bold; }
  .obs { color: #e67e22; font-weight: bold; }
  .hyp { color: #c0392b; font-weight: bold; }
  .small table { font-size: 14px; }
---

<!-- _class: title -->

# TSPO Ligands
## Target Search – What Drives the Reported Metabolic Phenotypes?

**Requestor**: ZHCO, Group 3 TSPO proposal
**Campaign**: 2026-10-14 → 10-20 (7 workstreams) · deck updated 2026-10-22
**RIC-408** · Analyst: Jin Qiuye (Computational Sciences)

Ligands: **PK11195** · **Emapunil (XBD173)** · **Etifoxine** · **Alpidem** · Ro5-4864 (control)

Full report: `tspo_ligand_target_search_report.html` — all claims tagged <span class="fact">FACT</span> / <span class="obs">OBS</span> / <span class="hyp">MECH / HYP</span> with sources per row

<!-- Note (CN): 开场——这次不讲算法，讲一个药理学问题：三个"TSPO配体"的代谢表型到底是不是TSPO介导的。结论先行：PK11195指向肝脏CAR，emapunil是唯一干净的TSPO故事但代谢证据空缺，etifoxine在临床暴露下TSPO排除、大概率走肠道菌群。10-16后新增结构验证阶段（对接→MD→TI），第5页讲第二口袋与两个突变实验建议。 -->

---

## 1. Background and Objective

**TSPO** (translocator protein, 18 kDa) is an outer mitochondrial membrane protein:

- Cholesterol transport; classic **PET neuroinflammation marker**
- Human tissue expression (GTEx): highest in **adipose**, then colon / liver / hypothalamus
- Open Targets human genetics: TSPO **not** flagged for T2D or obesity

The proposal cites metabolic benefits for three clinical TSPO ligands:

<div class="small">

| Compound | Reported metabolic phenotype | Source |
|---|---|---|
| **PK11195** | Glucose-lowering, anti-steatotic (preclinical) | PMID:23201900 |
| **Emapunil** | T2D benefit claimed (citation pending) | — |
| **Etifoxine** | Weight loss in diet-induced obese mice | PMID:32679124 |

</div>

> **Question**: for each ligand, which target can the phenotype actually run through **at real-world exposure**?
> **This analysis**: measured binding (ChEMBL + PubChem) × literature × tissue expression × disease genetics × docking validation gate.

<!-- Note (CN): 立项假设是TSPO介导代谢获益，我们做无偏靶点搜索来压力测试。TSPO背景一句话带过；关键铺垫：遗传学不支持TSPO作为T2D/肥胖驱动基因。 -->

---

## 2. Methods — Evidence Map: Five Method Families, One Evidence Ladder

**The claim under test**: "this ligand binds X" vs "X explains the phenotype" needs <span class="highlight">independent confirmation + exposure plausibility</span>. Five method families feed a two-gate evidence ladder:

<div class="small">

| Method family (what it measures) | What it can / cannot do | Role in the ladder |
|---|---|---|
| ① Measured binding — ChEMBL + PubChem (biochem / cell / qHTS) | Real K<sub>i</sub>/IC<sub>50</sub> per target; says nothing about in-vivo relevance | Gate 1 (binds, sub-µM) |
| ② Literature mining — Europe PMC (phenotypes + KO counter-evidence) | Captures effect direction & KO counter-evidence; not systematic | Gate 1 + direction |
| ③ Tissue expression (GTEx) + disease genetics (Open Targets) | Places targets in the right organ & disease context; correlation only | Gate 1 + context |
| ④ Docking (Vina, validation-gated) + similarity (SwissTargetPrediction) | Independent structural / chemotype confirmation; potency ranking unreliable | Gate 1 confirmation only |
| ⑤ Exposure / occupancy math (free C<sub>max</sub> vs K<sub>i</sub>) | Separates "binds in a test tube" from "occupied in a patient" | Gate 2 (occupancy) |

</div>

**Two-gate ladder**: <span class="good">Gate 1</span> = confirmed sub-µM binding + right tissue / disease context → shortlist · <span class="good">Gate 2</span> = occupancy at real exposure → carries the phenotype. <span class="good">Added 2026-10-16+</span>: docking shortlists further validated by <span class="good">MD pose stability</span> (drift ≤ 4 Å) → <span class="good">annihilation TI</span> / computational alanine scanning. Scores rank; dynamics + TI decide.

> QC: docking **validation gate** (PK11195 redock into its own TSPO pocket — PASS) · DrugCLIP reverse **failed its decoy gate** → excluded · every claim tagged FACT / OBS / MECH / HYP with source per row.

<!-- Note (CN): 方法页——五家族证据图谱：①实测结合(ChEMBL+PubChem)②文献挖掘(EPMC+KO反向证据)③组织表达GTEx+遗传学OT④对接验证门+SwissTarget相似性⑤暴露量/占据率计算。两级门：Gate1=独立确认的亚微摩尔结合+正确组织/疾病语境→进短名单；Gate2=真实暴露下占据可行→才能承载表型。质量控制：对接验证门PASS；DrugCLIP反向门禁失败（decoy排名高于真配体）→排除出结论；每条结论带FACT/OBS/MECH/HYP标签。新增：对接短名单加结构验证臂——MD姿态稳定性(250 ps,漂移≤4 Å=稳定)→湮灭式TI/computational alanine scanning(top-3锚点×8 λ窗)；分数排序，动力学+TI定夺。 -->

---

## 3. PK11195 — the Phenotype Points to CAR, Not TSPO

<span class="fact">FACT</span> **CAR (NR1I3), a liver nuclear receptor — the strongest non-TSPO target**, confirmed by **five independent method families**:

| Evidence | Result | Source |
|---|---|---|
| CAR binding (biochem + cell) | antagonism **25–56 nM**; inverse agonism 245–390 nM | ChEMBL (2 assay families) |
| CAR binding (qHTS) | 0.025–0.39 µM actives | PubChem |
| Docking, CAR LBD | **−10.89** kcal/mol (vs TSPO −9.42 in own co-crystal pocket) | Vina validation gate: PASS |
| Similarity prediction | CAR ranked **#2** (0.888), just behind TSPO (0.899) | SwissTargetPrediction |
| Complex fold (Boltz-2, CAR LBD + PK11195) | reproduces the co-crystal pose, **5.65 Å RMSD** | Boltz-2 |

> In hepatocytes, metabolism converts PK11195 from a CAR **antagonist** into an **agonist**, inducing CYP2B6 / CYP3A4 (PMID:28442602). CAR is liver-specific: **98.7 TPM in liver, <1 elsewhere** (GTEx).

**Two independent lines argue against a TSPO-mediated benefit:**

- <span class="obs">OBS</span> TSPO-knockout rats on high-fat diet show **worse** steatosis and insulin resistance (PMID:40195072)
- <span class="obs">OBS</span> PK11195 **inhibits** glucose-induced insulin secretion in isolated islets (PMID:10935532)

> **Key finding**: the phenotype fits **hepatic CAR activation + a fasting-like state** — not TSPO.

<!-- Note (CN): 核心页，多停留。CAR五来源验证（ChEMBL生化+细胞、PubChem qHTS、Vina、SwissTarget、Boltz-2折叠复现5.65 Å），肝细胞代谢翻转成激动剂。KO大鼠反向+胰岛分泌抑制是主动跑反向假说的结果。被追问docking细节就指向报告第8-9节。 -->

---

## 4. Emapunil & Etifoxine — Two Different Verdicts

<div class="small">

| | **Emapunil (XBD173)** | **Etifoxine** |
|---|---|---|
| TSPO affinity | Ki **6.4 nM** WT / 31.3 nM A147T; >1,000× selective | Ki **7.8 µM** (human) |
| Free plasma, clinical dose | **1.0 nM** (90 mg qd) | **0.31 nM** (50 mg tid) |
| TSPO occupancy | ~13% WT / ~3% A147T ✅ | **<0.01%** ❌ (~4 orders of magnitude gap) |
| Other measurable targets | none (GABA-A central site 8.4 µM) | GABA-A TBPS site 6.7 µM; CYP / DRD2 µM band |
| Metabolic evidence | **No T2D / obesity study found** in public data ⚠️ | Weight loss tracks **gut microbiome / bile-acid axis** (PMIDs 32679124, 38075272) |

</div>

- **Emapunil** — the clean TSPO story: occupancy-competent, cognition effects proven TSPO-dependent (TSPO-KO mice, PMID:37891168); the metabolic claim itself is unproven. <span class="hyp">HYP</span> Indirect route: endogenous **DBI / endozepine axis** (high in liver / adipose / hypothalamus; insulin-triggered, PMID:40976282)
- **Etifoxine** — mouse weight-loss dose (50 mg/kg i.p.) is allometrically in the same exposure league → TSPO route unlikely; the relevant GABA-A subunit is **CNS-restricted** (GTEx), so no peripheral metabolic route

> <span class="good">Emapunil</span>: TSPO-competent, phenotype citation missing · <span class="highlight">Etifoxine</span>: TSPO excluded at real exposure

<!-- Note (CN): emapunil干净但代谢证据空缺，需要ZHCO给引用；rs6971 A147T携带者Ki掉约5倍(6.4→31.3 nM)，occupancy从13.5%掉到3.1%。etifoxine关键数字：Ki 7.8 µM vs 游离血浆0.31 nM，差4个数量级；人5天交叉试验有菌群变化，是唯一人体证据。 -->

---

## 5. Beyond the First Report — TSPO Structural Findings & Suggested Experiments

**MD + annihilation TI (computational alanine scanning) across the docking shortlists** — 21 anchors on known pockets (emapunil + FGIN-1-27), 57 anchors across 29 novel pockets.

<div class="small">

| Finding | Evidence | Suggested experiment |
|---|---|---|
| **4RYI_p26 — second pocket at the TSPO dimer interface** (<30% residue overlap with the canonical pocket) | Emapunil −7.6 / FGIN −9.2 kcal/mol; MD-stable (3 seeds); TI confirmed both ways: MET1A +7.7 / LEU58B +7.6 kJ/mol | **LEU58 mutation + TSPO dimerization assay** |
| **6X3X_p78 SER196** — ligand-independent strong anchor on a GABA-A TMD pocket | Two chemotypes independently ≈ **+20 kJ/mol** (~1000× affinity cost) at the same residue | **SER196 mutation + GABA-A electrophysiology** |
| Scores mislead; dynamics rescues | OPRK1 −8.25 drifts 3.1 Å; 3 further ws7 pockets drift 4.6–8.5 Å → rejected | — (method working as designed) |

</div>

> All computed layers rank and generate hypotheses only — tier verdicts need measured data. Full results handed to ZHCO (corrected reports carry an inline IE erratum; docking / MD / tier numbers unaffected).

<!-- Note (CN): 10-16后新增的结构验证阶段一页讲完：MD姿态稳定性+湮灭式TI，已知口袋21锚点+新口袋57锚点。两个最重要发现：①TSPO二聚体界面第二口袋4RYI_p26（emapunil+FGIN双配体四层证据，实验路径现成：LEU58突变+二聚化assay）；②6X3X_p78 SER196两个化学型独立+20 kJ/mol≈千倍亲和力代价（唯一配体无关强锚，GABA-A TMD新调制位点，实验优先级最高）。两个突变实验建议已交ZHCO。边界：所有计算层只做排序和假设生成，tier判定仍需实测数据。 -->

---

## 6. Bottom Line for the Proposal

| Ligand | Most plausible driver of the phenotype | TSPO at real exposure | Verdict |
|---|---|---|---|
| **PK11195** | **CAR activation (liver)** + fasting-like hepatic state | Binding yes; benefit attribution disputed | <span class="warn">⚠️ Do not cite as TSPO evidence</span> |
| **Emapunil** | TSPO — but metabolic effect unproven; DBI-axis hypothesis | Yes (~13% WT / ~3% A147T) | <span class="good">✅ Only testable TSPO story</span> |
| **Alpidem** | GABA-A benzodiazepine site (docked −8.0, below clinical exposure); TSPO unlikely | Unlikely (dose-limited) | <span class="highlight">❌ TSPO claim rejected</span> |
| **Etifoxine** | Gut microbiome / bile-acid axis | No (<0.01%) | <span class="highlight">❌ TSPO excluded at exposure</span> |
| Ro5-4864 | TSPO-selective class control, co-phenotyped with PK11195 | — | Control ligand |

**What this changes for the proposal**

1. Do not cite PK11195's glucose / steatosis phenotype as TSPO evidence — **CAR** is the evidence-backed route.
2. Emapunil is the only ligand where a TSPO-mediated metabolic effect is both occupancy-competent and cleanly testable.
3. Etifoxine's weight-loss readout should not be used as TSPO evidence — exposure never reaches TSPO.

> **Asks for the team**: emapunil / PK11195 T2D citations · which PK11195 enantiomer the proposal assumes · internal islet / adipose TSPO expression or PET data

<!-- Note (CN): 收尾三句话：PK11195别默认归因TSPO；emapunil是唯一可检验的TSPO代谢故事；etifoxine的减重读出不能当TSPO证据。第二轮：alpidem加入且TSPO主张被否决；结构阶段发现第二口袋+两个突变实验建议（SER196/LEU58）。要三样东西：两篇T2D引用、对映体假设、内部表达/PET数据。全表在ws4_tiered_targets_v0.3.csv，逐行证据在报告HTML。 -->
