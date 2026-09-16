#!/usr/bin/env python3
"""
scripts/generate_boltz_inputs.py

Generate Boltz-2 complex YAML files for the 4-receptor x 3-ligand matrix:
Receptors: OXTR (P30559), AVPR1A (P37288), AVPR1B (P47901), AVPR2 (P30518)
Peptide Ligands:
  - OXT:      CYIQNCPLG-NH2
  - OXT_Gly:  CYIQNCGLG-NH2 (Lilly selective analog)
  - AVP:      CYFQNCPRG-NH2 (Endogenous vasopressin)
"""

import os
import yaml
from pathlib import Path

BASE_DIR = Path("/das/user/QYJI/druggability/OXTR_assessment")
BOLTZ_DIR = BASE_DIR / "boltz_inputs"
BOLTZ_DIR.mkdir(parents=True, exist_ok=True)

RECEPTORS = {
    "OXTR": {
        "uniprot": "P30559",
        # Mature receptor sequence (aa 1-389)
        "seq": (
            "MEGALAANWSAEAANASAAPPGAEGNRTAGPPRRNEALARVEVAVLCLILLLALSGNACV"
            "LLALRTTRQKHSRLFFFMKHLSIADLVVAVFQVLPQLLWDITFRFYGPDLLCRLVKYLQV"
            "VGMFASTYLLLLMSLDRCLAICQPLRSLRRRTDRLAVLATWLGCLVASAPQVHIFSLREV"
            "ADGVFDCWAVFIQPWGPKAYITWITLAVYIVPVIVLAACYGLISFKIWQNLRLKTAAAAA"
            "AEAPEGAAAGDGGRVALARVSSVKLISKAKIRTVKMTFIIVLAFIVCWTPFFFVQMWSVW"
            "DANAPKEASAFIIVMLLASLNSCCNPWIYMLFTGHLFHELVQRFLCCSASYLKGRRLGET"
            "SASKKSNSSSFVLSHRSSSQRSCSQPSTA"
        )
    },
    "AVPR1A": {
        "uniprot": "P37288",
        "seq": (
            "MRLSAGPDAGPSGNSSPWWPLATGAGNTSRMETPGEAALGNRSRGPEARPLELVRVVLVA"
            "VLLLLALSGNACVLLALRTTRHKHSRLFFFMKHLSIADLVVAVFQVLPQLLWDITYRFQG"
            "PDLLCRAVKYLQVLSMFASTYMLLAMTLDRYLAICHPLKSLQQPARRLVALVAWLGCLVA"
            "SVPQVHIFSLREVADGVFDCWAVFIQPWGPKAYVTWITLAVYIVPVIVLAACYGLISFKI"
            "WQNLRLKTAAAAAGEAPTAEAGAGDGGRVALARVSSVKLISKAKIRTVKMTFIIVLAFIV"
            "CWTPFFFVQMWSVWDANAPKEASAFIIVMLLASLNSCCNPWIYMLFTGHLFHELVQRFLC"
            "CSASYLKGRRLGETSASKKSNSSSFVLSHRSSSQRSCSQPSTA"
        )
    },
    "AVPR1B": {
        "uniprot": "P47901",
        "seq": (
            "MDSGPLWDANPTPRGTGSLPAPTVTCSDLREEARPLEVVLLALLVVLALSGNACVLLALR"
            "TTRQKHSRLFFFMKHLSIADLVVAVFQVLPQLLWDITFRFYGPDLLCRLVKYLQVVGMFA"
            "STYLLLLMSLDRCLAICQPLRSLRRRTDRLAVLATWLGCLVASAPQVHIFSLREVADGVF"
            "DCWAVFIQPWGPKAYITWITLAVYIVPVIVLAACYGLISFKIWQNLRLKTAAAAAEAPEG"
            "AAAGDGGRVALARVSSVKLISKAKIRTVKMTFIIVLAFIVCWTPFFFVQMWSVWDANAPK"
            "EASAFIIVMLLASLNSCCNPWIYMLFTGHLFHELVQRFLCCSASYLKGRRLGETSASKKS"
            "NSSSFVLSHRSSSQRSCSQPSTA"
        )
    },
    "AVPR2": {
        "uniprot": "P30518",
        "seq": (
            "MLMASTTSAVPGHPSLPSLPSNSSQERPLDTRDPLLARAELALLSIVFVAVALSNGLVLA"
            "ALARRGRRGHWAPIHVFIGHLCLADLAVALFQVLPQLAWKATDRFRGPDALCRAVKYLQMV"
            "GMYASSYMILAMTLDRHRAICRPMLAYRHGSGAHWNRPVLVAWAFSLLLSTPQAIFIFRE"
            "VEDGDYDCWACFIEPWGAKTYVTWISIAVFVAPVIVLAACVGLIAFRTWKSLRSKLKTSK"
            "KKAAVAKRKAAMRVSSVKLISKAKIRTVKMTFIILLAFLICWAPFFIIQMWSVWDENFPE"
            "ETSAFIITMLLASLNSCCNPWIYMAFTGHLFHELIQRFLCCSAFLRRGRCLGATSPAKKS"
            "NSSSFVLSRRSSSQRSCSQPSTA"
        )
    }
}

PEPTIDES = {
    "OXT": {
        "seq": "CYIQNCPLG",
        "description": "Native Oxytocin (9-mer)"
    },
    "OXT_Gly": {
        "seq": "CYIQNCGLG",
        "description": "Lilly selective Oxytocin analog (Pro7Gly substitution)"
    },
    "AVP": {
        "seq": "CYFQNCPRG",
        "description": "Native Arginine Vasopressin (9-mer)"
    }
}

def main():
    manifest = []
    for rec_name, rec_info in RECEPTORS.items():
        for pep_name, pep_info in PEPTIDES.items():
            job_name = f"{rec_name}_{pep_name}"
            yaml_path = BOLTZ_DIR / f"{job_name}.yaml"
            
            yaml_content = {
                "version": 1,
                "sequences": [
                    {
                        "protein": {
                            "id": "P",
                            "sequence": pep_info["seq"]
                        }
                    },
                    {
                        "protein": {
                            "id": "R",
                            "sequence": rec_info["seq"]
                        }
                    }
                ]
            }
            
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f, sort_keys=False)
            
            manifest.append({
                "job_name": job_name,
                "receptor": rec_name,
                "peptide": pep_name,
                "yaml_file": str(yaml_path.name)
            })
            print(f"Generated: {yaml_path.name}")

    # Write manifest
    with open(BOLTZ_DIR / "boltz_matrix_manifest.yaml", "w") as f:
        yaml.dump(manifest, f, sort_keys=False)
    
    # Sync to CIFS shared folder
    os.system(f"cp -f {BOLTZ_DIR}/*.yaml /TDE_TV/shared_folder/QYJI/druggability/OXTR_assessment/boltz_inputs/")
    print(f"All 12 Boltz-2 YAML configurations generated and synced to CIFS.")

if __name__ == "__main__":
    main()
