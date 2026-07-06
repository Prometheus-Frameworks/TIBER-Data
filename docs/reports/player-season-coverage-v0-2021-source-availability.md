# Source-Availability Report: `player_season_coverage_v0` — 2021 REG

- **Generated at:** 2026-07-05T22:47:32.675896+00:00
- **Tracking issue:** TIBER-Data#198
- **Forecast context (not source authority):** Prometheus-Frameworks/TIBER-Forecast#133, Prometheus-Frameworks/TIBER-Forecast#134 (merged 2517270)
- **Status:** `source_availability_evidence_report_not_an_artifact`
- **Scope:** season 2021, season_type REG, positions QB/RB/WR/TE, approved source family only (`nflreadpy.load_player_stats`, `nflreadpy.load_players`). This report is evidence only: it is **not** a candidate artifact, **not** a promoted artifact, and authorizes **no** Forecast behavior.

## Sources inspected

- `nflreadpy.load_player_stats(seasons=[2021], summary_level='week')`
- `nflreadpy.load_player_stats(seasons=[2021], summary_level='reg')`
- `nflreadpy.load_players()`

## 2021 REG availability

- Week-level rows (all season types): 18969
- Week-level rows (REG): 18128
- REG-summary rows (all positions): 2082
- REG-summary rows (QB/RB/WR/TE): 633
- `season_type` values seen (week level): ['POST', 'REG']
- `season_type` values seen (reg level): ['REG']

### Row and player counts by position (REG summary level)

| position | 2021 rows | 2021 unique players | promoted 2022 rows | promoted 2023 rows | promoted 2024 rows | promoted 2025 rows |
|---|---|---|---|---|---|---|
| QB | 81 | 81 | — | — | — | — |
| RB | 165 | 165 | — | — | — | — |
| WR | 256 | 256 | — | — | — | — |
| TE | 131 | 131 | — | — | — | — |

- Unique 2021 players across all four positions: 633
- Promoted 2022-2025 per-season row totals for comparison: 2022: 609, 2023: 576, 2024: 588, 2025: 610 (row counts by season+position are not stored in manifest counts; see per-season totals below).

## Schema compatibility with the 2022-2025 builder

- Missing REQUIRED week-level columns: none
- Missing REQUIRED reg-level columns: none
- Missing OPTIONAL reg-level columns: none

| builder field | resolved 2021 column | required | present |
|---|---|---|---|
| `season` | `season` | yes | yes |
| `week` | `week` | yes | yes |
| `player_id` | `player_id` | yes | yes |
| `team` | `team` | yes | yes |
| `season_type` | `season_type` | no | yes |
| `player_name` | `player_display_name` | yes | yes |
| `position` | `position` | yes | yes |
| `games` | `games` | yes | yes |
| `completions` | `completions` | no | yes |
| `attempts` | `attempts` | no | yes |
| `passing_yards` | `passing_yards` | no | yes |
| `passing_tds` | `passing_tds` | no | yes |
| `passing_interceptions` | `passing_interceptions` | no | yes |
| `carries` | `carries` | no | yes |
| `rushing_yards` | `rushing_yards` | no | yes |
| `rushing_tds` | `rushing_tds` | no | yes |
| `receptions` | `receptions` | no | yes |
| `targets` | `targets` | no | yes |
| `receiving_yards` | `receiving_yards` | no | yes |
| `receiving_tds` | `receiving_tds` | no | yes |
| `receiving_air_yards` | `receiving_air_yards` | no | yes |
| `target_share` | `target_share` | no | yes |
| `air_yards_share` | `air_yards_share` | no | yes |
| `wopr` | `wopr` | no | yes |
| `racr` | `racr` | no | yes |
| `fantasy_points_ppr` | `fantasy_points_ppr` | no | yes |

## Identity / age / draft availability (`load_players()`)

- gsis_id join rate for 2021 QB/RB/WR/TE players: 1.0 (633/633; floor 0.95)

| field | available | of joined | rate |
|---|---|---|---|
| `birth_date` | 633 | 633 | 1.0 |
| `rookie_season` | 633 | 633 | 1.0 |
| `draft_year` | 424 | 633 | 0.6698 |
| `draft_round` | 424 | 633 | 0.6698 |
| `draft_pick` | 424 | 633 | 0.6698 |
| `draft_team` | 424 | 633 | 0.6698 |

## Null / missing-field observations (2021 REG, QB/RB/WR/TE)

| reg-level field | nulls | total | rate |
|---|---|---|---|
| `games` | 0 | 633 | 0.0 |
| `fantasy_points_ppr` | 0 | 633 | 0.0 |
| `targets` | 0 | 633 | 0.0 |
| `receptions` | 0 | 633 | 0.0 |
| `carries` | 0 | 633 | 0.0 |
| `receiving_air_yards` | 0 | 633 | 0.0 |
| `target_share` | 0 | 633 | 0.0 |
| `air_yards_share` | 0 | 633 | 0.0 |
| `wopr` | 0 | 633 | 0.0 |
| `racr` | 127 | 633 | 0.2006 |

## Coverage-status methodology compatibility

- REG week numbers observed in 2021: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
- Max distinct REG weeks observed by any single player: 17
- Max `games` at reg level: 17 (null `games`: 0)
- Duplicate `(player_id, season, season_type)` pairs: 0
- Forecast PR #134 hypothesis: "2021 is likely methodology-compatible because it is a 17-game / 18-week season, unlike pre-2021 seasons."
- Hypothesis verified from TIBER-Data evidence: **True**

## Checks

| check | result |
|---|---|
| `week_level_2021_rows_exist` | PASS |
| `reg_level_2021_rows_exist` | PASS |
| `week_level_reg_season_type_rows_exist` | PASS |
| `required_week_level_columns_present` | PASS |
| `required_reg_level_columns_present` | PASS |
| `season_type_reg_emitted_by_source` | PASS |
| `all_four_positions_present` | PASS |
| `reg_week_span_1_to_18` | PASS |
| `games_within_17_game_season_cap_plus_trade_allowance` | PASS |
| `grain_unique_player_season_season_type` | PASS |
| `load_players_gsis_join_available` | PASS |
| `identity_join_rate_at_or_above_floor` | PASS |

## Decision

```text
may_open_player_season_coverage_2021_candidate_build_issue
```

- Basis: all source-availability and builder-compatibility checks passed

### Explicitly NOT emitted / NOT authorized by this report

- promotion of any artifact
- Forecast mirror refresh
- Forecast controlled rerun
- player-history threshold acceptance
- leakage audit
- model wiring / seasonalPprModel.ts changes

This report is evidence under `docs/reports/`. It is not a candidate artifact, not a promoted dataset, and does not authorize a 2021 build; a follow-up TIBER-Data issue must explicitly authorize any candidate build.
