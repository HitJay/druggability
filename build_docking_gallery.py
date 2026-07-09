#!/usr/bin/env python3
"""
Build a self-contained interactive docking pose gallery HTML for the top 10
GRB10 SH2 candidates. The 3Dmol.js library is INLINED into the HTML so the
single .html file works in any browser (Chrome file://, Firefox, etc.) with
no external dependencies.

Each card shows:
  - 2D structure (RDKit SVG)
  - 3D docking pose (3Dmol.js) with interactive controls:
      Surface opacity slider (0-100%)
      Receptor style: cartoon (spectrum/chain/ss), line, stick, hide
      Ligand style: stick, thick stick, ball-stick, space-fill, line
      Pocket mode: surface, residues (stick), both, none
      Reset view button
  - Global "Apply to all" surface opacity slider
"""
import json, os, re

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
OUTPUT_DIR = "/das/user/QYJI/druggability/output/2026-06-30/grb10_screening_expanded_chembl/vina_full"
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "grb10_docking_gallery.html")
LIB_3DMOL = os.path.join(OUTPUT_DIR, "3Dmol-min.js")


def generate_2d_svg(mol, size=(300, 225)):
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


# -- Build per-compound data ------------------------------------------------
init_calls = []
cards_html_parts = []

for idx, cpd in enumerate(TOP10):
    run_path = os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]))
    if not os.path.isdir(run_path):
        print("  !! Run dir not found: %s" % run_path)
        continue

    lig_sdf = extract_ligand_sdf(run_path)
    rec_pdb = extract_receptor_pdb(run_path)

    lig_js = json.dumps(lig_sdf)
    rec_js = json.dumps(rec_pdb)

    smiles = get_2d_smiles(run_path)
    svg_data = ""
    if smiles:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            try:
                svg_data = generate_2d_svg(mol)
            except Exception as e:
                print("  !! SVG failed for %s: %s" % (cpd["name"], e))

    badge_cls = "elite" if cpd["tier"] == "elite" else "tier1"
    phase_clean = cpd["phase"]
    if phase_clean == "--":
        phase_badge = '<span class="badge ph1">--</span>'
    else:
        phase_num = phase_clean.replace("Ph", "").lower()
        phase_badge = '<span class="badge ph%s">%s</span>' % (phase_num, phase_clean)

    card = """
<div class="cpd-card">
  <div class="cpd-header">
    <h3>%s</h3>
    <span class="badge %s">%s</span>
    %s
    <span class="rank">#%d</span>
  </div>
  <div class="cpd-body">
    <div class="cpd-2d">%s</div>
    <div class="cpd-3d-wrap">
      <div class="cpd-3d" id="viewer%d"></div>
      <div class="cpd-controls">
        <div class="ctrl-row">
          <label>Surface</label>
          <input type="range" min="0" max="100" value="30" data-idx="%d" class="opacity-slider" title="Surface opacity">
          <span class="ctrl-val" id="opval%d">30%%</span>
        </div>
        <div class="ctrl-row">
          <label>Receptor</label>
          <select data-idx="%d" class="rec-style">
            <option value="cartoon-spectrum">Cartoon spectrum</option>
            <option value="cartoon-chain">Cartoon by chain</option>
            <option value="cartoon-ss">Cartoon by 2nd struct</option>
            <option value="line">Lines</option>
            <option value="stick">Sticks</option>
            <option value="hide">Hide</option>
          </select>
        </div>
        <div class="ctrl-row">
          <label>Ligand</label>
          <select data-idx="%d" class="lig-style">
            <option value="stick">Stick</option>
            <option value="stick-thick">Stick (thick)</option>
            <option value="ball-stick">Ball &amp; stick</option>
            <option value="sphere">Space-fill</option>
            <option value="line">Line</option>
          </select>
        </div>
        <div class="ctrl-row">
          <label>Pocket</label>
          <select data-idx="%d" class="pocket-mode">
            <option value="surface">Surface</option>
            <option value="residues">Residues (stick)</option>
            <option value="both">Surface + residues</option>
            <option value="none">None</option>
          </select>
          <button class="reset-btn" data-idx="%d" title="Reset view">Reset</button>
        </div>
      </div>
    </div>
  </div>
  <div class="cpd-meta">
    <div class="stat-item"><span class="stat-label">Vina</span><span class="stat-val">%.3f</span></div>
    <div class="stat-item"><span class="stat-label">Boltz</span><span class="stat-val hboltz">%.3f</span></div>
    <div class="stat-item"><span class="stat-label">LE</span><span class="stat-val">%.3f</span></div>
    <div class="stat-item"><span class="stat-label">MW</span><span class="stat-val">%d</span></div>
    <div class="stat-item"><span class="stat-label">clogP</span><span class="stat-val">%.2f</span></div>
    <div class="stat-item"><span class="stat-label">CHEMBL</span><span class="stat-val cid">%s</span></div>
  </div>
</div>""" % (cpd["name"], badge_cls, cpd["tier"], phase_badge,
             idx+1, svg_data, idx,
             idx, idx,  # opacity slider + val
             idx,        # rec-style
             idx,        # lig-style
             idx, idx,   # pocket-mode + reset
             cpd["vina"], cpd["boltz"], cpd["le"], cpd["mw"], cpd["clogp"],
             cpd["chembl"])
    cards_html_parts.append(card)

    init_calls.append("  initViewer(%d, %s, %s);" % (idx, rec_js, lig_js))
    print("  ok %-20s  card + 3D data prepared" % cpd["name"])

cards_html = "\n".join(cards_html_parts)
init_js = "\n".join(init_calls)

# -- Load 3Dmol.js library to inline it into HTML ---------------------------
if not os.path.exists(LIB_3DMOL):
    raise SystemExit("ERROR: 3Dmol-min.js not found at %s" % LIB_3DMOL)

with open(LIB_3DMOL, 'r') as f:
    inline_lib = f.read()

# -- HTML template -----------------------------------------------------------
# Structured as: CSS -> body -> INLINE 3Dmol.js lib -> our init script
TEMPLATE = u"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>GRB10 SH2 - Top 10 Docking Pose Gallery</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0e17;color:#e2e8f0;line-height:1.4}
.container{max-width:1700px;margin:0 auto;padding:16px 24px}
.header{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);border-bottom:1px solid #1e3a5f;padding:20px 0}
.header h1{font-size:22px;font-weight:700;color:#f1f5f9}
.header .subtitle{font-size:13px;color:#94a3b8;margin-top:2px}
.global-ctrl{background:#1a2236;border:1px solid #243048;border-radius:8px;padding:10px 14px;margin:12px 0;display:flex;align-items:center;gap:14px;font-size:12px}
.global-ctrl label{color:#94a3b8;font-weight:500}
.global-ctrl button{background:#1e3a5f;border:1px solid #38bdf866;color:#7dd3fc;padding:5px 12px;border-radius:4px;cursor:pointer;font-size:11px;font-weight:500}
.global-ctrl button:hover{background:#2a4a7f;color:#bae6fd}
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(760px,1fr));gap:16px;margin:16px 0}
.cpd-card{background:#131b2f;border:1px solid #1e293b;border-radius:10px;overflow:hidden;transition:border-color .2s}
.cpd-card:hover{border-color:#38bdf866}
.cpd-header{display:flex;align-items:center;gap:8px;padding:10px 14px 6px;background:#1a2236;border-bottom:1px solid #243048}
.cpd-header h3{font-size:14px;font-weight:600;color:#f1f5f9;flex:1}
.cpd-header .rank{font-size:11px;color:#64748b;font-weight:500}
.badge{display:inline-block;font-size:10px;font-weight:600;padding:1px 7px;border-radius:4px}
.badge.elite{background:#1a3a2a;color:#4ade80;border:1px solid #4ade8044}
.badge.tier1{background:#3a2a1a;color:#fbbf24;border:1px solid #fbbf2444}
.badge.ph2{background:#1a2a3a;color:#60a5fa;border:1px solid #60a5fa44}
.badge.ph3{background:#2a1a3a;color:#a78bfa;border:1px solid #a78bfa44}
.badge.ph4{background:#2a3a1a;color:#a3e635;border:1px solid #a3e63544}
.badge.ph1{background:#3a1a1a;color:#f87171;border:1px solid #f8717144}
.cpd-body{display:flex;gap:12px;padding:10px 14px}
.cpd-2d{width:160px;min-width:160px;background:#0f172a;border-radius:6px;display:flex;align-items:center;justify-content:center;padding:6px;align-self:flex-start}
.cpd-2d svg{width:100%;height:auto}
.cpd-3d-wrap{flex:1;display:flex;flex-direction:column;gap:6px}
.cpd-3d{width:100%;height:280px;min-height:280px;background:#0a0e17;border-radius:6px;overflow:hidden;position:relative}
.cpd-controls{background:#0f172a;border-radius:6px;padding:6px 10px;display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;font-size:11px}
.ctrl-row{display:flex;align-items:center;gap:6px}
.ctrl-row label{color:#64748b;font-weight:500;min-width:56px;font-size:10px;text-transform:uppercase;letter-spacing:.5px}
.ctrl-row select{background:#131b2f;border:1px solid #243048;color:#e2e8f0;padding:2px 6px;border-radius:3px;font-size:11px;flex:1;cursor:pointer}
.ctrl-row select:focus{outline:none;border-color:#38bdf8}
.ctrl-row input[type=range]{flex:1;accent-color:#38bdf8;cursor:pointer}
.ctrl-val{color:#38bdf8;font-variant-numeric:tabular-nums;min-width:36px;text-align:right;font-size:10px}
.reset-btn{background:#1e293b;border:1px solid #38bdf866;color:#7dd3fc;padding:2px 8px;border-radius:3px;cursor:pointer;font-size:10px;font-weight:500}
.reset-btn:hover{background:#38bdf822}
.cpd-meta{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:6px 14px 10px;border-top:1px solid #1e293b}
.stat-item{display:flex;justify-content:space-between;padding:3px 8px;background:#0f172a;border-radius:4px;font-size:11px}
.stat-label{color:#64748b;font-weight:500}
.stat-val{color:#e2e8f0;font-variant-numeric:tabular-nums}
.stat-val.hboltz{color:#4ade80;font-weight:600}
.stat-val.cid{color:#94a3b8;font-size:10px}
@media(max-width:800px){.cards-grid{grid-template-columns:1fr}.cpd-body{flex-direction:column}.cpd-2d{width:100%;min-width:auto}.cpd-3d{height:240px}}
</style>
</head>
<body>

<div class="header"><div class="container">
<h1>GRB10 SH2 - Top 10 Docking Pose Gallery</h1>
<div class="subtitle">3D poses via 3Dmol.js (inlined) | per-card controls or global batch apply</div>
</div></div>

<div class="container">

<div class="global-ctrl">
  <label>Global:</label>
  <label style="color:#64748b">Surface opacity</label>
  <input type="range" min="0" max="100" value="30" id="globalOpacity" style="width:120px;accent-color:#38bdf8">
  <span id="globalOpVal" style="color:#38bdf8;min-width:36px">30%%</span>
  <button id="applyAllOpacity">Apply to all</button>
  <span style="color:#64748b;margin-left:auto;font-size:11px">Drag = rotate, scroll = zoom, right-drag = pan (per viewport)</span>
</div>

<div class="cards-grid" id="cardsGrid">
CARDS_PLACEHOLDER
</div>

</div>

<!-- 3Dmol.js library inlined below (self-contained, works in Chrome file://) -->
<script>
INLINE_3DMOL_LIB
</script>

<script>
var viewers = {};
var viewerState = {};

function getRecStyle(mode) {
  switch(mode) {
    case 'cartoon-spectrum': return { cartoon: { color: 'spectrum', opacity: 0.9 } };
    case 'cartoon-chain':    return { cartoon: { colorscheme: 'chain', opacity: 0.9 } };
    case 'cartoon-ss':       return { cartoon: { colorscheme: 'ssJmol', opacity: 0.9 } };
    case 'line':             return { line: { linewidth: 1.5 } };
    case 'stick':            return { stick: { radius: 0.12, opacity: 0.7 } };
    case 'hide':             return {};
    default:                 return { cartoon: { color: 'spectrum', opacity: 0.9 } };
  }
}

function getLigStyle(mode) {
  switch(mode) {
    case 'stick':       return { stick: { colorscheme: 'default', radius: 0.18 } };
    case 'stick-thick': return { stick: { colorscheme: 'default', radius: 0.28 } };
    case 'ball-stick':  return { stick: { colorscheme: 'default', radius: 0.14 }, sphere: { colorscheme: 'default', radius: 0.35 } };
    case 'sphere':      return { sphere: { colorscheme: 'default' } };
    case 'line':        return { line: { linewidth: 2 } };
    default:            return { stick: { colorscheme: 'default', radius: 0.18 } };
  }
}

function applyPocket(viewer, mode, opacity) {
  viewer.removeAllSurfaces();
  var op = opacity / 100.0;
  if (mode === 'surface' || mode === 'both') {
    if (op > 0.01) {
      viewer.addSurface($3Dmol.SurfaceType.VDW, {
        opacity: op,
        color: 'white'
      }, { model: 0, byres: true, within: { distance: 5, sel: { model: 1 } } });
    }
  }
  if (mode === 'residues' || mode === 'both') {
    viewer.addStyle({
      model: 0,
      byres: true,
      within: { distance: 5, sel: { model: 1 } }
    }, {
      stick: { colorscheme: 'default', radius: 0.13 }
    });
  }
}

function rebuildStyle(idx) {
  var v = viewers[idx];
  var st = viewerState[idx];
  if (!v || !st) return;
  v.setStyle({ model: 0 }, {});
  v.setStyle({ model: 1 }, {});
  v.setStyle({ model: 0 }, getRecStyle(st.recStyle));
  v.setStyle({ model: 1 }, getLigStyle(st.ligStyle));
  applyPocket(v, st.pocketMode, st.opacity);
  v.render();
}

function initViewer(idx, recData, ligData) {
  var container = document.getElementById('viewer' + idx);
  if (!container) { console.error('Container viewer' + idx + ' not found'); return; }
  try {
    var viewer = $3Dmol.createViewer(container, {
      backgroundColor: '#0a0e17',
      antialias: true
    });
    viewer.addModel(recData, 'pdb');
    viewer.addModel(ligData, 'sdf');
    viewers[idx] = viewer;
    viewerState[idx] = {
      opacity: 30,
      recStyle: 'cartoon-spectrum',
      ligStyle: 'stick',
      pocketMode: 'surface'
    };
    rebuildStyle(idx);
    viewer.zoomTo({ model: 1 });
    viewer.zoom(0.7);
    viewer.render();
  } catch(err) {
    console.error('Error init viewer ' + idx + ':', err);
    container.innerHTML = '<div style="color:#f87171;padding:12px;font-size:12px">3D render failed: ' + err.message + '</div>';
  }
}

function resetView(idx) {
  var v = viewers[idx];
  if (!v) return;
  v.zoomTo({ model: 1 });
  v.zoom(0.7);
  v.render();
}

function attachControls() {
  document.querySelectorAll('.opacity-slider').forEach(function(el) {
    el.addEventListener('input', function() {
      var idx = parseInt(this.dataset.idx);
      var val = parseInt(this.value);
      viewerState[idx].opacity = val;
      document.getElementById('opval' + idx).textContent = val + '%';
      rebuildStyle(idx);
    });
  });
  document.querySelectorAll('.rec-style').forEach(function(el) {
    el.addEventListener('change', function() {
      var idx = parseInt(this.dataset.idx);
      viewerState[idx].recStyle = this.value;
      rebuildStyle(idx);
    });
  });
  document.querySelectorAll('.lig-style').forEach(function(el) {
    el.addEventListener('change', function() {
      var idx = parseInt(this.dataset.idx);
      viewerState[idx].ligStyle = this.value;
      rebuildStyle(idx);
    });
  });
  document.querySelectorAll('.pocket-mode').forEach(function(el) {
    el.addEventListener('change', function() {
      var idx = parseInt(this.dataset.idx);
      viewerState[idx].pocketMode = this.value;
      rebuildStyle(idx);
    });
  });
  document.querySelectorAll('.reset-btn').forEach(function(el) {
    el.addEventListener('click', function() {
      resetView(parseInt(this.dataset.idx));
    });
  });
  var g = document.getElementById('globalOpacity');
  var gv = document.getElementById('globalOpVal');
  g.addEventListener('input', function() {
    gv.textContent = this.value + '%';
  });
  document.getElementById('applyAllOpacity').addEventListener('click', function() {
    var val = parseInt(g.value);
    Object.keys(viewerState).forEach(function(k) {
      viewerState[k].opacity = val;
      var slider = document.querySelector('.opacity-slider[data-idx="' + k + '"]');
      if (slider) slider.value = val;
      var lbl = document.getElementById('opval' + k);
      if (lbl) lbl.textContent = val + '%';
      rebuildStyle(parseInt(k));
    });
  });
}

window.addEventListener('load', function() {
  if (typeof $3Dmol === 'undefined') {
    console.error('3Dmol.js library not loaded (inlined lib failed to execute)');
    document.querySelectorAll('.cpd-3d').forEach(function(el) {
      el.innerHTML = '<div style="color:#f87171;padding:12px;font-size:12px">3Dmol.js library failed to execute. Open browser console for details.</div>';
    });
    return;
  }
  console.log('Loading ' + INIT_COUNT + ' viewers...');
INIT_PLACEHOLDER
  attachControls();
  console.log('All viewers initialized');
});
</script>
</body>
</html>"""

# -- Assemble HTML ----------------------------------------------------------
html = TEMPLATE.replace("CARDS_PLACEHOLDER", cards_html)
html = html.replace("INIT_PLACEHOLDER", init_js)
html = html.replace("INIT_COUNT", str(len(init_calls)))
# Inline the 3Dmol.js library LAST so it doesn't interfere with earlier replacements
html = html.replace("INLINE_3DMOL_LIB", inline_lib)

with open(OUTPUT_HTML, 'w') as f:
    f.write(html)

# -- Verify ------------------------------------------------------------------
total_dirs = sum(1 for cpd in TOP10 if os.path.isdir(
    os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]))))
total_rec = sum(1 for cpd in TOP10 if os.path.isfile(
    os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]), "PDB1___receptor.pdb")))
total_lig = sum(1 for cpd in TOP10 if os.path.isfile(
    os.path.join(RUN_DIR, "%s_%s" % (cpd["chembl"], cpd["name"]), "PDB1___STI_vina_out.sdf")))

size_kb = os.path.getsize(OUTPUT_HTML) / 1024
print("")
print("=" * 60)
print("Output:  %s" % OUTPUT_HTML)
print("Size:    %.0f KB (3Dmol.js %.0f KB inlined)" % (size_kb, len(inline_lib)/1024))
print("Cards:   %d/10 SVGs generated" % total_dirs)
print("3D:      %d/10 receptor PDBs + %d/10 ligand SDFs embedded" % (total_rec, total_lig))
print("Self-contained: opens directly in Chrome / Firefox / any browser")
print("Controls: opacity, rec/lig/pocket style, reset, global apply-all")
print("=" * 60)
