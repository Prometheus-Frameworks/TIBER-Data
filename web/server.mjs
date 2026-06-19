import http from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PORT = parseInt(process.env.PORT || '5000', 10);

// ---------------------------------------------------------------------------
// Artifact definitions
// ---------------------------------------------------------------------------

const ARTIFACT_DEFS = [
  {
    key: 'roster_source_backed',
    name: 'Player team assignments for 2025',
    path: 'data/processed/evidence/roster_player_team_map_2025.source_backed.json',
    kind: 'source_backed',
    viewerPath: '/roster',
  },
  {
    key: 'ppr_source_backed',
    name: 'Weekly player box-score outcomes for 2025',
    path: 'data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json',
    kind: 'source_backed',
    viewerPath: '/ppr',
  },
  {
    key: 'usage_source_backed',
    name: 'Weekly player usage for 2025',
    path: 'data/processed/evidence/player_weekly_usage_2025.source_backed.json',
    kind: 'source_backed',
    viewerPath: null,
  },
  {
    key: 'ppr_computed_source_backed',
    name: 'Computed weekly PPR totals for 2025',
    path: 'data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json',
    kind: 'source_backed',
    viewerPath: null,
  },
  {
    key: 'goblin_candidates_2025',
    name: 'Research signal candidates for 2025',
    path: 'data/processed/research/goblin_signal_candidates_2025.source_backed.json',
    kind: 'source_backed_research',
    viewerPath: '/goblin',
  },
  {
    key: 'roster_promoted',
    name: 'Published player team assignments v1',
    path: 'exports/promoted/nfl/roster_player_team_map_v1.json',
    kind: 'promoted_fixture',
    viewerPath: null,
  },
  {
    key: 'ppr_promoted',
    name: 'Published weekly player box scores v1',
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
      generatedAt = data.generated_at ?? records[0]?.generated_at ?? null;
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

function uniqueSortedValues(values) {
  return [...new Set(
    values
      .filter(v => v !== null && v !== undefined && v !== '')
      .map(String)
  )].sort((a, b) => a.localeCompare(b));
}

const ROSTER = ARTIFACTS.roster_source_backed;
const PPR = ARTIFACTS.ppr_source_backed;
const USAGE = ARTIFACTS.usage_source_backed;
const PPR_COMPUTED = ARTIFACTS.ppr_computed_source_backed;

const ROSTER_TEAMS = ROSTER.status === 'available' ? uniqueSorted(ROSTER.records, 'team') : [];
const ROSTER_POSITIONS = ROSTER.status === 'available' ? uniqueSorted(ROSTER.records, 'position') : [];
const ROSTER_WEEKS = ROSTER.status === 'available' ? uniqueSorted(ROSTER.records, 'week') : [];

const PPR_TEAMS = PPR.status === 'available' ? uniqueSorted(PPR.records, 'team') : [];
const PPR_POSITIONS = PPR.status === 'available' ? uniqueSorted(PPR.records, 'position') : [];
const PPR_WEEKS = PPR.status === 'available' ? uniqueSorted(PPR.records, 'week') : [];
const GOBLIN = ARTIFACTS.goblin_candidates_2025;
const GOBLIN_TEAMS = GOBLIN.status === 'available' ? uniqueSorted(GOBLIN.records, 'team') : [];
const GOBLIN_POSITIONS = GOBLIN.status === 'available' ? uniqueSorted(GOBLIN.records, 'position') : [];
const GOBLIN_WEEKS = GOBLIN.status === 'available' ? uniqueSorted(GOBLIN.records, 'week') : [];

const SYSTEM_FLOW_REGISTRY_PATH = 'contracts/tiber-system-flow-registry.v1.json';
const LOCAL_VIEWER_ROUTES = ['/health', '/artifacts', '/roster', '/ppr', '/player-lab', '/goblin', '/docs', '/system-flow'];

function loadSystemFlowRegistry() {
  const fullPath = path.join(ROOT, SYSTEM_FLOW_REGISTRY_PATH);
  if (!existsSync(fullPath)) {
    return { status: 'missing', path: SYSTEM_FLOW_REGISTRY_PATH, error: 'File not found', registry: null, flows: [], globalRules: [] };
  }

  try {
    const raw = readFileSync(fullPath, 'utf-8');
    const parsed = JSON.parse(raw);
    const flows = Array.isArray(parsed?.flows) ? parsed.flows : [];
    const globalRules = Array.isArray(parsed?.global_rules) ? parsed.global_rules : [];
    return { status: 'available', path: SYSTEM_FLOW_REGISTRY_PATH, error: null, registry: parsed, flows, globalRules };
  } catch (e) {
    return { status: 'invalid', path: SYSTEM_FLOW_REGISTRY_PATH, error: e.message, registry: null, flows: [], globalRules: [] };
  }
}

const SYSTEM_FLOW_REGISTRY = loadSystemFlowRegistry();

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
.artifact-meta{font-size:12px;color:var(--muted);margin-bottom:10px}
.artifact-fields{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.tag{display:inline-flex;align-items:center;border:1px solid var(--border);background:var(--surface2);border-radius:999px;padding:2px 8px;font-size:11px;color:var(--muted);line-height:1.5}
.tag-info{cursor:help}
.detail-block{margin:12px 0 16px;background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:10px 12px;color:var(--muted);font-size:12px}
.detail-block summary{cursor:pointer;color:var(--text);font-weight:500}
.detail-block[open] summary{margin-bottom:8px}
.detail-row{display:grid;grid-template-columns:minmax(130px,190px) 1fr;gap:8px;padding:3px 0;border-top:1px solid rgba(48,54,61,.5)}
.detail-row:first-of-type{border-top:none}
.detail-k{color:var(--muted)}
.detail-v{color:var(--text);font-family:'SFMono-Regular',Consolas,monospace;word-break:break-all}
.artifact-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px 16px;margin-top:10px;font-size:12px}
.artifact-kv{display:flex;flex-direction:column}
.artifact-kv-k{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.5px}
.artifact-kv-v{color:var(--text);word-break:break-word}

.badge{display:inline-flex;align-items:center;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:500;line-height:1.6;white-space:nowrap}
.badge-source{background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb55}
.badge-fixture{background:#6e40c922;color:#bc8cff;border:1px solid #6e40c955}
.badge-promoted{background:#1a7f3722;color:#3fb950;border:1px solid #1a7f3755}
.badge-ok{background:#1a7f3733;color:#3fb950;border:1px solid #1a7f3755}
.badge-missing{background:#f8514922;color:#f85149;border:1px solid #f8514955}
.badge-invalid{background:#d2992222;color:#d29922;border:1px solid #d2992255}
.badge-approved{background:#1a7f3733;color:#3fb950;border:1px solid #1a7f3755}
.badge-review{background:#d2992222;color:#d29922;border:1px solid #d2992255}
.badge-blocked{background:#f8514922;color:#f85149;border:1px solid #f8514955}

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
table{width:100%;border-collapse:separate;border-spacing:0;font-size:12px}
th{background:var(--surface2);border-bottom:1px solid var(--border);padding:8px 10px;text-align:left;font-weight:500;color:var(--muted);white-space:nowrap;font-size:11px;letter-spacing:.2px}
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

.source-summary{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:12px 14px;font-size:13px;color:var(--muted);margin-bottom:16px}
.source-summary b{color:var(--text)}

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
    ['/', 'Overview'],
    ['/artifacts', 'Data Files'],
    ['/roster', 'Player Teams'],
    ['/ppr', 'Weekly Stats'],
    ['/goblin', 'Research Signals'],
    ['/player-lab', 'Player Lab'],
    ['/docs', 'Contracts'],
    ['/system-flow', 'System Flow'],
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
  <span class="nav-brand">Football Evidence Viewer</span>
  <span class="nav-sep">/</span>
  <span class="nav-sep" style="font-size:12px;color:var(--muted)">read-only verified data</span>
  <div style="flex:1"></div>
  <div class="nav-links">${nav}</div>
</nav>
<main>${content}</main>
<footer>Football Evidence Viewer &mdash; read-only &mdash; verified data files only</footer>
</body>
</html>`;
}

const LABELS = {
  active_roster_status: 'Roster status',
  air_yards: 'Air yards',
  air_yards_share: 'Air yards share',
  candidate_score: 'Candidate score',
  evidence_status: 'Evidence status',
  generated_at: 'Generated at',
  generated_from: 'Generated from',
  gross_output_flags: 'Low-output signals',
  interceptions: 'Interceptions',
  legitimate_indicator_flags: 'Usage support signals',
  opponent: 'Opponent',
  passing_tds: 'Passing TDs',
  passing_yards: 'Passing yards',
  player_id: 'Player ID',
  player_name: 'Player name',
  position: 'Position',
  ppr_points: 'PPR points',
  provenance: 'Source summary',
  receiving_tds: 'Receiving TDs',
  receiving_yards: 'Receiving yards',
  receptions: 'Receptions',
  records: 'Records',
  rushing_attempts: 'Carries',
  rushing_tds: 'Rushing TDs',
  rushing_yards: 'Rushing yards',
  season: 'Season',
  source_path: 'Source file',
  source_status: 'Source status',
  target_share: 'Target share',
  targets: 'Targets',
  team: 'Team',
  week: 'Week',
};

const VALUE_LABELS = {
  source_verified: 'Verified',
  source_backed: 'Verified Source',
  source_backed_research: 'Verified Research Source',
  source_backed_research_candidate: 'Verified research row',
  promoted_fixture: 'Published',
  offline_fixture: 'Offline fixture',
  available: 'Available',
  missing: 'Missing',
  invalid: 'Invalid',
};

const SIGNAL_LABELS = {
  air_yards_without_output: ['Air yards without results', 'The player had air-yards usage, but it did not turn into fantasy output.'],
  carries_without_points: ['Carries without points', 'The player received rushing work without much fantasy scoring.'],
  low_ppr_high_target_share: ['Low PPR, high target share', 'The player earned a meaningful share of team targets but scored few PPR points.'],
  low_ppr_high_targets: ['Low PPR, high targets', 'The player had notable target volume without matching PPR production.'],
  negative_air_yards_share_context: ['Negative air-yards context', 'Air-yards context was unusual and should be reviewed carefully.'],
  target_share_without_touchdown: ['Targets without touchdowns', 'The player had target share but no touchdown result.'],
  usage_spike_without_box_score: ['Usage spike without box score', 'Usage increased without showing up strongly in the box score.'],
  low_ppr_output: ['Low PPR output', 'The weekly fantasy output was low.'],
  low_receiving_yardage: ['Low receiving yardage', 'Receiving yards were limited.'],
  low_reception_output: ['Low receptions', 'Reception count was limited.'],
  no_touchdown: ['No touchdown', 'The player did not score a touchdown in this row.'],
};

function humanLabel(key) {
  if (LABELS[key]) return LABELS[key];
  return String(key).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function displayValue(v) {
  if (v === null || v === undefined || v === '' || v === 'unknown' || v === 'null') return '—';
  return VALUE_LABELS[v] || String(v);
}

function kindBadge(kind) {
  const label = VALUE_LABELS[kind] || humanLabel(kind);
  if (kind === 'source_backed' || kind === 'source_backed_research') return `<span class="badge badge-source">${esc(label)}</span>`;
  if (kind === 'promoted_fixture') return `<span class="badge badge-promoted">${esc(label)}</span>`;
  return `<span class="badge badge-fixture">${esc(label)}</span>`;
}

function statusBadge(status) {
  if (status === 'available') return `<span class="badge badge-ok">${esc(displayValue(status))}</span>`;
  if (status === 'missing') return `<span class="badge badge-missing">${esc(displayValue(status))}</span>`;
  return `<span class="badge badge-invalid">${esc(displayValue(status))}</span>`;
}

function fmtNum(n) {
  return n == null ? '<span class="null-val">—</span>' : Number(n).toLocaleString();
}

function tdVal(v) {
  const label = displayValue(v);
  if (label === '—') return '<span class="null-val">—</span>';
  return esc(label);
}

function fieldTags(fields) {
  return fields.map(f => `<span class="tag">${esc(humanLabel(f))}</span>`).join('');
}

function signalTags(values) {
  if (!Array.isArray(values) || values.length === 0) return '<span class="null-val">—</span>';
  return values.map(v => {
    const [label, tip] = SIGNAL_LABELS[v] || [humanLabel(v), 'Research signal from the source artifact.'];
    return `<span class="tag tag-info" title="${esc(tip)}">${esc(label)}</span>`;
  }).join('');
}

function technicalDetails(summary, rows) {
  const body = rows.filter(r => r && r.value !== null && r.value !== undefined && r.value !== '').map(r => {
    const value = Array.isArray(r.value) ? r.value.join(', ') : String(r.value);
    return `<div class="detail-row"><span class="detail-k">${esc(r.label)}</span><span class="detail-v">${esc(value)}</span></div>`;
  }).join('');
  return body ? `<details class="detail-block"><summary>${esc(summary)}</summary>${body}</details>` : '';
}

function sourceSummary(a) {
  return `<div class="source-summary"><b>Source:</b> This page shows a committed, read-only data file with ${a.recordCount.toLocaleString()} records. The data is loaded from this repository at server start; it is not a live fetch.</div>`;
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
  <div class="stat-card"><div class="stat-val">${available}</div><div class="stat-lbl">Data files loaded</div></div>
  <div class="stat-card"><div class="stat-val">${totalRecords.toLocaleString()}</div><div class="stat-lbl">Total records</div></div>
  <div class="stat-card"><div class="stat-val">${ROSTER.recordCount.toLocaleString()}</div><div class="stat-lbl">Player roster rows</div></div>
  <div class="stat-card"><div class="stat-val">${PPR.recordCount.toLocaleString()}</div><div class="stat-lbl">Weekly box-score rows</div></div>
</div>`;

  const sections = `
<div class="section-grid">
  <div class="section-card">
    <h3>Verified data views</h3>
    <ul>
      <li><a href="/roster">Player team assignments for 2025</a></li>
      <li><a href="/ppr">Weekly player box-score outcomes for 2025</a></li>
      <li><a href="/goblin">Research signal rows for 2025</a></li>
      <li><a href="/player-lab">Player interpretability lab</a></li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Research signal review</h3>
    <ul>
      <li><a href="/goblin">Review research signals &rarr;</a></li>
      <li>Each row is a flagged player-week worth reviewing</li>
      <li>These are research rows, not recommendations</li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Player lab scaffold</h3>
    <ul>
      <li><a href="/player-lab">Search source-backed player rows &rarr;</a></li>
      <li>Deterministic tags with raw JSON visible</li>
      <li>No lineup advice or prediction scores</li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Published files</h3>
    <ul>
      <li>Player team assignments v1</li>
      <li>Weekly player box scores v1</li>
    </ul>
  </div>
  <div class="section-card">
    <h3>All data files</h3>
    <ul>
      <li><a href="/artifacts">View full file inventory &rarr;</a></li>
    </ul>
  </div>
  <div class="section-card">
    <h3>Schema docs</h3>
    <ul>
      <li><a href="/docs">Field definitions &amp; contracts &rarr;</a></li>
    </ul>
  </div>
</div>`;

  return layout('Home', '/', `
<div class="hero">
  <h1>Football Evidence Viewer</h1>
  <p class="hero-sub">
    Browse the football data files this repository has already verified and published.
    This viewer explains what data is available, where it came from, and what is missing without changing any files.
  </p>
</div>

${statCards}

<h2>What you can do here</h2>
<p>
  Browse the verified data files in this repository — see what's available, how many records each file contains,
  what fields are in each file, and where the data came from. Nothing here changes any files.
</p>

${sections}

<h2>What this viewer is not for</h2>
<p>
  This viewer does not give player rankings, start/sit advice, trade recommendations, or fantasy scores.
  Those outputs come from separate downstream tools that consume these data files.
</p>`);
}

function artifactsPage() {
  const cards = ARTIFACT_DEFS.map(def => {
    const a = ARTIFACTS[def.key];
    const viewer = a.viewerPath
      ? `<a href="${a.viewerPath}" class="btn-ghost" style="margin-top:10px;display:inline-flex">View data &rarr;</a>`
      : '';

    const detailsHtml = technicalDetails('Show source details', [
      { label: 'Artifact file path', value: a.path },
      { label: 'Source summary', value: a.provenance },
      { label: 'Source file', value: a.sourcePath },
      { label: 'Generated at', value: a.generatedAt },
      { label: 'Generated from', value: a.generatedFrom },
    ]);

    const errorHtml = a.error ? `<div class="error-box">${esc(a.error)}</div>` : '';
    const fieldsHtml = a.fields.length
      ? `<div><div class="artifact-kv-k" style="margin-top:10px">Fields in this file</div><div class="artifact-fields">${fieldTags(a.fields)}</div></div>`
      : '';

    return `
<div class="artifact-card">
  <div class="artifact-card-header">
    <span class="artifact-name">${esc(a.name)}</span>
    ${kindBadge(a.kind)}
    ${statusBadge(a.status)}
  </div>
  <div class="artifact-meta">${a.status === 'available' ? 'Ready to view from committed repository data.' : 'Needs attention before this file can be viewed.'}</div>
  ${errorHtml}
  <div class="artifact-row">
    <div class="artifact-kv"><span class="artifact-kv-k">Records</span><span class="artifact-kv-v">${a.recordCount.toLocaleString()}</span></div>
    <div class="artifact-kv"><span class="artifact-kv-k">Updated</span><span class="artifact-kv-v">${tdVal(a.generatedAt)}</span></div>
  </div>
  ${fieldsHtml}
  ${detailsHtml}
  ${viewer}
</div>`;
  }).join('');

  return layout('Artifacts', '/artifacts', `
<h1>Data file inventory</h1>
<p>All known verified and published data files. Missing or invalid files are still shown, and raw file paths are available inside each technical details section.</p>
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
    return layout('Player team assignments', '/roster', `
<h1>Player team assignments</h1>
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
  const thead = COLS.map(c => `<th>${esc(humanLabel(c))}</th>`).join('');
  const tbody = pageRows.length
    ? pageRows.map(r => `<tr>${COLS.map(c => `<td>${tdVal(r[c])}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${COLS.length}" class="empty">No records match the current filters.</td></tr>`;

  const pagLinks = buildPager('/roster', currentParams, clampedPage, totalPages);

  const sourceHtml = sourceSummary(a) + technicalDetails('Show source details', [
    { label: 'Artifact file path', value: a.path },
    { label: 'Source summary', value: a.provenance },
    { label: 'Source file', value: a.sourcePath },
    { label: 'Generated from', value: a.generatedFrom },
  ]);

  return layout('Player team assignments', '/roster', `
<h1>Player team assignments</h1>
<p>Use this page to check which NFL team and position each player is tied to in the verified roster file.</p>
${sourceHtml}
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
    return layout('Weekly player box scores', '/ppr', `
<h1>Weekly player box scores</h1>
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
  const thead = COLS.map(c => `<th>${esc(humanLabel(c))}</th>`).join('');
  const tbody = pageRows.length
    ? pageRows.map(r => `<tr>${COLS.map(c => `<td>${tdVal(r[c])}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${COLS.length}" class="empty">No records match the current filters.</td></tr>`;

  const pagLinks = buildPager('/ppr', currentParams, clampedPage, totalPages);

  const sourceHtml = sourceSummary(a) + technicalDetails('Show source details', [
    { label: 'Artifact file path', value: a.path },
    { label: 'Source summary', value: a.provenance },
    { label: 'Source file', value: a.sourcePath },
    { label: 'Generated from', value: a.generatedFrom },
  ]);

  return layout('Weekly player box scores', '/ppr', `
<h1>Weekly player box scores</h1>
<p>Use this page to review verified weekly player box-score inputs. Computed PPR totals are kept in the related computed evidence file listed on the data file inventory page.</p>
${sourceHtml}
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

function goblinPage(query) {
  const a = GOBLIN;
  if (a.status !== 'available') {
    return layout('Research signal review', '/goblin', `
<h1>Research signal review</h1>
${a.status === 'missing'
  ? '<div class="error-box">Artifact not found: ' + esc(a.path) + '</div>'
  : '<div class="error-box">Artifact invalid: ' + esc(a.error) + '</div>'}
<p>These rows highlight source-backed research signals for review. They are not start/sit, trade, ranking, or recommendation outputs.</p>`);
  }

  const nameQ = (query.name || '').trim().toLowerCase();
  const teamQ = query.team || '';
  const posQ = query.position || '';
  const weekQ = query.week || '';
  const legitFlagQ = query.legit_flag || '';
  const grossFlagQ = query.gross_flag || '';
  const page = Math.max(1, parseInt(query.page || '1', 10));
  const legitFlags = uniqueSortedValues(a.records.flatMap(r => Array.isArray(r.legitimate_indicator_flags) ? r.legitimate_indicator_flags : []));
  const grossFlags = uniqueSortedValues(a.records.flatMap(r => Array.isArray(r.gross_output_flags) ? r.gross_output_flags : []));

  let rows = a.records;
  if (nameQ) rows = rows.filter(r => (r.player_name || '').toLowerCase().includes(nameQ));
  if (teamQ) rows = rows.filter(r => String(r.team || '') === teamQ);
  if (posQ) rows = rows.filter(r => String(r.position || '') === posQ);
  if (weekQ) rows = rows.filter(r => String(r.week ?? '') === weekQ);
  if (legitFlagQ) rows = rows.filter(r => Array.isArray(r.legitimate_indicator_flags) && r.legitimate_indicator_flags.includes(legitFlagQ));
  if (grossFlagQ) rows = rows.filter(r => Array.isArray(r.gross_output_flags) && r.gross_output_flags.includes(grossFlagQ));

  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const clampedPage = Math.min(page, totalPages);
  const pageRows = rows.slice((clampedPage - 1) * PAGE_SIZE, clampedPage * PAGE_SIZE);
  const currentParams = { name: nameQ, team: teamQ, position: posQ, week: weekQ, legit_flag: legitFlagQ, gross_flag: grossFlagQ };
  const selectOpts = (opts, val, formatter = displayValue) => ['', ...opts].map(o => `<option value="${esc(o)}" ${o === val ? 'selected' : ''}>${esc(o ? formatter(o) : 'All')}</option>`).join('');
  const signalOptionLabel = value => (SIGNAL_LABELS[value]?.[0] || humanLabel(value));

  const flagCounts = {};
  for (const r of a.records) for (const f of (r.legitimate_indicator_flags || [])) flagCounts[f] = (flagCounts[f] || 0) + 1;
  const uniquePlayers = new Set(a.records.map(r => r.player_id)).size;
  const uniqueTeams = new Set(a.records.map(r => r.team)).size;

  const colVal = (r, key) => {
    const usage = r.usage_snapshot || {};
    if (key in usage) return tdVal(usage[key]);
    if (key === 'target_share' && usage.targets_share !== undefined) return tdVal(usage.targets_share);
    return tdVal(null);
  };

  const COLS = ['season','week','player_name','team','position','ppr_points','legitimate_indicator_flags','gross_output_flags','targets','target_share','air_yards','air_yards_share','rushing_attempts','candidate_score','evidence_status'];
  const tbody = pageRows.length ? pageRows.map(r => `<tr>
<td>${tdVal(r.season)}</td><td>${tdVal(r.week)}</td><td>${tdVal(r.player_name)}</td><td>${tdVal(r.team)}</td><td>${tdVal(r.position)}</td><td>${tdVal(r.ppr_points)}</td>
<td>${signalTags(r.legitimate_indicator_flags)}</td>
<td>${signalTags(r.gross_output_flags)}</td>
<td>${colVal(r,'targets')}</td><td>${colVal(r,'target_share')}</td><td>${colVal(r,'air_yards')}</td><td>${colVal(r,'air_yards_share')}</td><td>${colVal(r,'rushing_attempts')}</td>
<td><span class="null-val">Not calculated</span></td><td>${tdVal(r.evidence_status)}</td></tr>`).join('') : `<tr><td colspan="${COLS.length}" class="empty">No records match the current filters.</td></tr>`;

  const filters = `<form method="GET" action="/goblin"><div class="filters">
  <div class="fg" style="flex:2;min-width:180px"><label>Player name</label><input type="text" name="name" value="${esc(nameQ)}" placeholder="Search name..."></div>
  <div class="fg"><label>Team</label><select name="team">${selectOpts(GOBLIN_TEAMS, teamQ)}</select></div>
  <div class="fg"><label>Position</label><select name="position">${selectOpts(GOBLIN_POSITIONS, posQ)}</select></div>
  <div class="fg"><label>Week</label><select name="week">${selectOpts(GOBLIN_WEEKS, weekQ)}</select></div>
  <div class="fg"><label>Usage support signal</label><select name="legit_flag">${selectOpts(legitFlags, legitFlagQ, signalOptionLabel)}</select></div>
  <div class="fg"><label>Low-output signal</label><select name="gross_flag">${selectOpts(grossFlags, grossFlagQ, signalOptionLabel)}</select></div>
  <button type="submit" class="btn">Filter</button><a href="/goblin" class="btn-ghost">Reset</a></div></form>`;

  const flagSummary = Object.entries(flagCounts).sort((a1, b1) => b1[1] - a1[1]).map(([k,v]) => {
    const [label, tip] = SIGNAL_LABELS[k] || [humanLabel(k), 'Research signal from the source artifact.'];
    return `<li><span class="tag tag-info" title="${esc(tip)}">${esc(label)}</span> ${v.toLocaleString()} rows</li>`;
  }).join('');
  const sourceHtml = sourceSummary(a) + technicalDetails('Technical details', [
    { label: 'Artifact file path', value: a.path },
    { label: 'Generated at', value: a.generatedAt },
  ]);

  return layout('Research signal review', '/goblin', `
<h1>Research signal review</h1>
<p>GOBLIN flags player-weeks where usage patterns didn't match box-score output — for example, a player who saw heavy targets but produced little fantasy value. Each row here is a verified data point flagged for analyst review. These are not start/sit picks, rankings, or trade recommendations.</p>
${sourceHtml}
<div class="stats-grid">
  <div class="stat-card"><div class="stat-val">${a.recordCount.toLocaleString()}</div><div class="stat-lbl">Research rows</div></div>
  <div class="stat-card"><div class="stat-val">${uniquePlayers.toLocaleString()}</div><div class="stat-lbl">Unique players</div></div>
  <div class="stat-card"><div class="stat-val">${uniqueTeams.toLocaleString()}</div><div class="stat-lbl">Unique teams</div></div>
</div>
<div class="artifact-card"><h3>Usage support signal counts</h3><ul>${flagSummary || '<li>No signals present.</li>'}</ul></div>
${filters}
<div class="table-meta">Showing ${((clampedPage-1)*PAGE_SIZE+1).toLocaleString()}–${Math.min(clampedPage*PAGE_SIZE, total).toLocaleString()} of ${total.toLocaleString()} matching rows</div>
<div class="table-wrap"><table><thead><tr>${COLS.map(c => `<th>${esc(humanLabel(c))}</th>`).join('')}</tr></thead><tbody>${tbody}</tbody></table></div>
${buildPager('/goblin', currentParams, clampedPage, totalPages)}`);
}


function isMissing(v) {
  return v === null || v === undefined || v === '';
}

function sumField(rows, field) {
  return rows.reduce((sum, row) => sum + (Number(row[field]) || 0), 0);
}

function avgKnown(rows, field) {
  const vals = rows.map(row => row[field]).filter(v => !isMissing(v)).map(Number).filter(v => !Number.isNaN(v));
  if (!vals.length) return null;
  return vals.reduce((sum, v) => sum + v, 0) / vals.length;
}

function latestKnown(rows, field) {
  for (const row of [...rows].sort((a, b) => Number(b.week || 0) - Number(a.week || 0))) {
    if (!isMissing(row[field])) return row[field];
  }
  return null;
}

function tagCard(tag) {
  return `<div class="artifact-card">
    <div class="artifact-card-header"><span class="artifact-name">${esc(tag.label)}</span><span class="badge ${tag.kind === 'missing' ? 'badge-missing' : 'badge-source'}">${esc(tag.confidence)}</span></div>
    <p style="margin-bottom:8px">${esc(tag.meaning)}</p>
    <div class="artifact-row">
      <div class="artifact-kv"><span class="artifact-kv-k">Trigger</span><span class="artifact-kv-v">${esc(tag.trigger)}</span></div>
      <div class="artifact-kv"><span class="artifact-kv-k">Why it matters</span><span class="artifact-kv-v">${esc(tag.care)}</span></div>
    </div>
  </div>`;
}

function buildInterpretationTags({ usageRows, pprRows }) {
  const tags = [];
  const games = Math.max(usageRows.length, pprRows.length);
  const targets = sumField(usageRows, 'targets');
  const receptions = sumField(usageRows, 'receptions');
  const receivingYards = sumField(pprRows, 'receiving_yards');
  const receivingTds = sumField(pprRows, 'receiving_tds');
  const avgTargetShare = avgKnown(usageRows, 'target_share');
  const avgAirYardsShare = avgKnown(usageRows, 'air_yards_share');
  const latestTargetShare = latestKnown(usageRows, 'target_share');
  const latestAirYardsShare = latestKnown(usageRows, 'air_yards_share');

  if (games < 3) {
    tags.push({ label: 'Small Sample', confidence: 'high', kind: 'source', meaning: 'The source-backed sample has fewer than three player-week rows.', trigger: `${games} available player-week row(s).`, care: 'Treat any role read as early context, not a stable profile.' });
  }
  if (targets >= 30 || (avgTargetShare !== null && avgTargetShare >= 0.22)) {
    tags.push({ label: 'Volume Anchor', confidence: 'medium', kind: 'source', meaning: 'Targets or target share point to meaningful passing-game involvement.', trigger: `${targets} targets; average target share ${avgTargetShare === null ? 'missing' : avgTargetShare.toFixed(2)}.`, care: 'Volume is the cleanest source-backed clue that the offense is intentionally using this player.' });
  }
  if (targets >= 15 && receivingTds === 0) {
    tags.push({ label: 'Box Score Mirage', confidence: 'medium', kind: 'source', meaning: 'Usage exists, but touchdown output has not shown up in these rows.', trigger: `${targets} targets and ${receivingTds} receiving TDs.`, care: 'A plain box score can understate role when opportunities do not become touchdowns.' });
  }
  if (avgAirYardsShare !== null && avgAirYardsShare >= 0.25) {
    tags.push({ label: 'Deep Threat Profile', confidence: 'medium', kind: 'source', meaning: 'Air-yards share suggests a downfield component to the player role.', trigger: `Average air-yards share ${avgAirYardsShare.toFixed(2)}; latest ${latestAirYardsShare === null ? 'missing' : Number(latestAirYardsShare).toFixed(2)}.`, care: 'Downfield usage can create spiky weekly outcomes even when catch volume is uneven.' });
  }
  if (targets >= 20 && receptions / Math.max(targets, 1) < 0.55) {
    tags.push({ label: 'Efficiency Concern', confidence: 'medium', kind: 'source', meaning: 'Catch conversion is low relative to target volume in the selected rows.', trigger: `${receptions} receptions on ${targets} targets.`, care: 'Role may be real, but incomplete passes can make weekly output volatile.' });
  }
  for (const field of ['routes_run', 'route_participation', 'snap_share', 'red_zone_targets']) {
    if (usageRows.length && usageRows.every(row => isMissing(row[field]))) {
      tags.push({ label: 'Missing Data', confidence: 'high', kind: 'missing', meaning: `${humanLabel(field)} is not source-backed in the matched usage rows.`, trigger: `All matched rows have ${field}=null/missing.`, care: 'The UI is intentionally not inferring unsupported role details.' });
    }
  }
  if (!tags.length) {
    tags.push({ label: 'Missing Data', confidence: 'high', kind: 'missing', meaning: 'No deterministic interpretation tag fired from the available fields.', trigger: 'Known thresholds were not met.', care: 'This is an honest empty state, not a negative player evaluation.' });
  }
  return tags.slice(0, 6);
}

function playerLabPage(query) {
  const required = [PPR, USAGE];
  const unavailable = required.find(a => a.status !== 'available');
  if (unavailable) {
    return layout('Player interpretability lab', '/player-lab', `<h1>Player interpretability lab</h1><div class="error-box">Required artifact unavailable: ${esc(unavailable.path)} (${esc(unavailable.status)})</div>`);
  }

  const nameQ = (query.name || '').trim();
  const exactId = query.player_id || '';
  const hasSearch = Boolean(nameQ || exactId);
  const usageCandidates = hasSearch
    ? USAGE.records.filter(r => r.position === 'WR' && (exactId ? r.player_id === exactId : (r.player_name || '').toLowerCase().includes(nameQ.toLowerCase())))
    : [];
  const selected = usageCandidates[0] || null;
  const playerId = selected?.player_id || exactId;
  const usageRows = playerId ? USAGE.records.filter(r => r.player_id === playerId).sort((a,b) => Number(a.week)-Number(b.week)) : [];
  const pprRows = playerId ? PPR.records.filter(r => r.player_id === playerId).sort((a,b) => Number(a.week)-Number(b.week)) : [];
  const computedRows = PPR_COMPUTED.status === 'available' && playerId ? PPR_COMPUTED.records.filter(r => r.player_id === playerId).sort((a,b) => Number(a.week)-Number(b.week)) : [];
  const goblinRows = GOBLIN.status === 'available' && playerId ? GOBLIN.records.filter(r => r.player_id === playerId).sort((a,b) => Number(a.week)-Number(b.week)) : [];

  const suggestions = usageCandidates.slice(0, 8).map(r => `<a class="tag" href="/player-lab?player_id=${encodeURIComponent(r.player_id)}&name=${encodeURIComponent(r.player_name)}">${esc(r.player_name)} · ${esc(r.team)} · ${esc(r.position)}</a>`).join(' ');
  const tags = selected ? buildInterpretationTags({ usageRows, pprRows }) : [];
  const rawPreview = JSON.stringify({ selected_player: selected, usage_rows: usageRows.slice(0, 5), ppr_rows: pprRows.slice(0, 5), computed_rows: computedRows.slice(0, 3), research_rows: goblinRows.slice(0, 3) }, null, 2);

  const statCards = selected ? `<div class="stats-grid">
    <div class="stat-card"><div class="stat-val">${sumField(usageRows, 'targets')}</div><div class="stat-lbl">Targets</div></div>
    <div class="stat-card"><div class="stat-val">${sumField(usageRows, 'receptions')}</div><div class="stat-lbl">Receptions</div></div>
    <div class="stat-card"><div class="stat-val">${sumField(pprRows, 'receiving_yards')}</div><div class="stat-lbl">Receiving yards</div></div>
    <div class="stat-card"><div class="stat-val">${sumField(pprRows, 'receiving_tds')}</div><div class="stat-lbl">Receiving TDs</div></div>
    <div class="stat-card"><div class="stat-val">${avgKnown(usageRows, 'target_share') === null ? '—' : avgKnown(usageRows, 'target_share').toFixed(2)}</div><div class="stat-lbl">Avg target share</div></div>
    <div class="stat-card"><div class="stat-val">${avgKnown(usageRows, 'air_yards_share') === null ? '—' : avgKnown(usageRows, 'air_yards_share').toFixed(2)}</div><div class="stat-lbl">Avg air yards share</div></div>
  </div>` : '';

  return layout('Player interpretability lab', '/player-lab', `
<h1>Player interpretability lab</h1>
<p>Thin read-only scaffold for translating source-backed WR/player rows into deterministic football-language tags. This is not a prediction engine, fantasy lineup assistant, ranking surface, or scoring model.</p>
${sourceSummary({ recordCount: usageRows.length + pprRows.length + computedRows.length + goblinRows.length })}
<form method="GET" action="/player-lab"><div class="filters"><div class="fg" style="flex:2;min-width:220px"><label>WR/player search</label><input type="text" name="name" value="${esc(nameQ)}" placeholder="Search a WR name..."></div><button type="submit" class="btn">Search</button><a href="/player-lab" class="btn-ghost">Reset</a></div></form>
${!hasSearch ? '<div class="empty">Search for a source-backed WR to view deterministic tags and raw rows.</div>' : suggestions ? `<div class="artifact-card"><h3>Matched source-backed WR players</h3><div class="artifact-fields">${suggestions}</div></div>` : '<div class="empty">No source-backed player rows match this search.</div>'}
${selected ? `<h2>${esc(selected.player_name)} · ${esc(selected.team)} · ${esc(selected.position)} · ${esc(selected.season)}</h2>${statCards}<h2>Interpretation tags</h2><div class="section-grid">${tags.map(tagCard).join('')}</div><h2>Raw/source data preview</h2><p>Rows are copied from committed artifacts and truncated for readability. Missing fields stay null/missing.</p><pre class="detail-block" style="white-space:pre-wrap;overflow:auto;max-height:520px">${esc(rawPreview)}</pre>` : ''}`);
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


function flowStatusBadge(status) {
  const label = displayValue(status);
  if (status === 'approved') return `<span class="badge badge-approved">${esc(label)}</span>`;
  if (status === 'review_required') return `<span class="badge badge-review">${esc(label)}</span>`;
  if (status === 'blocked') return `<span class="badge badge-blocked">${esc(label)}</span>`;
  return `<span class="badge badge-fixture">${esc(label)}</span>`;
}

function systemFlowPage(query) {
  const reg = SYSTEM_FLOW_REGISTRY;
  if (reg.status !== 'available') {
    const message = reg.status === 'missing'
      ? `Registry file not found: ${esc(reg.path)}`
      : `Registry file could not be parsed: ${esc(reg.error)}`;
    return layout('System flow registry', '/system-flow', `
<h1>System flow registry</h1>
<p>Read-only inspection surface for the committed TIBER system flow governance registry.</p>
<div class="error-box">${message}</div>`);
  }

  const statusQ = query.status || '';
  const producerQ = query.producer || '';
  const consumerQ = query.consumer || '';
  const authorityQ = query.authority_level || '';
  const sourceLayerQ = query.source_layer || '';

  const options = (vals, selected) => ['', ...vals].map(v => `<option value="${esc(v)}" ${v === selected ? 'selected' : ''}>${esc(v || 'All')}</option>`).join('');
  const producerOpts = uniqueSorted(reg.flows, 'producer_repo');
  const consumerOpts = uniqueSorted(reg.flows, 'consumer_repo');
  const statusOpts = uniqueSorted(reg.flows, 'flow_status');
  const authorityOpts = uniqueSorted(reg.flows, 'authority_level');
  const sourceLayerOpts = uniqueSorted(reg.flows, 'source_layer');

  let rows = reg.flows;
  if (statusQ) rows = rows.filter(r => String(r.flow_status || '') === statusQ);
  if (producerQ) rows = rows.filter(r => String(r.producer_repo || '') === producerQ);
  if (consumerQ) rows = rows.filter(r => String(r.consumer_repo || '') === consumerQ);
  if (authorityQ) rows = rows.filter(r => String(r.authority_level || '') === authorityQ);
  if (sourceLayerQ) rows = rows.filter(r => String(r.source_layer || '') === sourceLayerQ);

  const statusCounts = reg.flows.reduce((acc, flow) => {
    const k = String(flow.flow_status || 'unknown');
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});
  const upstreamCount = reg.flows.filter(f => f.may_feed_back_upstream === true).length;
  const loadedArtifacts = Object.values(ARTIFACTS).filter(a => a.status === 'available').length;
  const missingArtifacts = Object.values(ARTIFACTS).filter(a => a.status !== 'available').length;

  const filters = `<form method="GET" action="/system-flow"><div class="filters">
  <div class="fg"><label>Status</label><select name="status">${options(statusOpts, statusQ)}</select></div>
  <div class="fg"><label>Producer</label><select name="producer">${options(producerOpts, producerQ)}</select></div>
  <div class="fg"><label>Consumer</label><select name="consumer">${options(consumerOpts, consumerQ)}</select></div>
  <div class="fg"><label>Authority level</label><select name="authority_level">${options(authorityOpts, authorityQ)}</select></div>
  <div class="fg"><label>Source layer</label><select name="source_layer">${options(sourceLayerOpts, sourceLayerQ)}</select></div>
  <button type="submit" class="btn">Filter</button><a href="/system-flow" class="btn-ghost">Reset</a>
</div></form>`;

  const table = rows.length ? rows.map(r => `<tr>
<td>${tdVal(r.producer_repo)}</td><td>${tdVal(r.consumer_repo)}</td><td>${tdVal(r.artifact_type)}</td><td>${tdVal(r.source_layer)}</td><td>${tdVal(r.authority_level)}</td><td>${flowStatusBadge(r.flow_status)}</td><td>${tdVal(r.may_feed_back_upstream)}</td><td>${tdVal(r.requires_human_review_if_feedback)}</td><td>${tdVal(r.staleness_policy)}</td><td>${tdVal(r.rollback_path)}</td><td>${tdVal(r.notes)}</td></tr>`).join('') : `<tr><td colspan="11" class="empty">No flows match the current filters.</td></tr>`;

  const rulesTable = reg.globalRules.length ? reg.globalRules.map(rule => `<tr><td>${tdVal(rule.rule_id)}</td><td>${flowStatusBadge(rule.flow_status)}</td><td>${tdVal(rule.description)}</td></tr>`).join('') : '<tr><td colspan="3" class="empty">No global rules found.</td></tr>';

  return layout('System flow registry', '/system-flow', `
<h1>System flow registry</h1>
<p>Read-only inspection surface for the committed TIBER system flow governance registry. This page does not perform remote checks.</p>
<div class="error-box">Truthfulness warning: This registry is a governance contract map. It does not prove downstream repos or APIs are live, does not perform cross-repo health checks, does not authorize runtime coupling, and approved status means governance approval only.</div>
${sourceSummary({recordCount: reg.flows.length})}
<div class="stats-grid">
  <div class="stat-card"><div class="stat-val">${reg.flows.length.toLocaleString()}</div><div class="stat-lbl">Total flows</div></div>
  <div class="stat-card"><div class="stat-val">${(statusCounts.approved || 0).toLocaleString()}</div><div class="stat-lbl">Approved flows</div></div>
  <div class="stat-card"><div class="stat-val">${(statusCounts.review_required || 0).toLocaleString()}</div><div class="stat-lbl">Review-required flows</div></div>
  <div class="stat-card"><div class="stat-val">${(statusCounts.blocked || 0).toLocaleString()}</div><div class="stat-lbl">Blocked flows</div></div>
  <div class="stat-card"><div class="stat-val">${upstreamCount.toLocaleString()}</div><div class="stat-lbl">May feed upstream</div></div>
  <div class="stat-card"><div class="stat-val">${loadedArtifacts.toLocaleString()} / ${missingArtifacts.toLocaleString()}</div><div class="stat-lbl">Artifacts loaded / missing</div></div>
</div>
${filters}
<div class="table-meta">Showing ${rows.length.toLocaleString()} flow rows</div>
<div class="table-wrap"><table><thead><tr><th>Producer repo</th><th>Consumer repo</th><th>Artifact type</th><th>Source layer</th><th>Authority level</th><th>Flow status</th><th>May feed upstream</th><th>Review required if feedback</th><th>Staleness policy</th><th>Rollback path</th><th>Notes</th></tr></thead><tbody>${table}</tbody></table></div>
<h2>Global rules</h2>
<div class="table-wrap"><table><thead><tr><th>Rule ID</th><th>Flow status</th><th>Description</th></tr></thead><tbody>${rulesTable}</tbody></table></div>
<h2>Local evidence viewer routes</h2>
<p>This list describes local viewer endpoints only; it is not proof that downstream repos are online.</p>
<div class="artifact-card"><ul>${LOCAL_VIEWER_ROUTES.map(route => `<li><code class="mono">${route}</code></li>`).join('')}</ul></div>`);
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
<h1>Schema docs &amp; contracts</h1>
<p>
  Field definitions, schema documentation, and data contracts for each file in this repository.
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
    if (pathname === '/goblin') return send(200, 'text/html', goblinPage(query));
    if (pathname === '/player-lab') return send(200, 'text/html', playerLabPage(query));
    if (pathname === '/docs') return send(200, 'text/html', docsPage());
    if (pathname === '/system-flow') return send(200, 'text/html', systemFlowPage(query));

    send(404, 'text/html', layout('Not Found', '', '<h1>404</h1><p>Page not found.</p>'));
  } catch (err) {
    console.error(err);
    send(500, 'text/plain', 'Internal Server Error');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`TIBER-Data Evidence Layer → http://0.0.0.0:${PORT}`);
});
