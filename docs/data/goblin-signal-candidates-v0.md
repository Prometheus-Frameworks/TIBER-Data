# GOBLIN Signal Candidates v0 (2025 Source-Backed Research)

## Purpose

`goblin_signal_candidates_v0` is a deterministic, research-only evidence scanner for 2025 player-week rows.

GOBLIN means **Gross Output But Legitimate Indicator Node** and this artifact is a **candidate review generator** only.

It is explicitly **not**:
- a recommendation engine,
- a ranking model,
- ML output,
- waiver/trade/start-sit guidance.

## Input artifacts

The builder consumes the current source-backed readiness spine:

1. `data/processed/evidence/roster_player_team_map_2025.source_backed.json` (identity wrapper)
2. `data/processed/evidence/player_weekly_usage_2025.source_backed.json` (usage wrapper)
3. `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json` (computed PPR row array)

## Output artifact

- `data/processed/research/goblin_signal_candidates_2025.source_backed.json`

Output wrapper contract:
- `provenance: goblin_signal_candidates_v0`
- `source_type: source_backed_research`
- `mode: research_candidate_scanner`
- `season: 2025`
- `records: [...]`

Only player-weeks with at least one computable legitimate indicator flag are emitted.

## Deterministic v0 legitimate indicator flags

1. `low_ppr_high_targets`: `ppr_points <= 8.0` and `targets >= 6`
2. `low_ppr_high_target_share`: `ppr_points <= 8.0` and `target_share >= 0.20`
3. `air_yards_without_output`: `ppr_points <= 8.0` and `air_yards >= 70`
4. `negative_air_yards_share_context`: `air_yards_share < 0`, `targets >= 3`, `ppr_points <= 8.0` (contextual signal)
5. `carries_without_points`: `ppr_points <= 8.0` and `rushing_attempts >= 10`
6. `target_share_without_touchdown`: `ppr_points <= 10.0`, `target_share >= 0.20`, total TDs == 0
7. `usage_spike_without_box_score`: for non-first player-weeks, `ppr_points <= 8.0` and at least one week-over-week jump:
   - `targets >= +3`, or
   - `target_share >= +0.08`, or
   - `air_yards >= +40`, or
   - `rushing_attempts >= +5`.

## Gross output labels

Candidate rows include grossness labels for interpretation only:
- `low_ppr_output`
- `no_touchdown`
- `low_receiving_yardage` (WR/TE only)
- `low_reception_output` (WR/TE only)

## Blocked/missing fields

Every candidate row includes blocked/missing field families not currently available in this lane:
- `routes_run`
- `route_participation`
- `snap_share`
- `red_zone_targets`
- `red_zone_carries`
- `end_zone_targets`
- `goal_line_carries`
- `slot_rate`
- `market_line`
- `wopr`
- `rookie_class`

## Fail-closed behavior

The builder fails closed if:
- any required artifact is missing,
- JSON is invalid,
- required records are empty,
- required fields are missing,
- usage or PPR contains duplicate `season/week/player_id` keys,
- usage rows cannot join to PPR on `season/week/player_id`,
- joined candidate rows cannot join to identity.

PPR-only rows are intentionally ignored (not fatal).

## Regeneration

```bash
python scripts/build_goblin_signal_candidates_2025.py
```

## Relationship to readiness checker

`check_goblin_source_readiness_2025.py` verifies source readiness and join viability.

`build_goblin_signal_candidates_2025.py` is the deterministic downstream scanner that only runs within that ready evidence envelope and emits research candidates without recommendations.
