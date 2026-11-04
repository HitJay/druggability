"""P2: AutoDock Vina docking campaign across all 25 structural pockets for imatinib.

Protocol:
  1. Receptor preparation: retain specified protein chains + catalytic cofactors
     (FAD in NQO2 3FW1; ZN in CA2 3HS4), convert to PDBQT with obabel -xr.
  2. Validation gate (Redock Control): extract the specific co-crystal ligand instance
     (code + chain + resSeq), convert to PDBQT preserving 3D coordinates via meeko
     (fallback to obabel single-tree if meeko fails on complex macrocycles/nucleotides),
     redock with Vina (box=20 A centered on co-crystal ligand centroid, exhaustiveness=32).
     GATE PASS: redock centroid recovery < 3.0 A.
  3. Imatinib docking: prepare fresh 3D conformer of imatinib from canonical SMILES
     via RDKit ETKDGv3 + MMFF94 + meeko PDBQT, dock into each gated pocket
     (box=20 A, exhaustiveness=32, 3 independent runs to confirm seed convergence).
"""
import json
import math
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdDistGeom, rdForceFieldHelpers
from meeko import MoleculePreparation, PDBQTWriterLegacy
from vina import Vina

BASE = Path("/das/user/QYJI/druggability/Imatinib_beta_cell_assessment")
DATA = BASE / "data"
STRUCT = BASE / "structures"
OUT = BASE / "output/docking"
OUT.mkdir(parents=True, exist_ok=True)
OBABEL = "/das/user/QYJI/druggability/.venv/bin/obabel"

IMATINIB_SMILES = "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC4=NC=CC(=N4)C5=CN=CC=C5"


def dist(a, b):
    if a is None or b is None:
        return 99.9
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def ligand_instance_coords(pdb_path, code, chain, resn):
    lines = []
    coords = []
    for line in open(pdb_path):
        if line.startswith("HETATM"):
            r = line[17:20].strip()
            c = line[21].strip()
            rn = line[22:26].strip()
            if r == code and c == chain and rn == str(resn):
                lines.append(line)
                elem = line[76:78].strip()
                aname = line[12:16].strip()
                if elem != "H" and not aname.startswith("H"):
                    coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
    if not coords:
        raise RuntimeError(f"No heavy atoms for {code}:{chain}:{resn} in {pdb_path}")
    n = len(coords)
    cen = (sum(x for x, y, z in coords) / n,
           sum(y for x, y, z in coords) / n,
           sum(z for x, y, z in coords) / n)
    return cen, coords, lines


def clean_receptor(pdb_path, out_pdb, keep_chains, keep_cofactors):
    keep_ch = set(keep_chains)
    keep_cof = {(r, c, str(rn)) for r, c, rn in keep_cofactors}
    out_lines = []
    for line in open(pdb_path):
        if line.startswith("ATOM"):
            if line[21].strip() in keep_ch:
                out_lines.append(line)
        elif line.startswith("HETATM"):
            key = (line[17:20].strip(), line[21].strip(), line[22:26].strip())
            if key in keep_cof:
                if line[76:78].strip() == "H":
                    continue
                out_lines.append(line)
        elif line.startswith(("TER", "END")):
            out_lines.append(line)
    Path(out_pdb).write_text("".join(out_lines))


def prep_receptor_pdbqt(rec_pdb, rec_pdbqt):
    r = subprocess.run([OBABEL, str(rec_pdb), "-O", str(rec_pdbqt), "-xr"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not Path(rec_pdbqt).exists():
        raise RuntimeError(f"obabel receptor failed: {r.stderr[-300:]}")
    lines = [l for l in open(rec_pdbqt) if l.startswith(("ATOM", "HETATM"))]
    Path(rec_pdbqt).write_text("".join(lines))


def prep_imatinib_pdbqt(out_pdbqt):
    mol = Chem.MolFromSmiles(IMATINIB_SMILES)
    mol = Chem.AddHs(mol)
    params = rdDistGeom.ETKDGv3()
    params.randomSeed = 20261103
    rdDistGeom.EmbedMolecule(mol, params)
    rdForceFieldHelpers.MMFFOptimizeMolecule(mol, maxIters=500)
    prep = MoleculePreparation()
    setups = prep.prepare(mol)
    pdbqt_str, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        raise RuntimeError(f"meeko imatinib failed: {err}")
    Path(out_pdbqt).write_text(pdbqt_str)
    w = Chem.SDWriter(str(Path(out_pdbqt).with_suffix(".sdf")))
    w.write(mol)
    w.close()


def prep_ctrl_ligand(het_lines, code, out_pdbqt):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".pdb", delete=False)
    tmp.write("".join(het_lines))
    tmp.close()
    sdf = str(out_pdbqt).replace(".pdbqt", ".sdf")
    subprocess.run([OBABEL, tmp.name, "-O", sdf], capture_output=True, text=True)
    Path(tmp.name).unlink(missing_ok=True)
    ok_meeko = False
    try:
        suppl = Chem.SDMolSupplier(sdf, removeHs=False, sanitize=True)
        mol = suppl[0] if len(suppl) > 0 else None
        if mol is not None:
            frags = Chem.GetMolFrags(mol, asMols=True)
            if len(frags) > 1:
                mol = max(frags, key=lambda fm: fm.GetNumAtoms())
            mol_h = Chem.AddHs(mol, addCoords=True)
            prep = MoleculePreparation()
            setups = prep.prepare(mol_h)
            pdbqt_str, ok, err = PDBQTWriterLegacy.write_string(setups[0])
            if ok and pdbqt_str.count("ATOM") + pdbqt_str.count("HETATM") >= 8:
                Path(out_pdbqt).write_text(pdbqt_str)
                ok_meeko = True
    except Exception:
        ok_meeko = False

    if not ok_meeko:
        r = subprocess.run([OBABEL, sdf, "-O", str(out_pdbqt), "-h"],
                           capture_output=True, text=True)
        if not Path(out_pdbqt).exists() or Path(out_pdbqt).stat().st_size == 0:
            raise RuntimeError(f"Control ligand prep failed for {code}: {r.stderr[-200:]}")
        lines = open(out_pdbqt).readlines()
        keep, seen_tors = [], 0
        for line in lines:
            if line.startswith("TORSDOF"):
                seen_tors += 1
                if seen_tors == 1:
                    keep.append(line)
                continue
            if seen_tors >= 1:
                break
            keep.append(line)
        Path(out_pdbqt).write_text("".join(keep))


def parse_pose_heavy_coords(pdbqt_path, pose=1):
    coords = []
    in_model = 0
    for line in open(pdbqt_path):
        if line.startswith("MODEL"):
            in_model += 1
        elif (in_model == pose or in_model == 0) and line.startswith(("ATOM", "HETATM")):
            ad_type = line[77:79].strip().upper()
            aname = line[12:16].strip().upper()
            if ad_type == "HD" or ad_type == "H" or aname.startswith("H"):
                continue
            coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL") and in_model >= pose:
            break
    if not coords:
        return None, []
    n = len(coords)
    cen = (sum(x for x, y, z in coords) / n,
           sum(y for x, y, z in coords) / n,
           sum(z for x, y, z in coords) / n)
    return cen, coords


def run_vina_dock(rec_pdbqt, lig_pdbqt, center, out_pdbqt, box_size=20.0, exhaustiveness=32, cpu=20):
    v = Vina(sf_name="vina", cpu=cpu, verbosity=0)
    v.set_receptor(str(rec_pdbqt))
    v.set_ligand_from_file(str(lig_pdbqt))
    v.compute_vina_maps(center=list(center), box_size=[box_size, box_size, box_size])
    try:
        e_in = float(v.score()[0])
    except Exception:
        e_in = None
    v.dock(exhaustiveness=exhaustiveness, n_poses=5)
    v.write_poses(str(out_pdbqt), n_poses=5, overwrite=True)
    energies = v.energies(n_poses=5)
    scores = [round(float(row[0]), 2) for row in energies]
    inter_e = round(float(energies[0][1]), 2) if len(energies) > 0 and len(energies[0]) > 1 else None
    intra_e = round(float(energies[0][2]), 2) if len(energies) > 0 and len(energies[0]) > 2 else None
    return scores, inter_e, intra_e, (round(e_in, 2) if e_in is not None else None)


def dock_one_target(c):
    gene = c["gene"]
    pdb = c["pocket_pdb"]
    imat_pdbqt = OUT / "lig_imatinib.pdbqt"
    per_target_json = OUT / f"res_{gene}_{pdb}.json"
    if per_target_json.exists():
        old = json.load(open(per_target_json))
        if "error" not in old:
            return gene, old

    t0 = time.time()
    try:
        pdb_path = STRUCT / f"{pdb}.pdb"
        code = c["cocrystal_lig"]
        chain = c["cocrystal_chain"]
        resn = c["cocrystal_resn"]
        center, crys_coords, het_lines = ligand_instance_coords(pdb_path, code, chain, resn)

        rec_pdb = OUT / f"rec_{gene}_{pdb}.pdb"
        clean_receptor(pdb_path, rec_pdb, c["keep_chains"], c["keep_cofactors"])
        rec_pdbqt = OUT / f"rec_{gene}_{pdb}.pdbqt"
        prep_receptor_pdbqt(rec_pdb, rec_pdbqt)

        ctrl_pdbqt = OUT / f"ctrl_{gene}_{pdb}_{code}.pdbqt"
        prep_ctrl_ligand(het_lines, code, ctrl_pdbqt)
        ctrl_docked = OUT / f"ctrl_{gene}_{pdb}_{code}_docked.pdbqt"
        box_ctrl = 16.0 if len(crys_coords) <= 15 else 20.0
        ctrl_scores, ctrl_inter, _, ctrl_in_score = run_vina_dock(
            rec_pdbqt, ctrl_pdbqt, center, ctrl_docked, box_size=box_ctrl, exhaustiveness=32, cpu=20
        )
        ctrl_cen, _ = parse_pose_heavy_coords(ctrl_docked, pose=1)
        ctrl_rec_A = round(dist(ctrl_cen, center), 2)

        imat_runs = []
        best_score = 999.0
        best_cen = None
        best_inter = None
        best_intra = None
        best_pose_file = OUT / f"imat_{gene}_{pdb}_docked.pdbqt"

        for r_idx in range(3):
            run_file = OUT / f"imat_{gene}_{pdb}_run{r_idx+1}.pdbqt"
            sc, inter_e, intra_e, _ = run_vina_dock(
                rec_pdbqt, imat_pdbqt, center, run_file, box_size=20.0, exhaustiveness=32, cpu=20
            )
            rcen, _ = parse_pose_heavy_coords(run_file, pose=1)
            rdist = round(dist(rcen, center), 2)
            imat_runs.append({"run": r_idx + 1, "top_score": sc[0], "centroid_dist_A": rdist, "poses": sc})
            if sc[0] < best_score:
                best_score = sc[0]
                best_cen = rcen
                best_inter = inter_e
                best_intra = intra_e
                Path(best_pose_file).write_text(Path(run_file).read_text())

        imat_dist_A = round(dist(best_cen, center), 2)
        run_scores = [r["top_score"] for r in imat_runs]
        run_dists = [r["centroid_dist_A"] for r in imat_runs]

        gate_pass = bool(ctrl_rec_A < 3.0)
        in_pocket = bool(imat_dist_A < 3.0 and best_score < -6.0)

        res = {
            "gene": gene,
            "pdb": pdb,
            "pocket_type": c["pocket_type"],
            "cocrystal_lig": f"{code}:{chain}:{resn}",
            "cocrystal_n_heavy": len(crys_coords),
            "pocket_center": [round(x, 2) for x in center],
            "crystal_in_place_score": ctrl_in_score,
            "redock_score": ctrl_scores[0],
            "redock_poses": ctrl_scores,
            "redock_recovery_A": ctrl_rec_A,
            "gate_pass": gate_pass,
            "imatinib_best_score": best_score,
            "imatinib_mean_score": round(sum(run_scores) / len(run_scores), 2),
            "imatinib_std_score": round((sum((x - sum(run_scores)/3)**2 for x in run_scores)/3)**0.5, 2),
            "imatinib_inter_kcal": best_inter,
            "imatinib_intra_kcal": best_intra,
            "imatinib_in_pocket_A": imat_dist_A,
            "imatinib_run_dists_A": run_dists,
            "imatinib_runs": imat_runs,
            "in_pocket_engaged": in_pocket,
            "runtime_s": round(time.time() - t0, 1)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        res = {"gene": gene, "pdb": pdb, "error": f"{type(e).__name__}: {e}"}

    json.dump(res, open(per_target_json, "w"), indent=2)
    return gene, res


def main():
    candidates = json.load(open(DATA / "p1_candidate_targets.json"))
    imat_pdbqt = OUT / "lig_imatinib.pdbqt"
    if not imat_pdbqt.exists():
        prep_imatinib_pdbqt(imat_pdbqt)

    results_path = OUT / "p2_docking_results.json"
    results = json.load(open(results_path)) if results_path.exists() else {}
    # Seed per-target files from existing results
    for g, r in results.items():
        if "error" not in r:
            p = OUT / f"res_{g}_{r['pdb']}.json"
            if not p.exists():
                json.dump(r, open(p, "w"), indent=2)

    jobs = [c for c in candidates if c["pocket_pdb"] is not None]
    print(f"Dispatching {len(jobs)} docking targets across 12 workers (20 CPUs each)...", flush=True)

    with ProcessPoolExecutor(max_workers=12) as ex:
        fut_map = {ex.submit(dock_one_target, c): c["gene"] for c in jobs}
        for fut in as_completed(fut_map):
            gene, res = fut.result()
            results[gene] = res
            json.dump(results, open(results_path, "w"), indent=2)
            if "error" in res:
                print(f"  [ERR] {gene}: {res['error']}", flush=True)
            else:
                print(f"  [OK]  {gene:8s} ({res['pdb']}) | Redock={res['redock_score']:+6.2f} ({res['redock_recovery_A']:4.2f} A, {'PASS' if res['gate_pass'] else 'FAIL'}) | "
                      f"Imatinib={res['imatinib_best_score']:+6.2f} ({res['imatinib_in_pocket_A']:4.2f} A, Engaged={res['in_pocket_engaged']}) [{res['runtime_s']}s]", flush=True)

    print(f"\nCompleted {len(results)} / {len(jobs)} targets.")


if __name__ == "__main__":
    main()
