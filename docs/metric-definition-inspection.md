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

### Three meanings of route participation

Three different quantities in this repository carry a route-participation name.
They are not interchangeable, none is canonically approved, and no conversion
between them is defined.

| Meaning | Where it lives | Formula | Inspection ID |
| --- | --- | --- | --- |
| Summed-player-route share | `src/derive/gold.py`: `route_share` in `build_player_role_inputs_weekly`, copied unchanged to `route_participation` by `build_player_role_profile_compatibility_weekly` | player `routes_run` / sum of input-player `routes_run` for team, season, week | `inspection.route_share.sum_player_routes.v0`; `inspection.route_participation.gold_compatibility_alias.v0` for the copy |
| Proposed routes per team dropback | Proposal text only; no producer computes it | actual player routes / eligible team dropbacks, event rules unresolved | `inspection.route_participation.team_dropbacks.proposed.v0` (`proposed_ratio`) |
| FORGE targets per team pass attempt proxy | `src/export/forgeWeeklyDerivedArtifact.ts`: `routeParticipation` in `deriveSkillRecord` | player targets / team pass attempts, clamped to 0..1; 0 for QB rows or when team pass attempts are not positive | none; not indexed |

The FORGE proxy predates this inspection layer and is described here only so it
is not mistaken for either catalog variant. It uses no route counts: the same
export sets `routesRun` to `max(targets, receptions)` and flags the rows with
`routes_and_route_participation_approximated_from_team_pass_attempts_and_player_target_volume`.
It has no inspection ID and no source pin, so the viewer's drift checks do not
cover this paragraph; the export code remains the authority for its behavior.
A `route_participation` or `route %` lookup therefore lists the two catalog
variants only. That list is not an inventory of every route-participation field
in the repository.

The proposed dropback ratio stays unapproved. The fixture rows are not evidence
for it or for any other meaning above.

### `definition_ids` are references; `definition_bindings` are coverage bindings

The registry has two different links from a field name to an inspection ID.

- `entries[].definition_ids` is a navigation reference: it lists catalog variants
  that share the entry's field name. It is validated by ID existence and
  field-name match only. It does not state which variant, if any, produced the
  values in an artifact, and no viewer response reads it.
- `coverage_artifacts[].definition_bindings` is the only link a coverage receipt
  uses. A field absent from it is reported with `definition_id: null` and
  `definition_binding: "unbound"`.

The `route_participation` entry references the gold compatibility alias and the
proposed dropback ratio. Both usage-lane coverage artifacts leave
`route_participation` and `routes_run` unbound, and they stay unbound: a
reference never becomes a binding, and binding a field needs its own reviewed
change with source support. Unbound means the definition behind those values is
not established, including for the six fixture rows.

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
inspection schema. Failure responses (`invalid_request`, `invalid_registry`,
`inspection_blocked`) carry both flags too. The flags are denials: `false` and
`not_granted` never mean a metric may be used. There is no HTTP/MCP endpoint, ingestion, data acquisition,
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
