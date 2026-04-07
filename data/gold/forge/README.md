# Forge canonical gold sample artifacts

This directory holds canonical handoff artifacts for `ForgeWeeklyPlayerInput` exports from TIBER-Data.

Current sample artifact:

- `forge_weekly_player_input_2025_w12.sample.json`
  - contract namespace/version: `src/contracts/v1/forgeWeeklyPlayerInput.ts`
  - represented scope: season `2025`, week `12`, asOf `2026-03-18T12:00:00Z`
  - source set id: `forge-weekly-input-fixtures-v1`
  - deterministic fixture-derived sample; **not** a live production weekly feed

Current derived artifact slices:

- `forge_weekly_player_input_2024_w01.qb_offline_fixture.derived.json`
  - represented scope: season `2024`, week `1`, QB-only cohort
  - source inputs (repo-held support artifacts):
    - `data/raw/forge/weekly_player_stats.offline_fixture.json`
    - `data/raw/forge/team_week_context.offline_fixture.json`
  - directly mapped fields: identity, scope, rush/pass usage, team points proxy
  - explicit gaps/defaults for now: spread/opponent matchup context uses neutral placeholders and route participation for QB remains unavailable, with quality flags
  - narrow sanity-check derived slice, **not** full weekly production parity

- repeatable broader skill-position weekly derived artifacts:
  - `forge_weekly_player_input_2024_w01.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w02.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w03.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w04.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w05.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w06.skill_offline_fixture.derived.json`
  - represented scope: season `2024`, small fixed set of contiguous weeks (`1-6`)
  - intended use: first repeatable weekly artifact factory pattern for FORGE ingestion sanity checks
  - explicit checks per generated week: non-empty artifact, coherent source metadata (`sourceSetId`/season/week), deterministic ordering, expected positions from source support, and schema validation
  - explicit gaps/defaults for now: snaps/snapShare remain opportunity-based approximations, route fields are lightweight target-share approximations for non-QB rows, and spread/matchup remain neutral/defaulted with quality flags
  - still an offline-fixture-backed constrained season-segment export path, **not** full-season production ETL parity
