"""BioLib enrichment wrappers for target-level druggability work.

The internal BioLib apps are useful evidence generators, but they have their own
runtime dependencies and access controls. Keep this layer optional and record
job metadata/logs instead of letting app failures break the core scoring path.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

TARGET_PORTAL_APP = "@nn/SBTD/Target-Portal"
AUTOMATED_TRACTABILITY_APP = "@nn/DCD/Automated-Tractability"
BIOLIB_RESULT_BASE_URL = "https://biolib.corp.novocorp.net/results"

TARGET_BIOLOGY_BY_TRAIT = {
    "T2D": "T2D",
    "WHRadjBMI": "Obesity",
    "BFPCT": "Obesity",
    "BMI": "Obesity",
    "Obesity": "Obesity",
    "Liver": "Liver",
    "Kidney": "Kidney",
    "Atherosclerosis": "Atherosclerosis",
    "HF": "HF",
}


@dataclass
class BioLibJobSummary:
    """Small, JSON-serializable record for a BioLib run."""

    app_uri: str
    job_id: str = ""
    result_url: str = ""
    exit_code: int | None = None
    output_dir: str = ""
    stdout_log: str = ""
    stderr_log: str = ""
    files: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and self.error is None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        return data


def infer_target_biology(gwas_trait: str, default: str = "Obesity") -> str:
    """Map local GWAS trait labels to Target-Portal target biology names."""
    trait = (gwas_trait or "").strip()
    return TARGET_BIOLOGY_BY_TRAIT.get(trait, default)


def write_gene_list(genes: Iterable[str], path: str | Path) -> Path:
    """Write a newline-delimited gene list for BioLib apps that require files."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cleaned = [str(g).strip() for g in genes if str(g).strip()]
    out.write_text("\n".join(cleaned) + ("\n" if cleaned else ""), encoding="utf-8")
    return out


def run_target_portal(
    gene_name: str,
    ensembl_id: str,
    *,
    target_biology: str,
    out_dir: str | Path,
    log_dir: str | Path,
    stream_logs: bool = False,
) -> BioLibJobSummary:
    """Run the internal Target-Portal app for one gene/biology pair."""
    output_dir = Path(out_dir)
    logs = Path(log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    summary = BioLibJobSummary(
        app_uri=TARGET_PORTAL_APP,
        output_dir=str(output_dir),
        stdout_log=str(logs / f"target_portal_{gene_name}_stdout.log"),
        stderr_log=str(logs / f"target_portal_{gene_name}_stderr.log"),
        metadata={"gene_name": gene_name, "ensembl_id": ensembl_id, "target_biology": target_biology},
    )

    try:
        biolib = _load_biolib()
        app = biolib.load(TARGET_PORTAL_APP)
        job = app.cli(
            ["-t", target_biology, "-g", f"{gene_name} - {ensembl_id}"],
            check=False,
            stream_logs=stream_logs,
        )
        _collect_job(job, summary, output_dir)
        if summary.ok:
            summary.metadata.update(_target_portal_manifest_summary(output_dir))
    except Exception as exc:  # noqa: BLE001 - optional external app should not crash core flow
        summary.error = f"{type(exc).__name__}: {exc}"
    return summary


def run_automated_tractability(
    genes_file: str | Path,
    *,
    out_dir: str | Path,
    log_dir: str | Path,
    outfile: str = "automated_tractability.csv",
    stream_logs: bool = False,
) -> BioLibJobSummary:
    """Run the internal Automated-Tractability app on a gene-list file."""
    output_dir = Path(out_dir)
    logs = Path(log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    genes_path = Path(genes_file)

    summary = BioLibJobSummary(
        app_uri=AUTOMATED_TRACTABILITY_APP,
        output_dir=str(output_dir),
        stdout_log=str(logs / "automated_tractability_stdout.log"),
        stderr_log=str(logs / "automated_tractability_stderr.log"),
        metadata={"genes_file": str(genes_path), "outfile": outfile},
    )

    try:
        biolib = _load_biolib()
        app = biolib.load(AUTOMATED_TRACTABILITY_APP)
        job = app.run(
            genes=str(genes_path),
            outfile=outfile,
            biolib_check=False,
            biolib_stream_logs=stream_logs,
        )
        _collect_job(job, summary, output_dir)
    except Exception as exc:  # noqa: BLE001
        summary.error = f"{type(exc).__name__}: {exc}"
    return summary


def _load_biolib() -> Any:
    try:
        import biolib  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("Install the optional BioLib client with `pip install pybiolib`.") from exc
    if not hasattr(biolib, "load"):
        raise RuntimeError("The imported `biolib` module lacks load(); install/use `pybiolib`.")
    return biolib


def _collect_job(job: Any, summary: BioLibJobSummary, output_dir: Path) -> None:
    summary.job_id = str(job.id)
    summary.result_url = f"{BIOLIB_RESULT_BASE_URL}/{job.id}/"
    summary.exit_code = int(job.get_exit_code())

    stdout = job.get_stdout()
    stderr = job.get_stderr()
    Path(summary.stdout_log).write_bytes(stdout)
    Path(summary.stderr_log).write_bytes(stderr)

    if summary.exit_code == 0:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        job.save_files(str(output_dir), overwrite=True)
        summary.files = _relative_files(output_dir)
    else:
        tail = stdout.decode("utf-8", errors="replace")[-1000:]
        summary.error = tail.strip() or f"BioLib app exited with code {summary.exit_code}"


def _relative_files(root: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(str(path.relative_to(root)))
    return files


def _target_portal_manifest_summary(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / "build" / "manifest.json"
    if not manifest_path.exists():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    params = dict(data.get("params") or {})
    params.pop("job_auth_token", None)
    sections = [
        {"key": section.get("key"), "title": section.get("title")}
        for section in data.get("sections") or []
    ]
    return {"target_portal_params": params, "target_portal_sections": sections}