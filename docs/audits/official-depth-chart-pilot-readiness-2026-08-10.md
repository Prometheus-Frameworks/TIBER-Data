# Official Depth-Chart Pilot Readiness Audit — 2026-08-10

## Answer first

TIBER-Data can now encode the source boundary, snapshot shape, 32-team discovery registry, clock separation, deterministic diff, and fail-closed latest-selection behavior. It cannot honestly commit the requested official source mirrors or normalized player snapshots yet.

The blocker is source-side redistribution authority, not HTTP access or parser feasibility. Six official pages/assets were retrieved twice and were byte-identical. None exposed a redistribution license, and the club pages assert an all-rights-reserved posture. `AGENTS.md` therefore prevents copying the full HTML/JPEG bytes into this public repository. Operator authorization to do the technical pilot is not a rights grant from those publishers.

This change stops before a player snapshot, promotion, scheduler, or downstream binding. The paired JSON contains the sole machine-readable completion decision.

## Classification and boundary

This is a combined contract, candidate-registry, provenance/source-audit, and external-source-audit task. It inherits every corresponding `AGENTS.md` constraint.

Allowed in this change:

- strict candidate contracts and validators;
- a 32-team source-discovery registry with honest unchecked/degraded states;
- URL/byte-count/SHA-256 observation receipts;
- deterministic failure and diff tests;
- source-format inventories derived from temporary read-only probes.

Not allowed without follow-up:

- mirroring full team HTML, JPEG, or PDF bytes without a rights/retention disposition;
- promoting any depth-chart artifact;
- an operational all-32 monitor;
- third-party fallback;
- product, Forecast, FORGE, Teamstate, Fantasy, or Role-and-opportunity bindings;
- interpreting a publication as actual deployment or availability.

## Pinned repository evidence

- Repository: `Prometheus-Frameworks/TIBER-Data`
- Base commit: `44296134a178f9d53fd7eda01a94548e76160d29`
- `AGENTS.md` blob: `7fdc142c1a621ed254ca752f89474fff918a4bd1`
- `TRUTH_SOURCES.md` blob: `27eec691b8e8535024a1bef1d342d67c83785e1c`
- Issue: [TIBER-Data #231](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/231)

The existing `roster_snapshot_v0` contract deliberately excludes depth-chart interpretation. This pilot therefore defines a separate assertion rather than overloading roster membership.

## Exact source observations

All source bytes were held only in temporary workspace storage for inspection and hashing. No source body or image is committed by this change.

| Team/source | Official URL | Effective/published clock | Bytes | SHA-256 | Refetch |
| --- | --- | --- | ---: | --- | --- |
| ARI article | [dated club article](https://www.azcardinals.com/news/the-first-depth-chart-of-the-season-2026) | chart 2026-08-02; published `2026-08-02T17:51:47.537Z` | 268,465 | `f3ba44dfd0f3f9151e427755c8fbcdd080bf23d7e06abf666603439ec86a94f2` | byte-identical |
| ARI chart | [original club-hosted JPEG](https://static.clubs.nfl.com/image/upload/cardinals/nicejzo6wgijyzgsmx28.jpg) | chart 2026-08-02; `Last-Modified: Sun, 02 Aug 2026 17:33:03 GMT` | 252,517 | `4c286b62db844bac44505a963f1cdd37e2f3e742066047df0d759b43255a786c` | byte-identical |
| WAS article/table | [dated club article](https://www.commanders.com/news/commanders-release-2026-unofficial-depth-chart) | published `2026-08-10T11:44:05.879Z` | 288,393 | `93097b8bf7012ee22d9f6f1b3c25f0147ea8984849a4a5d3fefad47dae54a2f1` | byte-identical |
| PIT page/table | [official mutable page](https://www.steelers.com/team/depth-chart/) | unavailable | 262,250 | `e6144ebe349c276b980b4b9198bb5906adb54c9277672a1ff6e100baef306167` | byte-identical |
| CAR page/table | [official mutable page](https://www.panthers.com/team/depth-chart) | unavailable | 253,176 | `00056e459650a686981d8dee4ffcaf49ef91af0659b909653331f5246515e6af` | byte-identical |
| BUF missing-state page | [official mutable page](https://www.buffalobills.com/team/depth-chart) | no chart published | 237,214 | `bf15815a2c13a324d3975f7da29ef3b631960debd59b31d01a5d1aa6c823601c` | byte-identical |

The full machine-readable observation ledger is `data/candidate/depth_charts/source_observation_receipts_2026-08-10.json`.

## Format probes

The format exercise used a dependency-free HTML table probe and manual visual inspection of the original Arizona image. Counts are audit evidence only; they are not normalized candidate snapshots.

| Team | Natural official format | Rows (O/D/ST) | Entries | Structural pressure |
| --- | --- | ---: | ---: | --- |
| ARI | dated article + image | 29 (11/12/6) | 100 | 3 `OR` groups, 13 underlines, 3 brackets, 3 wrapped entries, repeated position rows |
| WAS | dated article + 4-column HTML tables | 30 (12/12/6) | 103 | 7 `OR` tokens, 1 bracketed cell, 4 slash co-lists, 21 empty cells |
| PIT | undated mutable 5-column HTML tables | 30 (12/12/6) | 92 | 58 empty cells and no source effective clock |
| CAR | undated mutable 6-column HTML tables | 28 (11/11/6) | 89 | 79 empty cells and no source effective clock |

Arizona's manual source inventory found the expected non-rectangular layout and marker classes, but it has not received an independent second transcription. The source image does not expose a marker legend. Underlines and brackets therefore remain raw markers; they must not be decoded from convention alone.

Washington proves that `OR` can be appended to one table cell while its co-listed alternative appears in the next display column, and that slash co-lists can share one cell. Pittsburgh and Carolina prove that empty display cells and column counts vary even within first-party club HTML.

## Rights and retention blocker

The five publishers are first-party and the lineage is clear, so each is classified `external_candidate` under the narrow team-publication assertion. That classification does not supply redistribution rights.

No inspected source exposed a license allowing repository redistribution. The pages' copyright posture is all rights reserved. Under the repository rule, no declared license means no redistribution rights. Consequently:

- temporary technical retrieval was used only to inspect, count, and hash;
- full HTML/JPEG content is not committed;
- `repository_receipt_path` remains `null`;
- no snapshot can claim a stored immutable receipt;
- no candidate advances to verified current.

A follow-up must either obtain/record a rights and retention disposition or authorize a content-addressed, non-mirroring receipt design that an independent auditor accepts as satisfying the immutable-evidence requirement.

## Freshness and lineage result

The contract and validator encode these rules:

1. Effective/publication time and monitoring time are separate.
2. Byte-identical checks do not create snapshots.
3. Changed sources become candidates and cannot advance latest until validation passes.
4. Latest is selected by verified official effective/publication date, never retrieval time.
5. An undated mutable page cannot supersede a dated verified snapshot.
6. Changed-source parse failure retains the prior verified latest.
7. Conflicting official surfaces remain separate until official currency is resolved.

No later Arizona chart existed at the audit cutoff, so real successor lineage is not proven. The deterministic diff routine is tested with explicit test-only records; that is code-path validation, not substitute source evidence.

## 32-team registry result

`data/candidate/depth_charts/official_source_registry_v0.json` contains exactly 32 unique canonical team abbreviations. Only the hash-pinned pilot probes carry manual observation clocks. Unchecked team routes remain `monitoring_degraded` and explicitly say that no monitor was authorized. Buffalo is the bounded negative source case: its official page says the 2026 chart will be announced later, and the registry emits `not_yet_published` without fallback.

The registry is discovery/coverage metadata, not a runtime monitor and not evidence that every candidate URL currently resolves.

## Acceptance result

Implemented and testable now:

- official-host allowlist and third-party rejection;
- strict snapshot and registry schemas;
- exact hash-pinned observation ledger;
- 32-team registry;
- distinct source/monitor clocks;
- unresolved identity retention;
- deterministic diff order;
- no-op identical receipt handling;
- fail-closed latest retention on missing date or parse failure;
- no promoted output or downstream binding.

Still blocked:

- rights-cleared immutable source receipt storage;
- exact committed Arizona normalized snapshot;
- normalized Washington/Pittsburgh/Carolina format candidates;
- independent transcription/artifact review;
- real Arizona successor lineage;
- promotion design, scheduler, and broad rollout.

## Handoff

- Active task: bounded D0 official-depth-chart pilot for issue #231.
- Files touched: snapshot/registry schemas, contract documentation, candidate registry, source-observation ledger, paired readiness audit, validator, and tests.
- What is now true: source/format feasibility and exact observed bytes are pinned; contract and failure semantics are executable.
- What is still missing: immutable source retention and normalized player snapshots, plus real successor evidence.
- What must not be assumed: TIBER does not yet possess governed current depth-chart player hierarchy, and no publication proves actual deployment, availability, injury status, roster survival, or fantasy volume.
- Audit status: source/rights audit completed; any later receipt mirror, candidate snapshot, contract acceptance, or promotion still requires independent review.

