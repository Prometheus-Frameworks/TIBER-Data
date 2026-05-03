# Player Weekly Usage v1 (Evidence Layer)

Canonical promoted artifact target:

- `exports/promoted/nfl/player_weekly_usage_v1.json`

## Scope and mode (initial release)

- mode: `historical_backtest` only
- season: `2025`
- source lane: repo-held offline fixture support only

Committed artifact coverage is scaffold-only fixture data and does not represent full real 2025 season coverage.

This v1 lane is intentionally bounded to deterministic fixture-backed generation until a governed, reproducible historical source lane is promoted.

## How this complements PPR outcomes

`player_weekly_ppr_outcomes_v1` tells **what** happened in weekly fantasy points.

`player_weekly_usage_v1` provides the first Evidence Layer lane for **why** the outcome happened by exposing weekly opportunity and involvement features:

- receiving usage: `targets`, `receptions`, `routes_run`, `route_participation`, `target_share`, `air_yards`, `air_yards_share`
- rushing usage: `rushing_attempts`, `team_rushing_attempts`, `rush_share`, `red_zone_carries`
- high-value opportunity: `red_zone_targets`
- playing time context: `snap_share`

No scoring changes are introduced in this lane.

## Source currently used

- `data/raw/evidence/player_weekly_usage_2025.offline_fixture.json`
- source provenance label on every row: `offline_fixture:data/raw/evidence/player_weekly_usage_2025.offline_fixture.json`

## Minimum row fields

- `season`
- `week`
- `player_id`
- `player_name`
- `team`
- `position`
- `opponent`
- `targets`
- `receptions`
- `routes_run`
- `route_participation`
- `target_share`
- `air_yards`
- `air_yards_share`
- `rushing_attempts`
- `team_rushing_attempts`
- `rush_share`
- `red_zone_targets`
- `red_zone_carries`
- `snap_share`
- `source`
- `generated_at`

## Validation and fail-closed behavior

- raw wrapper validation requires `provenance`, `source_path`, and `records`
- export fails closed on duplicate `season/week/player_id`
- unsupported mode fails closed (`historical_backtest` only)
- export fails closed when no rows are available for requested season

## Null handling policy for this scaffold

- Offline fixture scaffold rows remain fully populated for deterministic fixture coverage.
- Source-backed rows preserve unavailable source fields as `null` (no fake zeros, no inference).
- `target_share` is bounded to `[0, 1]` when present and may be `null` when unavailable.
- `air_yards_share` may be negative when source-backed receiving air yards are negative; negative values are valid source signal, not an error.

## Missing-week policy

No synthetic missing-week rows are inserted.

## Regeneration

```bash
npm run export:player-weekly-usage-v1
```


## Source lanes
- Default lane: `sourceKind: "offline_fixture"` using `data/raw/evidence/player_weekly_usage_2025.offline_fixture.json`.
- Source-backed lane: `sourceKind: "source_backed"` using `data/processed/evidence/player_weekly_usage_2025.source_backed.json`.
- In source-backed rows, unsupported route/snap/red-zone fields are `null` (unavailable), never inferred and never forced to zero.
