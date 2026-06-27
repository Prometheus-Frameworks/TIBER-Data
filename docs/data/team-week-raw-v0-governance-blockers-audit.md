# team_week_raw_v0 governance blockers audit and future promotion gate

## Status

This is an **audit/spec document only** for TIBER-Data issue #171.

It does not promote any artifact, does not set any governance marker, does not
emit or modify any data artifact, does not change any contract, does not touch
TIBER-Teamstate or TIBER-Forecast, and makes no `governed_real_data` claim.

Its single job is to answer: *what exactly blocks `team_week_raw_v0` from
being promoted to governed source status in TIBER-Data, and what would a
legitimate future promotion PR have to satisfy?*

Starting stance (carried verbatim from the issue): do not promote by desire,
path, coverage, or downstream need. TIBER-Data must prove source truth first;
only then can Teamstate produce a governed team environment; only then can
Forecast test Run 2.

All findings below were re-verified directly against the repository's current
files on branch `claude/team-week-raw-governance-audit-admmze`, not assumed
from prior documents or issue text.

## 1. Current source artifact status

### 1.1 Artifacts that exist today

| Role | Path |
| --- | --- |
| Candidate source artifact | `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json` |
| Validation report | `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json` |
| Lineage / source manifest | `data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json` |
| Build (transform) script | `scripts/build_team_week_raw_v0_2024_candidate.py` |
| Source probe script | `scripts/probe_team_week_raw_v0_2024_sources.py` |
| Contract (schema) | `src/contracts/v1/teamWeekRawV0.ts` |
| Contract doc | `docs/contracts/team-week-raw-v0.md` |
| Fixture/sample (non-real) | `exports/fixtures/team_week_raw/team_week_raw_v0.sample.json`, `exports/fixtures/team_week_raw/team_week_raw_v0.tampa_bay_temporal.sample.json` |
| Prior spec docs | `docs/data/team-week-raw-v0-2024-source-artifact-spec.md` (PR A), `docs/data/team-week-raw-v0-2024-source-probe.md` (PR B), `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` (PR C preflight) |
| Prior promotion review | `docs/reviews/team-week-raw-v0-2024-candidate-promotion-review.md` (PR D — decided **do not promote**) |

The fixtures are `fixture_scaffold`/`sample` data and are **not** real-source
candidates; they are out of scope for promotion and named only so they are not
confused with the candidate. The single real-source candidate is the 2024 file
above.

### 1.2 Candidate artifact status (re-read directly)

| Attribute | Value as currently committed |
| --- | --- |
| `artifact` literal | `team_week_raw_v0` |
| Season / window | `2024`, Weeks `1..18` (full regular season; postseason excluded) |
| Row count | `544` |
| Team coverage | 32/32 expected teams present; `missingTeams: []`, `unexpectedTeams: []`; `isFullLeague: true` |
| Week coverage | weeks present `1..18` == expected `1..18`; `isFullRegularSeasonCalendar: true` |
| Bye handling | `byeWeeksHandled: true`; `544 = 32 × 17` (18-week window minus exactly one bye per team), independently recomputed |
| Source refs | **present** — `sourceArtifacts: ["nflverse-data:pbp/play_by_play_2024", "nflverse-data:schedules/games"]`; `metadata.inputSources` carries source URL, type `nflverse`, and snapshot timestamps |
| Retrieval / version metadata | **present** — manifest records `retrievalMethod` (`nflreadpy.load_pbp([2024])`, `nflreadpy.load_schedules([2024])`), `retrievalTimestamp` (2026-06-25T19:20:36Z / :50Z), `packageVersion` `0.1.5`, `sourceUrlOrDatasetId`, `transformCodePath` |
| Validation report | **present**; `allPassed: true`; 14/14 named checks pass; `rowCount: 544`, `teamCount: 32` |
| Lineage / manifest | **present** at the path above |
| Provenance status | `metadata.provenanceStatus: partial_real_data` |
| Governance status | `metadata.governance.governanceStatus: ungoverned` |
| Explicit governance marker | **absent** — `metadata.governance.governanceSource: not_set` (manifest agrees: `ungoverned` / `not_set`) |
| Deferred fields | `metadata.deferredFields: ["pressureRateAllowed"]` (reason recorded); fantasy-point split fields present but `null` |
| Blocked-field records | `metadata.blockedFieldRows`: `secondsPerPlay: []`, dropback-split: `[]` (no rows blocked); `buildDiagnostics.secondsPerPlayBlockedRowCount: 0`, `dropbackSplitBlockedRowCount: 0` |

### 1.3 Field nullability snapshot (recomputed over all 544 rows)

- `pressureRateAllowed`: **544/544 null** (deferred, §8 of the preflight).
- `redZoneTdRate`: 11/544 null — legitimate zero-denominator (`redZoneTrips == 0`), per the zero-denominator-is-null convention; **not** a deferral.
- `neutralPassRate`, `secondsPerPlay`, `passEpaPerPlay`, `rushEpaPerPlay`: 0/544 null.
- Fantasy-point split fields (`fantasyPointsForQB`…`fantasyPointsAllowedTE`): null on every row (deferred/forbidden downstream; see §2.10).

**Net status: an honest, complete-coverage, fully-sourced, validation-passing
`partial_real_data` / `ungoverned` candidate with no governance marker and one
contractually-required field (`pressureRateAllowed`) null-deferred on every
row.** Coverage, window, source refs, retrieval metadata, validation, and
lineage are all satisfied. Governance is not.

## 2. Promotion blockers

Each blocker is classified **BLOCKING** (must be cleared before any
`governed_real_data` / `governed` claim) or **NOT A BLOCKER** (already
satisfied, recorded here so a future PR does not re-litigate it). "Cleared"
never means *inferred* — see §2.12.

### 2.1 `pressureRateAllowed` deferred on every row — BLOCKING (primary)

`pressureRateAllowed` is a contractually-required field name (it is present and
nullable in `teamWeekRawRowV0Schema`, **not** `.optional()`), and it is
explicit `null` on all 544 rows. Preflight §8 states this in LOCKED terms:
promotion to `governed_real_data` is **blocked** while `pressureRateAllowed`
remains a required field that is null-deferred for every row, and that block is
*not* lifted by documenting the deferral, by a plausible path, by build
success, or by passing validation. Only one of two explicitly-authorized
follow-ups can lift it:

1. integrate an **accepted pressure-charting/provider source** with its own
   source refs and retrieval metadata, un-deferring the field; or
2. a **formal contract revision** that makes `pressureRateAllowed` optional /
   non-blocking for this lane.

Neither has occurred. This is the single hardest blocker and is sufficient on
its own to prevent promotion.

### 2.2 No explicit producer-set governance marker — BLOCKING

`governanceSource: not_set` in both the artifact and the manifest. A governed
claim requires an explicit marker (`governanceSource: explicit_marker`-style
value) set by a human promotion review, never inferred from build/validation
success (preflight §11). The PR D review
(`docs/reviews/team-week-raw-v0-2024-candidate-promotion-review.md`) already ran
and explicitly **decided not to promote**. No marker exists.

### 2.3 Contract cannot express a governance marker — BLOCKING (structural)

This is a gap not previously called out. The v0 metadata schema
`teamWeekRawMetadataV0Schema` (`src/contracts/v1/teamWeekRawV0.ts:45`) models
**only** `provenanceStatus`, `provenanceNotes`, `inputSources`, and
`coverage`. It does **not** model `governance`, `governanceStatus`,
`governanceSource`, `deferredFields`, `validationReportPath`, or
`lineageManifestPath`. Those keys exist on the committed artifact but are *not*
part of the validated contract — a default (non-strict) Zod object strips
unknown keys on parse, so a consumer that re-parses the artifact through the
contract schema would silently drop the governance block entirely.

Consequences:

- There is **no schema-enforced field** in which a future promotion can assert
  a governed marker. `governed_real_data` exists in the `provenanceStatus`
  enum, but `governanceSource: explicit_marker` is not in any contract enum.
- A governed promotion therefore cannot be *expressed in a validated contract
  field* without a backward-compatible contract extension that adds the
  governance/lineage/deferred-field metadata to the schema.

This does not weaken any rule; it means a legitimate promotion requires a
contract-extension step (§3.9, §4) in addition to clearing §2.1.

### 2.4 Source dataset identifier is a mutable release asset (no content hash) — BLOCKING (determinism)

`sourceUrlOrDatasetId` points at
`…/nflverse-data/releases/download/pbp/play_by_play_2024.parquet` (and the
schedules equivalent). These are **rolling release assets**: nflverse updates
the asset behind that URL in place. The manifest records a `retrievalTimestamp`
and `packageVersion` but **no content checksum / sha256 and no immutable
release tag** for the parquet actually consumed. Governance requires
deterministic, reproducible output (spec §9, preflight §10 "deterministic
output"); without a content hash or pinned immutable release ref, a re-run
cannot prove it consumed the same bytes. This is a real reproducibility gap
that a promotion PR must close.

### 2.5 No row-level source refs — NOT A BLOCKER (documented limitation)

`sourceRefs` is present and non-empty at the artifact and manifest level, but
not per row. The current contract does **not** require per-row source refs, so
this does not fail any locked criterion. It is recorded here so a future
governed promotion explicitly decides whether row-level lineage is required;
if it is, that becomes a new contract requirement, not an inference.

### 2.6 Sacks verification status — OPEN (verify before promotion)

`sacksAllowed` is derived from the nflverse play-by-play sack/dropback fields
(probe doc rows for `sacksAllowed`/`passEpaPerPlay`). It is consumed as-shipped
and has **not** been independently cross-verified against a second source. The
sack-counts are internally consistent and pass validation, but "passes our own
checks" is not "verified against an external truth." A promotion review should
record an explicit sacks-verification finding (even if the finding is "accepted
as nflverse-shipped, no second source required"), rather than leave it
implicit.

### 2.7 Pressure source missing/insufficient — BLOCKING (same root as §2.1)

Restated to match the issue's checklist: PR B's probe found no confirmed
pressure column in standard nflverse weekly-stats or play-by-play; no
charting/provider source is identified or approved. This is the *cause* of
§2.1's deferral. Until an accepted pressure source exists (or the contract is
revised), the field cannot carry governed real values.

### 2.8 Red-zone null handling policy — NOT A BLOCKER (satisfied)

`redZoneTdRate` is `null` only on the 11 team-weeks with `redZoneTrips == 0`
(legitimate zero denominator), per the zero-denominator-is-null convention
(preflight §3/§7). This is correct: it is *not* a deferral and *not* a
null-to-zero laundering. Validation (`rate_fields_bounded_0_1_or_null`)
accepts it. No action required, but a promotion record should state plainly
that these 11 nulls are zero-denominator, distinct from the `pressureRateAllowed`
deferral.

### 2.9 Coverage gaps — NOT A BLOCKER (satisfied)

Full 32-team, full Week 1-18 coverage; `544 = 32 × 17`; no missing/unexpected
teams; bye handling correct and independently recomputed. The window decision
is LOCKED (preflight §1). Coverage is complete. **Coverage completeness is not
itself governance** (§2.12) — it removes a blocker, it does not authorize
promotion.

### 2.10 Fantasy-point pollution risk — NOT A BLOCKER (contained)

The eight fantasy-point split fields are `null` on every row, are deferred per
spec §4, and Teamstate forecast-features v1 forbids them. They must remain null
and must not be populated, scored, or consumed for this lane. No fantasy
advice/product/ranking output is produced. Contained, not a blocker — but a
promotion PR must not start emitting them.

### 2.11 Source version / retrieval date — NOT A BLOCKER (present)

`retrievalTimestamp`, `packageVersion` (`0.1.5`), `retrievalMethod`, and
`transformCodePath` are all present and complete for both sources (validation
`retrieval_metadata_complete` passes). The remaining version concern is the
*immutability of the dataset bytes*, captured separately as §2.4.

### 2.12 Path / name / downstream-need governance inference risk — STANDING GUARDRAIL

No criterion below may be satisfied by inference. Specifically: living under
`exports/candidates/` or `data/manifests/` is **not** governance; build/
validation success is **not** governance; Teamstate's or Forecast's need for
the artifact (Run 2) is **not** governance and relaxes nothing. Missing or
unrecognized governance metadata must fail closed to ungoverned. This audit
asserts no governed status anywhere.

### 2.13 Blocker summary

| # | Blocker | Class |
| --- | --- | --- |
| 2.1 | `pressureRateAllowed` null-deferred on all 544 rows | **BLOCKING (primary)** |
| 2.2 | No explicit governance marker (`governanceSource: not_set`) | **BLOCKING** |
| 2.3 | Contract schema cannot express a governance marker | **BLOCKING (structural)** |
| 2.4 | Source bytes not pinned (mutable release URL, no checksum) | **BLOCKING (determinism)** |
| 2.7 | No accepted pressure source identified | **BLOCKING (root of 2.1)** |
| 2.6 | Sacks not independently verified | OPEN — record finding before promotion |
| 2.5 | No row-level source refs | NOT A BLOCKER (decide if required) |
| 2.8 | Red-zone zero-denominator nulls | NOT A BLOCKER (satisfied) |
| 2.9 | Coverage gaps | NOT A BLOCKER (satisfied) |
| 2.10 | Fantasy-point pollution | NOT A BLOCKER (contained) |
| 2.11 | Source version / retrieval date | NOT A BLOCKER (present) |
| 2.12 | Path/name/downstream-need inference | STANDING GUARDRAIL |

## 3. Required promotion gate (future PR — not this one)

A future promotion PR may mark the artifact governed **only if every item
below holds simultaneously**. This consolidates spec §9, preflight §9/§10/§11,
and the PR D review, and adds §2.3/§2.4.

1. **Upstream source references** — `sourceArtifacts` / `inputSources` /
   manifest `sources` present and non-empty for every consumed source
   (already satisfied; must remain so).
2. **Retrieval / version metadata** — `retrievalMethod`, UTC
   `retrievalTimestamp` recorded at retrieval, `packageVersion`,
   `sourceUrlOrDatasetId`, `transformCodePath` for each source (already
   satisfied), **plus** an immutable identifier for the consumed bytes: a
   content checksum (e.g. sha256) and/or a pinned immutable nflverse release
   ref (closes §2.4).
3. **Row-level lineage** — explicitly decide whether per-row source refs are
   required; if required, add to contract and populate; if not, record the
   decision (resolves §2.5 either way, no inference).
4. **Validation** — re-run the build/validation; expect `allPassed: true` with
   all 14 named checks passing, `rowCount: 544`, `teamCount: 32`, and (after a
   pressure resolution) a pressure check consistent with the chosen
   disposition. Validation passing is an *input* to the gate, never the gate.
5. **Coverage** — 32/32 teams, Weeks 1-18, `544 = 32 × 17`, byes handled, no
   missing/unexpected (already satisfied; must remain so).
6. **Null / deferred-field policy** — every null is either (a) a legitimate
   zero-denominator (`neutralPassRate`, `redZoneTdRate`) or (b) an explicitly
   recorded deferral; **no null-to-zero laundering, no zero-fill, no pressure
   backfill**. `pressureRateAllowed` must be *resolved*, not just documented
   (see #7).
7. **Pressure posture** — `pressureRateAllowed` must be either:
   (a) sourced from an accepted pressure-charting/provider source with its own
   source refs and retrieval metadata and emitted as real values; **or**
   (b) formally moved to optional/non-blocking for this lane by a contract
   revision. Documenting the deferral is **not** sufficient (preflight §8).
8. **Explicit governance marker semantics** — a human promotion review sets an
   explicit `governanceSource: explicit_marker` (or the contract's equivalent
   enum value once added per §3.9) and `governanceStatus: governed` /
   `provenanceStatus: governed_real_data`. Never inferred from build, path,
   validation, or downstream need.
9. **Contract can express the marker** — the v0 contract metadata schema is
   extended (backward-compatibly) to model `governance` (status + source),
   `deferredFields`, `validationReportPath`, and `lineageManifestPath`, so the
   governed marker survives a contract re-parse and is not silently stripped
   (closes §2.3). Adding a `governanceSource` enum that includes
   `explicit_marker` and `not_set` is part of this.
10. **Promotion manifest / event log** — the lineage manifest (and a promotion
    record) record the promotion event, the reviewer, the reviewed merge SHA,
    and the marker; `governed_real_data` is asserted in exactly one
    authoritative place and nowhere by inference.
11. **Deterministic output** — re-running the transform against the pinned
    bytes (#2) reproduces the artifact deterministically; rounding, ordering,
    and exclusion counts are stable and recorded (current build records
    `buildDiagnostics` such as `excludedPossessionPlaysTotal` and
    `paceAnomalousIntervalsTotal`; promotion should assert these are stable).
12. **Sacks finding** — record an explicit sacks-verification finding (§2.6).
13. **Separate authorized PR** — promotion is its own explicitly-authorized PR
    with its own human review; it is never folded into an audit, a build, or a
    contract change.

## 4. Downstream contract implications (what Teamstate/Forecast would need later)

TIBER-Data must provide the following so Teamstate can later consume the source
safely and Forecast can run no-leakage checks downstream. **This audit changes
none of these; it documents them.**

- **Stable artifact kind/version** — `artifact: team_week_raw_v0` (stable);
  any new metadata must be additive/backward-compatible.
- **Explicit `provenanceStatus` / `governanceStatus`** — surfaced as
  first-class, schema-modeled fields (today `governanceStatus` is *not* in the
  schema; §2.3/§3.9).
- **Explicit `governanceSource: explicit_marker`** if and only if promoted —
  with a contract enum that can represent it.
- **Source dataset refs + validation report path** — `sourceArtifacts` /
  `inputSources` plus `validationReportPath` reachable from the artifact.
- **Lineage manifest path** — `lineageManifestPath` reachable from the
  artifact (present today as out-of-contract metadata).
- **Field-level readiness / deferred metadata** — `deferredFields` +
  `deferredFieldReasons` + `blockedFieldRows`, so Teamstate can preserve and
  surface `pressureRateAllowed` deferral and must not treat
  `pressureRateAllowed: null` as a zero-pressure observation.
- **As-of / retrieval / source-season metadata** — `season`, per-source
  `retrievalTimestamp`/`sourceSnapshotAt`, and the pinned source identifier,
  so Forecast can enforce the 2024-predictor / 2025-target no-leakage boundary
  downstream.

Until promotion, Teamstate may treat the candidate only as an explicitly
allowed `partial_real_data` / `ungoverned` input (per the PR D review §14):
read-only adapter / schema-compliance / non-production development against
real-shaped 2024 data, **provided** it preserves and surfaces the
`partial_real_data` / `ungoverned` status and never backfills
`pressureRateAllowed`. No Teamstate or Forecast change is made or implied here.

## 5. Recommendation

**Is `team_week_raw_v0` promotable now? No.**

At least four blockers stand simultaneously: the `pressureRateAllowed`
all-rows deferral (§2.1/§2.7, the locked primary block), the absent governance
marker (§2.2), the contract's inability to even express that marker (§2.3),
and the un-pinned source bytes (§2.4). Coverage, window, source refs,
retrieval metadata, validation, and lineage are all already satisfied — but
none of those are governance, and completeness must not be read as
authorization (§2.12). The PR D review already reached "do not promote" on the
pressure block alone; this audit confirms that and adds the structural
contract and determinism gaps.

### Smallest next safe PR

The gating decision is the **pressure disposition** (§3.7), because it is
locked and dominates the rest. The smallest safe next step is a **docs/spec
decision PR** (no promotion, no data change, no contract code change) that:

1. chooses between §3.7(a) "find/integrate an accepted pressure source" and
   §3.7(b) "formally defer `pressureRateAllowed` to optional for this lane,"
   with rationale; and
2. records the dependent follow-up sequence: if (b), a contract-revision PR
   (which would also fold in the §2.3 governance-marker fields and the §2.4
   pinned-source-identifier requirement, since a governed promotion needs all
   three); then a re-run/validation PR; then a separate PR D-style promotion
   review.

That decision PR unblocks exactly one thing at a time, promotes nothing, and
keeps every guardrail intact. Promotion itself remains a **separate, later,
explicitly-authorized PR** that must satisfy the full §3 gate — it must never
be merged into the decision PR, the contract PR, or this audit.

Do not let this audit become the promotion.

## 6. Verification

Dependencies were installed in the session (`nflreadpy==0.1.5`, `polars`,
`pytest`, `jsonschema`, `fastapi`, `httpx`; `npm install`). Commands run from
the TIBER-Data repo root:

- `npm run typecheck` → **pass** (exit 0).
- `python3 -m pytest tests/test_probe_team_week_raw_v0_2024_sources.py tests/test_build_team_week_raw_v0_2024_candidate.py -q` → **53 passed**.
- `python3 -m pytest -q` (full Python suite) → **190 passed**.
- `npx vitest run` (full TS suite) → see PR body for the final figure; the
  suite passes apart from an intermittent vitest worker-RPC timeout
  (`Timeout calling "onTaskUpdate"`) that is an environment/runner artifact,
  not a test assertion failure.

This audit adds only this Markdown file; it changes no code, schema, artifact,
or downstream repository.
