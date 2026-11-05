#!/usr/bin/env python3
"""Prepare 10 domain-resolved Boltz-2 YAML + sanitized Baker omicMSA (.a3m) inputs
for all complex-template-free prioritized PPI frontrunners across the Top 5 Axes."""
import json
from pathlib import Path

OUT_DIR = Path("/das/user/QYJI/druggability/reports/frontrunners_triage")
MSA_SRC = Path("/das/user/QYJI/druggability/humanPPI_repro/work/single_msas")
BOLTZ_DIR = OUT_DIR / "md_fep_study"
MSA_OUT = BOLTZ_DIR / "msas"
YAML_OUT = BOLTZ_DIR / "boltz_inputs"
MSA_OUT.mkdir(parents=True, exist_ok=True)
YAML_OUT.mkdir(parents=True, exist_ok=True)

# 10 template-free prioritized Frontrunner complexes (covering all 5 Top Axes)
COMPLEX_SPECS = [
    {
        "id": "01_STARD10_PRMT6",
        "axis": "Axis 5A (90% Tier)",
        "pair_label": "STARD10-PRMT6",
        "chainA": {"id": "A", "gene": "STARD10", "uniprot": "Q9Y365", "start": 1, "end": 291},
        "chainB": {"id": "B", "gene": "PRMT6",   "uniprot": "Q96LA8", "start": 35, "end": 375},
        "fep_targets": [
            ("A", 90, "STARD10 Glu90 (RF2 #1 Contact to PRMT6 Ala261, p=0.899)"),
            ("A", 89, "STARD10 Ile89 (RF2 #2 Contact to PRMT6 Gly224, p=0.868)"),
            ("A", 91, "STARD10 Tyr91 (RF2 #4 Contact to PRMT6 Arg260, p=0.849)"),
            ("B", 260, "PRMT6 Arg260 (RF2 Contact to STARD10 Tyr91, p=0.849)"),
            ("B", 261, "PRMT6 Ala261 (RF2 #1 Contact to STARD10 Glu90, p=0.899)"),
            ("B", 194, "PRMT6 Ala194 (Human Coding SAV p.Ala194Val, rs2232016)"),
        ],
    },
    {
        "id": "02_PPARG_LPIN1",
        "axis": "Axis 4 (80% Tier)",
        "pair_label": "PPARG-LPIN1",
        "chainA": {"id": "A", "gene": "PPARG", "uniprot": "P37231", "start": 235, "end": 505},
        "chainB": {"id": "B", "gene": "LPIN1", "uniprot": "Q14693", "start": 500, "end": 760},
        "fep_targets": [
            ("A", 495, "PPARG Pro495 (FPLD3/T2D Dual-Pathogenic SAV p.Pro495Leu, rs121909244)"),
            ("A", 318, "PPARG Val318 (T2D/FPLD3 Dual-Pathogenic SAV p.Val318Met, rs72551362)"),
            ("A", 425, "PPARG Arg425 (FPLD3 Dual-Pathogenic SAV p.Arg425Cys, rs72551364)"),
            ("A", 289, "PPARG Lys289 (RF2 #2 Contact to LPIN1 Leu524, p=0.181)"),
            ("B", 725, "LPIN1 Leu725 (Validated LXXIL Motif Mutagen L725F, PMID:16959991)"),
            ("B", 726, "LPIN1 Ile726 (Validated LXXIL Motif Mutagen I726F, PMID:16959991)"),
            ("B", 524, "LPIN1 Leu524 (RF2 #2 Contact to PPARG Lys289, p=0.181)"),
        ],
    },
    {
        "id": "03_PRKAG1_FNIP1",
        "axis": "Axis 1A (90% Tier, #1 Overall)",
        "pair_label": "FNIP1-PRKAG1",
        "chainA": {"id": "A", "gene": "PRKAG1", "uniprot": "P54619", "start": 1, "end": 331},
        "chainB": {"id": "B", "gene": "FNIP1",  "uniprot": "Q8TF40", "start": 450, "end": 760},
        "fep_targets": [
            ("A", 89,  "PRKAG1 Thr89 (AlphaMissense LPath SAV p.Thr89Ser, rs1126930, AM=0.879)"),
            ("A", 90,  "PRKAG1 Asp90 (Validated AMP-Binding Mutagen D90A)"),
            ("A", 134, "PRKAG1 Pro134 (RF2 #1 Contact to FNIP1 Lys495, p=0.163)"),
            ("A", 135, "PRKAG1 Asn135 (RF2 #2 Contact to FNIP1 Lys495, p=0.163)"),
            ("B", 495, "FNIP1 Lys495 (RF2 #1 Contact to PRKAG1 Pro134/Asn135, p=0.163)"),
            ("B", 593, "FNIP1 Ser593 (Validated AMPK Phosphorylation Mutagen S593A)"),
            ("B", 648, "FNIP1 Gln648 (cDENN Coding SAV p.Gln648Arg, rs26008)"),
        ],
    },
    {
        "id": "04_FNIP1_PRKAG2",
        "axis": "Axis 1B (80% Tier)",
        "pair_label": "FNIP1-PRKAG2",
        "chainA": {"id": "A", "gene": "FNIP1",  "uniprot": "Q8TF40", "start": 100, "end": 320},
        "chainB": {"id": "B", "gene": "PRKAG2", "uniprot": "Q9UGJ0", "start": 30, "end": 550},
        "fep_targets": [
            ("A", 220, "FNIP1 Ser220 (RF2 #1 Contact p=0.167 & AMPK Mutagen S220A)"),
            ("A", 261, "FNIP1 Ser261 (Validated AMPK Phosphorylation Mutagen S261A)"),
            ("A", 117, "FNIP1 Tyr117 (RF2 #3 Contact to PRKAG2 Gly80, p=0.151)"),
            ("B", 45,  "PRKAG2 Met45 (RF2 #1 Contact to FNIP1 Ser220, p=0.167)"),
            ("B", 302, "PRKAG2 Arg302 (CMH6/WPW Dual-Pathogenic SAV p.Arg302Gln, rs121908987, AM=0.998)"),
            ("B", 383, "PRKAG2 His383 (CMH6 Dual-Pathogenic SAV p.His383Arg, rs121908988, AM=0.999)"),
            ("B", 531, "PRKAG2 Arg531 (CMH6 Dual-Pathogenic SAV p.Arg531Gly/Gln, rs121908990, AM=0.999)"),
        ],
    },
    {
        "id": "05_PRKAA1_FNIP1",
        "axis": "Axis 1C (80% Tier)",
        "pair_label": "FNIP1-PRKAA1",
        "chainA": {"id": "A", "gene": "PRKAA1", "uniprot": "Q13131", "start": 15, "end": 480},
        "chainB": {"id": "B", "gene": "FNIP1",  "uniprot": "Q8TF40", "start": 380, "end": 620},
        "fep_targets": [
            ("A", 266, "PRKAA1 Lys266 (RF2 #1 Contact to FNIP1 Pro411, p=0.134)"),
            ("A", 263, "PRKAA1 Asp263 (RF2 #2 Contact to FNIP1 Pro411, p=0.132)"),
            ("A", 262, "PRKAA1 Val262 (RF2 #4 Contact to FNIP1, p=0.126)"),
            ("B", 411, "FNIP1 Pro411 (RF2 #1 Contact to PRKAA1 Lys266, p=0.134)"),
            ("B", 593, "FNIP1 Ser593 (Validated AMPK Phosphorylation Mutagen S593A)"),
        ],
    },
    {
        "id": "06_FNIP1_BTRC",
        "axis": "Axis 2A (80% Tier, Molecular Glue Degrader)",
        "pair_label": "FNIP1-BTRC",
        "chainA": {"id": "A", "gene": "FNIP1", "uniprot": "Q8TF40", "start": 180, "end": 340},
        "chainB": {"id": "B", "gene": "BTRC",  "uniprot": "Q9Y297", "start": 250, "end": 605},
        "fep_targets": [
            ("A", 206, "FNIP1 Asn206 (RF2 #1 Contact to BTRC Arg513, p=0.129)"),
            ("A", 253, "FNIP1 Asp253 (RF2 #2 Contact to BTRC Ser484/Asp485, p=0.125)"),
            ("A", 252, "FNIP1 Arg252 (RF2 #3 Contact to BTRC Ser484, p=0.124)"),
            ("B", 513, "BTRC Arg513 (RF2 #1 Contact to FNIP1 Asn206, p=0.129)"),
            ("B", 510, "BTRC Arg510 (Validated WD40 Substrate-Abolishing Mutagen R510A)"),
            ("B", 307, "BTRC Tyr307 (Validated WD40 Substrate-Abolishing Mutagen Y307A)"),
            ("B", 592, "BTRC Pro592 (WD40 Coding SAV p.Pro592His, rs2270439)"),
        ],
    },
    {
        "id": "07_FNIP1_FBXW11",
        "axis": "Axis 2B (80% Tier, Paralog E3 Degrader)",
        "pair_label": "FNIP1-FBXW11",
        "chainA": {"id": "A", "gene": "FNIP1",  "uniprot": "Q8TF40", "start": 760, "end": 960},
        "chainB": {"id": "B", "gene": "FBXW11", "uniprot": "Q9UKB1", "start": 1, "end": 480},
        "fep_targets": [
            ("A", 850, "FNIP1 Asp850 (RF2 #1 Contact to FBXW11 Asp4, p=0.138)"),
            ("A", 849, "FNIP1 Ile849 (RF2 #2 Contact to FBXW11 Asp4, p=0.135)"),
            ("B", 363, "FBXW11 Arg363 (NEDJED Dual-Pathogenic WD40 SAV p.Arg363Trp, rs1758081729, AM=0.997)"),
            ("B", 444, "FBXW11 Glu444 (NEDJED Dual-Pathogenic WD40 SAV p.Glu444Lys, rs2113754835, AM=0.999)"),
            ("B", 447, "FBXW11 Arg447 (NEDJED Dual-Pathogenic WD40 SAV p.Arg447Gln, rs1757708758, AM=1.000)"),
        ],
    },
    {
        "id": "08_PDE3B_RAPGEF3",
        "axis": "Axis 3A (80% Tier)",
        "pair_label": "PDE3B-RAPGEF3",
        "chainA": {"id": "A", "gene": "PDE3B",   "uniprot": "Q13370", "start": 1, "end": 160},
        "chainB": {"id": "B", "gene": "RAPGEF3", "uniprot": "O95398", "start": 1, "end": 350},
        "fep_targets": [
            ("A", 5,   "PDE3B Glu5 (RF2 #4 Contact to RAPGEF3 Arg64, p=0.194)"),
            ("A", 6,   "PDE3B Arg6 (Validated EPAC1-Binding Mutagen R6A, PMID:21393242)"),
            ("A", 9,   "PDE3B Lys9 (Validated EPAC1-Binding Mutagen K9A, PMID:21393242)"),
            ("A", 11,  "PDE3B Met11 (RF2 #2 Contact to RAPGEF3 Asn42, p=0.197)"),
            ("A", 12,  "PDE3B Arg12 (Validated EPAC1-Binding Mutagen R12A, PMID:21393242)"),
            ("B", 42,  "RAPGEF3 Asn42 (RF2 #2 Contact to PDE3B Met11, p=0.197)"),
            ("B", 64,  "RAPGEF3 Arg64 (RF2 #4 Contact to PDE3B Glu5, p=0.194)"),
            ("B", 193, "RAPGEF3 Arg193 (Coding SAV p.Arg193Gly, rs372999850)"),
        ],
    },
    {
        "id": "09_PDE3B_LGR4",
        "axis": "Axis 3B (80% Tier)",
        "pair_label": "PDE3B-LGR4",
        "chainA": {"id": "A", "gene": "PDE3B", "uniprot": "Q13370", "start": 350, "end": 650},
        "chainB": {"id": "B", "gene": "LGR4",  "uniprot": "Q9BXB1", "start": 25, "end": 380},
        "fep_targets": [
            ("A", 421, "PDE3B Asp421 (RF2 #1 Contact to LGR4 Gly151, p=0.214)"),
            ("A", 425, "PDE3B Asn425 (RF2 #2 Contact to LGR4 Gly151, p=0.214)"),
            ("B", 151, "LGR4 Gly151 (RF2 #1 Contact to PDE3B Asp421, p=0.214)"),
            ("B", 96,  "LGR4 Ile96 (Functional Coding SAV p.Ile96Val, rs757351670)"),
            ("B", 363, "LGR4 Gly363 (Functional Coding SAV p.Gly363Cys, rs117543292)"),
        ],
    },
    {
        "id": "10_GRB14_TNKS2",
        "axis": "Axis 5B (80% Tier)",
        "pair_label": "GRB14-TNKS2",
        "chainA": {"id": "A", "gene": "GRB14", "uniprot": "Q14449", "start": 240, "end": 540},
        "chainB": {"id": "B", "gene": "TNKS2", "uniprot": "Q9H2K2", "start": 850, "end": 1166},
        "fep_targets": [
            ("A", 269, "GRB14 Gly269 (RF2 #1 Contact to TNKS2 Gln973/Ile994, p=0.160)"),
            ("A", 363, "GRB14 Gln363 (RF2 #4 Contact in BPS Domain, p=0.158)"),
            ("A", 348, "GRB14 Gln348 (Validated AKT/MAPK-Restoring Mutagen Q348A)"),
            ("A", 349, "GRB14 Asn349 (Validated AKT/MAPK-Restoring Mutagen N349A)"),
            ("B", 973, "TNKS2 Gln973 (RF2 #1 Contact to GRB14 Gly269, p=0.160)"),
            ("B", 994, "TNKS2 Ile994 (RF2 #2 Contact to GRB14 Gly269, p=0.160)"),
            ("B", 1054, "TNKS2 Met1054 (Validated Loss-of-Activity Mutagen M1054V)"),
        ],
    },
]

def slice_a3m(uniprot_acc: str, start_1: int, end_1: int, out_a3m: Path) -> str:
    """Slice a Baker single_msas/<acc>.a3m to [start_1, end_1] (1-indexed inclusive),
    stripping the >mask record and preserving lowercase insertions inside the slice."""
    src = MSA_SRC / f"{uniprot_acc}.a3m"
    raw_lines = src.read_text().splitlines()
    records = []
    curr_h, curr_s = None, []
    for l in raw_lines:
        if l.startswith(">"):
            if curr_h is not None:
                records.append((curr_h, "".join(curr_s)))
            curr_h = l
            curr_s = []
        else:
            curr_s.append(l.strip())
    if curr_h is not None:
        records.append((curr_h, "".join(curr_s)))

    # Drop >mask record
    if records and records[0][0].startswith(">mask"):
        records = records[1:]

    start_0 = start_1 - 1
    end_0 = end_1
    query_full = records[0][1]
    query_sub = query_full[start_0:end_0]
    assert len(query_sub) == (end_1 - start_1 + 1), f"Length mismatch for {uniprot_acc}: {len(query_sub)}"

    out_lines = [f">{uniprot_acc}_{start_1}_{end_1}", query_sub]
    for h, seq in records[1:]:
        col = 0
        sub_chars = []
        for ch in seq:
            if not ch.islower():
                if start_0 <= col < end_0:
                    sub_chars.append(ch)
                col += 1
            else:
                if start_0 < col <= end_0:
                    sub_chars.append(ch)
        s_out = "".join(sub_chars)
        # Skip all-gap rows
        if s_out.count("-") < len(query_sub):
            out_lines.append(h)
            out_lines.append(s_out)

    out_a3m.write_text("\n".join(out_lines) + "\n")
    return query_sub

manifest = []
for spec in COMPLEX_SPECS:
    cid = spec["id"]
    cA, cB = spec["chainA"], spec["chainB"]
    a3m_A = MSA_OUT / f"{cA['gene']}_{cA['start']}_{cA['end']}.a3m"
    a3m_B = MSA_OUT / f"{cB['gene']}_{cB['start']}_{cB['end']}.a3m"
    seq_A = slice_a3m(cA["uniprot"], cA["start"], cA["end"], a3m_A)
    seq_B = slice_a3m(cB["uniprot"], cB["start"], cB["end"], a3m_B)

    # Note: on loong, MSA path will be /work/user/QYJI/frontrunners_md_fep/msas/...
    loong_a3m_A = f"/work/user/QYJI/frontrunners_md_fep/msas/{a3m_A.name}"
    loong_a3m_B = f"/work/user/QYJI/frontrunners_md_fep/msas/{a3m_B.name}"

    yaml_text = f"""version: 1
sequences:
  - protein:
      id: A
      sequence: {seq_A}
      msa: {loong_a3m_A}
  - protein:
      id: B
      sequence: {seq_B}
      msa: {loong_a3m_B}
"""
    yaml_file = YAML_OUT / f"{cid}.yaml"
    yaml_file.write_text(yaml_text)
    spec_copy = dict(spec)
    spec_copy["seqA_len"] = len(seq_A)
    spec_copy["seqB_len"] = len(seq_B)
    spec_copy["total_len"] = len(seq_A) + len(seq_B)
    spec_copy["yaml_file"] = str(yaml_file)
    manifest.append(spec_copy)
    print(f"Prepared {cid:20s} | {cA['gene']}({cA['start']}-{cA['end']}, {len(seq_A)}aa) + {cB['gene']}({cB['start']}-{cB['end']}, {len(seq_B)}aa) = {len(seq_A)+len(seq_B)}aa")

(BOLTZ_DIR / "manifest_10complexes.json").write_text(json.dumps(manifest, indent=2))
print("Saved manifest_10complexes.json")
