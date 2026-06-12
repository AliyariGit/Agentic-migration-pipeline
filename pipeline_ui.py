"""
pipeline_ui.py — Web dashboard for the Agentic Migration Pipeline
Usage: python pipeline_ui.py
Then open: http://localhost:8080
"""

import http.server
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE_DIR = Path(__file__).parent
HTML_FILE = BASE_DIR / 'pipeline_ui.html'

_pipeline_log = []
_pipeline_running = False
_log_lock = threading.Lock()

# ─────────────────────────────────────────────────────────────────────────────
# HTML PAGE (loaded from pipeline_ui.html)
# ─────────────────────────────────────────────────────────────────────────────

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentic Migration Pipeline</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#e6edf3;height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* ── Header ── */
.header{background:#161b22;border-bottom:1px solid #30363d;padding:10px 20px;display:flex;align-items:center;gap:14px;flex-shrink:0}
.logo{font-size:15px;font-weight:700;color:#58a6ff;letter-spacing:-.3px}
.subtitle{font-size:12px;color:#8b949e;margin-top:1px}
.spacer{flex:1}
.btn{padding:6px 16px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:filter .15s}
.btn:hover{filter:brightness(1.15)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-run{background:#238636;color:#fff}
.btn-demo{background:#7b44d4;color:#fff;margin-left:6px}

/* ── Progress bar ── */
.progress-bar{background:#161b22;border-bottom:1px solid #30363d;padding:10px 20px;display:flex;align-items:center;gap:0;flex-shrink:0}
.prog-step{display:flex;align-items:center;flex:1}
.prog-node{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;transition:all .3s}
.prog-node.idle{background:#21262d;color:#8b949e;border:2px solid #30363d}
.prog-node.active{background:#1f3558;color:#58a6ff;border:2px solid #58a6ff;animation:pulse 1.2s infinite}
.prog-node.done{background:#1a4731;color:#3fb950;border:2px solid #3fb950}
.prog-node.fail{background:#4d1010;color:#f85149;border:2px solid #f85149}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(88,166,255,.4)}50%{box-shadow:0 0 0 5px rgba(88,166,255,0)}}
.prog-label{font-size:11px;color:#8b949e;margin-left:6px;white-space:nowrap}
.prog-line{flex:1;height:2px;background:#30363d;margin:0 6px;border-radius:1px;transition:background .5s}
.prog-line.done{background:#3fb950}

/* ── Layout ── */
.body{display:flex;flex:1;overflow:hidden}

/* ── Sidebar ── */
.sidebar{width:230px;background:#161b22;border-right:1px solid #30363d;display:flex;flex-direction:column;overflow:hidden;flex-shrink:0}
.sidebar-section{display:flex;flex-direction:column;min-height:0}
.sidebar-section.grow{flex:1;overflow:hidden;display:flex;flex-direction:column}
.sec-head{padding:8px 14px 4px;font-size:10px;font-weight:700;color:#8b949e;text-transform:uppercase;letter-spacing:.1em;flex-shrink:0}
.sec-scroll{overflow-y:auto;flex:1}
.sec-divider{height:1px;background:#21262d;margin:0}
.file-row{padding:5px 14px;cursor:pointer;display:flex;align-items:center;gap:6px;font-size:12px;color:#8b949e;border-left:2px solid transparent;transition:all .1s}
.file-row:hover{background:#1c2128;color:#e6edf3}
.file-row.sel{background:#1c2128;border-left-color:#58a6ff;color:#58a6ff}
.file-icon{flex-shrink:0;width:14px;text-align:center}
.file-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.val-row{padding:5px 14px;cursor:pointer;display:flex;align-items:center;gap:6px;font-size:12px;border-left:2px solid transparent}
.val-row:hover{background:#1c2128}
.val-row.pass{color:#3fb950}
.val-row.block{color:#f85149}
.empty-msg{padding:10px 14px;font-size:12px;color:#484f58;font-style:italic}

/* ── Main ── */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.tabs{display:flex;background:#161b22;border-bottom:1px solid #30363d;padding:0 16px;flex-shrink:0}
.tab{padding:8px 14px;font-size:13px;cursor:pointer;border-bottom:2px solid transparent;color:#8b949e;user-select:none}
.tab.on{color:#e6edf3;border-bottom-color:#58a6ff}
.tab:hover:not(.on){color:#c9d1d9}
.panels{flex:1;overflow:hidden;position:relative}
.panel{position:absolute;inset:0;overflow:auto;display:none}
.panel.on{display:block}

/* ── Log panel ── */
.log-body{padding:12px 16px;font-family:'Cascadia Code','Consolas',monospace;font-size:12px}
.ll{line-height:1.75;white-space:pre-wrap;word-break:break-all}
.ll.ok{color:#3fb950}
.ll.err{color:#f85149}
.ll.warn{color:#d29922}
.ll.head{color:#58a6ff;font-weight:600}
.ll.dim{color:#484f58}
.ll.def{color:#c9d1d9}
.idle-msg{color:#484f58;font-size:13px;padding:16px}

/* ── Code panel ── */
.code-topbar{padding:7px 16px;background:#161b22;border-bottom:1px solid #30363d;font-size:12px;color:#58a6ff;display:flex;gap:8px;align-items:center;flex-shrink:0;position:sticky;top:0;z-index:1}
pre{padding:16px 20px;font-family:'Cascadia Code','Consolas',monospace;font-size:12.5px;line-height:1.65;color:#e6edf3;tab-size:4}
.kw{color:#ff7b72}
.ty{color:#79c0ff}
.st{color:#a5d6ff}
.cm{color:#8b949e;font-style:italic}
.at{color:#ffa657}
.mt{color:#d2a8ff}
.nm{color:#79c0ff}
.empty-code{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:8px;color:#484f58}
.empty-icon{font-size:36px}

/* ── Validation panel ── */
.val-body{padding:20px}
.vc{background:#161b22;border:1px solid #30363d;border-radius:8px;margin-bottom:14px;overflow:hidden}
.vc-head{padding:11px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #21262d}
.vc-file{font-weight:600;font-size:13px}
.badge{padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700}
.badge.pass{background:#122d22;color:#3fb950}
.badge.block{background:#3d0e0e;color:#f85149}
.vc-counts{margin-left:auto;font-size:11px;color:#8b949e}
.vi{padding:10px 16px;border-bottom:1px solid #21262d;display:flex;gap:10px}
.vi:last-child{border-bottom:none}
.sev{padding:2px 8px;border-radius:4px;font-size:10px;font-weight:800;white-space:nowrap;align-self:flex-start;margin-top:2px}
.sev.CRITICAL{background:#3d0e0e;color:#f85149}
.sev.HIGH{background:#3d2600;color:#d29922}
.sev.MEDIUM{background:#0e2a25;color:#3fb950}
.vi-text .desc{font-size:13px;color:#e6edf3}
.vi-text .fix{font-size:12px;color:#8b949e;margin-top:3px}
.vi-text .line{font-family:'Cascadia Code','Consolas',monospace;font-size:11px;color:#8b949e;margin-top:4px;background:#0d1117;padding:3px 6px;border-radius:3px}
.val-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px;gap:8px;color:#484f58}

/* ── Status bar ── */
.statusbar{background:#1c2128;border-top:1px solid #30363d;padding:4px 18px;display:flex;gap:22px;font-size:11px;color:#8b949e;flex-shrink:0}
.sb{display:flex;align-items:center;gap:5px}
.sb b{color:#e6edf3}
.sb b.ok{color:#3fb950}
.sb b.err{color:#f85149}
.sb b.act{color:#58a6ff}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="logo">&#9889; Agentic Migration Pipeline</div>
    <div class="subtitle">VBScript &amp; Classic ASP &#8594; .NET Core C#</div>
  </div>
  <div class="spacer"></div>
  <button class="btn btn-run" id="btnRun" onclick="startRun(false)">&#9654; Run Pipeline</button>
  <button class="btn btn-demo" id="btnDemo" onclick="startRun(true)">&#129514; Demo Mode</button>
</div>

<div class="progress-bar" id="progBar"></div>

<div class="body">
  <div class="sidebar">
    <div class="sidebar-section grow">
      <div class="sec-head">Output Files</div>
      <div class="sec-scroll" id="fileList">
        <div class="empty-msg">Run pipeline to generate files</div>
      </div>
    </div>
    <div class="sec-divider"></div>
    <div class="sidebar-section" style="flex-shrink:0;max-height:180px;overflow:hidden;display:flex;flex-direction:column">
      <div class="sec-head">Validation</div>
      <div class="sec-scroll" id="valList">
        <div class="empty-msg">No reports yet</div>
      </div>
    </div>
  </div>

  <div class="main">
    <div class="tabs">
      <div class="tab on" id="tab-log" onclick="showTab('log')">&#128203; Log</div>
      <div class="tab" id="tab-code" onclick="showTab('code')">&#128196; Code</div>
      <div class="tab" id="tab-val" onclick="showTab('val')">&#9989; Validation</div>
    </div>
    <div class="panels">
      <div class="panel on" id="panel-log">
        <div class="log-body" id="logBody">
          <div class="idle-msg">Click &#9654; Run Pipeline or &#129514; Demo Mode to start.</div>
        </div>
      </div>
      <div class="panel" id="panel-code">
        <div id="codeArea" style="height:100%;display:flex;flex-direction:column">
          <div class="empty-code" style="flex:1">
            <div class="empty-icon">&#128196;</div>
            <div>Select a file from the sidebar</div>
          </div>
        </div>
      </div>
      <div class="panel" id="panel-val">
        <div class="val-body" id="valBody">
          <div class="val-empty">
            <div class="empty-icon">&#128269;</div>
            <div>Run the pipeline to see validation results</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="statusbar">
  <div class="sb">Status: <b id="sbStatus" class="act">Ready</b></div>
  <div class="sb">Files: <b id="sbFiles">0</b></div>
  <div class="sb">Passed: <b id="sbPass" class="ok">-</b></div>
  <div class="sb">Blocked: <b id="sbBlock" class="err">-</b></div>
</div>

<script>
const STAGES = [
  {n:1, label:'Decompose', markers:['STAGE 1','[EXTRACTOR]','EXTRACTOR AGENT']},
  {n:2, label:'Context',   markers:['STAGE 2','[ASSEMBLER]','CONTEXT ASSEMBLER']},
  {n:3, label:'Generate',  markers:['STAGE 3','[GENERATOR]','GENERATOR']},
  {n:4, label:'Validate',  markers:['STAGE 4','[VALIDATION','VALIDATION GATE','VALIDATION SUMMARY']},
  {n:5, label:'Recover',   markers:['STAGE 5','[RECOVERY]','RECOVERY AGENT','RECOVERY SUMMARY']},
];

const DONE_MARKERS = [
  'STAGE 1 COMPLETE', 'STAGE 2 COMPLETE', 'STAGE 3 COMPLETE',
  'VALIDATION SUMMARY', 'RECOVERY SUMMARY', 'PIPELINE RUN COMPLETE'
];

let stageState = ['idle','idle','idle','idle','idle'];
let lastLogLen = 0;
let pollTimer = null;
let currentTab = 'log';

// ── Progress bar ────────────────────────────────────────────────────────────
function renderProgress() {
  let html = '';
  STAGES.forEach((s, i) => {
    const st = stageState[i];
    const icon = st==='done'?'&#10003;' : st==='fail'?'&#10007;' : st==='active'?'&#9679;' : s.n;
    html += `<div class="prog-step">
      <div class="prog-node ${st}" title="Stage ${s.n}: ${s.label}">${icon}</div>
      <span class="prog-label">${s.label}</span>
      ${i<4?`<div class="prog-line ${stageState[i]==='done'?'done':''}"></div>`:''}
    </div>`;
  });
  document.getElementById('progBar').innerHTML = html;
}
renderProgress();

// ── Tab switching ────────────────────────────────────────────────────────────
function showTab(t) {
  currentTab = t;
  ['log','code','val'].forEach(id => {
    document.getElementById('tab-'+id).classList.toggle('on', id===t);
    document.getElementById('panel-'+id).classList.toggle('on', id===t);
  });
}

// ── Run pipeline ─────────────────────────────────────────────────────────────
function startRun(demo) {
  ['btnRun','btnDemo'].forEach(id => document.getElementById(id).disabled = true);
  document.getElementById('sbStatus').textContent = demo ? 'Running (demo)…' : 'Running…';
  document.getElementById('sbStatus').className = 'act';
  stageState = ['idle','idle','idle','idle','idle'];
  lastLogLen = 0;
  renderProgress();
  showTab('log');
  document.getElementById('logBody').innerHTML = '';

  fetch('/api/run', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({demo})
  }).then(() => {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(poll, 400);
  });
}

// ── Polling ──────────────────────────────────────────────────────────────────
function poll() {
  fetch('/api/log').then(r=>r.json()).then(data => {
    const newLines = data.log.slice(lastLogLen);
    lastLogLen = data.log.length;

    const body = document.getElementById('logBody');
    newLines.forEach(line => {
      if (!line.trim()) return;
      detectStage(line);
      const div = document.createElement('div');
      div.className = 'll ' + classifyLine(line);
      div.textContent = line;
      body.appendChild(div);
    });
    if (newLines.length) body.scrollTop = body.scrollHeight;

    if (!data.running && data.log.length > 0) {
      clearInterval(pollTimer);
      pollTimer = null;
      // Mark any active stages as done
      stageState = stageState.map(s => s==='active' ? 'done' : s);
      renderProgress();
      document.getElementById('sbStatus').textContent = 'Complete';
      document.getElementById('sbStatus').className = 'ok';
      ['btnRun','btnDemo'].forEach(id => document.getElementById(id).disabled = false);
      loadFiles();
      loadReports();
    }
  });
}

function detectStage(line) {
  const up = line.toUpperCase();
  STAGES.forEach((s, i) => {
    if (s.markers.some(m => up.includes(m.toUpperCase()))) {
      if (stageState[i] === 'idle') {
        // Mark previous stages done
        for (let j = 0; j < i; j++) if (stageState[j]==='active') stageState[j]='done';
        stageState[i] = 'active';
        renderProgress();
      }
    }
  });
  // Detect completions
  if (up.includes('STAGE 1 COMPLETE')) { stageState[0]='done'; renderProgress(); }
  if (up.includes('STAGE 2 COMPLETE')) { stageState[1]='done'; renderProgress(); }
  if (up.includes('STAGE 3 COMPLETE')) { stageState[2]='done'; renderProgress(); }
  if (up.includes('VALIDATION SUMMARY')) { stageState[3]='done'; renderProgress(); }
  if (up.includes('RECOVERY SUMMARY') || up.includes('PIPELINE RUN COMPLETE')) {
    stageState[4]='done'; renderProgress();
  }
}

function classifyLine(line) {
  if (line.includes('COMPLETE') || line.includes('PASSED') || line.includes('✓') || line.includes('✅')) return 'ok';
  if (line.includes('BLOCKED') || line.includes('🚫') || line.includes('❌') || line.includes('CRITICAL') || line.includes('failed')) return 'err';
  if (line.includes('⚠') || line.includes('WARNING') || line.includes('[HIGH]') || line.includes('[MEDIUM]')) return 'warn';
  if (line.includes('===') || line.includes('███') || line.startsWith('  STAGE') || line.includes('[STAGE')) return 'head';
  if (!line.trim() || line.match(/^─+$/)) return 'dim';
  return 'def';
}

// ── File browser ─────────────────────────────────────────────────────────────
function loadFiles() {
  fetch('/api/files').then(r=>r.json()).then(files => {
    document.getElementById('sbFiles').textContent = files.length;
    const el = document.getElementById('fileList');
    if (!files.length) { el.innerHTML = '<div class="empty-msg">No files generated</div>'; return; }
    el.innerHTML = files.map(f => {
      const name = f.split(/[\\/]/).pop();
      const ext = name.split('.').pop();
      const icon = ext==='cs'?'&#128998;' : ext==='cshtml'?'&#127760;' : ext==='json'?'&#128203;' : '&#128196;';
      return `<div class="file-row" onclick="openFile('${f}',this)" title="${f}">
        <span class="file-icon">${icon}</span>
        <span class="file-label">${name}</span>
      </div>`;
    }).join('');
  });
}

function openFile(path, el) {
  document.querySelectorAll('.file-row').forEach(r=>r.classList.remove('sel'));
  el.classList.add('sel');
  fetch('/api/file?path=' + encodeURIComponent(path)).then(r=>r.json()).then(data => {
    const name = path.split(/[\\/]/).pop();
    const ext = name.split('.').pop();
    let code = escHtml(data.content);
    if (ext === 'cs') code = highlightCS(code);
    document.getElementById('codeArea').innerHTML =
      `<div class="code-topbar">&#128196; <span>${path}</span></div>` +
      `<pre style="flex:1;overflow:auto">${code}</pre>`;
    showTab('code');
  });
}

// ── Validation reports ────────────────────────────────────────────────────────
function loadReports() {
  fetch('/api/reports').then(r=>r.json()).then(reports => {
    const passed = reports.filter(r=>r.status==='PASSED').length;
    const blocked = reports.filter(r=>r.status==='BLOCKED').length;
    document.getElementById('sbPass').textContent = passed;
    document.getElementById('sbBlock').textContent = blocked;

    // Sidebar
    const sl = document.getElementById('valList');
    sl.innerHTML = reports.map(r => {
      const cls = r.status==='PASSED' ? 'pass' : 'block';
      const icon = r.status==='PASSED' ? '&#9989;' : '&#128683;';
      const name = (r.file||'').split(/[\\/]/).pop();
      return `<div class="val-row ${cls}" onclick="showTab('val')">${icon} ${name}</div>`;
    }).join('') || '<div class="empty-msg">No reports</div>';

    // Main panel
    const vb = document.getElementById('valBody');
    if (!reports.length) {
      vb.innerHTML = '<div class="val-empty"><div class="empty-icon">&#128269;</div><div>No reports found</div></div>';
      return;
    }
    vb.innerHTML = reports.map(r => {
      const issues = r.issues || [];
      const issueHtml = issues.length === 0
        ? '<div style="padding:10px 16px;color:#3fb950;font-size:13px">&#10003; No issues found</div>'
        : issues.map(i => `
          <div class="vi">
            <span class="sev ${i.severity}">${i.severity}</span>
            <div class="vi-text">
              <div class="desc">${escHtml(i.description)}</div>
              <div class="fix">&#128295; ${escHtml(i.fix_hint)}</div>
              <div class="line">Line ${i.line_number}: ${escHtml(i.line_content)}</div>
            </div>
          </div>`).join('');
      const cnt = r.issue_count || {};
      const name = (r.file||'').split(/[\\/]/).pop();
      return `<div class="vc">
        <div class="vc-head">
          <span class="vc-file">${name}</span>
          <span class="badge ${r.status==='PASSED'?'pass':'block'}">${r.status}</span>
          <span class="vc-counts">C:${cnt.CRITICAL||0} H:${cnt.HIGH||0} M:${cnt.MEDIUM||0}</span>
        </div>
        ${issueHtml}
      </div>`;
    }).join('');
  });
}

// ── C# syntax highlight ───────────────────────────────────────────────────────
function highlightCS(code) {
  // Order matters — process comments and strings first
  code = code.replace(/(\/\/[^\n]*)/g, '<span class="cm">$1</span>');
  code = code.replace(/(&quot;[^&\n]*?&quot;)/g, '<span class="st">$1</span>');
  code = code.replace(/(\[(?:HttpGet|HttpPost|ValidateAntiForgeryToken|FromForm|FromRoute|Route)[^\]]*\])/g, '<span class="at">$1</span>');
  const kws = ['using','namespace','public','private','protected','internal','sealed','static','readonly','override','virtual','abstract','async','await','return','var','new','throw','try','catch','finally','if','else','foreach','for','while','in','true','false','null','this','base','void','class','interface','enum'];
  const tys = ['Task','string','int','bool','decimal','long','double','float','object','List','IEnumerable','ILogger','IActionResult','Exception','DateTime','Guid','ActionResult'];
  kws.forEach(k => { code = code.replace(new RegExp('(?<![\\w.])(' + k + ')(?![\\w])', 'g'), '<span class="kw">$1</span>'); });
  tys.forEach(t => { code = code.replace(new RegExp('(?<![\\w.])(' + t + ')(?![\\w])', 'g'), '<span class="ty">$1</span>'); });
  // Method calls
  code = code.replace(/\b(\w+)(?=\s*\()/g, (m, n) => {
    if (n[0] === n[0].toUpperCase() && !['if','for','while','foreach','catch','using'].includes(n)) return `<span class="mt">${n}</span>`;
    return m;
  });
  return code;
}

function escHtml(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Init — load any already-existing files on page open
loadFiles();
loadReports();
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# HTTP SERVER
# ─────────────────────────────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        p = urlparse(self.path)
        qs = parse_qs(p.query)

        if p.path == '/':
            content = HTML_FILE.read_text(encoding='utf-8')
            self._html(content)
        elif p.path == '/api/files':
            self._json(self._list_files())
        elif p.path == '/api/file':
            path = qs.get('path', [''])[0]
            self._json({'content': self._read_file(path)})
        elif p.path == '/api/reports':
            self._json(self._load_reports())
        elif p.path == '/api/log':
            with _log_lock:
                self._json({'log': list(_pipeline_log), 'running': _pipeline_running})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        global _pipeline_running, _pipeline_log
        if self.path == '/api/run':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length) or b'{}')
            demo = bool(body.get('demo', False))
            migration_type = body.get('migrationType', 'vbscript-to-dotnet')
            migration_label = body.get('migrationLabel') or 'VBScript → .NET Core C#'

            with _log_lock:
                if _pipeline_running:
                    self._json({'error': 'already running'}, 409); return
                _pipeline_log = []
                _pipeline_running = True
                _pipeline_log.append(f'[CONFIG] Selected migration: {migration_label}')

            threading.Thread(target=self._run_pipeline, args=(demo, migration_type), daemon=True).start()
            self._json({'started': True})
        else:
            self.send_response(404); self.end_headers()

    # ── Pipeline runner ───────────────────────────────────────────────────────

    def _run_pipeline(self, demo: bool, migration_type: str):
        global _pipeline_running
        try:
            cmd = [sys.executable, '-u', 'run_pipeline.py']
            if demo:
                cmd.append('--demo')
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'
            env['PIPELINE_MIGRATION_TYPE'] = migration_type
            proc = subprocess.Popen(
                cmd, cwd=str(BASE_DIR),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=env, text=True, encoding='utf-8', errors='replace',
                bufsize=1,
            )
            for line in proc.stdout:
                with _log_lock:
                    _pipeline_log.append(line.rstrip())
            proc.wait()
        except Exception as e:
            with _log_lock:
                _pipeline_log.append(f'ERROR: {e}')
        finally:
            global _pipeline_running
            _pipeline_running = False

    # ── File helpers ──────────────────────────────────────────────────────────

    def _list_files(self):
        out_dir = BASE_DIR / 'output'
        if not out_dir.exists():
            return []
        files = sorted(
            str(f.relative_to(BASE_DIR)).replace('\\', '/')
            for f in out_dir.rglob('*') if f.is_file()
        )
        return files

    def _read_file(self, rel_path: str) -> str:
        try:
            target = (BASE_DIR / rel_path).resolve()
            if not str(target).startswith(str(BASE_DIR.resolve())):
                return 'Access denied'
            return target.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            return f'Error reading file: {e}'

    def _load_reports(self):
        reports_dir = BASE_DIR / 'validation-reports'
        if not reports_dir.exists():
            return []
        result = []
        for f in sorted(reports_dir.glob('*.json')):
            try:
                result.append(json.loads(f.read_text(encoding='utf-8')))
            except Exception:
                pass
        return result

    # ── Response helpers ──────────────────────────────────────────────────────

    def _html(self, body: str):
        data = body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass  # silence request logs


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = 8080
    server = http.server.HTTPServer(('localhost', port), Handler)
    url = f'http://localhost:{port}'
    print(f'Pipeline UI  ->  {url}')
    print('Press Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
