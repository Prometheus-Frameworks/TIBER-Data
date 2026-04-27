# Evidence Layer v0 Contract Shapes

This document defines the initial contract-level artifact shapes for the TIBER Evidence Layer v0 doctrine.

Scope in this PR is documentation-level contract specification only.

## Canonical artifact targets

- `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`
- `exports/promoted/nfl/team_offense_summary_v1.json`
- `exports/promoted/nfl/team_pace_pass_environment_v1.json`
- `exports/promoted/nfl/roster_player_team_map_v1.json`
- `exports/promoted/nfl/coaching_staff_context_v1.json`

## General contract expectations (all artifacts)

- Artifact payload is deterministic and versioned by filename suffix (`_v1`).
- Each row includes source/provenance metadata sufficient for downstream inspection.
- Null is preferred over synthetic imputation when an optional source field is unavailable.
- `generated_at` must use ISO-8601 UTC timestamp format.

## `player_weekly_ppr_outcomes_v1`

Canonical file: `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`

Minimum row fields:

- `season`
- `week`
- `player_id`
- `player_name`
- `team`
- `position`
- `opponent`
- `receptions`
- `targets`
- `receiving_yards`
- `receiving_tds`
- `rushing_attempts`
- `rushing_yards`
- `rushing_tds`
- `passing_yards`
- `passing_tds`
- `interceptions`
- `ppr_points`
- `rolling_3_week_ppr`
- `rolling_5_week_ppr`
- `season_ppr`
- `games_played`
- `source`
- `generated_at`

## `player_weekly_usage_v1`

Canonical file: `exports/promoted/nfl/player_weekly_usage_v1.json`

Minimum row fields:

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

## `team_pace_pass_environment_v1`

Canonical file: `exports/promoted/nfl/team_pace_pass_environment_v1.json`

Minimum row fields:

- `season`
- `team`
- `plays_per_game`
- `neutral_pass_rate`
- `pass_rate_over_expected` *(nullable: `null` when unavailable)*
- `dropbacks_per_game`
- `seconds_per_snap` *(nullable: `null` when unavailable)*
- `red_zone_pass_rate`
- `wr_target_share`
- `te_target_share`
- `rb_target_share`
- `source`
- `generated_at`

## `coaching_staff_context_v1`

Canonical file: `exports/promoted/nfl/coaching_staff_context_v1.json`

Minimum row fields:

- `season`
- `team`
- `head_coach`
- `offensive_coordinator`
- `play_caller`
- `source`
- `source_status`
- `notes`
- `generated_at`

## Remaining v0 artifacts (shape declaration pending deeper field freeze)

The following artifacts are in-scope for Evidence Layer v0 governance, with field-level schemas to be frozen in follow-on contract revisions:

- `exports/promoted/nfl/team_offense_summary_v1.json`
- `exports/promoted/nfl/roster_player_team_map_v1.json`

Until field freeze, downstream consumers must treat these as declared canonical targets but not infer undocumented columns.
