# HCAR1 / GPR81 — Activation-direction safety & druggability assessment

> Date: 2026-08-04. Prepared as the 3_safety-style companion to the GPR81 docking campaign.
> Evidence: Open Targets Platform v4 (2026-08-04 pull, raw JSON in `HCAR1_ot_platform_2026-08-04.json`),
> UniProt Q9BXC0, GTEx v8, PubMed. Direction assessed: **ACTIVATION** (agonist program).
> Evidence labels: [FACT] database/paper-verified; [MECH] mechanism-based; [HYP] hypothesis; [GAP] no data.

## 1. Identity

| Field | Value |
|---|---|
| Gene | HCAR1 / GPR81 / HCA1 / GPR104 |
| Ensembl | ENSG00000196917 |
| UniProt | Q9BXC0 (346 aa, 7TM GPCR) |
| Function | L-lactate receptor; Gi-mediated anti-lipolysis [FACT, UniProt] |
| Localization | Cell membrane, multi-pass [FACT] |
| Pathways | G alpha(i) signalling; hydroxycarboxylic acid-binding receptors [FACT, OT] |
| Expression (GTEx v8, median TPM) | Breast 10.0, adipose visceral 5.7, spleen 3.7, salivary 2.8, adipose subcut. 2.7, thyroid 2.4, stomach 2.3; liver/kidney/muscle < 1.1 [FACT] |

## 2. Genetic constraint — UNDERPOWERED, no conclusion

gnomAD via OT: syn oe=0.96, mis oe=0.945, **LoF oe=0, oeUpper=1.77, upperBin=8**.
upperBin 8 is the weakest constraint bin; with zero observed LoF variants the
interval is uninformative [FACT]. **Do not read oe=0 as strong LoF intolerance** —
it means "no data". No genetic signal to hang either activation or inhibition risk on. [GAP]

## 3. KO phenotype (IMPC, LoF direction — indirect for activation)

17 records: skeleton (tibia, vertebra, pelvis), kidney morphology, **retina vasculature
+ cone electrophysiology + increased retina apoptosis**, hyperactivity, LGN morphology,
uterus physiology, **decreased effector-memory T-helper cells** [FACT, OT].
Interpretation for activation: LoF phenotype is NOT the mirror of activation risk;
these flag organ systems where the receptor has a physiological role worth monitoring
(retina, immune, kidney) but no direct activation-toxicity read. [MECH]

## 4. Cancer dependency (DepMap via OT)

1243 screens / 29 tissues; **7 cell lines with geneEffect < -0.5** (moderate, not strong
essentiality): NGP neuroblastoma -0.73, SNU-245 bile-duct -0.75, MY AML -0.69,
SCC-3 NHL -0.65, IM95/GSU gastric -0.50/-0.66, NMB neuroblastoma -0.51 [FACT].
Consistent with literature that lactate/HCAR1 signaling supports certain tumors [MECH].

## 5. Activation-direction risk (the score-relevant section)

### 🔴 HIGH — tumor promotion / cachexia
- **"Activation of GPR81 by lactate drives tumour-induced cachexia"** (PMID 38499763, 2024) [FACT]
- Lactate/GPR81 signaling role in cancer: angiogenesis, immune escape, Warburg metabolism (PMID 31836453, 2020) [FACT]
- MCT4-dependent lactate secretion suppresses antitumor immunity in LKB1-deficient lung ADC (PMID 37327788, 2023) [FACT, lactate/GPR81-dependent mechanism]
- → An HCAR1 agonist could accelerate occult tumors / worsen cachexia in cancer-prone patients. Direct consequence of the mechanism (lactate receptor), not a remote analogy. [MECH]
- Preclinical gate: carcinogenicity study + tumor-history exclusion criteria + body-composition/cachexia monitoring.

### 🔴 HIGH — liver fibrosis potentiation
- "Deletion of GPR81 activates CREB/Smad7 pathway and alleviates liver fibrosis in mice" (PMID 38982366, 2024): KO is protective ⇒ activation is predicted pro-fibrotic [FACT + MECH].
- Monitor liver stiffness/fibrosis markers (Pro-C3, ELF) in long-term studies.

### 🟡 MEDIUM — immune modulation (double-edged)
- Lactate suppresses macrophage pro-inflammatory response via GPR81 (YAP/NF-κB, PMID 33123172, 2020) [FACT]
- Anti-inflammatory in sepsis models (PMID 34363018, 2022) but immunosuppression could trade safety for efficacy in infection-prone populations [MECH].
- Immunophenotyping recommended; watch opportunistic infection signal.

### 🟡 MEDIUM — retina (direction-ambiguous)
- Müller-cell GPR81 regulates inner retinal vasculature (PMID 31220454, 2019); HCAR1 involved in neurovisual development (PMID 34208876, 2021) [FACT]
- BUT GPR81 activation is also reported neuroprotective in retinal explants (PMID 35805182, 2022) [FACT]
- → Monitor retinal exams; the net direction is unresolved. [HYP]

### 🟢 LOW / potential benefit
- Anti-lipolysis (intended mechanism); new 2026 report: lactate-activated GPR81/FARP1 drives insulin-independent glucose uptake (PMID 41530347) [FACT]
- Retinal protection potential (PMID 35805182).

## 6. Tractability

- SM: **Druggable Family** (class A GPCR) [FACT, OT] — small-molecule agonists feasible; no high-quality probe registered in OT chemicalProbes (empty) [FACT].
- AB: feasible in principle (membrane protein, extracellular epitopes) but an agonist antibody with the right pharmacology is a big lift.
- The Davidsson 2020 series (5 nM-1 uM EC50) is a credible starting point; tool compounds confirmed in this project.

## 7. Recommended preclinical safety package (activation program)

1. **Carcinogenicity (2-yr) + 6-mo Tg.ras** — tumor-promotion signal is mechanism-based, not hypothetical.
2. **Liver fibrosis markers** (Pro-C3, ELF, histology) in chronic toxicology.
3. **Ophthalmology** (fundoscopy, ERG) — retina is a receptor-dense tissue with ambiguous direction.
4. **Immunophenotyping** + infection monitoring — macrophage suppression signal.
5. **Body composition / cachexia readouts** in long-term studies.
6. **Cardiovascular**: lactate handling + heart-rate monitoring (Gi-coupled, adipose-driven metabolic shifts).
7. Clinical exclusion: active malignancy, history of cancer within N years.

## 8. Bottom line

HCAR1 agonism is metabolically attractive (anti-lipolysis + glucose uptake) but carries
**mechanism-based tumor-promotion/cachexia and liver-fibrosis risk** that must be treated
as RED until a carcinogenicity package and fibrosis biomarkers say otherwise; retina and
immune monitoring are secondary watch items.

---

# Appendix — HCAR2/GPR109A selectivity (program-level context)

- The niacin-flush side effect is mediated by **HCAR2 (GPR109A)** activation — the classic
  family lesson; any HCAR1 agonist program must demonstrate HCAR2/3 selectivity or accept
  flush as a dose-limiting side effect. [FACT, IUPHAR PMID 21454438; Si-containing
  GPR81/GPR109A agonists PMID 26459194]
- The Davidsson 2020 paper reports selectivity for its series (compound 38 noted as a
  "potent/selective example" in this project's inventory); **exact GPR109A EC50 values are
  in the paper but were not transcribed into this repo** — extract them for the final
  deliverable. [GAP]
- Structural angle: this project's docking is on HCAR1 only. An HCAR2 pocket comparison
  (AlphaFold3 or homology model of HCAR2 vs the cryo-EM HCAR1 structures) would let the
  docking campaign speak to selectivity directly; currently it cannot. [GAP → optional next step]

## Provenance
- `HCAR1_ot_platform_2026-08-04.json` — raw OT Platform v4 target pull (this folder).
- PubMed searches executed 2026-08-04 via E-utilities; PMIDs above.
- GTEx v8 median gene expression via gtexportal.org v2 API.
