"""ws6 (novel-pocket request): fpocket screening across all structures behind the
PK11195 binder list + new structural coverage (GRM5 4OO9, TMEM97 bovine 7M93/9ZIR).

For every structure:
  1. download PDB, strip to ATOM records (drop H, keep all chains) -> fpocket -f
  2. parse pockets_info.txt (score, druggability, volume, SASA, ...)
  3. parse pocketN_atm.pdb residue sets; compute overlap with the drug-like
     co-crystal ligand of the *known* (literature-reported) pocket
  4. a pocket "recovers" the known site if >=30% of ligand-contact residues
     (<4.5 A of any ligand atom) sit in the pocket OR the nearest pocket alpha
     sphere is <3.0 A from the ligand centroid
Outputs data/novelq_p2_fpocket_pockets.json (audit) + per-structure fpocket dirs.

Deterministic: fixed ligand codes carried over from emapunil_f2_docking.json
(same sources as the 2026-10-19 emapunil/FGIN campaigns) so the "known pocket"
baseline is identical across ligand series.
"""
import json, subprocess, sys, urllib.request
from pathlib import Path

BASE = Path("/das/user/QYJI/druggability/TSPO_assessment")
OUT = BASE / "output/novel_pockets"
OUT.mkdir(parents=True, exist_ok=True)

# pdb -> (label, gene, ligand code, chain (None=auto largest cluster), known-pocket description)
STRUCTURES = {
    "4RYI":  ("TSPO (BcTSPO/PK11195 crystal)", "TSPO", "PKA", "A", "PK11195 inner concave pocket (literature: ligand-dependent cholesterol/DRD site)"),
    "1XVP":  ("CAR LBD", "NR1I3", "CID", "A", "CAR ligand-binding pocket (co-activator-facing)"),
    "2QNV":  ("PXR LBD", "NR1I2", "CDZ", "A", "PXR large ligand-binding pocket"),
    "6X3X":  ("GABA-A a1/b3/g2 BZD site", "GABRA1/GABRB3/GABRG2", "DZP", "E", "benzodiazepine site (a/g interface)"),
    "6HUG":  ("GABA-A picrotoxin site", "GABRA-family", "PIO", "A", "pore/picrotoxin site"),
    "4DKL":  ("OPRM1", "OPRM1", "BF0", "A", "orthosteric morphinan pocket"),
    "4DJH":  ("OPRK1", "OPRK1", "JDC", "A", "orthosteric pocket"),
    "4WB9":  ("ALDH1A1", "ALDH1A1", "NAI", "A", "catalytic NAD pocket"),
    "5TGZ":  ("CNR1", "CNR1", "ZDG", "A", "orthosteric antagonist pocket"),
    "7F61":  ("HRH3", "HRH3", "CLR", "A", "orthosteric pocket"),
    "2ILT":  ("HSD11B1", "HSD11B1", "NAP", "A", "catalytic steroid/NADPH pocket"),
    "5HK1":  ("SIGMAR1", "SIGMAR1", "61W", "A", "orthosteric pocket"),
    "4XAQ":  ("GRM2 7TM", "GRM2", "40F", "A", "7TM allosteric pocket"),
    "4GQ4":  ("MEN1", "MEN1/KMT2A", "0RT", "A", "MLL inhibitor pocket"),
    "4OO9":  ("GRM5 7TM", "GRM5", "auto", "A", "mGlu5 7TM allosteric pocket (literature: MPEP-class site)"),
    "7M93":  ("TMEM97/S2R (bovine)", "TMEM97", "YT1", "A", "sigma-2 orthosteric pocket (PB28)"),
    "9ZIR":  ("TMEM97/S2R (bovine, zervimesine)", "TMEM97", "auto", "A", "sigma-2 orthosteric pocket (CT1812)"),
}
SKIP_AUTO_HET = {"HOH", "SO4", "PO4", "GOL", "EDO", "PEG", "ACT", "CL", "NA", "MG", "MN", "ZN", "CA", "CD", "K", "MES", "TRS", "EPE", "DMS", "MPD", "IPA", "ACE", "NH4", "BR", "IOD", "OZN", "NAG", "BMA", "MAN", "FUC", "FLC", "OLA", "OLB", "PE8", "1PE", "2PE", "P6G", "PG4", "PG5", "PG6", "SPD", "SPM", "PUT", "GDP", "GTP", "ADP", "ATP", "FMN", "FAD", "PLP", "CIT", "BCT", "CO3", "SCN", "NO3", "IHP", "BEF", "ALF"}

def fetch_pdb(pdb_id):
    dst = OUT / f"{pdb_id}.pdb"
    if not dst.exists():
        try:
            req = urllib.request.Request(f"https://files.rcsb.org/download/{pdb_id}.pdb",
                                         headers={"User-Agent": "Mozilla/5.0"})
            dst.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        except Exception:
            # large/deprecated-format entries: fetch mmCIF and convert via gemmi
            import gemmi
            cifreq = urllib.request.Request(f"https://files.rcsb.org/download/{pdb_id}.cif",
                                            headers={"User-Agent": "Mozilla/5.0"})
            cif_bytes = urllib.request.urlopen(cifreq, timeout=180).read()
            cifp = OUT / f"{pdb_id}.cif"
            cifp.write_bytes(cif_bytes)
            st = gemmi.read_structure(str(cifp))
            st.setup_entities()
            dst.write_text(st.make_pdb_string())
    return dst

def protein_pdb(src: Path):
    lines = [l for l in src.read_text().splitlines()
             if l.startswith("ATOM") and l[76:78].strip() != "H"]
    dst = src.with_suffix("").with_suffix("")  # 4RYI -> 4RYI (reuse stem)
    dst = src.parent / f"{src.stem}_prot.pdb"
    dst.write_text("\n".join(lines) + "\n")
    return dst, len(lines)

def het_ligands(pdb_path: Path):
    """cluster HETATM by (resname, chain); return [(resname, chain, natoms, centroid)]"""
    groups = {}
    for l in pdb_path.read_text().splitlines():
        if not l.startswith("HETATM"):
            continue
        res, ch = l[17:20].strip(), l[21].strip()
        groups.setdefault((res, ch), []).append(l)
    out = []
    for (res, ch), ls in groups.items():
        if res in SKIP_AUTO_HET:
            continue
        xs = [l[30:38] for l in ls]
        n = len(ls)
        cx = sum(float(x) for x in xs) / n
        cy = sum(float(l[38:46]) for l in ls) / n
        cz = sum(float(l[46:54]) for l in ls) / n
        out.append((res, ch, n, (cx, cy, cz)))
    out.sort(key=lambda t: -t[2])
    return out

def ligand_atoms(pdb_path: Path, res, chain):
    return [(float(l[30:38]), float(l[38:46]), float(l[46:54]))
            for l in pdb_path.read_text().splitlines()
            if l.startswith("HETATM") and l[17:20].strip() == res and l[21].strip() == chain]

def parse_info(info_path: Path):
    blocks, cur = {}, None
    for line in info_path.read_text().splitlines():
        ls = line.strip()
        if ls.startswith("Pocket "):
            cur = int(ls.split()[1].rstrip(":"))
            blocks[cur] = {}
        elif cur is not None and ":" in ls:
            k, v = ls.split(":", 1)
            try:
                blocks[cur][k.strip()] = float(v.strip())
            except ValueError:
                blocks[cur][k.strip()] = v.strip()
    return blocks

def parse_pocket_residues(atm_path: Path):
    res = set()
    alpha = []
    for l in atm_path.read_text().splitlines():
        if l.startswith("ATOM"):
            res.add((l[21].strip(), l[22:26].strip()))
        elif l.startswith("QS "):
            alpha.append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
    return res, alpha

def run_one(pdb_id, cfg, results):
    label, gene, lig, chain, known = cfg
    src = fetch_pdb(pdb_id)
    prot, natoms = protein_pdb(src)
    # known ligand resolution
    if lig == "auto":
        cands = [c for c in het_ligands(src) if c[2] >= 15]
        if not cands:
            results[pdb_id] = {"label": label, "error": "no drug-like co-crystal ligand"}
            return
        res, lchain, _, lcen = cands[0]
    else:
        res, lchain = lig, chain
        lat = ligand_atoms(src, res, lchain)
        if not lat:
            results[pdb_id] = {"label": label, "error": f"ligand {res} chain {lchain} not found"}
            return
        lcen = (sum(a[0] for a in lat) / len(lat), sum(a[1] for a in lat) / len(lat), sum(a[2] for a in lat) / len(lat))
    lat = ligand_atoms(src, res, lchain)
    # fpocket
    outdir = prot.parent / f"{prot.stem}_out"
    if not outdir.exists():
        subprocess.run(["fpocket", "-f", str(prot)], cwd=str(prot.parent),
                       capture_output=True, timeout=3600)
    info = outdir / f"{prot.stem}_info.txt"
    if not info.exists():
        results[pdb_id] = {"label": label, "error": "fpocket produced no info file"}
        return
    blocks = parse_info(info)
    # ligand-contact residues on the protein
    contact = set()
    for l in prot.read_text().splitlines():
        if not l.startswith("ATOM"):
            continue
        x, y, z = float(l[30:38]), float(l[38:46]), float(l[46:54])
        if min((x - a[0]) ** 2 + (y - a[1]) ** 2 + (z - a[2]) ** 2 for a in lat) < 20.25:  # 4.5 A
            contact.add((l[21].strip(), l[22:26].strip()))
    pockets = []
    for pid, m in sorted(blocks.items()):
        atm = outdir / "pockets" / f"pocket{pid}_atm.pdb"
        if not atm.exists():
            continue
        pres, alpha = parse_pocket_residues(atm)
        ov = len(pres & contact) / max(1, len(contact))
        near = 1e9
        if alpha:
            near = min(((c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2 + (c[2] - a[2]) ** 2) ** 0.5
                       for a in alpha for c in [lcen])
        pockets.append({
            "pocket_id": pid,
            "score": m.get("Score"), "ds": m.get("Druggability Score"),
            "volume": m.get("Volume"), "sasa": m.get("Total SASA"),
            "n_alpha": m.get("Number of Alpha Spheres"),
            "apolar_as_prop": m.get("Apolar alpha sphere proportion"),
            "flexibility": m.get("Flexibility"),
            "n_res": len(pres), "overlap_known": round(ov, 3),
            "near_known_lig_A": round(near, 2) if near < 1e8 else None,
            "recovers_known": bool(ov >= 0.30 or (near is not None and near < 3.0)),
            "residues": sorted(pres),
        })
    results[pdb_id] = {
        "label": label, "gene": gene, "known_pocket": known,
        "pocket_ligand": res, "pocket_chain": lchain,
        "ligand_centroid": [round(v, 2) for v in lcen],
        "n_atoms_input": natoms, "n_pockets_fpocket": len(blocks),
        "pockets": pockets,
    }
    print(f"{pdb_id} {label}: {len(blocks)} pockets; known-lig {res}/{lchain}; "
          f"recovered by {[p['pocket_id'] for p in pockets if p['recovers_known']]}")

def main():
    results = {}
    for pdb_id, cfg in STRUCTURES.items():
        try:
            run_one(pdb_id, cfg, results)
        except Exception as e:
            results[pdb_id] = {"label": cfg[0], "error": f"{type(e).__name__}: {e}"}
            print(pdb_id, "ERROR", e)
        json.dump(results, open(OUT / ".." / ".." / "data" / "novelq_p2_fpocket_pockets.json", "w"), indent=1)
    print("saved data/novelq_p2_fpocket_pockets.json")

if __name__ == "__main__":
    main()
