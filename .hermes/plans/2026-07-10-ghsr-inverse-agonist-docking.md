# GHSR Inverse Agonist Docking Campaign — Implementation Plan

> **Goal**: Dock a compound library against GHSR 7F83 (inactive state) and counter-screen against 8JSR (active state) to identify conformation-selective inverse agonists. Prioritize hits with ΔScore(7F83 − 8JSR) > 0.

> **Strategy**: 7F83 is the only inactive-state GHSR structure. True inverse agonists will score well in the tight inactive pocket but poorly in the open active pocket. Pan-state competitive binders score well in both and are deprioritized.

> **Tech Stack**: AutoDock Vina · Meeko (receptor prep) · RDKit (ligand prep) · OpenBabel · 3Dmol.js (gallery)

**Input**: GHSR PDB 7F83 (inactive) + 8JSR (active)
**Output**: Ranked hit list with ΔScore · HTML docking gallery

---

## Phase 0 — Environment Setup

### Task 0.1: Install docking tools

```bash
# In the project venv
source /home/QYJI/das/druggability/.venv/bin/activate
pip install meeko vina openbabel-wheel
```

**Verify**:
```bash
python -c "import meeko; print('meeko', meeko.__version__)"
python -c "from vina import Vina; print('vina OK')"
```

---

## Phase 1 — Structure Download

### Task 1.1: Download 7F83 and 8JSR from RCSB

```bash
mkdir -p /das/user/QYJI/druggability/output/$(date +%Y-%m-%d)/ghsr_inverse_agonist_docking/structures
cd /das/user/QYJI/druggability/output/$(date +%Y-%m-%d)/ghsr_inverse_agonist_docking/structures

# Inactive state (primary target)
curl -o 7F83.pdb "https://files.rcsb.org/download/7F83.pdb"

# Active state (counter-screen)
curl -o 8JSR.pdb "https://files.rcsb.org/download/8JSR.pdb"
```

**Verify**: `grep -c "^ATOM" 7F83.pdb` > 1000

---

## Phase 2 — Receptor Preparation

### Task 2.1: Strip water, heteroatoms, and extract protein only

Use `pdbfixer` or RDKit-based cleaning. Keep 1KQ ligand in a separate file for box definition.

```python
# scripts/prepare_ghsr_receptor.py
from pdbfixer import PDBFixer
from openmm.app import PDBFile

for pdb_id in ["7F83", "8JSR"]:
    fixer = PDBFixer(filename=f"structures/{pdb_id}.pdb")
    fixer.removeHeterogens(keepWater=False)    # remove ligands, ions
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)             # physiological pH
    PDBFile.writeFile(fixer.topology, fixer.positions, 
                      open(f"structures/{pdb_id}_prepared.pdb", "w"))
```

Alternative: use Meeko for GPCR-optimized preparation (handles protonation states better for titratable residues in the binding pocket).

### Task 2.2: Extract the co-crystallized ligand (1KQ) from 7F83

```python
# Extract 1KQ as reference for box definition
# 1KQ residue name in 7F83
# Save as structures/1KQ_reference.pdb
```

### Task 2.3: Convert prepared receptor to PDBQT

```bash
# Via Meeko
mk_prepare_receptor.py -i structures/7F83_prepared.pdb -o structures/7F83_receptor.pdbqt
mk_prepare_receptor.py -i structures/8JSR_prepared.pdb -o structures/8JSR_receptor.pdbqt
```

**Verify**: `grep -c "^ATOM" structures/7F83_receptor.pdbqt` > 0

---

## Phase 3 — Grid Box Definition

### Task 3.1: Define grid box around 1KQ binding site

Center the box on the co-crystallized inverse agonist 1KQ. Box size should extend ~5 Å beyond the ligand in all directions to accommodate diverse chemotypes.

```python
# scripts/define_grid.py
# Parse 1KQ_reference.pdb → compute centroid
# Add 5 Å padding → output center_x, center_y, center_z, size_x, size_y, size_z
```

Expected values (approximate, from visual inspection of 7F83):

| Parameter | Value |
|-----------|-------|
| center | centroid of 1KQ heavy atoms |
| box size | ~24 × 24 × 24 Å |

**Verify**: box encompasses the entire orthosteric pocket (TM3-TM7 extracellular side) + 5 Å margin.

---

## Phase 4 — Ligand Library Preparation

### Task 4.1: Assemble screening library

Three tiers of compounds:

| Tier | Source | ~N | Purpose |
|------|--------|-----|---------|
| **Positive controls** | Known GHSR ligands (anamorelin, macimorelin, ibutamoren, GHRP-6, 1KQ) | ~10 | Validate docking can recover known binders |
| **Drug repurposing** | Approved drugs from ChEMBL (drug-like filter: MW 200–500, logP −1 to 5) | ~2,000 | Repurposing opportunity |
| **Diverse lead-like** | ChEMBL lead-like subset or Enamine REAL diversity subset | ~5,000–50,000 | De novo hit discovery |

### Task 4.2: Ligand preparation pipeline

```python
# scripts/prepare_ligands.py
# For each SMILES:
#   1. RDKit: generate 3D conformer (ETKDG)
#   2. RDKit: assign protonation at pH 7.4
#   3. OpenBabel/Meeko: convert to PDBQT
#   4. Output: ligands/<chembl_id>.pdbqt
```

**Verify**: `ls ligands/*.pdbqt | wc -l` matches input count.

---

## Phase 5 — Primary Docking (7F83)

### Task 5.1: Dock all ligands against 7F83

```python
# scripts/dock_7F83.py
from vina import Vina
import glob, os

v = Vina(sf_name='vina')
v.set_receptor('structures/7F83_receptor.pdbqt')
v.set_box(center=[cx, cy, cz], box_size=[sx, sy, sz])

results = []
for pdbqt in sorted(glob.glob('ligands/*.pdbqt')):
    name = os.path.basename(pdbqt).replace('.pdbqt', '')
    v.set_ligand_from_file(pdbqt)
    v.dock(exhaustiveness=8, n_poses=5)
    score = v.energies(n_poses=1)[0][0]  # best pose score
    results.append({'name': name, 'score_7F83': score})
    # Save best pose
    v.write_poses(f'docked_7F83/{name}_out.pdbqt', n_poses=1, overwrite=True)
```

**Parameters**:
- exhaustiveness: 8 (screening) → 32 (top hits re-docking)
- n_poses: 5 (keep top 5 for visual inspection)
- Scoring: Vina empirical (ΔG in kcal/mol)

**Output**: `docked_7F83/*.pdbqt` + `results_7F83.csv`

---

## Phase 6 — Counter-Screen (8JSR)

### Task 6.1: Dock same ligands against 8JSR active state

Identical protocol, but against the active-state receptor. Grid box centered on anamorelin (UYI) in 8JSR.

```python
# scripts/dock_8JSR.py — same as 5.1 but against 8JSR_receptor.pdbqt
```

**Output**: `docked_8JSR/*.pdbqt` + `results_8JSR.csv`

---

## Phase 7 — ΔScore Analysis

### Task 7.1: Compute conformational selectivity

```python
# scripts/rank_hits.py
import pandas as pd

df7 = pd.read_csv('results_7F83.csv')
df8 = pd.read_csv('results_8JSR.csv')
df = df7.merge(df8, on='name', suffixes=('_7F83', '_8JSR'))

# Core metric: delta score
# Vina scores are negative (more negative = stronger binding).
# delta = score_7F83 - score_8JSR.
# Inverse agonists bind better to inactive (7F83): 7F83 << 8JSR → delta < 0.
# Agonists bind better to active (8JSR): 8JSR << 7F83 → delta > 0.
df['delta_score'] = df['score_7F83'] - df['score_8JSR']

# Classification (fixed sign: negative delta = 7F83-preferred = inverse agonist)
df['class'] = 'pan_binder'           # default
df.loc[df['delta_score'] < -1.0, 'class'] = 'strong_inverse_agonist'
df.loc[df['delta_score'] < -0.5, 'class'] = 'moderate_inverse_agonist'
df.loc[df['delta_score'] >  0.5, 'class'] = 'active_state_preferring'
df.loc[df['delta_score'] >  1.0, 'class'] = 'agonist_like'

# Rank: prioritize negative delta (inverse agonist) + strong 7F83 binding
df['priority'] = -df['delta_score'] * 0.6 + (-df['score_7F83']) * 0.4
df = df.sort_values('priority', ascending=False)
```

### Task 7.2: Validate positive controls

Positive controls (anamorelin, macimorelin) should show:
- **Agonists** → low ΔScore or negative ΔScore (prefer 8JSR)
- **1KQ** → high positive ΔScore (strong preference for 7F83)

If this pattern holds → docking protocol is validated.

---

## Phase 8 — Hit Prioritization

### Task 8.1: Filter criteria

| Filter | Threshold |
|--------|-----------|
| ΔScore (7F83 − 8JSR) | > 0.5 (moderate) / > 1.0 (strong) |
| Absolute 7F83 score | < −7.0 kcal/mol |
| Ligand efficiency (LE) | > 0.25 (score / heavy_atoms) |
| PAINS / aggregator | RDKit PAINS filter → remove |
| Drug-likeness | QED > 0.3, MW 200–500 |

### Task 8.2: Cluster by Murcko scaffold

Group hits by scaffold to identify chemotypes. Prioritize scaffolds with >1 member and consistent ΔScore.

```python
# Reuse pattern from scripts/scaffold_clustering.py
from rdkit.Chem.Scaffolds import MurckoScaffold
```

### Task 8.3: Select top 10–20 for visual inspection

Top candidates by priority-score, ensuring scaffold diversity.

---

## Phase 9 — Visualization Gallery

### Task 9.1: Build interactive HTML gallery

```python
# scripts/build_ghsr_gallery.py
# Pattern: reuse build_docking_gallery.py structure
# For each top hit:
#   - 2D structure (RDKit SVG)
#   - 3D pose in 7F83 (3Dmol.js inline)
#   - Overlay with reference 1KQ
#   - ΔScore annotation
#   - LE, MW, QED metrics
```

**Output**: `ghsr_docking_gallery.html` — single self-contained HTML, openable via `file://`.

---

## Phase 10 — Deliverables

| Artifact | Path |
|----------|------|
| Primary docking results | `output/<date>/ghsr_inverse_agonist_docking/results_7F83.csv` |
| Counter-screen results | `output/<date>/ghsr_inverse_agonist_docking/results_8JSR.csv` |
| Ranked hit list | `output/<date>/ghsr_inverse_agonist_docking/ranked_hits.csv` |
| Scaffold clusters | `output/<date>/ghsr_inverse_agonist_docking/scaffold_clusters.csv` |
| Docking gallery | `output/<date>/ghsr_inverse_agonist_docking/ghsr_docking_gallery.html` |
| Summary report | `output/<date>/ghsr_inverse_agonist_docking/GHSR_docking_summary.md` |

---

## Decision Tree

```
Dock library against 7F83 (inactive)
         │
         ▼
    Top 10–20% by Vina score
         │
    Counter-screen against 8JSR (active)
         │
    ┌────┴────┐
    ▼         ▼
  ΔScore    ΔScore
  > 0.5     < 0
    │         │
    ▼         ▼
  ✅ Hit    ❌ Deprioritize
    │       (pan-binder or
    │        agonist-like)
    ▼
  Filter: LE, PAINS, QED
    │
    ▼
  Cluster by scaffold
    │
    ▼
  Visual inspection (gallery)
    │
    ▼
  Top 5–10 → experimental validation
```

---

## Pitfalls

- **7F83 has Fab bound**: the PDB contains an antibody Fab fragment for crystallization. Strip Fab chains before docking — keep only chain A (GHSR). Docking into the Fab interface produces false positives.
- **1KQ is a large ligand**: the inverse agonist 1KQ extends deep into the 7TM bundle. Set box size with ≥5 Å padding in all directions to capture diverse chemotypes.
- **Protonation matters**: GPCR binding pockets contain titratable residues (Asp, Glu, His). Use pH 7.4 protonation; Meeko handles this better than naive OpenBabel.
- **GHSR constitutive activity**: even with inverse agonist, the receptor basal activity is ~30-50%. The docking score reflects binding energy, not inverse agonism efficacy — prioritize ΔScore over absolute score.
- **Don't skip positive controls**: dock known agonists into 7F83. If they score well, the protocol is not distinguishing conformation states — adjust box or receptor preparation.

---

## Expected Timeline

| Phase | Est. time | Key dependency |
|-------|-----------|----------------|
| 0 — Setup | 10 min | pip/conda network |
| 1 — Download | 2 min | RCSB access |
| 2 — Receptor prep | 10 min | Meeko/pdbfixer |
| 3 — Grid box | 5 min | — |
| 4 — Ligand prep | 5–30 min | Library size |
| 5 — 7F83 docking | 1–12 hr | Library size, CPU |
| 6 — 8JSR docking | 1–12 hr | Library size, CPU |
| 7 — ΔScore analysis | 5 min | — |
| 8 — Hit prioritization | 10 min | — |
| 9 — Gallery | 15 min | — |
| **Total** | **2–24 hr** | Library size dominant |
