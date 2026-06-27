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

## v0 metadata revision (#175)

The `team_week_raw_v0` envelope was extended **additively and
backward-compatibly** (no field removals, no version bump) so TIBER-Data can
express the governance and field-readiness metadata required by the
#171/#172 governance-blockers audit and the #173/#174 `pressureRateAllowed`
disposition decision. All new metadata fields are optional; existing artifacts
(including the 2024 candidate) remain valid. This revision adds the *capability*
to represent honest governance and honest field unavailability — it does **not**
promote, rebuild, or mark any artifact governed.

Newly schema-modeled `metadata` fields:

- `governance` (`governanceStatus`, `governanceSource`, optional `notes`,
  optional `reviewRefs`)
- `deferredFields`
- `deferredFieldReasons`
- `fieldReadiness`
- `validationReportPath`
- `lineageManifestPath`

Newly schema-modeled `metadata.inputSources[]` fields (all optional):
`sourceRefs`, `retrievalMethod`, `retrievalTimestamp`, `packageVersion`,
`sourceUrlOrDatasetId`, `transformCodePath`, `checksum`
(`{ algorithm, value }`), `immutableSourceRef`.

## Provenance status vocabulary

Allowed `metadata.provenanceStatus` values:

- `fixture_scaffold`
- `sample`
- `partial_real_data`
- `governed_real_data`
- `unknown_provenance`

## Governance metadata

`metadata.governance` carries the explicit governance marker. It is optional;
**absent, malformed, or unrecognized governance fails closed to ungoverned.**

- `governanceStatus`: `ungoverned` | `governed`.
- `governanceSource`: `not_set` | `explicit_marker`.
- `notes` (optional): free-text reviewer note.
- `reviewRefs` (optional): references to the promotion review (e.g. a review
  doc path or PR).

Hard rules (schema- and helper-enforced):

- A `governed` status is only valid when paired with
  `governanceSource: explicit_marker`. The schema **refuses to encode**
  `governed` + `not_set`, so a governed claim cannot be expressed by path,
  name, build success, validation, or downstream need.
- `explicit_marker` set by a human promotion review is the **only** route to a
  governed claim.
- `resolveTeamWeekRawGovernance()` returns `ungoverned` / `not_set` /
  `isGoverned: false` for any absent or non-conforming governance.
- This contract revision does **not** set `governance` on the current
  candidate; the candidate remains `ungoverned` / `not_set`.

## Field-readiness / deferred metadata

`metadata.fieldReadiness` is an optional per-field status map; `deferredFields`
and `deferredFieldReasons` record which fields are intentionally not sourced and
why.

`fieldReadiness` statuses:

- `available` — real source values present.
- `partial_nulls` — present, with some legitimately-null rows (e.g. a
  zero-denominator ratio). **Not** a deferral.
- `deferred` — intentionally not sourced yet for this lane.
- `insufficient_data` — no governed source of adequate quality exists.
- `unavailable` — no source available at all.

`deferred` / `insufficient_data` / `unavailable` all mean the field's null is
**unknown, never zero**. `findTeamWeekRawDeferredFieldViolations()` is the
machine check against null-to-zero laundering: a deferred field carrying a
numeric value (including `0`) on any row is a violation.

### `pressureRateAllowed` posture (per #173 / PR #174)

- `pressureRateAllowed` is **optional / non-blocking for governance** in this
  lane. In the row schema it is now optional-and-nullable.
- A present-and-null (or omitted) `pressureRateAllowed` means
  **unknown/unavailable**, and must be paired with field-readiness/deferred
  metadata (e.g. `fieldReadiness.pressureRateAllowed = "deferred"` and/or
  `deferredFields` including `pressureRateAllowed`). It must **never** be
  zero-filled or backfilled.
- A future governed `team_week_raw_v0` may be promoted **without** real
  pressure values, provided pressure is explicitly deferred and every other
  promotion gate (see #171/#172 audit) is satisfied.
- Real pressure sourcing remains **future additive work**: when an accepted
  source is integrated, `fieldReadiness.pressureRateAllowed` flips from
  `deferred` to `available` additively — it was never a blocker.

Downstream obligations (no downstream repo is changed by this contract PR):

- **Teamstate** must read field-readiness and surface deferred pressure as
  `insufficient_data` / unavailable — never zero, never backfilled.
- **Forecast Run 2** may proceed without pressure, treating it as an
  unavailable feature (omit or mark explicitly missing); introducing no
  fabricated feature keeps the no-leakage boundary intact.

## Validation / lineage / source-pin metadata

The envelope can now represent the metadata a future promotion review needs:

- `metadata.validationReportPath` — path/id of the validation report.
- `metadata.lineageManifestPath` — path/id of the lineage/source manifest.
- per `metadata.inputSources[]`: `sourceRefs`, `retrievalMethod`,
  `retrievalTimestamp`, `packageVersion`, `sourceUrlOrDatasetId`,
  `transformCodePath`, `checksum` (`{ algorithm, value }`), and
  `immutableSourceRef`.

A mutable release-asset URL is not a deterministic pin (see #171/#172 audit
§2.4); `checksum` / `immutableSourceRef` exist so a future governed promotion
can pin the consumed bytes. This PR only adds the capability to represent these
values; it does not generate or assert any pin.

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


## Team code canonicalization (current alignment)

For this v0 fixture lane, Washington is represented as `WAS` to match the current Teamstate/Fantasy canonical abbreviation path and avoid cross-repo adapter alias friction.

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
