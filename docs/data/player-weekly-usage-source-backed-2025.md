# Player Weekly Usage Source-Backed Lane (2025)

## Source
- `nflreadpy.load_player_stats([2025])`

## Generated input path
- `data/processed/evidence/player_weekly_usage_2025.source_backed.json`

## Export behavior
- `player_weekly_usage_v1` defaults to `sourceKind: "offline_fixture"`.
- `sourceKind: "source_backed"` reads the source-backed input path above.
- Source-backed lane fails closed if the source-backed file is missing.

## Supported mappings from nflreadpy player stats
- `season` <- `season`
- `week` <- `week`
- `player_id` <- `player_id`
- `player_name` <- `player_name` or `player_display_name`
- `team` <- `team`
- `position` <- `position`
- `opponent` <- `opponent_team`
- `targets` <- `targets`
- `receptions` <- `receptions`
- `target_share` <- `target_share`
- `air_yards` <- `receiving_air_yards`
- `air_yards_share` <- `air_yards_share`
- `rushing_attempts` <- `carries`

## Unsupported-field null policy
The following fields are emitted as `null` in the source-backed lane because they are not available from `nflreadpy.load_player_stats([2025])`:
- `routes_run`
- `route_participation`
- `team_rushing_attempts`
- `rush_share`
- `red_zone_targets`
- `red_zone_carries`
- `snap_share`

`null` means "not available from this source", not zero usage. No route/snap/red-zone inference is performed.

## Share-field validation notes
- `target_share` must stay within `[0, 1]` when present; out-of-range values fail export validation.
- `air_yards_share` is preserved as a finite source-backed number and may be negative.
- Negative `air_yards_share` can occur when receiving air yards are negative (for example, shallow/checkdown profiles); this is valid football signal and is not clamped or rewritten.

## Regeneration
```bash
python scripts/build_player_weekly_usage_source_backed_2025.py
```
