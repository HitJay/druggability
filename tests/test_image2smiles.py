from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from rdkit import Chem

from litkit.image2smiles import (
    ImageToSmilesResult,
    discover_image_paths,
    run_image_to_smiles_batch,
    write_results_csv,
    write_results_sdf,
)


def test_discover_image_paths_supports_directories_and_recursive(tmp_path):
    direct = tmp_path / "direct.png"
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested = nested_dir / "nested.jpg"
    ignored = tmp_path / "notes.txt"

    direct.write_bytes(b"png")
    nested.write_bytes(b"jpg")
    ignored.write_text("ignore me", encoding="utf-8")

    non_recursive = discover_image_paths([str(tmp_path)], recursive=False)
    recursive = discover_image_paths([str(tmp_path)], recursive=True)

    assert direct.resolve() in non_recursive
    assert nested.resolve() not in non_recursive
    assert direct.resolve() in recursive
    assert nested.resolve() in recursive


def test_run_image_to_smiles_batch_normalizes_worker_output(monkeypatch, tmp_path):
    image = tmp_path / "aspirin.png"
    image.write_bytes(b"image")
    seen = {}

    stdout = json.dumps(
        {
            "image_path": str(image.resolve()),
            "status": "ok",
            "smiles": "C(C)O",
            "confidence": 0.75,
        }
    )

    def fake_run(cmd, capture_output, text, check, cwd=None):
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        return subprocess.CompletedProcess(cmd, 0, stdout + "\n", "")

    monkeypatch.setattr("litkit.image2smiles.subprocess.run", fake_run)

    results = run_image_to_smiles_batch([image], compute_confidence=True)
    assert len(results) == 1
    result = results[0]
    assert result.success is True
    assert result.predicted_smiles == "C(C)O"
    assert result.canonical_smiles == "CCO"
    assert result.inchikey == Chem.MolToInchiKey(Chem.MolFromSmiles("CCO"))
    assert result.confidence == 0.75
    assert Path(seen["cmd"][0]).name.startswith("python")
    assert "--backend" in seen["cmd"]
    assert seen["cmd"][seen["cmd"].index("--backend") + 1] == "decimer"


def test_write_results_csv_and_sdf(tmp_path):
    results = [
        ImageToSmilesResult(
            image_path=str(tmp_path / "mol.png"),
            status="ok",
            predicted_smiles="CCO",
            canonical_smiles="CCO",
            inchikey=Chem.MolToInchiKey(Chem.MolFromSmiles("CCO")),
            confidence=0.9,
        ),
        ImageToSmilesResult(
            image_path=str(tmp_path / "bad.png"),
            status="failed",
            error="No SMILES returned",
        ),
    ]

    csv_path = tmp_path / "results.csv"
    sdf_path = tmp_path / "results.sdf"
    write_results_csv(results, csv_path)
    write_results_sdf(results, sdf_path)

    csv_lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(csv_lines) == 3
    assert csv_lines[0].startswith("image_path,status,success")

    supplier = Chem.SDMolSupplier(str(sdf_path), removeHs=False)
    mols = [mol for mol in supplier if mol is not None]
    assert len(mols) == 1
    assert mols[0].GetProp("CANONICAL_SMILES") == "CCO"
    assert mols[0].GetProp("STATUS") == "ok"