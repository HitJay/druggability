#!/usr/bin/env python3
"""
Build an interactive docking pose gallery HTML for the top 10 GRB10 SH2
candidates.  Generates:
  - 2D structure SVGs (inline, via RDKit)
  - 3D NGL Viewer (CDN) with receptor + docked ligand pose embedded inline
  - A tabbed/card UI to browse all 10 compounds
"""
import json, os, re, string

from rdkit import Chem
from rdkit.Chem import Draw, AllChem

# -- Top 10 candidates (ordered by Boltz prob descending) --------------------
TOP10 = [
    dict(name="FUNOBACTAM",    chembl="CHEMBL5095101", vina=-7.002, boltz=0.659,
         tier="tier1",  phase="--",    le=0.224, mw=438, clogp=-0.91),
    dict(name="FUNAPIDE",      chembl="CHEMBL3707218", vina=-7.391, boltz=0.460,
         tier="elite",  phase="Ph2",  le=0.238, mw=429, clogp=4.25),
    dict(name="GLISINDAMIDE",  chembl="CHEMBL2106689", vina=-7.209, boltz=0.344,
         tier="tier1",  phase="Ph2",  le=0.240, mw=383, clogp=2.63),
    dict(name="TIVANTINIB",    chembl="CHEMBL2103882", vina=-7.426, boltz=0.334,
         tier="elite",  phase="Ph3",  le=0.265, mw=369, clogp=3.59),
    dict(name="TALNIFLUMATE",  chembl="CHEMBL1081506", vina=-7.715, boltz=0.305,
         tier="elite",  phase="Ph2",  le=0.257, mw=414, clogp=4.87),
    dict(name="FDL169",        chembl="CHEMBL5095180", vina=-7.113, boltz=0.304,
         tier="tier1",  phase="--",    le=0.215, mw=492, clogp=5.15),
    dict(name="CRAVACITINIB",  chembl="CHEMBL4596392", vina=-7.166, boltz=0.290,
         tier="elite",  phase="Ph4",  le=0.231, mw=422, clogp=1.73),
    dict(name="OCINAPLON",     chembl="CHEMBL2105199", vina=-7.230, boltz=0.288,
         tier="elite",  phase="Ph2",  le=0.314, mw=301, clogp=2.42),
    dict(name="MAVACOXIB",     chembl="CHEMBL28527",   vina=-7.091, boltz=0.275,
         tier="elite",  phase="Ph2",  le=0.273, mw=385, clogp=3.34),
    dict(name="CELECOXIB",     chembl="CHEMBL118",     vina=-7.149, boltz=0.272,
         tier="elite",  phase="Ph4",  le=0.275, mw=381, clogp=3.51),
]

RUN_DIR = "/das/user/QYJI/druggability/output/2026-06-30/grb10_screening_expanded_chembl/vina_full/runs"
OUTPUT_HTML = "/das/user/QYJI/druggability/output/2026-06-30/grb10_screening_expanded_chembl/vina_full/grb10_docking_gallery.html"


def generate_2d_svg(mol, size=(300, 225)):
    """Return inline SVG string of the molecule's 2D structure."""
    try:
        AllChem.Compute2DCoords(mol)
    except Exception:
        pass
    d2d = Draw.MolDraw2DSVG(size[0], size[1])
    d2d.DrawMolecule(mol)
    d2d.FinishDrawing()
    svg = d2d.GetDrawingText()
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    return svg.strip()


def extract_ligand_sdf(run_path):
    sdf_file = os.path.join(run_path, "PDB1___STI_vina_out.sdf")
    if not os.path.exists(sdf_file):
        return ""
    with open(sdf_file) as f:
        text = f.read()
    blocks = text.split("$$$$\n")
    if not blocks or not blocks[0].strip():
        return ""
    return blocks[0].strip() + "\n$$$$\n"


def extract_receptor_pdb(run_path):
    pdb_file = os.path.join(run_path, "PDB1___receptor.pdb")
    if not os.path.exists(pdb_file):
        return ""
    with open(pdb_file) as f:
        return f.read()


def get_2d_smiles(run_path):
    sdf_file = os.path.join(run_path, "PDB1___STI_vina_out.sdf")
    if os.path.exists(sdf_file):
        supp = Chem.SDMolSupplier(sdf_file)
        for mol in supp:
            if mol:
                return Chem.MolToSmiles(mol)
    return ""


# -- Helper: read template ------------------------------------------------
def read_template(path):
    with open(path) as f:
        return f.read()


# -- Build cards HTML -----------------------------------------------------
cards_html_parts = []
js_data_parts = []

for idx, cpd in enumerate(TOP10):
    run_path = os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]))
    if not os.path.isdir(run_path):
        print("  !! Run dir not found: %s" % run_path)
        continue

    smiles = get_2d_smiles(run_path)
    svg_data = ""
    if smiles:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            try:
                svg_data = generate_2d_svg(mol)
            except Exception as e:
                print("  !! SVG failed for %s: %s" % (cpd["name"], e))

    lig_sdf = extract_ligand_sdf(run_path)
    rec_pdb = extract_receptor_pdb(run_path)

    lig_js = json.dumps(lig_sdf)
    rec_js = json.dumps(rec_pdb)

    badge_cls = "elite" if cpd["tier"] == "elite" else "tier1"
    phase_clean = cpd["phase"]
    if phase_clean == "--":
        phase_badge = '<span class="badge ph1">--</span>'
    else:
        phase_num = phase_clean.replace("Ph", "").lower()
        phase_badge = '<span class="badge ph%s">%s</span>' % (phase_num, phase_clean)

    card = """
<div class="cpd-card" data-idx="%d">
  <div class="cpd-header">
    <h3>%s</h3>
    <span class="badge %s">%s</span>
    %s
    <span class="rank">#%d</span>
  </div>
  <div class="cpd-body">
    <div class="cpd-2d">%s</div>
    <div class="cpd-meta">
      <div class="stat-row"><span class="stat-label">Vina</span><span class="stat-val">%.3f</span></div>
      <div class="stat-row"><span class="stat-label">Boltz</span><span class="stat-val hboltz">%.3f</span></div>
      <div class="stat-row"><span class="stat-label">LE</span><span class="stat-val">%.3f</span></div>
      <div class="stat-row"><span class="stat-label">MW</span><span class="stat-val">%d</span></div>
      <div class="stat-row"><span class="stat-label">clogP</span><span class="stat-val">%.2f</span></div>
      <div class="stat-row"><span class="stat-label">CHEMBL</span><span class="stat-val cid"><code>%s</code></span></div>
    </div>
  </div>
  <div class="cpd-footer">
    <button class="view3d-btn" data-idx="%d">&#x1f52c; 3D Pose</button>
  </div>
</div>""" % (idx, cpd["name"], badge_cls, cpd["tier"], phase_badge,
             idx+1, svg_data,
             cpd["vina"], cpd["boltz"], cpd["le"], cpd["mw"], cpd["clogp"],
             cpd["chembl"], idx)

    cards_html_parts.append(card)

    js_data_parts.append("""
const lig_%d = %s;
const rec_%d = %s;
const name_%d = "%s";
const vina_%d = %f;
const boltz_%d = %f;
const chembl_%d = "%s";
""" % (idx, lig_js, idx, rec_js, idx, cpd["name"],
       idx, cpd["vina"], idx, cpd["boltz"], idx, cpd["chembl"]))

    print("  ok %-20s  2D+3D data prepared" % cpd["name"])

cards_html = "\n".join(cards_html_parts)
js_data = "\n".join(js_data_parts)

# -- Template with $cards and $jsdata placeholders -- uses string.Template
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>GRB10 SH2 — Top 10 Docking Pose Gallery</title>
<script src="https://cdn.jsdelivr.net/npm/ngl@2.5.0/dist/ngl.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0e17;color:#e2e8f0;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:24px 32px}
.header{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);border-bottom:1px solid #1e3a5f;padding:28px 0}
.header h1{font-size:24px;font-weight:700;color:#f1f5f9}
.header .subtitle{font-size:13px;color:#94a3b8;margin-top:4px}
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:20px;margin:24px 0}
.cpd-card{background:#131b2f;border:1px solid #1e293b;border-radius:12px;overflow:hidden;transition:border-color .2s}
.cpd-card:hover{border-color:#38bdf855}
.cpd-header{display:flex;align-items:center;gap:8px;padding:14px 16px 8px;background:#1a2236;border-bottom:1px solid #243048}
.cpd-header h3{font-size:15px;font-weight:600;color:#f1f5f9;flex:1}
.cpd-header .rank{font-size:12px;color:#64748b;font-weight:500}
.cpd-body{display:flex;gap:16px;padding:16px}
.cpd-2d{width:180px;min-width:180px;background:#0f172a;border-radius:8px;display:flex;align-items:center;justify-content:center;padding:8px}
.cpd-2d svg{width:100%;height:auto}
.cpd-meta{flex:1;display:flex;flex-direction:column;gap:3px;justify-content:center}
.stat-row{display:flex;justify-content:space-between;padding:4px 8px;background:#0f172a;border-radius:4px;font-size:12px}
.stat-label{color:#64748b;font-weight:500}
.stat-val{color:#e2e8f0;font-variant-numeric:tabular-nums}
.stat-val.hboltz{color:#4ade80;font-weight:600}
.stat-row .cid code{color:#94a3b8;font-size:10px}
.cpd-footer{padding:8px 16px 12px;display:flex;justify-content:center}
.view3d-btn{background:#1e3a5f;border:1px solid #38bdf855;color:#38bdf8;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:500;transition:all .2s;width:100%}
.view3d-btn:hover{background:#1e3a5f;border-color:#38bdf8;color:#7dd3fc}
.modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:#000000cc;z-index:1000;display:none;align-items:center;justify-content:center}
.modal-overlay.active{display:flex}
.modal-content{background:#131b2f;border:1px solid #1e293b;border-radius:12px;width:90vw;height:90vh;max-width:1200px;display:flex;flex-direction:column;overflow:hidden}
.modal-header{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid #243048;background:#1a2236}
.modal-header h2{font-size:16px;font-weight:600;color:#f1f5f9}
.modal-close{background:none;border:none;color:#94a3b8;font-size:22px;cursor:pointer;padding:4px 8px;border-radius:4px}
.modal-close:hover{color:#f1f5f9;background:#243048}
.modal-viewer{flex:1;position:relative}
.modal-viewer .ngl-container{width:100%;height:100%}
.modal-info{padding:12px 20px;border-top:1px solid #243048;background:#1a2236;display:flex;gap:20px;font-size:12px;color:#94a3b8}
.section-title{font-size:18px;font-weight:600;color:#f1f5f9;margin:32px 0 16px;padding-bottom:8px;border-bottom:1px solid #1e293b}
@media(max-width:800px){.cards-grid{grid-template-columns:1fr}.cpd-body{flex-direction:column}.cpd-2d{width:100%;min-width:auto}}
</style>
</head>
<body>

<div class="header"><div class="container">
<h1>GRB10 SH2 — Top 10 Docking Pose Gallery</h1>
<div class="subtitle">Interactive 3D viewing of the best-ranked docked poses from 8490-compound ChEMBL screen</div>
</div></div>

<div class="container">

<div class="section-title">Top 10 Candidates <span style="font-size:13px;color:#64748b;font-weight:400">— sorted by Boltz-2 affinity probability</span></div>

<div class="cards-grid" id="cardsGrid">
$cards
</div>

<p style="color:#64748b;font-size:12px;margin-top:16px;text-align:center">
Click <strong>"🔬 3D Pose"</strong> on any card to view the docked binding pose in interactive 3D.<br>
Use mouse to rotate, scroll to zoom, right-click drag to pan.
</p>

</div>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal-content">
    <div class="modal-header">
      <h2 id="modalTitle">Compound Name</h2>
      <button class="modal-close" id="modalClose">&times;</button>
    </div>
    <div class="modal-viewer" id="modalViewer">
      <div id="nglStage" class="ngl-container"></div>
    </div>
    <div class="modal-info">
      <span id="modalScores">Vina: -- | Boltz: --</span>
      <span id="modalChembl">CHEMBL: --</span>
      <span style="flex:1"></span>
      <span>Rotate: left-drag  |  Zoom: scroll  |  Pan: right-drag</span>
    </div>
  </div>
</div>

<script>
$jsdata

var currentStage = null;

function openViewer(idx) {{
  var overlay = document.getElementById('modalOverlay');
  document.getElementById('modalTitle').textContent = window['name_' + idx];
  document.getElementById('modalScores').textContent =
    'Vina: ' + window['vina_' + idx].toFixed(3) + '  |  Boltz: ' + window['boltz_' + idx].toFixed(3);
  document.getElementById('modalChembl').textContent =
    'CHEMBL: ' + window['chembl_' + idx];
  overlay.classList.add('active');

  var container = document.getElementById('nglStage');
  container.innerHTML = '';
  if (currentStage) {{ try {{ currentStage.dispose(); }} catch(e) {{ }} currentStage = null; }}

  setTimeout(function() {{
    var stage = new NGL.Stage(container, {{ backgroundColor: '#0a0e17' }});
    currentStage = stage;
    stage.viewer.setRock(false);
    stage.setParameters({{ clipNear: 0, clipFar: 100 }});

    var recBlob = new Blob([window['rec_' + idx]], {{ type: 'text/plain' }});
    stage.loadFile(recBlob, {{ ext: 'pdb', name: 'Receptor' }}).then(function(comp) {{
      comp.addRepresentation('cartoon', {{ color: 'residueindex', scale: 1.0 }});
      comp.addRepresentation('surface', {{ opacity: 0.25, color: 'white', side: 'front' }});
      comp.autoView();
    }});

    var ligBlob = new Blob([window['lig_' + idx]], {{ type: 'text/plain' }});
    stage.loadFile(ligBlob, {{ ext: 'sdf', name: 'Ligand' }}).then(function(comp) {{
      comp.addRepresentation('ball+stick', {{
        color: 'element', radiusScale: 0.8,
        multipleBond: true, bondScale: 1.0
      }});
      comp.autoView();
    }});
  }}, 100);
}}

document.querySelectorAll('.view3d-btn').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    openViewer(parseInt(this.dataset.idx));
  }});
}});

document.getElementById('modalClose').addEventListener('click', function() {{
  document.getElementById('modalOverlay').classList.remove('active');
  if (currentStage) {{ try {{ currentStage.dispose(); }} catch(e) {{ }} currentStage = null; }}
}});

document.getElementById('modalOverlay').addEventListener('click', function(e) {{
  if (e.target === this) {{
    document.getElementById('modalOverlay').classList.remove('active');
    if (currentStage) {{ try {{ currentStage.dispose(); }} catch(e) {{ }} currentStage = null; }}
  }}
}});

document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') {{
    document.getElementById('modalOverlay').classList.remove('active');
    if (currentStage) {{ try {{ currentStage.dispose(); }} catch(e) {{ }} currentStage = null; }}
  }}
}});
</script>
</body>
</html>
"""

tmpl = string.Template(TEMPLATE)
html = tmpl.substitute(cards=cards_html, jsdata=js_data)

with open(OUTPUT_HTML, 'w') as f:
    f.write(html)

total_dirs = sum(1 for cpd in TOP10 if os.path.isdir(
    os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]))))
total_rec = sum(1 for cpd in TOP10 if os.path.isfile(
    os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]), "PDB1___receptor.pdb")))
total_lig = sum(1 for cpd in TOP10 if os.path.isfile(
    os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]), "PDB1___STI_vina_out.sdf")))

size_kb = os.path.getsize(OUTPUT_HTML) / 1024
print("")
print("=" * 60)
print("Output: %s" % OUTPUT_HTML)
print("Size:   %.0f KB" % size_kb)
print("Cards:  %d/10 SVGs generated" % total_dirs)
print("3D:     %d/10 receptor PDBs + %d/10 ligand SDFs embedded" % (total_rec, total_lig))
print("=" * 60)
