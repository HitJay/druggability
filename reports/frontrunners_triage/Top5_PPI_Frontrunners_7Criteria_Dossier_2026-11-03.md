# Top 5 Prioritized PPI Frontrunner Axes — 7-Criteria Evidence Verification & Campaign Dossier (RIC-410)

**Date:** November 3, 2026  
**Prepared by:** Qiuye Jin (QYJI)  
**Stakeholders:** Zheng Cao (ZHCO), Li Jiang (JXDL)  
**Target Scope:** 8 Frontrunner Targets (`GRB14`, `FNIP1`, `FNIP2`, `FLCN`, `PDE3B`, `PPARG`, `SLC25A5`, `STARD10`)  
**Dataset Audited:** Baker & Cong Proteome-Wide Human Interactome (`Science` 2025 `final_predictions_80.tsv` = 39 pairs involving the 8 frontrunners, including 18 pairs in `final_predictions_90.tsv`, plus 79 supplementary Stage-4 `AF2 >= 0.80` pairs).

---

## 1. Executive Summary & Veracity Audit Protocol

Prior to ranking and drafting this dossier, every piece of structural, genetic, literature, and safety evidence across all 39 Baker pairs (45 unique human proteins) was independently verified against primary databases:
1. **Criterion 1 (Interface SAVs & Validated Mutagens):** Parsed directly from official UniProt flat files (`rest.uniprot.org/uniprotkb/{ACC}.txt`, 216 `FT VARIANT` SAVs + 114 `FT MUTAGEN` experimental point mutations), cross-checked against **AlphaMissense** (`AFDB API` per-protein pathogenicity scores, requiring dual evidence `AM LPath >= 0.5 + UniProt Disease` per Pei, Zhang & Cong, `Sci Rep` 2026 16:25590), and mapped onto experimental RCSB PDB coordinates (`6ULG`, `8DHB`, `8JE2`, `6D94`, `6ONJ`, `1K74`, `3E00`, `2AUH`, `6SER`) and local **RF2-PPI** residue-residue contact probability matrices (`.npz`).
2. **Criterion 2 (Both-Protein Cardiometabolic Genetics & Directionality):** Audited via **Open Targets Platform v4 GraphQL** (`genetic_association`, `genetic_literature`, `animal_model`), dbSNP/Ensembl coordinates, and peer-reviewed large-scale exome/GWAS publications in **Europe PMC**.
3. **Criteria 3–6 (Pathways, Perturbation Literature, Co-Progression & Complex Structures):** Audited via Reactome, GO-BP, STRING v12 (`dscore`, `escore`, `ascore`), IntAct/BioGRID Multi-Validated sets, Europe PMC full-abstract verification (including canonical protein aliases such as `AMPK`, `beta-TrCP`, `EPAC1`, `Tankyrase`, `Lipin-1`), and RCSB PDB REST API metadata verification.
4. **Criterion 7 (Safety Risks & Modality Governance):** Cross-checked against Novo Nordisk internal **3_safety** bidirectional traffic-light evaluations (23 of the 45 proteins previously audited in production runs), Open Targets `safetyLiabilities`, and COSMIC/Mendelian loss-of-function redlines.

Out of the 39 precision-calibrated Baker pairs:
- **22 pairs pass all 6 biological/structural criteria (6/6 on C1–C6)**.
- Applying **Criterion 7 (Safety & Modality Governance)** separates these 22 pairs into **16 actionable therapeutic pairs** (grouped into the **Top 5 Campaign Axes** below) and **6 mandatory selectivity counter-screens** (where the partner carries a `3_safety RED` tumor-suppressor, oncogenic, cardiovascular, or TZD fluid-retention liability: `PPARG-MED1`, `PPARG-NCOA1`, `PPARG-NR0B1`, `PDE3B-PDE3A`, `PPARG-ARID1A/RB1`, `FLCN-BAG3`).

---

## 2. Deep-Dive on the Top 5 Prioritized PPI Frontrunner Axes

### Top 1 Axis: `FNIP1–PRKAG1` (90% Tier, Rank #1) / `FNIP1–PRKAA1` (80%) / `FNIP1–PRKAG2` (80%) [Anchored on `FLCN–FNIP1/2` (90% Tier)]
* **Program Alignment:** `FNIP1 / FNIP2 / FLCN` cluster inhibition & `AMPK` activation for T2D, Obesity, and MASH.
* **Baker Prediction Scores [FACT]:**
  * `FLCN–FNIP1` (90% tier): `RFprob = 0.9985`, `AFprob = 1.000`, `AFprob5 = 1.000`, `AFMprob = 1.000` (`Source = D,S,P`; local RF2-PPI `max_p = 0.989`).
  * `FLCN–FNIP2` (90% tier): `RFprob = 0.9976`, `AFprob = 0.9995`, `AFprob5 = 1.000`, `AFMprob = 1.000` (`Source = D,S,P`).
  * `FNIP1–PRKAG1` (90% tier): `RFprob = 0.4807`, `AFprob = 0.7770`, `AFprob5 = 0.7300`, `AFMprob = 0.7217` (`Source = P`; `STRING-exp = 0.802`).
  * `FNIP1–PRKAA1` (80% tier): `RFprob = 0.4360`, `AFprob = 0.2438`, `AFprob5 = 0.5900`, `AFMprob = 0.8706` (`Source = P`; `STRING-exp = 0.487`).
  * `FNIP1–PRKAG2` (80% tier): `RFprob = 0.4988`, `AFprob = 0.6006`, `AFprob5 = 0.7417`, `AFMprob = 0.7134` (`Source = P`).
* **Criterion 1 (3D Interface SAVs & Validated Mutagens) [FACT]:**
  * **Atomic Cryo-EM Verification (`6ULG` 3.31 Å, `8DHB` 3.53 Å, `8JE2` 3.63 Å):**
    * `FLCN p.Glu132Lys` (`rs2145009956`, `AlphaMissense = 0.9995 LPath`, Dual-Pathogenic in BHD/pneumothorax) forms a **2.60 Å inter-subunit salt bridge** with `FNIP2 Lys156` across the uDENN dimerization interface.
    * `FLCN p.Ser108Ile` (`rs2145012002`, `AM = 0.9992 LPath`, BHD1) sits at **`d_min = 6.90 Å`** from `FNIP2 Gly550`; `FLCN p.Lys508Arg` (`rs199643834`, BHD1) sits at **`d_min = 7.11 Å`** from `FNIP2 Leu1064` and 2 residues from the #1 RF2-PPI contact `FLCN:Cys506` (`p = 0.989`).
    * `FNIP1 p.Ser1118Asn` (`rs2149501551`, `AM = 0.9888 LPath`, Dual-Pathogenic in IMD93/hypertrophic cardiomyopathy) sits at position **1118**, directly sandwiched between the #1 and #2 RF2-PPI contact residues `FNIP1:Phe1116` (`p = 0.989` with `FLCN:Cys506`) and `FNIP1:Met1120` (`p = 0.987` with `FLCN:Gln502`) and adjacent to the ubiquitination mutagen `FNIP1 K1119R`.
    * `FNIP2 p.Val146Asp` (UniProt `FT MUTAGEN` abolishing FLCN GAP activity) sits at **`d_min = 3.64 Å`** from `FLCN` and **`6.67 Å`** from `RRAGA` in `6ULG`.
  * **AMPK Interface SAVs & Mutagens:**
    * `PRKAG2` harbors **6 dual-evidence pathogenic SAVs** in its CBS nucleotide/subunit interface causing familial hypertrophic cardiomyopathy 6 (CMH6) and Wolff-Parkinson-White (WPW) syndrome: `R302Q` (`rs121908987`, `AM = 0.9976`), `H383R` (`rs121908988`, `AM = 0.9994`), `T400N` (`rs28938173`, `AM = 0.9964`), `N488I` (`rs121908989`, `AM = 0.9788`), `R531G` (`rs121908990`, `AM = 0.9993`), and `R531Q` (`rs121908991`, `AM = 0.9974`).
    * `PRKAG1` carries `T89S` (`rs1126930`, `AM = 0.8790 LPath`) adjacent to AMP/ADP-sensing mutagens `D90A`, `D245A`, and `D317A`, with RF2-PPI top contact at `PRKAG1:Glu159–FNIP1:Asp530` (`p = 0.163`).
    * `FNIP1` carries experimentally validated AMPK phosphorylation-site mutagens `S220A / S261A / S593A` (`SA5` mutant in UniProt `Q8TF40`, which abolishes phosphorylation by AMPK) plus cDENN coding SAVs `Q648R` (`rs26008`) and `V738L` (`rs12109782`) inside the `544–911` AMPK-binding region.
* **Criterion 2 (Human Genetics & Directionality) [FACT]:**
  * **1-Million-Human Exome Proof (`PMID:42557317`, 2026):** Exome sequencing across **1,032,116 individuals** demonstrates that ultra-rare protein-truncating variants (PTVs, AF = 0.01%) in `FNIP1` are associated with **lower TG:HDL ratio, lower liver fat, lower glycaemia, favorable fat distribution, and ~60% lower odds of cardiometabolic disease**.
  * **Directionality (Opposite Direction -> PPI Disruptor = Agonist):** `FNIP1` acts as a metabolic brake (suppressor of AMPK and mitochondrial biogenesis), whereas `AMPK` (`PRKAG1/PRKAA1/PRKAG2`) activation promotes hepatic lipid oxidation and insulin sensitivity (`Open Targets` `PRKAG1` CKD = 0.46; `PRKAG2` CMH6 = 0.90, T2D KO = 0.37). Disrupting the inhibitory tethering of `FNIP1` onto `AMPK` directly unleashes endogenous AMPK activity.
* **Criteria 3–6 (Pathway, Perturbation, Co-Progression & Structures) [FACT]:**
  * Both belong to the canonical AMPK–mTORC1–TFEB nutrient-sensing cascade (C3). Baba et al. (`PNAS` 2006, `PMID:17028174`) and Malik et al. (`Science` 2023, `PMID:37079686`) proved that AMPK directly binds and phosphorylates `FNIP1`, while `FNIP1` knockdown in primary human hepatocytes induces lipid breakdown and lysosomal gene expression (`PMID:42557317`) (C4/C5). Validated by Cryo-EM (`8JE2`, `6ULG`, `6NZD`, `8DHB`) and UniProt/BioGRID/STRING (C6).
* **Criterion 7 (Safety & Modality Strategy) [FACT / MECH]:**
  * In `3_safety`, `PRKAA1 Activation = GREEN (score=0)` and `FNIP2 = GREEN`, whereas systemic `FLCN Inhibition = RED` (renal cell carcinoma tumor suppressor in Birt-Hogg-Dube syndrome) and complete homozygous `FNIP1` null causes recessive immunodeficiency/HCM (`IMD93`, score=104). Crucially, heterozygous human `FNIP1` PTV carriers in 1M exomes are completely spared of IMD93 while enjoying 60% cardiometabolic protection (`PMID:42557317`).
  * **Actionable Strategy & Wet-Lab Controls:** Target the `FNIP1 (cDENN Asp530) : PRKAG1 (Glu159) / PRKAA1` interface with a PPI disruptor or hepatocyte-targeted `FNIP1/2` GalNAc-siRNA (sparing `FLCN` and cardiac `PRKAG2`). **Controls:** `FNIP1 D530A`, `FNIP1 SA5 (S220A/S261A/S593A)`, `PRKAG1 E159A`, and `FLCN E132K`.

---

### Top 2 Axis: `FNIP1–BTRC` [beta-TrCP1] (80% Tier) & `FNIP1–FBXW11` [beta-TrCP2] (80% Tier)
* **Program Alignment:** Endogenous E3 Ubiquitin Ligase **Molecular Glue Degrader** for `FNIP1` (T2D, Obesity, MASH).
* **Baker Prediction Scores [FACT]:**
  * `FNIP1–BTRC` (80% tier): `RFprob = 0.3945`, `AFMprob = 0.8360` (`Source = P`, `BioGRID MV & STRING-exp = 0.217`).
  * `FNIP1–FBXW11` (80% tier): `RFprob = 0.4190`, `AFMprob = 0.8090` (`Source = P`, `BioGRID MV & STRING-exp = 0.181`).
* **Criterion 1 (3D Interface SAVs & Validated Mutagens) [FACT]:**
  * RF2-PPI top residue contacts `FNIP1:Met241–BTRC:Ile603` (`p = 0.129`) and `FNIP1:Arg288–BTRC:Asp574` (`p = 0.125`) dock the `FNIP1` uDENN phosphodegron region (immediately flanking AMPK phosphorylation sites `Ser220` and `Ser261`) directly into the WD40 repeat substrate-binding beta-propeller of `BTRC` (`301–605`).
  * On `BTRC`, this WD40 pocket contains coding SAV `P592H` (`rs2270439`) and 3 experimentally validated substrate-abolishing point mutations in UniProt (`Q9Y297`): `Y307A`, `R321A`, and `R510A` ("Abolished binding to DEPTOR, TFE3 and MITF substrates").
  * On paralog `FBXW11` (`Q9UKB1`), the WD40 beta-propeller harbors **7 dual-evidence pathogenic SAVs** (`G242R` `rs1759346639` `AM = 1.000`; `R363W` `rs1758081729` `AM = 0.9966`; `A364D` `rs1758081491` `AM = 0.9999`; `A365T` `rs2113777419` `AM = 0.9994`; `E444K` `rs2113754835` `AM = 0.9992`; `R447L/Q` `rs1757708758` `AM = 0.9978/0.9997`), plus `FNIP1` ubiquitination-site mutagen `K1119R` ("Impaired ubiquitination, leading to increased stability").
* **Criterion 2 (Human Genetics & Directionality) [FACT]:**
  * **Both-Protein Human Genetics:** `FNIP1` rare PTVs protect against cardiometabolic disease in 1M humans (`PMID:42557317`), while `BTRC` has direct human GWAS associations in Open Targets for **Diabetes Mellitus (`OT = 0.50`), Morbid Obesity (`OT = 0.33`), and Atrial Fibrillation (`OT = 0.54`)**, and `FBXW11` associates with **Liver Disorder (`OT = 0.12`)**.
  * **Directionality (Molecular Glue Degrader):** Because `SCF(BTRC/FBXW11)` is the endogenous E3 ligase that ubiquitinates and degrades `FNIP1`, a small-molecule **molecular glue** that enhances `FNIP1` binding to the `BTRC/FBXW11` WD40 propeller accelerates `FNIP1` degradation—converting a traditional PPI into a catalytic degrader that mimics human `FNIP1` LoF protection.
* **Criteria 3–7 (Pathway, Perturbation, Structures & Safety) [FACT / MECH]:**
  * Validated in BioGRID Multi-Validated set and STRING (`escore = 0.217`, `ascore = 0.065/0.075`). In `3_safety`, recruiting endogenous `BTRC` as an E3 ligase for `FNIP1` avoids systemic `BTRC` inhibition (`YELLOW`, score=56) and provides a clean peripheral metabolic window.
  * **Wet-Lab Controls:** `BTRC R510A / Y307A / R321A` (WD40 pocket dead mutants) and `FNIP1 M241A / R288A / K1119R` for ternary TR-FRET and HiBiT-FNIP1 degradation assays.

---

### Top 3 Axis: `PDE3B–RAPGEF3` [EPAC1] (80% Tier) & `PDE3B–LGR4` (80% Tier) [with `PDE3B–PDE3A/PDE4D` as Counter-Screens]
* **Program Alignment:** `PDE3Bi` adipocyte/hepatocyte cAMP microdomain regulation, lipolysis control, and insulin sensitization.
* **Baker Prediction Scores [FACT]:**
  * `PDE3B–RAPGEF3` (80% tier): `RFprob = 0.1927`, `AFprob = 0.7075`, `AFprob5 = 0.7390`, `AFMprob = 0.6820` (`Source = P`; `UniProt Q13370 SUBUNIT`, `IntAct EBI-6172856 NbExp = 8`, `STRING = 762`, `escore = 0.456`).
  * `PDE3B–LGR4` (80% tier): `RFprob = 0.5940`, `AFprob = 0.4414`, `AFprob5 = 0.6460`, `AFMprob = 0.7010` (`Source = P`; `BioGRID`).
  * Selectivity Counter-Screens: `PDE3B–PDE3A` (90% tier: `AFprob = 0.9990`, `AFMprob = 0.9966`) and `PDE4D–PDE3B` (80% tier: `AFprob = 0.9976`, `AFMprob = 0.9946`).
* **Criterion 1 (3D Interface SAVs & Validated Mutagens) [FACT]:**
  * **7 Validated Interface Mutagens on `PDE3B` (`UniProt Q13370`, `PMID:21393242`):** Seven point mutations in the unique N-terminal membrane-tethering peptide of `PDE3B` (**`R2A`, `R3A`, `R6A`, `A8D`, `K9A`, `A10D`, `R12A`**) directly abolish physical binding to `RAPGEF3 (EPAC1)`. RF2-PPI additionally identifies secondary contacts at `RAPGEF3:Gly132–PDE3B:Ala126` (`p = 0.197`) and `RAPGEF3:Gly594–PDE3B:Glu797` (`p = 0.210`), with 3 `RAPGEF3` coding SAVs (`R193G`, `G374S`, `C517Y`) on the contact surface.
  * **`LGR4` Coding Variants:** `LGR4` harbors 8 coding SAVs in UniProt including functional signaling variants `I96V` (`rs757351670`), `G363C` (`rs117543292`), and C-terminal tail `D844G` (`rs34804482`, reduced protein expression) alongside the human gain-of-function obesity mutation **`LGR4 p.Ala750Thr`** (`PMID:42677820`).
  * **`PDE3A` & `PDE4D` Counter-Screen SAVs:** `PDE3A` harbors 6 dual-pathogenic gain-of-function SAVs (`T445A/N/S`, `A447T/V`, `G449V`; `AM = 0.802–0.974 LPath`) causing Mendelian hypertension-brachydactyly syndrome (HTNB), while `PDE4D` harbors 11 dual-pathogenic ACRDYS2 SAVs (`AM = 0.779–0.999 LPath`) and dimerization-abolishing mutagens `D527R / R563D`.
* **Criterion 2 (Human Genetics & Directionality) [FACT]:**
  * **`PDE3B`:** UK Biobank exome sequencing proves rare human `PDE3B` loss-of-function variants confer **lower triglycerides, lower waist-to-hip ratio (WHR), favorable gluteofemoral fat distribution, and reduced coronary artery disease risk** (`PMID:34875679`; `Open Targets` T2D = 0.56).
  * **`RAPGEF3 (EPAC1)`:** Human genetic association with **Type 2 Diabetes (`OT = 0.19`)** and Blood Pressure (`OT = 0.13`) plus **46 KO mouse metabolic/vascular phenotypes** (`OT = 0.59`; `PMID:39199373`).
  * **`LGR4`:** Human nonsense mutation `p.Arg126Ter` lowers body weight while gain-of-function `p.Ala750Thr` drives human central obesity and insulin resistance (`PMID:42677820`; `OT` obesity = 0.10), and endothelial `LGR4` protects against MASLD hepatic steatosis (`PMID:42749044`, 2026).
* **Criteria 3–7 (Pathway, Perturbation, Structures & Safety) [FACT / MECH]:**
  * Both `PDE3B` (`Inhibition = GREEN`) and `RAPGEF3` (`Inhibition = GREEN`, `Activation = GREEN`, score=0) are **GREEN in `3_safety`**, whereas `PDE3A` is **RED** (milrinone-class cardiac positive inotropy, arrhythmia, and increased heart-failure mortality). Because `PDE3A` lacks the `PDE3B` N-terminal `RAPGEF3/LGR4` signalosome tether, allosterically targeting the `PDE3B–RAPGEF3/LGR4` complex achieves complete isoform selectivity over cardiac `PDE3A`.
  * **Wet-Lab Controls:** `PDE3B R2A/R3A/R6A/K9A/R12A` (validated `RAPGEF3`-binding null mutant, `PMID:21393242`), `RAPGEF3 G557A / G594A`, and `LGR4 D844G / A750T`.

---

### Top 4 Axis: `PPARG–NR1H2` [LXRB] (90% Tier) / `PPARG–NR1H3` [LXRA] (90% Tier) / `PPARG–LPIN1` [Lipin-1] (80% Tier) [with `PPARG–MED1 / NCOA1` (90% Tier) as `3_safety RED` Counter-Screens]
* **Program Alignment:** Next-Generation `PPARg` Modulator (`SPPARM`) / `GLP-1-GIP-PPARg` — decoupling insulin sensitization & MASH resolution from TZD fluid retention/heart failure.
* **Baker Prediction Scores [FACT]:**
  * `PPARG–NR1H2` (90% tier): `RFprob = 0.1843`, `AFprob = 0.8440`, `AFprob5 = 0.9507`, `AFMprob = 0.9790` (RF2-PPI LBD contact `PPARG:Leu464–NR1H2:Met422`, `p = 0.500`).
  * `PPARG–NR1H3` (90% tier): `RFprob = 0.1660`, `AFprob = 0.8370`, `AFprob5 = 0.9250`, `AFMprob = 0.9746` (`STRING-exp = 0.622`, `coexpr = 0.100`).
  * `PPARG–LPIN1` (80% tier): `RFprob = 0.1272`, `AFprob = 0.4690`, `AFMprob = 0.8354` (`STRING = 909`, `coexpr = 0.060`).
  * Negative Counter-Screens (90% tier): `PPARG–MED1` (`AFprob5 = 0.9650`, `AFMprob = 0.9546`; exact crystal `6D94` / `6ONJ`) and `PPARG–NCOA1` (`AFprob5 = 0.9720`, `AFMprob = 0.9365`; exact crystal `1K74` / `3VN2`).
* **Criterion 1 (Exact Crystal Atomic Distances of Human Disease SAVs) [FACT]:**
  * Measured directly on experimental X-ray crystal coordinates **`6D94.pdb` (1.90 Å)**, **`6ONJ.pdb` (2.30 Å)**, **`1K74.pdb` (2.30 Å)**, and **`3E00.pdb` (3.10 Å)** (noting canonical `P37231` PPARG2 is +28 aa relative to PDB PPARG1 numbering):
    1. **`PPARG p.Pro495Leu` (`rs121909244`, `AM = 0.9788 LPath`, Dual-Pathogenic in severe human insulin resistance, T2D & FPLD3; PDB `Pro467` in AF-2 helix H12):** Sits at **`d_min = 3.64 Å` from `MED1 Met644` (`6ONJ`) / `3.73 Å` from `MED1 Met290` (`6D94`)** and **`d_min = 4.84 Å` from `NCOA1 Ile689` (`1K74`)**!
    2. **`PPARG p.Val318Met` (`rs72551362`, `AM = 0.8189 LPath`, Dual-Pathogenic in T2D/FPLD3; PDB `Val290`):** Sits at **`d_min = 6.07 Å` from `MED1 Leu648` (`6ONJ`)** and **`d_min = 6.14 Å` from `NCOA1 Leu693` (`1K74`)**!
    3. **`NCOA1 p.Glu685Ala` (`rs1049021`, `AM = 0.8739 LPath`):** Is the **exact N-terminal cap residue (`Glu685`)** of the crystallized `NCOA1` LXXLL peptide (`685–700`) in `1K74.pdb`!
    4. **`PPARG p.Arg425Cys` (`rs72551364`, `AM = 0.9972 LPath`, Dual-Pathogenic in FPLD3/T2D; PDB `Arg397`):** Sits at **`d_min = 5.10 Å` (`1K74`) / `5.46 Å` (`3E00`) from the heterodimer partner `Glu352`**, forming a direct inter-chain salt bridge on the nuclear receptor heterodimer interface used by `NR1H2 / NR1H3 / RXRG`!
    5. **`LPIN1 p.Gly56Glu` (`AM = 0.9983 LPath`, Dual-Pathogenic)** plus `LPIN1` `LXXIL` coactivator motif and `K425R/K595R` acetylation mutagens (`UniProt Q14693`).
* **Criteria 2–7 (Genetics, Biology & `3_safety`-Guided SPPARM Ratio Assay) [FACT / MECH]:**
  * Full `PPARG` agonists (TZDs) trigger `3_safety RED` (`score = 96`, boxed warning for fluid retention, edema, and congestive heart failure) by locking AF-2 helix H12 (`Pro495`) to hyper-recruit `MED1` (`3_safety RED`, score=140) and `NCOA1` (`3_safety RED`, score=77).
  * By contrast, **`LPIN1 Activation = GREEN (score = 0)`** and **`NR1H2 Inhibition = GREEN (score = 0)`** in `3_safety`. Biologically, `LPIN1` coactivates `PPARG/PPARA` to drive hepatocyte fatty acid oxidation in MASH (`PMID:42212316`, 2026; human `LPIN1 rs13412852` MASLD genetics `PMID:41751781`) and white adipocyte browning (`PMID:41007632`, 2025) without inducing TZD-like renal sodium/water retention.
  * **Actionable Wet-Lab Cascade:** Use a dual-readout TR-FRET cofactor recruitment screen measuring the **selectivity ratio of `[PPARG–LPIN1 + PPARG–NR1H2]` (desired GREEN/YELLOW axis) over `[PPARG–MED1 + PPARG–NCOA1]` (undesired RED TZD axis)**, using crystal-verified mutants `PPARG P495L (d=3.64 Å)`, `PPARG V318M (d=6.07 Å)`, and `PPARG R425C (d=5.10 Å)` as structural controls.

---

### Top 5 Axis: `STARD10–PRMT6` (90% Tier) & `GRB14–TNKS2` (80% Tier) [Sole High-Confidence Baker Partners for `STARD10` & `GRB14`]
* **Program Alignment:** `STARD10i` (islet beta-cell function & hepatic lipid transport) and `GRB14i Hepato / HepatoPan` (insulin receptor sensitizer).
* **5A. `STARD10–PRMT6` (90% Tier, Rank #11):**
  * **Baker & Interface Proof [FACT]:** `RFprob = 0.7627`, `AFMprob = 0.7220`, local RF2-PPI **`max_p = 0.899`** at **`PRMT6:Gly281–STARD10:Val110`** and **`p = 0.868` at `PRMT6:Glu244–STARD10:Thr109`**, mapping directly onto the `STARD10` START lipid-binding cavity (resolved in crystal structure **`6SER` at 2.30 Å**) and the `PRMT6` Rossmann fold (carrying coding SAV `A194V`, `rs2232016`). Validated in `UniProt Q9Y365` (`IntAct EBI-4289836, NbExp = 2`), `BioGRID MV`, and `STRING` (`escore = 0.456`, `ascore = 0.094`).
  * **Human Genetics & Perturbation (C2/C4/C5) [FACT]:** Both proteins have strong human T2D/obesity genetic associations in Open Targets: **`STARD10` (`diabetes = 0.83`, `T2D = 0.69`, `gestational diabetes = 0.53`)** and **`PRMT6` (`obesity = 0.65`, `T2D = 0.57`)**. In 2026, human stem-cell islet deletion of `STARD10` proved its essential role in beta-cell differentiation and triglyceride metabolism (`PMID:41687621`), while therapeutic targeting of the hepatic `PRMT6/FOXK1` axis restored lipid homeostasis and ameliorated hepatic steatosis and MASH in mice (`PMID:42948769`, 2026).
  * **Safety & Modality (C7) [FACT]:** Systemic catalytic `PRMT6` inhibition is `3_safety RED` (`score = 101`, thrombocytopenia & genotoxicity), whereas `STARD10` is `GREEN`. Disrupting the specific `PRMT6:Gly281–STARD10:Val110` PPI interface in hepatocytes/islets avoids systemic PRMT6 catalytic toxicity. **Controls:** `STARD10 T109A/V110A` and `PRMT6 E244A/G281A`.
* **5B. `GRB14–TNKS2` [Tankyrase-2] (80% Tier, Rank #18):**
  * **Baker & Interface Proof [FACT]:** `RFprob = 0.2605`, `AFprob = 0.6626`, `AFprob5 = 0.6987`, `AFMprob = 0.4053` (`Source = P`; validated in `UniProt Q14449 SUBUNIT`, `BioGRID MV`, and `STRING = 863`, `escore = 0.476`). `UniProt Q14449` confirms `GRB14` binds the ankyrin repeat clusters (ARC) of `TNKS2` via its N-terminus (adjacent to `GRB14` coding SAV `F90I`, `rs61748245`), while RF2-PPI maps a secondary contact at **`GRB14:Ala378–TNKS2:Asp1045/Ser1066` (`p = 0.160`)**, placing `GRB14 Ala378` right inside the `GRB14` **BPS (Between PH and SH2) kinase-inhibitory domain** (resolved in crystal **`2AUH` at 3.20 Å**, adjacent to AKT/MAPK-restoring mutagens `Q348A/N349A`) and flanking `TNKS2` loss-of-activity mutagen `M1054V`.
  * **Human Genetics & Scope Note [FACT / MECH]:** Both proteins have direct human **Type 2 Diabetes genetic associations in Open Targets (`GRB14 T2D = 0.74`, WHR/insulin resistance GWAS lead `rs13389219`; `TNKS2 T2D = 0.25`)**, and Tankyrase regulates GLUT4 vesicle translocation and insulin sensitivity (`PMID:41744791`). *Methodological Boundary Note:* As established in our platform benchmark, Baker's RF2-PPI has only 4.5% recall on `<800 Å²` short linear motifs (SLiMs), which is why transient proline-rich/kinase cleft complexes (`GIGYF1–GRB14` crystal `7RUQ` and `GRB14–INSR` crystal `2AUH`) are captured by our structure/WES pipeline rather than RF2-PPI, whereas `GRB14–TNKS2` represents a larger ankyrin-repeat scaffold interaction uniquely surfaced by Baker's pipeline. **Controls:** `GRB14 F90I / Q348A / A378R` and `TNKS2 M1054V`.

---

## 3. Summary Note on `SLC25A5` (ANT2, NN4005 Hepato RNAi)
In Baker's `final_predictions_80.tsv`, `SLC25A5` has 5 predicted partners: `ATXN3` (90% tier, `AF2 = 0.829`), `IKZF1` (80%, `AF2 = 0.860`), `CIAPIN1` (80%, `AF2 = 0.791`, `AFM = 0.809`), `MAP3K1` (80%, `AF2 = 0.771`, `AFM = 0.839`), and `AFDN` (80%, `AFM = 0.965`). However, none of the 5 partners pass all 6 biological criteria (`IKZF1` is a `3_safety RED` hematopoietic transcription factor; `MAP3K1` has human T2D genetics `OT = 0.49` and dual-pathogenic SAVs `L189P/R` [Rank #32, 3/6 criteria]; `CIAPIN1` is an essential mitochondrial Fe-S assembly factor with coronary atherosclerosis genetics `OT = 0.41`). This confirms that for `SLC25A5`, **direct hepatocyte-targeted RNAi (`NN4005 SLC25A5 Hepato RNAi`) remains superior to binary PPI modulation**.


---

---

## 4. Stage 1–3 Computational Biophysics Audit on All 11 Template-Free Prioritized Frontrunner Constructs (Boltz-2 + omicMSA Docking, Explicit-Solvent NPT MD, MM/GBSA & 8-Lambda Alchemical TI FEP)

Following Zheng's recommendation, we executed the full 3-stage biophysical validation pipeline across all **10 complex-template-free prioritized Frontrunner pairs plus the restored N-terminal `GRB14(1-115)–TNKS2(ARC3-4)` construct (11 complexes total, `PDBtemp = none` across the Top 5 Axes)** on our 8x NVIDIA L20 GPU cluster (`Precision = double` throughout to prevent mixed-precision zero-window artifacts):
1. **Stage 1 (Boltz-2 + Sanitized Baker `omicMSA` Co-Folding/Docking):** Domain-resolved constructs spanning the RF2-PPI coevolving interfaces, SAVs, and experimental mutagens (`436–742 aa` per complex), with output PDB coordinates re-numbered back to canonical 1-indexed UniProt numbering (`02_TemplateFree_Docked_PDBs/*.pdb`).
2. **Stage 2 (Explicit-Solvent NPT MD + Ensemble GBn2 MM/GBSA):** Solvated in explicit `TIP3P` water boxes (`95,408–236,172 atoms`, `0.15 M NaCl`, `310 K`, `1 bar`, `Amber14SB`), energy-minimized, equilibrated (`20 ps`), and sampled (`200 ps`, `15 snapshots`) with PBC minimum-image re-imaging, Baker-Hubbard dynamic H-bond persistence, and per-residue vdW/Coulomb decomposition.
3. **Stage 3 (8-Lambda Alchemical TI FEP Mutational Hotspot Scan):** 110 interface mutations (human disease SAVs, validated experimental mutagens, RF2-PPI coevolving pairs mapped through canonical `(*)` mask positions, and top MD energetic anchors) evaluated across 8 lambda windows (`0.0, 0.15, 0.30, 0.45, 0.60, 0.75, 0.90, 1.0`, `Precision = double`, 0/110 zero-window artifacts).

### Summary of 11 Template-Free Complexes (Full 110-Mutation Table in Excel Sheet `5_TemplateFree_Dock_MD_FEP`)

| Complex ID | PPI Pair (Axis) | Constructs (Canonical UniProt) | Boltz-2 Confidence | Explicit-Solvent MD Stability & MM/GBSA | Key Alchemical FEP Hotspots (`ddG_screened`, kcal/mol) |
|---|---|---|---|---|---|
| `01_STARD10_PRMT6` | `STARD10–PRMT6` (Axis 5A, 90%) | `STARD10 (1-291)` + `PRMT6 (35-375)` | `conf = 0.775`, `pTM = 0.734`, `ipTM = 0.509`, `pLDDT = 0.841` (70 contacts `<=5A`) | `RMSD = 0.47 A` (`final 0.55 A`), `<dG_GBn2> = -72.1 +/- 4.1 kcal/mol`, `<E_vdW> = -94.1` | RF2 #2 `PRMT6 Glu244Ala` (**`+6.17`**, `d=2.06A`), RF2 #4 `PRMT6 Tyr280Ala` (**`+3.81`**, `d=2.35A`), `STARD10 Lys202Ala` (**`+13.21`**, `d=1.75A`), `PRMT6 Asp334Ala` (**`+7.02`**, `d=1.84A`), `PRMT6 Arg249Ala` (**`+5.39`**, `d=1.86A`) |
| `02_PPARG_LPIN1` | `PPARG–LPIN1` (Axis 4, 80%) | `PPARG (235-505)` + `LPIN1 (500-760)` | `conf = 0.542`, `pTM = 0.554`, `ipTM = 0.285`, `pLDDT = 0.607` (291 contacts `<=5A`) | `RMSD = 0.50 A` (`final 0.67 A`), `<dG_GBn2> = -318.4 +/- 10.7 kcal/mol`, `<E_vdW> = -420.1` | RF2 #2 `PPARG Asp424Ala` (**`+12.56`**, `d=1.76A`, adjacent to FPLD3 SAV `R425C`), validated mutagen `LPIN1 Lys595Ala` (**`+2.17`**, `d=2.49A`), `PPARG Glu326Ala` (**`+11.28`**, `d=1.77A`), `LPIN1 Lys508Ala` (**`+10.59`**), `LPIN1 Arg629Ala` (**`+8.34`**); FPLD3 SAVs `P495/V318/R425` sit at `d=2.51–4.39A` |
| `03_PRKAG1_FNIP1` | `FNIP1–PRKAG1` (Axis 1A, 90%, #1) | `PRKAG1 (1-331)` + `FNIP1 (450-760)` | `conf = 0.470`, `pTM = 0.511`, `ipTM = 0.184` (183 contacts `<=5A`) | `RMSD = 0.50 A` (`final 0.61 A`), `<dG_GBn2> = -210.3 +/- 9.1 kcal/mol`, `<E_vdW> = -236.4` | Validated AMPK phosphorylation site `FNIP1 Ser593Ala` (**`+1.94`**, `d=2.92A`); RF2 #1/#2 `PRKAG1 Glu159/Ser160` (`d=2.19/2.50A`, **`+0.17/+0.83`**); `PRKAG1 Lys174Ala` (**`+14.03`**, `d=1.77A`), `PRKAG1 Lys170Ala` (**`+13.77`**), `FNIP1 Glu629Ala` (**`+7.97`**) |
| `04_FNIP1_PRKAG2` | `FNIP1–PRKAG2` (Axis 1B, 80%) | `FNIP1 (100-320)` + `PRKAG2 (30-550)` | `conf = 0.396`, `pTM = 0.404`, `ipTM = 0.154` (454 contacts `<=5A`) | `RMSD = 0.46 A` (`final 0.53 A`), `<dG_GBn2> = -533.2 +/- 13.5 kcal/mol`, `<E_vdW> = -595.7` | RF2 #1 `FNIP1 Gly255` (`d=2.35A`) & AMPK site `FNIP1 Ser220` (`d=2.80A`); adjacent `FNIP1 Glu221Ala` (**`+21.04`**, `d=1.59A`) & `PRKAG2 Lys155Ala` (**`+9.76`**, `d=1.87A`) |
| `05_PRKAA1_FNIP1` | `FNIP1–PRKAA1` (Axis 1C, 80%) | `PRKAA1 (15-480)` + `FNIP1 (380-620)` | `conf = 0.539`, `pTM = 0.459`, `pLDDT = 0.642` (86 contacts `<=5A`) | `RMSD = 0.50 A` (`final 0.64 A`), `<dG_GBn2> = -84.0 +/- 7.5 kcal/mol`, `<E_vdW> = -129.8` | `FNIP1 Glu438Ala` (**`+4.60`**, `d=2.17A`, H-bond to `PRKAA1 Lys396` [**`+2.11`**, `d=1.89A`]), `FNIP1 Glu444Ala` (**`+3.00`**, `d=2.74A`, adjacent to RF2 #1 `Ala446` [`d=3.24A`]), `FNIP1 Gln529Ala` (**`+2.45`**, `d=2.35A`) |
| `06_FNIP1_BTRC` | `FNIP1–BTRC` (Axis 2A, 80%) | `FNIP1 (180-340)` + `BTRC (250-605)` | `conf = 0.626`, `pTM = 0.657`, `ipTM = 0.214`, `pLDDT = 0.729` (127 contacts `<=5A`) | `RMSD = 0.46 A` (`final 0.58 A`), `<dG_GBn2> = -145.5 +/- 5.5 kcal/mol`, `<E_vdW> = -147.2` | Validated WD40 mutagens `BTRC Arg510Ala` (**`+5.63`**, `d=1.84A`) & `BTRC Tyr307Ala` (**`+3.28`**, `d=2.15A`); RF2 #1 contact `FNIP1 Met241Ala` (**`+1.67`**, `d=1.99A`); `BTRC Arg557Ala` (**`+7.63`**), `BTRC Arg446Ala` (**`+6.83`**), `FNIP1 Asp315Ala` (**`+6.63`**) |
| `07_FNIP1_FBXW11` | `FNIP1–FBXW11` (Axis 2B, 80%) | `FNIP1 (760-960)` + `FBXW11 (1-480)` | `conf = 0.558`, `pTM = 0.472`, `ipTM = 0.255`, `pLDDT = 0.634` (422 contacts `<=5A`) | `RMSD = 0.46 A` (`final 0.58 A`), `<dG_GBn2> = -426.8 +/- 14.7 kcal/mol`, `<E_vdW> = -581.8` | Dual-Pathogenic WD40 SAVs `FBXW11 Arg363Ala` (**`+19.42`**, `d=1.59A`, `rs1758081729`) & `FBXW11 Arg447Ala` (**`+15.35`**, `d=1.91A`, `rs1757708758`); RF2 #1 contact `FBXW11 Arg63Ala` (**`+8.19`**, `d=4.56A`); `FNIP1 Ile849Ala` (**`+2.53`**, `d=2.47A`) |
| `08_PDE3B_RAPGEF3` | `PDE3B–RAPGEF3` (Axis 3A, 80%) | `PDE3B (1-160)` + `RAPGEF3 (1-350)` | `conf = 0.528`, `pTM = 0.524`, `pLDDT = 0.623` (331 contacts `<=5A`) | `RMSD = 0.49 A` (`final 0.60 A`), `<dG_GBn2> = -373.9 +/- 9.9 kcal/mol`, `<E_vdW> = -439.3` | Validated EPAC1-binding mutagens (`PMID:21393242`): `PDE3B Arg12Ala` (**`+11.04`**, `d=4.39A`), `PDE3B Lys9Ala` (**`+10.15`**, `d=2.28A`), `PDE3B Arg6Ala` (**`+5.48`**, `d=2.82A`), plus `PDE3B Lys33Ala` (**`+19.59`**, `d=1.72A`) & `RAPGEF3 Asp137Ala` (**`+14.02`**, `d=1.71A`) |
| `09_PDE3B_LGR4` | `PDE3B–LGR4` (Axis 3B, 80%) | `PDE3B (350-650)` + `LGR4 (25-380)` | `conf = 0.553`, `pTM = 0.591`, `ipTM = 0.370`, `pLDDT = 0.599` (326 contacts `<=5A`) | `RMSD = 0.44 A` (`final 0.55 A`), `<dG_GBn2> = -263.3 +/- 8.9 kcal/mol`, `<E_vdW> = -350.3` | RF2 #1 contact `PDE3B Phe537Ala` (**`+3.31`**, `d=2.29A`) & RF2 #3 `LGR4 Ser133Ala` (**`+2.14`**, `d=1.90A`); `PDE3B Lys546Ala` (**`+17.00`**, `d=1.71A`), `LGR4 Arg156Ala` (**`+9.92`**, `d=1.74A`), `LGR4 Lys212Ala` (**`+9.35`**, `d=1.99A`) |
| `10_GRB14_TNKS2` | `GRB14–TNKS2` (Axis 5B-Cterm, 80%) | `GRB14 (240-540)` + `TNKS2 (850-1166)` | `conf = 0.600`, `pTM = 0.434`, `ipTM = 0.221`, `pLDDT = 0.695` (234 contacts `<=5A`) | `RMSD = 0.49 A` (`final 0.62 A`), `<dG_GBn2> = -261.9 +/- 6.9 kcal/mol`, `<E_vdW> = -325.6` | Validated AKT-restoring mutagen `GRB14 Gln348Ala` (**`+4.19`**, `d=1.97A`), validated TNKS2 mutagen `Met1054Ala` (**`+1.11`**, `d=2.83A`), RF2 #1 `GRB14 Ala378` (`d=2.92A`); `TNKS2 Glu971Ala` (**`+13.72`**, `d=1.67A`) & `TNKS2 Glu970Ala` (**`+11.34`**, `d=1.97A`) |
| `10B_GRB14_Nterm_TNKS2_ARC34` | `GRB14(N-term)–TNKS2(ARC3-4)` (Axis 5B-Nterm, `PMID:11278563`) | `GRB14 (1-115)` + `TNKS2 (330-650)` | `conf = 0.635`, `pTM = 0.466`, `ipTM = 0.177`, `pLDDT = 0.749` (209 contacts `<=5A`) | `RMSD = 0.45 A` (`final 0.55 A`), `<dG_GBn2> = -168.6 +/- 9.8 kcal/mol`, `<E_vdW> = -264.5` | N-term `33-RGDAHD-38` motif `GRB14 Arg33Ala` (**`+8.31`**, `d=1.81A`) & `GRB14 Asp38Ala` (**`+5.39`**, `d=2.11A`), `TNKS2 Asp636Ala` (**`+5.17`**, `d=2.22A`), coding SAV `GRB14 Phe90Ala` (**`+1.35`**, `d=2.57A`, `rs61748245`, flanking `68-80` GIGYF1 motif), contacting ARC3/4 `Leu401` (`d=2.91A`) & `Leu560` (`d=2.86A`, **`+0.61`**) |
