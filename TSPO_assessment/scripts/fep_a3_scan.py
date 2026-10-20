"""Thin CLI wrapper for fep_a3_lib + inline A/B debug."""
import sys

sys.path.insert(0, "/das/user/QYJI/druggability/TSPO_assessment/scripts")

# ORDER MATTERS (empirically): openmm.app -> openmmforcefields.generators -> fep_a3_lib
from openmm import app
from openmmforcefields.generators import SMIRNOFFTemplateGenerator  # noqa: F401
import openmm.unit as unit

from fep_a3_lib import mode_contacts, mode_run, lig_molecule, DOCK

if __name__ == "__main__":
    if "--ab5" in sys.argv:
        from fep_a3_lib import build_manual_debug
        sy = build_manual_debug("4RYI", "fgin")
        print("AB5 lib-module manual OK", sy.getNumParticles())
        sys.exit(0)
    if "--ab4" in sys.argv:
        from fep_a3_lib import build_system
        out = build_system("4RYI", "fgin")
        print("AB4 build_system literal OK", out[2].getNumParticles())
        sys.exit(0)
    if "--ab3" in sys.argv:
        from openmmforcefields.generators import SMIRNOFFTemplateGenerator
        lig = lig_molecule("fgin")
        tg = SMIRNOFFTemplateGenerator(molecules=[lig])
        ff = app.ForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
        ff.registerTemplateGenerator(tg.generator)
        p = app.PDBFile(f"{DOCK}/f4_4RYI_fgin_relaxed.pdb")
        sy = ff.createSystem(p.topology, nonbondedMethod=app.CutoffNonPeriodic,
                             nonbondedCutoff=1.2 * unit.nanometer)
        print("AB3 manual+cutoff OK", sy.getNumParticles())
        sys.exit(0)
    if "--ab2" in sys.argv:
        import traceback
        from fep_a3_lib import build_system
        try:
            out = build_system("4RYI", "fgin")
            print("AB2 build_system OK", out[2].getNumParticles())
        except Exception:
            traceback.print_exc()
        sys.exit(0)
    if "--ab" in sys.argv:
        from openmmforcefields.generators import SMIRNOFFTemplateGenerator
        lig = lig_molecule("fgin")
        tg = SMIRNOFFTemplateGenerator(molecules=[lig])
        ff = app.ForceField("amber14/protein.ff14SB.xml", "amber14/tip3p.xml")
        ff.registerTemplateGenerator(tg.generator)
        p = app.PDBFile(f"{DOCK}/f4_4RYI_fgin_relaxed.pdb")
        sy = ff.createSystem(p.topology)
        print("AB manual OK", sy.getNumParticles())
        sys.exit(0)
    mode = sys.argv[1]
    if mode == "contacts":
        mode_contacts(sys.argv[2], sys.argv[3])
    elif mode == "run":
        mode_run(sys.argv[2], sys.argv[3], sys.argv[4].split(","))
    else:
        raise SystemExit(__doc__)
