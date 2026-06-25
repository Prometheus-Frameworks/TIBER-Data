# team_week_raw_v0 2024 real source artifact spec

## Status

This is PR A for TIBER-Data issue #162: source-side acquisition and normalization specification only.

This document does not ingest data, does not generate a real artifact, does not promote any artifact, does not modify TIBER-Teamstate, and does not change PPM behavior.

## 1. Artifact purpose

TIBER-Data owns the raw-source side of the 2024 all-32 team-week lane:

- raw source acquisition;
- source normalization;
- source refs;
- retrieval date and source version metadata;
- deterministic transform rules;
- validation reports;
- source manifest / lineage record;
- explicit source-governance status.

TIBER-Teamstate consumes the future artifact through a read-only adapter and performs deterministic interpretation into Teamstate movement / forecast-features artifacts. Teamstate must not scrape or own raw NFL source ingestion directly for this lane.

This future artifact is the source-side prerequisite for:

- TIBER-Teamstate #50, the parent Teamstate real source-path lane;
- TIBER-Data #162, the governed 2024 all-32 team-week source artifact spec.

## 2. Candidate artifact path/name

Proposed future candidate artifact path:

```text
exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json
```

Proposed future validation report path:

```text
exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json
```

Proposed future lineage / source manifest path:

```text
data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json
```

These files are intentionally not created by this PR. The paths are candidate names only and may be adjusted by a later implementation PR if repository conventions change.

The candidate artifact must not be treated as promoted or governed merely because it lives under a plausible path. Governance must be explicit in the artifact metadata and supporting manifest / validation records.

## 3. Contract expectations

The future real source artifact must conform to the existing `team_week_raw_v0` envelope unless a later contract PR explicitly revises that contract.

Expected top-level envelope fields:

- `artifact`: fixed literal `team_week_raw_v0`.
- `generatedAt`: UTC ISO-8601 generation timestamp for the normalized artifact.
- `season`: `2024`.
- `sourceArtifacts`: non-empty list of raw source artifact ids, paths, URLs, or retrieval descriptors used to build the artifact.
- `metadata`: provenance, coverage, governance, validation, and source lineage metadata.
- `rows`: normalized team-week rows.

Expected metadata concepts:

- `provenanceStatus`: initially `partial_real_data`, `ungoverned`, or an equivalent explicit incomplete/unpromoted status; never `governed_real_data` before promotion criteria pass.
- `inputSources`: explicit source names, source types, source refs, retrieval timestamps, and version/release metadata where available.
- `coverage`: expected teams, present teams, missing teams, unexpected teams, expected weeks/window, present weeks, row counts, and bye handling posture.
- `governance`: explicit marker that states whether the artifact is ungoverned, candidate, partial, or governed.
- `validationReport`: path or id for the validation report emitted by the build/validation job.
- `lineageManifest`: path or id for the source manifest / lineage record.

The existing contract uses `metadata.provenanceStatus`, `metadata.inputSources`, and `metadata.coverage`. A future implementation PR may either extend metadata in a backward-compatible way or add companion manifest/report files if the current schema should remain unchanged.

## 4. Required and deferred fields

Each non-bye row in the future real artifact must represent one team-game / team-week observation for the selected 2024 window.

Required real fields:

- `season`
- `week`
- `teamCode`
- `opponentCode`
- `offensivePlays`
- `neutralPlays`
- `secondsPerPlay`
- `passRate`
- `neutralPassRate`
- `rushRate`
- `epaPerPlay`
- `passEpaPerPlay`
- `rushEpaPerPlay`
- `successRate`
- `explosivePlayRate`
- `drives`
- `pointsPerDrive`
- `pointsFor`
- `pointsAgainst`
- `pressureRateAllowed`
- `turnovers`
- `sacksAllowed`
- `redZoneTrips`
- `redZoneTdRate`

Optional/deferred fields:

- `fantasyPointsForQB`
- `fantasyPointsForRB`
- `fantasyPointsForWR`
- `fantasyPointsForTE`
- `fantasyPointsAllowedQB`
- `fantasyPointsAllowedRB`
- `fantasyPointsAllowedWR`
- `fantasyPointsAllowedTE`

The fantasy-point split fields are not required for the real Teamstate lane because Teamstate movement v1 drops them and Teamstate forecast-features v1 forbids them. A future artifact may omit them or keep them null if the contract still permits those fields, but Teamstate must not depend on them for this lane.

## 5. Source candidates

### nflreadpy / nflverse weekly team stats

Access method:

- Existing repo precedent uses `nflreadpy.load_team_stats(..., summary_level="week")` for an upstream-backed FORGE scaffold.
- Existing repo precedent also allows direct public nflverse parquet URL fallback references through the public ingest client path when explicitly implemented.

Likely fields provided:

- `season`
- `week`
- team code
- pass attempts / dropbacks variants
- rush attempts / carries variants
- total points / points variants
- passing air yards / air-yards variants

Fields missing or requiring derivation:

- opponent code may require schedule or game-level join.
- neutral situation fields require play-level or drive/game-state logic.
- seconds per play likely requires play clock / game time aggregation from play-by-play.
- EPA, success rate, explosive rate, sacks allowed, turnovers, red-zone trips, points per drive, and pressure rate allowed may require play-by-play, drive data, or another source.

Source refs / retrieval date / version expectations:

- record the nflreadpy function name and arguments;
- record nflreadpy package version if available;
- record nflverse dataset/release URL or source descriptor;
- record retrieval timestamp;
- record raw source artifact path if materialized in a later PR.

Known limitations:

- Weekly team stats alone are not enough for the full required field set.
- Existing FORGE use is proof-of-path only and narrowed to a small 2024 slice, so it cannot imply all-32 or full-window support.

### nflfastR / nflverse play-by-play

Access method:

- Candidate future path through nflfastR/nflverse play-by-play data, either via an accepted Python/R loader or a deterministic direct source retrieval path selected by a later PR.

Likely fields provided or derivable:

- `season`
- `week`
- game id
- possession/offense team
- opponent/defense team
- play type
- pass/rush indicators
- EPA and success indicators if present in the selected source
- yardline and red-zone context
- sacks and turnovers
- score/points context
- game-clock context for pace derivation

Fields missing or requiring derivation:

- neutral situation definitions must be specified before aggregation.
- explosive play thresholds must be specified before aggregation.
- drives and points per drive may require drive id/drive result handling or a separate drive table.
- pressure rate allowed may not be present and may require an additional charting/provider source or explicit deferred/null policy.

Source refs / retrieval date / version expectations:

- record selected nflfastR/nflverse extraction path;
- record package/library version or dataset release/ref;
- record retrieval timestamp;
- record source URL or dataset id where visible;
- record transformation code version / commit sha in the source manifest.

Known limitations:

- Play inclusion rules must be decided before artifact generation, including spikes, kneels, penalties, scrambles, sacks, aborted plays, and no-plays.
- Team attribution must be explicit, likely based on possession/offense team for offensive metrics and opponent/defense team for points against.
- Source model/version assumptions for expected-pass or EPA fields must be recorded rather than inferred.

### Existing offline fixture / FORGE proof-of-path data

Access method:

- Existing committed offline fixtures and proof/reference snapshots under the FORGE weekly lane.

Likely fields provided:

- Some 2024 fixture/proof team-week context fields for narrow operational checks.
- The upstream proof-of-path currently demonstrates a limited public-source workflow.

Fields missing or requiring derivation:

- Does not provide all 32 teams.
- Does not provide a decided full 2024 window.
- Does not provide the full required Teamstate real field set.
- Does not close provenance gaps for broader weekly coverage.

Source refs / retrieval date / version expectations:

- Existing manifests and docs may be cited as audit context only.
- These sources must not be used to claim governed real 2024 all-32 coverage.

Known limitations:

- Explicitly insufficient for the governed 2024 all-32 Teamstate source artifact.
- Must remain labeled fixture/proof/reference/legacy as applicable.
- Must not be promoted into real source coverage by path inference or pattern completion.

## 6. Missing-field policy

Missing source truth must reduce scope or block promotion. It must not be filled with invented or representative values.

Policy:

- Missing required fields fail closed unless this spec or a later contract/spec PR explicitly downgrades the field to optional/deferred.
- Nulls must be explicit, schema-valid, and explained in metadata or the validation report.
- Required finite numeric fields must not be `NaN`, infinite, empty string, or silently coerced from missing source truth.
- `pressureRateAllowed` is the highest-risk required field in the initial source pass. If the selected public sources cannot produce it with a governed denominator, a later PR must either add an accepted source, revise the contract/spec to defer it, or keep the artifact ungoverned/partial.
- Fantasy-point split fields are deferred and must not block the real Teamstate lane.

## 7. Window decision gate

The 2024 support window remains unresolved:

- full 18-week regular season; or
- fantasy-aligned window.

No real artifact should be generated until this decision is made and documented. The selected window must drive expected week coverage, row count expectations, bye handling, validation thresholds, and downstream Teamstate adapter assumptions.

## 8. Validation requirements

A future real candidate artifact must emit or reference a validation report. At minimum, validation must check:

- all 32 NFL teams present for the selected window;
- expected weeks/window present;
- no duplicate team-week rows by `season`, `week`, and `teamCode`;
- valid `teamCode` and `opponentCode` values;
- opponent consistency where paired team-game rows exist;
- bounded rates in `0..1` for rate fields;
- finite numeric fields where required;
- nonnegative count fields where required;
- row count and team-week coverage report;
- bye handling posture if the chosen window includes calendar slots;
- source manifest / lineage record exists;
- validation report path/id is recorded in artifact metadata or companion governance metadata.

Validation must fail closed on duplicate rows, impossible team/opponent codes, unsupported weeks, missing required fields, invalid rates, invalid numeric values, or absent source refs.

## 9. Governance requirements

Before any artifact can be marked `governed_real_data`, require:

- explicit source refs;
- source version or retrieval date;
- deterministic transform code;
- validation report;
- all 32 NFL teams present;
- expected weeks/window present;
- duplicate checks;
- documented missing-field policy;
- explicit governance marker;
- no path-inference governance;
- source manifest or lineage record if that remains the repo pattern;
- human promotion review that confirms the artifact says no more than the sources support.

Interim statuses must remain honest:

- use `partial_real_data`, `ungoverned`, `candidate`, or equivalent explicit incomplete/unpromoted status while incomplete or under review;
- never use `governed_real_data` until all promotion criteria pass;
- never rely on artifact path, file name, or downstream need as a substitute for governance metadata.

## 10. Proposed follow-up PR sequence

- PR A: this docs/spec-only source artifact spec.
- PR B: dry-run source probe and schema mapping, no committed real artifact.
- PR C: generate an ungoverned or `partial_real_data` real 2024 candidate artifact with validation report.
- PR D: promotion review to `governed_real_data` only if explicit-marker governance and validation pass.
- PR E: Teamstate consumes the governed or explicitly allowed real source artifact through a read-only adapter.

## Hard guardrails

This source path must not include:

- ingestion in this PR;
- generated real data artifacts in this PR;
- governed claims before promotion;
- Teamstate code changes in this PR;
- PPM model changes;
- PPM runs;
- Product/Management work;
- rankings;
- fantasy advice;
- invented data;
- path-inference governance.
