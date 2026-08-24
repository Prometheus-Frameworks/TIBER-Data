# RB Contact-Evasion Observations v0 Contract

## Status and scope

`rb_contact_evasion_observations_v0` is a **contract, schema, documentation, and
fixture corpus only** (TIBER-Data #234, Slice A).

It ships **no** builder, no ingestion route, no candidate artifact, no promotion
script, and no promoted artifact. No external source was accessed, downloaded,
probed, scraped, or classified to produce it. Nothing under `exports/candidates/**`
or `exports/promoted/**` was written or read.

No admitted source exists for this lane yet. Under the repo's core rule — *if
source truth is missing, reduce scope* — the honest state of this lane is: the
contract can express the evidence, and there is currently nothing admitted to put
in it.

Issue #234's original no-implementation boundary is superseded **only** for this
Slice A scope. The Python artifact validator and manifest gate (Slice B), the
Bucky assembler (Slice C), cohort normalization, percentiles, thresholds, scores,
and the Data/FORGE ownership decision are all out of scope and unimplemented.

## Purpose

"Bucky Irving was elite and elusive as a rookie" is a human sentence, not a
measurement. This contract is the first step in turning such a sentence into
inspectable evidence questions:

```text
human concept -> distinct football mechanisms -> eligible governed observables
-> explicit denominators and cohorts -> deterministic receipts -> claim-ready evidence
```

The purpose is **not** to produce an elusiveness number. There is deliberately no
score, composite, neutral default, grade, ranking, percentile, tier, rating,
fantasy field, or "elite" judgment anywhere in this contract or schema, and none
may be added. A test enforces that absence over the schema's property names and
over every emittable vocabulary.

## Files

| File | Role |
|---|---|
| `src/contracts/v1/rbContactEvasionObservationsV0.ts` | Contract, closed vocabularies, registries, and the cross-field validation layer |
| `schemas/rb_contact_evasion_observations_v0.schema.json` | Shape gate (closed vocabularies, required clocks, unknown-field rejection) |
| `test/fixtures/rb_contact_evasion/positive/**` | P1–P7 |
| `test/fixtures/rb_contact_evasion/negative/**` | N1–N15 |
| `test/rbContactEvasionObservationsV0.contract.test.ts` | Contract behavior at the public barrel |
| `tests/test_rb_contact_evasion_observations_v0.py` | Schema-boundary behavior and corpus/doc drift guards |

### Two enforcement layers, and where each stops

The JSON schema is a **shape** gate. It closes the vocabularies, requires all
seven clocks individually, and rejects unknown fields at every level — but it
cannot express cross-field rules.

The cross-field rules live in the TypeScript contract layer and are the reason
N1–N15 are rejected. Every negative fixture is deliberately **shape-valid**, so
its rejection is attributable to the named contract rule rather than to a parse
failure. `tests/test_rb_contact_evasion_observations_v0.py` asserts that split
explicitly rather than implying the schema catches more than it does.

## Row grain

One row is:

```text
one canonical player
x one exact football window
x one metric definition
x one source snapshot
x one denominator definition
```

Season aggregates, partial-season windows, weekly observations, rushing
observations, and receiving observations never share a row.

## Concept decomposition: five separate mechanisms

The mechanism universe is closed to exactly:

```text
speed
agility_change_of_direction
contact_avoidance
contact_survival
explosiveness
```

`elusiveness` is not a member — it is the umbrella term these decompose. A player
may be strong in one mechanism and unsupported in another. **Evidence for one
mechanism never satisfies another**, and that is enforced structurally, not by
convention: `RB_CONTACT_EVASION_METRIC_REGISTRY` binds each metric identity to
the mechanisms it may ever evidence.

Metrics bound to **no** mechanism are components, denominators, or known-inadmissible
summaries — `rush_attempts`, `touches`, `longest_rush_yards`, `yards_per_carry`.
A lone long gain, a 40-yard dash, and yards per carry can never stand as
contact-evasion evidence. A metric id absent from the registry fails closed
(`UNKNOWN_METRIC_ID`): admitting a metric is a contract change, not a data decision.

## Identity

Canonical identity requires a `gsis_id` matching `^00-\d{7}$` **and**
`identity_resolution: "canonical_gsis_id"`. Name, team, position, and provider
player id are display or lineage context and never authorize identity;
`display_name_non_authoritative` is named to say so. `gsis_id` is nullable in the
shape only so an unresolved row can be *expressed* and then rejected
(`CANONICAL_IDENTITY_UNRESOLVED`), never silently accepted.

The Bucky golden trace uses governed canonical identity `00-0039361`.

## Metric, numerator, denominator

A `value_kind: "rate"` observation with a value requires exact numerator **and**
denominator metric ids and values. A percentage without an exact denominator is
not interchangeable with another source's similarly named rate.

Opportunity classes and their admissible denominator opportunity types:

| `opportunity_class` | admissible `opportunity_type` |
|---|---|
| `rushing` | `rush_attempt`, `contact_event` |
| `receiving` | `reception`, `target`, `contact_event` |
| `combined_rushing_receiving` | `touch` |
| `athletic_testing` | `testing_trial` |

`touch` spans rushing and receiving. It is admissible **only** under the
explicitly declared combined class **and** with a `combined_component_disclosure`
naming both component metrics. A touch denominator on a row declared `rushing` is
a silent combination and is rejected. This is why `forced_missed_tackles_per_rush_attempt`
and `forced_missed_tackles_per_touch` remain distinct metric identities, and why
they are declared mutually incompatible as transform inputs.

The declared source must actually support the denominator: an opportunity type
absent from `source.supported_opportunity_types` is rejected
(`DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE`).

## Clocks

All seven clocks are separately required and separately meaningful:

```text
window_start          window_end
source_observed_at    source_generated_at    source_available_at
retrieved_at          artifact_generated_at
```

`retrieved_at` may not coincide with `window_end`, `source_generated_at`, or
`source_observed_at`. Clocks are compared as **instants**, not strings, so a
re-formatted offset is not an escape hatch. Ordering is enforced
(`window_start <= window_end`; `source_observed_at <= source_generated_at <=
source_available_at <= retrieved_at <= artifact_generated_at`), and each row's
`artifact_generated_at` must equal the envelope `generated_at`.

## Evidence class and source access

Evidence class is closed to `direct | normalized | derived | external_opinion`.
Source-access classification is closed to:

```text
open_and_ingestible
public_but_terms_constrained
licensed_or_gated
reference_only
unavailable
unknown
```

`licensed_or_gated`, `reference_only`, `unavailable`, and `unknown` are
**restricted**: they can never be marked `promotable`, and they can never back an
*observed* value that is anything other than a cited `external_opinion`. A
restricted source therefore yields either no value (`status: "missing"`) or a
cited opinion — never a direct observation. That carve-out is what P4 exercises:
a rights-blocked component stays missing.

`source.material_kind` records what the material actually is
(`measured_observation | derived_publication | editorial_opinion`). Editorial
opinion must carry `evidence_class: "external_opinion"`; labeling it an
observation is rejected.

Provenance is explicit per row: `live | snapshot | fixture`. A `fixture`-provenance
row may never appear in an artifact at `candidate` or `promoted` position —
fixture data does not become governed truth by location.

## Missingness

A missing component carries an explicit `missingness_reason` and **no value of any
kind** — `value`, `numerator`, and `denominator` must all be null. There is no
neutral default, no zero fill, and no substitution from another mechanism. A rate
whose eligible opportunities fall below the metric minimum must be emitted as
missing with `below_minimum_sample`, never as a value.

## Definition drift

Within one artifact, a `metric_id` must carry one unchanged definition — the same
`source_native_metric_name`, `definition_ref`, and `definition_version`. A changed
definition requires a new metric identity. `minimum_eligible_opportunities` is
deliberately **not** part of the drift tuple, because a window-appropriate sample
threshold legitimately differs between a weekly and a season row (P6 exercises
both windows under one definition).

## Cohort scope

`cohort_scope` records cohort **membership inputs only** — position, season,
season type, window completeness, and minimum eligible opportunities. It carries
no percentile, rank, threshold, score, or grade, and none may be added: that
boundary is TIBER-Ops #15 and remains unresolved. Cohort position, season, and
season type must match the observation's own scope.

Comparing a partial window against a full-window cohort requires a non-empty
`window_completeness_disclosure`. **Residual risk:** that disclosure is a declared
string. The contract can prove a disclosure is present and that the mismatch is
not silent; it cannot judge whether the prose is adequate. A reviewer or a later
slice must.

## Reason codes

Rejection is machine-readable. `evaluateRbContactEvasionObservationsV0` returns
`{ valid, shape_valid, violations, reason_codes }`; `shape_valid` lets a caller
always distinguish "rejected by a contract rule" from "did not parse".
`validateRbContactEvasionObservationsV0` throws `RbContactEvasionContractError`
carrying the same codes.

Codes beyond the fixture corpus: `SCHEMA_SHAPE_INVALID`, `UNKNOWN_FIELD_PRESENT`,
`DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH`, `CLOCK_ORDER_INVALID`,
`ARTIFACT_CLOCK_MISMATCH`, `UNKNOWN_METRIC_ID`,
`INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC`, `DERIVED_EVIDENCE_REQUIRES_TRANSFORM`,
`SUPERSESSION_SELF_REFERENCE`.

## Fixture corpus

All fixture values are **synthetic**. No fixture contains acquired provider data.
Every observation declares this in its `warnings`, every source `owner` is an
`example_*` placeholder, and every `snapshot_id` is marked synthetic. Fixtures
other than the Bucky trace use the reserved synthetic canonical identity
`00-0000001`, which corresponds to no real player.

Bucky Irving (`00-0039361`) appears **only** in P7, as the governed golden-trace
identity and contract example already authorized by #234. P7's values are
synthetic and are **not** evidence about Bucky Irving or any real player.

### Positive fixtures P1–P7

| # | File | What it establishes |
|---|---|---|
| P1 | `p1_complete_derived_explosiveness_rate.json` | A complete derived explosiveness rate: exact numerator/denominator, declared transform, cohort scope matching the observation window |
| P2 | `p2_raw_count_without_denominator.json` | A raw count is legitimate with no denominator, and is not a rate |
| P3 | `p3_historical_testing_classified.json` | A 40-yard dash correctly classified under `speed` and `athletic_testing`, warning that historical testing is a different evidence class from live movement |
| P4 | `p4_rights_blocked_missing_component.json` | A gated source yields a missing component with `rights_blocked`, `promotable: false`, and no value |
| P5 | `p5_declared_snapshot_supersession.json` | Snapshot provenance with an explicitly declared superseding snapshot |
| P6 | `p6_weekly_and_season_windows_coexist.json` | A weekly and a full-season window coexist as separate rows under one unchanged metric definition |
| P7 | `p7_bucky_receipt_remains_partial.json` | The Bucky receipt: three mechanisms observed, `speed` and `agility_change_of_direction` honestly missing, and no composite emitted. The receipt may legitimately stay partial |

### Negative fixtures N1–N15

Each is shape-valid and rejected by exactly one reason code.

| # | File | Reason code |
|---|---|---|
| N1 | `n01_rate_missing_denominator.json` | `RATE_MISSING_DENOMINATOR` |
| N2 | `n02_denominator_unsupported_by_source.json` | `DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE` |
| N3 | `n03_rushing_receiving_silently_combined.json` | `RUSHING_RECEIVING_SILENTLY_COMBINED` |
| N4 | `n04_metric_definition_drift.json` | `METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID` |
| N5 | `n05_reference_only_source_overclaimed.json` | `RESTRICTED_SOURCE_ACCESS_OVERCLAIMED` |
| N6 | `n06_external_opinion_labeled_observation.json` | `EXTERNAL_OPINION_LABELED_AS_OBSERVATION` |
| N7 | `n07_partial_full_window_comparison_undisclosed.json` | `WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED` |
| N8 | `n08_below_minimum_sample_rate_emitted.json` | `MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED` |
| N9 | `n09_cohort_scope_mismatch.json` | `COHORT_SCOPE_MISMATCH` |
| N10 | `n10_retrieval_clock_substituted.json` | `RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK` |
| N11 | `n11_canonical_identity_unresolved.json` | `CANONICAL_IDENTITY_UNRESOLVED` |
| N12 | `n12_mechanism_metric_binding_violation.json` | `MECHANISM_METRIC_BINDING_VIOLATION` |
| N13 | `n13_default_value_for_missing_component.json` | `MISSING_COMPONENT_CARRIES_VALUE` |
| N14 | `n14_incompatible_transform_inputs.json` | `INCOMPATIBLE_METRIC_TRANSFORM_INPUT` |
| N15 | `n15_fixture_provenance_in_candidate_position.json` | `FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION` |

N12 carries three rows in one fixture — a 40-yard dash offered as contact
avoidance, a long gain offered as explosiveness, and yards per carry offered as
contact survival — because #234 names all three as the same failure and they are
rejected by the same rule.

N15 is the one fixture that declares `artifact_position: "candidate"`, precisely
so the rule that keeps fixture provenance out of candidate position has something
to reject.

## Repository-convention adjustments

- **Field naming.** Rows and envelope use `snake_case`, matching the field names
  #234 specifies (`gsis_id`, `mechanism_id`, `window_start`, `retrieved_at`) and
  the newest committed schemas (`bounded_2026_population_census_v0`,
  `player_season_coverage_v0_promoted`). Older contracts in `src/contracts/v1/`
  use `camelCase`; this contract does not, and the divergence is intentional.
- **Envelope fields** follow the `bounded_2026_population_census_v0` pattern
  (`artifact_id`, `schema_version`, `generated_at`), with `artifact_position`
  replacing that artifact's `status` because position is the governance fact this
  contract needs to enforce.
- **No Python validator script.** Existing Python schema tests load a validator
  from `scripts/`. That validator is Slice B and is not authorized, so
  `tests/test_rb_contact_evasion_observations_v0.py` exercises the committed JSON
  schema directly.

## Residual risks: what this contract cannot prove

These are limits of a contract-only slice, recorded rather than papered over.

- **Producer-declared source facts.** `source.access_class`, `material_kind`,
  `supported_opportunity_types`, `promotable`, and `rights_review_ref` are
  declared by whoever writes the row. The contract proves they are internally
  consistent — a gated source cannot also be promotable, an editorial source
  cannot also be a direct observation, a denominator cannot exceed what the
  source declares it supports. It cannot prove a declaration matches reality.
  Pinning declarations to an admitted source registry is Slice B work.
- **A row with no cohort sets its own minimum-sample bar.** When
  `cohort_scope` is present the stricter of the metric and cohort minimums
  governs, so self-lowering buys nothing. With no cohort stated, the row's own
  `minimum_eligible_opportunities` is the only bar. A row can also drop
  `cohort_scope` to `null` and skip the cohort rules entirely — that makes a
  weaker claim rather than laundering a stronger one, but it is a real gap in
  coverage, not an enforced guarantee.
- **Disclosure presence is not disclosure adequacy.** The contract proves a
  window-completeness disclosure exists and that a mismatch is not silent. It
  cannot judge whether the prose is honest or sufficient.
- **`promotable: true` is a claim, never an authorization.** No promotion path
  exists in this slice; the field only records a producer's assertion that
  separate promotion review could consider the source.
- **`summarize…MechanismCoverage` reports presence, not quality.** `observed`
  means an observation row exists with observed status. It is not a judgment
  that the evidence is good, sufficient, or comparable to anything.

## What must not be assumed

- That any source is admitted for this lane. None is.
- That a fixture value says anything about a real player. None does.
- That a present disclosure string is an adequate disclosure. The contract proves
  presence, not adequacy.
- That the contract layer's guarantees hold from the JSON schema alone. It is a
  shape gate; the cross-field rules are the TypeScript layer.
- That this contract authorizes normalization, percentiles, thresholds, scores,
  cohort ranking, or any Data/FORGE ownership decision. It does not.

## Related work

- TIBER-Data #234 — this lane's intake and design authority
- TIBER-Data #212 — parent player-attribute evidence design
- TIBER-Data #224 — promoted-artifact integrity (binds any future builder)
- TIBER-Ops #15 — Data/FORGE derivation boundary, unresolved
- TIBER-Ops #57 W4 — deterministic claim-assessment spine (downstream, not here)
- TIBER-Rookies #245 — the unsupported-Bucky-comparison failure mode this lane exists to prevent
