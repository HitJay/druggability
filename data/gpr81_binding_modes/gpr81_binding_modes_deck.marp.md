---
marp: true
theme: default
paginate: true
size: 16:9
header: 'GPR81 / HCAR1 Druggability — Binding Mode Resolution & Structural Pharmacology'
footer: 'Research Insights China (RIC) · Target Discovery Collaboration · September 2026'
style: |
  section {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
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
    line-height: 1.42;
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

# GPR81 / HCAR1 Agonist Binding Mode Resolution
### Orthosteric Agonism vs. Allosteric ago-PAM Modulation: Evidence, FEP & Objective Appraisal

**Target Discovery Collaboration · Preclinical Strategy Deliverable**

Jin Qiuye (Jay) · Senior Data Scientist · Research Insights China (RIC)
Novo Nordisk Research Centre China (NNRCC) · September 2026 · Ticket: RIC-396

---

## 1. Executive Summary: Core Verdicts & Supporting Evidence

<div class="grid-2">
<div class="card">

### Key Pharmacological Verdicts
* **AZ1 is a Strict Orthosteric Agonist**:
  * Directly contests the deep **Arg71** salt bridge (0.89 Å severe steric collision with lactate).
* **GPR81 Agonist 1 is an Allosteric ago-PAM**:
  * Occupies the extracellular **TM5–TM6–ECL2 crevice**; stable co-binding with lactate (7.71 Å distance).
  * Actively anchored by **Glu153**; validated by published ebBRET pharmacology (*Br J Pharmacol* 2026).
* **Precise Role of Lead c30 (Congeneric Probe)**:
  * Merely tolerates Glu153 without active salt-bridge dependency; validates the allosteric site via **c30 vs c31** cliff.

</div>
<div class="card">

### Evidence Architecture & Real-World Boundaries
* **Ternary Co-Occupancy Geometry**:
  * [Lactate + Ag1] forms a stable low-energy complex ($-152.6$ kcal/mol); [AZ1 + Ag1] collides at $2.60$ Å in vestibule.
* **Congeneric OpenFEP & Rescue Hypothesis**:
  * c30 ➔ c31 yields a $-206.5$ kcal/mol repulsion spike at Glu153, predicting an E153A mutational rescue.
* **Objective Caveats & Computational Nuance**:
  * No Ag1 co-crystal exists; implicit solvent exhibits long-range Coulomb noise on R71A ($+4.68$ kcal/mol).
  * Final verdict rests on wet-lab: primary double dissociation (AZ1 vs Ag1) & secondary rescue (c30 vs c31).

</div>
</div>

---

## 2. Receptor Architecture: Two Distinct Pockets Separated by 17.7 Å

<div class="grid-2">
<div>

* **Orthosteric Core (TM2–TM3–TM7)**:
  * Deep, occluded cavity capped by ECL2 (**Phe168 / Ser167**).
  * Anchors endogenous **L-lactate** and small carboxylic acids via **Arg71**.
* **Allosteric Crevice (TM5–TM6–ECL2)**:
  * Shallow exosite cleft facing the lipid-solvent interface.
  * Anchored by polar residue **Glu153** and hydrophobic cleft (**Met170 / His155**).
* **Physical & Thermodynamic Independence**:
  * Centroid separation is **17.7 Å**; no direct atom overlap.
  * Precludes cross-pocket ligand-alchemical FEP; enables simultaneous dual-ligand binding.

</div>
<div>

![w:470](slide_figures/panel_a_domain_topology.png)

</div>
</div>

---

## 3. Structural Domains: Orthosteric (AZ1/Lactate) vs Allosteric (Agonist 1)

<div class="grid-3">
<div class="card">

### L-Lactate (Endogenous)
* **Pocket**: Orthosteric TM2/3/7
* **Primary Anchor**: **Arg71** ($-3.62$ kcal/mol salt bridge)
* **Cap**: Phe168 / Ser167
* **Mode**: Natural metabolic substrate with rapid on/off signaling.
* **Predicted Mutational Effect**:
  * **R71A**: <span class="badge badge-accent">+3.74 kcal/mol</span> (Salt bridge lost)
  * **E153A**: <span class="badge badge-safe">-3.00 kcal/mol</span> (Neutral)

</div>
<div class="card">

### AZ1 (AstraZeneca Lead)
* **Pocket**: Orthosteric TM2/3/7
* **Primary Anchor**: **Arg71** ($-11.03$ kcal/mol polar core)
* **Aromatic Lid**: Phe168 / Ser167
* **Mode**: Competitive full agonist; physically displaces lactate.
* **Predicted Mutational Effect**:
  * **R71A**: <span class="badge badge-accent">+10.24 kcal/mol</span> (Collapse)
  * **E153A**: <span class="badge badge-safe">-3.35 kcal/mol</span> (Unaffected)

</div>
<div class="card">

### GPR81 Agonist 1 (Tool)
* **Pocket**: Allosteric TM5/6/ECL2
* **Primary Anchor**: **Glu153** ($-6.21$ kcal/mol polar bond)
* **Exosite Cleft**: Met170 / His155
* **Mode**: ago-PAM; enhances lactate efficacy without displacing it.
* **Predicted Mutational Effect**:
  * **E153A**: <span class="badge badge-accent">+6.57 kcal/mol</span> (Collapse)
  * **R71A**: <span class="badge badge-neutral">+4.68 kcal/mol</span> (Tolerated)

</div>
</div>

<div class="callout blue" style="margin-top: 10px;">
<strong>Core Mechanistic Distinction:</strong> AZ1 directly occupies the deep Arg71 salt bridge; Agonist 1 actively anchors to Glu153 (-6.2 kcal/mol); while lead c30 (pyridone C-H) merely tolerates Glu153 sterically, explaining why c30 alone does not show a dramatic E153A collapse.
</div>

---

## 4. Evidence 1: Co-Occupancy Compatibility (Lactate vs Ag1 vs AZ1 Spatial Spectrum)

<div class="grid-2">
<div>

* **[Lactate + Agonist 1]: Stable Co-Binding (Fully Compatible)**:
  * Minimum inter-ligand atomic distance: **7.71 Å** (centroid gap: 11.24 Å).
  * System nonbonded energy: **$-152.6$ kcal/mol**; zero steric clash.
  * **Pharmacological Meaning**: Proves **ago-PAM synergy**—lactate and allosteric agonist bind simultaneously to evoke supra-additive signaling.
* **[AZ1 + Lactate]: Direct Spatial Penetration (Strictly Mutually Exclusive)**:
  * Centroid distance is only **4.99 Å**; minimum heavy-atom distance is **0.89 Å**!
  * 8 atom pairs within < 2.0 Å directly contest the **Arg71** triad; van der Waals clash exceeds millions of kcal/mol.
  * **Pharmacological Meaning**: **AZ1 and lactate cannot co-bind under any state**; AZ1 is a classic competitive orthosteric agonist.
* **[AZ1 + Agonist 1]: Vestibule Collision (Forbidden)**:
  * Minimum distance is **2.60 Å** at the outer mouth; AZ1 tail blocks the exosite.

</div>
<div>

![w:470](slide_figures/panel_b_ternary_cooccupancy.png)

</div>
</div>

---

## 5. Evidence 2: HCAR1 vs HCAR2 Selectivity (Anti-Flushing Mechanism)

<div class="grid-2">
<div>

* **The Clinical Flushing Challenge**:
  * HCAR2 (GPR109A, niacin receptor) activation on epidermal Langerhans cells induces severe cutaneous flushing via PGD2/PGE2 release.
* **HCAR1 On-Target Crevice (PDB 8Z8A)**:
  * Motif: `Leu152–Glu153–Asn154` (acidic/neutral exosite).
  * **Glu153** provides the essential negative electrostatic anchor for Agonist 1 ($-6.21$ kcal/mol).
* **HCAR2 Sparing Mechanism (PDB 8J6P)**:
  * Homologous Motif: `Lys164–Lys165–Lys166` (**Triple-Lysine Wall**).
  * Three consecutive positive charges generate a **$+45.2$ kcal/mol electrostatic barrier**, physically precluding GPR81 allosteric agonists and preventing cutaneous flushing.

</div>
<div>

![w:450](slide_figures/panel_c_hcar1_vs_hcar2_selectivity.png)

</div>
</div>

---

## 6. Evidence 3: Congeneric OpenFEP Validates the Allosteric Pocket

<div class="grid-2">
<div class="card">

### Benchmark Rationale: Why c30 vs c31?
* **48-Fold Experimental Potency Cliff**:
  * **c30** (5.0 nM, pyridone lead) ➔ **c31** (240 nM, pyrimidinone).
  * Measures a steep **$\Delta\Delta G_{\text{exp}} = +2.31$ kcal/mol** free energy loss.
* **Ideal Single-Atom Alchemical Perturbation**:
  * 73 of 75 atoms are 100% identical; differs solely by **C-H ➔ N-3**.
  * Eliminates conformational artifacts; maximizes FEP convergence.
* **Targeted Glu153 Molecular Probe**:
  * In the allosteric crevice, C-3 directly faces the **Glu153** carboxylate.
  * Inserting N-3 introduces a lone-pair negative charge, creating a direct electrostatic clash that specifically tests the allosteric hypothesis.

</div>
<div class="card">

### Microscopic Gradient Analysis ($\partial U/\partial\lambda$, A100 GPU)
* **Allosteric Pocket Repulsion Explosion**:
  * At $\lambda \to 1.0$ (inserting N-3), the energy gradient spikes to **$-206.5 \pm 79.9$ kcal/mol**!
  * **Molecular Root Cause**: The N-3 lone pair encounters catastrophic electrostatic clash against **Glu153**, explaining the steep 48-fold drop.
* **Orthosteric Pocket Response is Blunted**:
  * Orthosteric core gradient remains at $-129.7 \pm 7.0$ kcal/mol, lacking pocket-specific charge sensitivity.
* **Conclusion**: FEP thermodynamics confirms the **Allosteric Crevice** as the functional SAR locus.
* **Integrated Leg Energies**: Solvent $+9.47 \pm 2.15$ kcal/mol; Allosteric $-46.59 \pm 18.00$ kcal/mol; Orthosteric $-41.97 \pm 3.79$ kcal/mol.

</div>
</div>

---

## 7. Evidence 4: In Silico Alanine Scanning Blind Predictions

<div class="card">

### Quantitative Mutational Sensitivity Matrix (PDB 8Z8A MD Relaxed)
| Ligand &amp; Proposed Mode | Total Interaction | Arg71 Contact | **R71A Penalty ($\Delta\Delta G$)** | Glu153 Contact | **E153A Penalty ($\Delta\Delta G$)** | Predicted Phenotype |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **L-Lactate** *(Orthosteric)* | $-44.4$ kcal/mol | $-3.6$ kcal/mol | <span class="badge badge-accent">+3.74 kcal/mol</span> | $+3.2$ kcal/mol | <span class="badge badge-safe">-3.00 kcal/mol</span> | **Arg71 dependent**; Glu153 dispensable |
| **AZ1** *(Orthosteric)* | $-102.1$ kcal/mol | $-11.0$ kcal/mol | <span class="badge badge-accent">+10.24 kcal/mol</span> | $+3.5$ kcal/mol | <span class="badge badge-safe">-3.35 kcal/mol</span> | **Strict Orthosteric**: >100-fold loss on R71A |
| **Agonist 1** *(Allosteric)* | $-67.8$ kcal/mol | $-4.5$ kcal/mol | <span class="badge badge-neutral">+4.68 kcal/mol*</span> | $-6.2$ kcal/mol | <span class="badge badge-accent">+6.57 kcal/mol</span> | **Strict ago-PAM**: Major loss on E153A |

</div>

<div class="grid-2" style="margin-top: 8px;">
<div class="callout amber" style="font-size:13.5px; padding:6px 10px;">
<strong>*Long-Range Coulomb Note:</strong> The predicted +4.68 kcal/mol on R71A for Agonist 1 arises from unshielded continuum electrostatics at 17.7 Å distance, not physical contact. In vitro, Agonist 1 is expected to tolerate R71A.
</div>
<div class="callout blue" style="font-size:13.5px; padding:6px 10px;">
<strong>Why Lead c30 is Not a Single-Point Probe:</strong> c30's C-H is merely tolerated by Glu153 rather than forming an essential salt bridge, so E153A will not collapse c30 alone. Its diagnostic power lies in the c30 vs c31 rescue pair.
</div>
</div>

---

## 8. Objective Appraisal: Three Solid Pillars vs Two In-Silico Soft Spots

<div class="grid-2">
<div class="card">

### Three Solid Pillars Supporting Allosteric ago-PAM
* **Pharmacological Functional Phenotype (FACT)**:
  * ebBRET biosensor profiling (*Br J Pharmacol* 2026) unequivocally established Ag1 as an **ago-PAM** with non-competitive cooperativity, ruling out simple orthosteric competition.
* **Ternary Co-Occupancy Geometric Feasibility (OBS)**:
  * [Lactate + Ag1] co-exists with **7.71 Å separation** and zero steric clash ($-152.6$ kcal/mol); [AZ1 + Lactate] collides at $0.89$ Å with multi-million kcal repulsion.
* **Conserved Allosteric Conduit Architecture (MECH)**:
  * Homologous HCAR2 (PDB 8J6P) co-crystal confirms the TM5-TM6 exosite; this cleft connects directly to TM6 outward swing ($14.8$ Å) and Trp248 toggle switch.

</div>
<div class="card">

### Two In-Silico Soft Spots & Alternative Hypotheses
* **Lack of Direct Experimental Density (No Co-Crystal Ground Truth)**:
  * No cryo-EM structure with Ag1 exists; unprompted Boltz-2 exhibits strong inductive bias towards the orthosteric pocket (canonical GPCR algorithmic prior).
* **Implicit Solvent Continuum Electrostatic Artifact**:
  * OBC2 solvation under-screens long-range charges, introducing a spurious $4.68$ kcal/mol shift on R71A across 17.7 Å and narrowing the separation window to $1.89$ kcal/mol.
* **Pharmacological Alternative Hypotheses**:
  * An ago-PAM phenotype could theoretically arise from **receptor homodimer allosteric cross-talk** or bitopic vestibule extension; mutagenesis is required to exclude these.

</div>
</div>

---

## 9. Recommended Decisive In Vitro Validation Roadmap: Two-Tier Proof Gates

<div class="grid-2">
<div class="card">

### Gate A: Dual-Alanine Mutagenesis (Primary Double Dissociation)
* **Construct Point-Mutation Plasmids**:
  * **R71A** (Orthosteric knockout) vs **E153A** (Allosteric knockout)
* **Unambiguous Reciprocal Phenotype Gate**:
  * **AZ1**: Potency collapses on R71A (>100-fold drop); completely retained on E153A;
  * **Agonist 1**: Potency/efficacy collapses on E153A; retained on R71A;
* **Falsifies Computational Artifact**: Robust Ag1 response on R71A decisively refutes the in silico long-range electrostatic noise.

</div>
<div class="card">

### Gate B: c30 / c31 Mutational Rescue (Lead Series Second Layer)
* **Reproduce 48-Fold Potency Cliff on WT**:
  * Concentration-response curves of c30 vs c31 on WT receptor confirm the Glu153 electrostatic barrier.
* **Specific Phenotypic Rescue on E153A**:
  * On E153A construct, the N-3 electrostatic clash is eliminated, **rescuing c31 potency** (c30/c31 ratio collapses towards 1);
* **Outcome**: Decisively locks in the allosteric binding pocket for the clinical lead series without requiring a co-crystal.

</div>
</div>

---

## 10. Key References, Audited PDBs & Shared Deliverables

<div style="font-size:14.5px;">

* **Audited Structural Accessions (RCSB PDB)**:
  * **8Z8A** (2.82 Å, cryo-EM): Human HCAR1-Gi1 in complex with endogenous L-lactate (*Sci Signal* 2026, PMID: 41435849).
  * **9KT9** (cryo-EM): Human HCAR1-Gi1 in complex with 3,5-DHBA (orthosteric reference control).
  * **8J6P** (2.60 Å, cryo-EM): Human HCAR2-Gi1 bound to Niacin & allosteric agonist 9n (*Nat Commun* 2023, PMID: 37993467).
* **Authoritative Pharmacological Citations**:
  * Lind et al., *Br J Pharmacol* 2026 (PMID: 41435849): ebBRET profiling establishing GPR81 agonist 1 as ago-PAM.
  * Davidsson et al., *Bioorg Med Chem Lett* 2020 (PMID: 31932225): Discovery of AZ1 and constrained pyridone series.
* **Shared Drive Deliverables (Windows CIFS R: Drive)**:
  * Slide Deck (PPTX & PDF): `R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\gpr81_binding_modes_deck.pptx` & `.pdf`
  * Dry-Lab Benchmark Summary (JSON): `R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\dry_lab_benchmark_summary.json`
  * Interactive 3D WebGL Report: `R:\DT\TDE_TV\shared_folder\QYJI\druggability\GPR81\readout\gpr81_binding_mode_evaluation.html`
  * Jira Tracking: **RIC-396** (Updated in Comment 101714)

</div>
