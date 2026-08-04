# GPR81 / HCAR1 Phase-1 input package

This directory contains the auditable input-normalization output for the HCAR1/GPR81 small-molecule agonist docking request.

## Target identity
- Human HCAR1/GPR81/HCA1/GPR104
- UniProt: Q9BXC0
- Reviewed sequence length: 346 aa

## Tool compounds
`tool_compounds.csv` contains the five requested PubChem records, including CID, formula, molecular weight, canonical/connectivity SMILES, isomeric SMILES, and source URLs. The corresponding 3-D PubChem SDF files are under `ligands/`.

## Receptor structures
The strongest Phase-2 starting points are experimental human HCAR1-Gi cryo-EM structures, not AlphaFold alone:
- `structures/8Z87.cif`: CHBA-bound
- `structures/9KT9.pdb`: 3,5-DHBA-bound
- `structures/8Z8A.pdb`: lactate-bound
- `structures/8Z8B.pdb`: apo

`structure_records.json` records the RCSB titles, methods, release dates, and URLs.

## Paper series
`paper_compound_inventory.csv` inventories compounds 1-39 from the supplied Davidsson et al. (2020) paper across acyl urea, constrained analogue, and amide series. Potency values are transcribed from Tables 1-8. Structures are intentionally marked `figure_only_in_main_pdf`; no SMILES were guessed.

## Important limitations
This is an input package, not a docking result. Exact structures for the 39 paper compounds still require the article supplementary information or another authoritative structure source.
