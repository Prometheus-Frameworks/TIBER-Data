# Source-Availability Report: `player_season_coverage_v0` — 2015-2020 REG

- **Generated at:** 2026-07-18T13:23:40.070250+00:00
- **Tracking issue:** TIBER-Data#216
- **Status:** `source_availability_evidence_report_not_an_artifact`
- **Environment:** Python 3.14.0, nflreadpy 0.1.5
- **Scope:** seasons 2015-2020, season_type REG, positions QB/RB/WR/TE, approved source family only (`nflreadpy.load_player_stats`, `nflreadpy.load_players`). This report is aggregate evidence only: it is **not** a candidate artifact, **not** a promoted artifact, carries **no** player-level rows, and authorizes **no** candidate build, promotion, Forecast behavior, or product behavior.
- **Strategy context (not authority):** TIBER-Strategy#3 (research/proven-production-discount-field-note-v0, commit 9992648, docs/design/proven-production-discount-research-note-v0.md) motivates why deeper player history may later matter; it carries NO authority over TIBER-Data behavior and did not influence this audit's verdict.

## What this audit may and may not establish

May establish: `source_rows_exist`, `builder_compatible`, `candidate_build_may_be_proposed`

May NOT establish: `candidate_built`, `promoted`, `Forecast_ready`, `2015-2025_available_to_consumers`

## Sources authorized and called

- `nflreadpy.load_player_stats(seasons=[year], summary_level='week')`
- `nflreadpy.load_player_stats(seasons=[year], summary_level='reg')`
- `nflreadpy.load_players()`
- `nflreadpy.load_players()` status: **ok**

## Schedule methodology

- Rule deliberately not reused: `EXPECTED_REG_WEEKS = set(range(1, 19)) (2021+ assumption) was NOT applied`
- Bounds applied: weeks must fall within 1-18; span itself is taken from evidence
- **Narrowest supported rule from evidence:** every observed season 2015-2020 exposes exactly REG weeks 1-17; the narrowest supported rule is EXPECTED_REG_WEEKS = set(range(1, 18)) for these seasons only (NOT the 2021+ range(1, 19) rule)

## Per-season results

| season | source calls | week rows (all/REG) | REG-summary rows (all/QB+RB+WR+TE) | unique players | REG weeks observed | gaps | dup grain | identity join |
|---|---|---|---|---|---|---|---|---|
| 2015 | ok | 17613/16905 | 1846/556 | 556 | 1-17 | none | 0 | 1.0 |
| 2016 | ok | 17552/16840 | 1856/557 | 557 | 1-17 | none | 0 | 1.0 |
| 2017 | ok | 17477/16786 | 1869/553 | 553 | 1-17 | none | 0 | 1.0 |
| 2018 | ok | 17414/16728 | 1884/577 | 577 | 1-17 | none | 0 | 1.0 |
| 2019 | ok | 17362/16663 | 1889/572 | 572 | 1-17 | none | 0 | 1.0 |
| 2020 | ok | 17602/16774 | 1984/602 | 602 | 1-17 | none | 0 | 1.0 |

### Per-season statuses (kept separate per #216)

| season | source_rows_exist | required_columns_present | identity_join_sufficient | schedule_method_observed | existing_schema_compatible | existing_validator_semantics_compatible | builder_compatible |
|---|---|---|---|---|---|---|---|
| 2015 | pass | pass | pass | pass | pass | pass | compatible_with_explicit_week_span_parameter |
| 2016 | pass | pass | pass | pass | pass | pass | compatible_with_explicit_week_span_parameter |
| 2017 | pass | pass | pass | pass | pass | pass | compatible_with_explicit_week_span_parameter |
| 2018 | pass | pass | pass | pass | pass | pass | compatible_with_explicit_week_span_parameter |
| 2019 | pass | pass | pass | pass | pass | pass | compatible_with_explicit_week_span_parameter |
| 2020 | pass | pass | pass | pass | pass | pass | compatible_with_explicit_week_span_parameter |

### Season 2015

- `nflreadpy.load_player_stats(seasons=[2015], summary_level='week')`: **ok**
- `nflreadpy.load_player_stats(seasons=[2015], summary_level='reg')`: **ok**
- Week-level rows: 17613 total, 16905 REG (season values observed: [2015]; wrong-season rows excluded: 0)
- REG-summary rows: 1846 total, 556 QB/RB/WR/TE (season values observed: [2015]; wrong-season rows excluded: 0)
- Rows by position: QB: 74 rows / 74 players, RB: 151 rows / 151 players, WR: 212 rows / 212 players, TE: 119 rows / 119 players; unique players total: 556
- REG weeks observed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] (min 1, max 17, gaps none, unexpected none)
- Max games (REG summary): 16; max distinct weeks any player: 16; duplicate grain pairs: 0
- Missing required columns: week-level none, reg-level none; missing optional reg-level: none
- Identity join (gsis_id): 1.0 (556/556; floor 0.95)
- Identity field availability: birth_date: 1.0, rookie_season: 1.0, draft_year: 0.6924, draft_round: 0.6924, draft_pick: 0.6924, draft_team: 0.6924
- Null observations (REG summary, QB/RB/WR/TE):
  - `games`: 0/556 null (rate 0.0)
  - `fantasy_points_ppr`: 0/556 null (rate 0.0)
  - `targets`: 0/556 null (rate 0.0)
  - `receptions`: 0/556 null (rate 0.0)
  - `carries`: 0/556 null (rate 0.0)
  - `receiving_air_yards`: 0/556 null (rate 0.0)
  - `target_share`: 0/556 null (rate 0.0)
  - `air_yards_share`: 0/556 null (rate 0.0)
  - `wopr`: 0/556 null (rate 0.0)
  - `racr`: 102/556 null (rate 0.1835)
  - `team_context`: 0/16905 null (rate 0.0)

### Season 2016

- `nflreadpy.load_player_stats(seasons=[2016], summary_level='week')`: **ok**
- `nflreadpy.load_player_stats(seasons=[2016], summary_level='reg')`: **ok**
- Week-level rows: 17552 total, 16840 REG (season values observed: [2016]; wrong-season rows excluded: 0)
- REG-summary rows: 1856 total, 557 QB/RB/WR/TE (season values observed: [2016]; wrong-season rows excluded: 0)
- Rows by position: QB: 71 rows / 71 players, RB: 151 rows / 151 players, WR: 210 rows / 210 players, TE: 125 rows / 125 players; unique players total: 557
- REG weeks observed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] (min 1, max 17, gaps none, unexpected none)
- Max games (REG summary): 16; max distinct weeks any player: 16; duplicate grain pairs: 0
- Missing required columns: week-level none, reg-level none; missing optional reg-level: none
- Identity join (gsis_id): 1.0 (557/557; floor 0.95)
- Identity field availability: birth_date: 1.0, rookie_season: 1.0, draft_year: 0.6858, draft_round: 0.6858, draft_pick: 0.6858, draft_team: 0.6858
- Null observations (REG summary, QB/RB/WR/TE):
  - `games`: 0/557 null (rate 0.0)
  - `fantasy_points_ppr`: 0/557 null (rate 0.0)
  - `targets`: 0/557 null (rate 0.0)
  - `receptions`: 0/557 null (rate 0.0)
  - `carries`: 0/557 null (rate 0.0)
  - `receiving_air_yards`: 0/557 null (rate 0.0)
  - `target_share`: 0/557 null (rate 0.0)
  - `air_yards_share`: 0/557 null (rate 0.0)
  - `wopr`: 0/557 null (rate 0.0)
  - `racr`: 88/557 null (rate 0.158)
  - `team_context`: 0/16840 null (rate 0.0)

### Season 2017

- `nflreadpy.load_player_stats(seasons=[2017], summary_level='week')`: **ok**
- `nflreadpy.load_player_stats(seasons=[2017], summary_level='reg')`: **ok**
- Week-level rows: 17477 total, 16786 REG (season values observed: [2017]; wrong-season rows excluded: 0)
- REG-summary rows: 1869 total, 553 QB/RB/WR/TE (season values observed: [2017]; wrong-season rows excluded: 0)
- Rows by position: QB: 73 rows / 73 players, RB: 143 rows / 143 players, WR: 214 rows / 214 players, TE: 123 rows / 123 players; unique players total: 553
- REG weeks observed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] (min 1, max 17, gaps none, unexpected none)
- Max games (REG summary): 16; max distinct weeks any player: 16; duplicate grain pairs: 0
- Missing required columns: week-level none, reg-level none; missing optional reg-level: none
- Identity join (gsis_id): 1.0 (553/553; floor 0.95)
- Identity field availability: birth_date: 1.0, rookie_season: 1.0, draft_year: 0.6872, draft_round: 0.6872, draft_pick: 0.6872, draft_team: 0.6872
- Null observations (REG summary, QB/RB/WR/TE):
  - `games`: 0/553 null (rate 0.0)
  - `fantasy_points_ppr`: 0/553 null (rate 0.0)
  - `targets`: 0/553 null (rate 0.0)
  - `receptions`: 0/553 null (rate 0.0)
  - `carries`: 0/553 null (rate 0.0)
  - `receiving_air_yards`: 0/553 null (rate 0.0)
  - `target_share`: 0/553 null (rate 0.0)
  - `air_yards_share`: 0/553 null (rate 0.0)
  - `wopr`: 0/553 null (rate 0.0)
  - `racr`: 102/553 null (rate 0.1844)
  - `team_context`: 0/16786 null (rate 0.0)

### Season 2018

- `nflreadpy.load_player_stats(seasons=[2018], summary_level='week')`: **ok**
- `nflreadpy.load_player_stats(seasons=[2018], summary_level='reg')`: **ok**
- Week-level rows: 17414 total, 16728 REG (season values observed: [2018]; wrong-season rows excluded: 0)
- REG-summary rows: 1884 total, 577 QB/RB/WR/TE (season values observed: [2018]; wrong-season rows excluded: 0)
- Rows by position: QB: 72 rows / 72 players, RB: 149 rows / 149 players, WR: 228 rows / 228 players, TE: 128 rows / 128 players; unique players total: 577
- REG weeks observed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] (min 1, max 17, gaps none, unexpected none)
- Max games (REG summary): 16; max distinct weeks any player: 17; duplicate grain pairs: 0
- Missing required columns: week-level none, reg-level none; missing optional reg-level: none
- Identity join (gsis_id): 1.0 (577/577; floor 0.95)
- Identity field availability: birth_date: 1.0, rookie_season: 1.0, draft_year: 0.688, draft_round: 0.688, draft_pick: 0.688, draft_team: 0.688
- Null observations (REG summary, QB/RB/WR/TE):
  - `games`: 0/577 null (rate 0.0)
  - `fantasy_points_ppr`: 0/577 null (rate 0.0)
  - `targets`: 0/577 null (rate 0.0)
  - `receptions`: 0/577 null (rate 0.0)
  - `carries`: 0/577 null (rate 0.0)
  - `receiving_air_yards`: 0/577 null (rate 0.0)
  - `target_share`: 0/577 null (rate 0.0)
  - `air_yards_share`: 0/577 null (rate 0.0)
  - `wopr`: 0/577 null (rate 0.0)
  - `racr`: 92/577 null (rate 0.1594)
  - `team_context`: 0/16728 null (rate 0.0)

### Season 2019

- `nflreadpy.load_player_stats(seasons=[2019], summary_level='week')`: **ok**
- `nflreadpy.load_player_stats(seasons=[2019], summary_level='reg')`: **ok**
- Week-level rows: 17362 total, 16663 REG (season values observed: [2019]; wrong-season rows excluded: 0)
- REG-summary rows: 1889 total, 572 QB/RB/WR/TE (season values observed: [2019]; wrong-season rows excluded: 0)
- Rows by position: QB: 71 rows / 71 players, RB: 146 rows / 146 players, WR: 230 rows / 230 players, TE: 125 rows / 125 players; unique players total: 572
- REG weeks observed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] (min 1, max 17, gaps none, unexpected none)
- Max games (REG summary): 17; max distinct weeks any player: 17; duplicate grain pairs: 0
- Missing required columns: week-level none, reg-level none; missing optional reg-level: none
- Identity join (gsis_id): 1.0 (572/572; floor 0.95)
- Identity field availability: birth_date: 1.0, rookie_season: 1.0, draft_year: 0.6713, draft_round: 0.6713, draft_pick: 0.6713, draft_team: 0.6713
- Null observations (REG summary, QB/RB/WR/TE):
  - `games`: 0/572 null (rate 0.0)
  - `fantasy_points_ppr`: 0/572 null (rate 0.0)
  - `targets`: 0/572 null (rate 0.0)
  - `receptions`: 0/572 null (rate 0.0)
  - `carries`: 0/572 null (rate 0.0)
  - `receiving_air_yards`: 0/572 null (rate 0.0)
  - `target_share`: 0/572 null (rate 0.0)
  - `air_yards_share`: 0/572 null (rate 0.0)
  - `wopr`: 0/572 null (rate 0.0)
  - `racr`: 99/572 null (rate 0.1731)
  - `team_context`: 0/16663 null (rate 0.0)

### Season 2020

- `nflreadpy.load_player_stats(seasons=[2020], summary_level='week')`: **ok**
- `nflreadpy.load_player_stats(seasons=[2020], summary_level='reg')`: **ok**
- Week-level rows: 17602 total, 16774 REG (season values observed: [2020]; wrong-season rows excluded: 0)
- REG-summary rows: 1984 total, 602 QB/RB/WR/TE (season values observed: [2020]; wrong-season rows excluded: 0)
- Rows by position: QB: 82 rows / 82 players, RB: 157 rows / 157 players, WR: 233 rows / 233 players, TE: 130 rows / 130 players; unique players total: 602
- REG weeks observed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17] (min 1, max 17, gaps none, unexpected none)
- Max games (REG summary): 16; max distinct weeks any player: 16; duplicate grain pairs: 0
- Missing required columns: week-level none, reg-level none; missing optional reg-level: none
- Identity join (gsis_id): 1.0 (602/602; floor 0.95)
- Identity field availability: birth_date: 1.0, rookie_season: 1.0, draft_year: 0.691, draft_round: 0.691, draft_pick: 0.691, draft_team: 0.691
- Null observations (REG summary, QB/RB/WR/TE):
  - `games`: 0/602 null (rate 0.0)
  - `fantasy_points_ppr`: 0/602 null (rate 0.0)
  - `targets`: 0/602 null (rate 0.0)
  - `receptions`: 0/602 null (rate 0.0)
  - `carries`: 0/602 null (rate 0.0)
  - `receiving_air_yards`: 0/602 null (rate 0.0)
  - `target_share`: 0/602 null (rate 0.0)
  - `air_yards_share`: 0/602 null (rate 0.0)
  - `wopr`: 0/602 null (rate 0.0)
  - `racr`: 102/602 null (rate 0.1694)
  - `team_context`: 0/16774 null (rate 0.0)

## Builder / validator / schema reuse assessment

Reusable unchanged:

- schemas/player_season_coverage_v0.schema.json is season-agnostic (season >= 1900; no week-span constant) and needs no change for 2015-2020 rows
- scripts/validate_player_season_coverage_v0.py semantics (unique player_id+season+season_type grain, explicit REG season_type, approved-source-prefix refs, null-vs-zero honesty, no availability assertions) contain no season-shape assumption and need no change
- the approved source allowlist (nflreadpy.load_player_stats(, nflreadpy.load_players() call family) is unchanged for these seasons

NOT reusable as-is:

- EXPECTED_REG_WEEKS = set(range(1, 19)) in scripts/build_player_season_coverage_2021_candidate.py fails closed on any season whose observed REG span is not exactly weeks 1-18; a 2015-2020 build must take an explicit per-season expected-week-span constant justified by this audit's observations
- COVERAGE_STATUS_RULE (full_season: weeks_observed >= 15) is calibrated to a 17-game/18-week season; for a shorter observed span the threshold's meaning changes (15 of 17 vs 15 of 18 weeks) and must be explicitly restated and re-justified, not silently reused
- the 17-game games cap and bye/trade allowances assumed by the 2021+ builders must be re-derived from the observed max games and week span for each older season

Must not change:

- the 2021 and 2022-2025 builders themselves (out of scope for this audit and for any follow-up 2015-2020 build)
- the promoted artifact, its manifest, the schema, the validator, and the source allowlist

## Decision

```text
may_open_player_season_coverage_2015_2020_candidate_build_issue
```

- Basis: every season 2015-2020 cleared source_rows_exist, required_columns_present, identity_join_sufficient, schedule_method_observed, existing_schema_compatible, existing_validator_semantics_compatible, and a builder_compatible path

- Seasons fully cleared: [2015, 2016, 2017, 2018, 2019, 2020]
- Seasons with definitive failures: none
- Seasons with follow-up items: none
- Seasons not observed: none

### Explicitly NOT emitted / NOT authorized by this report

- candidate build (a later issue must separately authorize it)
- promotion of any artifact
- support-window widening to 2015-2025 anywhere
- Forecast mirror refresh, rerun, or validation
- ADP or market-data ingestion
- rankings, projections, advice, or product behavior

This report is aggregate evidence under `docs/reports/`. It is not a candidate artifact and not a promoted dataset. The decision above may authorize only a later issue **proposal**; the phrase "2015-2025 is available" remains prohibited until a later candidate build, independent review, and explicit promotion are complete.
