#!/usr/bin/env python3
"""
RDKit scaffold clustering for GRB10 SH2 domain Vina docking candidates.

Groups elite + tier1 compounds by:
  1) Murcko scaffold (generic) - removes sidechain atoms, keeps ring + linker topology
  2) Bemis-Murcko framework (atom-type-sensitive) - distinguishes heteroatom differences

Outputs CSV + JSON summary.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# ─── Paths ────────────────────────────────────────────────────────────────────
INPUT_CSV = Path(
    "/das/user/QYJI/druggability/output/2026-06-30/"
    "grb10_screening_expanded_chembl/vina_full/grb10_vina_full_triage.csv"
)
OUTPUT_DIR = INPUT_CSV.parent
OUTPUT_CSV = OUTPUT_DIR / "grb10_vina_scaffold_clusters.csv"
OUTPUT_JSON = OUTPUT_DIR / "grb10_vina_scaffold_summary.json"
OUTPUT_CSV_BM = OUTPUT_DIR / "grb10_vina_scaffold_clusters_bemis_murcko.csv"

# ─── Step 1: Read & filter ───────────────────────────────────────────────────
print("Reading input CSV...")
rows = []
with open(INPUT_CSV, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"Total rows in CSV: {len(rows)}")

# Filter to elite + tier1
target_tiers = {"elite", "tier1"}
filtered = [r for r in rows if r["tier"].strip().lower() in target_tiers]
print(f"After tier filter (elite+tier1): {len(filtered)}")

# Count tiers
tier_counts = defaultdict(int)
for r in filtered:
    tier_counts[r["tier"].strip().lower()] += 1
print(f"  elite: {tier_counts.get('elite', 0)}, tier1: {tier_counts.get('tier1', 0)}")

# ─── Step 2: Parse SMILES ────────────────────────────────────────────────────
def parse_smiles(row):
    """Parse SMILES, return (mol, errors) or (None, msg)."""
    smi = row.get("canonical_smiles", "").strip()
    if not smi:
        return None, f"{row['compound_id']}: empty SMILES"
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None, f"{row['compound_id']}: RDKit parse failed for '{smi[:60]}'"
    return mol, None

compounds = []   # list of dicts with computed fields
parse_errors = []
for r in filtered:
    mol, err = parse_smiles(r)
    if err:
        parse_errors.append(err)
        continue
    compounds.append({
        "tier": r["tier"].strip().lower(),
        "compound_id": r["compound_id"].strip(),
        "name": r.get("name", "").strip(),
        "vina": float(r.get("best_vina_kcal_mol", 0) or 0),
        "le": float(r.get("ligand_efficiency", 0) or 0),
        "smiles": r.get("canonical_smiles", "").strip(),
        "mol": mol,
    })

print(f"Successfully parsed: {len(compounds)}")
if parse_errors:
    print(f"Parse errors ({len(parse_errors)}):")
    for e in parse_errors[:5]:
        print(f"  - {e}")

n_compounds = len(compounds)

# ─── Step 3: Compute scaffolds ────────────────────────────────────────────────
print("\nComputing Murcko scaffolds (generic) and Bemis-Murcko frameworks...")

def get_scaffolds(mol):
    """Return (murcko_scaffold_smiles, bemis_murcko_smiles) or (None, None)."""
    try:
        # Murcko scaffold (generic) — removes sidechains, keeps ring + linker topology
        murcko = MurckoScaffold.GetScaffoldForMol(mol)
        if murcko is None:
            return None, None
        murcko_smi = Chem.MolToSmiles(murcko, canonical=True)

        # Bemis-Murcko framework — atom-type-sensitive, preserves heteroatom info
        # This is MurckoScaffold.MakeScaffoldGeneric with atom typing
        framework = MurckoScaffold.MakeScaffoldGeneric(murcko)
        # Actually, for Bemis-Murcko framework (atom-type-sensitive), we want
        # the framework with atom types preserved. Let's use MurckoScaffold.GetScaffoldForMol
        # which keeps atom types by default, then the generic version removes them.
        # For "Bemis-Murcko framework" we can also use:
        from rdkit.Chem.Scaffolds.MurckoScaffold import MurckoScaffoldSmiles
        
        # Actually, MurckoScaffoldSmiles(smi) gives the Murcko scaffold SMILES (with atom types)
        # GetScaffoldForMol gives the Mol object of the scaffold
        # MakeScaffoldGeneric removes atom type info
        # So "Murcko scaffold (generic)" = MakeScaffoldGeneric
        # "Bemis-Murcko framework (atom-type-sensitive)" = regular scaffold with atom types
        
        # Let's be more explicit:
        # Murcko generic: all atoms become carbon, all bonds single/double/aromatic kept
        murcko_generic = MurckoScaffold.MakeScaffoldGeneric(murcko)
        murcko_generic_smi = Chem.MolToSmiles(murcko_generic, canonical=True)
        
        # Bemis-Murcko framework: atom-type-sensitive version
        # This is just the regular Murcko scaffold SMILES (preserves atom types)
        murcko_atomtyped = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
        # or equivalently: Chem.MolToSmiles(murcko, canonical=True)
        
        return murcko_generic_smi, murcko_atomtyped

    except Exception as e:
        return None, None

# Actually let me reconsider. The user asked for:
# 1) Murcko scaffold (generic) - using rdkit.Chem.Scaffolds.MurckoScaffold
# 2) Bemis-Murcko framework (atom-type-sensitive)

# In RDKit:
# - MurckoScaffold.GetScaffoldForMol(mol) returns the Murcko scaffold Mol (preserves atom types by default)
# - MurckoScaffold.MakeScaffoldGeneric(mol) makes all atoms carbon (generic)
# - To get the SMILES of the scaffold: Chem.MolToSmiles(GetScaffoldForMol(mol))
# 
# Bemis-Murcko framework = The Murcko scaffold with atom types preserved = GetScaffoldForMol (default)
# Murcko scaffold generic = MakeScaffoldGeneric = all carbons

# Let me re-write the function cleanly:

def compute_scaffolds(mol):
    """Return (murcko_generic_smiles, bemis_murcko_smiles) or (None, None)."""
    try:
        scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold_mol is None:
            return None, None
        
        # Bemis-Murcko framework = scaffold with atom types (default)
        bm_smi = Chem.MolToSmiles(scaffold_mol, canonical=True)
        
        # Murcko generic = all atoms generic (carbon)
        generic_mol = MurckoScaffold.MakeScaffoldGeneric(scaffold_mol)
        generic_smi = Chem.MolToSmiles(generic_mol, canonical=True)
        
        return generic_smi, bm_smi
    except Exception as e:
        return None, None

scaffold_data = []
no_scaffold = 0
for c in compounds:
    generic_smi, bm_smi = compute_scaffolds(c["mol"])
    if generic_smi is None:
        no_scaffold += 1
        continue
    c["murcko_generic"] = generic_smi
    c["bemis_murcko"] = bm_smi
    scaffold_data.append(c)

print(f"Compounds with scaffolds: {len(scaffold_data)}")
if no_scaffold:
    print(f"  No scaffold generated: {no_scaffold}")

# ─── Step 4: Group by scaffold ────────────────────────────────────────────────
print("\nGrouping by Murcko scaffold (generic)...")

def compute_rank_key(c):
    """Score for ranking: primary = Vina (more negative = better), secondary = LE (higher = better)."""
    return (c["vina"], -c["le"])

def group_and_score(compounds_list, scaffold_key):
    """Group compounds by a scaffold key function.
    Returns list of dicts with cluster info, sorted by cluster size desc."""
    clusters = defaultdict(list)
    for c in compounds_list:
        key = c[scaffold_key]
        clusters[key].append(c)
    
    results = []
    for scaffold_smi, members in clusters.items():
        # Sort members by rank key (best Vina first, then best LE)
        members_sorted = sorted(members, key=compute_rank_key, reverse=True)
        # Actually: more negative vina = better, so reverse on vina, positive on LE
        # Let's fix: (more negative vina) should come first
        # compute_rank_key returns (vina, -le). More negative vina = smaller = earlier in sort.
        # But we want best first. So sort normally (ascending vina) then reverse LE priority.
        # Actually let's just sort: primary by vina ascending (more negative first),
        # secondary by LE descending (higher first).
        members_sorted = sorted(members, key=lambda c: (c["vina"], -c["le"]))
        
        best = members_sorted[0]
        runner_up = members_sorted[1] if len(members_sorted) > 1 else None
        compound_ids = [m["compound_id"] for m in members_sorted]
        
        results.append({
            "scaffold_smiles": scaffold_smi,
            "cluster_size": len(members),
            "best_compound_id": best["compound_id"],
            "best_name": best["name"],
            "best_vina": best["vina"],
            "best_le": best["le"],
            "best_tier": best["tier"],
            "runner_up_compound_id": runner_up["compound_id"] if runner_up else "",
            "runner_up_name": runner_up["name"] if runner_up else "",
            "runner_up_vina": runner_up["vina"] if runner_up else "",
            "compound_ids_list": ";".join(compound_ids),
        })
    
    # Sort by cluster size descending, then by best_vina ascending
    results.sort(key=lambda x: (-x["cluster_size"], x["best_vina"]))
    return results

murcko_clusters = group_and_score(scaffold_data, "murcko_generic")
bm_clusters = group_and_score(scaffold_data, "bemis_murcko")

print(f"  Murcko generic: {len(murcko_clusters)} clusters")
print(f"  Bemis-Murcko:   {len(bm_clusters)} clusters")

# ─── Step 5: Output ──────────────────────────────────────────────────────────
CSV_COLUMNS = [
    "scaffold_smiles",
    "cluster_size",
    "best_compound_id",
    "best_name",
    "best_vina",
    "best_le",
    "best_tier",
    "runner_up_compound_id",
    "runner_up_name",
    "runner_up_vina",
    "compound_ids_list",
]

def write_csv(filepath, clusters, label):
    print(f"\nWriting {label} clusters CSV: {filepath}")
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(clusters)
    print(f"  {len(clusters)} clusters written")

write_csv(OUTPUT_CSV, murcko_clusters, "Murcko generic")
write_csv(OUTPUT_CSV_BM, bm_clusters, "Bemis-Murcko")

# ─── Step 6: JSON summary ────────────────────────────────────────────────────
def build_summary(clusters, compounds_list, label):
    """Build a summary dict for JSON output."""
    n_clusters = len(clusters)
    n_compounds = len(compounds_list)
    largest = max(clusters, key=lambda x: x["cluster_size"]) if clusters else {}
    singletons = [c for c in clusters if c["cluster_size"] == 1]
    top_10 = clusters[:10]
    
    return {
        "label": label,
        "n_clusters": n_clusters,
        "n_compounds": n_compounds,
        "largest_cluster_size": largest.get("cluster_size", 0),
        "largest_cluster_scaffold": largest.get("scaffold_smiles", ""),
        "scaffold_diversity_ratio": round(n_clusters / n_compounds, 4) if n_compounds > 0 else 0,
        "n_singletons": len(singletons),
        "singleton_ratio": round(len(singletons) / n_clusters, 4) if n_clusters > 0 else 0,
        "top_10_scaffolds": [
            {
                "scaffold_smiles": c["scaffold_smiles"],
                "cluster_size": c["cluster_size"],
                "best_compound_id": c["best_compound_id"],
                "best_name": c["best_name"],
                "best_vina": c["best_vina"],
                "best_le": c["best_le"],
            }
            for c in top_10
        ],
        "singletons": [
            {
                "scaffold_smiles": c["scaffold_smiles"],
                "compound_id": c["best_compound_id"],
                "name": c["best_name"],
                "vina": c["best_vina"],
            }
            for c in singletons
        ],
    }

summary = {
    "analysis": "GRB10 SH2 Domain - Vina Docking Scaffold Analysis",
    "n_total_compounds": n_compounds,
    "elite_count": tier_counts.get("elite", 0),
    "tier1_count": tier_counts.get("tier1", 0),
    "parse_errors": len(parse_errors),
    "murcko_generic": build_summary(murcko_clusters, scaffold_data, "Murcko Scaffold (Generic)"),
    "bemis_murcko": build_summary(bm_clusters, scaffold_data, "Bemis-Murcko Framework"),
}

print(f"\nWriting JSON summary: {OUTPUT_JSON}")
with open(OUTPUT_JSON, "w") as f:
    json.dump(summary, f, indent=2)
print("Done.")

# ─── Quick stats ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SCAFFOLD CLUSTERING SUMMARY")
print("=" * 70)
print(f"  Compounds analyzed:        {n_compounds}")
print(f"  Elite / Tier 1:            {tier_counts.get('elite', 0)} / {tier_counts.get('tier1', 0)}")
print(f"  Parse errors:              {len(parse_errors)}")
print(f"  Without scaffold:          {no_scaffold}")
print()
_largest_m = max(murcko_clusters, key=lambda x: x["cluster_size"]) if murcko_clusters else {}
_singletons_m = [c for c in murcko_clusters if c["cluster_size"] == 1]
print(f"  MURCKO SCAFFOLD (Generic): {len(murcko_clusters)} clusters")
print(f"    Largest cluster:         {_largest_m.get('cluster_size', 0)} compounds")
print(f"    Singletons:              {len(_singletons_m)}")
print(f"    Diversity ratio:         {len(murcko_clusters)/n_compounds:.4f}")
print(f"  Top 5 scaffolds:")
for i, c in enumerate(murcko_clusters[:5], 1):
    print(f"    {i}. [{c['cluster_size']:3d}] {c['scaffold_smiles'][:70]}")
    print(f"       Best: {c['best_name'][:40]:40s}  Vina={c['best_vina']:.3f}  Tier={c['best_tier']}")
print()
_largest_bm = max(bm_clusters, key=lambda x: x["cluster_size"]) if bm_clusters else {}
_singletons_bm = [c for c in bm_clusters if c["cluster_size"] == 1]
print(f"  BEMIS-MURCKO Framework:    {len(bm_clusters)} clusters")
print(f"    Largest cluster:         {_largest_bm.get('cluster_size', 0)} compounds")
print(f"    Singletons:              {len(_singletons_bm)}")
print(f"    Diversity ratio:         {len(bm_clusters)/n_compounds:.4f}")
print(f"  Top 5 Bemis-Murcko frameworks:")
for i, c in enumerate(bm_clusters[:5], 1):
    print(f"    {i}. [{c['cluster_size']:3d}] {c['scaffold_smiles'][:70]}")
    print(f"       Best: {c['best_name'][:40]:40s}  Vina={c['best_vina']:.3f}  Tier={c['best_tier']}")
