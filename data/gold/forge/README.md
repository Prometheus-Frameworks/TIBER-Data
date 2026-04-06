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
  - explicit gaps/defaults for now: spread/opponent matchup context and route participation fields use neutral/default placeholders with quality flags
  - narrow sanity-check derived slice, **not** full weekly production parity

- `forge_weekly_player_input_2024_w01.skill_offline_fixture.derived.json`
  - represented scope: season `2024`, week `1`, small QB/RB/WR/TE cohort from the same support fixtures
  - intended use: broader FORGE engine ingestion sanity checks while keeping deterministic offline-fixture provenance
  - explicit gaps/defaults for now: snaps/snapShare are opportunity-based approximations and route/spread/matchup fields remain neutral/defaulted with quality flags
  - still a constrained derived slice, **not** full weekly production parity
