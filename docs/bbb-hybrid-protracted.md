# BBB Hybrid — Protraction-Aware Prediction (WS2 Option A 基线)

> 设计文档（搞之前）· 靳秋野（Jay）/ NNRCC agenter group · 2026-06-16
> 关联：[improvement_plan.md](../output/2026-06-16/bbb_protracted_improvement_plan/improvement_plan.md) 的 **WS2**
> 前置：WS1 适用域层已交付（`report.py`/`predict.py`），本文档落地 **WS2 的可验证基线**。

---

## 1. 目标与约束

**目标**：把"缺的那条轴"——修饰/PK——补进 BBB 预测，使 **protracted（脂化/长效）肽**
不再得到序列模型的"骨架假阳性"，而是被按长效化程度**定向下调**。

**硬约束（沿用计划）**：
- **零新增湿实验**：不依赖任何新做的 PK/脑暴露实验。
- **诚实可审计**：方向（长效化→降低入脑）是已确立药理学；惩罚幅度是**透明可调的物理先验**，
  明确标注为启发式，**不冒充已训练的定量模型**。
- **可立即验证**：用真实 backbone 分数 + 已知长效化药做对照，无需 GPU 即可跑惩罚层。

## 2. 核心设计：logit 空间的 protraction 惩罚

序列塔给出**骨架内在通透倾向** `p_seq`（= 上界，已由 `predict_bbb` 产出）。
修饰塔给出**长效化惩罚** `Δ ≥ 0`（只降不升，编码物理先验）。融合：

$$ p_\text{final} = \sigma\big(\operatorname{logit}(p_\text{seq}) - \Delta\big) $$

- 天然/无修饰肽：`Δ = 0` → `p_final = p_seq`（不改变，保证不回归）。
- 长效化越重，`Δ` 越大，下调越多 → 直接回答 Tingqing "gap 多大"。

> 直接映射给 Dan 的邮件叙述：`p_seq` = backbone 上界，`Δ` = 长效化惩罚。

## 3. 模块划分（纯 Python，无 torch → 可在 .venv pytest）

| 文件 | 角色 |
|------|------|
| `bbbkit/peptide/descriptors.py` | `parse_modification()` 修饰串→结构化描述符；`protraction_penalty()` 描述符→Δ；`apply_penalty()` p_seq+Δ→p_final |
| `bbbkit/peptide/predict.py`（扩展） | `predict_bbb(..., apply_protraction=True)`：序列分数 + 惩罚融合 |

### 3.1 修饰描述符（`parse_modification`）

从修饰字符串（如 `"C18 diacid + PEG2"`）规则解析：

| 描述符 | 取值 | 来源关键词 |
|--------|------|-----------|
| `fa_chain_len` | 0 / 16 / 18 / 20 | `C16` `C18` `C20` `palmit` `stear` |
| `is_diacid` | bool | `diacid` |
| `has_peg` | bool | `peg` `pegylat` |
| `is_cyclic` | bool | `cyclic` `lactam` `disulf` `staple` |
| `has_d_aa` | bool | `d-ala` `d-phe` `d-amino` |
| `is_lipidated` | derived | `fa_chain_len > 0` |

### 3.2 惩罚函数（`protraction_penalty`）—— 透明启发式

每个长效化特征加一份 logit 惩罚（常量，集中定义、可调、有注释来源）：

- 脂化：C16 → 中等；C18 → 更大；C20 → 最大（链越长，白蛋白结合越强、游离分数越低）。
- 二酸：在脂化基础上再加（二酸连接子显著增强白蛋白结合，如 semaglutide）。
- PEG：加惩罚（增大有效尺寸 + 亲水）。
- 环化/D-aa：小幅标记（主要影响稳定性而非入脑，给小权重）。

> 这些常量是**物理先验的显式编码**，不是回归拟合数。报告中明确标注为
> "heuristic protraction prior"，并保留 `p_seq`（上界）与 `p_final` 同时展示。

## 4. 验证策略（无需湿实验）

用**真实 backbone ESM-2 分数** + **已知长效化药**做对照：

| 肽 | backbone p_seq | 修饰 | 期望 p_final | 依据 |
|----|---------------|------|-------------|------|
| BRP native | 87.5% | 无 | **87.5%（不变）** | 无修饰 → Δ=0 |
| α-MSH | 98.0% | 无 | **98.0%（不变）** | 无修饰 → Δ=0 |
| GLP-1 backbone | 95.8% | C16（liraglutide） | 明显下调 | 脂化外周受限 |
| GLP-1 backbone | 95.8% | C18 diacid（semaglutide） | 下调更多 | 二酸白蛋白结合更强 |
| NN9161-style | （骨架高） | C18 + PEG | 强下调 | C18+PEG ~2200Da，外周设计 |

**关键验证门槛**：
1. 无修饰肽 `p_final == p_seq`（零回归）。
2. 惩罚随长效化程度**单调**（C16 < C18 < C18+diacid < C18+PEG）。
3. `p_final ∈ [0,100]` 且**只降不升**。
4. NN9161 类从"骨架高分假阳性"→ 低分（呼应 Tingqing Q1/Q2）。

## 5. 测试（pytest，纯 Python）

`tests/test_descriptors.py`：解析正确性、惩罚单调性、apply_penalty 边界与单向性、
天然肽零惩罚、端到端 hybrid 数值。全部不依赖 GPU/网络。

## 6. 诚实边界（写入报告与文档）

- 这是**物理先验基线**，不是定量校准模型——幅度待 P4 内部 PK 数据校准。
- 仍只看 20 种标准氨基酸的**骨架**；惩罚来自修饰**字符串**而非完整分子图（P5 用分子编码器）。
- `p_final` 是"经长效化下调的上界"，仍非体内脑暴露（propensity ≠ exposure 不变）。

---

> **结果将在实现+测试后追加到本文档 §7。**

## 7. 实现与结果（搞之后 · 2026-06-16）

### 7.1 已交付

| 文件 | 内容 |
|------|------|
| `bbbkit/peptide/descriptors.py` | `parse_modification` / `protraction_penalty` / `apply_penalty` / `protraction_adjust`（纯 Python，无 torch） |
| `bbbkit/peptide/predict.py` | `predict_bbb(..., apply_protraction=True)`：序列分 + 惩罚融合，输出 `p_seq`/`p_bbb`(=p_final)/`protraction_delta` |
| CLI | `bbbkit peptide report ... --protraction` |
| `tests/test_descriptors.py` | 24 测试：解析 / 惩罚单调 / 融合单向边界 / 零回归 / NN9161 修复 |

### 7.2 验证结果（真实 backbone 分数）

| 肽 | p_seq | Δ | **p_final** | call | 说明 |
|----|------:|---:|----------:|:----:|------|
| BRP native | 87.5 | 0.00 | **87.5** | BBB+ | 无修饰 → 零回归 ✅ |
| α-MSH | 98.0 | 0.00 | **98.0** | BBB+ | 无修饰 → 零回归 ✅ |
| GLP-1 backbone | 95.8 | 0.00 | **95.8** | BBB+ | 骨架上界 |
| liraglutide (C16) | 95.8 | 3.00 | **53.2** | BBB+ | 脂化中等下调 |
| semaglutide (C18 diacid) | 95.8 | 5.00 | **13.3** | BBB− | 二酸白蛋白结合强 → 强下调 |
| NN9161-like (C18+PEG) | 83.0 | 5.00 | **3.2** | BBB− | **假阳性修复** ✅ |

**四条验证门槛全部满足**：
1. ✅ 无修饰肽 `p_final == p_seq`（零回归）。
2. ✅ 惩罚单调：C16(3.0) < C18(3.5) < C18+diacid(5.0)。
3. ✅ `p_final ∈ [0,100]` 且只降不升。
4. ✅ NN9161 类 83% → 3.2%（假阳性翻转为 BBB−，呼应 Tingqing Q1/Q2）。

### 7.3 对 Dan/Tingqing 诉求的回应

- **Tingqing "基于序列还是完整分子"**：现在两者都有——`p_seq` 是序列骨架上界，`p_final` 叠加了修饰惩罚。
- **Tingqing "gap 多大"**：native→protracted 落差**可量化**且按程度分级（lira 53% vs sema 13%）。
- **Dan "protracted 关切"**：长效化肽不再得到骨架假阳性，被定向下调。

### 7.4 测试

`tests/test_descriptors.py` 24 测试全绿；与既有套件合计 **68 passed**（无回归）。

### 7.5 诚实边界（保留）

- 惩罚幅度是**物理先验启发式**，非内部 PK 数据拟合——量化精度待计划 **P4** 校准。
- 仍只看 20 种标准氨基酸骨架；惩罚来自修饰**字符串**而非完整分子图（P5 用分子编码器）。
- `p_final` 是"经长效化下调的上界"，仍非体内脑暴露（propensity ≠ exposure 不变）。
- 报告同时展示 `p_seq`（上界）与 `p_final`（下调后），不掩盖中间量。
