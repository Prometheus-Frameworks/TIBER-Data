# Roster Player Team Map v1 (Evidence Layer)

Canonical promoted artifact target:

- `exports/promoted/nfl/roster_player_team_map_v1.json`

Source-backed raw lane path:

- `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

## Scope and mode (initial release)

- mode: `historical_backtest` only
- season: `2025`
- source lane: repo-held offline fixture scaffold only
- cohort: small bounded fixture subset only

Committed artifact coverage is fixture-only scaffold data and does **not** represent full real 2025 NFL roster coverage.

This lane is an identity/referee layer for Evidence Layer joins. Downstream repos must not invent missing player/team mappings when source truth is absent.

## Source currently used

- `data/raw/evidence/roster_player_team_map_2025.offline_fixture.json`
- source provenance label on every row: `offline_fixture:data/raw/evidence/roster_player_team_map_2025.offline_fixture.json`

## Source-backed transition

This export now supports explicit source-lane selection through `sourceKind`:

- `offline_fixture` (default): existing scaffold lane, unchanged
- `source_backed`: expects `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

### 2025 source audit + ingestion status

- Audit baseline: `docs/data/roster-player-team-map-source-audit-2025.md`
- Approved ingestion lane doc: `docs/data/roster-player-team-map-source-backed-2025.md`
- Source-backed generator: `scripts/build_roster_player_team_map_source_backed_2025.py`

Boundary decisions preserved:

- default promoted behavior remains fixture lane (`offline_fixture`)
- source-backed lane is explicit (`sourceKind=source_backed`) and still fail-closed if file is missing
- no synthetic rows or fabricated IDs are permitted
- `active_roster_status` remains `unknown` for current nflreadpy v1 ingest lane

## Field semantics

- `season` — NFL season
- `week` — NFL week
- `player_id` — stable player identifier where available (fixture IDs are permitted in this bounded scaffold)
- `player_name` — display name
- `position` — one of `QB`, `RB`, `WR`, `TE`
- `team` — NFL abbreviation
- `active_roster_status` — one of `active`, `inactive`, `practice_squad`, `injured_reserve`, `unknown`, `fixture_only`
- `source_status` — one of `offline_fixture`, `source_verified`, `needs_verification`, `stale_or_missing_data`
- `source` — provenance/source_path label from raw wrapper
- `generated_at` — UTC ISO-8601 export timestamp

## Validation and fail-closed behavior

- raw wrapper validation requires `provenance`, `source_path`, and `records`
- unsupported mode fails closed (`historical_backtest` only)
- export fails closed on duplicate `season/week/player_id`
- export fails closed when no rows are available for requested season
- `season` must be a nonnegative integer
- `week` must be a positive integer
- `player_id` must be a non-empty string
- `player_name` must be a non-empty string
- `position` must be one of `QB/RB/WR/TE`
- `team` must be a non-empty string
- `active_roster_status` must be one of:
  - `active`
  - `inactive`
  - `practice_squad`
  - `injured_reserve`
  - `unknown`
  - `fixture_only`
- `source_status` must be one of:
  - `offline_fixture`
  - `source_verified`
  - `needs_verification`
  - `stale_or_missing_data`
- `generated_at` must parse as an ISO-8601 UTC string

## Regeneration

```bash
python scripts/build_roster_player_team_map_source_backed_2025.py
npm run export:roster-player-team-map-v1
```
