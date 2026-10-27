# humanPPI_repro — Zhang et al., Science 2025 方法复现

复现论文: "Predicting protein-protein interactions in the human proteome"
Jing Zhang, Ian R. Humphreys, ..., David Baker, Qian Cong.
Science 390(6771), eadt1630 (2025). DOI: 10.1126/science.adt1630
PMCID: PMC13281779

## 复现范围（边界声明）

论文全量工作 = 30PB 基因组/SRA 数据挖掘 (omicMSAs) + AFDB 2 亿结构蒸馏 DDI
训练集 + 训练 RF2-PPI + 2 亿蛋白对筛选。单组算力不可行,也不必要:

1. omicMSAs 是作者正式交付物(conglab.swmed.edu 公开下载),直接使用 =
   使用论文的方法产物,等同用作者的试剂跑他们的方法。
2. 不重训 RF2-PPI(DDI 训练集 330GB + PPI 训练集 226GB + 多卡训练数周);
   使用官方权重 RF2-PPI.pt,复现"推理+基准评估"闭环。
3. 全量 2 亿对筛选(约 4700 万对进入 DL 阶段)不硬复现;以论文自建的
   3,000 阳性 / 30,000 阴性 benchmark 做端到端打分与 PR 曲线复现
   (对应 Fig. 1E-G / Fig. 2D),并与作者释放的 RF2-PPI_scores 抽样对拍。

## 目录结构

    refs/                  论文 PDF、补充材料(方法 M1-M6)
    external/              第三方代码 (RoseTTAFold2-PPI, GPL-3.0, 不修改)
    downloads/             官方大文件 (权重/benchmark/omicMSA),不入 git
    data/                  benchmark 解包与整理
    work/                  中间产物 (pMSA、npz 打分),不入 git
    scripts/               本复现的管线脚本
    results/               PR 曲线、对拍表
    reports/               复现报告

## 复现步骤

0. 环境: conda env `rf2ppi` (python 3.9, torch 1.12.1+cu113, hhsuite)。
   官方另提供 SE3nv-20230612.sif (14GB) singularity 镜像,为备选。
1. Sanity: 官方 examples 输入跑通,对拍 examples/expected_output。
2. pMSA: 用 generate_protein_pair_MSA.py 从 protein_omicMSAs 为 benchmark
   33,000 蛋白对生成 paired MSAs (pairing -> 去 unpaired -> hhfilter 90%)。
3. 打分: RF2-PPI (src/predict_list_PPI.py) 多 GPU 分片批跑,断点续跑。
4. 评估: 加权 PR 曲线 (正例权重 0.01, S/N=1:1000, 论文 Fig.1 公式),
   复现 RF2-PPI @ 90% precision 的 recall;与作者 RF2-PPI_scores 抽样对拍。

## 关键外部资源

- 代码: https://github.com/CongLabCode/RoseTTAFold2-PPI
- 权重: https://conglab.swmed.edu/humanPPI/downloads/RF2-PPI.pt (296MB)
- benchmark: https://conglab.swmed.edu/humanPPI/downloads/benchmarks.tar.gz
- omicMSA: protein_omicMSAs.tar.gz (17GB) / segment_omicMSAs.tar.gz (12GB)
- 作者结果: RF2-PPI_scores.gz (423MB), final_predictions.tar.gz (14MB)
- 补充材料(方法): PMC13281779 supplemental_text_and_figures.pdf

## 状态

见 reports/ 下复现报告(完成后生成)。
