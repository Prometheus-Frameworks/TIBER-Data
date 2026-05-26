# Team Week Raw v0 Contract

## Status and scope

`team_week_raw_v0` defines a governed, provenance-aware team-week input artifact for downstream TIBER repositories (especially TIBER-Teamstate).

This issue is **contract/spec + fixture only**. It does **not** ingest external data, does **not** claim full 2025 coverage, and does **not** change Teamstate runtime behavior.

## Purpose

TIBER-Data owns raw/source/provenance truth for team-week inputs. Teamstate consumes governed artifacts and interprets them for profile generation.

This contract exists to prevent downstream repos from becoming ad-hoc raw-data lanes.

## Ownership boundary

### TIBER-Data owns

- `team_week_raw_v0` contract and artifact shape.
- Source and provenance semantics.
- Fixture/sample vs governed-real-data labeling.
- Coverage metadata semantics and validation expectations.

### TIBER-Teamstate owns

- Interpretation of governed team-week rows.
- Team scoring/environment logic.
- Team environment profile generation.

Teamstate should consume governed team-week artifacts and should not become the raw ingestion authority in this path.

## Artifact envelope (canonical shape)

A `team_week_raw_v0` artifact is an envelope with metadata and row payloads.

Top-level fields:

- `artifact`: fixed literal `"team_week_raw_v0"`.
- `generatedAt`: ISO-8601 timestamp.
- `season`: season represented by the artifact.
- `sourceArtifacts`: list of source artifact ids/paths used to build this artifact.
- `metadata`: provenance and coverage semantics.
- `rows`: list of team-week rows.

## Provenance status vocabulary

Allowed `metadata.provenanceStatus` values:

- `fixture_scaffold`
- `sample`
- `partial_real_data`
- `governed_real_data`
- `unknown_provenance`

## Source typing vocabulary

Each `metadata.inputSources[]` item includes:

- `source`: source name/path/identifier.
- `sourceType`: one of:
  - `fixture`
  - `sample`
  - `nflverse`
  - `manual_verified`
  - `governed_artifact`
  - `unknown`
- `sourceSnapshotAt` (optional nullable timestamp)
- `notes` (optional)

## Coverage semantics

`metadata.coverage` must capture what is present and what is absent without inventing continuity.

Required concepts:

- team set accounting (`expectedTeams`, `presentTeams`, `missingTeams`, `unexpectedTeams`)
- week set accounting (`weeks`, `expectedWeeks`)
- calendar fullness flags
- team-game row counts
- explicit bye handling posture

### Important distinction: calendar slots vs played team-games

For a regular NFL season:

- **Calendar team-week slots**: `32 teams × 18 weeks = 576`.
- **Played team-game rows**: `32 teams × 17 games = 544`.

Bye weeks are expected non-game weeks, not inherently missing truth.

The contract must therefore distinguish:

- calendar coverage (`isFullRegularSeasonCalendar`),
- played-game coverage accounting (`expectedTeamGameRows` vs `actualTeamGameRows`),
- and whether bye handling is explicit (`byeWeeksHandled`).

v0 allows phased implementation of bye validation, but the semantic distinction is mandatory.

## Row semantics (camelCase)

Rows are camelCase even when upstream/source fixtures use snake_case.

Each row represents a team-week context with nullable metric fields allowed where source truth is unavailable.

`isByeWeek` may be used when a week is intentionally represented as a bye slot.

## Current fixture lane in this repo

This repository now includes a sample fixture artifact (scaffold-level), containing **4 rows for 2025 Week 8 only**:

- DET
- PIT
- TEN
- MIA

This fixture is explicitly non-full-league and non-full-calendar.

## Future governed batching plan

Intended expansion path (batch by week, all teams per batch):

1. Week 1 (all teams)
2. Weeks 1-4 (all teams)
3. Weeks 1-8 (all teams)
4. Weeks 1-18 (all teams), bye-aware regular season coverage

Batching by week keeps season-to-date aggregation coherent for consumers.

## Out of scope for v0 contract introduction

- No external ingest implementation in this issue.
- No full 2025 league artifact generation in this issue.
- No Teamstate code changes in this issue.
- No fabricated rows to mimic full coverage.

## Validation expectation

At minimum, contract-aware checks should assert:

- envelope field presence and literal artifact id,
- allowed provenance/sourceType enums,
- coverage/accounting field presence,
- honest fixture labeling (`fixture_scaffold`/`sample` when applicable),
- no full-league/full-calendar claims unless supported by source truth.
