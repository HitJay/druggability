# GPR81 next-step plan after supplementary-material discovery

## Newly confirmed input

Supporting material:
`/TDE_TV/shared_folder/QYJI/druggability/GPR81/1-s2.0-S0960894X20300068-mmc1.docx`

The document is the correct Elsevier supplementary material for Davidsson et al. (2020), PII `S0960894X20300068`.

It contains:

- synthesis Schemes 1-8;
- experimental sections for compounds 1-39;
- MS `[M+H]+` values and NMR data for compounds 3-39, plus the compound-1/28b section;
- enough synthetic context to distinguish acyl-urea, constrained-analogue, and amide series.

The embedded structure drawings are EMF vector images inside the DOCX. The document does not contain SMILES, SDF, molfile, or a machine-readable chemical table. The temporary `~$...docx` file is an Office lock file and is not an input.

## Why the plan changes

The supplementary document removes the previous blocker that the paper series could not be traced beyond the main-paper figures. However, exact structures still need to be reconstructed and validated from the embedded drawings. MS values and synthesis context provide strong validation constraints but are not sufficient by themselves to uniquely determine every structure.

P3.5 also showed that independently docked pose RMSD can be very large even when receptor backbone alignment is good. Therefore, raw cross-receptor pose RMSD must not be interpreted as biological state preference without an experimental-ligand redocking/control step.

## Priority 1 — recover and validate paper-series structures

**STATUS UPDATE (2026-08-03, later same day): UNBLOCKED.** The user exported the DOCX supplementary material to PDF (`1-s2.0-S0960894X20300068-mmc1.pdf`, same shared folder) and dropped it into the shared folder. PyMuPDF renders PDF pages to PNG natively (no LibreOffice/EMF renderer needed), which sidesteps the entire EMF blocker described below. The blocker history is kept for reference since the same problem will recur for any future EMF-only document.

**Original blocker (resolved):** structure recovery from the 8 embedded EMF drawings (Schemes 1–8) inside the DOCX could not proceed — see the attempted/failed list below. The PDF export avoids EMF entirely because pypdf/PyMuPDF rasterizes PDF vector graphics directly.

Attempted, in this environment, without success (for the DOCX/EMF path specifically):
- `convert`/ImageMagick: delegate is hardcoded to `libreoffice --convert-to pdf`, which is not installed.
- `mamba install -c conda-forge libreoffice` / `libreoffice-impress`: package does not exist on conda-forge for this platform.
- PIL/Pillow: opens the EMF header (reports correct pixel size) but has no EMF/WMF raster loader — `im.load()` raises `OSError: cannot find loader for this WMF file`.
- System `libwmf-lite` (already installed, `libwmflite-0.2.so.7`): confirmed via `ldd` to be linked only against libm/libpthread/libc — no gd/cairo/freetype rendering backend, so `wmf_play()` has no output target. This is a headless "lite" build; it cannot rasterize.
- No PyPI package for EMF parsing exists (`pyemf`, `emf2svg-py`, `python-emf` all return no matching distribution).
- No `wine`, `libreoffice`, `unoconv`, `inkscape`, or WMF CLI tools (`wmf2eps`, `wmf2gd`) are present, and none are installable without sudo or a working conda-forge package.

Rejected approach (still rejected, applies regardless of format): manually parsing raw EMF drawing records (POLYLINE/POLYLINE16/EXTTEXTOUTW byte offsets) to reconstruct bond connectivity was evaluated and explicitly rejected — this would amount to guessing molecular structure from unverified low-level pixel/vector coordinates, which violates the project's rule against inferring SMILES from ambiguous image data.

**Recovery method actually used (validated):**
1. Render each PDF page to a 300 DPI PNG via PyMuPDF (`page.get_pixmap(dpi=300)`).
2. Use vision analysis to read each page's chemical structures, cross-referencing both the supplementary-material PDF (schemes + MS/NMR) and the main paper PDF (Table 1–8 structures + reported EC50/LogD/LLE).
3. Construct a candidate SMILES from the vision-read structure.
4. **Before accepting**, cross-check independently: (a) query ChEMBL for activities linked to document CHEMBL4610061 (this paper) and find an EC50 matching the paper-reported value; (b) compare the ChEMBL canonical SMILES against the vision-derived SMILES — accept only if they match; (c) compute exact `[M+H]+` and compare against the supplementary MS value.
5. If any check fails (as happened for compound 22, see below), reject the candidate and mark it `unresolved_MS_mismatch` rather than force-fitting or guessing further.

**Results this session (compounds 1 and 2 only):**
- **Compound 1** (= tool compound AZ1/CID 57422810, already fully identity-resolved in Phase 1): vision-read Table 1 structure independently reproduces the known SMILES. Formula C26H27ClN6O5S2, calc [M+H]+ = 603.1246. Status: `authoritative`.
- **Compound 2**: vision-read Table 1 structure (R1=Cl, R2=OEt, R3=morpholin-4-yl, RHS=benzothiazole-CH2-4-methylpiperazine) independently matches the ChEMBL canonical SMILES for CHEMBL4632411 (EC50=74.0 nM, matching paper's reported 0.074 µM) EXACTLY. Formula C27H33ClN6O4S, calc [M+H]+ = 573.2045. PubChem CID 154699458 (found via InChIKey lookup). Status: `authoritative`.
- **Compound 22 (attempted, rejected)**: candidate built from compound 2's core + compound 1's RHS gave calc [M+H]+ = 622.1555, but the SI reports 627.1839 for entry "22." — a 5.28 mass unit mismatch. The candidate is **wrong** and was not accepted. Root cause not yet diagnosed (likely wrong R3 substituent or RHS variant). Status: `unresolved_MS_mismatch`.

**Scope note:** only compounds 1 and 2 were fully recovered and validated this session. The remaining 36 compounds (3–21, 23–39) were NOT attempted beyond the one rejected trial (22) — extending the method is straightforward in principle (PDF rendering works, vision reading works, ChEMBL cross-validation works) but requires the same per-compound discipline for each of the 36 remaining structures, which is substantial additional work not completed here. See `paper_structures_recovered.json` for the full machine-readable record.

Recovery for the high-value matched pairs (15→26, 21/22→28/30, 30→31, 35→36/37/38) has not yet been attempted — the compound-22 mismatch means the RHS/R3 numbering-to-structure mapping cannot yet be assumed reliable for the 15–22 Table 5 series and needs care.

1. Extract the eight EMF images and associate each image with Scheme 1-8 and the relevant compound-number labels. [DONE — 8 images extracted to /tmp, mapped to Schemes 1-8 by document order; superseded by the PDF-based approach]
2. Convert EMF to a readable high-resolution raster/vector format using a compatible office/vector renderer. [OBSOLETE — sidestepped via user-provided PDF export + PyMuPDF rendering, no EMF conversion needed]
3. Recover structures for the high-value matched pairs first:
   - 1, 2; [DONE — both authoritative]
   - 15 -> 26;
   - 21/22 -> 28/30;
   - 30 -> 31;
   - 35 -> 36/37/38.

4. Use the drawing plus synthesis route to construct candidate structures.
5. Validate every candidate with:
   - exact molecular formula and calculated `[M+H]+` against the supplementary MS;
   - expected N/O/S/Cl count;
   - series/linker identity;
   - stereochemistry and cis/trans or S,S/R,R labels where reported;
   - PubChem/ChEMBL match when available.
6. Mark each structure as `authoritative`, `reconstructed_and_MS_validated`, or `unresolved`; unresolved structures are excluded from docking.

## Priority 2 — repair the docking validation design before interpreting P3.5

1. Redock CHBA, 3,5-DHBA, and lactate using their experimental coordinates as controls.
2. Report both:
   - pose recovery RMSD versus the experimental ligand coordinates;
   - unconstrained docking score/pose ensemble.
3. Add a restrained or reference-guided docking condition for the small acid ligands, while retaining the unconstrained result as a separate hypothesis.
4. Use the controls to determine whether the current box/scoring setup can reproduce the known pocket at all.
5. For the large AZ1 and Takeda agonist, run multiple random seeds and higher exhaustiveness only after the control behavior is documented.
6. Do not use independent-pose RMSD alone to claim receptor-state preference.

## Priority 3 — redo the five-tool-compound comparison

For each tool compound, combine:

- experimental-pocket control/redocking result;
- multi-seed score distribution;
- pose-cluster occupancy after receptor alignment;
- conserved and ligand-specific contacts;
- interaction geometry;
- known experimental activity and selectivity;
- molecular weight, ligand efficiency, and physicochemical liabilities.

The output should classify each compound as:

- stable common-pocket binder hypothesis;
- conformation-sensitive/alternative-pose hypothesis;
- underdetermined by current docking;
- incompatible with the current pocket model.

This is a hypothesis classification, not a claim of confirmed affinity or agonism.

## Priority 4 — reverse-validate the paper optimization

After exact structures are available:

1. Dock matched pairs under the validated protocol.
2. Compare acyl-urea, pyridone/pyrimidone, and amide linkers.
3. Test the proposed mechanism:
   - conformational restriction;
   - intramolecular H-bond preservation;
   - HBD/HBA geometry;
   - LHS/RHS vectoring;
   - pocket occupancy and subpocket filling;
   - selectivity versus GPR109A/GHS-R1a where the paper provides data.
4. Pair every structural observation with the paper's EC50, efficacy, LogD, solubility, and LLE.
5. Explicitly separate improvements in receptor binding from improvements in solubility or exposure. A compound can be better for in-vivo use without having a better docking score.
6. Highlight cases where the biological SAR is not explained by the rigid docking model.

## Deliverables

- `paper_structures_recovered.csv`
- `paper_ligands/compound_*.sdf`
- `paper_structure_validation.json`
- `gpr81_redocking_control_report.md`
- `tool_compound_binding_mode_v2.csv`
- `gpr81_optimization_reverse_validation.md`
- updated 3D gallery with experimental and predicted poses separated by evidence level

## Stop conditions

Do not proceed to production paper-series docking if:

- a structure cannot be uniquely reconstructed;
- calculated formula or `[M+H]+` does not match the supplementary MS;
- the receptor control redocking does not reproduce the known ligand pocket;
- a pose is being selected only because it has the most negative score;
- a structure-state difference is being inferred from unaligned absolute coordinates.
