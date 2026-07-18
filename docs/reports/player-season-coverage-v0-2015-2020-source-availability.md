# Source-Availability Report: `player_season_coverage_v0` — 2015-2020 REG

- **Generated at:** 2026-07-18T01:03:58.408044+00:00
- **Tracking issue:** TIBER-Data#216
- **Status:** `source_availability_evidence_report_not_an_artifact`
- **Environment:** Python 3.11.15, nflreadpy 0.1.5
- **Scope:** seasons 2015-2020, season_type REG, positions QB/RB/WR/TE, approved source family only (`nflreadpy.load_player_stats`, `nflreadpy.load_players`). This report is aggregate evidence only: it is **not** a candidate artifact, **not** a promoted artifact, carries **no** player-level rows, and authorizes **no** candidate build, promotion, Forecast behavior, or product behavior.
- **Strategy context (not authority):** TIBER-Strategy#3 (research/proven-production-discount-field-note-v0, commit 9992648, docs/design/proven-production-discount-research-note-v0.md) motivates why deeper player history may later matter; it carries NO authority over TIBER-Data behavior and did not influence this audit's verdict.

## What this audit may and may not establish

May establish: `source_rows_exist`, `builder_compatible`, `candidate_build_may_be_proposed`

May NOT establish: `candidate_built`, `promoted`, `Forecast_ready`, `2015-2025_available_to_consumers`

## Sources authorized and called

- `nflreadpy.load_player_stats(seasons=[year], summary_level='week')`
- `nflreadpy.load_player_stats(seasons=[year], summary_level='reg')`
- `nflreadpy.load_players()`
- `nflreadpy.load_players()` status: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet`

## Schedule methodology

- Rule deliberately not reused: `EXPECTED_REG_WEEKS = set(range(1, 19)) (2021+ assumption) was NOT applied`
- Bounds applied: weeks must fall within 1-18; span itself is taken from evidence
- **Narrowest supported rule from evidence:** no schedule-span rule can be stated: no season's REG week span was observed from source in this run

## Per-season results

| season | source calls | week rows (all/REG) | REG-summary rows (all/QB+RB+WR+TE) | unique players | REG weeks observed | gaps | dup grain | identity join |
|---|---|---|---|---|---|---|---|---|
| 2015 | ERROR | not observed | not observed | not observed | not observed | — | — | not observed |
| 2016 | ERROR | not observed | not observed | not observed | not observed | — | — | not observed |
| 2017 | ERROR | not observed | not observed | not observed | not observed | — | — | not observed |
| 2018 | ERROR | not observed | not observed | not observed | not observed | — | — | not observed |
| 2019 | ERROR | not observed | not observed | not observed | not observed | — | — | not observed |
| 2020 | ERROR | not observed | not observed | not observed | not observed | — | — | not observed |

### Per-season statuses (kept separate per #216)

| season | source_rows_exist | required_columns_present | identity_join_sufficient | schedule_method_observed | existing_schema_compatible | existing_validator_semantics_compatible | builder_compatible |
|---|---|---|---|---|---|---|---|
| 2015 | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed |
| 2016 | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed |
| 2017 | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed |
| 2018 | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed |
| 2019 | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed |
| 2020 | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed | not_observed |

### Season 2015

- `nflreadpy.load_player_stats(seasons=[2015], summary_level='week')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2015.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2015.parquet`
- `nflreadpy.load_player_stats(seasons=[2015], summary_level='reg')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2015.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2015.parquet`
- Not observed: source calls failed, so availability for this season is **unknown** (this is an access failure, not evidence the source lacks the season).

### Season 2016

- `nflreadpy.load_player_stats(seasons=[2016], summary_level='week')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2016.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2016.parquet`
- `nflreadpy.load_player_stats(seasons=[2016], summary_level='reg')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2016.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2016.parquet`
- Not observed: source calls failed, so availability for this season is **unknown** (this is an access failure, not evidence the source lacks the season).

### Season 2017

- `nflreadpy.load_player_stats(seasons=[2017], summary_level='week')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2017.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2017.parquet`
- `nflreadpy.load_player_stats(seasons=[2017], summary_level='reg')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2017.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2017.parquet`
- Not observed: source calls failed, so availability for this season is **unknown** (this is an access failure, not evidence the source lacks the season).

### Season 2018

- `nflreadpy.load_player_stats(seasons=[2018], summary_level='week')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2018.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2018.parquet`
- `nflreadpy.load_player_stats(seasons=[2018], summary_level='reg')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2018.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2018.parquet`
- Not observed: source calls failed, so availability for this season is **unknown** (this is an access failure, not evidence the source lacks the season).

### Season 2019

- `nflreadpy.load_player_stats(seasons=[2019], summary_level='week')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2019.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2019.parquet`
- `nflreadpy.load_player_stats(seasons=[2019], summary_level='reg')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2019.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2019.parquet`
- Not observed: source calls failed, so availability for this season is **unknown** (this is an access failure, not evidence the source lacks the season).

### Season 2020

- `nflreadpy.load_player_stats(seasons=[2020], summary_level='week')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2020.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2020.parquet`
- `nflreadpy.load_player_stats(seasons=[2020], summary_level='reg')`: **error** — `ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2020.parquet: 403 Client Error: Forbidden for url: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_2020.parquet`
- Not observed: source calls failed, so availability for this season is **unknown** (this is an access failure, not evidence the source lacks the season).

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
player_season_coverage_2015_2020_source_audit_requires_followup
```

- Basis: season(s) [2015, 2016, 2017, 2018, 2019, 2020] have unresolved followup items or were not observed: 2015: ['source_call_failed: season not observed; availability is UNKNOWN, not absent. This is an inspection-environment/source-access failure, not evidence that the upstream source lacks this season.']; 2016: ['source_call_failed: season not observed; availability is UNKNOWN, not absent. This is an inspection-environment/source-access failure, not evidence that the upstream source lacks this season.']; 2017: ['source_call_failed: season not observed; availability is UNKNOWN, not absent. This is an inspection-environment/source-access failure, not evidence that the upstream source lacks this season.']; 2018: ['source_call_failed: season not observed; availability is UNKNOWN, not absent. This is an inspection-environment/source-access failure, not evidence that the upstream source lacks this season.']; 2019: ['source_call_failed: season not observed; availability is UNKNOWN, not absent. This is an inspection-environment/source-access failure, not evidence that the upstream source lacks this season.']; 2020: ['source_call_failed: season not observed; availability is UNKNOWN, not absent. This is an inspection-environment/source-access failure, not evidence that the upstream source lacks this season.']

- Seasons fully cleared: none
- Seasons with definitive failures: none
- Seasons with follow-up items: [2015, 2016, 2017, 2018, 2019, 2020]
- Seasons not observed: [2015, 2016, 2017, 2018, 2019, 2020]

### Explicitly NOT emitted / NOT authorized by this report

- candidate build (a later issue must separately authorize it)
- promotion of any artifact
- support-window widening to 2015-2025 anywhere
- Forecast mirror refresh, rerun, or validation
- ADP or market-data ingestion
- rankings, projections, advice, or product behavior

This report is aggregate evidence under `docs/reports/`. It is not a candidate artifact and not a promoted dataset. The decision above may authorize only a later issue **proposal**; the phrase "2015-2025 is available" remains prohibited until a later candidate build, independent review, and explicit promotion are complete.
