# TSPO 配体靶点评估项目 — 方法沉淀与结论综述（RIC-408 系列）

> 日期：2026-10-20。覆盖 2026-10-14 至 2026-10-20 六轮工作（ws1–ws7 + FEP-A）。
> 请求人：Zheng Cao（RIC-408 卡 + 邮件）。交付物全部在 CIFS `R:\DT\TDE_TV\shared_folder\QYJI\druggability\TSPO_assessment\`（01–06 + 90_archive），代码在 `TSPO_assessment/`。
> 关联：[docs/binding-structure-assessment.md](binding-structure-assessment.md)（结构能力总表）、用户级 skill `ligand-target-fishing`（协议正文）、`small-molecule-docking-validation`（协议正文 + references/tspo-ie-audit-and-annihilation-scanning.md 坑日志）。

## 一句话结论

以 PK11195 为锚的 TSPO 配体靶点评估跑通了「curation → 门禁对接 → MD 姿态稳定性 → 湮灭式 TI（computational alanine scanning）」完整方法链，并把两个非 TSPO 结论坐实到实验可验证的粒度：**CAR/NR1I3 是 PK11195 的 #2 靶点（五路独立证据收敛）**；**TSPO 二聚体界面存在第二口袋 4RYI_p26，emapunil 与 FGIN-1-27 双配体四层证据齐全**。所有计算层仅做排序与假设生成，tier 判定仍需实测数据。

## 六轮工作与关键数字

| 轮次 | 内容 | 关键数字 |
|---|---|---|
| ws1–ws4 | PK11195/emapunil/etifoxine/Ro5-4864 curation + 证据挖掘 + 门禁对接 | TSPO 4RYI −9.42 / CAR 1XVP −10.89 / PXR −7.55 → gate PASS |
| ws5 | alpidem（零 ChEMBL 记录案例）| GABA-A 6X3X −8.02、CAR −9.03 → 否决 TSPO 主张；BSEP/DILI 链 |
| ws6 | emapunil + FGIN 全链 + MD 层；fpocket 新口袋筛查 | FGIN 4RYI −8.46（0.67 Å）；OPRK1 −8.25 被 MD 否决（漂 3.1 Å）；17/17 口袋方法对照、29 novel |
| FEP-A | perses 不可用（OpenEye 授权）→ 湮灭式 TI 替代；IE 审计勘误 | 21 锚点；ASP83A +16.3 kJ/mol（OPRM1）最强单锚；4RYI 锚更换 PHE23/ASN151/MET47 → SER20/TRP49/PHE88 |
| ws7 | FGIN × 29 novel pockets（Zheng 追加） | 15/29 engaged、16/17 hit-confirmed、13/16 md-stable、57 TI 锚点 |
| 勘误 | IE 双重污染（单位 + 幽灵电荷）内联更正 | 报告 corrected* 标记 + erratum callout；对接/MD/tier 不受影响 |

## 最重要的发现（按对项目走向的影响排序）

1. **CAR = PK11195 #2 靶点**。ChEMBL（亚微摩尔拮抗）+ PubChem + SwissTarget 0.888 + 对接 1XVP −10.89 + Boltz-2 折叠复现 5.65 Å RMSD，五路独立收敛。所有 TSPO PET 示踪剂/PK11195 类配体的安全解读须纳入核受体轴（CAR/PXR → DILI、DDI）。
2. **4RYI_p26 = TSPO 二聚体界面第二口袋**。正构口袋残基重叠 <30%（novelty gate）；emapunil −7.64 / FGIN −9.17，均 3-seed 稳定；MD 姿态稳定；TI 双向坐实（emapunil MET1A +7.7 / FGIN LEU58B +7.6 kJ/mol）。实验验证路径现成：TSPO 二聚化 assay + LEU58 突变。
3. **占据率/暴露框架**：游离 Cmax vs Ki 的量级比较把"文献靶点"与"真实靶点"分开（etifoxine：0.31 nM vs 7.8 µM，10⁴ 差距排除通路）。T1–T4 分层 + "not tested ≠ non-binder" + 每行 FACT/OBS/MECH/HYP 是本项目最可复用的框架。
4. **6X3X_p78 SER196A**：两个不同化学型配体独立给出 ~+20 kJ/mol（≈1000 倍亲和力量级）的湮灭代价——唯一配体无关强锚，GABA-A TMD 新调制位点假设，实验优先级最高。
5. **分数会骗人，动力学救回**：OPRK1（−8.25 漂 3.1 Å）、ws7 的 6HUG_p114/7F61_p15/7M93_p8（≤ −7.8 但漂 4.6–8.5 Å）——MD 层否决了分数层喜欢的 pose，这是方法链按设计工作，报告中如实呈现为 computed-negative。
6. **人源 TSPO 结构缺口是领域级空白**：P30536 零 PDB entry；哺乳动物 TSPO 无配体不稳定（2MGY/2N02 需 PK11195），全场用细菌同源物。这是 4RYI 锚定合理性的依据；附 rs6971 A147T（emapunil 敏感 12.6× vs PK11195 1.2×）。

## 方法链（可复用协议）

```
curation（CID/InChIKey/ChEMBL/同义名，racemate 分开）
  → 证据挖掘（ChEMBL activities + PubChem assays + Europe PMC KO 证据 + 相似性闭包）
  → 结构臂门禁（正构口袋重 dock 回收 <2 Å + off-target 回收，PASS 后分数才可比）
  → MD 姿态稳定性（250 ps，全重原子约束 5 kcal/mol/Å²，drift ≤ 4 Å = stable）
  → 湮灭式 TI（top-3 侧链锚点 × 8 λ 窗，q/ε × (1−λ)，native_t0 = −dU/dlam|λ=0 自检）
  → tier CSV（词汇封顶：anchor/computed-md/computed-dock/computed-negative/computed-ti/skipped/untested，无 computed-positive）
  → 单测先行（tests/ 写在给用户看 CSV 之前）→ CIFS sha256 验证 → 邮件数字从终版产物重导
```

新口袋筛查专用（ws6/ws7 模板）：UniProt PDB xref 结构普查 → fpocket 全组装扫描（方法对照 = fpocket 必须复现已知口袋）→ novelty 门（<30% 残基重叠 + >3 Å 离所有配体拷贝 + DS/vol/alpha-sphere 阈值）→ scan/hit 双层对接 → MD → TI。demoted-adjacent 行保留数据内联标注。

## 方法学教训（已固化进 skill/测试，此处仅索引）

- **IE 单位与电荷污染**：Coulomb 常数必须配对单位（138.935 kJ·nm/e² 配 nm）；`SystemGenerator` 内部 Interchange 套 preset charges 会给配体幽灵净电荷（−2.1e），直用 `SMIRNOFFTemplateGenerator` + 全原子（含 H）。详见 skill reference §A。
- **perses PME 死路**：OpenEye 商业授权硬依赖，stub 骗不过 createOEMolFromSDF；湮灭式 ASA 是等价替代（回答"配体是否使用该残基"），详见 §B/C。
- **真空 MD 必须约束配体**（否则 ps 级漂移湮灭信号）、大体系必须先 minimise、1XVP/fgin 需 CUDA double precision，详见 §D。
- **零锚点伪影**：4-GPU 并发 + mixed precision 下 12/57 锚点全窗口精确 0.0（配体静默逃逸）；`test_ti_no_zero_anchors` 防复发；分析恒等式 dU/dλ|λ=0 = −native IE 是自检依据。详见 §I。
- **文件名后缀陷阱**：FGIN relaxed 文件带配体后缀导致静默加载错误配体；build 函数内打印解析路径。详见 §G。
- **CUDA 700 是进程级致命**：整 worker 丢队列；换卡不重试；盘点缺失任务而非只看 error JSON。
- **跨轮 anchor key 不一致**：ws6 无链后缀 vs fep_a3 有；跨轮解析链用最近距配体残基，勿取 chains[0]。

## 代码地图（TSPO_assessment/）

- 配体轮：`scripts/*_f0_curation.py` → `f2_docking`（+`f2d_scoreonly_gate`）→ `f4_iedecompo`/`f4final_recover` → `f5_tier_csv`；`tests/test_emapunil_dataset.py` 等 3×11 tests
- 新口袋轮：`scripts/novelq_p2_fpocket_scan.py` … `novelq_p7_report.py`（ws6）、`novelq7_p1_fgin_docking.py` … `novelq7_p6_report.py`（ws7）
- FEP-A：`scripts/fep_a3_lib.py`（核心库：build_system/dUdlam/ie_decomp，单位正确）、`fep_a3_scan.py`（CLI）、`fep_a5_summarise.py`；留档 `fep_a_mutation.py`/`fep_a_driver.py`（perses 尝试）
- 测试：`tests/` 55 个（含 `test_novelq7_dataset.py` 11 个）
- 数据：`data/emapunil_fep_selection.json`（预注册选集）、`data/novelq7_p4_jobs.json`（TI 任务清单）

## Git 提交索引（2026-10-20 沉淀）

* fae5d14 chore(tspo): extend gitignore for FEP-A/ws7 intermediates; env example model name
* 9e05bf9 feat(tspo): FEP-A annihilation alanine-scanning TI on known pockets (emapunil + FGIN)
* 6f4a34c feat(tspo): ws7 FGIN-1-27 across fpocket novel pockets — docking, MD, annihilation TI
* 632d57b docs(tspo): corrected ligand reports (IE erratum inline) + F2 gate JSONs + final deliverable copies

## 后续候选（未启动）

- FGIN 新口袋扩展已在 ws7 完成；剩余可选项：更长时程 MD（residence time 语义）需重设计，非当前优先。
- 6X3X_p78 SER196 突变 + GABA-A 电生理、4RYI_p26 LEU58 突变 + TSPO 二聚化 assay——两个 TI 驱动的实验建议已交 Zheng。
- 湿实验结果回填 tier 后，本协议链可直接复用到下一个配体系列。
