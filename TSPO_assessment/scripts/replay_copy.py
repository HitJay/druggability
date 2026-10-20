
import os, sys, json, time
sys.path.insert(0,'/das/user/QYJI/druggability/TSPO_assessment/scripts')
import numpy as np, openmm as mm, openmm.unit as unit
from openmm import app
from openmmforcefields.generators import SMIRNOFFTemplateGenerator
import fep_a3_lib as L
lig=L.lig_molecule('fgin')
tg=SMIRNOFFTemplateGenerator(molecules=[lig])
ff=app.ForceField('amber14/protein.ff14SB.xml','amber14/tip3p.xml')
ff.registerTemplateGenerator(tg.generator)
p=app.PDBFile(f"{L.DOCK}/f4_4RYI_fgin_relaxed.pdb")
sy=ff.createSystem(p.topology, nonbondedMethod=app.CutoffNonPeriodic, nonbondedCutoff=1.2*unit.nanometer)
print('FILE-ARG OK', sy.getNumParticles())

import openmm.app as _appmod
FF_before = _appmod.ForceField
from fep_a3_lib import build_manual_debug
FF_after = _appmod.ForceField
print("ForceField class changed by lib import:", FF_before is not FF_after)
try:
    sy2 = build_manual_debug("4RYI", "fgin")
    print("LIB-MODULE OK", sy2.getNumParticles())
except Exception as e:
    print("LIB-MODULE FAIL:", str(e)[:80])
