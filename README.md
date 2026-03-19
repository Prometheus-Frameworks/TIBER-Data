# TIBER-Data

TIBER-Data is the shared football data foundation for downstream TIBER model repositories. PR2 makes the public ingest path real and deterministic so the repository can produce trustworthy silver and gold outputs from actual public NFL data instead of placeholder URLs or method-guessing logic.

## Why this repo exists

Downstream role, opportunity, projection, and ranking models need one deterministic place to pull curated football tables from. This repository establishes that backbone with three explicit layers:

- **raw**: minimally touched source pulls written to disk for auditability.
- **silver**: normalized canonical tables with stable column contracts.
- **gold**: first-pass model-ready tables derived from silver tables.

That layered split keeps ingestion logic, normalization logic, and model-ready derivations from collapsing into one pile of sludge.

## Project layout

```text
data/
  raw/
  silver/
  gold/
docs/
  schemas/
scripts/
src/
  config/
  ingest/
  transform/
  derive/
  utils/
```

## Scope of the current pipeline

Included in this pipeline:

- Python ETL scaffold using `polars`, `pyarrow`, and optional `nflreadpy`.
- Canonical schema docs for the first foundational tables.
- Deterministic public-data ingest entrypoints for players, teams, weekly player stats, and team-week context.
- Silver tables for players, weekly player stats, and weekly team stats.
- Gold tables for player role inputs and team context.
- Lightweight validation checks for required columns, duplicate keys, and non-negative numeric metrics.
- One command entrypoint to run the pipeline end to end.

Explicitly out of scope for this repo version:

- databases or warehouse infrastructure
- cloud deployment
- auth
- ML/model training
- expansive historical backfill beyond configured seasons
- fabricated tracking-grade metrics where public data is not yet cleanly available

## Installation

Create a Python 3.10+ environment and install the package with dependencies:

```bash
python -m pip install -e .
```

## Supported public ingest path

The pipeline now uses explicit documented public source paths.

### Preferred loader when available

If `nflreadpy` is installed and working, the ingest client uses these explicit functions:

- `nflreadpy.load_rosters(seasons=..., file_type="parquet")`
- `nflreadpy.load_player_stats(seasons=..., summary_level="week", file_type="parquet")`
- `nflreadpy.load_team_stats(seasons=..., summary_level="week", file_type="parquet")`
- `nflreadpy.load_teams()`

### Stable direct public fallback

If `nflreadpy` is unavailable, the pipeline falls back to direct public nflverse paths:

- players season snapshots: `https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.parquet`
- weekly player stats: `https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.parquet`
- weekly team stats / team-week context: `https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_{season}.parquet`
- team metadata: `https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/teams_colors_logos.csv`

The current silver and gold weekly outputs are **regular-season only** because the canonical schema does not yet carry `season_type`.

There is no placeholder ingest URL in the main path anymore.

## Run the pipeline

```bash
python -m src.main --overwrite
```

Optional flags:

```bash
python -m src.main --season 2024 --overwrite
python -m src.main --seasons 2023 2024 --overwrite
python -m src.main --season 2024 --disable-offline-fallback
```

The pipeline will:

1. ingest source data into `data/raw/`
2. normalize canonical parquet tables into `data/silver/`
3. derive first-pass gold tables into `data/gold/`
4. validate schema and basic quality constraints before succeeding

## Run the read-only API

After you have produced parquet outputs in `data/silver/` and `data/gold/`, start the API with:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Recommended local flow:

```bash
python -m src.main --overwrite
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

The API is intentionally small and read-only. It reads directly from the existing parquet outputs and does not use a database, auth layer, or write path. If required parquet files are missing, endpoints fail clearly with a `503` response that names the missing dataset and path.

### Endpoints

- `GET /health`
- `GET /api/teams`
- `GET /api/players`
- `GET /api/team-context`
- `GET /api/team-context/{team}`
- `GET /api/player-role-inputs`
- `GET /api/player-role-inputs/{player_id}`

### Example requests

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/teams
curl http://127.0.0.1:8000/api/players
curl http://127.0.0.1:8000/api/team-context
curl http://127.0.0.1:8000/api/team-context/BAL
curl http://127.0.0.1:8000/api/player-role-inputs
curl http://127.0.0.1:8000/api/player-role-inputs/00-0037834
```

Each API response returns simple JSON in this shape:

```json
{
  "dataset": "teams",
  "count": 32,
  "data": [
    {
      "team": "ARI",
      "team_name": "Cardinals",
      "conference": "NFC",
      "division": "West"
    }
  ]
}
```

## Tables produced

### Silver

- `data/silver/players.parquet`
- `data/silver/teams.parquet`
- `data/silver/weekly_player_stats.parquet`
- `data/silver/weekly_team_stats.parquet`

### Gold

- `data/gold/player_role_inputs_weekly.parquet`
- `data/gold/team_context_weekly.parquet`

## Column honesty rules

The docs and code use four practical states for fields:

- **real**: directly sourced from the public ingest path.
- **derived**: computed deterministically from real inputs.
- **null_when_unavailable**: kept null if the public source does not cleanly expose it.
- **pending**: intentionally reserved for later public derivation work.

This keeps the repo from pretending it already has routes, tracking, or red-zone participation when those fields are not reliably available from the current public path.

## Known limitations

- The current weekly silver/gold outputs keep regular-season weeks only. Postseason support should add an explicit `season_type` field before widening scope.
- `red_zone_targets`, `routes_run`, `route_share`, `snap_share`, `yprr`, `tprr`, `neutral_pass_rate`, `red_zone_pass_rate`, `qb_epa_per_dropback`, and `receiver_room_certainty` remain null/pending until a stable public source is added.
- `team_air_yards` uses official team stats when present and otherwise falls back to player-level summed air yards.
- `fantasy_points_ppr` is passed through when the source provides it; otherwise it is computed deterministically from passing, rushing, and receiving box-score stats.
- Offline fixtures remain available only as a restricted-environment fallback for local testing or CI. They are not the main ingest path.
