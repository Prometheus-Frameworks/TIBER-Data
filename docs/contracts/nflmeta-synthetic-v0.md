# NFLMeta synthetic contracts v0

Issue: [Data #287](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/287).
Provider audit: [Ops #94](https://github.com/Prometheus-Frameworks/TIBER-Ops/issues/94).

## Boundary

This is a **contract task**: schema-reference-only design, pure in-memory functions,
and invented fixtures. It qualifies no football data, season, player or identity.
There is no transport, SDK, API key, environment lookup, persistent store, public
MCP registration, package-root export or downstream integration. Neither function
admits a source or modifies the promoted identity crosswalk. Synthetic receipts
cannot establish actual provider publication, TIBER custody or replay rights.

We implement two source-boundary rehearsals under
`src/contracts/nflmetaSyntheticV0/`:

- `decodeSyntheticNflmetaPlayerGames(input, receipt)` validates a ranked
  player-game page and preserves its observations and metadata.
- `createSyntheticNflmetaReconciler(baseline)` accepts invented HTTP outcomes
  through `submit(status, body, receipt)`, stages a full mapping registry, and
  exposes a proposal only through `result()` after successful completion.

All fixture builders live under `test/fixtures/nflmetaSyntheticV0/`; their subjects,
IDs, dates and counts are invented. They are not retained provider specimens.

## Documentation basis

Read November 9, 2026:

- [Core endpoint semantics](https://nflmeta.org/api-docs/core-endpoints)
- [November 5 release entries](https://nflmeta.org/changelog)
- [OpenAPI](https://nflmeta.org/openapi.yaml)

Public OpenAPI retrieval: 857,943 bytes, info.version `1.3.0`, SHA-256
`49e25cfb6178c52c256ce7e554d5ebe025d5e58d5bbf14b5b4e5858d8f04ed9f`.
This identifies the inspected documentation only. The URL is mutable, and no
protected football response was requested or retained. The complete YAML contains
duplicate anchors rejected by PyYAML's standard whole-document loader; the two
selected path blocks parsed separately. We inspected those path declarations,
not a validated complete SDK specification. No downloaded OpenAPI copy is shipped.

The wire declaration for `meta.contract_version` is **string `"2"`**, despite the
prose's shorthand `2`. Other player-log/family routes retain their own contracts.
This v0 must not be applied to them by structural resemblance.

## Player-game observation rules

All 34 base statistic fields and their four-state `stat_status` entries are
required. `reported` requires a numeric value, including zero. `missing`,
`not_reported` and `partial` require null; no coercion, defaults or imputation.
Negative yardage and fractional defensive sacks remain representable. The
selected base statistic must equal `stat_value`. For the nine documented derived
rates, inputs must be reported, the denominator positive, and the selected field
present and equal to `stat_value`. Fractional percentage units and consistency
with the inputs are checked using an explicit TIBER synthetic acceptance tolerance
of `1e-6 * max(1, abs(expected))`. Actual provider rounding precision is unqualified;
we preserve the received value instead of recomputing or changing it.

Calendar dates stay dates (nullable where documented), never fabricated kickoff
timestamps. `providerWriteAt` is the serving-row write clock;
`evidence.receivedAt` is a simulated test receipt; publication stays null. A
content fingerprint remains opaque and non-monotonic: A → B → A is possible,
unchanged writes are possible, and polls can miss intervening changes. No
correction archive, historical cutoff witness or immutable page snapshot is
claimed. We do not order observations by fingerprint or rank.

The query metadata and original provider row, including additional fields, are
preserved as detached copies. Resolved player-game duplicates are rejected;
unresolved identities stay unresolved without name joins. Empty/filtered results
have unknown participation meaning. A reported numeric value remains
`provider_reported_unverified`; finality and upstream independence stay unknown.
This contract has no independently reconciled-fact branch because no independent
witness is supplied by this synthetic task.

## Cross-reference reconciliation rules

The baseline is a synthetic set of existing key-to-Sleeper bindings and an
optional completed version. We never mutate it. Only a full published-registry
traversal can produce a new proposal; batch and additions-only data cannot do so.

We require:

1. contiguous offsets starting at zero; matching version, total, snapshot and
   returned page limit; bound subsequent pages;
2. page-complete responses, affordable result windows, consistent row counts and
   continuation metadata;
3. relative continuation URLs on the declared cross-reference path with the
   exact version/snapshot/offset/limit; no duplicate parameters or scope changes;
4. a terminal `complete=true` with exactly the declared total staged rows;
5. unique registered mapping IDs within the snapshot boundary, valid verified
   identity fields, and no conflicting alias/canonical/Sleeper relationships.

The caller retains the supplied continuation URL verbatim. The implementation
validates it but never fetches or reconstructs a request. This rehearsal allows
at most 1,000 rows/page, 10,000 registry rows and 1,000 aliases/row. These are
bounded TIBER acceptance limits, not claims about a purchased provider tier.

A 409, other HTTP failure, malformed body, page inconsistency or caller `abort()`
discards every staged row and makes the instance terminal. Restart requires a
new instance; the baseline does not advance. Returned state reveals only progress,
not partial rows. `result()` is null while incomplete and returns detached copies
when terminal.

A matching conditional `unchanged` result reuses a supplied completed version;
it is not an empty new baseline. An empty complete registry also does not erase
existing identities. Needs-review/null/absent relationships cannot clear IDs.
Verified aliases may propose additional provider-key bindings. Every proposed binding
labels its basis as a current provider-verified relationship or a retained existing
identity without current verification. Preserving an ID does not renew its evidence.
If any established
binding conflicts, the whole proposal is withheld and the previous completed
version retained. This is a proposal, never automatic promotion or overwrite.
Full registry completion is not a player census or claim-eligibility check.

## Validation and remaining gates

Run focused checks:

```bash
npm run typecheck
npx vitest run test/nflmetaSyntheticPlayerGame.v0.test.ts test/nflmetaSyntheticCrossReferences.v0.test.ts
npm run build
```

Repository pre-PR validation: `./scripts/pre_pr.sh` with the declared Node/Python
dependencies installed. The paired implementation audit is under
`docs/audits/nflmeta-synthetic-v0-2026-11-09.*`; independent review is pending.

Passing synthetic tests establishes an internally consistent contract rehearsal.
It does not certify real payload conformance, current coverage, billing, source
freshness, independent corroboration or actual identity matches. Before any
later authenticated qualification, we still need a separately bounded purpose,
access entitlement, retention/replay/reviewer/successor permission, and an
admission decision. No provider email or purchase follows from this work.
