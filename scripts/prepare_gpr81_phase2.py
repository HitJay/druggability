#!/usr/bin/env python3
"""Prepare experimental HCAR1 chain-R receptors and ligand-anchored pockets."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import gemmi

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "data/gpr81_phase1"
STRUCTURES = PHASE1 / "structures"
OUT = PHASE1 / "phase2_prepared"
RECEPTORS = OUT / "receptors"
REFERENCES = OUT / "reference_ligands"

STRUCTURE_CONFIG = {
    "8Z87": {"file": "8Z87.cif", "ligand": "A1D71", "state": "CHBA-bound"},
    "9KT9": {"file": "9KT9.pdb", "ligand": "34D", "state": "3,5-DHBA-bound"},
    "8Z8A": {"file": "8Z8A.pdb", "ligand": "2OP", "state": "lactate-bound"},
    "8Z8B": {"file": "8Z8B.pdb", "ligand": None, "state": "apo"},
}
STANDARD_RESIDUES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}


def distance_sq(a: gemmi.Position, b: gemmi.Position) -> float:
    return (a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2


def atom_positions(residue: gemmi.Residue) -> list[gemmi.Position]:
    return [atom.pos for atom in residue if atom.element.name != "H"]


def write_chain_pdb(structure: gemmi.Structure, output: Path) -> gemmi.Chain:
    model = structure[0]
    chain = next(c for c in model if c.name == "R")
    clean_chain = gemmi.Chain("R")
    for residue in chain:
        if residue.name in STANDARD_RESIDUES:
            clean_chain.add_residue(residue.clone())
    out = gemmi.Structure()
    out.add_model(gemmi.Model("1"))
    out[0].add_chain(clean_chain)
    out.cell = structure.cell
    out.spacegroup_hm = structure.spacegroup_hm
    out.write_pdb(str(output))
    return clean_chain


def extract_reference_ligand(structure: gemmi.Structure, ligand_name: str | None, output: Path) -> dict:
    if ligand_name is None:
        return {"ligand": None, "atoms": 0}
    found = []
    for chain in structure[0]:
        for residue in chain:
            if residue.name == ligand_name:
                found.append((chain.name, residue))
    if len(found) != 1:
        raise RuntimeError(f"Expected one {ligand_name} residue, found {len(found)}")
    chain_name, residue = found[0]
    # Write a minimal PDB containing the experimental ligand coordinates.
    lines = []
    for i, atom in enumerate(residue, start=1):
        p = atom.pos
        lines.append(
            f"HETATM{i:5d} {atom.name:<4s} {residue.name:>3s} L{chain_name:1s}"
            f"{residue.seqid.num:4d}    {p.x:8.3f}{p.y:8.3f}{p.z:8.3f}"
            f"  1.00  0.00          {atom.element.name:>2s}\n"
        )
    output.write_text("".join(lines) + "END\n")
    return {"ligand": ligand_name, "chain": chain_name, "residue_number": residue.seqid.num, "atoms": len(lines)}


def ligand_geometry(structure: gemmi.Structure, ligand_name: str | None) -> dict | None:
    if ligand_name is None:
        return None
    positions = []
    for chain in structure[0]:
        for residue in chain:
            if residue.name == ligand_name:
                positions.extend(atom_positions(residue))
    if not positions:
        return None
    center = [sum(getattr(p, axis) for p in positions) / len(positions) for axis in ("x", "y", "z")]
    span = [max(getattr(p, axis) for p in positions) - min(getattr(p, axis) for p in positions) for axis in ("x", "y", "z")]
    box_size = [round(max(s + 10.0, 24.0), 3) for s in span]
    return {
        "atom_count": len(positions),
        "center_A": [round(x, 3) for x in center],
        "ligand_span_A": [round(x, 3) for x in span],
        "box_size_A": box_size,
    }


def prepare_receptor_pdbqt(receptor_pdb: Path, output: Path) -> dict:
    temporary = output.with_suffix(".raw.pdbqt")
    subprocess.run(
        ["obabel", str(receptor_pdb), "-O", str(temporary), "-p", "7.4", "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
    kept = [line for line in temporary.read_text().splitlines(True) if line.startswith(("ATOM", "HETATM"))]
    output.write_text("".join(kept))
    temporary.unlink()
    return {"path": str(output), "atom_lines": len(kept), "non_atom_lines_removed": True}


def pocket_residues(clean_chain: gemmi.Chain, ligand_atoms: list[gemmi.Position], cutoff: float = 6.0) -> list[dict]:
    result = []
    cutoff_sq = cutoff * cutoff
    for residue in clean_chain:
        positions = atom_positions(residue)
        if not positions:
            continue
        min_sq = min(distance_sq(a, b) for a in positions for b in ligand_atoms)
        if min_sq <= cutoff_sq:
            result.append({"residue": residue.name, "number": residue.seqid.num, "min_distance_A": round(min_sq ** 0.5, 3)})
    return result


def main() -> None:
    RECEPTORS.mkdir(parents=True, exist_ok=True)
    REFERENCES.mkdir(parents=True, exist_ok=True)
    records = []
    consensus: dict[int, set[str]] = {}
    for pdb_id, cfg in STRUCTURE_CONFIG.items():
        structure = gemmi.read_structure(str(STRUCTURES / cfg["file"]))
        receptor_pdb = RECEPTORS / f"{pdb_id}_chainR_protein.pdb"
        clean_chain = write_chain_pdb(structure, receptor_pdb)
        receptor_pdbqt = RECEPTORS / f"{pdb_id}_chainR_protein.pdbqt"
        receptor_pdbqt_record = prepare_receptor_pdbqt(receptor_pdb, receptor_pdbqt)
        reference_pdb = REFERENCES / f"{pdb_id}_{cfg['ligand'] or 'apo'}.pdb"
        ligand_record = extract_reference_ligand(structure, cfg["ligand"], reference_pdb)
        ligand_atoms = []
        if cfg["ligand"]:
            for chain in structure[0]:
                for residue in chain:
                    if residue.name == cfg["ligand"]:
                        ligand_atoms.extend(atom_positions(residue))
        pockets = pocket_residues(clean_chain, ligand_atoms) if ligand_atoms else []
        for row in pockets:
            consensus.setdefault(row["number"], set()).add(pdb_id)
        records.append({
            "pdb_id": pdb_id,
            "state": cfg["state"],
            "source_file": str(STRUCTURES / cfg["file"]),
            "receptor_chain": "R",
            "receptor_pdb": str(receptor_pdb),
            "receptor_pdbqt": receptor_pdbqt_record,
            "reference_ligand": ligand_record,
            "ligand_geometry": ligand_geometry(structure, cfg["ligand"]),
            "pocket_cutoff_A": 6.0,
            "pocket_residues": pockets,
        })
    consensus_rows = [
        {"number": n, "structure_count": len(ids), "structures": sorted(ids)}
        for n, ids in sorted(consensus.items())
    ]
    manifest = {
        "target": "human HCAR1/GPR81",
        "uniprot": "Q9BXC0",
        "receptor_chain": "R",
        "preparation": "protein standard residues only; G protein and experimental ligands removed from receptor PDB",
        "pocket_definition": "protein residues with any non-hydrogen atom within 6.0 A of the experimental ligand",
        "structures": records,
        "ligand_anchored_consensus": consensus_rows,
        "next_step": "inspect pocket and prepare receptor PDBQT; do not interpret docking scores as agonism evidence",
    }
    (OUT / "phase2_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(OUT), "structures": records, "consensus": consensus_rows}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
