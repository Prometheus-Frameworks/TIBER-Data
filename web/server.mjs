import http from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PORT = parseInt(process.env.PORT || '3000', 10);

// ---------------------------------------------------------------------------
// Artifact definitions
// ---------------------------------------------------------------------------

const ARTIFACT_DEFS = [
  {
    key: 'roster_source_backed',
    name: 'Roster Player-Team Map 2025',
    path: 'data/processed/evidence/roster_player_team_map_2025.source_backed.json',
    kind: 'source_backed',
    viewerPath: '/roster',
  },
  {
    key: 'ppr_source_backed',
    name: 'Player Weekly PPR Outcomes 2025',
    path: 'data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json',
    kind: 'source_backed',
    viewerPath: '/ppr',
  },
  {
    key: 'roster_promoted',
    name: 'Roster Player-Team Map v1 (Promoted)',
    path: 'exports/promoted/nfl/roster_player_team_map_v1.json',
    kind: 'promoted_fixture',
    viewerPath: null,
  },
  {
    key: 'ppr_promoted',
    name: 'Player Weekly PPR Outcomes v1 (Promoted)',
    path: 'exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json',
    kind: 'promoted_fixture',
    viewerPath: null,
  },
];

function loadArtifact(def) {
  const fullPath = path.join(ROOT, def.path);
  if (!existsSync(fullPath)) {
    return { ...def, status: 'missing', records: [], recordCount: 0, error: 'File not found',
      provenance: null, sourcePath: null, generatedFrom: null, generatedAt: null, fields: [], sampleRecord: null };
  }
  try {
    const raw = readFileSync(fullPath, 'utf-8');
    const data = JSON.parse(raw);
    let records = [];
    let provenance = null;
    let sourcePath = null;
    let generatedFrom = null;
    let generatedAt = null;

    if (Array.isArray(data)) {
      records = data;
      generatedAt = records[0]?.generated_at ?? null;
    } else {
      records = Array.isArray(data.records) ? data.records : [];
      provenance = data.provenance ?? null;
      sourcePath = data.source_path ?? null;
      generatedFrom = data.generated_from ?? null;
    }

    const fields = records.length > 0 ? Object.keys(records[0]) : [];
    const sampleRecord = records[0] ?? null;

    return { ...def, status: 'available', records, recordCount: records.length,
      provenance, sourcePath, generatedFrom, generatedAt, fields, sampleRecord, error: null };
  } catch (e) {
    return { ...def, status: 'invalid', records: [], recordCount: 0, error: e.message,
      provenance: null, sourcePath: null, generatedFrom: null, generatedAt: null, fields: [], sampleRecord: null };
  }
}

console.log('Loading artifacts...');
const ARTIFACTS = {};
for (const def of ARTIFACT_DEFS) {
  ARTIFACTS[def.key] = loadArtifact(def);
  console.log(`  ${def.key}: ${ARTIFACTS[def.key].status} (${ARTIFACTS[def.key].recordCount} records)`);
}
console.log('Done.');

// ---------------------------------------------------------------------------
// Unique filter values (built once at startup)
// ---------------------------------------------------------------------------

function uniqueSorted(records, field) {
  const vals = new Set();
  for (const r of records) {
    const v = r[field];
    if (v !== null && v !== undefined && v !== '') vals.add(String(v));
  }
  return [...vals].sort((a, b) => {
    const na = Number(a), nb = Number(b);
    if (!isNaN(na) && !isNaN(nb)) return na - nb;
    return a.localeCompare(b);
  });
}

const ROSTER = ARTIFACTS.roster_source_backed;
const PPR = ARTIFACTS.ppr_source_backed;

const ROSTER_TEAMS = ROSTER.status === 'available' ? uniqueSorted(ROSTER.records, 'team') : [];
const ROSTER_POSITIONS = ROSTER.status === 'available' ? uniqueSorted(ROSTER.records, 'position') : [];
const ROSTER_WEEKS = ROSTER.status === 'available' ? uniqueSorted(ROSTER.records, 'week') : [];

const PPR_TEAMS = PPR.status === 'available' ? uniqueSorted(PPR.records, 'team') : [];
const PPR_POSITIONS = PPR.status === 'available' ? uniqueSorted(PPR.records, 'position') : [];
const PPR_WEEKS = PPR.status === 'available' ? uniqueSorted(PPR.records, 'week') : [];

// ---------------------------------------------------------------------------
// HTML helpers
// ---------------------------------------------------------------------------

const PAGE_SIZE = 50;

function esc(v) {
  if (v === null || v === undefined) return '';
  return String(v)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const CSS = `
:root{--bg:#0d1117;--surface:#161b22;--surface2:#21262d;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#388bfd;--green:#3fb950;--yellow:#d29922;--red:#f85149;--purple:#bc8cff}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;line-height:1.6;min-height:100vh}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code,pre,.mono{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace}

nav{background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px;display:flex;align-items:center;gap:8px;height:52px;position:sticky;top:0;z-index:10}
.nav-brand{font-weight:700;font-size:14px;color:var(--text);margin-right:8px;white-space:nowrap}
.nav-sep{color:var(--border);font-size:18px;user-select:none}
.nav-links{display:flex;gap:2px}
.nav-links a{color:var(--muted);font-size:13px;padding:4px 10px;border-radius:4px;transition:color .15s,background .15s}
.nav-links a:hover{color:var(--text);background:var(--surface2);text-decoration:none}
.nav-links a.active{color:var(--text);background:var(--surface2)}

main{max-width:1280px;margin:0 auto;padding:36px 24px 80px}

h1{font-size:22px;font-weight:700;margin-bottom:8px}
h2{font-size:16px;font-weight:600;margin:28px 0 12px;color:var(--text)}
h3{font-size:14px;font-weight:600;margin:0 0 6px}
p{color:var(--muted);margin-bottom:14px;max-width:720px}

.hero{margin-bottom:36px;padding-bottom:28px;border-bottom:1px solid var(--border)}
.hero-sub{font-size:15px;color:var(--muted);max-width:640px;margin-bottom:0}

.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:32px}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px 18px}
.stat-val{font-size:26px;font-weight:700;font-variant-numeric:tabular-nums}
.stat-lbl{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-top:4px}

.section-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-bottom:32px}
.section-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 20px}
.section-card h3{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;font-weight:500;margin-bottom:8px}
.section-card ul{list-style:none;padding:0}
.section-card li{padding:3px 0;font-size:13px}

.artifact-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 20px;margin-bottom:14px}
.artifact-card-header{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.artifact-name{font-weight:600;font-size:14px}
.artifact-meta{font-size:12px;color:var(--muted);margin-bottom:10px;font-family:'SFMono-Regular',Consolas,monospace}
.artifact-fields{font-size:11px;color:var(--muted);background:var(--surface2);border-radius:4px;padding:8px 10px;font-family:'SFMono-Regular',Consolas,monospace;margin-top:8px;word-break:break-all}
.artifact-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px 16px;margin-top:10px;font-size:12px}
.artifact-kv{display:flex;flex-direction:column}
.artifact-kv-k{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.5px}
.artifact-kv-v{color:var(--text);font-family:'SFMono-Regular',Consolas,monospace;word-break:break-all}

.badge{display:inline-flex;align-items:center;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:500;line-height:1.6;white-space:nowrap}
.badge-source{background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb55}
.badge-fixture{background:#6e40c922;color:#bc8cff;border:1px solid #6e40c955}
.badge-promoted{background:#1a7f3722;color:#3fb950;border:1px solid #1a7f3755}
.badge-ok{background:#1a7f3733;color:#3fb950;border:1px solid #1a7f3755}
.badge-missing{background:#f8514922;color:#f85149;border:1px solid #f8514955}
.badge-invalid{background:#d2992222;color:#d29922;border:1px solid #d2992255}

.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin-bottom:20px}
.fg{display:flex;flex-direction:column;gap:4px;flex:1;min-width:140px}
.fg label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;font-weight:500}
input[type=text],select{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:5px 9px;border-radius:5px;font-size:13px;width:100%}
input[type=text]:focus,select:focus{outline:none;border-color:var(--accent)}
.btn{background:var(--accent);color:#fff;border:none;padding:6px 16px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:500;white-space:nowrap;align-self:flex-end}
.btn:hover{opacity:.9}
.btn-ghost{background:transparent;color:var(--muted);border:1px solid var(--border);padding:5px 14px;border-radius:5px;cursor:pointer;font-size:12px;white-space:nowrap;align-self:flex-end;text-decoration:none;display:inline-flex;align-items:center}
.btn-ghost:hover{color:var(--text);text-decoration:none}

.table-meta{color:var(--muted);font-size:12px;margin-bottom:10px}
.table-wrap{overflow-x:auto;border-radius:8px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:12px}
thead{position:sticky;top:52px;z-index:5}
th{background:var(--surface2);border-bottom:1px solid var(--border);padding:8px 10px;text-align:left;font-weight:500;color:var(--muted);white-space:nowrap;font-size:11px;text-transform:uppercase;letter-spacing:.4px}
td{border-bottom:1px solid #21262d;padding:7px 10px;vertical-align:top;color:var(--text)}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,.025)}
.null-val{color:var(--border);font-style:italic}

.pager{display:flex;gap:8px;align-items:center;margin-top:16px;flex-wrap:wrap}
.pager-info{color:var(--muted);font-size:12px;flex:1}
.page-link{padding:4px 10px;border-radius:4px;font-size:12px;background:var(--surface);border:1px solid var(--border);color:var(--text);cursor:pointer;text-decoration:none}
.page-link:hover{background:var(--surface2);text-decoration:none}
.page-link.current{background:var(--accent);color:#fff;border-color:var(--accent)}
.page-link.disabled{color:var(--border);cursor:default;pointer-events:none}

.prov-block{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:12px 14px;font-size:12px;color:var(--muted);margin-bottom:16px;font-family:'SFMono-Regular',Consolas,monospace}
.prov-block b{color:var(--text)}

.doc-links{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.doc-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px}
.doc-card a{color:var(--text);font-weight:500}
.doc-card p{font-size:12px;margin-top:4px;margin-bottom:0}

.empty{color:var(--muted);padding:32px;text-align:center;font-size:13px}
.error-box{background:#f8514911;border:1px solid #f8514944;border-radius:6px;padding:12px 14px;color:#f85149;font-size:13px;margin-bottom:14px}

footer{border-top:1px solid var(--border);padding:16px 24px;text-align:center;font-size:11px;color:var(--muted);margin-top:40px}
`;

function layout(title, activeRoute, content) {
  const nav = [
    ['/', 'Home'],
    ['/artifacts', 'Artifacts'],
    ['/roster', 'Roster'],
    ['/ppr', 'PPR Outcomes'],
    ['/docs', 'Docs'],
  ].map(([href, label]) =>
    `<a href="${href}" class="${activeRoute === href ? 'active' : ''}">${label}</a>`
  ).join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} — TIBER-Data</title>
<style>${CSS}</style>
</head>
<body>
<nav>
  <span class="nav-brand">TIBER-Data</span>
  <span class="nav-sep">/</span>
  <span class="nav-sep" style="font-size:12px;color:var(--muted)">Evidence Layer</span>
  <div style="flex:1"></div>
  <div class="nav-links">${nav}</div>
</nav>
<main>${content}</main>
<footer>TIBER-Data Evidence Layer &mdash; read-only &mdash; source-verified artifacts only</footer>
</body>
</html>`;
}

function kindBadge(kind) {
  if (kind === 'source_backed') return `<span class="badge badge-source">source_backed</span>`;
  if (kind === 'promoted_fixture') return `<span class="badge badge-promoted">promoted_fixture</span>`;
  return `<span class="badge badge-fixture">offline_fixture</span>`;
}

function statusBadge(status) {
  if (status === 'available') return `<span class="badge badge-ok">available</span>`;
  if (status === 'missing') return `<span class="badge badge-missing">missing</span>`;
  return `<span class="badge badge-invalid">invalid</span>`;
}

function fmtNum(n) {
  return n == null ? '<span class="null-val">—</span>' : Number(n).toLocaleString();
}

function tdVal(v) {
  if (v === null || v === undefined) return '<span class="null-val">null</span>';
  return esc(String(v));
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

function homePage() {
  const totalRecords = Object.values(ARTIFACTS)
    .filter(a => a.status === 'available')
    .reduce((s, a) => s + a.recordCount, 0);
  const available = Object.values(ARTIFACTS).filter(a => a.status === 'available').length;

  const statCards = `
<div class="stats-grid">
  <div class="stat-card"><div class="stat-val">${available}</div><div class="stat-lbl">Artifacts loaded</div></div>
  <div class="stat-card"><div class="stat-val">${totalRecords.toLocaleString()}</div><div class="stat-lbl">Total records</div></div>
  <div class="stat-card"><div class="stat-val">${ROSTER.recordCount.toLocaleString()}</div><div class="stat-lbl">Roster records</div></div>
  <div class="stat-card"><div class="stat-val">${PPR.recordCount.toLocaleString()}</div><div class="stat-lbl">PPR outcome records</div></div>
</div>`;

  const sections = `
<div class="section-grid">
  <div class="section-card">
    <h3>Source-Backed Artifacts</h3>
    <ul>
      <li><a href="/roster">Roster Player-Team Map 2025</a></li>
      <li><a href="/ppr">Player Weekly PPR Outcomes 2025</a></li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Promoted Artifacts</h3>
    <ul>
      <li>Roster Player-Team Map v1</li>
      <li>Player Weekly PPR Outcomes v1</li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Artifact Inventory</h3>
    <ul>
      <li><a href="/artifacts">View all artifacts &rarr;</a></li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Contract Docs</h3>
    <ul>
      <li><a href="/docs">Evidence Layer &amp; contracts &rarr;</a></li>
    </ul>
  </div>
</div>`;

  return layout('Home', '/', `
<div class="hero">
  <h1>TIBER-Data Evidence Layer</h1>
  <p class="hero-sub">
    TIBER-Data is the source and provenance layer for the TIBER system. It stores canonical contracts,
    source-backed evidence artifacts, fixture scaffolds, and validation metadata used by
    downstream football intelligence modules.
  </p>
</div>

${statCards}

<h2>What this viewer does</h2>
<p>
  Inspect what data artifacts exist, where they came from, how many records they contain,
  what fields are available, and whether they are source-backed or fixture-based.
  This is a read-only data lab — not a fantasy product surface.
</p>

${sections}

<h2>What this viewer does not do</h2>
<p>
  This viewer does not answer who to start, who to trade for, player rankings, or final
  player grades. Those belong in TIBER-Fantasy, FORGE, or downstream scoring surfaces.
</p>`);
}

function artifactsPage() {
  const cards = ARTIFACT_DEFS.map(def => {
    const a = ARTIFACTS[def.key];
    const viewer = a.viewerPath
      ? `<a href="${a.viewerPath}" class="btn-ghost" style="margin-top:10px;display:inline-flex">View data &rarr;</a>`
      : '';

    const provenanceRows = [
      a.provenance && `<div class="artifact-kv"><span class="artifact-kv-k">provenance</span><span class="artifact-kv-v">${esc(a.provenance)}</span></div>`,
      a.sourcePath && `<div class="artifact-kv"><span class="artifact-kv-k">source_path</span><span class="artifact-kv-v">${esc(a.sourcePath)}</span></div>`,
      a.generatedAt && `<div class="artifact-kv"><span class="artifact-kv-k">generated_at</span><span class="artifact-kv-v">${esc(a.generatedAt)}</span></div>`,
      a.generatedFrom && `<div class="artifact-kv"><span class="artifact-kv-k">generated_from</span><span class="artifact-kv-v">${esc(
        Array.isArray(a.generatedFrom) ? a.generatedFrom.join(', ') : String(a.generatedFrom)
      )}</span></div>`,
    ].filter(Boolean).join('');

    const errorHtml = a.error ? `<div class="error-box">${esc(a.error)}</div>` : '';
    const fieldsHtml = a.fields.length
      ? `<div class="artifact-fields">${esc(a.fields.join(' · '))}</div>`
      : '';

    return `
<div class="artifact-card">
  <div class="artifact-card-header">
    <span class="artifact-name">${esc(a.name)}</span>
    ${kindBadge(a.kind)}
    ${statusBadge(a.status)}
  </div>
  <div class="artifact-meta">${esc(a.path)}</div>
  ${errorHtml}
  <div class="artifact-row">
    <div class="artifact-kv"><span class="artifact-kv-k">records</span><span class="artifact-kv-v">${a.recordCount.toLocaleString()}</span></div>
    ${provenanceRows}
  </div>
  ${fieldsHtml}
  ${viewer}
</div>`;
  }).join('');

  return layout('Artifacts', '/artifacts', `
<h1>Artifact Inventory</h1>
<p>All known TIBER-Data evidence artifacts — source-backed and promoted. Missing or invalid artifacts are shown rather than omitted.</p>
${cards}`);
}

function buildFilterUrl(base, currentParams, overrides) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries({ ...currentParams, ...overrides })) {
    if (v !== undefined && v !== null && v !== '') p.set(k, String(v));
  }
  return `${base}?${p.toString()}`;
}

function rosterPage(query) {
  const a = ROSTER;

  if (a.status !== 'available') {
    return layout('Roster Identity Viewer', '/roster', `
<h1>Roster Identity Viewer</h1>
${a.status === 'missing'
  ? '<div class="error-box">Artifact not found: ' + esc(a.path) + '</div>'
  : '<div class="error-box">Artifact invalid: ' + esc(a.error) + '</div>'}`);
  }

  const nameQ = (query.name || '').trim().toLowerCase();
  const teamQ = query.team || '';
  const posQ = query.position || '';
  const weekQ = query.week || '';
  const page = Math.max(1, parseInt(query.page || '1', 10));

  let rows = a.records;
  if (nameQ) rows = rows.filter(r => (r.player_name || '').toLowerCase().includes(nameQ));
  if (teamQ) rows = rows.filter(r => String(r.team || '') === teamQ);
  if (posQ) rows = rows.filter(r => String(r.position || '') === posQ);
  if (weekQ) rows = rows.filter(r => String(r.week ?? '') === weekQ);

  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const clampedPage = Math.min(page, totalPages);
  const pageRows = rows.slice((clampedPage - 1) * PAGE_SIZE, clampedPage * PAGE_SIZE);

  const currentParams = { name: nameQ, team: teamQ, position: posQ, week: weekQ };

  const selectOpts = (opts, val) =>
    ['', ...opts].map(o => `<option value="${esc(o)}" ${o === val ? 'selected' : ''}>${esc(o) || 'All'}</option>`).join('');

  const filters = `
<form method="GET" action="/roster">
<div class="filters">
  <div class="fg" style="flex:2;min-width:180px"><label>Player name</label><input type="text" name="name" value="${esc(nameQ)}" placeholder="Search name..."></div>
  <div class="fg"><label>Team</label><select name="team">${selectOpts(ROSTER_TEAMS, teamQ)}</select></div>
  <div class="fg"><label>Position</label><select name="position">${selectOpts(ROSTER_POSITIONS, posQ)}</select></div>
  <div class="fg"><label>Week</label><select name="week">${selectOpts(ROSTER_WEEKS, weekQ)}</select></div>
  <button type="submit" class="btn">Filter</button>
  <a href="/roster" class="btn-ghost">Reset</a>
</div>
</form>`;

  const COLS = ['season','week','player_id','player_name','team','position','active_roster_status','source_status'];
  const thead = COLS.map(c => `<th>${esc(c)}</th>`).join('');
  const tbody = pageRows.length
    ? pageRows.map(r => `<tr>${COLS.map(c => `<td>${tdVal(r[c])}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${COLS.length}" class="empty">No records match the current filters.</td></tr>`;

  const pagLinks = buildPager('/roster', currentParams, clampedPage, totalPages);

  const provHtml = a.provenance ? `
<div class="prov-block">
  <b>provenance:</b> ${esc(a.provenance)}<br>
  <b>source_path:</b> ${esc(a.sourcePath)}<br>
  <b>generated_from:</b> ${esc(Array.isArray(a.generatedFrom) ? a.generatedFrom.join(', ') : String(a.generatedFrom ?? ''))}
</div>` : '';

  return layout('Roster Identity Viewer', '/roster', `
<h1>Source-Backed Roster Identity Viewer</h1>
<p>Read-only view of <code class="mono">${esc(a.path)}</code> — ${a.recordCount.toLocaleString()} records. Data reflects committed artifact, not live fetch.</p>
${provHtml}
${filters}
<div class="table-meta">Showing ${((clampedPage-1)*PAGE_SIZE+1).toLocaleString()}–${Math.min(clampedPage*PAGE_SIZE, total).toLocaleString()} of ${total.toLocaleString()} matching records</div>
<div class="table-wrap">
<table>
<thead><tr>${thead}</tr></thead>
<tbody>${tbody}</tbody>
</table>
</div>
${pagLinks}`);
}

function pprPage(query) {
  const a = PPR;

  if (a.status !== 'available') {
    return layout('PPR Outcomes Viewer', '/ppr', `
<h1>Player Weekly PPR Outcomes Viewer</h1>
${a.status === 'missing'
  ? '<div class="error-box">Artifact not found: ' + esc(a.path) + '</div>'
  : '<div class="error-box">Artifact invalid: ' + esc(a.error) + '</div>'}`);
  }

  const nameQ = (query.name || '').trim().toLowerCase();
  const teamQ = query.team || '';
  const posQ = query.position || '';
  const weekQ = query.week || '';
  const page = Math.max(1, parseInt(query.page || '1', 10));

  let rows = a.records;
  if (nameQ) rows = rows.filter(r => (r.player_name || '').toLowerCase().includes(nameQ));
  if (teamQ) rows = rows.filter(r => String(r.team || '') === teamQ);
  if (posQ) rows = rows.filter(r => String(r.position || '') === posQ);
  if (weekQ) rows = rows.filter(r => String(r.week ?? '') === weekQ);

  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const clampedPage = Math.min(page, totalPages);
  const pageRows = rows.slice((clampedPage - 1) * PAGE_SIZE, clampedPage * PAGE_SIZE);

  const currentParams = { name: nameQ, team: teamQ, position: posQ, week: weekQ };

  const selectOpts = (opts, val) =>
    ['', ...opts].map(o => `<option value="${esc(o)}" ${o === val ? 'selected' : ''}>${esc(o) || 'All'}</option>`).join('');

  const filters = `
<form method="GET" action="/ppr">
<div class="filters">
  <div class="fg" style="flex:2;min-width:180px"><label>Player name</label><input type="text" name="name" value="${esc(nameQ)}" placeholder="Search name..."></div>
  <div class="fg"><label>Team</label><select name="team">${selectOpts(PPR_TEAMS, teamQ)}</select></div>
  <div class="fg"><label>Position</label><select name="position">${selectOpts(PPR_POSITIONS, posQ)}</select></div>
  <div class="fg"><label>Week</label><select name="week">${selectOpts(PPR_WEEKS, weekQ)}</select></div>
  <button type="submit" class="btn">Filter</button>
  <a href="/ppr" class="btn-ghost">Reset</a>
</div>
</form>`;

  const COLS = [
    'season','week','player_id','player_name','team','opponent','position',
    'receptions','targets','rushing_attempts','rushing_yards','rushing_tds',
    'receiving_yards','receiving_tds','passing_yards','passing_tds','interceptions',
  ];
  const thead = COLS.map(c => `<th>${esc(c)}</th>`).join('');
  const tbody = pageRows.length
    ? pageRows.map(r => `<tr>${COLS.map(c => `<td>${tdVal(r[c])}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${COLS.length}" class="empty">No records match the current filters.</td></tr>`;

  const pagLinks = buildPager('/ppr', currentParams, clampedPage, totalPages);

  const provHtml = a.provenance ? `
<div class="prov-block">
  <b>provenance:</b> ${esc(a.provenance)}<br>
  <b>source_path:</b> ${esc(a.sourcePath)}<br>
  <b>generated_from:</b> ${esc(Array.isArray(a.generatedFrom) ? a.generatedFrom.join(', ') : String(a.generatedFrom ?? ''))}
</div>` : '';

  return layout('PPR Outcomes Viewer', '/ppr', `
<h1>Source-Backed Player Weekly PPR Outcomes Viewer</h1>
<p>Read-only view of <code class="mono">${esc(a.path)}</code> — ${a.recordCount.toLocaleString()} records. Rows are raw source-backed input records from committed artifact. Data reflects committed artifact, not live fetch.</p>
${provHtml}
${filters}
<div class="table-meta">Showing ${((clampedPage-1)*PAGE_SIZE+1).toLocaleString()}–${Math.min(clampedPage*PAGE_SIZE, total).toLocaleString()} of ${total.toLocaleString()} matching records</div>
<div class="table-wrap">
<table>
<thead><tr>${thead}</tr></thead>
<tbody>${tbody}</tbody>
</table>
</div>
${pagLinks}`);
}

function buildPager(base, params, page, totalPages) {
  if (totalPages <= 1) return '';

  const mkLink = (p, label, cls = '') => {
    const url = buildFilterUrl(base, params, { page: p });
    return `<a href="${url}" class="page-link ${cls}">${label}</a>`;
  };

  const links = [];
  links.push(page > 1 ? mkLink(page - 1, '&larr; Prev') : `<span class="page-link disabled">&larr; Prev</span>`);

  const window = 3;
  let start = Math.max(1, page - window);
  let end = Math.min(totalPages, page + window);
  if (start > 1) { links.push(mkLink(1, '1')); if (start > 2) links.push(`<span class="page-link disabled">…</span>`); }
  for (let i = start; i <= end; i++) links.push(mkLink(i, i, i === page ? 'current' : ''));
  if (end < totalPages) { if (end < totalPages - 1) links.push(`<span class="page-link disabled">…</span>`); links.push(mkLink(totalPages, totalPages)); }

  links.push(page < totalPages ? mkLink(page + 1, 'Next &rarr;') : `<span class="page-link disabled">Next &rarr;</span>`);

  return `<div class="pager"><span class="pager-info">Page ${page} of ${totalPages}</span>${links.join('')}</div>`;
}

function docsPage() {
  const docs = [
    {
      title: 'Evidence Layer v0 Contract',
      path: 'docs/contracts/evidence-layer-v0.md',
      desc: 'Governance contract for the TIBER-Data Evidence Layer — provenance, validation, and artifact lifecycle.',
    },
    {
      title: 'Roster Player-Team Map v1',
      path: 'docs/data/roster-player-team-map-v1.md',
      desc: 'Schema and provenance documentation for the roster identity artifact.',
    },
    {
      title: 'Player Weekly PPR Outcomes v1',
      path: 'docs/data/player-weekly-ppr-outcomes-v1.md',
      desc: 'Schema and provenance documentation for the player weekly PPR outcomes artifact.',
    },
    {
      title: 'Player Weekly PPR Outcomes — Source-Backed 2025',
      path: 'docs/data/player-weekly-ppr-outcomes-source-backed-2025.md',
      desc: 'Source-backed artifact documentation for 2025 nflreadpy-derived PPR outcomes.',
    },
    {
      title: 'Historical Rookie Replay v0',
      path: 'docs/data/historical-rookie-replay-v0.md',
      desc: 'Documentation for the historical rookie replay contract.',
    },
    {
      title: 'Player Weekly Usage v1',
      path: 'docs/data/player-weekly-usage-v1.md',
      desc: 'Schema documentation for player weekly usage contract.',
    },
    {
      title: 'Team Offense Summary v1',
      path: 'docs/data/team-offense-summary-v1.md',
      desc: 'Team-level offensive summary contract documentation.',
    },
  ];

  const cards = docs.map(d => {
    const exists = existsSync(path.join(ROOT, d.path));
    const statusEl = exists
      ? `<span class="badge badge-ok" style="margin-left:6px;font-size:10px">found</span>`
      : `<span class="badge badge-missing" style="margin-left:6px;font-size:10px">missing</span>`;
    return `
<div class="doc-card">
  <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px">
    <span class="doc-card a">${esc(d.title)}</span>${statusEl}
  </div>
  <p>${esc(d.desc)}</p>
  <code class="mono" style="font-size:11px;color:var(--muted)">${esc(d.path)}</code>
</div>`;
  }).join('');

  return layout('Docs', '/docs', `
<h1>Docs &amp; Contracts</h1>
<p>
  Contract and governance documentation for TIBER-Data artifacts. These docs live in the repository at <code class="mono">docs/</code>.
  For full content, browse the repository directly.
</p>
<div class="doc-links">${cards}</div>`);
}

// ---------------------------------------------------------------------------
// HTTP server
// ---------------------------------------------------------------------------

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const { pathname, searchParams } = url;
  const query = Object.fromEntries(searchParams.entries());

  function send(status, contentType, body) {
    res.writeHead(status, { 'Content-Type': contentType });
    res.end(body);
  }

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    return send(405, 'text/plain', 'Method Not Allowed');
  }

  try {
    if (pathname === '/health') {
      const payload = {
        status: 'ok',
        service: 'tiber-data-evidence-layer',
        artifacts: Object.fromEntries(
          Object.entries(ARTIFACTS).map(([k, v]) => [k, { status: v.status, recordCount: v.recordCount }])
        ),
        timestamp: new Date().toISOString(),
      };
      return send(200, 'application/json', JSON.stringify(payload, null, 2));
    }

    if (pathname === '/' || pathname === '') return send(200, 'text/html', homePage());
    if (pathname === '/artifacts') return send(200, 'text/html', artifactsPage());
    if (pathname === '/roster') return send(200, 'text/html', rosterPage(query));
    if (pathname === '/ppr') return send(200, 'text/html', pprPage(query));
    if (pathname === '/docs') return send(200, 'text/html', docsPage());

    send(404, 'text/html', layout('Not Found', '', '<h1>404</h1><p>Page not found.</p>'));
  } catch (err) {
    console.error(err);
    send(500, 'text/plain', 'Internal Server Error');
  }
});

server.listen(PORT, () => {
  console.log(`TIBER-Data Evidence Layer → http://localhost:${PORT}`);
});
