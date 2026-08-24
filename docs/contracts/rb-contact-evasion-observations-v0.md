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

Current schema version: `rb_contact_evasion_observations_v0.3.0`. No artifact
exists under any version.

## Semantic authority

**The contract owns what a row means; the payload may only agree.**

Two exact-head reviews established this rule the hard way. The first found five
escapes where a row defined its own metric, sample bar, clock semantics, rights
posture, or grain. The repair moved those five named dimensions into code — and
the second review found the same defect pattern in the adjacent dimensions the
first review had not named: opportunity class, canonical definition text,
transform composition, required caveats, eligible-opportunity identity, numeric
domain, non-rate component shape, ordering across null clocks, retention of
opinion values, acquisition prose, attribution obligations, digest format, and
window/week coherence.

The convergence repair therefore stopped patching named escapes and instead
enumerated every dimension a row could author, then moved each one into either a
code-owned descriptor, a closed vocabulary, or a cross-field rule. That
enumeration is the invariant matrix below, and it — not any fixture list — is
the contract's design.

## Invariant matrix

For every dimension: who owns the fact, and the machine-readable reason code
that fires when a payload disagrees.

### A. Canonical metric identity and definition

| Fact | Owner | Code on disagreement |
|---|---|---|
| metric id universe | `RB_CONTACT_EVASION_METRIC_DICTIONARY` | `UNKNOWN_METRIC_ID` |
| value kind, unit, directionality | descriptor | `METRIC_DESCRIPTOR_CONTRADICTED` |
| canonical inclusion/exclusion rules (verbatim) | descriptor | `CANONICAL_DEFINITION_CONTRADICTED` |
| source-native name / ref / version | source-native, inspectable | drift-checked only: `METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID` |
| required caveat identity | descriptor | `REQUIRED_CAVEAT_MISSING` |

A row restates value kind, unit, directionality, and inclusion rules for
inspectability; none of them is authoritative. Rewriting "10 or more yards" to
"5 or more yards" under `explosive_rushes_10_plus_per_rush_attempt` is a
rejection, not a variant. Source-native wording lives in
`source_native_metric_name` / `definition_ref` / `definition_version`, is
drift-checked within an artifact, and never redefines the canonical metric.

### B. Mechanism and opportunity-class compatibility

| Fact | Owner | Code |
|---|---|---|
| metric → mechanisms (empty = never evidence) | descriptor | `MECHANISM_METRIC_BINDING_VIOLATION` |
| metric → allowed opportunity classes | descriptor | `METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE` |
| class → admissible denominator opportunity types | contract table | `DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH` |
| cross-class `touch` requires combined class + disclosure | contract | `RUSHING_RECEIVING_SILENTLY_COMBINED` |
| denominator type supported by declared source | cross-check | `DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE` |

A 40-yard dash cannot be relabeled a rushing observation; the descriptor pins
`forty_yard_dash_seconds` to `athletic_testing` and the earlier decision to
leave opportunity class out of the descriptor (to keep a fixture at one reason
code) is reversed — fixtures were reshaped to isolate rules; the contract was
not weakened to accommodate them. Metrics bound to **no** mechanism
(`rush_attempts`, `touches`, `longest_rush_yards`, `yards_per_carry`) can never
stand as mechanism evidence: a lone long gain, a timed 40, and yards per carry
never establish contact evasion.

### C. Value kind, unit, directionality, numeric domain

| Fact | Owner | Code |
|---|---|---|
| per-metric numeric domain (`non_negative` / `positive`) | descriptor | `MEASUREMENT_NUMERIC_DOMAIN_VIOLATION` |
| per-metric integrality (discrete event counts) | descriptor | `MEASUREMENT_NUMERIC_DOMAIN_VIOLATION` |
| finiteness of every stored number | contract | `MEASUREMENT_NUMERIC_DOMAIN_VIOLATION` |

Domains apply to the emitted value **and** to numerator and denominator values,
each under its own metric's descriptor. A negative forced-missed-tackle count is
rejected even when the emitted rate is arithmetically consistent with it.

### D. Numerator / denominator / eligible / emitted relationships

| Fact | Owner | Code |
|---|---|---|
| rate requires exact numerator and denominator | contract | `RATE_MISSING_DENOMINATOR` |
| component metric ids equal the descriptor's | descriptor | `RATE_COMPONENT_METRIC_MISMATCH` |
| denominator strictly positive | contract | `RATE_DENOMINATOR_NOT_POSITIVE` |
| eligible_opportunities equals the denominator value | contract (code-owned equality rule) | `ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH` |
| value equals round(numerator/denominator, 3) | contract (`RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS`) | `RATE_VALUE_INCONSISTENT_WITH_COMPONENTS` |
| non-rate metrics carry no rate components | descriptor (null composition) | `RATE_COMPONENTS_ON_NON_RATE_METRIC` |
| observed rate states its eligible opportunities | contract | `ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE` |

The denominator **is** the eligible-opportunity count. Without that equality, a
five-attempt rate could clear a forty-sample gate by declaring an unrelated
eligible count — the exact laundering the second review reproduced.

### E. Transform lineage

| Fact | Owner | Code |
|---|---|---|
| derived evidence requires a transform | contract | `DERIVED_EVIDENCE_REQUIRES_TRANSFORM` |
| a transform requires derived evidence | contract | `TRANSFORM_REQUIRES_DERIVED_EVIDENCE` |
| a derived rate's inputs include its declared components | descriptor | `TRANSFORM_COMPOSITION_INCOMPLETE` |
| no incompatible input pair | symmetric registry | `INCOMPATIBLE_METRIC_TRANSFORM_INPUT` |
| registry symmetry, self-checked at evaluation | contract | `INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC` |

A derived `explosive_rushes_10_plus_per_rush_attempt` whose lineage names only
`receptions` did not derive this metric. Extra inputs are allowed (and screened
for incompatibility); the declared components are mandatory.

### F. Football window and week coherence

All rules under `WINDOW_SCOPE_INCOHERENT`:

- `athletic_testing` is the one admitted non-game event shape: `single_week`,
  `week: null`, `games_included: 0`.
- Game classes: `single_week` requires a named week; `multi_week`,
  `partial_season`, and `full_season` forbid one — a weekly observation is a
  separate row, per the row grain.
- An **observed** game window cannot claim zero games (`single_week` = exactly 1,
  `multi_week` ≥ 2, `partial_season`/`full_season` ≥ 1). A missing-status row may
  carry window context without observed games.

### G. Clock availability and total ordering

| Fact | Owner | Code |
|---|---|---|
| every clock declares a closed origin | row, cross-checked | `RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK` / `CLOCK_AVAILABILITY_CONTRADICTED` |
| total order over the subsequence of non-null clocks | contract | `CLOCK_ORDER_INVALID` |
| `window_start <= window_end` | contract | `CLOCK_ORDER_INVALID` |
| row artifact clock equals envelope `generated_at` | contract | `ARTIFACT_CLOCK_MISMATCH` |

The three source clocks are nullable so an unavailable clock stays honestly
absent. Ordering (`source_observed_at <= source_generated_at <=
source_available_at <= retrieved_at <= artifact_generated_at`) is enforced over
**every consecutive existing pair** of the chain — not adjacent hard-coded
pairs — so a null intermediate clock can never hide a reversal between its
neighbors. Substitution is rejected by declared origin, not timestamp
arithmetic: an equality heuristic was unsound in both directions and is gone.

### H. Acquisition, permissions, retention, attribution, digest

| Fact | Owner | Code |
|---|---|---|
| acquisition is a closed mode (`automated_ingestion` / `manual_citation` / `synthetic_fixture` / `not_acquired`); prose moves to `acquisition_notes` | contract vocabulary | shape |
| `automated_ingestion` requires `automated_access: permitted` | contract | `ACQUISITION_MODE_PERMISSION_INCOMPATIBLE` |
| `synthetic_fixture` acquisition requires fixture provenance; `not_acquired` forbids an observed value | contract | `ACQUISITION_MODE_INCOHERENT` |
| **every stored exact value requires retention permitted** — the action is gated, never the evidence label; `external_opinion` is not exempt | contract | `STORED_EXACT_VALUE_REQUIRES_RETENTION` |
| attribution `required` + stored value requires `attribution_text` | contract | `ATTRIBUTION_METADATA_MISSING` |
| promotable requires retention, redistribution, automation all permitted and attribution settled | contract | `SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE` |
| restricted access cannot be promotable or back a non-opinion observed value | contract | `RESTRICTED_SOURCE_ACCESS_OVERCLAIMED` |
| editorial material must be labeled opinion | contract | `EXTERNAL_OPINION_LABELED_AS_OBSERVATION` |
| snapshot requires a digest; a digest is forbidden where retention is prohibited | contract | `SNAPSHOT_WITHOUT_CONTENT_DIGEST` / `CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION` |
| digest closed to `sha256` + 64 lowercase hex | contract | `CONTENT_DIGEST_MALFORMED` |
| supersession never self-references | contract | `SUPERSESSION_SELF_REFERENCE` |

Rights follow the action being taken. Storing an exact figure is retention of
source material whether the row calls itself `direct` or `external_opinion`; a
published claim whose exact value is stored is still stored. Automation
permission binds to the closed acquisition mode, not to what the value is. The
acquisition-provenance rule is deliberately one-directional: synthetically
produced material can only be fixture provenance, but a fixture row may honestly
*model* any acquisition mode (a synthetic row simulating a gated source declares
`not_acquired`).

`unknown` dispositions fail closed everywhere. They are never read as
permission.

### I. Artifact identity, grain, and position

| Fact | Owner | Code |
|---|---|---|
| `observation_id` unique per artifact | contract | `DUPLICATE_OBSERVATION_ID` |
| canonical grain unique (player × window × opportunity class × metric definition × snapshot × denominator) | contract, key exported as `rbContactEvasionGrainKey` | `DUPLICATE_OBSERVATION_GRAIN` |
| fixture provenance never in candidate/promoted | contract | `FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION` |
| minimum-sample rule code-owned; fixture-only authority; observed rates fail closed outside `fixture_only` | contract | `MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED` / `MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION` / `MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED` |
| **promoted position fails closed entirely** | contract | `PROMOTED_POSITION_REQUIRES_PROMOTION_GATE` |
| canonical identity requires `gsis_id` | contract | `CANONICAL_IDENTITY_UNRESOLVED` |
| missing carries no value + explicit reason; observed carries a value | contract | `MISSING_COMPONENT_CARRIES_VALUE` / `MISSINGNESS_REASON_ABSENT` / `OBSERVED_COMPONENT_MISSING_VALUE` |
| cohort scope matches the observation; window-completeness comparison disclosed | contract | `COHORT_SCOPE_MISMATCH` / `WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED` |

The promoted fail-closed rule is new in the convergence round: #224 binds
promotion to a manifest/digest/review gate that Slice A does not implement, so
nothing can sit at `promoted` position under this contract version — not even a
count. This extends the dispatch's fail-closed instruction for rates to the
position that has no legitimate occupant at all.

## Files

| File | Role |
|---|---|
| `src/contracts/v1/rbContactEvasionObservationsV0.ts` | Contract: closed vocabularies, code-owned metric dictionary and minimum-sample rule, cross-field validation |
| `schemas/rb_contact_evasion_observations_v0.schema.json` | Shape gate (closed vocabularies, clock origins, unknown-field rejection) |
| `test/fixtures/rb_contact_evasion/positive/**` | P1–P8 |
| `test/fixtures/rb_contact_evasion/negative/**` | N1–N42 |
| `test/rbContactEvasionObservationsV0.contract.test.ts` | Contract behavior at the public barrel, exact-attack regression locks, cross-product suites |
| `tests/test_rb_contact_evasion_observations_v0.py` | Schema-boundary behavior and corpus/doc drift guards |

### Two enforcement layers, and where each stops

The JSON schema is a **shape** gate: closed vocabularies (mechanisms, evidence
classes, access classes, acquisition modes, caveat ids, clock origins,
dispositions), all seven clocks with declared origins, and unknown-field
rejection at every level. Every cross-field rule in the invariant matrix lives
in the TypeScript contract layer. Every negative fixture is deliberately
**shape-valid**, so its rejection is attributable to the named contract rule
rather than to a parse failure.

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
observations, and receiving observations never share a row, and the grain is
enforced at artifact level, not merely described.

## Identity

Canonical identity requires a `gsis_id` matching `^00-\d{7}$` **and**
`identity_resolution: "canonical_gsis_id"`. Name, team, position, and provider
player id are display or lineage context and never authorize identity.
`gsis_id` is nullable in the shape only so an unresolved row can be *expressed*
and then rejected, never silently accepted. The Bucky golden trace uses governed
canonical identity `00-0039361`.

## Mechanisms

The mechanism universe is closed to exactly:

```text
speed
agility_change_of_direction
contact_avoidance
contact_survival
explosiveness
```

`elusiveness` is not a member — it is the umbrella term these decompose.
Evidence for one mechanism never satisfies another, enforced by the dictionary's
metric → mechanism binding.

## Sample sufficiency

The governing minimum is **code-owned**. A row carries
`metric.minimum_sample_rule_id` naming the rule that binds it and can state no
threshold anywhere. `RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE` holds the
thresholds, keyed by window completeness (`single_week` 10, `multi_week` 20,
`partial_season` 30, `full_season` 40).

**These thresholds are fixture-only pinned placeholders, not empirical football
thresholds.** #234 has authorized no empirical N and this slice does not invent
one. The rule's `authority` is `fixture_only_placeholder`, and the contract
fails closed accordingly: an observed rate outside `fixture_only` position is
rejected outright until Slice B binds an admitted rule.

## Missingness

A missing component carries an explicit `missingness_reason` and no value of any
kind. There is no neutral default, no zero fill, and no substitution from
another mechanism. A below-minimum sample must be emitted as missing with
`below_minimum_sample`, never as a value.

## Fixture corpus

All fixture values are **synthetic**. No fixture contains acquired provider
data. Every observation declares this via the required `synthetic_fixture_value`
caveat on fixture-provenance rows, `example_*` source owners, and synthetic
snapshot ids. Fixtures other than the Bucky trace use the reserved synthetic
canonical identity `00-0000001`, which corresponds to no real player.

Bucky Irving (`00-0039361`) appears **only** in P7, as the governed golden-trace
identity and contract example authorized by #234. P7's values are synthetic and
are **not** evidence about Bucky Irving or any real player.

### Positive fixtures

#### Mandated corpus P1–P7 (TIBER-Data #234)

| # | File | What it establishes |
|---|---|---|
| P1 | `p1_complete_derived_explosiveness_rate.json` | A complete derived explosiveness rate: exact components, declared transform consuming them, cohort scope matching the window |
| P2 | `p2_raw_count_without_denominator.json` | A raw count is legitimate with no denominator, and is not a rate |
| P3 | `p3_historical_testing_classified.json` | A 40-yard dash under `speed` + `athletic_testing` with the mandatory `historical_testing_not_current_form` caveat |
| P4 | `p4_rights_blocked_missing_component.json` | A gated source yields a missing component with `rights_blocked`, `not_acquired`, and no value |
| P5 | `p5_declared_snapshot_supersession.json` | Snapshot provenance with a well-formed sha256 digest and an explicitly declared superseding snapshot |
| P6 | `p6_weekly_and_season_windows_coexist.json` | A weekly (week 12) and a full-season window coexist as separate rows and separate grains under one unchanged definition |
| P7 | `p7_bucky_receipt_remains_partial.json` | The Bucky receipt: three mechanisms observed, `speed` and `agility_change_of_direction` honestly missing, no composite emitted |

#### Supplementary positive

| # | File | What it establishes |
|---|---|---|
| P8 | `p8_absent_source_clock_stays_null.json` | A source supplying no observation or generation clock leaves both `null` with declared origins, instead of backfilling |

### Negative fixtures

Each is shape-valid and rejected by exactly one reason code.

#### Mandated corpus N1–N15 (TIBER-Data #234)

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

N3 was reshaped in the convergence round: it now declares the combined class
without its component disclosure — the literal silent combination — because the
dictionary pins `forced_missed_tackles_per_touch` to the combined class, and
weakening that pin to keep the old fixture single-coded would have been
backwards. The old attack (a touch denominator under a `rushing` row) is still
rejected, now for two reasons at once.

#### Supplementary corpus N16–N28 (second review round)

| # | File | Reason code |
|---|---|---|
| N16 | `n16_promotable_without_permissions.json` | `SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE` |
| N17 | `n17_direct_observation_without_retention.json` | `STORED_EXACT_VALUE_REQUIRES_RETENTION` |
| N18 | `n18_snapshot_without_content_digest.json` | `SNAPSHOT_WITHOUT_CONTENT_DIGEST` |
| N19 | `n19_duplicate_observation_id.json` | `DUPLICATE_OBSERVATION_ID` |
| N20 | `n20_duplicate_observation_grain.json` | `DUPLICATE_OBSERVATION_GRAIN` |
| N21 | `n21_rate_value_inconsistent_with_components.json` | `RATE_VALUE_INCONSISTENT_WITH_COMPONENTS` |
| N22 | `n22_rate_component_metric_mismatch.json` | `RATE_COMPONENT_METRIC_MISMATCH` |
| N23 | `n23_rate_denominator_not_positive.json` | `RATE_DENOMINATOR_NOT_POSITIVE` |
| N24 | `n24_metric_descriptor_contradicted.json` | `METRIC_DESCRIPTOR_CONTRADICTED` |
| N25 | `n25_eligible_opportunities_absent.json` | `ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE` |
| N26 | `n26_clock_availability_contradicted.json` | `CLOCK_AVAILABILITY_CONTRADICTED` |
| N27 | `n27_minimum_sample_rule_not_code_owned.json` | `MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED` |
| N28 | `n28_minimum_sample_rule_not_admitted_for_position.json` | `MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION` |

N17 was reshaped: retention now gates every stored exact value (the action), so
the fixture prohibits retention rather than automation, and the old
evidence-class code is retired.

#### Convergence corpus N29–N42 (third review round)

One fixture per escape family from the second exact-head review.

| # | File | Reason code |
|---|---|---|
| N29 | `n29_metric_opportunity_class_incompatible.json` | `METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE` |
| N30 | `n30_canonical_definition_contradicted.json` | `CANONICAL_DEFINITION_CONTRADICTED` |
| N31 | `n31_transform_composition_incomplete.json` | `TRANSFORM_COMPOSITION_INCOMPLETE` |
| N32 | `n32_required_caveat_missing.json` | `REQUIRED_CAVEAT_MISSING` |
| N33 | `n33_eligible_opportunities_denominator_mismatch.json` | `ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH` |
| N34 | `n34_measurement_numeric_domain_violation.json` | `MEASUREMENT_NUMERIC_DOMAIN_VIOLATION` |
| N35 | `n35_rate_components_on_non_rate_metric.json` | `RATE_COMPONENTS_ON_NON_RATE_METRIC` |
| N36 | `n36_clock_order_invalid_across_null.json` | `CLOCK_ORDER_INVALID` |
| N37 | `n37_acquisition_mode_permission_incompatible.json` | `ACQUISITION_MODE_PERMISSION_INCOMPATIBLE` |
| N38 | `n38_attribution_metadata_missing.json` | `ATTRIBUTION_METADATA_MISSING` |
| N39 | `n39_content_digest_malformed.json` | `CONTENT_DIGEST_MALFORMED` |
| N40 | `n40_window_scope_incoherent.json` | `WINDOW_SCOPE_INCOHERENT` |
| N41 | `n41_transform_requires_derived_evidence.json` | `TRANSFORM_REQUIRES_DERIVED_EVIDENCE` |
| N42 | `n42_acquisition_mode_incoherent.json` | `ACQUISITION_MODE_INCOHERENT` |

N12 carries three rows in one fixture — a 40-yard dash offered as contact
avoidance, a long gain offered as explosiveness, and yards per carry offered as
contact survival — because #234 names all three as the same failure and one rule
rejects them. Exactly two fixtures declare `artifact_position: "candidate"` (N15
and N28); none sits at promoted position, which fails closed outright.

Beyond the fixture corpus, the focused test suite runs **cross-product
adversarial sweeps** at the public evaluator boundary: every dictionary metric ×
every opportunity class; every value kind × component presence; denominator ×
eligible-opportunity equality; negative, zero, fractional, and non-finite values
per metric domain; all eight nullable source-clock patterns with a reversal at
every consecutive existing pair; every evidence class × acquisition mode ×
retention × automation disposition; every artifact position × provenance mode;
and every window completeness × week presence × class. Each invalid combination
must fail semantically — never merely by parsing.

## Reason codes

Rejection is machine-readable. `evaluateRbContactEvasionObservationsV0` returns
`{ valid, shape_valid, violations, reason_codes }`; `shape_valid` distinguishes
"rejected by a contract rule" from "did not parse".
`validateRbContactEvasionObservationsV0` throws `RbContactEvasionContractError`
carrying the same codes.

Codes beyond the fixture corpus: `SCHEMA_SHAPE_INVALID`, `UNKNOWN_FIELD_PRESENT`,
`UNKNOWN_METRIC_ID`, `DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH`,
`MISSINGNESS_REASON_ABSENT`, `OBSERVED_COMPONENT_MISSING_VALUE`,
`CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION`, `ARTIFACT_CLOCK_MISMATCH`,
`INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC`, `DERIVED_EVIDENCE_REQUIRES_TRANSFORM`,
`SUPERSESSION_SELF_REFERENCE`, `PROMOTED_POSITION_REQUIRES_PROMOTION_GATE`.

## Repository-convention adjustments

- **Field naming** is `snake_case`, matching #234's field names and the newest
  committed schemas. Older `src/contracts/v1/` contracts use `camelCase`; the
  divergence is intentional.
- **Envelope fields** follow the `bounded_2026_population_census_v0` pattern,
  with `artifact_position` carrying the governance fact this contract enforces.
- **No Python validator script.** That validator is Slice B;
  `tests/test_rb_contact_evasion_observations_v0.py` exercises the committed
  JSON schema directly and asserts explicitly where the shape gate stops.

## Residual risks: what this contract cannot prove

- **Producer-declared source facts.** `access_class`, `material_kind`,
  `supported_opportunity_types`, `promotable`, `permissions`, `acquisition_method`,
  `attribution_text`, `content_digest`, and `rights_review_ref` are declared by
  whoever writes the row. The contract proves internal consistency and fails
  closed on incompatible combinations; it cannot prove a declaration matches
  reality. Pinning declarations to an admitted source registry is Slice B.
- **A declared clock origin can still be a lie.** A producer who copies the
  retrieval clock into a source clock and declares it `source_supplied` is
  undetectable here. Declared origin defeats arithmetic laundering, not
  dishonesty.
- **A content digest is required and format-checked, not verified.** Nothing
  recomputes it against payload bytes — there is no payload in this slice.
- **Attribution presence is not attribution correctness.** The contract proves
  `attribution_text` exists when the obligation is declared; it cannot judge the
  text.
- **Canonical inclusion rules are exact strings.** Semantically equivalent
  rewordings are rejected. That is deliberate — prose equivalence judgments do
  not belong in a fail-closed gate — but it means admitting new wording is a
  contract change.
- **Dropping `cohort_scope` to `null` skips the cohort rules.** A weaker claim,
  not a laundered stronger one, and the sample bar applies regardless.
- **The pinned minimum-sample thresholds are placeholders, not football.** No
  observed rate may sit outside `fixture_only` under them.

## What must not be assumed

- That any source is admitted for this lane. None is.
- That a fixture value says anything about a real player. None does.
- That the contract layer's guarantees hold from the JSON schema alone. It is a
  shape gate; the invariant matrix is the TypeScript layer.
- That anything may sit at `promoted` position under this contract version. It
  fails closed.
- That this contract authorizes normalization, percentiles, thresholds, scores,
  cohort ranking, or any Data/FORGE ownership decision. It does not.

## Related work

- TIBER-Data #234 — this lane's intake and design authority
- TIBER-Data #212 — parent player-attribute evidence design
- TIBER-Data #224 — promoted-artifact integrity (binds any future builder, and
  the reason promoted position fails closed here)
- TIBER-Ops #15 — Data/FORGE derivation boundary, unresolved
- TIBER-Ops #57 W4 — deterministic claim-assessment spine (downstream, not here)
- TIBER-Rookies #245 — the unsupported-Bucky-comparison failure mode this lane exists to prevent
