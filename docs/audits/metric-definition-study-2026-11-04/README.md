# TIBER metric definitions: decision study

**Prepared for Joe, 4 November 2026. Study and offline demonstration only.**

**Recommendation:** extend TIBER-Data's existing semantics inspection work with a
small, source-bound definition catalog. Start with receiving usage. Keep
definition approval, evidence availability, and football interpretation separate.
The useful next decision is whether to activate that bounded implementation.
This packet does not implement or authorize it.

## The practical reason

TIBER already owns much of the underlying specification. What is missing is an
easy way for a person or agent to retrieve the precise meaning of a field and
see where that meaning, source support, or scope remains unresolved.

This study found a concrete naming trap in committed code. The gold transform's
`route_share` divides a player's routes by the **sum of input player-routes for
the team-week**. A proposed routes-per-team-dropback definition uses a different
denominator. One team dropback can contain several player-routes. These two
fields must not be treated as aliases.

Illustrative arithmetic, with no real player, game, or validated event ledger:

| Expression | Counts | Result | Meaning |
| --- | --- | ---: | --- |
| Existing `route_share` formula | 21 routes / 105 input team player-routes | 20% | Share of counted player-routes |
| Proposed route-participation ratio | 21 routes / 30 eligible team dropbacks | 70% | Routes relative to team dropbacks |
| Pass-attempt denominator counterexample | 21 routes / 24 pass attempts | 87.5% | Different denominator; not an approved variant |
| Pass-play on-field proxy | 24 on-field plays / 30 eligible pass plays | 80% | Presence, not proof of running a route |

The mathematical contrast is demonstrated. Provider play eligibility, source
admission, and real-player route coverage are not established by this example.

## What was inspected

All TIBER-Data findings bind to
[`c46e9c34fd355bf922bc14eaeeb88fc9c3e77adc`](https://github.com/Prometheus-Frameworks/TIBER-Data/tree/c46e9c34fd355bf922bc14eaeeb88fc9c3e77adc).
The external reference is football-docs
[`5027a0946bced5e8e4e843f885d1c4bb93b0a421`](https://github.com/withqwerty/football-docs/tree/5027a0946bced5e8e4e843f885d1c4bb93b0a421),
whose package declares version 0.17.7 and MIT software licensing. Software
licensing does not admit or grant rights to its indexed providers' data.

The external source code and documentation were inspected as
`schema_reference_only`. No football-docs server was installed or run, no
provider corpus or feed was ingested, and no new upstream player data was
acquired. This is source inspection, not an end-to-end qualification of that
project. The evidence inventory is in [inspection.json](inspection.json).

## The pattern worth borrowing

| football-docs mechanism | Inspected implementation | Appropriate TIBER adaptation |
| --- | --- | --- |
| Metric family and exact variant IDs | `src/metrics.ts`; metric tests | Resolve a family first; cite the exact source/denominator definition used |
| Definition, formula, caveats, source checks | Metric-card schema | Carry authoritative source and unresolved questions; never label a proposal canonical |
| Exact versus approximate reference code | Metric variant schema | Distinguish arithmetic illustration, implementation reproduction, and provider validation |
| Explicit partial and missing retrieval coverage | `src/tools.ts`; search-coverage tests | A nearby document must not become an answer to an unsupported question |
| Signed, compatible documentation updates | `src/data-update.ts` | Preserve origin and compatibility checks; pin accepted versions for governed consumers |

The last item should not become a TIBER day-one auto-update system. A signature
can establish origin/integrity; it does not establish correct semantics, admitted
observations, or a valid football hypothesis. A source quote appearing in a page
likewise does not prove the inference made from it.

## Existing TIBER foundations

1. `data/semantics/projection_input_semantics.json` and its viewer already expose
   field descriptions, ownership, null behavior, and candidate/verification
   status. This is the natural integration point, subject to later review.
2. `src/contracts/v1/rbContactEvasionObservationsV0.ts` has a code-owned metric
   dictionary binding units, rules, rate components, caveats, and valid uses.
   A catalog should expose that authority, not create a second editable copy.
3. `src/contracts/v1/roleOpportunity.ts` constrains share values to 0-1 and
   includes model/version/source metadata. A numeric range alone does not
   specify a denominator or prove that data exists.
4. The participation readiness audit and receiving-role scaffold already keep
   on-field pass-play presence distinct from true routes. Preserve that work.

### Fresh, bounded coverage census

These are non-null counts in exact committed artifacts, not new source
admissions, a census of every repository, or current 2026 coverage.

| Inspected artifact | Rows | Non-null target share | Non-null routes / route participation / snap share |
| --- | ---: | ---: | --- |
| 2025 source-backed weekly usage input | 6,326 | 6,326 | 0 / 0 / 0 |
| Weekly usage export with row-level `offline_fixture` labels | 6 | 6 | 6 / 6 / 6, fixture only |
| Historical 2021-2025 WR subset of player-season coverage | 1,191 WR rows out of 3,016 total | 1,191 | 0 / 0 / 0 |

The 2025 weekly file includes week keys 1-22. It lacks an explicit season-type
field in these rows; its presence is not an assertion of a regular-season-only
window. The audit preserves that limitation rather than inferring one.

### Two additional issues the catalog must expose

**Target-share source bindings differ.** The gold transform calculates targets
over silver team targets. The weekly source-backed builder instead passes
through upstream `target_share`. The inspected weekly artifact does not pin the
exact upstream generator/definition version needed to retroactively bind that
value to the gold formula. These are separate inspection views; the study does
not conclude that their numerical values disagree.

**Existing missing-value behavior needs an explicit decision.** In the gold
target-share branch, zero, negative, or null team targets lead to `0.0`. General
Data doctrine prefers null/unknown when support is missing. The study records
that tension and preserves the existing behavior. A later repair needs its own
scope, compatibility assessment, and review; a documentation layer must not
quietly change it or describe it as already fail-closed.

## The reviewable prototype

[study.py](study.py) is a dependency-free, offline inspection demonstration. It
does not expose an HTTP endpoint or register an MCP tool. Its six `study.*` views
are explicitly noncanonical and unbound to runtime consumers:

| View | Status |
| --- | --- |
| Target share / gold team targets | Existing-code inspection |
| Target share / upstream weekly value | Existing-mapping inspection; exact formula binding unresolved |
| Route share / summed input player-routes | Existing-code inspection |
| Route participation / team dropbacks | Proposed ratio; play eligibility unresolved |
| Targets per actual route | Existing-code inspection; source support still required |
| Pass-play participation proxy | Existing scaffold inspection; not actual routes |

It demonstrates exact-ID retrieval, ambiguous-name handling, explicit missing
results, definition comparison, null versus zero, and two aggregation rules.
For example, averaging game-level rates can differ from dividing summed counts:
`(1/2 + 9/30)/2 = 40%`, while `(1+9)/(2+30) = 31.25%`. Both require an explicit
question and rule; the prototype chooses no default.

Every response states `consumer_authorized=false`. Definition lookup never
returns player evidence. Synthetic ratios are separately marked. Unknown and
ambiguous CLI queries return exit code 2, so an automated caller cannot treat
them as a successful exact lookup.

From a checkout containing the pinned baseline:

```bash
python3 docs/audits/metric-definition-study-2026-11-04/study.py list
python3 docs/audits/metric-definition-study-2026-11-04/study.py get 'route %'
python3 docs/audits/metric-definition-study-2026-11-04/study.py get study.route_share.sum_player_routes.v0
python3 docs/audits/metric-definition-study-2026-11-04/study.py demo
python3 docs/audits/metric-definition-study-2026-11-04/study.py audit
python3 -m unittest discover -s docs/audits/metric-definition-study-2026-11-04 -p 'test_*.py' -v
```

Retained outputs: [catalog.json](catalog.json), [examples.json](examples.json),
and [inspection.json](inspection.json). These are study records, not promoted
exports. The census reads pinned git objects rather than mutable working files.

## Ownership and the minimum useful interface

| Responsibility | Proposed owner / boundary |
| --- | --- |
| Field meaning, definition IDs, source mappings, null policy | TIBER-Data, reusing existing contract authority |
| Source eligibility, identity, clocks, artifact/window coverage | TIBER-Data; separate receipts from definition records |
| Role/opportunity or team-environment interpretation | Existing producer models; no metric redefinition |
| Research claims and follow-up questions | TIBER-Research; cite definition and evidence separately |
| Agent transport and user-facing inspection | A later TIBER-Fantasy consumer, using a pinned accepted catalog |
| Acceptance and fantasy decisions | Human operator / manager |

A later first interface could provide `list_definitions`, `get_definition`,
and `compare_definitions`. These are proposed operations, not existing TIBER
MCP tools. General search, paper retrieval, identity resolution, ingestion,
scoring, and a standalone NFL documentation service are outside the first slice.

An eventual definition response should carry family ID, exact definition ID and
version/content digest, authoritative source pin, formula/components, units,
grain, event eligibility, aggregation rule, null policy, caveats, and approval
status. An observation/capability receipt must separately bind the actual player,
source snapshot, identity, season/week or window, clocks, coverage and admission
status. One must never imply the other.

## Decision options

| Option | Benefit | Cost / limitation | Recommendation |
| --- | --- | --- | --- |
| A. Improve the existing documentation/viewer only | Smallest maintenance surface | Agents still need manual source navigation and variant selection | Useful fallback |
| B. Add a small definition inspection layer over existing Data authority | Exact lookup and comparisons; exposes ambiguous meanings and missing support | Requires source bindings, drift checks, review and maintained versioning | Recommended next activation |
| C. Build a separate NFL documentation MCP/catalog service | Broader public provider infrastructure | New corpus, transport, update and rights maintenance; duplicates existing work unless demand is proven | Defer |

No time estimate is presented as measured engineering effort. Option B can be
bounded to the existing registry, code-owned descriptors, and receiving-usage
definitions before any new consumer work is considered.

## Acceptance gates for a later implementation

1. Record a bounded activation and affected producer/consumer owners.
2. Pin each source definition and mapping; distinguish existing, proposed,
   incomplete and deprecated semantics. Preserve legacy null behavior until a
   separately reviewed change resolves it.
3. Generate machine views from authoritative descriptors where possible; prove
   regeneration/drift checks instead of maintaining parallel editable truth.
4. Return a family/ambiguity result for bare names with competing meanings.
   Unknown concepts stay unknown; proxies remain distinct.
5. Keep definition approval and observed coverage separate. Route-based values
   stay unavailable until their actual source, scope and event rules qualify.
6. Test source/definition mismatch, changed denominators, partial populations,
   unit mismatch, null/zero, aggregation choice, unknown IDs, stale pins and
   fixture-to-real promotion attempts. Arithmetic fixtures alone are insufficient.
7. Obtain independent review of the exact implementation candidate. Consider
   transport/integration only after the Data-side boundary is accepted.

## Handoff and validation

- Active task: architecture-pattern/source audit with an offline design
  demonstration, authorized by Joe's request to study the pattern and prepare a
  decision without merging.
- Files touched: this audit directory only. Existing contracts, governance
  versions, data artifacts and runtime code are unchanged.
- Now true: source-pinned study, fresh bounded census, six explicit inspection
  views, synthetic denominator/aggregation examples, and reproducible checks.
- Still missing: operator decision on Option B, canonical definition approval,
  complete source/eligibility mappings, independent review, any real source
  admission, consumer implementation and release qualification.
- Must not assume: this draft is canonical, all TIBER routes are covered, route
  data exists, existing missingness behavior was repaired, or the prototype
  validates a player hypothesis or authorizes a fantasy decision.
- Audit-trigger status: builder contradiction checks completed; independent
  exact-head review pending. No merge or activation is part of this handoff.

See [validation.md](validation.md) for commands, outcomes and limitations.
