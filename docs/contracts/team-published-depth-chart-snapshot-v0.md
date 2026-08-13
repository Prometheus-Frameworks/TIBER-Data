# Team-Published Depth Chart Snapshot v0

`team_published_depth_chart_snapshot_v0` is TIBER-Data's candidate-only contract for one bounded claim:

> This is the depth chart an NFL team published as of the source-supported date.

It is not a claim about who will start, make the roster, dress, play, run a route, receive a target, carry the ball, or produce fantasy points. The contract is deliberately separate from `roster_snapshot_v0`, availability/injury evidence, Teamstate interpretation, and actual role/opportunity evidence.

Normative JSON Schema: `schemas/team_published_depth_chart_snapshot_v0.schema.json`.

The 32-team discovery companion is governed by `schemas/team_published_depth_chart_source_registry_v0.schema.json`.

## Source boundary

A qualifying source is published by the club on its official website or as a club-hosted article, media/game release, image, or PDF. A chart prepared by the club's media-relations or communications department qualifies as a team publication. If the team labels its chart `unofficial`, preserve that label exactly; it remains canonical for what the team published.

The validator couples each `team_abbr` to its explicit official hostname. Both `canonical_source_url` and every receipt URL must satisfy that team-specific policy, and the canonical URL must have an exact receipt. Shared asset hosts are fail-closed exceptions: this pilot recognizes only the observed Arizona `static.clubs.nfl.com/image/upload/cardinals/` prefix for Arizona. A globally official hostname belonging to another team is not sufficient.

The following are never fallback truth:

- third-party projections;
- beat-writer or analyst ordering;
- ESPN, CBS, Ourlads, FantasyPros, or equivalent depth-chart surfaces;
- search-result snippets;
- social screenshots without a canonical team publication.

If a qualifying publication cannot be found or retained, emit an explicit registry state. Do not fill the gap.

## Required envelope

Each snapshot carries:

- the fixed `artifact_type`, `contract_version`, and `assertion_scope`;
- stable `snapshot_id`;
- team, season, and phase;
- separate `chart_as_of`, source `published_at`, and TIBER `observed_at` clocks;
- publisher and stated publishing department;
- the source's raw official/unofficial label;
- canonical official source URL;
- one or more content-hash-pinned source receipts;
- transcription method/version, source and normalized counts;
- normalization and verification state;
- previous/superseded snapshot lineage;
- warnings and review clock;
- ordered source rows and entries.

Null is required when a source does not expose an effective/publication clock or when identity is unresolved. Retrieval time must never fill a missing publication clock.

`normalization_status: complete` is strictly lossless in v0. `source_row_count` must equal `normalized_row_count`, and `source_entry_count` must equal `normalized_entry_count`. A dropped, merged, or otherwise unreconciled source row or entry remains `partial` or `quarantined`; v0 has no exception structure for lossy reconciliation.

## Receipt rule

Every normalized snapshot must point to the exact bytes that supported it. A receipt records URL, retrieval clock, MIME type, byte length, SHA-256, optional source validators (`ETag`/`Last-Modified`), archive status, and immutable repository path when storage is authorized.

`stored_immutable` requires a non-null repository-relative path under `data/raw/depth_charts/`. Validation requires the file to exist and recomputes both byte length and SHA-256 from those bytes. Missing, escaping, symlinked, length-mismatched, or hash-mismatched evidence fails closed. Other receipt states require `immutable_receipt_path: null` and cannot support a verified-current snapshot.

Technical access is not a redistribution license. Under `AGENTS.md`, an official source with no observed redistribution grant remains blocked from repository mirroring until the rights disposition is recorded. A URL plus hash is an observation receipt, not a substitute for retained immutable bytes.

## Row and entry semantics

Rows preserve the source's unit and repeated position instances. `row_instance_id` identifies the visual/source row, not a football rank.

Entries preserve:

- exact display column and order inside wrapped cells;
- co-list/alternative group identity for `OR` relationships;
- jersey number when printed;
- exact raw name and source text;
- raw underline, bracket, `OR`, slash co-list, and wrap markers;
- explicit empty `decoded_marker_meanings` and null `decoded_marker_legend_reference` fields;
- canonical player ID or `null`;
- explicit identity status and resolution method.

An underline is not automatically decoded as `rookie`, and brackets are not automatically decoded as an injury designation. Contract v0 prohibits marker decoding: `decoded_marker_meanings` must remain empty and `decoded_marker_legend_reference` must remain `null`. Any future decoded semantics require a separately reviewed contract that can independently bind exact legend content to retained official evidence.

Every identity state other than `resolved_exact`—including `ambiguous_multiple_matches`—requires `player_id: null`. `resolved_exact` requires both a non-null canonical `player_id` and a non-null explicit `identity_resolution_method`. Raw entries remain present regardless of resolution outcome.

`display_column` is descriptive source layout. It must never be renamed or interpreted as actual `rank`, starter probability, or workload order.

## Freshness and latest selection

The clocks have different meanings:

- `chart_as_of` / `published_at`: evidence currency;
- `observed_at` / registry `last_checked_at`: monitor health.

Latest selection follows these rules:

1. Contract v0 never infers monitor health from hash equality. An equal hash is only a stable observation and does not create or advance a snapshot. Any future health claim requires a separately governed run-record contract with distinct run identity and clocks.
2. Every changed qualifying source is a new candidate receipt; a changed source whose parse fails is quarantined and cannot advance.
3. A candidate advances `latest` only after full schema and semantic validation, nonempty and exactly reconciled source/normalized row and entry counts, team-coupled canonical/receipt policy, review validation, and recomputation of every immutable receipt's byte length and SHA-256.
4. Advancement is permitted only within the same contract/assertion/team/season stream and only when the retained source-hash set changed.
5. `latest` is selected first by the newest verified `chart_as_of` date, then by the full timezone-aware `published_at` value—not retrieval time or a truncated publication date.
6. Null `chart_as_of` is ineligible for advancement even when `published_at` exists; an undated mutable page may be captured but cannot supersede a dated verified snapshot.
7. A changed source that fails parsing is quarantined while the prior verified latest remains unchanged.
8. A stale source cannot be made current by regenerating it.

An operational daily/event-triggered monitor and any all-32 rollout require separate approval.

## Deterministic diff

A semantic entry key is:

```text
(unit, row_instance_id, display_column, display_order_within_column, raw_source_text)
```

A snapshot diff sorts keys lexically and emits explicit `added`, `removed`, and `changed` records. Identity changes are not permitted to erase the raw source key. An unchanged source hash yields an empty diff. A real successor snapshot—not a synthetic artifact—is required before lineage is considered proven for rollout.

## Registry states

The source registry contains exactly 32 team rows and supports:

- `not_yet_published`
- `official_source_discovered`
- `captured_candidate`
- `verified_current`
- `superseded`
- `parse_blocked`
- `official_source_conflict`
- `monitoring_degraded`
- `official_source_unavailable`

Unchecked candidate URLs are discovery hints, not confirmed availability. A registry row may point at an official team hostname while still declaring monitoring degraded.

Normalized candidate enumeration is itself bounded. `data/candidate/depth_charts/normalized_candidate_manifest_2026-08-10.json` names the only authorized pilot teams, exact candidate directory, and sorted candidate paths. Validation derives the candidate count from agreement between that manifest and the directory; an unlisted file or out-of-scope team fails closed. The current empty list is evidence-backed by the immutable-receipt blocker, not a hard-coded validator result.

## Fail-closed behavior

- Conflicting official surfaces are retained independently. If official currency cannot be established, emit `official_source_conflict` and retain the prior verified snapshot.
- Parser failure quarantines the changed candidate.
- Ambiguous layout remains raw and partial; it is never silently flattened.
- Failed identity resolution retains the raw entry.
- Fetch failure degrades monitoring and retains the prior verified snapshot.
- Absence means only `absent_from_this_publication` unless another separately governed source proves more.
- No writer under this contract targets `exports/promoted/**`.

## Candidate and consumer boundary

This contract authorizes contract validation and candidate evidence only. It does not activate TIBER-Fantasy, Forecast, FORGE, Teamstate, Role-and-opportunity-model, a product surface, a scheduler, a promotion, or a merge.
