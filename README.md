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
- Gold tables for player role inputs, team context, and explicit compatibility views for the Role-and-opportunity-model client contract.
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
4. derive explicit compatibility outputs from gold inputs without mutating the core raw/silver/gold contracts
5. validate schema and basic quality constraints before succeeding

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
- `GET /api/players` with optional `team`, `season`, `position`, and `player_id` filters
- `GET /api/team-context` with optional `team`, `season`, and `week` filters
- `GET /api/team-context/{team}`
- `GET /api/player-role-inputs` with optional `team`, `season`, `week`, `position`, and `player_id` filters
- `GET /api/player-role-inputs/{player_id}`
- `GET /api/compatibility/player-role-profiles` with optional `team`, `season`, `week`, `position`, and `player_id` filters
- `GET /api/compatibility/player-role-profiles/{player_id}`
- `GET /api/compatibility/team-opportunity-context` with optional `team`, `season`, and `week` filters
- `GET /api/compatibility/team-opportunity-context/{team}`

### Example requests

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/teams
curl http://127.0.0.1:8000/api/players
curl "http://127.0.0.1:8000/api/players?team=BAL&season=2024&position=WR"
curl http://127.0.0.1:8000/api/team-context
curl "http://127.0.0.1:8000/api/team-context?team=BAL&season=2024&week=1"
curl http://127.0.0.1:8000/api/team-context/BAL
curl http://127.0.0.1:8000/api/player-role-inputs
curl "http://127.0.0.1:8000/api/player-role-inputs?team=BAL&season=2024&week=1&position=WR"
curl http://127.0.0.1:8000/api/player-role-inputs/00-0037834
curl http://127.0.0.1:8000/api/compatibility/player-role-profiles
curl "http://127.0.0.1:8000/api/compatibility/player-role-profiles?team=BAL&season=2024&week=1&position=WR"
curl http://127.0.0.1:8000/api/compatibility/player-role-profiles/00-0037834
curl http://127.0.0.1:8000/api/compatibility/team-opportunity-context
curl "http://127.0.0.1:8000/api/compatibility/team-opportunity-context?team=BAL&season=2024&week=1"
curl http://127.0.0.1:8000/api/compatibility/team-opportunity-context/BAL
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
- `data/gold/player_role_profile_compatibility_weekly.parquet`
- `data/gold/team_opportunity_context_compatibility_weekly.parquet`

## Compatibility layer contract

The compatibility layer is intentionally explicit and additive. It does **not** rename or muddy the core gold tables. Instead, it publishes separate gold compatibility views that line up with the client-facing shapes used by `Role-and-opportunity-model`.

### Player role profile compatibility output

`data/gold/player_role_profile_compatibility_weekly.parquet` and `/api/compatibility/player-role-profiles` expose:

- directly carried or renamed fields: `player_id`, `player_name`, `position`, `target_share`
- deterministic weekly derivations: `air_yard_share`, `route_participation`, `red_zone_target_share`, `average_depth_of_target`, `competition_for_role`
- season-level deterministic carry-forward: `vacated_targets_available`
- explicit null placeholders when the public source does not honestly support the field yet: `slot_rate`, `inline_rate`, `wide_rate`, `first_read_share`, `explosive_target_rate`, `personnel_versatility`, `injury_risk`

### Team opportunity context compatibility output

`data/gold/team_opportunity_context_compatibility_weekly.parquet` and `/api/compatibility/team-opportunity-context` expose:

- directly carried or joined fields: `team_id`, `team_name`
- deterministic weekly derivations: `pace_index`, `target_competition_index`
- season-level deterministic carry-forward: `vacated_target_share`
- explicit null placeholders where play-by-play, coaching, or QB continuity data are not yet supported in the current public path: `pass_rate_over_expected`, `neutral_pass_rate`, `red_zone_pass_rate`, `quarterback_stability`, `play_caller_continuity`, `receiver_room_certainty`

### Compatibility derivation rules

- `red_zone_target_share`: player red-zone targets divided by the summed team red-zone targets for the same team-week when public red-zone targets exist; otherwise null.
- `average_depth_of_target`: player air yards divided by player targets when both are available and targets are positive.
- `competition_for_role`: same-team, same-position target share total minus the player’s own target share for that week. This is a deterministic proxy for same-room role competition rather than a tracking-grade alignment metric.
- `pace_index`: team `pace_proxy` divided by the league average `pace_proxy` for the same season-week.
- `vacated_target_share` / `vacated_targets_available`: prior-season team targets earned by players absent from the current season roster, divided by the prior-season team target total. This is only derivable when adjacent seasons are present in the ingest window; otherwise it remains null.

## Column honesty rules

The docs and code use four practical states for fields:

- **real**: directly sourced from the public ingest path.
- **derived**: computed deterministically from real inputs.
- **null_when_unavailable**: kept null if the public source does not cleanly expose it.
- **pending**: intentionally reserved for later public derivation work.

This keeps the repo from pretending it already has routes, tracking, or red-zone participation when those fields are not reliably available from the current public path.

## Known limitations

- The current weekly silver/gold outputs keep regular-season weeks only. Postseason support should add an explicit `season_type` field before widening scope.
- `routes_run`, `route_share`, `snap_share`, `yprr`, `tprr`, `pass_rate_over_expected`, `neutral_pass_rate`, `red_zone_pass_rate`, `qb_epa_per_dropback`, `quarterback_stability`, `play_caller_continuity`, and `receiver_room_certainty` remain null/pending until a stable public source is added.
- Compatibility alignment-style fields such as `slot_rate`, `inline_rate`, `wide_rate`, and `first_read_share` remain explicit nulls rather than fabricated estimates.
- `team_air_yards` uses official team stats when present and otherwise falls back to player-level summed air yards.
- `fantasy_points_ppr` is passed through when the source provides it; otherwise it is computed deterministically from passing, rushing, and receiving box-score stats.
- Offline fixtures remain available only as a restricted-environment fallback for local testing or CI. They are not the main ingest path.
