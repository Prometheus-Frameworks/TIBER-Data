# Player Weekly PPR Outcomes v1 (Evidence Layer)

Canonical promoted artifact target:

- `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`

## Scope and mode (initial release)

- mode: `historical_backtest` only
- season: `2025`
- source lane: repo-held offline fixture support only

- committed artifact coverage is scaffold-only fixture data and does not represent full real 2025 season coverage.

This v1 lane is intentionally bounded to deterministic fixture-backed generation until a governed, reproducible historical source lane is promoted.

## Source currently used

- `data/raw/evidence/player_weekly_box_scores_2025.offline_fixture.json`
- source provenance label on every row: `offline_fixture:data/raw/evidence/player_weekly_box_scores_2025.offline_fixture.json`

## Scoring formula

`ppr_points` is computed deterministically as:

- `receptions * 1`
- `+ receiving_yards * 0.1`
- `+ receiving_tds * 6`
- `+ rushing_yards * 0.1`
- `+ rushing_tds * 6`
- `+ passing_yards * 0.04`
- `+ passing_tds * 4`
- `- interceptions * 2`

Rounding policy:

- `ppr_points` rounded to 2 decimals.
- `rolling_3_week_ppr`, `rolling_5_week_ppr`, and `season_ppr` rounded to 2 decimals.

## Null and zero handling

- Raw numeric source fields are validated as nullable numbers.
- During scoring and output shaping, nullable numeric inputs are explicitly converted to `0`.
- `opponent` remains nullable in the output contract (`null` if unavailable).

## Rolling totals behavior

For each player, rows are ordered by increasing `week`:

- `rolling_3_week_ppr`: sum of current week and prior 2 available weeks.
- `rolling_5_week_ppr`: sum of current week and prior 4 available weeks.
- `season_ppr`: cumulative sum from player week 1 through current row week.
- `games_played`: count of available player rows through current row.

No synthetic missing-week rows are inserted.

## Regeneration

```bash
npm run export:player-weekly-ppr-outcomes-v1
```
