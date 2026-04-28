# Historical Rookie Replay Readiness v0

## Canonical artifact path

- `exports/promoted/rookie-replay/historical_rookie_replay_readiness_v0.json`

## Scope

This builder is intentionally narrow:

- replay season `2025` only
- mode `historical_backtest` only
- offline fixture/scaffold promoted artifact inputs only
- no external fetching and no scraping

This is a readiness/join audit scaffold, not a scoring or projection artifact.

## Purpose

`historical_rookie_replay_readiness_v0` evaluates whether each `historical_rookie_replay_v0` row has enough supporting Evidence Layer artifacts to be considered join-ready.

It explicitly reports missing identity or team context evidence and does not infer or invent missing mappings.

## Input artifacts

- `exports/promoted/rookie-replay/historical_rookie_replay_v0.json`
- `exports/promoted/nfl/roster_player_team_map_v1.json`
- `exports/promoted/nfl/team_pace_pass_environment_v1.json`
- `exports/promoted/nfl/team_offense_summary_v1.json`

## Readiness status semantics

- `ready`: exact player identity exists, roster team matches expected team, and both team context artifacts exist.
- `partial`: identity exists and teams match, but exactly one team context artifact is missing.
- `missing_identity`: no exact `player_id` match in roster map; v0 does not allow fuzzy name fallback.
- `missing_team_context`: identity exists and teams match, but both team context artifacts are missing.
- `mismatch`: identity exists but roster team differs from replay expected team.
- `stale_or_missing_data`: reserved fail-safe status when readiness cannot be resolved cleanly.

## Missing evidence semantics

`missing_evidence` is a deterministic array of explicit missing keys:

- `roster_identity`
- `team_pace_pass_environment`
- `team_offense_summary`

## Validation and fail-closed behavior

The export fails closed when:

- mode is not `historical_backtest`
- any required input artifact file is missing
- duplicate `replay_season/player_id` exists in replay rows
- duplicate `season/week/player_id` exists in roster rows for the selected season
- duplicate `season/team` exists in either team context artifact for the selected season
- no replay rows exist for the selected replay season

## Regeneration

```bash
npm run export:historical-rookie-replay-readiness-v0
```
