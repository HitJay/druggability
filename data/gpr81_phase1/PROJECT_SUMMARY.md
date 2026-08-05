# GPR81 / HCAR1 项目总结（简单版）

> 2026-08-04 · 请求人：Huan · 数据科学家：QYJI · 完整报告见 `gpr81_final_report.html`

## 项目是做什么的

HCAR1（GPR81）是乳酸受体，Gi 偶联，主要在脂肪组织表达，介导抗脂解。Huan 请求我们对
Davidsson 2020 (BMCL) 的 GPR81 激动剂系列做分子对接分析——包括 5 个工具化合物和论文
里的 39 个化合物，用最新的人 HCAR1 cryo-EM 结构（8Z87/8Z8A/9KT9）。

## 数据基础（已全部核实）

- **结构**：3 个人 HCAR1-Gi cryo-EM 结构（CHBA / 3,5-DHBA / 乳酸结合态）+ 1 个 apo
- **工具化合物**：AZ1（23 nM，Davidsson c1）、Takeda 激动剂（50 nM）、CHBA、3,5-DHBA、3-OBA——身份全部经 PubChem/ChEMBL 交叉确认，还纠正了一个（GPR81_agonist_1 其实是 Takeda 2014 的化合物，不是 Davidsson c2）
- **论文 39 个化合物**：全部从 PDF+补充材料恢复出结构，每个都过了 [M+H]+ 质谱校验（误差 <5 mDa），3 个有 ChEMBL 双重确认

## 三个核心发现

1. **大分子激动剂结合在 TM5-TM6 胞外区域，不在乳酸的小分子口袋里**
   Davidsson 系列（MW 460-630）在 8Z8A/8Z87 上都落在胞外区域（离 orthosteric 中心 12-14 Å），
   多 seed 共识确认。8Z87 上那些"正分"是 CHBA 构象下该区域的空间冲突，**不是不结合**
   （AZ1 是 23 nM 的强效激动剂，不可能不结合）。

2. **pyridone→pyrimidinone 的活性悬崖有了结构解释**
   c30（pyridone，5 nM）vs c31（pyrimidinone，240 nM）差 47 倍。机制：pyrimidinone 的
   环氮（N3）在 8/8 个 seed 里都落在 Glu153 羧基旁 3.8 Å 处——负负静电排斥，
   分子间能量差 ~4 kcal/mol。这是可以写进论文的计算-实验互证。

3. **HCAR1 激活的安全性有机制性风险**
   肿瘤促进/恶病质（激活驱动肿瘤诱导恶病质）+ 肝纤维化（GPR81 KO 减轻纤维化）。
   另外：最强效的 c30 对 GPR109A 选择性只有 7.4 倍（niacin flush 受体），c28 才是
   综合最优（22 nM、41× GPR109A、82× GHS-R1a）。

## 方法学上做了什么

- 发现并修复了 9KT9 的大盒子深插伪影（tight-box 协议，红对接 5.71 Å → 1.67 Å）
- 建立了三套质量门：红对接 centroid 恢复、tight-box 验证、9KT9 深插门控
- 全 39 化合物 × 2 受体全量 docking + reverse-SAR 分析（确认全局 score-EC50 无相关，
  acyl-urea 系列内有弱排序能力）

## 交付物

| 文件 | 内容 |
|---|---|
| `gpr81_final_report.html` | 综合最终报告（暗色主题，10 个 section） |
| `gpr81_initial_report.html` | 早期 Phase 1-3.5 报告（历史） |
| `REVIEW_2026-08-04.md` | 全链路审计 + P0-P3 修复记录 |
| `phase5_tightbox/` | 9KT9 修复 + c30/c31 机制验证 |
| `phase6_full_series/` | 39 化合物全量 docking + reverse-SAR |
| `safety/` | HCAR1 安全性 + 选择性转录 + HCAR2 口袋对比 |

## 给 Huan 的建议（一句话版）

大分子系列结合胞外位点的假设值得用 TM5-TM6 突变实验验证；推进化合物优先看 c28
（效价+选择性平衡），c30 需要先解决 GPR109A 选择性；临床前必须做致癌性和肝纤维化
标志物。
