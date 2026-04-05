# Forge canonical gold sample artifacts

This directory holds canonical **sample handoff artifacts** for `ForgeWeeklyPlayerInput` exports from TIBER-Data.

Current sample artifact:

- `forge_weekly_player_input_2025_w12.sample.json`
  - contract namespace/version: `src/contracts/v1/forgeWeeklyPlayerInput.ts`
  - represented scope: season `2025`, week `12`, asOf `2026-03-18T12:00:00Z`
  - source set id: `forge-weekly-input-fixtures-v1`
  - deterministic fixture-derived sample; **not** a live production weekly feed

Next step: TIBER-FORGE should ingest this canonical artifact shape in its next PR.
