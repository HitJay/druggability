#!/usr/bin/env python3
"""Redock HCAR1 experimental ligands and compare pocket recovery."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import urllib.request
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation
from vina import Vina

ROOT=Path(__file__).resolve().parents[1]; P=ROOT/'data/gpr81_phase1'; P2=P/'phase2_prepared'; OUT=P/'phase3_5_controls'; (OUT/'ligands').mkdir(parents=True,exist_ok=True); (OUT/'poses').mkdir(exist_ok=True)
controls=[('CHBA','8Z87','A1D71','CHBA_CID13071646.sdf'),('3_5_DHBA','9KT9','34D','3_5_DHBA_CID7424.sdf'),('lactate','8Z8A','2OP','lactate_CID612.sdf')]

def atoms(path):
 out=[]
 for line in Path(path).read_text().splitlines():
  if line.startswith(('ATOM','HETATM')):
   try:
    el=(line[76:78].strip() or line[12:16].strip()[0]).upper()
    if el!='H': out.append((el,np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])) )
   except (ValueError, IndexError):
    # The locally generated reference-ligand PDB uses a minimally formatted
    # record; whitespace parsing is safer than silently returning no atoms.
    fields=line.split()
    try:
     el=fields[2].upper(); coord_start=6
     if el!='H': out.append((el,np.array([float(fields[coord_start]),float(fields[coord_start+1]),float(fields[coord_start+2])])) )
    except (ValueError, IndexError):
     continue
 return out

def prep_from_sdf(sdf,out):
 m=next(x for x in Chem.SDMolSupplier(str(sdf),removeHs=False) if x is not None); m=Chem.AddHs(m)
 if AllChem.EmbedMolecule(m,randomSeed=20260803,useRandomCoords=True)!=0: raise RuntimeError('embed failed')
 AllChem.MMFFOptimizeMolecule(m,maxIters=200); s=MoleculePreparation(); s.prepare(m); s.write_pdbqt_file(str(out)); return m.GetNumAtoms()

def prep_from_pdb(pdb,out):
 m=Chem.MolFromPDBFile(str(pdb),removeHs=False,sanitize=False)
 if m is None: raise RuntimeError('PDB parse failed')
 try: Chem.SanitizeMol(m)
 except: pass
 m=Chem.AddHs(m,addCoords=True); s=MoleculePreparation(); s.prepare(m); s.write_pdbqt_file(str(out)); return m.GetNumAtoms()

def parse_pose(p):
 lines=p.read_text().splitlines(); models=[];cur=[]
 for l in lines:
  if l.startswith('MODEL') and cur: models.append(cur);cur=[]
  cur.append(l)
 if cur:models.append(cur)
 score=None
 for l in models[0]:
  if l.startswith('REMARK VINA RESULT:'):score=float(l.split()[3])
 return models[0],score

def main():
 rows=[]
 for cid,rid,ref,sdf_name in controls:
  rec=json.loads((P2/'phase2_manifest.json').read_text())['structures']; r=next(x for x in rec if x['pdb_id']==rid); geom=r['ligand_geometry']; exp=next(P2.joinpath('reference_ligands').glob(f'{rid}_{ref}.pdb'))
  lig=OUT/'ligands'/f'{cid}.pdbqt'
  if sdf_name:
   sdf_path=P/'ligands'/sdf_name
   if not sdf_path.exists() and cid=='lactate':
    sdf_path.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve('https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/612/SDF?record_type=3d',sdf_path)
   n=prep_from_sdf(sdf_path,lig)
  else: n=prep_from_pdb(exp,lig)
  v=Vina(sf_name='vina',seed=20260803);v.set_receptor(r['receptor_pdbqt']['path']);v.compute_vina_maps(center=geom['center_A'],box_size=geom['box_size_A']);v.set_ligand_from_file(str(lig));v.dock(exhaustiveness=32,n_poses=5)
  pose=OUT/'poses'/f'{cid}_{rid}.pdbqt';v.write_poses(str(pose),n_poses=5,overwrite=True); lines,score=parse_pose(pose); pose_atoms=atoms(pose)
  exp_atoms=atoms(exp); pc=np.mean([x[1] for x in pose_atoms],axis=0); ec=np.mean([x[1] for x in exp_atoms],axis=0); centroid=float(np.linalg.norm(pc-ec))
  rows.append({'compound_id':cid,'receptor_id':rid,'experimental_ligand':ref,'prepared_atom_count':n,'experimental_heavy_atoms':len(exp_atoms),'redock_score_kcal_mol':score,'experimental_centroid_x':round(float(ec[0]),3),'experimental_centroid_y':round(float(ec[1]),3),'experimental_centroid_z':round(float(ec[2]),3),'predicted_centroid_x':round(float(pc[0]),3),'predicted_centroid_y':round(float(pc[1]),3),'predicted_centroid_z':round(float(pc[2]),3),'centroid_distance_A':round(centroid,3),'note':'centroid recovery; atom-mapped RMSD not asserted'} )
 with (OUT/'redocking_controls.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 (OUT/'redocking_controls.json').write_text(json.dumps({'controls':rows,'method':'unconstrained Vina redocking in experimental ligand-derived box','limitation':'PDB/PubChem atom mapping was not asserted; centroid distance is reported instead of invented RMSD'},indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
