# Monthly Report — 2026/06 (QYJI)

**Date:** 2026/06/30
**Author:** Jin Qiuye (Jay) — QYJI
**Period:** 2026-05-28 → 2026-06-25

---

| Category | List of activities | Brief description | Relevant links/files |
|---|---|---|---|
| **Capability** | **HepG2 EE — DRUG-seq × imaging cross-modal MoA + vAssay leak-proof benchmark** | 1. **1440-well three-modality alignment** with zero gaps: DRUG-seq transcriptomics × C24 imaging (DINOv2 384-dim + Seahorse prediction) × TMRM mechanism axis. Pipeline + tests in vCell (24/24 passed). <br>2. **vAssay model review — label-leak diagnosis**: traced random R²≈0.77 to within-group y-leak (264 imaging rows → 88 unique Seahorse y; within-group std≈0) + plate effect; established well-group-aware + leave-plate-out evaluation framework. <br>3. **Cross-modal MoA story + EE-DrugSeq-v1 benchmark**: 175 target perturbations, KD-quality tiering (strong 46 / weak 94 / failed 28); MoA states uncoupler-like 53 / mixed 39 / biogenesis-like 13 / toxic-collapse 6 / neutral 64; **52 tier-1 immediate-validation candidates** (DDI2, TAGLN, G6PC, …). <br>4. TMRM channel-identity correction verified against `1_Pipeline/2_tmrm.py` and imaging. | [RIC-381](https://jira.novonordisk.com/browse/RIC-381) |
| | **Safety landscape tool — modality-aware + conditional-risk + v6 keywords** | 1. **Modality-aware prompts + hedge-aware risk scoring**: peripherally-restricted / partial-IA modality no longer blindly down-weights CNS LoF evidence. <br>2. **P0/P1 scoring + conditional-risk layer** (2026-06-18): modality-based mitigation and residual no-go concerns made explicit for safety review. <br>3. Packaged toolkit as installable `safety` CLI; produced ZH/EN **one-pager + Mermaid pipeline flowchart** (EN PPTX+PDF, 10 slides) for onboarding. <br>4. **v6_composite keyword set**: binary accuracy **70.8%** on NCBN N=305 (+2.3 pp vs v5_final). | [RIC-349](https://jira.novonordisk.com/browse/RIC-349) |
| | **BBB prediction expansion — Phase 2/3/4 + auto-report pipeline** | 1. **Phase 2 (peptide DL)**: local ESM-2 peptide-BBB model + ESM-BBB-Pred / DeepB3P; 4 BRP (BRINP2-related) sequences predicted for EJNH (Jason). <br>2. **Phase 3 (benchmarking)**: cross-tool sensitivity / specificity / MCC; B3clf 12-model committee for SM. <br>3. **Phase 4 — protraction-aware fusion layer**: lipidated / long-acting peptides no longer scored as backbone false-positives; **end-to-end auto-report pipeline** (CLI → HTML + PPTX + LLM narrative). <br>4. **Phase 4+ — modality-adaptive uncertainty**: SM uses committee-disagreement 90% Wilson interval; peptide retains ESM framing — method-aware, no longer mixed. | [RIC-388](https://jira.novonordisk.com/browse/RIC-388) |
| **Targets** | **Multi-target safety assessments — RORA / CDK8-19 / DGKQ family / GRB10 / PAM / EE strict-tox** | • **RORA** (req. MUEW): direction-feasibility for cardiometabolic / DIO — activation vs peripherally-restricted partial inverse agonist, modality-aware run. **RORA tool compounds** SR3335 / SR1001 / SR1078 BBB report via B3clf / CNS-MPO + committee uncertainty → **RIC-389 Done**. <br>• **CDK8 / CDK19 inhibition**: independent cross-check supporting NCBN/IKEB reproductive-tox termination call on RP0909 (CDK8i, T2D). <br>• **DGKQ family** (9 paralogs): inhibition RED=2 / YELLOW=5 / GREEN=2; activation-vs-inhibition two-direction comparison delivered. <br>• Additional batches: **GRB10 inhibition**, **PAM inhibition**, **EE strict-tox panel**, and 2026-06-09 / 06-10 GJSN series — outputs mirrored to `/TDE_TV/shared_folder/QYJI/safety/`. | [RIC-349](https://jira.novonordisk.com/browse/RIC-349) / [RIC-389](https://jira.novonordisk.com/browse/RIC-389) / [RIC-386](https://jira.novonordisk.com/browse/RIC-386) |
| **Campaign** | **Skeletal Muscle Atrophy assay — new batch + 4-way skeleton benchmark + cross-batch generalisation** | 1. New batch **IGWU_20260608_1 (PLXN/SEMA siRNA repeat)**: 240 wells end-to-end through v3.5 decoupled pipeline (no code changes; new wet-lab data). <br>2. **4-way skeleton-analysis benchmark**: ImageJ / OldPipeline / LegacyApprox / NewPyimagej over 240 images. <br>3. **Cross-batch SSMD validation (3 batches, 720 images)**: per-image total-length ρ ≥ 0.97, SSMD ρ ≥ 0.986, hit-class concordance ≥ 11/12 (best 20/20). <br>4. Single-file HTML dashboard updated: persistent path + cross-batch volcano (time-period & class colouring, click-to-jump). | [RIC-261](https://jira.novonordisk.com/browse/RIC-261) |
| | **Adipocyte Lipolysis Assay — imaging arm split + Round-1 BF analysis** | 1. Imaging-side activity log split out into new ticket **RIC-390**; RIC-298 kept as parent vAssay capability ticket. <br>2. **Round-1 KDE plate BF analysis** (data: Yang Huan / OFGM): CIDEC KD vs NTC, **2,700 images (5 Z × 9 fields × 60 wells)**, DICOM tiff stack → segmentation → droplet-level quantification end-to-end. | [RIC-298](https://jira.novonordisk.com/browse/RIC-298) / [RIC-390](https://jira.novonordisk.com/browse/RIC-390) |
| | **RadEE — Speakman cohort VBQ pipeline validation closure** | Closed RIC-340 with full activity log of the only actively pursued sub-stream: collaboration with **NNRCO Imaging Analytics (Mateusz Florkow et al., Oxford)** to validate their VBQ MRI-marker docker pipeline on Dr Speakman's cohort. Status: **Done**. | [RIC-340](https://jira.novonordisk.com/browse/RIC-340) |

---

## Tickets in period

**New / Active**
- RIC-381 — HepG2 EE multimodal MoA + vAssay leak-proof (Capability, primary)
- RIC-390 — Lipolysis imaging arm (split from RIC-298)
- RIC-375 — Seahorse imaging pipeline (NYOL request, peripheral)

**Progressed**
- RIC-349 (Safety landscape tool — modality-aware), RIC-388 (BBB expansion), RIC-261 (Skeletal Muscle), RIC-298 (Lipolysis parent), RIC-386 (DGK family)

**Closed**
- RIC-389 (RORA BBB — Done)
- RIC-340 (RadEE Speakman VBQ — Done)

---

## Deliverables

- **PPTX (single-page table):** `/das/user/QYJI/druggability/docs/monthly_report_2026_06.pptx`
- **Shared drive mirror:** `/TDE_TV/shared_folder/QYJI/monthly_report/QYJI_2026-06-25/monthly_report_2026_06.pptx`
- **Builder script:** `/tmp/build_monthly_report_v3.py`
