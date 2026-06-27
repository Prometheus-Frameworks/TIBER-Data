# PR D Promotion Review: 2024 team_week_raw_v0 — APPROVED (governed)

## Status

**PROMOTED to `governed_real_data`.** This is the explicit human governance
review (PR D) required by the `team_week_raw_v0` chain, for TIBER-Data #179. It
records the explicit-marker decision that promotes the rebuilt 2024 candidate to
governed source status.

The governed claim is made **only** because this review explicitly authorizes it
and sets `governanceSource: explicit_marker` with an agreeing
`provenanceStatus: governed_real_data`. It is not inferred from path, file name,
build success, validation passing, or downstream need.

## Context chain

- TIBER-Data #171 / PR #172 — governance-blockers audit (defined the promotion gate).
- TIBER-Data #173 / PR #174 — `pressureRateAllowed` disposition: Option B (formally defer).
- TIBER-Data #175 / PR #176 — contract revision: governance, field-readiness, source-pin metadata.
- TIBER-Data #177 / PR #178 — candidate rebuilt under the revised contract.
- TIBER-Data #179 (this review) — PR D promotion decision.

## Reviewed artifacts

- Artifact: `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`
- Validation report: `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json`
- Lineage manifest: `data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json`
- Reviewed base: `main` at the #178 merge (`rebuild: regenerate team_week_raw_v0 candidate under revised contract`).

## Reviewer / authority note

This review was performed by an AI coding agent (Claude Code) acting on
**explicit operator authorization** for Path A (approve & promote), given in the
TIBER-Data #179 promotion-review decision. The agent is not an autonomous
governance authority: the gate was re-verified directly against the committed
files, and the governed marker is set only because the operator explicitly
authorized promotion after reviewing the findings below. No row value was
changed, no source was re-fetched, and pressure was neither sourced nor filled.

## Promotion in place (path rationale)

The artifact is promoted **in place** at its existing
`exports/candidates/.../...candidate.json` path. Per the chain's core rule,
governance is carried by the explicit metadata marker, **not** by the file
path — so neither the `candidate` path nor a move to `exports/promoted/` changes
the governance fact. Relocating/renaming the artifact is deliberately out of
scope for this promotion (it would be a larger change and risks reintroducing
path-based governance inference); the governed marker in metadata + manifest +
this review is authoritative.

## Required review questions

### 1. Does the rebuilt candidate satisfy the #171/#172 promotion gate?

**Yes.** Re-verified directly against the committed files:

- Upstream source refs present (`sourceArtifacts`, `inputSources`, manifest `sources`).
- Retrieval/version metadata complete (`retrieval_metadata_complete` passes) plus
  a `sha256` checksum over the exact consumed bytes per source
  (`source_checksums_present` passes) — satisfying the gate's "checksum and/or
  immutable ref" requirement.
- Validation report: **16/16 checks pass**.
- Coverage: 32 teams, Weeks 1–18, **544 = 32 × 17** rows, byes handled, no
  missing/unexpected teams.
- Null/deferred policy honest; deterministic, byte-stable rows (unchanged by promotion).
- Contract can express the governed marker (#175/#176), and the full contract
  gate (`validateTeamWeekRawArtifactV0`) accepts the promoted artifact.

### 2. Are source refs, retrieval metadata, checksums, validation, and lineage sufficient for governed source use?

**Yes.** Every consumed source records `sourceRefs`, `retrievalMethod`,
`retrievalTimestamp`, `packageVersion`, `sourceUrlOrDatasetId`,
`transformCodePath`, and a `sha256` `checksum`. The validation report and lineage
manifest are present and referenced from the artifact
(`validationReportPath`, `lineageManifestPath`).

### 3. Is the remaining source mutability acceptable?

**Yes, under the gate as written.** nflverse release-asset URLs are mutable
rolling files and no immutable per-release ref is exposed; the #171/#172 audit
gate explicitly accepted a content checksum *and/or* an immutable ref. The
`sha256` checksum pins the exact bytes consumed at `retrievalTimestamp` so any
future rebuild can detect upstream drift, and the mutability is documented
honestly (artifact `provenanceNotes`, manifest `mutabilityNote`). This residual
is recorded, not hidden; it does not block promotion under the established gate.

### 4. Is the pressure deferral acceptable?

**Yes.** This is exactly the Option B posture decided in #173/#174 and made
expressible by the #175/#176 contract: `pressureRateAllowed` is optional /
non-blocking for governance, null on every row, and machine-readable `deferred`.

### 5. Are red-zone partial nulls and pressure deferred nulls free of null-to-zero laundering?

**Yes.** `pressureRateAllowed` is `null` on all 544 rows and marked `deferred`;
the 11 red-zone zero-denominator nulls are marked `partial_nulls` (a legitimate
undefined ratio, not a deferral). `findTeamWeekRawDeferredFieldViolations`
reports **0** violations — no deferred field carries a numeric/zero value.

### 6. Is the no-fantasy-splits / downstream-safety boundary preserved?

**Yes.** All eight fantasy-point split fields are `null` on every row (0 non-null
values); no fantasy/ranking/product output is produced.

### 7. Is there any remaining blocker that should withhold promotion?

**No mechanical blocker.** The only outstanding element was the explicit human
governance signature, which this review supplies under operator authorization.
The source-mutability residual (Q3) is documented and accepted under the gate.

## Decision

**APPROVE — promote to `governed_real_data`.** Set by this review:

- `metadata.provenanceStatus: governed_real_data`
- `metadata.governance.governanceStatus: governed`
- `metadata.governance.governanceSource: explicit_marker`
- `metadata.governance.notes` and `metadata.governance.reviewRefs` recording this
  review (`docs/reviews/team-week-raw-v0-2024-promotion-review-pr-d.md`,
  `TIBER-Data#179`).

`resolveTeamWeekRawGovernance()` returns `governed` **only** because the explicit
marker and `provenanceStatus: governed_real_data` agree; absent either, it fails
closed to ungoverned. The lineage manifest and validation report were updated to
record the promotion (the report's pre-promotion `non_governed_status` check is
replaced by `governance_marker_consistent`). Pressure remains null/deferred and
no deferred-field violation exists.

The promotion was applied deterministically by
`scripts/promote_team_week_raw_v0_2024_candidate.py`, which re-verifies the data
gate and fails closed if any invariant (validation data checks, pressure null,
no deferred-field violations, checksums, full coverage) does not hold.

## Allowed downstream posture

With this promotion, TIBER-Teamstate may consume the artifact as a **governed**
`team_week_raw_v0` source, provided it honors the field-readiness metadata:
`pressureRateAllowed` is `insufficient_data` / unavailable (never zero or
backfilled), and red-zone `partial_nulls` are undefined ratios. TIBER-Forecast
Run 2 may proceed treating pressure as an unavailable feature (no fabricated
feature; no-leakage boundary intact). This review makes **no** Teamstate or
Forecast change; it only states the posture a separately-scoped downstream
change must honor.

## Out of scope (unchanged by this review)

No new source logic, no source re-fetch, no pressure sourcing/backfill/zero-fill,
no row value changes, no Teamstate/Forecast changes, no model training, no
fantasy/ranking output.
