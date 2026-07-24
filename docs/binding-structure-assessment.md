# Binding / 结构评估能力 — 现状盘点

> 日期：2026-07-24
> 目的：把过去几周陆续跑通的"结构预测 + 结合评估"相关脚本/流水线做一次系统盘点，固化为可复用能力，供后续靶点项目直接调用。
> 关联：[docs/biolib-druggability-integration.md](biolib-druggability-integration.md)（BioLib 接入记录）、[output/2026-06-29/boltz_function_research/boltz2_function_research.md](../output/2026-06-29/boltz_function_research/boltz2_function_research.md)（Boltz-2 功能研究）、`research/boltz2-mmgbsa` skill。

## 一句话结论

现在可以从"靶点+配体/肽序列"直接跑到**复合物结构 + 结构置信度 + （小分子）结合概率/亲和力值 + MM/GBSA 结合自由能**，并且已经在三个真实项目（GIP/GCGR 交叉反应性、GHSR 反向激动剂虚拟筛选、GRB10 PPI 小分子筛选）里验证过全流程。**但两条读数（Boltz-2 `iptm` 结构置信度、MM/GBSA 单构象 ΔG）都只是结构合理性代理指标，不是验证过的结合强度排序——已经用同源阴性对照（secretin）证实过这一局限，任何汇报都必须带上这条免责声明。**

## 能力矩阵

| 能力 | 工具/路径 | 验证状态 | 产出 | 局限 |
|---|---|---|---|---|
| 复合物结构预测（蛋白-蛋白/肽-受体） | BioLib `@nn/DCD/Boltz-2:0.0.37` | ✅ 生产可用 | `.cif` 结构 + confidence JSON (`iptm`/`ptm`/`complex_plddt`/`pae`/`pde`) | 无 ligand 时 `ligand_iptm=0`；iptm 是结构置信度，不是结合强度 |
| 小分子-蛋白亲和力预测 | 同上，YAML `properties.affinity` | ✅ 已用于 GHSR top hits 交叉验证 | `affinity_probability_binary`（binder概率）+ `affinity_pred_value`（log10 IC50 近似） | 仅支持单一 small-molecule binder；ligand≤128原子；跨骨架绝对排序不可靠 |
| MM/GBSA 结合自由能（肽-受体） | 本地 OpenMM 8.3 + PDBFixer + GBn2 隐式溶剂，`run_mmpbsa_minimized.py` | ✅ 已跑通 9 组肽-GPCR 复合物 | ΔG_binding (kcal/mol，minimized single-point) | 单构象、无采样/无熵项；未minimize直接算会有数千kcal/mol的碰撞伪能量，已修复但仍是粗筛 |
| 大规模小分子对接虚拟筛选 | BioLib `@nn/SmallMolecules/AutoDock-Vina`，本地 `vina` Python binding | ✅ 生产可用，GHSR 项目跑过 7931 个化合物 × 2 受体状态 | Vina score (kcal/mol) + 分类标签 + 排名 CSV | 打分函数固有误差；需要阳性/阴性对照校验（见下） |
| 对接结果 + Boltz-2 交叉验证 | `submit_ghsr_boltz_crossval.py` | ✅ 已用于 GHSR top hits | Vina ΔScore 与 Boltz binder probability 的 Spearman 相关性 | 两个都是计算预测，相关性高只说明方法一致，不等于实验验证 |
| Scaffold 聚类 / 结果去冗余 | `scripts/scaffold_clustering.py`（RDKit Murcko/Bemis-Murcko） | ✅ 生产可用 | scaffold-level 分组 CSV/JSON | — |
| PPI/adaptor 蛋白小分子筛选全链路 | GRB10 项目：ChEMBL种子库→Vina→Boltz-2→AI pose review v3→细胞可穿透性打分→liability筛查 | ✅ 全流程跑通，产出可讨论候选（hymecromone） | 多层筛选评分表 + 候选评审报告 | 目前是"计算假设"，未经生化/细胞实验确认，报告中明确标注不可称为"hit" |
| 相对结合自由能 (RBFE/FEP) | OpenFE + OpenMM，GRB14 项目 | ⚠️ 仅 smoke test，非生产 | 网络规划 + 极简参数下的执行验证（3 lambda窗/0.001ns，无科学意义） | complex leg 未产出正式结果；需要真实 lambda/replica/ns 设置重跑 |
| Embedding 检索式虚拟筛选 (DrugCLIP) | 官方 repo + Uni-Core，独立 venv | ⚠️ 环境/CLI 验证通过，未产出生产筛选结果 | import/CLI smoke test 通过；checkpoint+数据下载完成 | 尚未接入实际化合物库产出候选 |

## 典型工作流

### A. 结构+亲和力预测（Boltz-2 via BioLib）

```yaml
# 输入 YAML（去掉 msa 字段让远端自动生成）
version: 1
sequences:
  - protein:
      id: A
      sequence: <receptor sequence>
  - protein:              # 或 ligand: {smiles: ...} 做小分子亲和力
      id: B
      sequence: <peptide sequence>
```

```python
import biolib
b = biolib.load("@nn/DCD/Boltz-2:0.0.37")
job = b.run(input=str(yaml_path), recycling_steps="1",
            diffusion_samples="1", sampling_steps="50",
            biolib_check=False, biolib_stream_logs=False)
job.save_files(dest_dir, overwrite=True)  # 注意过滤 predictions/boltz/novocif/ 子目录
```

产出读数解读：

- `confidence_score` / `iptm` / `complex_plddt`：结构置信度聚合分数，**不是**结合强度。
- `affinity_probability_binary`：0-1 binder 概率，适合 hit discovery 粗筛。
- `affinity_pred_value`：≈`log10(IC50 [µM])`，适合同一化学系列内部排序，不适合跨骨架绝对比较。ΔG ≈ (6−y)×1.364 kcal/mol。

### B. MM/GBSA 结合自由能（本地 OpenMM）

```python
FF = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")  # OpenMM 8.3 起 implicitSolvent kwarg 已移除，须用组合力场文件
system = FF.createSystem(topology, nonbondedMethod=app.NoCutoff, constraints=None)
```

流程：CIF → 清洗 PDB（非标准残基如 AIB→ALA）→ PDBFixer 补原子/加氢 → 能量最小化（SD + L-BFGS）→ GBn2 单点能 → 拆分链分别重复上述步骤 → `ΔG = E(complex_min) − ΣE(chain_min)`。**未 minimize 直接打分会得到数千 kcal/mol 的碰撞伪能量，是最容易踩的坑。**

### C. 大规模小分子虚拟筛选（AutoDock Vina）

GHSR 反向激动剂筛选实例：7931 个 ChEMBL 化合物 × 2 个受体构象（7F83 inactive / 8JSR active），exhaustiveness=8，按 `ΔScore = score(inactive) − score(active)` 分类：

| 分类 | 数量 |
|---|---:|
| strong_inverse_agonist | 3325 |
| moderate_inverse_agonist | 2268 |
| pan_binder | 1021 |
| other | 766 |
| active_state_preferring | 279 |
| weak_binder | 179 |
| agonist_like | 93 |

阳性对照校验（4 个已知配体中，仅 1 个正确分类）——**这说明当前 Vina 打分函数在本受体系统上的判别力有限，排名结果只能做初筛，高优先级化合物必须叠加 Boltz-2 交叉验证 + 结构复核，不能单独作为结论**。

## 关键踩坑（供复跑参考）

1. **OpenMM 8.3 API 断裂**：`implicitSolvent=app.GBn2` 参数已移除，改用 `ForceField("amber14-all.xml", "implicit/gbn2.xml")` 双文件写法。
2. **未 minimize 直接算能量** → 碰撞产生数千 kcal/mol 伪能量，必须先 SD 再 L-BFGS 两段最小化。
3. **BioLib `msa: empty`** 在部署版会被当成文件名而不是"强制单序列"信号——直接省略 `msa` 字段让远端自动处理。
4. **`predictions/boltz/` 含 `novocif/` 子目录**，天真的 `shutil.copy2` 会因为它是目录而报 `IsADirectoryError`，下载时要过滤 `f.is_file()`。
5. **同源肽负对照的 Boltz-2/MM-GBSA 局限（重要）**：GIP/GCGR/GIPR 交叉反应性项目里，与 GIPR/GCGR 无已知生物学活性的 secretin，其 Boltz-2 `iptm`（0.93+）反而**高于**全部真实激动剂对照，MM/GBSA ΔG 也落在真实结合对的同一区间而非明显更弱。结论：iptm 只反映"这是不是一个合理的 class-B GPCR 肽激素结合构象"，不反映"这条肽是不是真的能激活/结合这个受体"；单构象 ΔG 是粗筛级别的方向性证据，不是验证过的亲和力排序。**任何用到这两个读数的报告都必须显式写出这条局限。**
6. **BioLib 配对 MSA 对特定序列组合有确定性 bug**：某些 peptide+receptor 组合会反复交替报 `MMseqs2 API is giving errors` / `KeyError: '>'`，换 ID 或调整链顺序均无效——这是该序列对的可复现 edge case，不是网络抖动。约 5 次重试后应换用同源家族的替代阴性对照（如本项目用 secretin 替代反复失败的 GLP-1 对照）。先单独提交 monomer 验证问题出在配对 MSA 而非序列本身。
7. **DrugCLIP 不是 PyPI 上的 `drugclip` 包**——那是同名但不同的包；本能力用的是官方 GitHub repo (NeurIPS 2023 official code)，需要从源码装 Uni-Core，且新版 `setup.py` 要用 `--enable-cuda-ext` 而不是旧文档里的 `--disable-cuda-ext`。

## 已验证的项目案例

| 项目 | 目录 | 用到的能力 |
|---|---|---|
| GIP/GCGR/GIPR 交叉反应性评估 | `output/2026-07-23/gip_assessment/` | Boltz-2 结构预测 + MM/GBSA ΔG，含同源阴性对照(secretin) |
| GHSR 反向激动剂虚拟筛选 | `output/2026-07-10/ghsr_inverse_agonist_docking/` | AutoDock Vina 大规模筛选 + Boltz-2 交叉验证 + 阳性对照 |
| GRB10 PPI 小分子筛选 | `output/2026-06-29/grb10_inhibition_cmpd_research/`、`output/2026-06-30/grb10_*` | Vina 对接 + Boltz-2 + AI pose 评审 v3 + 细胞可穿透性 + liability 筛查 全链路 |
| GRB14 FEP 方法探针 | `output/2026-07-01/grb14_openfe_fep_probe/` | OpenFE/OpenMM RBFE smoke test（仅方法验证，非生产结果） |
| DrugCLIP 环境安装 | `output/2026-07-02/drugclip_install_probe/` | Embedding 检索式虚拟筛选工具链（环境就绪，待接入生产筛选） |

## 下一步建议

1. 把 MM/GBSA pipeline 从"单构象"升级为多构象/短MD采样，至少给出方向性置信区间。
2. 把 Boltz-2 + Vina 交叉验证的阳性/阴性对照校验做成标准前置步骤，写进复用脚本而不是每个项目临时写。
3. DrugCLIP 接入一次真实生产筛选，验证其相对 ChEMBL 种子库 + Vina 的增量价值。
4. GRB14 FEP 补齐真实 lambda/replica/ns 参数，产出第一个生产级 RBFE 结果。
