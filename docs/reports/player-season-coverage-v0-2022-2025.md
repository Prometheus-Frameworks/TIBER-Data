# Coverage Report: player_season_coverage_v0 — 2022-2025 Candidate

- **Generated at:** 2026-06-30T19:38:19.797324+00:00
- **Artifact:** `data/processed/evidence/player_season_coverage_2022_2025.source_backed.json`
- **Artifact status:** `candidate_evidence_artifact_not_promoted`
- **Candidate vs promoted:** This is a **candidate/evidence artifact**, **not** a promoted dataset. It does not authorize Forecast consumption.
- **Tracking issue:** TIBER-Data #190 (follows #184/#185, #186/#187, #188/#189)

## Seasons and scope

- Seasons covered: [2022, 2023, 2024, 2025]
- `season_type` values emitted: ['REG'] (POST is out of scope for this build slice)
- Included positions: ['QB', 'RB', 'TE', 'WR']
- Total records: 2383

## Row counts by season and position

| season | QB | RB | WR | TE | total | unique players | multi-team rows |
|---|---|---|---|---|---|---|---|
| 2022 | 83 | 159 | 238 | 129 | 609 | 609 | 28 |
| 2023 | 81 | 148 | 223 | 124 | 576 | 576 | 12 |
| 2024 | 78 | 148 | 234 | 128 | 588 | 588 | 19 |
| 2025 | 81 | 151 | 240 | 138 | 610 | 610 | 25 |

## Coverage status distribution

- `partial_season`: 1504
- `full_season`: 693
- `single_week`: 186

## Identity confidence distribution

- `source_verified`: 2383

## Null / unavailable rates by field family

| field | null/unavailable | total | rate |
|---|---|---|---|
| `birth_date` | 0 | 2383 | 0.0% |
| `season_age` | 0 | 2383 | 0.0% |
| `draft_year` | 653 | 2383 | 27.4% |
| `rookie_year` | 0 | 2383 | 0.0% |
| `career_year` | 0 | 2383 | 0.0% |
| `games_played` | 0 | 2383 | 0.0% |
| `games_missed` | 2383 | 2383 | 100.0% |
| `usage_summary.target_share` | 0 | 2383 | 0.0% |
| `usage_summary.air_yards_share` | 0 | 2383 | 0.0% |
| `usage_summary.racr` | 472 | 2383 | 19.8% |
| `usage_summary.snap_share` | 2383 | 2383 | 100.0% |
| `usage_summary.routes_run` | 2383 | 2383 | 100.0% |
| `usage_summary.route_participation` | 2383 | 2383 | 100.0% |
| `usage_summary.red_zone_targets` | 2383 | 2383 | 100.0% |
| `usage_summary.red_zone_carries` | 2383 | 2383 | 100.0% |

Note: `usage_summary.snap_share`, `routes_run`, `route_participation`, `red_zone_targets`, `red_zone_carries` are 100% unavailable by design — these are not exposed by `nflreadpy.load_player_stats` and are correctly represented as `null`, never `0`. `games_missed` is 100% unavailable by design — not source-backed in this build (no schedule join). `draft_year` nulls are genuine (undrafted players), not a build gap.

## Age / career-year availability

- `birth_date`: 100.0% available
- `season_age`: 100.0% available
- `rookie_year`: 100.0% available
- `career_year`: 100.0% available
- `draft_year`: 72.6% available

## Sources used

- `nflreadpy.load_player_stats(summary_level='reg')`
- `nflreadpy.load_player_stats(summary_level='week')`
- `nflreadpy.load_players()`

- Source failures or gaps: none

## Validation results

- **Duplicate-row check** (grain `player_id + season + season_type`): PASSED (2383/2383 unique)
- **Fixture/scaffold exclusion check**: PASSED (0 marker hits)
- **Validator** (`scripts/validate_player_season_coverage_v0.py`): PASSED

## 2024 readiness

- Records present for 2024: 588
- Source-backed: True
- 2024 is now source-backed via nflreadpy.load_player_stats/load_players in this candidate artifact (no fixture/scaffold markers detected in source_refs for any 2024 row). This is still a candidate/evidence artifact, not promoted, and is not a Forecast input today.

## Forecast consumption

This is a candidate/evidence artifact under data/processed/evidence/, not a promoted dataset under exports/promoted/. Forecast must not consume this artifact until a separate coverage/provenance gate exists and passes. No Forecast run is authorized by this report.

