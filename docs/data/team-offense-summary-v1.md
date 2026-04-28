# Team Offense Summary v1 (Evidence Layer)

Canonical promoted artifact target:

- `exports/promoted/nfl/team_offense_summary_v1.json`

## Scope and mode (initial release)

- mode: `historical_backtest` only
- season: `2025`
- source lane: repo-held offline fixture scaffold only

Committed artifact coverage is fixture-only scaffold data and does not represent full real 2025 league coverage.

This v1 lane is intentionally bounded so Historical Rookie Replay can distinguish **good role in bad offense** from **good role in productive offense** without over-claiming team-level support.

## How this complements team_pace_pass_environment_v1

- `team_pace_pass_environment_v1` captures pace, pass tendency, and target-distribution style context.
- `team_offense_summary_v1` captures output/efficiency quality context (points, yards per play, scoring/turnover rates, and optional advanced efficiency metrics).

Together they form complementary environment context lanes rather than duplicate fields.

## How this supports Historical Rookie Replay environment_supported checks

`historical_rookie_replay_v0` includes `environment_supported` as a replay judgment field.

`team_offense_summary_v1` provides deterministic team quality context rows that replay reviews can inspect when judging whether player usage occurred in a productive or constrained offensive setting.

This scaffold is for bounded evidence inspection only. It does not alter replay scoring or infer unsupported claims.

## Source currently used

- `data/raw/evidence/team_offense_summary_2025.offline_fixture.json`
- source provenance label on every row: `offline_fixture:data/raw/evidence/team_offense_summary_2025.offline_fixture.json`

## Minimum row fields and semantics

- `season` — season key for filtering/export
- `team` — team abbreviation
- `points_per_game` — team points scored per game
- `yards_per_play` — offensive yards gained per snap/play
- `offensive_plays_per_game` — offense run-rate volume
- `touchdowns_per_game` — offensive touchdowns per game
- `scoring_drive_rate` — share of drives ending in points *(nullable)*
- `turnover_rate` — share of drives/plays ending in turnover events
- `offensive_epa_per_play` — signed efficiency signal *(nullable)*
- `offensive_success_rate` — share of plays meeting success criteria *(nullable)*
- `red_zone_td_rate` — red-zone drive touchdown conversion rate *(nullable)*
- `third_down_conversion_rate` — third-down conversion rate *(nullable)*
- `source` — provenance/source_path label from raw wrapper
- `generated_at` — UTC ISO-8601 export timestamp

## Null handling policy for this scaffold

Only these fields are nullable in this scaffold contract:

- `offensive_epa_per_play`
- `offensive_success_rate`
- `scoring_drive_rate`
- `red_zone_td_rate`
- `third_down_conversion_rate`

No additional nullable expansion is allowed unless governance/contracts are updated first.

## Validation and fail-closed behavior

- raw wrapper validation requires `provenance`, `source_path`, and `records`
- export fails closed on duplicate `season/team`
- unsupported mode fails closed (`historical_backtest` only)
- export fails closed when no rows are available for requested season
- `team` must be a non-empty string
- `points_per_game`, `yards_per_play`, `offensive_plays_per_game`, and `touchdowns_per_game` must be nonnegative
- `turnover_rate` must be in `0..1`
- nullable rate fields must be in `0..1` when present:
  - `scoring_drive_rate`
  - `offensive_success_rate`
  - `red_zone_td_rate`
  - `third_down_conversion_rate`
- `offensive_epa_per_play` is signed and bounded to `-1..1` when present
- `generated_at` must parse as ISO-8601 with UTC offset

## Regeneration

```bash
npm run export:team-offense-summary-v1
```
