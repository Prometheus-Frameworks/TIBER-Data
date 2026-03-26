from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from src.config.settings import build_config
from src.utils.frames import require_polars

app = FastAPI(title="TIBER-Data API", version="0.1.0")

DATASETS = {
    "teams": build_config().silver_dir / "teams.parquet",
    "players": build_config().silver_dir / "players.parquet",
    "team_context": build_config().gold_dir / "team_context_weekly.parquet",
    "player_role_inputs": build_config().gold_dir / "player_role_inputs_weekly.parquet",
    "player_role_profile_compatibility": build_config().gold_dir
    / "player_role_profile_compatibility_weekly.parquet",
    "team_opportunity_context_compatibility": build_config().gold_dir
    / "team_opportunity_context_compatibility_weekly.parquet",
}


def _missing_dataset_response(dataset: str, path: Path) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "error": "parquet_output_missing",
            "dataset": dataset,
            "path": str(path),
            "message": f"Missing parquet output for '{dataset}'. Run the pipeline first.",
        },
    )


def _load_dataset(dataset: str) -> Any:
    path = DATASETS[dataset]
    if not path.exists():
        raise _missing_dataset_response(dataset, path)
    pl = require_polars()
    return pl.read_parquet(path)


def _records_response(dataset: str, records: list[dict[str, Any]]) -> JSONResponse:
    return JSONResponse(content={"dataset": dataset, "count": len(records), "data": records})


def _apply_filters(frame: Any, filters: dict[str, Any]) -> Any:
    pl = require_polars()
    filtered = frame
    for column, value in filters.items():
        if value is None:
            continue
        if column in {"team", "position"}:
            filtered = filtered.filter(pl.col(column).str.to_uppercase() == str(value).upper())
            continue
        filtered = filtered.filter(pl.col(column) == value)
    return filtered


@app.get("/health")
def health() -> JSONResponse:
    missing = [
        {"dataset": dataset, "path": str(path)}
        for dataset, path in DATASETS.items()
        if not path.exists()
    ]
    if missing:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "One or more parquet outputs are missing. Run the pipeline first.",
                "missing": missing,
            },
        )
    return JSONResponse(
        content={
            "status": "ok",
            "datasets": {dataset: str(path) for dataset, path in DATASETS.items()},
        }
    )


@app.get("/api/teams")
def get_teams() -> JSONResponse:
    frame = _load_dataset("teams")
    return _records_response("teams", frame.to_dicts())


@app.get("/api/players")
def get_players(
    team: str | None = Query(default=None),
    season: int | None = Query(default=None),
    player_id: str | None = Query(default=None),
    position: str | None = Query(default=None),
) -> JSONResponse:
    frame = _load_dataset("players")
    filtered = _apply_filters(
        frame,
        {
            "team": team,
            "season": season,
            "player_id": player_id,
            "position": position,
        },
    )
    return _records_response("players", filtered.to_dicts())


@app.get("/api/team-context")
def get_team_context(
    team: str | None = Query(default=None),
    season: int | None = Query(default=None),
    week: int | None = Query(default=None),
) -> JSONResponse:
    frame = _load_dataset("team_context")
    filtered = _apply_filters(
        frame,
        {
            "team": team,
            "season": season,
            "week": week,
        },
    )
    return _records_response("team_context", filtered.to_dicts())


@app.get("/api/team-context/{team}")
def get_team_context_for_team(team: str) -> JSONResponse:
    frame = _load_dataset("team_context")
    filtered = _apply_filters(frame, {"team": team})
    if filtered.height == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "team_not_found",
                "team": team,
                "message": f"No team context rows found for team '{team}'.",
            },
        )
    return _records_response("team_context", filtered.to_dicts())


@app.get("/api/player-role-inputs")
def get_player_role_inputs(
    team: str | None = Query(default=None),
    season: int | None = Query(default=None),
    week: int | None = Query(default=None),
    position: str | None = Query(default=None),
    player_id: str | None = Query(default=None),
) -> JSONResponse:
    frame = _load_dataset("player_role_inputs")
    filtered = _apply_filters(
        frame,
        {
            "team": team,
            "season": season,
            "week": week,
            "position": position,
            "player_id": player_id,
        },
    )
    return _records_response("player_role_inputs", filtered.to_dicts())


@app.get("/api/player-role-inputs/{player_id}")
def get_player_role_inputs_for_player(player_id: str) -> JSONResponse:
    frame = _load_dataset("player_role_inputs")
    filtered = _apply_filters(frame, {"player_id": player_id})
    if filtered.height == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "player_not_found",
                "player_id": player_id,
                "message": f"No player role input rows found for player_id '{player_id}'.",
            },
        )
    return _records_response("player_role_inputs", filtered.to_dicts())


@app.get("/api/compatibility/player-role-profiles")
def get_player_role_profile_compatibility(
    team: str | None = Query(default=None),
    season: int | None = Query(default=None),
    week: int | None = Query(default=None),
    position: str | None = Query(default=None),
    player_id: str | None = Query(default=None),
) -> JSONResponse:
    frame = _load_dataset("player_role_profile_compatibility")
    filtered = _apply_filters(
        frame,
        {
            "team": team,
            "season": season,
            "week": week,
            "position": position,
            "player_id": player_id,
        },
    )
    return _records_response("player_role_profile_compatibility", filtered.to_dicts())


@app.get("/api/compatibility/player-role-profiles/{player_id}")
def get_player_role_profile_compatibility_for_player(player_id: str) -> JSONResponse:
    frame = _load_dataset("player_role_profile_compatibility")
    filtered = _apply_filters(frame, {"player_id": player_id})
    if filtered.height == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "player_not_found",
                "player_id": player_id,
                "message": f"No compatibility rows found for player_id '{player_id}'.",
            },
        )
    return _records_response("player_role_profile_compatibility", filtered.to_dicts())


@app.get("/api/compatibility/team-opportunity-context")
def get_team_opportunity_context_compatibility(
    team: str | None = Query(default=None),
    season: int | None = Query(default=None),
    week: int | None = Query(default=None),
) -> JSONResponse:
    frame = _load_dataset("team_opportunity_context_compatibility")
    filtered = _apply_filters(
        frame,
        {
            "team": team,
            "season": season,
            "week": week,
        },
    )
    return _records_response("team_opportunity_context_compatibility", filtered.to_dicts())


@app.get("/api/compatibility/team-opportunity-context/{team}")
def get_team_opportunity_context_compatibility_for_team(team: str) -> JSONResponse:
    frame = _load_dataset("team_opportunity_context_compatibility")
    filtered = _apply_filters(frame, {"team": team})
    if filtered.height == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "team_not_found",
                "team": team,
                "message": f"No compatibility rows found for team '{team}'.",
            },
        )
    return _records_response("team_opportunity_context_compatibility", filtered.to_dicts())


@app.get("/api/players/search")
def search_players(name: str = Query(..., min_length=1)) -> JSONResponse:
    frame = _load_dataset("players")
    pl = require_polars()
    filtered = frame.filter(pl.col("full_name").str.to_lowercase().str.contains(name.lower()))
    return _records_response("players", filtered.to_dicts())


@app.get("/api/player/{player_id}/all")
def get_player_all(player_id: str) -> JSONResponse:
    pl = require_polars()
    result: dict[str, Any] = {}
    for dataset in ["players", "player_role_inputs", "player_role_profile_compatibility"]:
        try:
            frame = _load_dataset(dataset)
            result[dataset] = frame.filter(pl.col("player_id") == player_id).to_dicts()
        except HTTPException:
            result[dataset] = []
    return JSONResponse(content={"player_id": player_id, "data": result})


_HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TIBER-Data Player Search</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: monospace; background: #0f0f0f; color: #e0e0e0; min-height: 100vh; padding: 2rem; }
  h1 { font-size: 1.1rem; color: #888; margin-bottom: 1.5rem; letter-spacing: 0.05em; }
  #search-form { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
  input[type=text] { flex: 1; max-width: 400px; padding: 0.5rem 0.75rem; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; font-family: monospace; font-size: 0.95rem; outline: none; }
  input[type=text]:focus { border-color: #555; }
  button { padding: 0.5rem 1rem; background: #222; border: 1px solid #444; color: #ccc; font-family: monospace; font-size: 0.95rem; cursor: pointer; }
  button:hover { background: #2a2a2a; }
  #matches { margin-bottom: 1.5rem; }
  .match-item { padding: 0.4rem 0.6rem; cursor: pointer; border-left: 2px solid transparent; color: #aaa; font-size: 0.9rem; }
  .match-item:hover, .match-item.active { border-left-color: #666; color: #e0e0e0; background: #1a1a1a; }
  #output { display: none; }
  .section { margin-bottom: 2rem; }
  .section-title { font-size: 0.75rem; color: #555; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.75rem; border-bottom: 1px solid #1e1e1e; padding-bottom: 0.4rem; }
  .profile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.4rem 1rem; }
  .kv { font-size: 0.85rem; }
  .kv .k { color: #555; }
  .kv .v { color: #ccc; }
  table { border-collapse: collapse; font-size: 0.78rem; width: 100%; overflow-x: auto; display: block; }
  th { color: #555; font-weight: normal; text-align: left; padding: 0.3rem 0.6rem; border-bottom: 1px solid #1e1e1e; white-space: nowrap; }
  td { padding: 0.25rem 0.6rem; color: #bbb; white-space: nowrap; }
  tr:hover td { background: #141414; }
  #status { color: #555; font-size: 0.85rem; margin-bottom: 1rem; }
</style>
</head>
<body>
<h1>TIBER-DATA / player search</h1>
<form id="search-form">
  <input type="text" id="name-input" placeholder="player name..." autocomplete="off" autofocus>
  <button type="submit">search</button>
</form>
<div id="status"></div>
<div id="matches"></div>
<div id="output">
  <div class="section" id="section-profile">
    <div class="section-title">profile</div>
    <div class="profile-grid" id="profile-grid"></div>
  </div>
  <div class="section" id="section-role-inputs">
    <div class="section-title">role inputs (weekly)</div>
    <div id="role-inputs-table"></div>
  </div>
  <div class="section" id="section-compatibility">
    <div class="section-title">role profile compatibility (weekly)</div>
    <div id="compatibility-table"></div>
  </div>
</div>
<script>
function fmt(v) {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(3);
  return v;
}

function renderKV(container, obj) {
  container.innerHTML = '';
  for (const [k, v] of Object.entries(obj)) {
    const el = document.createElement('div');
    el.className = 'kv';
    el.innerHTML = '<span class="k">' + k + '</span>: <span class="v">' + fmt(v) + '</span>';
    container.appendChild(el);
  }
}

function renderTable(container, rows) {
  container.innerHTML = '';
  if (!rows.length) { container.textContent = 'no data'; return; }
  const keys = Object.keys(rows[0]);
  const table = document.createElement('table');
  const thead = table.createTHead();
  const hr = thead.insertRow();
  keys.forEach(k => { const th = document.createElement('th'); th.textContent = k; hr.appendChild(th); });
  const tbody = table.createTBody();
  rows.forEach(row => {
    const tr = tbody.insertRow();
    keys.forEach(k => { const td = tr.insertCell(); td.textContent = fmt(row[k]); });
  });
  container.appendChild(table);
}

async function loadPlayer(playerId) {
  document.getElementById('status').textContent = 'loading...';
  document.getElementById('output').style.display = 'none';
  const res = await fetch('/api/player/' + encodeURIComponent(playerId) + '/all');
  const json = await res.json();
  const d = json.data;

  const profile = d.players?.[0] ?? {};
  renderKV(document.getElementById('profile-grid'), profile);
  renderTable(document.getElementById('role-inputs-table'), d.player_role_inputs ?? []);
  renderTable(document.getElementById('compatibility-table'), d.player_role_profile_compatibility ?? []);

  document.getElementById('output').style.display = 'block';
  document.getElementById('status').textContent = '';
}

document.getElementById('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('name-input').value.trim();
  if (!name) return;
  document.getElementById('matches').innerHTML = '';
  document.getElementById('output').style.display = 'none';
  document.getElementById('status').textContent = 'searching...';
  const res = await fetch('/api/players/search?name=' + encodeURIComponent(name));
  const json = await res.json();
  const players = json.data ?? [];
  document.getElementById('status').textContent = players.length ? players.length + ' result(s)' : 'no results';
  if (players.length === 1) {
    loadPlayer(players[0].player_id);
    return;
  }
  const matchesEl = document.getElementById('matches');
  const seen = new Set();
  players.forEach(p => {
    if (seen.has(p.player_id)) return;
    seen.add(p.player_id);
    const el = document.createElement('div');
    el.className = 'match-item';
    el.textContent = p.full_name + '  ' + (p.position ?? '') + '  ' + (p.team ?? '');
    el.addEventListener('click', () => {
      document.querySelectorAll('.match-item').forEach(x => x.classList.remove('active'));
      el.classList.add('active');
      loadPlayer(p.player_id);
    });
    matchesEl.appendChild(el);
  });
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def ui() -> str:
    return _HTML_UI
