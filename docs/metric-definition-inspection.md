# Metric-definition inspection candidate

This Data-only implementation follows the decision study in
[PR #285](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/285).
Joe authorized preparing a separate implementation PR on 9 November 2026.
PR preparation does not grant merge, canonical metric approval, source admission,
consumer activation, deployment, or changes to ROP or fantasy rankings.

## Ownership

The existing `data/semantics/projection_input_semantics.json` is the only editable
inspection descriptor registry. The `definition_inspection` section contains
source-pinned implementation inspections, proposals and artifact selectors.
Producer code retains authority over its behavior. Inspection descriptors do not
override that code or resolve unresolved provider semantics.

The viewer reads these descriptors, checks exact source commits and SHA-256
digests against Git objects and the working tree, then generates JSON/Markdown.
Each exact definition has its own digest; every response also has a catalog
digest. A changed producer or missing Git object blocks inspection until the pin
and descriptor receive review. Hash validation detects drift, not semantic truth;
synthetic producer parity tests provide an additional bounded check.

Generated views must not be edited. Existing code-owned dictionaries, such as
`RB_CONTACT_EVASION_METRIC_DICTIONARY`, remain their own authority; a future
catalog adapter should read those descriptors directly rather than copying them.
That RB adapter is outside this receiving-usage slice.

## Commands

Run from the repository root, with the pinned Git history available:

```bash
node scripts/inspect_projection_input_semantics.mjs --definitions list
node scripts/inspect_projection_input_semantics.mjs --definitions get --id 'route %'
node scripts/inspect_projection_input_semantics.mjs --definitions get --id inspection.route_share.sum_player_routes.v0
node scripts/inspect_projection_input_semantics.mjs --definitions compare --left inspection.route_share.sum_player_routes.v0 --right inspection.route_participation.team_dropbacks.proposed.v0
node scripts/inspect_projection_input_semantics.mjs --definitions coverage --artifact weekly_usage_2025.source_backed
node scripts/inspect_projection_input_semantics.mjs --definitions coverage --artifact weekly_usage.offline_fixture
node scripts/inspect_projection_input_semantics.mjs --definitions list --write
node scripts/inspect_projection_input_semantics.mjs --definitions list --check-generated
npm run test:metric-definition-inspection
python -m pytest tests/test_metric_definition_source_parity.py -q
```

Definition operations emit JSON; `--json` is accepted explicitly. Exit codes:

| Exit | Meaning |
| --- | --- |
| 0 | The requested inspection operation completed; no consumer authorization is implied |
| 1 | Invalid request/registry, source drift, unavailable pin, or stale generated view |
| 2 | Concept/artifact not indexed, or an exact definition selection is required |

Family and field names always require an exact-ID selection, including a family
with one indexed variant. `route %` lists summed-player-route share, the gold
compatibility alias, and proposed dropback participation. No default is selected.
Unknown concepts remain `not_indexed`; nearby proxies are not substituted.
Legacy `--group`, `--status`, `--consumer` and legacy Markdown generation retain
their existing behavior. They cannot be mixed with definition operations.

## Meaning and data are separate

The seven `inspection.*` IDs are inspection identities, not newly approved
canonical metrics. They distinguish:

- gold target share using silver team targets, including the unchanged legacy
  zero fallback for a null/zero/negative denominator;
- weekly upstream target-share passthrough, whose exact formula stays unresolved;
- route share using summed input player-routes;
- the compatibility builder's `route_share` to `route_participation` alias,
  which retains that same summed-player-route denominator;
- proposed actual routes per eligible team dropback, with unresolved event rules;
- targets per actual route;
- the separate on-field pass-play participation proxy scaffold.

Definitions return formulas, components, fraction units, player/team/week grain,
source pins/symbols, caveats, explicit event/aggregation uncertainty, and approval
status. They return no player observations. Comparisons return `incompatible`
for known component/unit/grain conflicts, `unresolved` where equivalence is not
established, or `same_definition` for an identical ID. Every comparison leaves
observation comparability `not_assessed`.

Coverage is a separate operation over two allowlisted committed artifacts. It
returns their exact source pin/digest, row and missing/non-null/zero/invalid-value
counts, observed season/week keys, explicit season-type uncertainty, source
classification, definition-binding status, unknown clocks and population
completeness. It returns no player-level values and makes no source-admission or
current-2026 coverage claim. Non-null values are `unqualified_values`; an existing
populated source-backed field is not automatically a valid measurement.

At the pinned baseline, the 2025 source-backed weekly input has 6,326 rows and no
populated routes, route participation or snap share. Its populated target share
retains the unresolved upstream formula binding. The six populated rows in the
promoted-path usage export are explicitly labeled fixtures and remain
`fixture_only`. Neither filename nor registry classification can promote them.

## Bounded release and later consumer gates

This version fixes `consumer_authorized=false` and `canonical_approval=not_granted`.
Neither caller options nor registry edits may switch those flags on under this
inspection schema. There is no HTTP/MCP endpoint, ingestion, data acquisition,
scoring operation, automatic update, or downstream export registration.

Before inspection acceptance: review the exact candidate head; verify generated
views, immutable source pins, behavior tests, legacy viewer compatibility and
the paired audit/validation record. Complete required checks and explicitly
dispose of baseline blockers without claiming an uncompleted full-suite pass.

Before any later measurement consumer: separately approve exact definitions and
source/event rules, bind admitted observations to those definitions, verify
identity and matching windows, freeze unit conversions and aggregation, reject
missing/proxy/fixture/mismatched inputs, review compatibility/recalibration, and
obtain explicit operator activation approval. Actual routes remain unavailable
until that source qualification exists. This inspection does not fill them.

Implementation handoff and validation:
[audit record](audits/metric-definition-inspection-2026-11-09/README.md).
