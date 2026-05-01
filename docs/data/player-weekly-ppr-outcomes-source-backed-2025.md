# Player Weekly PPR Outcomes — Source-Backed Input (2025)

## Purpose

This document defines the source-backed raw input lane for `player_weekly_ppr_outcomes_v1`.

- Source: `nflreadpy.load_player_stats([2025])`
- Generated file: `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json`
- Generator: `python scripts/build_player_weekly_ppr_outcomes_source_backed_2025.py`

## Lane behavior

- `offline_fixture` remains default in the TypeScript artifact builder.
- `source_backed` is explicit and fail-closed if the processed source-backed input file is missing.
- This change does not replace or rewrite the committed promoted fixture artifact.

## Mapping policy

The script prints detected columns and resolves fields from known candidates at runtime.

- `player_id`: `player_id` or `gsis_id`
- `team`: `recent_team` or `team`
- `player_name`: `player_name` or `player_display_name` or `full_name`
- `position`: direct `position`; fallback via committed source-backed roster identity (`season/week/player_id` exact join only)
- `opponent`: `opponent_team` or `opponent` or `null` if unsupported
- stats: direct canonical stat columns where present; `null` when unsupported by source columns

## Constraints

- Scope is QB/RB/WR/TE only.
- Rows with missing `player_id` are dropped.
- Rows with missing `team` are dropped.
- Duplicate `season/week/player_id` fails closed.
- Empty valid output fails closed.
- Deterministic ordering: `season`, `week`, `player_id`.

## PPR formula (applied in TS export builder)

- `receptions * 1`
- `+ receiving_yards * 0.1`
- `+ receiving_tds * 6`
- `+ rushing_yards * 0.1`
- `+ rushing_tds * 6`
- `+ passing_yards * 0.04`
- `+ passing_tds * 4`
- `- interceptions * 2`

## Regeneration

```bash
python scripts/build_player_weekly_ppr_outcomes_source_backed_2025.py
```
