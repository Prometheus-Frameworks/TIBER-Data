# Forge canonical gold sample artifacts

This directory holds canonical **sample handoff artifacts** for `ForgeWeeklyPlayerInput` exports from TIBER-Data.

Current sample artifact:

- `forge_weekly_player_input_2025_w12.sample.json`
  - contract namespace/version: `src/contracts/v1/forgeWeeklyPlayerInput.ts`
  - represented scope: season `2025`, week `12`, asOf `2026-03-18T12:00:00Z`
  - source set id: `forge-weekly-input-fixtures-v1`
  - deterministic fixture-derived sample; **not** a live production weekly feed

Current first derived artifact slice:

- `forge_weekly_player_input_2024_w01.qb_offline_fixture.derived.json`
  - represented scope: season `2024`, week `1`, QB-only cohort
  - source inputs (repo-held support artifacts):
    - `data/raw/forge/weekly_player_stats.offline_fixture.json`
    - `data/raw/forge/team_week_context.offline_fixture.json`
  - directly mapped fields: identity, scope, rush/pass usage, team points proxy
  - explicit gaps/defaults for now: spread/opponent matchup context and route participation fields use neutral/default placeholders with quality flags
  - this is a narrow first derived slice, **not** full weekly production parity

Next step: expand derived source coverage and test TIBER-FORGE ingestion against this derived artifact lane.
