# Historical Rookie Replay v0 (Scaffold)

Canonical promoted artifact target:

- `exports/promoted/rookie-replay/historical_rookie_replay_v0.json`

## Scope and mode (initial scaffold)

- mode: `historical_backtest` only
- replay season: `2025`
- source lane: repo-held offline fixture scaffold only
- cohort size: intentionally small and bounded

Committed artifact coverage is fixture-only and does **not** claim full real 2025 rookie replay coverage.

## Current fixture cohort

- Tetairoa McMillan → Carnell Tate archetype comp anchor
- Ashton Jeanty → Jeremiyah Love archetype comp anchor
- Emeka Egbuka → KC Concepcion archetype comp anchor

These rows are deterministic scaffolds for contract and workflow validation.

## Source currently used

- `data/raw/evidence/historical_rookie_replay_2025.offline_fixture.json`
- row provenance label: `offline_fixture:data/raw/evidence/historical_rookie_replay_2025.offline_fixture.json`

Raw wrapper is required and validated fail-closed:

- `provenance`
- `source_path`
- `records`

## Relationship to Evidence Layer artifacts

Historical Rookie Replay v0 rows carry replay judgments plus weekly PPR vectors in a compact cohort scaffold.

This artifact is designed to be contract-compatible with Evidence Layer lanes introduced in:

- `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`
- `exports/promoted/nfl/player_weekly_usage_v1.json`

In this first v0 scaffold, replay rows are fixture-backed and bounded; they do not attempt to claim complete 2025 joins across those artifacts.

## Deterministic metric definitions

From each row's `actual_weekly_ppr` ordered numeric array:

- `season_ppr`: sum of all weekly values, rounded to 2 decimals
- `games_played`: array length
- `startable_weeks`: count of weeks where `actual_weekly_ppr >= 12`
- `spike_weeks`: count of weeks where `actual_weekly_ppr >= 20`
- `bust_weeks`: count of weeks where `actual_weekly_ppr < 8`
- `weekly_volatility`: population standard deviation of `actual_weekly_ppr`, rounded to 4 decimals

No synthetic missing-week rows are inserted.

## Validation and fail-closed behavior

- replay mode must be `historical_backtest`
- duplicate `replay_season/player_id` rows fail closed
- `evidence_status` must be one of:
  - `supported`
  - `partially_supported`
  - `contradicted`
  - `needs_verification`
  - `stale_or_missing_data`
- every output row must include non-empty `source` and valid ISO-8601 UTC `generated_at`
- deterministic sort order is `replay_season`, then `player_id`

## Regeneration

```bash
npm run export:historical-rookie-replay-v0
```
