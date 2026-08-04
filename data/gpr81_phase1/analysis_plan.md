# GPR81 / HCAR1 Structure–Biology Analysis Plan

## Revised scientific question

The goal is not merely to rank compounds by a docking score. The analysis should answer two linked questions:

1. **Five slide tool compounds**
   - Do the five compounds bind the same HCAR1/GPR81 pocket?
   - Which parts of the pocket does each compound occupy?
   - Which interactions are conserved, and which are compound-specific?
   - Which compounds appear structurally better matched to the experimentally observed agonist pocket, and why?

2. **Davidsson et al. (2020) lead-series optimization**
   - Does the reported optimization from the initial hit series to constrained analogues and amides produce a credible structural improvement?
   - Can the potency/selectivity/solubility trends be explained by changes in hydrogen-bond geometry, conformational restriction, pocket occupancy, ligand efficiency, or receptor selectivity?
   - Are there cases where biological improvement is not supported by a simple docking explanation?

## Confirmed input identity

- Target: human HCAR1/GPR81/HCA1/GPR104, UniProt Q9BXC0.
- Receptor chain for experimental structures: chain R.
- AZ1 / CID 57422810 / CHEMBL4641579: confirmed as Davidsson 2020 compound 1; hHCAR1 EC50 23 nM.
- GPR81 agonist 1 / CID 86279608 / CHEMBL6177006: not Davidsson 2020 compound 2; linked to Sakurai/Takeda 2014 compound 2; HCA1 activity approximately 50 nM.
- CHBA: CID 13071646; matched experimental reference ligand in RCSB 8Z87.
- 3,5-DHBA: CID 7424; matched experimental reference ligand in RCSB 9KT9.
- 3-OBA: CID 441; no matching co-complex in the current downloaded structure set.

## Phase 2: receptor and pocket preparation

1. Prepare HCAR1 chain R from 8Z87, 9KT9, 8Z8A, and 8Z8B.
2. Retain the experimental ligand coordinates as pocket anchors, not as proof that every ligand uses the identical pose.
3. Compare the CHBA-bound, 3,5-DHBA-bound, lactate-bound, and apo structures before defining a consensus docking region.
4. Record chain extraction, removed chains, retained heteroatoms, protonation assumptions, and pocket-box coordinates.
5. Use at least two experimentally anchored receptor conformations for the five-compound comparison. The ligand-bound structures should be treated as active-state references; the apo structure is a conformational control.
6. Do not silently claim that a predicted pose proves agonism. The structures and scores generate structural hypotheses.

## Phase 3: five-tool-compound binding-mode comparison

For each compound, generate and record:

- docking pose ensemble, not only pose 1;
- score and score spread across receptor conformations;
- pocket centroid and pocket-volume occupancy;
- contacts by residue and interaction type;
- hydrogen bonds, salt bridges, aromatic contacts, hydrophobic contacts, and ligand exposure;
- overlap with CHBA/3,5-DHBA/lactate reference ligand coordinates where meaningful;
- pose stability/consistency across receptor structures;
- ligand efficiency and basic physicochemical descriptors.

The comparison should distinguish:

- **Shared anchor interactions**: interactions reproduced across several compounds and supported by experimental ligand structures.
- **Pocket expansion**: additional subpockets or extracellular/intramembrane regions occupied by larger tool compounds.
- **Pose ambiguity**: multiple similarly scored poses or receptor-state-dependent pose switching.
- **Chemical-series advantage**: stronger interpretation only when structural fit is consistent with experimental potency and not just a more negative score.

“Better” should be reported as a multidimensional assessment:

- agonist-pocket compatibility;
- interaction completeness and geometry;
- pose reproducibility across receptor conformations;
- potency consistency with known biology;
- selectivity plausibility versus GPR109A/GHS-R1a where data exist;
- ligand efficiency and tractability.

## Phase 4: reverse validation of the paper optimization

The paper compounds are organized as:

- Acyl urea: compounds 1–25.
- Constrained analogues: compounds 26–31.
- Amides: compounds 32–39.

The analysis should use matched-pair comparisons from the paper tables, prioritizing:

- compound 1 vs related acyl-urea substitutions;
- compound 2 and its R1/R2/R3/RHS matched pairs;
- compound 15 → 26 and compound 21/22 → 28/30 where the constrained linker is introduced;
- compound 30 vs pyrimidone analogue 31;
- compound 35 → 36/37/38 for the amide-series stereochemical/substitution effects;
- compound 2/22/30/38 as representative cross-series comparisons where structure recovery permits.

For each matched pair, test whether the claimed improvement is structurally plausible through:

1. **Conformational restriction**
   - reduced torsional freedom;
   - preservation of the proposed intramolecular H-bond geometry;
   - lower pose entropy / fewer competing orientations.

2. **Hydrogen-bond pharmacophore**
   - retention of the required HBD/HBA pattern;
   - donor/acceptor orientation toward the receptor;
   - effects of N- or O-methylation that remove an HBD or HBA.

3. **Pocket vectoring**
   - whether the linker sends the LHS and RHS into the same or improved receptor regions;
   - whether the pyridone/pyrimidone is a credible acyl-urea bioisostere;
   - whether the amide changes the RHS vector enough to explain non-transferable SAR.

4. **Selectivity and physicochemical properties**
   - whether the pose can explain improved GPR81 vs GHS-R1a or GPR109A separation;
   - whether improved solubility is explained by reduced lipophilicity or disrupted crystal packing rather than stronger receptor binding;
   - whether potency and LLE improve together or trade off.

5. **Biology alignment**
   - compare structural hypotheses with reported hGPR81 EC50, efficacy, GPR109A, GHS-R1a, solubility, LogD, and LLE;
   - explicitly flag cases where docking cannot explain the observed biology.

## Required outputs

- `tool_compound_binding_mode_comparison.csv`
- `tool_compound_residue_interactions.csv`
- `tool_compound_pose_gallery.html`
- `paper_matched_pair_structure_biology.csv`
- `gpr81_optimization_reverse_validation.md`
- receptor-preparation manifest with chain and pocket coordinates

The final report must separate:

- experimental facts;
- computational observations;
- mechanistic interpretation;
- unresolved hypotheses.

It must not call a compound a confirmed hit or claim that docking proves agonism, affinity, or selectivity.

## Current blocker before full paper-series analysis

The main supplied PDF contains structure drawings but not machine-readable structures for compounds 1–39. Exact SMILES/SDF should be recovered from the article supplementary information, ChEMBL, PubChem, or another authoritative source before docking. Structures should not be reconstructed by guessing from low-resolution figures.
