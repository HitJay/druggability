#!/usr/bin/env python3
"""
GPR81 follow-up: submit HCAR2 (GPR109A) and HCAR3 (GPR109B) to BioLib AlphaFold
(@nn/DCD/AlphaFold:0.1.210) for internally reproducible receptor models.

UniProt sequences fetched 2026-08-05:
  HCAR2 Q8TDS4 (363 aa) - the niacin/3-hydroxybutyrate receptor (selectivity target)
  HCAR3 Q8TDS5 (384 aa) - GPR109B (hydroxycarboxylic acid receptor 3)

Outputs: data/alphafold/hcar2/, hcar3/ (model files), data/alphafold/alphafold_results.json
"""
import json, shutil, traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "data" / "alphafold"
OUT.mkdir(parents=True, exist_ok=True)

# UniProt accessions -> internal names. SEQUENCES ARE FETCHED FROM THE UNIPROT
# REST API AT RUNTIME (never hardcoded/transcribed by hand - see audit note
# 2026-08-05: a hand-assembled sequence was caught and rejected in this project).
ACCESSION = {"hcar2": "Q8TDS4", "hcar3": "Q8TDS5"}


def fetch_sequence(acc: str) -> str:
    import json as _json
    import subprocess
    url = f"https://rest.uniprot.org/uniprotkb/{acc}.json"
    r = subprocess.run(["curl", "-sS", "--max-time", "40", url],
                       capture_output=True, text=True, check=True)
    seq = _json.loads(r.stdout)["sequence"]["value"]
    if not seq or len(seq) < 200:
        raise RuntimeError(f"sequence fetch for {acc} failed (len={len(seq) if seq else 0})")
    return seq


def main() -> None:
    import biolib
    app = biolib.load("@nn/DCD/AlphaFold")
    results = {}
    prev = {}
    if (OUT / "alphafold_results.json").exists():
        prev = json.loads((OUT / "alphafold_results.json").read_text(encoding="utf-8"))
    for name, acc in ACCESSION.items():
        if prev.get(name, {}).get("exit") == 0:
            print(f"[SKIP] {name} already complete", flush=True)
            results[name] = prev[name]
            continue
        seq = fetch_sequence(acc)
        fasta = OUT / f"{name}.fasta"
        fasta.write_text(f">sp|{acc}|{name}\n{seq}\n", encoding="utf-8")
        run_dir = OUT / name
        print(f"[SUBMIT] {name} ({acc}, {len(seq)} aa)", flush=True)
        try:
            job = app.run(fasta_paths=str(fasta.resolve()), model_preset="monomer",
                          biolib_check=False, biolib_stream_logs=False)
            exit_code = job.get_exit_code()
            print(f"[DONE] {name} exit={exit_code} job={job.id}", flush=True)
            if exit_code == 0:
                if run_dir.exists():
                    shutil.rmtree(run_dir)
                run_dir.mkdir(parents=True, exist_ok=True)
                # retry the download once (a partial_biolib_download crash wiped a
                # mid-transfer file on 2026-08-06 for hcar3 job 2c525a56...)
                for attempt in (1, 2):
                    try:
                        job.save_files(str(run_dir), overwrite=True)
                        break
                    except Exception as e:
                        print(f"[RETRY] {name} save_files attempt {attempt}: {str(e)[:120]}", flush=True)
                        if attempt == 2:
                            raise
                # keep only the audit-relevant outputs; drop multi-GB intermediates
                for p in list(run_dir.rglob("*.pkl")) + list(run_dir.rglob("features.pkl")):
                    p.unlink(missing_ok=True)
                msa_dir = run_dir / "result/msas"
                if msa_dir.exists():
                    shutil.rmtree(msa_dir)
                files = sorted(str(p.relative_to(run_dir)) for p in run_dir.rglob("*") if p.is_file())
                results[name] = {"accession": acc, "length": len(seq), "job_id": str(job.id),
                                 "exit": exit_code, "files": files[:15]}
            else:
                results[name] = {"accession": acc, "length": len(seq),
                                 "job_id": str(job.id), "exit": exit_code, "error": "non-zero exit"}
        except Exception as e:
            err = "".join(traceback.format_exception_only(type(e), e)).strip()
            results[name] = {"accession": acc, "length": len(seq), "error": err[:300]}
            print(f"[FAIL] {name}: {err[:160]}", flush=True)
    (OUT / "alphafold_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
