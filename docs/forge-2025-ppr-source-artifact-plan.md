# FORGE 2025 PPR Source Artifact Plan

## Purpose

TIBER-Data owns the real source truth for FORGE 2025 PPR season grading. TIBER-FORGE consumes the gold artifacts produced here; it must not scrape, project, fixture-fill, or invent player PPR totals.

Target artifacts:

- `data/gold/forge/forge_season_player_input_2025.ppr.v1.json`
- `data/gold/forge/forge_weekly_player_ppr_2025.v1.json`

The initial builder is intentionally bounded to 20-50 source-backed QB/RB/WR/TE players and uses only completed/available 2025 regular-season rows already present in this repository.

## 1. Source files currently present

### Source-backed 2025 player weekly outcome input

- File: `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json`
- Provenance label in file: `nflreadpy.load_player_stats`
- Source path label in file: `nflverse player stats via nflreadpy`
- Generator listed in file: `scripts/build_player_weekly_ppr_outcomes_source_backed_2025.py` and `nflreadpy.load_player_stats([2025])`
- Contains QB/RB/WR/TE weekly player rows with `season`, `week`, `player_id`, `player_name`, `team`, `position`, `opponent`, receiving/rushing/passing counting stats, targets, and interceptions where available.

### Computed 2025 source-backed PPR evidence

- File: `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json`
- Contains computed weekly PPR, rolling PPR, season-to-date PPR, and games played from the source-backed row lane.
- This is useful evidence, but the FORGE gold builder recomputes PPR from the documented formula so the scoring rule remains explicit at the FORGE handoff boundary.

### Source-backed 2025 player usage input

- File: `data/processed/evidence/player_weekly_usage_2025.source_backed.json`
- Provenance label in file: `nflreadpy.load_player_stats`
- Contains player/team/week usage fields such as targets, receptions, air yards, rushing attempts, target share, and rush share when available.

### Source-backed 2025 roster/team identity input

- File: `data/processed/evidence/roster_player_team_map_2025.source_backed.json`
- Provenance label in file: `nflreadpy.load_rosters_weekly`
- Source status in file: `source_verified`
- Used by the FORGE PPR builder for full player-name enrichment where the weekly stats source uses abbreviated names.

### Existing FORGE weekly inputs

- `data/gold/forge/forge_weekly_player_input_2024_w01.skill_offline_fixture.derived.json` through `w06`
- `data/gold/forge/forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json` through `w03`
- `data/gold/forge/forge_weekly_player_input_2025_w12.sample.json`

These existing FORGE inputs are calibration, fixture, proof-reference, or sample lanes. They are not source truth for the new 2025 PPR gold artifacts.

## 2. Are 2025 PPR totals available?

Yes, but with a contract boundary:

- Source-backed weekly counting stats are present in `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json`.
- A computed source-backed PPR evidence file already exists at `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json`.
- The new FORGE gold builder recomputes PPR from counting stats using the explicit PPR formula rather than copying fixture-backed or promoted fixture output.
- Interceptions and fumbles lost are nullable/unavailable if the source-backed input does not carry those fields for a row. Missing values are treated as zero only for PPR arithmetic and remain `null` in emitted stat blocks.

## 3. Are weekly player outputs vs opponent available?

Yes for the source-backed player-week outcome lane:

- The weekly source rows include `season`, `week`, `team`, `position`, and `opponent`.
- Regular-season weeks 1-18 are used for the FORGE 2025 PPR handoff.
- Postseason/source weeks beyond 18 are intentionally excluded from these regular-season grading artifacts.

## 4. Proposed season artifact schema

`data/gold/forge/forge_season_player_input_2025.ppr.v1.json` is an object with:

- `artifactId`: `forge_season_player_input_2025.ppr.v1`
- `season`: `2025`
- `schemaVersion`: `v1`
- `scoringFormat`: `PPR`
- `regularSeasonWeeks`: `[1, ..., 18]`
- `availableWeeks`: source-backed weeks represented after filtering
- `playerCount`: count of selected source-backed players, bounded to 20-50
- `scoringRules`: documented scoring rule labels
- `metadata`:
  - `sourceSetId`
  - `asOf`
  - `sourceUpdatedAt`
  - `buildId`
  - `sourceProviders`
  - `sourcePaths`
  - `sourceProvenance`
  - `sourcePathLabel`
  - `generatedFrom`
  - `scoringFormat`
- `records`: player season records with:
  - `playerId`
  - `playerName`
  - `team`
  - `position`
  - `season`
  - `weeks`
  - `games`
  - `scoringFormat`
  - `pprTotal`
  - `ppg`
  - `opportunities` (`rushingAttempts + targets` when available)
  - `stats` totals for passing/rushing/receiving/fumbles-lost fields where available
  - `source` summary metadata

## 5. Proposed weekly artifact schema

`data/gold/forge/forge_weekly_player_ppr_2025.v1.json` is an object with the same artifact-level metadata fields and weekly `records` containing:

- `playerId`
- `playerName`
- `team`
- `position`
- `season`
- `week`
- `opponent`
- `scoringFormat`
- `pprPoints`
- `opportunities` (`rushingAttempts + targets` when available)
- `stats` for passing/rushing/receiving/fumbles-lost fields where available
- `source` summary metadata

## 6. Missing source data

Current known gaps are preserved rather than filled:

- Fumbles lost are not present in the existing source-backed weekly PPR input and are emitted as `null`.
- Some passing turnover fields may be unavailable/null in the source-backed input and are emitted as `null`.
- Snap counts, routes, injury status, betting/team context, and projection-like semantics are outside this PPR artifact contract.
- The builder does not use existing offline fixture, sample, or calibration rows to patch missing source-backed values.

## 7. Builder implementation plan

Implemented builder:

- Script: `scripts/build_forge_2025_ppr_artifacts.py`
- Inputs:
  - `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json`
  - `data/processed/evidence/roster_player_team_map_2025.source_backed.json`
- Outputs:
  - `data/gold/forge/forge_season_player_input_2025.ppr.v1.json`
  - `data/gold/forge/forge_weekly_player_ppr_2025.v1.json`

Builder behavior:

1. Fail clearly if the source-backed weekly PPR input is missing.
2. Filter to 2025 regular-season weeks 1-18.
3. Filter to QB/RB/WR/TE.
4. Select up to 50 fantasy-relevant players deterministically:
   - first include existing FORGE calibration names if present in source-backed rows;
   - then fill by source-computed season PPR total.
5. Compute PPR with the documented formula:
   - passing yards / 25
   - passing TD × 4
   - interception × -2
   - rushing yards / 10
   - rushing TD × 6
   - receiving yards / 10
   - receiving TD × 6
   - reception × 1
   - fumble lost × -2 when available
6. Aggregate season totals and PPG.
7. Emit source metadata and build metadata.
8. Serialize with JSON `allow_nan=False`.

## 8. Validation checks

Validation expectations now covered or expected for future hardening:

- Artifact object has required metadata fields.
- `scoringFormat` is `PPR` at artifact and row level.
- `playerCount` is between 20 and 50.
- Weekly rows only include season 2025 and weeks 1-18.
- Season and weekly rows only include QB/RB/WR/TE.
- No row source provider or source path references `offline_fixture`, `sample`, or fabricated fixture lanes.
- PPR formula has a unit test with a hardcoded source-backed-style row.
- Missing source-backed input fails with an explicit missing-source message.
- Future schema validation should be promoted to JSON Schema once the downstream FORGE consumer locks exact field names.

## 9. Handoff contract to TIBER-FORGE

TIBER-FORGE may consume these artifacts as source-backed PPR truth for 2025 season grading.

TIBER-FORGE must not:

- scrape player PPR totals independently;
- import offline fixture/sample/calibration rows as real 2025 truth;
- infer missing fumbles, interceptions, snap, route, injury, betting, or projection fields;
- widen the season/week support window beyond the artifact metadata.

TIBER-FORGE should treat nullable fields as unavailable source truth, not as implicit projections. If FORGE requires fields outside this contract, the request should come back to TIBER-Data as a new source-backed artifact or an explicit contract revision.
