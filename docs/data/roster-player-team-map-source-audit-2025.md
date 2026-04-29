# 2025 Roster Player Team Map Source Audit (Repo-Held)

## Purpose

Determine whether this repository currently contains enough **repo-held, source-backed** 2025 player/week/team identity data to derive:

- `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

This is an audit-only determination. No external scraping/fetching was used.

## Files inspected

| File | Season present | Week present | Player ID present | Player name present | Team field present | Position present | Lane type | Can support `roster_player_team_map_2025.source_backed.json`? |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `data/raw/evidence/roster_player_team_map_2025.offline_fixture.json` | Yes | Yes | Yes | Yes | `team` | Yes | offline fixture scaffold | **No** (fixture lane only) |
| `data/raw/evidence/player_weekly_usage_2025.offline_fixture.json` | Yes | Yes | Yes | Yes | `team` | Yes | offline fixture scaffold | **No** (fixture lane only) |
| `data/raw/evidence/player_weekly_box_scores_2025.offline_fixture.json` | Yes | Yes | Yes | Yes | `team` | Yes | offline fixture scaffold | **No** (fixture lane only) |
| `data/raw/evidence/historical_rookie_replay_2025.offline_fixture.json` | No | No | Yes | Yes | No team field | Yes | offline fixture scaffold | **No** (missing season/week/team) |
| `data/gold/forge/forge_weekly_player_input_2025_w12.sample.json` | Yes | Yes | No | No | `team` | Yes | sample artifact | **No** (missing stable player_id; sample lane) |
| `data/raw/forge/weekly_player_stats.offline_fixture.json` | 2024 fixture scope | 2024 fixture scope | Yes | Yes | `recent_team` | Yes | offline fixture scaffold | **No** (not 2025 source-backed) |
| `data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.proof_reference_snapshot.json` | 2024 only | 2024 only | Yes | Yes | `recent_team` | Yes | upstream proof reference snapshot scaffold | **No** (2024 bounded scaffold only) |
| `exports/promoted/nfl/roster_player_team_map_v1.json` | Yes | Yes | Yes | Yes | `team` | Yes | promoted export from offline fixture lane | **No** (derived promoted output, not raw source-backed input) |

## Additional contract/docs inspected

- `docs/data/roster-player-team-map-v1.md`
  - documents that `source_backed` expects `data/processed/evidence/roster_player_team_map_2025.source_backed.json`
  - documents fail-closed behavior when source-backed file is absent
- `scripts/export_roster_player_team_map_v1.mjs`
  - source lane switch exists (`offline_fixture` vs `source_backed`)
  - `source_backed` lane fails closed when the source-backed file is missing

## Conclusion

### Status: **Blocked (intentionally)**

A real repo-held 2025 source-backed player/week/team identity source file is **not currently committed**. The available 2025 files with relevant fields are fixture/sample artifacts, not source-verified ingestion outputs.

Therefore:

- do **not** create `data/processed/evidence/roster_player_team_map_2025.source_backed.json`
- keep `source_backed` fail-closed behavior intact
- keep fixture lane as current canonical promoted scaffold output until a real approved source-backed 2025 input is added

## Boundary statement

This repository should not invent or synthesize missing 2025 roster mappings. Source-backed coverage can only be enabled after a committed repo-held source file with stable `player_id` + `season` + `week` + `team` support is introduced via approved repo conventions.

## Update: approved ingestion lane added (post-audit)

Since this audit was recorded, the repository added an approved source-backed ingestion script:

- `scripts/build_roster_player_team_map_source_backed_2025.py`

This script uses nflreadpy weekly rosters (`nflreadpy.load_rosters_weekly([2025])`) to produce:

- `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

The original audit conclusion remains historically accurate for that point in time: the file was absent then. The lane is now implemented, but artifact availability still depends on running the script in an environment with nflverse access.
