# Team Pace/Pass Environment v1 (Evidence Layer)

Canonical promoted artifact target:

- `exports/promoted/nfl/team_pace_pass_environment_v1.json`

## Scope and mode (initial release)

- mode: `historical_backtest` only
- season: `2025`
- source lane: repo-held offline fixture scaffold only

Committed artifact coverage is fixture-only scaffold data and does not represent full real 2025 league coverage.

This v1 lane is intentionally bounded so Historical Rookie Replay can evaluate **environment-supported context** without claiming complete team-level truth coverage.

## How this supports Historical Rookie Replay

`historical_rookie_replay_v0` includes `environment_supported` as a replay judgment field.

`team_pace_pass_environment_v1` provides deterministic team context inputs that can be inspected alongside replay rows:

- offense volume context: `plays_per_game`, `dropbacks_per_game`
- pass tendency context: `neutral_pass_rate`, `pass_rate_over_expected`, `red_zone_pass_rate`
- target distribution context: `wr_target_share`, `te_target_share`, `rb_target_share`
- pace context: `seconds_per_snap`

This scaffold is for bounded evidence inspection only. It does not alter replay scoring or infer unsupported claims.

## Source currently used

- `data/raw/evidence/team_pace_pass_environment_2025.offline_fixture.json`
- source provenance label on every row: `offline_fixture:data/raw/evidence/team_pace_pass_environment_2025.offline_fixture.json`

## Minimum row fields

- `season`
- `team`
- `plays_per_game`
- `neutral_pass_rate`
- `pass_rate_over_expected` *(nullable)*
- `dropbacks_per_game`
- `seconds_per_snap` *(nullable)*
- `red_zone_pass_rate`
- `wr_target_share`
- `te_target_share`
- `rb_target_share`
- `source`
- `generated_at`

## Validation and fail-closed behavior

- raw wrapper validation requires `provenance`, `source_path`, and `records`
- export fails closed on duplicate `season/team`
- unsupported mode fails closed (`historical_backtest` only)
- export fails closed when no rows are available for requested season
- all rate/share fields must be in `0..1` when non-null:
  - `neutral_pass_rate`
  - `pass_rate_over_expected`
  - `red_zone_pass_rate`
  - `wr_target_share`
  - `te_target_share`
  - `rb_target_share`

## Null handling policy for this scaffold

Only these fields are nullable in this scaffold contract:

- `pass_rate_over_expected`
- `seconds_per_snap`

No additional nullable expansion is allowed unless governance docs are updated first.

## Regeneration

```bash
npm run export:team-pace-pass-environment-v1
```
