# 2025 Source-Backed Roster Player Team Map (nflreadpy lane)

## Source

- `nflreadpy.load_rosters_weekly([2025])`
- Upstream dataset: nflverse weekly rosters

## Generated artifact

- `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

## Generation command

```bash
python scripts/build_roster_player_team_map_source_backed_2025.py
```

## Wrapper contract

The script writes a wrapper with:

- `provenance`: `nflreadpy.load_rosters_weekly`
- `source_path`: `nflverse weekly rosters via nflreadpy`
- `source_status`: `source_verified`
- `generated_from`:
  - `scripts/build_roster_player_team_map_source_backed_2025.py`
  - `nflreadpy.load_rosters_weekly([2025])`
- `records`: normalized deterministic roster rows

## Column mapping policy

The script inspects real returned columns at runtime and fail-closes if required fields are missing.

Resolved mapping candidates:

- `season` <- `season`
- `week` <- `week`
- `player_id` <- `gsis_id` (fallback `player_id` only if present)
- `player_name` <- first available of `full_name`, `player_name`, `football_name`
- `position` <- `position`
- `team` <- first available of `team`, `recent_team`

## v1 scope choices

- Included positions: `QB`, `RB`, `WR`, `TE`
- Excluded positions: all non-QB/RB/WR/TE rows
- `active_roster_status` is always `unknown` for this lane unless explicit source semantics are added later.

## Fail-closed rules

- drop rows with missing/blank `player_id`
- drop rows with missing/blank `team`
- reject duplicate `season/week/player_id`
- reject empty post-filter output
- deterministic sort by `season`, `week`, `team`, `player_id`

## Known limitations

- The builder requires external nflverse network access through nflreadpy.
- Active/inactive roster semantics are intentionally not inferred in v1.
