import { z } from 'zod';

/**
 * `rb_contact_evasion_observations_v0` — source-observation contract for the RB
 * contact-evasion mechanism lane (TIBER-Data #234, Slice A).
 *
 * This module is a **contract and validation surface only**. It does not build,
 * ingest, promote, normalize, rank, or score anything.
 *
 * Design rule, after the first exact-head review: **semantic authority lives in
 * this file, not in the payload.** A row does not get to define what its metric
 * means, what its minimum-sample bar is, or which clock a timestamp came from.
 * The contract owns those facts in code-owned descriptors and rules; the payload
 * may only *agree* with them, and disagreement is a rejection with a stable
 * machine-readable reason code.
 *
 * Deliberate absences (see `docs/contracts/rb-contact-evasion-observations-v0.md`):
 * there is no score, composite, grade, ranking, percentile, tier, rating,
 * neutral default, or "elite" judgment anywhere in this contract. A mechanism
 * with no admitted evidence stays missing; it is never filled from another.
 */

const isoDatetimeSchema = z.string().datetime({ offset: true });
const nonEmptyStringSchema = z.string().min(1);

/** Canonical GSIS identity form. Names/teams/positions never authorize identity. */
export const RB_CONTACT_EVASION_GSIS_ID_PATTERN = /^00-\d{7}$/;

// ---------------------------------------------------------------------------
// Closed vocabularies
// ---------------------------------------------------------------------------

/**
 * The mechanism universe is closed. "Elusiveness" is not a member: it is a human
 * umbrella term that decomposes into these five separately-observed mechanisms.
 */
export const rbContactEvasionMechanismIdSchema = z.enum([
  'speed',
  'agility_change_of_direction',
  'contact_avoidance',
  'contact_survival',
  'explosiveness',
]);

export const rbContactEvasionEvidenceClassSchema = z.enum([
  'direct',
  'normalized',
  'derived',
  'external_opinion',
]);

export const rbContactEvasionSourceAccessClassSchema = z.enum([
  'open_and_ingestible',
  'public_but_terms_constrained',
  'licensed_or_gated',
  'reference_only',
  'unavailable',
  'unknown',
]);

/** Access classes that cannot back a promotable, directly-ingested observation. */
export const RB_CONTACT_EVASION_RESTRICTED_ACCESS_CLASSES: ReadonlySet<
  RbContactEvasionSourceAccessClass
> = new Set(['licensed_or_gated', 'reference_only', 'unavailable', 'unknown']);

export const rbContactEvasionProvenanceModeSchema = z.enum(['live', 'snapshot', 'fixture']);

/** Where an artifact carrying these rows is allowed to sit. */
export const rbContactEvasionArtifactPositionSchema = z.enum([
  'fixture_only',
  'candidate',
  'promoted',
]);

/** What the source material actually is, independent of how it is labeled. */
export const rbContactEvasionSourceMaterialKindSchema = z.enum([
  'measured_observation',
  'derived_publication',
  'editorial_opinion',
]);

/**
 * Rights dispositions, recorded separately because #234 requires attribution,
 * retention, redistribution/display, and automation to be stated independently.
 * `unknown` is a real answer and fails closed — it is never read as permission.
 */
export const rbContactEvasionPermissionDispositionSchema = z.enum([
  'permitted',
  'prohibited',
  'unknown',
]);

export const rbContactEvasionAttributionDispositionSchema = z.enum([
  'required',
  'not_required',
  'unknown',
]);

export const rbContactEvasionOpportunityClassSchema = z.enum([
  'rushing',
  'receiving',
  'combined_rushing_receiving',
  'athletic_testing',
]);

export const rbContactEvasionOpportunityTypeSchema = z.enum([
  'rush_attempt',
  'reception',
  'target',
  'touch',
  'contact_event',
  'testing_trial',
]);

/**
 * Opportunity types admissible for each opportunity class. `touch` spans the
 * rushing and receiving classes and is therefore admissible only under the
 * explicitly-declared and disclosed combined class.
 */
export const RB_CONTACT_EVASION_CLASS_OPPORTUNITY_TYPES: Readonly<
  Record<RbContactEvasionOpportunityClass, readonly RbContactEvasionOpportunityType[]>
> = {
  rushing: ['rush_attempt', 'contact_event'],
  receiving: ['reception', 'target', 'contact_event'],
  combined_rushing_receiving: ['touch'],
  athletic_testing: ['testing_trial'],
};

/** Opportunity types that mix rushing and receiving opportunity in one denominator. */
export const RB_CONTACT_EVASION_CROSS_CLASS_OPPORTUNITY_TYPES: ReadonlySet<
  RbContactEvasionOpportunityType
> = new Set(['touch']);

export const rbContactEvasionSeasonTypeSchema = z.enum(['PRE', 'REG', 'POST']);

export const rbContactEvasionWindowCompletenessSchema = z.enum([
  'single_week',
  'multi_week',
  'partial_season',
  'full_season',
]);

export const rbContactEvasionValueKindSchema = z.enum([
  'rate',
  'count',
  'duration_seconds',
  'speed_mph',
]);

export const rbContactEvasionDirectionalitySchema = z.enum([
  'higher_is_more_of_mechanism',
  'lower_is_more_of_mechanism',
]);

export const rbContactEvasionMeasurementStatusSchema = z.enum(['observed', 'missing']);

export const rbContactEvasionMissingnessReasonSchema = z.enum([
  'rights_blocked',
  'source_unavailable',
  'below_minimum_sample',
  'not_measured',
  'definition_incompatible',
]);

export const rbContactEvasionIdentityResolutionSchema = z.enum([
  'canonical_gsis_id',
  'unresolved',
]);

export const rbContactEvasionPositionSchema = z.enum(['QB', 'RB', 'WR', 'TE']);

/**
 * Which clock a timestamp actually came from.
 *
 * This replaces the previous timestamp-equality heuristic, which was unsound in
 * both directions: it rejected a legitimately coincident instant and let an
 * invented one-millisecond offset launder a substituted retrieval clock. A
 * declared clock origin is machine-readable and cannot be dodged by arithmetic.
 */
export const rbContactEvasionClockProvenanceSchema = z.enum([
  'football_window',
  'source_supplied',
  'not_supplied_by_source',
  'retrieval_clock',
  'artifact_build_clock',
]);

/** Clock origins that a source or window clock may never claim. */
export const RB_CONTACT_EVASION_NON_SOURCE_CLOCK_ORIGINS: ReadonlySet<
  RbContactEvasionClockProvenance
> = new Set(['retrieval_clock', 'artifact_build_clock']);

// ---------------------------------------------------------------------------
// Code-owned metric dictionary
// ---------------------------------------------------------------------------

/**
 * What a metric identity *means*, owned by this contract.
 *
 * The first review found that binding only `metric_id -> mechanisms` left the
 * payload free to redefine everything else: a row could keep a known metric id
 * while swapping its unit, flipping its directionality, pointing the numerator
 * at an unrelated metric, or emitting a value unrelated to its own numerator and
 * denominator. Each descriptor now pins all of it, and a row may only agree.
 *
 * `mechanisms: []` means the metric may never stand as mechanism evidence at all
 * — a component, a denominator, or a known-inadmissible summary (a lone long
 * gain, yards per carry, a raw touch count).
 *
 * Admitting or changing a metric is a contract change, not a data decision.
 */
export interface RbContactEvasionMetricDescriptor {
  readonly mechanisms: readonly RbContactEvasionMechanismId[];
  readonly value_kind: RbContactEvasionValueKind;
  readonly unit: string;
  readonly directionality: RbContactEvasionDirectionality;
  readonly numerator_metric_id: string | null;
  readonly denominator_metric_id: string | null;
  readonly denominator_opportunity_type: RbContactEvasionOpportunityType | null;
}

const countDescriptor = (
  mechanisms: readonly RbContactEvasionMechanismId[],
  unit: string,
): RbContactEvasionMetricDescriptor => ({
  mechanisms,
  value_kind: 'count',
  unit,
  directionality: 'higher_is_more_of_mechanism',
  numerator_metric_id: null,
  denominator_metric_id: null,
  denominator_opportunity_type: null,
});

export const RB_CONTACT_EVASION_METRIC_DICTIONARY: Readonly<
  Record<string, RbContactEvasionMetricDescriptor>
> = {
  // --- contact_avoidance ---
  forced_missed_tackles_count: countDescriptor(['contact_avoidance'], 'forced_missed_tackles'),
  forced_missed_tackles_per_rush_attempt: {
    mechanisms: ['contact_avoidance'],
    value_kind: 'rate',
    unit: 'forced_missed_tackles_per_rush_attempt',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'forced_missed_tackles_count',
    denominator_metric_id: 'rush_attempts',
    denominator_opportunity_type: 'rush_attempt',
  },
  forced_missed_tackles_per_touch: {
    mechanisms: ['contact_avoidance'],
    value_kind: 'rate',
    unit: 'forced_missed_tackles_per_touch',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'forced_missed_tackles_count',
    denominator_metric_id: 'touches',
    denominator_opportunity_type: 'touch',
  },
  // --- contact_survival ---
  yards_after_contact_total: countDescriptor(['contact_survival'], 'yards'),
  yards_after_contact_per_rush_attempt: {
    mechanisms: ['contact_survival'],
    value_kind: 'rate',
    unit: 'yards_per_rush_attempt',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'yards_after_contact_total',
    denominator_metric_id: 'rush_attempts',
    denominator_opportunity_type: 'rush_attempt',
  },
  yards_after_contact_per_contact: {
    mechanisms: ['contact_survival'],
    value_kind: 'rate',
    unit: 'yards_per_contact',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'yards_after_contact_total',
    denominator_metric_id: 'contact_events',
    denominator_opportunity_type: 'contact_event',
  },
  // --- explosiveness ---
  explosive_rushes_10_plus_count: countDescriptor(['explosiveness'], 'explosive_rushes'),
  explosive_rushes_10_plus_per_rush_attempt: {
    mechanisms: ['explosiveness'],
    value_kind: 'rate',
    unit: 'explosive_rushes_per_rush_attempt',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'explosive_rushes_10_plus_count',
    denominator_metric_id: 'rush_attempts',
    denominator_opportunity_type: 'rush_attempt',
  },
  explosive_rushes_15_plus_count: countDescriptor(['explosiveness'], 'explosive_rushes'),
  explosive_rushes_15_plus_per_rush_attempt: {
    mechanisms: ['explosiveness'],
    value_kind: 'rate',
    unit: 'explosive_rushes_per_rush_attempt',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'explosive_rushes_15_plus_count',
    denominator_metric_id: 'rush_attempts',
    denominator_opportunity_type: 'rush_attempt',
  },
  // --- speed ---
  verified_max_game_speed_mph: {
    mechanisms: ['speed'],
    value_kind: 'speed_mph',
    unit: 'miles_per_hour',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: null,
    denominator_metric_id: null,
    denominator_opportunity_type: null,
  },
  forty_yard_dash_seconds: {
    mechanisms: ['speed'],
    value_kind: 'duration_seconds',
    unit: 'seconds',
    directionality: 'lower_is_more_of_mechanism',
    numerator_metric_id: null,
    denominator_metric_id: null,
    denominator_opportunity_type: null,
  },
  // --- agility / change of direction ---
  three_cone_drill_seconds: {
    mechanisms: ['agility_change_of_direction'],
    value_kind: 'duration_seconds',
    unit: 'seconds',
    directionality: 'lower_is_more_of_mechanism',
    numerator_metric_id: null,
    denominator_metric_id: null,
    denominator_opportunity_type: null,
  },
  short_shuttle_seconds: {
    mechanisms: ['agility_change_of_direction'],
    value_kind: 'duration_seconds',
    unit: 'seconds',
    directionality: 'lower_is_more_of_mechanism',
    numerator_metric_id: null,
    denominator_metric_id: null,
    denominator_opportunity_type: null,
  },
  tracking_change_of_direction_events_count: countDescriptor(
    ['agility_change_of_direction'],
    'change_of_direction_events',
  ),
  tracking_change_of_direction_events_per_rush_attempt: {
    mechanisms: ['agility_change_of_direction'],
    value_kind: 'rate',
    unit: 'change_of_direction_events_per_rush_attempt',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'tracking_change_of_direction_events_count',
    denominator_metric_id: 'rush_attempts',
    denominator_opportunity_type: 'rush_attempt',
  },
  // --- components, denominators, and inadmissible summaries ---
  rush_attempts: countDescriptor([], 'rush_attempts'),
  receptions: countDescriptor([], 'receptions'),
  targets: countDescriptor([], 'targets'),
  touches: countDescriptor([], 'touches'),
  contact_events: countDescriptor([], 'contact_events'),
  testing_trials: countDescriptor([], 'testing_trials'),
  rush_yards_total: countDescriptor([], 'yards'),
  longest_rush_yards: countDescriptor([], 'yards'),
  yards_per_carry: {
    mechanisms: [],
    value_kind: 'rate',
    unit: 'yards_per_rush_attempt',
    directionality: 'higher_is_more_of_mechanism',
    numerator_metric_id: 'rush_yards_total',
    denominator_metric_id: 'rush_attempts',
    denominator_opportunity_type: 'rush_attempt',
  },
};

/** Decimal places an emitted rate is rounded to, owned here rather than declared per row. */
export const RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS = 3;

/** The rounded rate this contract expects for a given numerator and denominator. */
export function rbContactEvasionExpectedRate(numerator: number, denominator: number): number {
  return Number((numerator / denominator).toFixed(RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS));
}

// ---------------------------------------------------------------------------
// Code-owned minimum-sample rule
// ---------------------------------------------------------------------------

export const RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID =
  'rb_contact_evasion_fixture_only_minimum_sample_v0';

/**
 * The governing minimum-sample rule, owned in code so a row cannot set its own bar.
 *
 * **These thresholds are fixture-only pinned placeholders, not empirical
 * football thresholds.** #234 has authorized no empirical N, and this slice does
 * not invent one. They exist so the contract has a code-owned bar to enforce
 * against fixtures. Accordingly the rule's authority is `fixture_only_placeholder`
 * and {@link checkMinimumSample} **fails closed** for any observed rate in a
 * `candidate` or `promoted` artifact: a real bar has to come from an admitted
 * rule bound in Slice B before a rate may sit in either position.
 */
export const RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE = {
  rule_id: RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID,
  authority: 'fixture_only_placeholder',
  thresholds_by_window_completeness: {
    single_week: 10,
    multi_week: 20,
    partial_season: 30,
    full_season: 40,
  },
} as const satisfies {
  rule_id: string;
  authority: 'fixture_only_placeholder';
  thresholds_by_window_completeness: Record<RbContactEvasionWindowCompleteness, number>;
};

// ---------------------------------------------------------------------------
// Metric incompatibilities
// ---------------------------------------------------------------------------

/**
 * Metric pairs that may not be consumed together by one deterministic transform:
 * they carry different denominators or different opportunity universes, so a
 * transform combining them silently changes what is being measured.
 */
export const RB_CONTACT_EVASION_INCOMPATIBLE_METRIC_PAIRS: readonly (readonly [
  string,
  string,
])[] = [
  ['forced_missed_tackles_per_rush_attempt', 'forced_missed_tackles_per_touch'],
  ['yards_after_contact_per_rush_attempt', 'yards_after_contact_per_contact'],
  ['rush_attempts', 'touches'],
  ['rush_attempts', 'contact_events'],
];

function buildIncompatibilityIndex(
  pairs: readonly (readonly [string, string])[],
): Record<string, ReadonlySet<string>> {
  const index: Record<string, Set<string>> = {};
  for (const [left, right] of pairs) {
    (index[left] ??= new Set()).add(right);
    (index[right] ??= new Set()).add(left);
  }
  return index;
}

/** Symmetric `incompatible_with` adjacency, expanded from the declared pairs. */
export const RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES: Readonly<
  Record<string, ReadonlySet<string>>
> = buildIncompatibilityIndex(RB_CONTACT_EVASION_INCOMPATIBLE_METRIC_PAIRS);

/**
 * Returns every asymmetric `incompatible_with` edge in the given adjacency
 * (empty means fully symmetric). Exported so the symmetry invariant is provable
 * against the real index rather than asserted in prose.
 */
export function findRbContactEvasionIncompatibilityAsymmetries(
  index: Readonly<
    Record<string, ReadonlySet<string>>
  > = RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES,
): Array<{ from: string; to: string }> {
  const asymmetries: Array<{ from: string; to: string }> = [];
  for (const [from, targets] of Object.entries(index)) {
    for (const to of targets) {
      if (!index[to]?.has(from)) {
        asymmetries.push({ from, to });
      }
    }
  }
  return asymmetries;
}

// ---------------------------------------------------------------------------
// Reason codes
// ---------------------------------------------------------------------------

/**
 * Closed, stable reason codes. Each fixture under
 * `test/fixtures/rb_contact_evasion/negative/` is rejected by exactly one of
 * these, so a rejection can be attributed to a rule rather than to "it failed to
 * parse".
 */
export const rbContactEvasionReasonCodeSchema = z.enum([
  'SCHEMA_SHAPE_INVALID',
  'UNKNOWN_FIELD_PRESENT',
  // metric semantics
  'UNKNOWN_METRIC_ID',
  'MECHANISM_METRIC_BINDING_VIOLATION',
  'METRIC_DESCRIPTOR_CONTRADICTED',
  'METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID',
  // rate semantics
  'RATE_MISSING_DENOMINATOR',
  'RATE_COMPONENT_METRIC_MISMATCH',
  'RATE_DENOMINATOR_NOT_POSITIVE',
  'RATE_VALUE_INCONSISTENT_WITH_COMPONENTS',
  // denominators and opportunity classes
  'DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE',
  'DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH',
  'RUSHING_RECEIVING_SILENTLY_COMBINED',
  // sample sufficiency
  'ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE',
  'MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED',
  'MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION',
  'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
  // source governance
  'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
  'EXTERNAL_OPINION_LABELED_AS_OBSERVATION',
  'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE',
  'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_EVIDENCE_CLASS',
  'SNAPSHOT_WITHOUT_CONTENT_DIGEST',
  'CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION',
  'SUPERSESSION_SELF_REFERENCE',
  'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION',
  // clocks
  'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
  'CLOCK_AVAILABILITY_CONTRADICTED',
  'CLOCK_ORDER_INVALID',
  'ARTIFACT_CLOCK_MISMATCH',
  // cohort scope
  'WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED',
  'COHORT_SCOPE_MISMATCH',
  // identity, grain, measurement status
  'CANONICAL_IDENTITY_UNRESOLVED',
  'DUPLICATE_OBSERVATION_ID',
  'DUPLICATE_OBSERVATION_GRAIN',
  'MISSING_COMPONENT_CARRIES_VALUE',
  'MISSINGNESS_REASON_ABSENT',
  'OBSERVED_COMPONENT_MISSING_VALUE',
  // transforms
  'INCOMPATIBLE_METRIC_TRANSFORM_INPUT',
  'INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC',
  'DERIVED_EVIDENCE_REQUIRES_TRANSFORM',
]);

export type RbContactEvasionReasonCode = z.infer<typeof rbContactEvasionReasonCodeSchema>;

// ---------------------------------------------------------------------------
// Row / envelope shape
// ---------------------------------------------------------------------------

export const rbContactEvasionIdentitySchema = z
  .object({
    /** Canonical identity. `null` is representable so an unresolved row can be
     * *expressed* and then rejected by the contract, never silently accepted. */
    gsis_id: nonEmptyStringSchema.nullable(),
    identity_resolution: rbContactEvasionIdentityResolutionSchema,
    provider_player_id: nonEmptyStringSchema.nullable(),
    /** Display context only. Never authorizes identity. */
    display_name_non_authoritative: nonEmptyStringSchema.nullable(),
  })
  .strict();

export const rbContactEvasionScopeSchema = z
  .object({
    position_at_window: rbContactEvasionPositionSchema,
    season: z.number().int().min(1900),
    season_type: rbContactEvasionSeasonTypeSchema,
    week: z.number().int().min(1).max(22).nullable(),
    games_included: z.number().int().min(0),
    window_completeness: rbContactEvasionWindowCompletenessSchema,
    opportunity_class: rbContactEvasionOpportunityClassSchema,
  })
  .strict();

/**
 * All seven clocks. The three source clocks are nullable so an unavailable
 * source clock can stay honestly absent instead of being backfilled, and each
 * carries a declared origin in {@link rbContactEvasionClockProvenanceSchema}.
 */
export const rbContactEvasionClocksSchema = z
  .object({
    window_start: isoDatetimeSchema,
    window_end: isoDatetimeSchema,
    source_observed_at: isoDatetimeSchema.nullable(),
    source_generated_at: isoDatetimeSchema.nullable(),
    source_available_at: isoDatetimeSchema.nullable(),
    retrieved_at: isoDatetimeSchema,
    artifact_generated_at: isoDatetimeSchema,
  })
  .strict();

export const rbContactEvasionClockProvenanceMapSchema = z
  .object({
    window_start: rbContactEvasionClockProvenanceSchema,
    window_end: rbContactEvasionClockProvenanceSchema,
    source_observed_at: rbContactEvasionClockProvenanceSchema,
    source_generated_at: rbContactEvasionClockProvenanceSchema,
    source_available_at: rbContactEvasionClockProvenanceSchema,
    retrieved_at: rbContactEvasionClockProvenanceSchema,
    artifact_generated_at: rbContactEvasionClockProvenanceSchema,
  })
  .strict();

export const rbContactEvasionCombinedComponentDisclosureSchema = z
  .object({
    rushing_component_metric_id: nonEmptyStringSchema,
    receiving_component_metric_id: nonEmptyStringSchema,
    disclosure: nonEmptyStringSchema,
  })
  .strict();

/**
 * Per-row metric declaration. `value_kind`, `unit`, and `directionality` are
 * restated here for inspectability but are **not authoritative** — they must
 * equal the code-owned descriptor. `minimum_sample_rule_id` names the governing
 * rule; the row cannot state a threshold, only which rule binds it.
 */
export const rbContactEvasionMetricSchema = z
  .object({
    metric_id: nonEmptyStringSchema,
    source_native_metric_name: nonEmptyStringSchema,
    definition_ref: nonEmptyStringSchema,
    definition_version: nonEmptyStringSchema,
    unit: nonEmptyStringSchema,
    value_kind: rbContactEvasionValueKindSchema,
    directionality: rbContactEvasionDirectionalitySchema,
    minimum_sample_rule_id: nonEmptyStringSchema,
    inclusion_exclusion_rules: z.array(nonEmptyStringSchema),
    combined_component_disclosure:
      rbContactEvasionCombinedComponentDisclosureSchema.nullable(),
  })
  .strict();

export const rbContactEvasionNumeratorSchema = z
  .object({ metric_id: nonEmptyStringSchema, value: z.number() })
  .strict();

export const rbContactEvasionDenominatorSchema = z
  .object({
    metric_id: nonEmptyStringSchema,
    value: z.number(),
    opportunity_type: rbContactEvasionOpportunityTypeSchema,
  })
  .strict();

export const rbContactEvasionMeasurementSchema = z
  .object({
    status: rbContactEvasionMeasurementStatusSchema,
    missingness_reason: rbContactEvasionMissingnessReasonSchema.nullable(),
    value: z.number().nullable(),
    numerator: rbContactEvasionNumeratorSchema.nullable(),
    denominator: rbContactEvasionDenominatorSchema.nullable(),
    eligible_opportunities: z.number().int().min(0).nullable(),
  })
  .strict();

/**
 * The scope an observation is stated to be *eligible for*. Cohort membership
 * inputs only — no percentile, rank, threshold, score, or grade, and none may be
 * added (that boundary is TIBER-Ops #15, unresolved). It states no minimum
 * either: the minimum-sample bar is code-owned.
 */
export const rbContactEvasionCohortScopeSchema = z
  .object({
    position: rbContactEvasionPositionSchema,
    season: z.number().int().min(1900),
    season_type: rbContactEvasionSeasonTypeSchema,
    window_completeness: rbContactEvasionWindowCompletenessSchema,
    window_completeness_disclosure: nonEmptyStringSchema.nullable(),
  })
  .strict();

export const rbContactEvasionTransformSchema = z
  .object({
    transform_version: nonEmptyStringSchema,
    input_metric_ids: z.array(nonEmptyStringSchema).min(1),
  })
  .strict();

export const rbContactEvasionContentDigestSchema = z
  .object({ algorithm: nonEmptyStringSchema, value: nonEmptyStringSchema })
  .strict();

/**
 * Rights dispositions stated separately, per #234's source-and-rights audit.
 * Every disposition is required; `unknown` is a real answer that fails closed.
 */
export const rbContactEvasionSourcePermissionsSchema = z
  .object({
    attribution: rbContactEvasionAttributionDispositionSchema,
    retention_and_reproduction: rbContactEvasionPermissionDispositionSchema,
    redistribution_and_display: rbContactEvasionPermissionDispositionSchema,
    automated_access: rbContactEvasionPermissionDispositionSchema,
  })
  .strict();

/**
 * Source descriptor.
 *
 * Honest limitation: `access_class`, `material_kind`, `supported_opportunity_types`,
 * `promotable`, `permissions`, and `rights_review_ref` are **declared by the
 * producer**. This contract proves they are internally consistent and fails
 * closed on incompatible combinations; it cannot prove a declaration matches
 * reality. Pinning declarations to an admitted source registry is Slice B work.
 * `promotable: true` is a producer claim requiring separate promotion review; it
 * never authorizes promotion.
 */
export const rbContactEvasionSourceSchema = z
  .object({
    owner: nonEmptyStringSchema,
    product: nonEmptyStringSchema,
    snapshot_id: nonEmptyStringSchema,
    access_class: rbContactEvasionSourceAccessClassSchema,
    acquisition_method: nonEmptyStringSchema,
    material_kind: rbContactEvasionSourceMaterialKindSchema,
    supported_opportunity_types: z.array(rbContactEvasionOpportunityTypeSchema),
    rights_review_ref: nonEmptyStringSchema,
    permissions: rbContactEvasionSourcePermissionsSchema,
    content_digest: rbContactEvasionContentDigestSchema.nullable(),
    promotable: z.boolean(),
    provenance_mode: rbContactEvasionProvenanceModeSchema,
    superseded_by_snapshot_id: nonEmptyStringSchema.nullable(),
  })
  .strict();

export const rbContactEvasionObservationSchema = z
  .object({
    observation_id: nonEmptyStringSchema,
    mechanism_id: rbContactEvasionMechanismIdSchema,
    evidence_class: rbContactEvasionEvidenceClassSchema,
    identity: rbContactEvasionIdentitySchema,
    scope: rbContactEvasionScopeSchema,
    clocks: rbContactEvasionClocksSchema,
    clock_provenance: rbContactEvasionClockProvenanceMapSchema,
    metric: rbContactEvasionMetricSchema,
    measurement: rbContactEvasionMeasurementSchema,
    cohort_scope: rbContactEvasionCohortScopeSchema.nullable(),
    transform: rbContactEvasionTransformSchema.nullable(),
    source: rbContactEvasionSourceSchema,
    warnings: z.array(nonEmptyStringSchema),
  })
  .strict();

export const RB_CONTACT_EVASION_ARTIFACT_ID = 'rb_contact_evasion_observations_v0';
export const RB_CONTACT_EVASION_SCHEMA_VERSION = 'rb_contact_evasion_observations_v0.2.0';

export const rbContactEvasionObservationsV0Schema = z
  .object({
    artifact_id: z.literal(RB_CONTACT_EVASION_ARTIFACT_ID),
    schema_version: z.literal(RB_CONTACT_EVASION_SCHEMA_VERSION),
    artifact_position: rbContactEvasionArtifactPositionSchema,
    generated_at: isoDatetimeSchema,
    contract_ref: nonEmptyStringSchema,
    observations: z.array(rbContactEvasionObservationSchema),
  })
  .strict();

export type RbContactEvasionMechanismId = z.infer<typeof rbContactEvasionMechanismIdSchema>;
export type RbContactEvasionEvidenceClass = z.infer<
  typeof rbContactEvasionEvidenceClassSchema
>;
export type RbContactEvasionSourceAccessClass = z.infer<
  typeof rbContactEvasionSourceAccessClassSchema
>;
export type RbContactEvasionProvenanceMode = z.infer<
  typeof rbContactEvasionProvenanceModeSchema
>;
export type RbContactEvasionArtifactPosition = z.infer<
  typeof rbContactEvasionArtifactPositionSchema
>;
export type RbContactEvasionSourceMaterialKind = z.infer<
  typeof rbContactEvasionSourceMaterialKindSchema
>;
export type RbContactEvasionPermissionDisposition = z.infer<
  typeof rbContactEvasionPermissionDispositionSchema
>;
export type RbContactEvasionAttributionDisposition = z.infer<
  typeof rbContactEvasionAttributionDispositionSchema
>;
export type RbContactEvasionOpportunityClass = z.infer<
  typeof rbContactEvasionOpportunityClassSchema
>;
export type RbContactEvasionOpportunityType = z.infer<
  typeof rbContactEvasionOpportunityTypeSchema
>;
export type RbContactEvasionSeasonType = z.infer<typeof rbContactEvasionSeasonTypeSchema>;
export type RbContactEvasionWindowCompleteness = z.infer<
  typeof rbContactEvasionWindowCompletenessSchema
>;
export type RbContactEvasionValueKind = z.infer<typeof rbContactEvasionValueKindSchema>;
export type RbContactEvasionDirectionality = z.infer<
  typeof rbContactEvasionDirectionalitySchema
>;
export type RbContactEvasionMeasurementStatus = z.infer<
  typeof rbContactEvasionMeasurementStatusSchema
>;
export type RbContactEvasionClockProvenance = z.infer<
  typeof rbContactEvasionClockProvenanceSchema
>;
export type RbContactEvasionObservation = z.infer<typeof rbContactEvasionObservationSchema>;
export type RbContactEvasionObservationsV0 = z.infer<
  typeof rbContactEvasionObservationsV0Schema
>;

// ---------------------------------------------------------------------------
// Contract validation
// ---------------------------------------------------------------------------

export interface RbContactEvasionViolation {
  reason_code: RbContactEvasionReasonCode;
  path: string;
  detail: string;
}

export interface RbContactEvasionValidationReport {
  valid: boolean;
  /** True when the strict shape parse succeeded, so cross-field rules actually ran. */
  shape_valid: boolean;
  violations: RbContactEvasionViolation[];
  /** Unique reason codes, sorted. */
  reason_codes: RbContactEvasionReasonCode[];
}

export class RbContactEvasionContractError extends Error {
  readonly reasonCodes: RbContactEvasionReasonCode[];
  readonly violations: RbContactEvasionViolation[];

  constructor(report: RbContactEvasionValidationReport) {
    super(
      `${RB_CONTACT_EVASION_ARTIFACT_ID} contract violations: ${report.violations
        .map((v) => `${v.reason_code} at ${v.path}: ${v.detail}`)
        .join('; ')}`,
    );
    this.name = 'RbContactEvasionContractError';
    this.reasonCodes = report.reason_codes;
    this.violations = report.violations;
  }
}

type Push = (violation: RbContactEvasionViolation) => void;

function instant(value: string): number {
  return Date.parse(value);
}

function getDescriptor(metricId: string): RbContactEvasionMetricDescriptor | undefined {
  return Object.prototype.hasOwnProperty.call(RB_CONTACT_EVASION_METRIC_DICTIONARY, metricId)
    ? RB_CONTACT_EVASION_METRIC_DICTIONARY[metricId]
    : undefined;
}

function checkIdentity(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { gsis_id: gsisId, identity_resolution: resolution } = observation.identity;
  if (
    gsisId === null ||
    !RB_CONTACT_EVASION_GSIS_ID_PATTERN.test(gsisId) ||
    resolution !== 'canonical_gsis_id'
  ) {
    push({
      reason_code: 'CANONICAL_IDENTITY_UNRESOLVED',
      path: `${path}.identity`,
      detail: `canonical identity requires a gsis_id matching ${RB_CONTACT_EVASION_GSIS_ID_PATTERN} with identity_resolution "canonical_gsis_id" (got gsis_id=${JSON.stringify(gsisId)}, identity_resolution="${resolution}"); name, team, position, and provider ids never authorize identity`,
    });
  }
}

/**
 * The metric identity must mean what this contract says it means. Every
 * referenced metric id must be in the dictionary, the row's restated semantics
 * must equal the descriptor's, and the mechanism binding must hold.
 */
function checkMetricSemantics(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { metric, measurement, transform } = observation;

  const referenced: Array<{ metricId: string; where: string }> = [
    { metricId: metric.metric_id, where: `${path}.metric.metric_id` },
  ];
  if (measurement.numerator) {
    referenced.push({
      metricId: measurement.numerator.metric_id,
      where: `${path}.measurement.numerator.metric_id`,
    });
  }
  if (measurement.denominator) {
    referenced.push({
      metricId: measurement.denominator.metric_id,
      where: `${path}.measurement.denominator.metric_id`,
    });
  }
  for (const inputMetricId of transform?.input_metric_ids ?? []) {
    referenced.push({ metricId: inputMetricId, where: `${path}.transform.input_metric_ids` });
  }
  for (const { metricId, where } of referenced) {
    if (getDescriptor(metricId) === undefined) {
      push({
        reason_code: 'UNKNOWN_METRIC_ID',
        path: where,
        detail: `metric id "${metricId}" is not in the code-owned rb_contact_evasion metric dictionary; admitting a metric is a contract change`,
      });
    }
  }

  const descriptor = getDescriptor(metric.metric_id);
  if (descriptor === undefined) {
    return;
  }

  const contradictions: string[] = [];
  if (metric.value_kind !== descriptor.value_kind) {
    contradictions.push(
      `value_kind "${metric.value_kind}" != "${descriptor.value_kind}"`,
    );
  }
  if (metric.unit !== descriptor.unit) {
    contradictions.push(`unit "${metric.unit}" != "${descriptor.unit}"`);
  }
  if (metric.directionality !== descriptor.directionality) {
    contradictions.push(
      `directionality "${metric.directionality}" != "${descriptor.directionality}"`,
    );
  }
  if (contradictions.length > 0) {
    push({
      reason_code: 'METRIC_DESCRIPTOR_CONTRADICTED',
      path: `${path}.metric`,
      detail: `metric "${metric.metric_id}" restates semantics that contradict the code-owned descriptor (${contradictions.join('; ')}); the contract owns metric meaning, the row may only agree`,
    });
  }

  if (!descriptor.mechanisms.includes(observation.mechanism_id)) {
    push({
      reason_code: 'MECHANISM_METRIC_BINDING_VIOLATION',
      path: `${path}.mechanism_id`,
      detail:
        descriptor.mechanisms.length === 0
          ? `metric "${metric.metric_id}" may never stand as mechanism evidence (it is a component, denominator, or known-inadmissible summary), but it is declared under mechanism "${observation.mechanism_id}"`
          : `metric "${metric.metric_id}" may only evidence [${descriptor.mechanisms.join(', ')}], but it is declared under mechanism "${observation.mechanism_id}"; evidence for one mechanism never satisfies another`,
    });
  }
}

/**
 * Rate arithmetic and component identity. A rate must name the numerator and
 * denominator metrics its descriptor declares, carry a positive denominator, and
 * emit the value its own components imply at the contract's rounding.
 */
function checkRateSemantics(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { metric, measurement } = observation;
  const descriptor = getDescriptor(metric.metric_id);
  if (
    descriptor === undefined ||
    descriptor.value_kind !== 'rate' ||
    measurement.status !== 'observed'
  ) {
    return;
  }
  const measurementPath = `${path}.measurement`;
  const { numerator, denominator, value } = measurement;

  if (numerator === null || denominator === null) {
    push({
      reason_code: 'RATE_MISSING_DENOMINATOR',
      path: measurementPath,
      detail: `a rate requires exact numerator and denominator metric ids and values (numerator=${JSON.stringify(numerator)}, denominator=${JSON.stringify(denominator)}); a rate without an exact denominator is not comparable to any other source's similarly named rate`,
    });
    return;
  }

  const mismatches: string[] = [];
  if (numerator.metric_id !== descriptor.numerator_metric_id) {
    mismatches.push(
      `numerator "${numerator.metric_id}" != declared "${descriptor.numerator_metric_id}"`,
    );
  }
  if (denominator.metric_id !== descriptor.denominator_metric_id) {
    mismatches.push(
      `denominator "${denominator.metric_id}" != declared "${descriptor.denominator_metric_id}"`,
    );
  }
  if (denominator.opportunity_type !== descriptor.denominator_opportunity_type) {
    mismatches.push(
      `denominator opportunity_type "${denominator.opportunity_type}" != declared "${descriptor.denominator_opportunity_type}"`,
    );
  }
  if (mismatches.length > 0) {
    push({
      reason_code: 'RATE_COMPONENT_METRIC_MISMATCH',
      path: measurementPath,
      detail: `metric "${metric.metric_id}" is composed of components the code-owned descriptor does not declare (${mismatches.join('; ')}); a known metric name does not license arbitrary components`,
    });
    return;
  }

  if (!(denominator.value > 0)) {
    push({
      reason_code: 'RATE_DENOMINATOR_NOT_POSITIVE',
      path: `${measurementPath}.denominator.value`,
      detail: `a rate denominator must be strictly positive, got ${denominator.value}; a zero or negative opportunity count cannot produce a rate`,
    });
    return;
  }

  if (value !== null) {
    const expected = rbContactEvasionExpectedRate(numerator.value, denominator.value);
    if (Math.abs(value - expected) > 1e-9) {
      push({
        reason_code: 'RATE_VALUE_INCONSISTENT_WITH_COMPONENTS',
        path: `${measurementPath}.value`,
        detail: `emitted value ${value} does not equal ${numerator.value}/${denominator.value} rounded to ${RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS} decimals (${expected}); the numerator and denominator define the rate, not the emitted number`,
      });
    }
  }
}

/**
 * Sample sufficiency, bound to the code-owned rule rather than to the row.
 * Fails closed outside `fixture_only`, because the pinned thresholds are
 * fixture placeholders and #234 has authorized no empirical minimum.
 */
function checkMinimumSample(
  observation: RbContactEvasionObservation,
  artifactPosition: RbContactEvasionArtifactPosition,
  path: string,
  push: Push,
): void {
  const { metric, measurement, scope } = observation;
  const descriptor = getDescriptor(metric.metric_id);
  if (
    descriptor === undefined ||
    descriptor.value_kind !== 'rate' ||
    measurement.status !== 'observed'
  ) {
    return;
  }
  const measurementPath = `${path}.measurement`;

  if (metric.minimum_sample_rule_id !== RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID) {
    push({
      reason_code: 'MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED',
      path: `${path}.metric.minimum_sample_rule_id`,
      detail: `minimum_sample_rule_id "${metric.minimum_sample_rule_id}" is not the code-owned rule "${RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID}"; a row names the governing rule, it never states its own threshold`,
    });
    return;
  }

  if (artifactPosition !== 'fixture_only') {
    push({
      reason_code: 'MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION',
      path: `${path}.metric.minimum_sample_rule_id`,
      detail: `the only minimum-sample rule bound in this contract has authority "${RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.authority}" and cannot govern an observed rate at artifact_position "${artifactPosition}"; an admitted rule must be bound before a rate may sit in a candidate or promoted artifact`,
    });
    return;
  }

  if (measurement.eligible_opportunities === null) {
    push({
      reason_code: 'ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE',
      path: `${measurementPath}.eligible_opportunities`,
      detail: 'an observed rate must state its eligible opportunities; a null sample cannot be checked against any minimum',
    });
    return;
  }

  const threshold =
    RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.thresholds_by_window_completeness[
      scope.window_completeness
    ];
  if (measurement.eligible_opportunities < threshold) {
    push({
      reason_code: 'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
      path: measurementPath,
      detail: `eligible_opportunities ${measurement.eligible_opportunities} is below the code-owned minimum ${threshold} for window_completeness "${scope.window_completeness}"; a below-minimum sample must be emitted as status "missing" with missingness_reason "below_minimum_sample" and no value`,
    });
  }
}

function checkMeasurementStatus(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { measurement } = observation;
  const measurementPath = `${path}.measurement`;

  if (measurement.status === 'missing') {
    if (
      measurement.value !== null ||
      measurement.numerator !== null ||
      measurement.denominator !== null
    ) {
      push({
        reason_code: 'MISSING_COMPONENT_CARRIES_VALUE',
        path: measurementPath,
        detail: `a missing component carries no value: status "missing" requires value, numerator, and denominator to be null (got value=${JSON.stringify(measurement.value)}); a neutral or default stand-in is never permitted`,
      });
    }
    if (measurement.missingness_reason === null) {
      push({
        reason_code: 'MISSINGNESS_REASON_ABSENT',
        path: `${measurementPath}.missingness_reason`,
        detail: 'status "missing" requires an explicit missingness_reason',
      });
    }
    return;
  }

  if (measurement.value === null || measurement.missingness_reason !== null) {
    push({
      reason_code: 'OBSERVED_COMPONENT_MISSING_VALUE',
      path: measurementPath,
      detail: `status "observed" requires a non-null value and a null missingness_reason (got value=${JSON.stringify(measurement.value)}, missingness_reason=${JSON.stringify(measurement.missingness_reason)})`,
    });
  }
}

function checkDenominatorSemantics(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { scope, metric, measurement, source } = observation;
  const denominator = measurement.denominator;
  const opportunityClass = scope.opportunity_class;

  if (
    opportunityClass === 'combined_rushing_receiving' &&
    metric.combined_component_disclosure === null
  ) {
    push({
      reason_code: 'RUSHING_RECEIVING_SILENTLY_COMBINED',
      path: `${path}.metric.combined_component_disclosure`,
      detail:
        'opportunity_class "combined_rushing_receiving" requires an explicit combined_component_disclosure naming the rushing and receiving component metrics; rushing and receiving observations are never combined silently',
    });
  }

  if (denominator === null) {
    return;
  }
  const denominatorPath = `${path}.measurement.denominator`;
  const opportunityType = denominator.opportunity_type;

  if (RB_CONTACT_EVASION_CROSS_CLASS_OPPORTUNITY_TYPES.has(opportunityType)) {
    if (opportunityClass !== 'combined_rushing_receiving') {
      push({
        reason_code: 'RUSHING_RECEIVING_SILENTLY_COMBINED',
        path: denominatorPath,
        detail: `denominator opportunity_type "${opportunityType}" spans rushing and receiving opportunity but opportunity_class is "${opportunityClass}"; a cross-class denominator requires opportunity_class "combined_rushing_receiving" with a combined_component_disclosure`,
      });
    }
  } else if (
    !RB_CONTACT_EVASION_CLASS_OPPORTUNITY_TYPES[opportunityClass].includes(opportunityType)
  ) {
    push({
      reason_code: 'DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH',
      path: denominatorPath,
      detail: `denominator opportunity_type "${opportunityType}" is not admissible for opportunity_class "${opportunityClass}" (admissible: ${RB_CONTACT_EVASION_CLASS_OPPORTUNITY_TYPES[opportunityClass].join(', ')})`,
    });
  }

  if (!source.supported_opportunity_types.includes(opportunityType)) {
    push({
      reason_code: 'DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE',
      path: denominatorPath,
      detail: `denominator opportunity_type "${opportunityType}" is not in the declared source's supported_opportunity_types [${source.supported_opportunity_types.join(', ')}]; the declared source must actually support the denominator`,
    });
  }
}

/**
 * Clock availability, origin, and ordering.
 *
 * Substitution is rejected by the declared clock origin, not by timestamp
 * equality — equality was unsound in both directions. Ordering is checked only
 * between clocks that actually exist, so an unavailable source clock stays null
 * rather than being backfilled to satisfy a comparison.
 */
function checkClocks(
  observation: RbContactEvasionObservation,
  envelopeGeneratedAt: string,
  path: string,
  push: Push,
): void {
  const { clocks, clock_provenance: provenance } = observation;
  const clocksPath = `${path}.clocks`;
  const provenancePath = `${path}.clock_provenance`;

  const sourceClocks = [
    ['source_observed_at', clocks.source_observed_at, provenance.source_observed_at],
    ['source_generated_at', clocks.source_generated_at, provenance.source_generated_at],
    ['source_available_at', clocks.source_available_at, provenance.source_available_at],
  ] as const;

  for (const [name, value, origin] of sourceClocks) {
    if (RB_CONTACT_EVASION_NON_SOURCE_CLOCK_ORIGINS.has(origin)) {
      push({
        reason_code: 'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
        path: `${provenancePath}.${name}`,
        detail: `${name} declares origin "${origin}"; retrieval and artifact-build clocks never substitute for a source clock`,
      });
      continue;
    }
    if (origin === 'football_window') {
      push({
        reason_code: 'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
        path: `${provenancePath}.${name}`,
        detail: `${name} declares origin "football_window"; a football window never substitutes for a source clock`,
      });
      continue;
    }
    if (origin === 'source_supplied' && value === null) {
      push({
        reason_code: 'CLOCK_AVAILABILITY_CONTRADICTED',
        path: `${clocksPath}.${name}`,
        detail: `${name} declares origin "source_supplied" but carries no timestamp`,
      });
    }
    if (origin === 'not_supplied_by_source' && value !== null) {
      push({
        reason_code: 'CLOCK_AVAILABILITY_CONTRADICTED',
        path: `${clocksPath}.${name}`,
        detail: `${name} declares origin "not_supplied_by_source" but carries timestamp ${value}; an unavailable source clock stays null rather than being backfilled`,
      });
    }
  }

  for (const [name, expected] of [
    ['window_start', 'football_window'],
    ['window_end', 'football_window'],
    ['retrieved_at', 'retrieval_clock'],
    ['artifact_generated_at', 'artifact_build_clock'],
  ] as const) {
    if (provenance[name] !== expected) {
      push({
        reason_code: 'CLOCK_AVAILABILITY_CONTRADICTED',
        path: `${provenancePath}.${name}`,
        detail: `${name} must declare origin "${expected}", got "${provenance[name]}"`,
      });
    }
  }

  // Ordering, evaluated only between clocks that exist.
  const ordered: Array<[string, string | null, string, string | null]> = [
    ['window_start', clocks.window_start, 'window_end', clocks.window_end],
    ['source_observed_at', clocks.source_observed_at, 'source_generated_at', clocks.source_generated_at],
    ['source_generated_at', clocks.source_generated_at, 'source_available_at', clocks.source_available_at],
    ['source_available_at', clocks.source_available_at, 'retrieved_at', clocks.retrieved_at],
    ['source_generated_at', clocks.source_generated_at, 'retrieved_at', clocks.retrieved_at],
    ['retrieved_at', clocks.retrieved_at, 'artifact_generated_at', clocks.artifact_generated_at],
  ];
  for (const [earlierName, earlier, laterName, later] of ordered) {
    if (earlier !== null && later !== null && instant(earlier) > instant(later)) {
      push({
        reason_code: 'CLOCK_ORDER_INVALID',
        path: clocksPath,
        detail: `${earlierName} (${earlier}) must not be after ${laterName} (${later})`,
      });
    }
  }

  if (instant(clocks.artifact_generated_at) !== instant(envelopeGeneratedAt)) {
    push({
      reason_code: 'ARTIFACT_CLOCK_MISMATCH',
      path: `${clocksPath}.artifact_generated_at`,
      detail: `artifact_generated_at (${clocks.artifact_generated_at}) must equal the envelope generated_at (${envelopeGeneratedAt})`,
    });
  }
}

function checkSourceAndEvidence(
  observation: RbContactEvasionObservation,
  artifactPosition: RbContactEvasionArtifactPosition,
  path: string,
  push: Push,
): void {
  const { source, evidence_class: evidenceClass, measurement, transform } = observation;
  const sourcePath = `${path}.source`;
  const permissions = source.permissions;
  const observed = measurement.status === 'observed';

  if (RB_CONTACT_EVASION_RESTRICTED_ACCESS_CLASSES.has(source.access_class)) {
    if (source.promotable) {
      push({
        reason_code: 'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
        path: `${sourcePath}.promotable`,
        detail: `source access_class "${source.access_class}" cannot be marked promotable`,
      });
    }
    if (observed && evidenceClass !== 'external_opinion') {
      push({
        reason_code: 'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
        path: `${path}.evidence_class`,
        detail: `source access_class "${source.access_class}" cannot back an observed value classified "${evidenceClass}"; a restricted source yields either no value (status "missing") or a cited "external_opinion"`,
      });
    }
  }

  if (source.material_kind === 'editorial_opinion' && evidenceClass !== 'external_opinion') {
    push({
      reason_code: 'EXTERNAL_OPINION_LABELED_AS_OBSERVATION',
      path: `${path}.evidence_class`,
      detail: `source material_kind "editorial_opinion" requires evidence_class "external_opinion", got "${evidenceClass}"`,
    });
  }

  // Promotability requires every rights disposition to be affirmatively settled.
  if (source.promotable) {
    const blockers: Array<[string, string]> = [
      ['retention_and_reproduction', permissions.retention_and_reproduction],
      ['redistribution_and_display', permissions.redistribution_and_display],
      ['automated_access', permissions.automated_access],
    ].filter(([, disposition]) => disposition !== 'permitted') as Array<[string, string]>;
    if (permissions.attribution === 'unknown') {
      blockers.push(['attribution', permissions.attribution]);
    }
    if (blockers.length > 0) {
      push({
        reason_code: 'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE',
        path: `${sourcePath}.permissions`,
        detail: `promotable "true" requires retention_and_reproduction, redistribution_and_display, and automated_access all "permitted" and attribution settled, but ${blockers.map(([name, disposition]) => `${name}="${disposition}"`).join(', ')}`,
      });
    }
  }

  // Storing an exact observed value requires retention and automated access.
  // Only a cited `external_opinion` escapes this: it reproduces a published
  // claim rather than storing measured payload values.
  if (observed && evidenceClass !== 'external_opinion') {
    const blockers: Array<[string, string]> = [
      ['retention_and_reproduction', permissions.retention_and_reproduction],
      ['automated_access', permissions.automated_access],
    ].filter(([, disposition]) => disposition !== 'permitted') as Array<[string, string]>;
    if (blockers.length > 0) {
      push({
        reason_code: 'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_EVIDENCE_CLASS',
        path: `${sourcePath}.permissions`,
        detail: `evidence_class "${evidenceClass}" stores an exact observed value (only a cited "external_opinion" does not), which requires retention_and_reproduction and automated_access "permitted", but ${blockers.map(([name, disposition]) => `${name}="${disposition}"`).join(', ')}`,
      });
    }
  }

  if (source.provenance_mode === 'snapshot' && source.content_digest === null) {
    push({
      reason_code: 'SNAPSHOT_WITHOUT_CONTENT_DIGEST',
      path: `${sourcePath}.content_digest`,
      detail: 'provenance_mode "snapshot" requires a content digest; a snapshot with no digest cannot prove a rebuild consumed the same bytes',
    });
  }

  if (
    source.content_digest !== null &&
    permissions.retention_and_reproduction === 'prohibited'
  ) {
    push({
      reason_code: 'CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION',
      path: `${sourcePath}.content_digest`,
      detail: 'a content digest of payload bytes cannot be recorded when retention_and_reproduction is "prohibited"',
    });
  }

  if (evidenceClass === 'derived' && transform === null) {
    push({
      reason_code: 'DERIVED_EVIDENCE_REQUIRES_TRANSFORM',
      path: `${path}.transform`,
      detail: 'evidence_class "derived" requires an explicit transform with a transform_version and input metric ids',
    });
  }

  if (source.superseded_by_snapshot_id === source.snapshot_id) {
    push({
      reason_code: 'SUPERSESSION_SELF_REFERENCE',
      path: `${sourcePath}.superseded_by_snapshot_id`,
      detail: `snapshot "${source.snapshot_id}" cannot supersede itself`,
    });
  }

  if (source.provenance_mode === 'fixture' && artifactPosition !== 'fixture_only') {
    push({
      reason_code: 'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION',
      path: `${sourcePath}.provenance_mode`,
      detail: `provenance_mode "fixture" cannot appear in an artifact at position "${artifactPosition}"; fixture data never becomes candidate or promoted truth by position`,
    });
  }
}

function checkCohortScope(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const cohort = observation.cohort_scope;
  if (cohort === null) {
    return;
  }
  const cohortPath = `${path}.cohort_scope`;
  const { scope } = observation;

  const mismatches: string[] = [];
  if (cohort.position !== scope.position_at_window) {
    mismatches.push(`position ${cohort.position} != ${scope.position_at_window}`);
  }
  if (cohort.season !== scope.season) {
    mismatches.push(`season ${cohort.season} != ${scope.season}`);
  }
  if (cohort.season_type !== scope.season_type) {
    mismatches.push(`season_type ${cohort.season_type} != ${scope.season_type}`);
  }
  if (mismatches.length > 0) {
    push({
      reason_code: 'COHORT_SCOPE_MISMATCH',
      path: cohortPath,
      detail: `declared cohort scope does not match the observation scope (${mismatches.join('; ')})`,
    });
  }

  if (
    cohort.window_completeness !== scope.window_completeness &&
    (cohort.window_completeness_disclosure === null ||
      cohort.window_completeness_disclosure.trim() === '')
  ) {
    push({
      reason_code: 'WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED',
      path: `${cohortPath}.window_completeness_disclosure`,
      detail: `observation window_completeness "${scope.window_completeness}" is stated against a cohort of window_completeness "${cohort.window_completeness}" with no disclosure; partial-window and full-window comparison requires explicit disclosure`,
    });
  }
}

function checkTransform(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const transform = observation.transform;
  if (transform === null) {
    return;
  }
  const inputs = transform.input_metric_ids;
  for (let i = 0; i < inputs.length; i += 1) {
    for (let j = i + 1; j < inputs.length; j += 1) {
      if (RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES[inputs[i]]?.has(inputs[j])) {
        push({
          reason_code: 'INCOMPATIBLE_METRIC_TRANSFORM_INPUT',
          path: `${path}.transform.input_metric_ids`,
          detail: `transform consumes incompatible metrics "${inputs[i]}" and "${inputs[j]}"; their denominators or opportunity universes differ, so combining them changes what is measured`,
        });
      }
    }
  }
}

/** The declared one-row grain, as a comparable key. */
export function rbContactEvasionGrainKey(observation: RbContactEvasionObservation): string {
  const { identity, scope, clocks, metric, measurement, source } = observation;
  return JSON.stringify([
    identity.gsis_id,
    scope.season,
    scope.season_type,
    scope.week,
    scope.window_completeness,
    clocks.window_start,
    clocks.window_end,
    metric.metric_id,
    metric.definition_version,
    source.snapshot_id,
    measurement.denominator?.metric_id ?? null,
    measurement.denominator?.opportunity_type ?? null,
  ]);
}

/**
 * Artifact-level identity and grain uniqueness. Without this, the same
 * observation could appear twice and be double-counted downstream, which
 * contradicts the declared one-row grain.
 */
function checkArtifactUniqueness(
  observations: RbContactEvasionObservation[],
  push: Push,
): void {
  const seenIds = new Map<string, number>();
  const seenGrains = new Map<string, number>();
  observations.forEach((observation, index) => {
    const priorId = seenIds.get(observation.observation_id);
    if (priorId === undefined) {
      seenIds.set(observation.observation_id, index);
    } else {
      push({
        reason_code: 'DUPLICATE_OBSERVATION_ID',
        path: `observations[${index}].observation_id`,
        detail: `observation_id "${observation.observation_id}" already appears at observations[${priorId}]; observation ids are unique within an artifact`,
      });
    }

    const grain = rbContactEvasionGrainKey(observation);
    const priorGrain = seenGrains.get(grain);
    if (priorGrain === undefined) {
      seenGrains.set(grain, index);
    } else {
      push({
        reason_code: 'DUPLICATE_OBSERVATION_GRAIN',
        path: `observations[${index}]`,
        detail: `this row repeats the canonical grain (player x window x metric definition x source snapshot x denominator) already present at observations[${priorGrain}]; the declared one-row grain forbids double-counting`,
      });
    }
  });
}

function checkDefinitionDrift(
  observations: RbContactEvasionObservation[],
  push: Push,
): void {
  const seen = new Map<string, { definition: string; index: number }>();
  observations.forEach((observation, index) => {
    const { metric } = observation;
    const definition = JSON.stringify([
      metric.source_native_metric_name,
      metric.definition_ref,
      metric.definition_version,
    ]);
    const previous = seen.get(metric.metric_id);
    if (previous === undefined) {
      seen.set(metric.metric_id, { definition, index });
      return;
    }
    if (previous.definition !== definition) {
      push({
        reason_code: 'METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID',
        path: `observations[${index}].metric`,
        detail: `metric_id "${metric.metric_id}" carries definition ${definition} here but ${previous.definition} at observations[${previous.index}]; a changed definition requires a new metric identity`,
      });
    }
  });
}

/**
 * Evaluate an artifact against the full `rb_contact_evasion_observations_v0`
 * contract and return every violation with its machine-readable reason code.
 *
 * The strict shape parse runs first. When it fails, cross-field rules are not
 * run and the report says so via `shape_valid: false` — so a caller can always
 * distinguish "rejected by a contract rule" from "did not parse".
 */
export function evaluateRbContactEvasionObservationsV0(
  input: unknown,
): RbContactEvasionValidationReport {
  const violations: RbContactEvasionViolation[] = [];
  const push: Push = (violation) => {
    violations.push(violation);
  };

  const parsed = rbContactEvasionObservationsV0Schema.safeParse(input);
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      push({
        reason_code:
          issue.code === z.ZodIssueCode.unrecognized_keys
            ? 'UNKNOWN_FIELD_PRESENT'
            : 'SCHEMA_SHAPE_INVALID',
        path: issue.path.length > 0 ? issue.path.join('.') : '<root>',
        detail: issue.message,
      });
    }
    return buildReport(false, violations);
  }

  const artifact = parsed.data;

  for (const asymmetry of findRbContactEvasionIncompatibilityAsymmetries()) {
    push({
      reason_code: 'INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC',
      path: 'RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES',
      detail: `"${asymmetry.from}" declares "${asymmetry.to}" incompatible without the reverse edge`,
    });
  }

  artifact.observations.forEach((observation, index) => {
    const path = `observations[${index}]`;
    checkIdentity(observation, path, push);
    checkMetricSemantics(observation, path, push);
    checkMeasurementStatus(observation, path, push);
    checkRateSemantics(observation, path, push);
    checkMinimumSample(observation, artifact.artifact_position, path, push);
    checkDenominatorSemantics(observation, path, push);
    checkClocks(observation, artifact.generated_at, path, push);
    checkSourceAndEvidence(observation, artifact.artifact_position, path, push);
    checkCohortScope(observation, path, push);
    checkTransform(observation, path, push);
  });

  checkArtifactUniqueness(artifact.observations, push);
  checkDefinitionDrift(artifact.observations, push);

  return buildReport(true, violations);
}

function buildReport(
  shapeValid: boolean,
  violations: RbContactEvasionViolation[],
): RbContactEvasionValidationReport {
  const reasonCodes = [...new Set(violations.map((v) => v.reason_code))].sort();
  return { valid: violations.length === 0, shape_valid: shapeValid, violations, reason_codes: reasonCodes };
}

/**
 * Contract gate. Returns the parsed artifact, or throws
 * {@link RbContactEvasionContractError} carrying every reason code.
 */
export function validateRbContactEvasionObservationsV0(
  input: unknown,
): RbContactEvasionObservationsV0 {
  const report = evaluateRbContactEvasionObservationsV0(input);
  if (!report.valid) {
    throw new RbContactEvasionContractError(report);
  }
  return rbContactEvasionObservationsV0Schema.parse(input);
}

export function isRbContactEvasionObservationsV0(
  input: unknown,
): input is RbContactEvasionObservationsV0 {
  return evaluateRbContactEvasionObservationsV0(input).valid;
}

/**
 * Per-mechanism coverage receipt for one canonical player.
 *
 * Deliberately emits no composite, average, score, grade, or ranking: each of
 * the five mechanisms reports its own observed/missing state, and a mechanism
 * with no admitted observation stays `no_admitted_observation`. This is the
 * shape a later claim assessment reads; it is not itself an assessment, and
 * `observed` means an observation row exists, never that the evidence is good.
 */
export function summarizeRbContactEvasionMechanismCoverage(
  artifact: Pick<RbContactEvasionObservationsV0, 'observations'>,
  gsisId: string,
): Record<
  RbContactEvasionMechanismId,
  { observed_observation_ids: string[]; missing_observation_ids: string[]; status: string }
> {
  const summary = {} as Record<
    RbContactEvasionMechanismId,
    { observed_observation_ids: string[]; missing_observation_ids: string[]; status: string }
  >;
  for (const mechanismId of rbContactEvasionMechanismIdSchema.options) {
    summary[mechanismId] = {
      observed_observation_ids: [],
      missing_observation_ids: [],
      status: 'no_admitted_observation',
    };
  }
  for (const observation of artifact.observations) {
    if (observation.identity.gsis_id !== gsisId) {
      continue;
    }
    const entry = summary[observation.mechanism_id];
    if (observation.measurement.status === 'observed') {
      entry.observed_observation_ids.push(observation.observation_id);
    } else {
      entry.missing_observation_ids.push(observation.observation_id);
    }
  }
  for (const mechanismId of rbContactEvasionMechanismIdSchema.options) {
    const entry = summary[mechanismId];
    if (entry.observed_observation_ids.length > 0) {
      entry.status = 'observed';
    } else if (entry.missing_observation_ids.length > 0) {
      entry.status = 'known_missing';
    }
  }
  return summary;
}
