# Dated redraft ADP v0 source-readiness audit — 2026-08-10

## Answer first

TIBER-Data is accepted as the D0 source-truth owner for immutable, source-specific market observations. No source is ready for operator activation.

TIBER-Fantasy PR #304 is useful prototype evidence: it proves a compact snapshot shape, provider IDs, sample-window metadata, three exact 2026 request configurations, and a dated-file pattern. It does not establish source rights, an exact ADP definition, draft population/type, source publication or revision clocks, a lawful trailing-12-month archive, or an exact provider-to-GSIS bridge. Those are admission blockers, not implementation details.

This audit accessed no external market source, copied no external market rows into TIBER-Data, and created no adapter, snapshot, identity edge, schedule, candidate artifact, promoted artifact, or downstream behavior.

## Authority and task class

- Tracking issue: [TIBER-Data #235](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/235)
- Operator activation: [issue comment 5241761961](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/235#issuecomment-5241761961)
- Task classes: provenance/source audit, external-dataset audit, and contract design only
- Evidence cutoff: 2026-08-10T00:00:00Z
- Authorized write surface: this paired Markdown/JSON audit under docs/audits
- Mandatory stop: draft PR for operator review

Explicitly outside authority: live API access, scraping, credentials, purchase, subscription, license acceptance, download, retention, mirroring, backfill, adapter, scheduler, database, candidate rows, identity promotion, source promotion, consensus, strategy, ranking, advice, UI, downstream wiring, merge, and deployment.

## Pinned evidence and collision check

### TIBER-Data

- Repository: Prometheus-Frameworks/TIBER-Data
- Base branch: main
- Base commit: 44296134a178f9d53fd7eda01a94548e76160d29
- AGENTS.md blob: 7fdc142c1a621ed254ca752f89474fff918a4bd1
- TRUTH_SOURCES.md blob: 27eec691b8e8535024a1bef1d342d67c83785e1c
- Bucky Irving canonical identity evidence: exports/promoted/nfl/player_season_coverage_v0.json, blob f7b2918b978d842cd8753a7f3dedd3836934859b, GSIS 00-0039361

At branch creation, the only open Data PR returned by the collision inventory was draft PR #247 on branch codex/issue-245-offensive-participation-readiness. It changes a different paired audit. It does not overlap either issue-235 path. No issue-235 branch already existed.

TIBER-Data #241 is adjacent identity work, not authority for this task. Its proposed normalized-name candidate path cannot become a governed join here.

### TIBER-Fantasy prototype

- PR: [TIBER-Fantasy #304](https://github.com/Prometheus-Frameworks/TIBER-Fantasy/pull/304), merged
- Base: 5e983b0d7315b817aa99ffc1016304d04f2d6bd0
- Head: 39eee962aa754781e4c3f8a9939d96f42a355293
- Merge: 93e26825fb4dbafec722083a2704a0cc59f5aac5

| Evidence | Git blob SHA-1 | Audit use |
|---|---|---|
| data/adp/README.md | 7406c03e730286895bb0833a9f2a74889ddd4d4f | Prototype contract/caveats only |
| scripts/fetch_adp_snapshot.mjs | e31234596e951a64f7b22714b158ae3161f09745 | Prototype request/write behavior only |
| 2026 half-PPR, requested 10-team dated file | c0201a44cf27d4958cea091fb9b14919967b571b | Committed metadata only |
| 2026 PPR, requested 10-team dated file | ff362cfa071dc0180999c6be43de96a8c315515c | Committed metadata only |
| 2026 PPR, requested 12-team dated file | 792ffe7b2419df1925e0daebc6f0a575f34d4b73 | Exact lane audited |
| three latest aliases | same three blobs above | Mutable-alias risk only |

No endpoint was called to produce this audit. The audit reads already-committed repository evidence at an immutable Git ref.

## Ownership decision

TIBER-Data is accepted as the source-truth owner for this D0 evaluation because a dated market snapshot is an external observation whose trust depends on provenance, rights, exact market semantics, identity, clocks, immutable history, missingness, and validation.

The boundary remains:

- TIBER-Data: source admission, exact market contract, provider identity, clocks, immutable snapshots, validation, and any later promotion.
- TIBER-Strategy: market interpretation, Board Geometry, tier policy, and strategic cohort policy.
- TIBER-Research: bounded empirical questions consuming admitted snapshots.
- TIBER-Fantasy / Observatory: truthful display and claim-assessment states.
- TIBER-Ops / operator: source-rights admission, implementation activation, promotion, and downstream authority.

Accepting ownership does not admit a source or authorize a build.

## Source and rights matrix

| Source/product | Access evidence | Measure and population | Identity | History/cadence/clocks | Rights | Status |
|---|---|---|---|---|---|---|
| Fantasy Football Calculator API v1 ADP endpoint, exact product name/documentation not pinned | PR #304 code performs an unauthenticated GET. This audit did not repeat it. | Response uses an adp field, but calculation semantics are unverified. Managed redraft, mock, best-ball, contest, and other population distinctions are unknown. | Provider player_id exists. No governed FFC-to-GSIS bridge exists. | Prototype has source-reported calculation-window dates and retrieval time. Source as-of, generated, available, revision, publication cadence, and lawful historical availability are unknown. | Automated access, retention, exact-value storage, reproducibility, redistribution, display, attribution, rate limits, and license/credential duties are all unreviewed. | Issue status: unknown. AGENTS classification: schema_reference_only. Not admitted. |

The prototype is design evidence, not an external source admission. Public visibility or a working request does not grant automated-access, storage, archival, display, or redistribution authority.

### First-source finding

There is no recommended first source for activation. FFC is the only source-shaped prototype inspected, but it cannot be advanced while the following remain unresolved:

1. pinned source documentation and exact metric definition;
2. exact draft population and draft type;
3. meaning of team-count configuration;
4. source as-of, generated, available, and revision clocks;
5. source publication/correction behavior and cadence;
6. lawful current and historical access, retention, exact-value storage, display, and redistribution;
7. stable immutable payload or source-reference support; and
8. exact provider-ID-to-GSIS identity.

The smallest honest next step is a separately authorized source-and-rights review that binds one provider product and its full use envelope. It is not an adapter task.

## Exact 2026 market configuration audited

The exact prototype lane examined is:

| Dimension | Observed value | Readiness |
|---|---|---|
| Source request | /api/v1/adp/ppr?teams=12&year=2026 | Observed in committed prototype |
| Season | 2026 | Present |
| Source scoring label | PPR | Present |
| Reception points | Unknown | Blocking |
| Requested/meta team count | 12 | Present |
| Team-count population semantics | Unknown; prototype README says the parameter mainly affects round.pick formatting | Blocking |
| Draft type | Unknown | Blocking |
| Population scope | Unknown | Blocking |
| Contest/roster context | Unknown | Blocking |
| Source measure name | adp | Present |
| Governed measure ID/definition | Unavailable | Blocking |
| Sample window | 2026-07-31 through 2026-08-07 | Present |
| Source-reported total drafts | 4,929 | Present |
| Source as-of/generated/available/revision | Unknown | Blocking |
| Retrieval time | 2026-08-07T13:58:25.891Z | Present, but not a source clock |
| Player count | 256 | Present |
| Admission/eligibility | Ineligible | Fail closed |

This is a requested configuration, not yet an exact governed market object. In particular, PPR must not be expanded into an assumed reception-points rule, and teams=12 must not be treated as proof of a distinct 12-team draft population.

## Prototype inventory: what it proves and what it does not

PR #304 changed eight files total: six snapshot JSON files, one README, and one fetch script. The six snapshot files contain three unique payload blobs because each latest alias is byte-identical at the pinned commit to its corresponding dated file. The three persisted retrievals occurred at 02:11:50.897, 13:58:25.891, and 13:58:31.704 UTC on the single retrieval date 2026-08-07.

| Source label | Requested teams | Sample window | Source-reported drafts | Rows |
|---|---:|---|---:|---:|
| Half-PPR | 10 | 2026-08-01..2026-08-06 | 1,731 | 211 |
| PPR | 10 | 2026-07-31..2026-08-07 | 4,929 | 256 |
| PPR | 12 | 2026-07-31..2026-08-07 | 4,929 | 256 |

This proves three persisted retrievals on one retrieval date and a candidate vocabulary. It does not prove six historical observations, daily history, source cadence, current source time, different underlying 10-team and 12-team populations, lawful retention, or a governed source lane.

The latest files are overwritten by the prototype script. A mutable latest alias can be a convenience pointer in a future system, but it cannot be the immutable historical object or the thing whose prior bytes are silently replaced.

## Market-measure dictionary

- ADP: may populate a governed value only after the source defines the calculation and draft population. A field named adp is insufficient on its own.
- Median pick: a separate measure. It cannot be relabeled as ADP unless the source explicitly defines its ADP that way.
- Overall rank and position rank: provider rankings, not ADP.
- Expert rank: an opinion/ranking object, not ADP.
- Provider consensus: a source-specific product. Its disclosed components and method remain attached.
- TIBER consensus: unavailable and out of scope without a separately approved, versioned methodology.

Source-native adp_formatted, high, low, stdev, and times_drafted fields remain source-native context until their definitions, units, and population relationship are pinned. Missing sample size remains unknown.

## Candidate contract sketch

Candidate ID: dated_redraft_adp_snapshot_v0.

Snapshot grain:

~~~text
one source product
x one exact market configuration
x one NFL season
x one source calculation window
x one source/as-of time
~~~

Required snapshot fields:

- schema_version, snapshot_id, and season;
- source owner, product, platform, immutable reference, revision ID, and payload digest;
- market-measure ID, source-native name, and pinned definition reference;
- scoring format, reception points, league/team count, draft type, population, and roster/contest context;
- calculation-window start/end;
- source as-of, generated, available, retrieval, artifact-generation, and claim-cutoff clocks;
- source-access/rights state and cadence-policy ID;
- row count, validation status, warnings, gaps, and definition version;
- append-only supersession ID, reason, correction-observed time, corrected revision, and changed-field summary.

Required player-row fields:

- snapshot ID;
- canonical GSIS ID when exactly resolved;
- provider player ID;
- player name, team, and position as non-authoritative context;
- market-measure ID and value only when source-defined;
- source-supplied overall/position rank where present;
- source-supplied sample size/draft count and explicit availability state;
- observation/identity status and unresolved reason;
- immutable source-row reference and warnings.

Invariants:

- a row belongs to exactly one immutable snapshot;
- null/unknown never becomes a plausible default;
- ranks, median pick, expert opinion, consensus, and ADP never share one ambiguous field;
- values never lose source product or market configuration;
- unresolved identity remains visible;
- corrections append and supersede rather than overwrite.

These are design requirements only. No schema file or source row is created here.

## Identity contract

GSIS is canonical join authority. Bucky Irving's canonical trace ID 00-0039361 is pinned to TIBER-Data exports/promoted/nfl/player_season_coverage_v0.json at blob f7b2918b978d842cd8753a7f3dedd3836934859b. That artifact is canonical identity evidence for this trace, not market evidence.

The FFC prototype carries provider IDs, but there is no governed FFC-to-GSIS edge. Player names, teams, positions, approximate values, and provider IDs from unrelated sources cannot authorize a match. Bucky's presence in the prototype does not make the row claim-ready, and this audit deliberately does not republish its market value.

TIBER-Data #213 is parked and concerns Sleeper-to-GSIS, so it cannot solve an FFC identity edge. TIBER-Data #241 proposes normalized-name candidates, but a name match is not governed identity and is outside this activation.

Provider-ID reuse, duplicate IDs, conflicting GSIS edges, trades, suffixes, and renamed players fail closed or require explicit operator review. Unresolved rows stay unresolved.

## Clock semantics and current selection

Preserve separately:

- calculation-window start/end;
- source as-of;
- source-generated time;
- source-available time;
- retrieval time;
- artifact-generation time; and
- downstream claim cutoff.

A retrieval timestamp is not a source as-of timestamp. A repository commit time is provenance, not a market clock. A sample-window end date is not automatically a source publication or as-of timestamp.

Current selection is:

~~~text
latest eligible immutable source snapshot
on or before the claim cutoff
for the exact source product and market configuration
~~~

Eligibility requires admitted rights, a defined metric/population, exact scoring/team-count/draft-type match, source as-of at or before cutoff, valid freshness under a source-specific cadence, valid schema/digest, resolved anchor identity, and non-fixture status.

If two snapshots have the same documented source clock, use documented source revision order and then immutable snapshot-ID order. If source revisions remain indistinguishable or conflict, return unavailable rather than choose.

For the 2026-08-10T00:00:00Z audit cutoff, the prototype returns unavailable because its rights, market definition, source clocks, and identity are unresolved.

## Trailing-12-month history

For the pinned example cutoff, the exact window is 2025-08-10T00:00:00Z through 2026-08-10T00:00:00Z.

Rules:

- preserve every admitted immutable snapshot independently;
- compare only the same source product and exact market configuration;
- never splice sources, forward-fill, interpolate, or invent a historical as-of;
- return partial when lawful comparable observations cover only part of the window;
- distinguish source corrections from new market movement; and
- disclose expected and observed cadence gaps.

PR #304 supplies one retrieval date, not a trailing-12-month history. A 2026 retrieval cannot be backdated into 2025 history.

## Cadence and supersession

No cadence-policy ID is selected. That is an explicit blocked finding, not an omitted design decision. The source publication schedule is unknown, and PR #304's intended daily retrieval is a TIBER proposal rather than evidence of provider cadence or permission.

A future source-specific cadence must bind:

- known source publication schedule;
- operator-approved retrieval schedule;
- expected-snapshot rule and allowable delay;
- missed-snapshot and off-season behavior;
- event-triggered behavior; and
- definition/revision change behavior.

Corrections are append-only. A corrected snapshot records supersedes_snapshot_id, reason, correction-observed time, corrected source revision, and changed-field summary. It never mutates the prior dated object.

## Consensus, disagreement, and conflicts

- Keep every platform, product, configuration, and clock in a separate lane.
- Never average incompatible platforms, formats, draft types, league sizes, populations, or windows.
- Preserve a provider consensus as that provider's product.
- Disclose unknown component composition.
- Show material disagreement; do not pick the most favorable value.
- A future TIBER consensus requires a separate methodology, source list, weights, clocks, missingness rules, and operator approval.

## Same-position peer selector

Selector ID: same_position_nearest_adp_v0.

For Bucky, the selector operates on one exact admitted snapshot and selects the three eligible RB rows immediately above and three immediately below the anchor by numeric governed ADP. Ties sort by provider player ID lexically.

The receipt preserves selector ID/version, snapshot ID/digest, anchor GSIS/provider IDs, position, requested count per side, selected provider/GSIS IDs, exclusions/reasons, and tie-break rule.

Return unavailable when the anchor identity or governed measure is unresolved. Return partial only when an otherwise eligible snapshot has fewer than three valid peers on a side, with every exclusion disclosed. Never fill across platforms, mix historical and current snapshots, choose favorable comparators, or silently change the selector.

## Bucky Irving golden-trace plan

Requested lane: 2026 full-PPR redraft with an exact source-supported team count and draft type.

Required future output:

1. current eligible source-specific observation;
2. comparable snapshots in the trailing window;
3. nearest comparable prior-year observation, if present;
4. cadence gaps;
5. definition/configuration changes;
6. identity and sample-size limitations;
7. same-position peers from the same snapshot;
8. separate platform lanes;
9. disagreement without averaging; and
10. a claim-ready W4 receipt.

Execution is blocked by source admission, rights, market semantics, source clocks, history, and identity. Data may later report observations and missingness; it cannot label a dip, value, buy, or opportunity.

## Negative tests required for any later builder

| Case | Required behavior |
|---|---|
| Expert rank labeled as ADP | Reject |
| Median pick labeled as ADP without source definition | Reject |
| Best-ball returned for managed redraft | Reject |
| Half-PPR returned for full-PPR | Reject |
| 10-team returned for 12-team | Reject |
| Unknown population treated as managed redraft | Unavailable |
| Platforms/products silently averaged | Reject |
| Unknown consensus composition hidden | Reject |
| Future snapshot selected for earlier cutoff | Reject |
| Retrieval time substituted for source as-of | Reject |
| Missing history forward-filled/interpolated | Reject |
| Correction overwrites prior snapshot | Reject |
| Unresolved identity falls back to name/team/position | Reject |
| Duplicate/reused provider ID silently accepted | Reject |
| Definition drift treated as comparable | Reject |
| Snapshot/row digest does not reconcile | Reject |
| Fixture/manual/schema-reference supports current claim | Reject |
| Mutable latest alias used as immutable history | Reject |
| Missing sample size inferred | Preserve unknown |
| Bucky/peer selection crosses snapshot or platform | Reject |
| Unknown rights state admitted | Reject |

## Proposed future paths

These paths are reserved design suggestions only and may be changed during a later repository-convention review:

- schema: schemas/dated_redraft_adp_snapshot_v0.schema.json
- builder: scripts/build_dated_redraft_adp_snapshot_v0.py
- validator: scripts/validate_dated_redraft_adp_snapshot_v0.py
- candidate: exports/candidates/market/dated_redraft_adp_snapshot_v0/<source_id>/<snapshot_id>.json
- validation receipt: same directory with <snapshot_id>.validation.json
- promoted: exports/promoted/market/dated_redraft_adp_snapshot_v0/<source_id>/<snapshot_id>.json

Path adoption, implementation, execution, independent artifact audit, promotion review, and promotion are separate gates.

## Downstream boundaries

Even a future source admission would not authorize Research execution, Strategy interpretation, Board Geometry mutation, Fantasy/Observatory integration, Claim Lens advice, FORGE/Forecast consumption, ranking, recommendation, merge, or deployment.

Allowed truthful consumer states are available, partial, unavailable, conflicted, and stale. Promotion in Data is not consumer activation.

## Handoff

Active task: issue #235 D0 governed redraft ADP source-readiness packet.

Files touched:

- docs/audits/dated-redraft-adp-source-readiness-audit-2026-08-10.md
- docs/audits/dated-redraft-adp-source-readiness-audit-2026-08-10.json

What is now true:

- TIBER-Data is accepted as D0 source-truth owner.
- PR #304 is pinned and classified as prototype/schema evidence only.
- The inspected FFC configuration is ineligible and no source is admitted.
- Contract fields, selectors, history rules, failure states, validation cases, ownership, and consumer boundaries are explicit.

What is still missing:

- an operator-approved source/rights envelope;
- source documentation and exact metric definition;
- exact population, draft type, team-count semantics, and source clocks;
- lawful 12-month history and source cadence;
- exact FFC-to-GSIS identity;
- any later implementation, independent audit, candidate acceptance, or promotion authority.

What must not be assumed:

- six files are six historical observations;
- a field name proves governed ADP semantics;
- PPR proves a reception-points contract;
- teams=12 proves a distinct 12-team draft population;
- fetched_at proves current source time;
- provider IDs or names resolve to GSIS;
- daily refresh is permitted or source-supported; or
- any current ADP, ADP-dip, or fantasy-value claim is supported.

Audit-trigger status: independent audit completed with three corrections requested and applied; post-fix reviewer verification remains pending.

## Validation

- Machine companion parsed as JSON before commit.
- Pinned repository files and Git blobs were re-fetched.
- Human and machine artifacts use the same evidence cutoff, ownership boundary, prohibited scope, blockers, and outcome.
- Branch contents are documentation-only.
- No external source/network request was made for source evidence.
- The three independent-review findings are addressed; post-fix reviewer verification remains pending.

## Terminal decision

~~~text
dated_redraft_adp_v0_requires_source_or_ownership_work
~~~
