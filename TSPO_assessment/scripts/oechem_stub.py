"""openeye stub for perses on license-free environments.

perses' PointMutationExecutor imports openeye unconditionally but only USES it for
(i) an isinstance(ligand_input, oechem.OEMol) check and (ii) SDF/OEB parsing helpers
in perses.utils.openeye. We pass ligand_input=None and protein/ligand as PDB, so a
stub satisfies the imports. If a real openeye license is later available, delete
this stub registration and the driver will use the genuine toolkit.
"""
import sys
import types


def install_stub():
    if "openeye" in sys.modules and getattr(sys.modules["openeye"], "_is_stub", False):
        return
    oe = types.ModuleType("openeye")
    oechem = types.ModuleType("openeye.oechem")

    class OEMol:
        pass

    class OEGraphMol(OEMol):
        pass

    oechem.OEMol = OEMol
    oechem.OEGraphMol = OEGraphMol
    oechem.OEChemIsLicensed = lambda *a, **k: True
    oechem.OEGetRelease = lambda: "stub-0.0"
    oe.oechem = oechem
    oe._is_stub = True
    sys.modules["openeye"] = oe
    sys.modules["openeye.oechem"] = oechem
