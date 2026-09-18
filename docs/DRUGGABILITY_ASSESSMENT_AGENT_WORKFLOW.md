# End-to-End Druggability & Structural Pharmacology Assessment: Agent Workflow Standard

> **Document Version**: v1.0.0  
> **Date**: 2026-09-16  
> **Repository Anchor**: `/das/user/QYJI/druggability/`  
> **Target Class**: GPCRs (Peptide / Small-Molecule Modalities) & Soluble Therapeutic Targets  
> **Primary References**: OXTR Benchmark (PDB: 7QVM, 6TPK, 7DW9; Jira: RIC-403), GPR81/HCAR1 (RIC-396), GHSR (RIC-392/393)

---

## 1. Executive Summary & Design Philosophy

This document formalizes the production-grade **Autonomous Agent Workflow for Target Druggability & Structural Pharmacology Assessment**. It provides a standardized, battle-tested execution protocol that takes a target from literature ingestion and experimental cryo-EM/X-ray structures to:

1. **Dual-state binding pocket characterization** (active vs. inactive, activation triggers, exit vectors);
2. **Computational selectivity audit** (identifying tool limits across AI, static MM/GBSA, dynamic MD, and FEP);
3. **GPU-accelerated all-atom explicit-solvent dynamics** (A100-optimized unbinding & stability validation);
4. **Colleague-facing deliverables** (self-contained 3D interactive HTML, high-DPI publication plots, Jira automation, tiered wet-lab proposals).

```
                      TARGET DRUGGABILITY WORKFLOW PIPELINE
                      
  [Literature & PDBs] ──> Stage 1: Structural Curation & Core Alignment
                                 │
                                 ├──> Active vs. Inactive Superposition (Core TM1-TM4 RMSD)
                                 └──> Residue-Level Contact Fingerprinting (Exit vectors & Switched loops)
                                 │
                          Stage 2: Small-Molecule QC & Pocket Segmentation
                                 │
                                 ├──> Tight-Box (12-14 Å) AutoDock Vina Redocking (Centroid < 2.0 Å)
                                 └──> Grid Box Definitions (Orthosteric, Core sub-cavity, Vestibule)
                                 │
                          Stage 3: Multi-Tier In Silico Assessment & Dynamics
                                 │
                                 ├──> Layer 1: Boltz-2 / AlphaFold-Multimer (Backbone plausibility)
                                 ├──> Layer 2: Static MM/GBSA (Caveat: void artifact diagnosis)
                                 ├──> Layer 3: All-Atom Explicit-Solvent MD (A100 CUDA, RMSD, H-bonds)
                                 └──> Layer 4: Alchemical FEP Dual-Topology Setup (openmmtools.alchemy)
                                 │
                          Stage 4: Automated Delivery & Governance
                                 │
                                 ├──> Interactive 3Dmol.js HTML (Self-contained, crash-resilient)
                                 ├──> Pixel-Probed High-DPI Diagram (Novo Nordisk corporate palette)
                                 ├──> Jira Automation (RIC Individual Target task, 3-hop walk to In Progress)
                                 └──> Tiered Wet-Lab Validation Panel (In vitro, Ex vivo, In vivo)
```

---

## 2. Four-Stage Standardized Execution Protocol

### Stage 1: Structural Curation & Dual-State Profiling

1. **PDB Identification & Ingestion**:
   - Query RCSB REST API for high-resolution active state (G-protein coupled, agonist-bound, e.g. 7QVM 3.25 Å) and inactive state (antagonist-bound, e.g. 6TPK 3.20 Å).
   - Ingest counter-screen homologous receptor structures (e.g. V2R 7DW9 2.80 Å) for subtype selectivity analysis.
2. **Cleaning & Dissection**:
   - Strip non-physiological engineering fusion tags (BRIL, rubredoxin, T4L, antibody scFv fragments, heterotrimeric G-proteins) from the 7TM bundle.
   - Separate endogenous/synthetic peptide ligands and co-crystallized small molecules into dedicated coordinate files.
3. **Rigid-Core Superposition**:
   - Align all structures onto the active reference frame using invariant transmembrane helices (TM1–TM4, excluding flexible extracellular/intracellular loops).
   - *Acceptance Gate*: Invariant core CA RMSD $\le 2.0\text{ \AA}$.

### Stage 2: Small-Molecule QC & Pocket Segmentation

1. **AutoDock Vina QC Gating**:
   - Convert receptor to PDBQT via `obabel -xr` and ligand via `meeko.MoleculePreparation`.
   - **Tight-Box Protocol**: Center the box on the experimental ligand centroid with a compact boundary (12–14 Å) and `exhaustiveness >= 32` to eliminate the large-box deep-insert artifact.
   - *Pass Gate*: Re-docked pose centroid recovery $< 2.0\text{ \AA}$ vs. experimental crystal/EM pose.
2. **Sub-Pocket Segmentation**:
   - Partition the binding groove into functionally distinct grid boxes:
     * **Full Orthosteric Box**: Covers the global cavity from deep TM crevice to ECL loops.
     * **Core Sub-Pocket**: Deep cavity accommodating the aromatic activation trigger (e.g., Tyr2, Retosiban overlap).
     * **Vestibule Exit Box**: Extracellular entrance harboring subtype-specific residues and solvent-exposed exit vectors.
3. **Ultra-Large Screening Tool: DrugCLIP (NeurIPS 2023)**:
   - For novel target pockets without rich known chemical seeds, invoke `bbbkit.druggability.drugclip.screen_drugclip()` (`scripts/run_drugclip_screen.py`).
   - Rapidly filters 2.94M commercial/virtual compound library down to Top-K (e.g. 500) candidates via Pocket-Ligand contrastive representation space in seconds, before feeding into tight-box Vina docking and Boltz-2 cross-validation.

### Stage 3: Multi-Tier In Silico Assessment & Dynamics

Do not rely on a single scoring function. Screen across four orthogonal tiers:

| Tier | Computational Tool | Primary Metric | Role & Evaluation Gate |
| :--- | :--- | :--- | :--- |
| **Tier 1: AI Plausibility** | Boltz-2 (`@nn/DCD/Boltz-2:0.0.37`) | `iptm`, `complex_ipde` | Tests overall fold compatibility. **Mandatory Caveat**: Class A/B GPCR peptide pairs yield $iptm > 0.82$ across homologous subtypes; cannot predict functional potency. |
| **Tier 2: Static MM/GBSA** | OpenMM (Amber14SB + GBn2) | $\Delta G_\text{bind}$ (kcal/mol) | Fast single-point minimization. **Mandatory Caveat**: Deleting residues (e.g., Pro $\to$ Gly) creates artificial unrelaxed vacuum cavities (void penalty artifact). |
| **Tier 3: Explicit MD** | OpenMM (Amber14SB + TIP3P + 0.15M NaCl) on A100 | Backbone RMSD, H-bond persistence | **The Decisive Proof**: 1.0–5.0 ns production at 310 K, 1 bar. Cognate complexes remain stable (RMSD $< 1.5\text{ \AA}$, H-bond 100%); clashing subtypes show steric pushout. |
| **Tier 4: Alchemical FEP** | `openmmtools.alchemy` | Dual-topology $\Delta\Delta G$ | Formulate thermodynamic cycle: soft-core vdW ($\alpha=0.5, \beta=12$) + electrostatic decoupling over 11 $\lambda$ windows ($1.0 \to 0.0$). Export serialized XMLs. |

### Stage 4: Automated Delivery & Governance

1. **Interactive 3D HTML Deliverable**:
   - Single-file standalone HTML with embedded base64/PDB coordinate strings (no external server or CORS issues).
   - Driven by 3Dmol.js with custom color themes (Teal `#00857C`, Navy `#001965`, Coral `#D9383A`).
   - Pre-configured camera views: (1) Active complex, (2) Acylation vector, (3) Selectivity switch, (4) Dual-state superposition, (5) Cross-subtype steric clash.
2. **High-DPI Summary Diagrams**:
   - Multi-panel figure rendered via Matplotlib at 300 DPI.
   - Tested with deterministic **Pixel Ink Probes** to guarantee header breathing room ($>50\text{ px}$) and zero edge text truncation ($>200\text{ px}$ right margin).
3. **Jira Lifecycle Automation (RIC Board)**:
   - Create ticket under Component `Individual Target` with Requester set to the requesting colleague (e.g., `MUEW`, `UHYG`).
   - Execute the 3-hop transition walk: `To Do` $\to$ `Analysis` (Hop 1, id=11) $\to$ `In Progress` (Hop 2, id=21).
   - Post milestone progress comment citing UNC paths on the shared drive (`R:\DT\TDE_TV\shared_folder\QYJI\...`).
4. **Tiered Wet-Lab Validation Panel**:
   - Translate computational findings into concrete experimental protocols:
     * *Tier 1 (In Vitro)*: Primary Gq IP1/calcium flux + mandatory 4-plex counter-screen (V1a, V1b, V2) + $\beta$-arrestin bias.
     * *Tier 2 (Translational Ex Vivo)*: Human donor islets (Insulin vs. Glucagon secretion) + mature adipocyte lipolysis + skeletal myotube atrophy rescue.
     * *Tier 3 (In Vivo)*: Conscious radiotelemetry blood pressure (ruling out V1a vasoconstriction) + EchoMRI body composition (quantifying fat loss with 100% lean mass preservation).

---

## 3. Hard-Won Technical Traps & Battle Rules

### Trap 1: 3Dmol.js Surface Promise Hang & Viewer Freeze
* **Symptom**: Clicking "Toggle Surface" hangs the browser; subsequently clicking other preset views fails completely, forcing a hard page refresh.
* **Root Cause**: Modern 3Dmol.js executes `viewer.addSurface()` asynchronously in a WebWorker, returning a **`Promise` object** rather than an integer handle. Passing this Promise into `viewer.removeSurface(promise)` triggers `TypeError: Cannot read properties of undefined (reading 'length')`, crashing the main JavaScript thread and aborting subsequent `loadPreset()` execution.
* **The Rule**:
  1. Never pass surface handles to `removeSurface()`. Use `viewer.removeAllSurfaces()` exclusively.
  2. Protect surface addition with an asynchronous `.then()` callback and debounce flag:
  ```javascript
  let isSurfaceVisible = false, isGenerating = false;
  function removeSurfaceSafely() {
    isSurfaceVisible = false; isGenerating = false;
    if (viewer && typeof viewer.removeAllSurfaces === 'function') viewer.removeAllSurfaces();
  }
  function toggleSurface() {
    if (!viewer || isGenerating) return;
    if (isSurfaceVisible) { removeSurfaceSafely(); viewer.render(); return; }
    isGenerating = true;
    let p = viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 0.38, color: '#00857C'}, {model: 0});
    if (p && typeof p.then === 'function') {
      p.then(id => { isSurfaceVisible = true; isGenerating = false; viewer.render(); });
    }
  }
  ```

### Trap 2: Explicit-Solvent PME Mixed-Precision Overflow (NaN Coordinate Trap)
* **Symptom**: During NPT equilibration or early production MD on a subtype counter-screen (e.g., V2R:OXT_Gly), OpenMM crashes immediately with `OpenMMException: Particle coordinate is NaN`.
* **Root Cause**: When a peptide is modeled into a sterically constricted pocket (such as V2R where Helix I is displaced inward by 3.51 Å), initial Lennard-Jones repulsion between colliding atoms exceeds $10^5\text{ kJ/(mol}\cdot\text{nm)}$. Under CUDA `Precision: mixed`, the 32-bit fixed-point accumulator in the reciprocal PME space overflows during the line search, poisoning the gradient with `NaN`.
* **The Rule**:
  1. For clashing counter-screen complexes, run OpenMM CUDA with **`Precision: double`** (`props = {'Precision': 'double'}`). On an NVIDIA A100 GPU, double precision still delivers **~115 ns/day** on a 60,000-atom system.
  2. Execute a deep two-stage energy minimization (`maxIterations=1000, tolerance=5.0 kJ/(mol*nm)`) prior to initializing velocities.

### Trap 3: The Static MM/GBSA Point-Mutation Illusion
* **Symptom**: Static single-point MM/GBSA scores a validated selective agonist (e.g. OXT_Gly with Pro7Gly) worse than native (e.g., $-2.15$ vs. $-34.28\text{ kcal/mol}$), falsely predicting loss of binding.
* **Root Cause**: Truncating an amino acid sidechain in a rigid, frozen experimental lattice leaves an unrelaxed vacuum cavity. The forcefield penalizes the lost van der Waals contacts without allowing the surrounding loop (ECL3) and water network to dynamically relax or gain conformational entropy.
* **The Rule**: Always pair static scoring with **All-Atom Explicit-Solvent MD (50–100 ns)**. Measure dynamic contact retention and H-bond persistence rather than trusting rigid static $\Delta G$.

### Trap 4: Matplotlib Bounding-Box Clipping & Vertical Crowding
* **Symptom**: Main titles touch subtitles; table text in the rightmost column extends off the image canvas and gets sliced.
* **Root Cause**: Matplotlib's `text(wrap=True)` without an explicit renderer context fails to wrap long strings. Setting `gridspec top=0.92` places panel titles directly over subtitle baselines.
* **The Rule**:
  1. Enforce strict character line wrapping via Python's standard library: `textwrap.fill(text, width=64)`.
  2. Set `gridspec top <= 0.850`, leaving $\ge 50\text{ px}$ vertical ink clearance between Title, Subtitle, Divider, and Panel Cards.
  3. Validate final PNGs using automated **Pixel Probes**:
  ```python
  # Verify right edge has 0 ink in the last 40 pixel columns
  arr = np.array(Image.open(png_path).convert('L'))
  assert np.sum(np.abs(arr[:, -40:] - arr[0,0]) > 20) == 0, "Right-edge text truncation detected!"
  ```

### Trap 5: Jira RIC Board Transition Enforcement
* **Symptom**: API calls to transition RIC tickets fail with HTTP 400 despite `expand=transitions.fields` reporting `required=False`.
* **Root Cause**: The RIC workflow enforces hidden server-side validators at transition runtime.
* **The Rule**: Always execute the mandatory 2-step setup:
  - Step 1 (Create): Only post `project`, `summary`, `description`, `issuetype: Task`, `components: [{"name": "Individual Target"}]`, and `customfield_12903: {"name": "REQUESTER"}`.
  - Step 2 (Pre-populate via PUT): Set `customfield_14819` (Expected Delivery date), `customfield_20611` (`[{"value": "AI/ML"}]`, Skill), `customfield_20612` (`{"value": "Supporting path"}`, Criticality), `customfield_20300` (`{"value": "1-3 days"}`, Effort).
  - Step 3: Transition sequentially: `11` (To Do $\to$ Analysis) then `21` (Analysis $\to$ In Progress), and re-PUT assignee to `QYJI` (workflow clears assignee on status change).

---

## 4. Directory & File Organization Standards

For any new target assessment, instantiate the following standardized structure:

```
/das/user/QYJI/druggability/<TARGET>_assessment/
├── raw_pdb/               # Pristine downloaded CIF/PDB files (7QVM, 6TPK, etc.)
├── structures/            # Cleaned, standardized, core-aligned PDBs
│   ├── <PDB>_active_receptor.pdb
│   ├── <PDB>_active_complex.pdb
│   ├── <PDB>_inactive_receptor_aligned.pdb
│   └── <MUTANT>_complex.min.pdb
├── grids/                 # AutoDock Vina inputs and parameters
│   ├── grid_definitions.json
│   ├── <PDB>_receptor.pdbqt
│   └── <LIGAND>_redocked.pdbqt
├── boltz_inputs/          # Cross-subtype Boltz-2 YAML configurations
│   ├── boltz_matrix_manifest.yaml
│   └── <RECEPTOR>_<PEPTIDE>.yaml
├── md_runs/               # Explicit-solvent MD production runs
│   ├── <SYSTEM_A>/        # production.dcd, solvated_system.pdb, trajectory_data.csv
│   └── <SYSTEM_B>/
├── fep_setup/             # Alchemical dual-topology FEP systems
│   ├── <SYSTEM>_alchemical_system.xml
│   └── <SYSTEM>_fep_manifest.json
├── reports/               # Deliverables for biologists and stakeholders
│   ├── <TARGET>_druggability_and_structure_report.html   # Standalone 3D report
│   ├── <TARGET>_druggability_summary.png                 # Overview publication plot
│   ├── md_stability_and_ensemble_comparison.png          # Trajectory validation plot
│   ├── redocking_benchmark.json                          # QC audit numbers
│   └── selectivity_computational_benchmark.json
└── scripts/               # Reproducible pipeline automation scripts
```

**CIFS Synchronisation Rule**:  
All files in `structures/`, `grids/`, `boltz_inputs/`, `fep_setup/`, and `reports/` must be synchronized to the CIFS shared mount (`/TDE_TV/shared_folder/QYJI/druggability/<TARGET>_assessment/`). All colleague-facing links in Jira and emails must be written in Windows UNC format:  
`R:\DT\TDE_TV\shared_folder\QYJI\druggability\<TARGET>_assessment\reports\...`

---

## 5. Reusable Code Template Arsenal

### Script 1: Multi-Structure Preparation & Core Alignment
`scripts/prepare_and_align_structures.py`
- Ingests PDB/CIF via Biopython `MMCIFParser` and `PDBParser`.
- Extracts 7TM receptor domain, separates co-factors and ligands.
- Performs rigid-body superposition on TM1–TM4 core ($C_\alpha$ atoms).
- Generates aligned active, inactive, and homologous counter-screen complexes.

### Script 2: Pocket Segmentation & Vina Redocking QC
`scripts/analyze_pockets_and_redock.py`
- Measures geometric extents and pocket coordinates with 8 Å padding.
- Automatically generates `grid_definitions.json`.
- Runs Meeko ligand preparation and AutoDock Vina tight-box redocking (`exhaustiveness=32`).
- Asserts centroid recovery gate ($< 2.0\text{ \AA}$) and logs `redocking_benchmark.json`.

### Script 3: A100 GPU Explicit-Solvent Molecular Dynamics
`scripts/run_stability_md.py`
- Solvates complex in TIP3P water box (1.0 nm padding) with 0.15 M NaCl.
- Parameterizes with Amber14SB + PME on CUDA platform (`Precision: double` for clashing systems).
- Executes NPT equilibration (50 ps) and production (1.0–5.0 ns).
- Computes trajectory RMSD, activation hydrogen bond persistence, and relative pocket drift via MDTraj.

### Script 4: Alchemical FEP Thermodynamic Cycle Setup
`scripts/setup_alchemical_fep.py`
- Identifies target mutating residue in peptide chain.
- Isolates sidechain atoms ($C_\beta, C_\gamma, C_\delta$ and hydrogens) for decoupling.
- Instantiates `openmmtools.alchemy.AbsoluteAlchemicalFactory` with softcore Lennard-Jones potential.
- Configures 11-stage $\lambda$ schedule (Coulomb discharge $\to$ softcore vdW scaling) and serializes OpenMM XML.

### Script 5: 3Dmol.js Standalone Interactive Viewer Generator
`scripts/build_oxtr_visualization_report.py`
- Embeds cleaned PDB coordinates directly into JavaScript strings.
- Implements asynchronous `removeAllSurfaces()` surface management with state debouncing.
- Constructs multi-preset camera routing to highlight activation switches, acylation vectors, and steric clashes.

---

## 6. Target Assessment Checklist (Before Handover)

- [ ] **Dual-state PDBs resolved**: Active (agonist-bound) and Inactive (antagonist-bound) structures curated and aligned.
- [ ] **Core alignment verified**: Invariant TM1–TM4 core RMSD $< 2.0\text{ \AA}$.
- [ ] **Redocking QC passed**: Small-molecule co-crystal redocking achieves centroid recovery $< 2.0\text{ \AA}$.
- [ ] **AI prediction caveats documented**: Boltz-2 / AlphaFold $iptm$ false-positive risk explicitly highlighted.
- [ ] **Dynamic MD conducted**: At least 1.0 ns explicit-solvent trajectory completed on A100 GPU, confirming binding stability (RMSD $< 1.5\text{ \AA}$) vs. counter-screen clash.
- [ ] **FEP manifest generated**: 11-window alchemical schedule and XML model serialized for prospective optimization.
- [ ] **Deliverable files checked**:
  - [ ] Standalone 3D HTML opens smoothly with working surface toggle and presets.
  - [ ] High-DPI summary PNG verified by pixel probe (0 ink in rightmost 40 columns; header gaps $>50\text{ px}$).
  - [ ] Files synchronized to CIFS `R:\DT\TDE_TV\shared_folder\QYJI\...`.
- [ ] **Jira ticket updated**: RIC Individual Target task created, transitioned to `In Progress`, and progress comment posted.
- [ ] **Email drafted**: English deliverable email prepared for the requesting scientist with actionable wet-lab testing proposals.
