import { z } from 'zod';

/**
 * `rb_contact_evasion_observations_v0` — source-observation contract for the RB
 * contact-evasion mechanism lane (TIBER-Data #234, Slice A).
 *
 * This module is a **contract and validation surface only**. It does not build,
 * ingest, promote, normalize, rank, or score anything. It defines the shape a
 * candidate artifact would have to satisfy, and the machine-readable reason
 * codes by which a non-conforming artifact is rejected.
 *
 * Deliberate absences (see `docs/contracts/rb-contact-evasion-observations-v0.md`):
 * there is no score, composite, grade, ranking, percentile, tier, neutral
 * default, or "elite" judgment anywhere in this contract. A mechanism with no
 * admitted evidence stays missing; it is never filled from another mechanism.
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

// ---------------------------------------------------------------------------
// Metric registry: metric identity -> the mechanisms it may ever evidence
// ---------------------------------------------------------------------------

/**
 * Closed metric registry. The value is the set of mechanisms a metric may
 * evidence — an **empty** set means the metric is a component/denominator or a
 * known-inadmissible summary statistic that may never stand as mechanism
 * evidence at all (a lone long gain, yards per carry, a raw touch count).
 *
 * Admitting a new metric is a contract change, not a data decision. This is the
 * structure that stops evidence for one mechanism from satisfying another.
 */
export const RB_CONTACT_EVASION_METRIC_REGISTRY: Readonly<
  Record<string, readonly RbContactEvasionMechanismId[]>
> = {
  // contact_avoidance
  forced_missed_tackles_count: ['contact_avoidance'],
  forced_missed_tackles_per_rush_attempt: ['contact_avoidance'],
  forced_missed_tackles_per_touch: ['contact_avoidance'],
  // contact_survival
  yards_after_contact_total: ['contact_survival'],
  yards_after_contact_per_rush_attempt: ['contact_survival'],
  yards_after_contact_per_contact: ['contact_survival'],
  // explosiveness
  explosive_rushes_10_plus_count: ['explosiveness'],
  explosive_rushes_10_plus_per_rush_attempt: ['explosiveness'],
  explosive_rushes_15_plus_per_rush_attempt: ['explosiveness'],
  // speed
  verified_max_game_speed_mph: ['speed'],
  forty_yard_dash_seconds: ['speed'],
  // agility / change of direction
  three_cone_drill_seconds: ['agility_change_of_direction'],
  short_shuttle_seconds: ['agility_change_of_direction'],
  tracking_change_of_direction_events_count: ['agility_change_of_direction'],
  tracking_change_of_direction_events_per_rush_attempt: ['agility_change_of_direction'],
  // components, denominators, and inadmissible summaries (never mechanism evidence)
  rush_attempts: [],
  receptions: [],
  targets: [],
  touches: [],
  contact_events: [],
  testing_trials: [],
  rush_yards_total: [],
  longest_rush_yards: [],
  yards_per_carry: [],
};

/**
 * Metric pairs that may not be consumed together by one deterministic transform:
 * they carry different denominators or different opportunity universes, so a
 * transform combining them silently changes what is being measured.
 *
 * Declared once as unordered pairs; {@link RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES}
 * is expanded symmetrically from these and
 * {@link findRbContactEvasionIncompatibilityAsymmetries} proves the symmetry.
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
  index: Readonly<Record<string, ReadonlySet<string>>> = RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES,
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
 * Closed, stable reason codes. Each negative fixture under
 * `test/fixtures/rb_contact_evasion/negative/` is rejected by exactly one of
 * these, so a rejection can be attributed to a rule rather than to "it failed
 * to parse".
 */
export const rbContactEvasionReasonCodeSchema = z.enum([
  'SCHEMA_SHAPE_INVALID',
  'UNKNOWN_FIELD_PRESENT',
  'RATE_MISSING_DENOMINATOR',
  'DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE',
  'DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH',
  'RUSHING_RECEIVING_SILENTLY_COMBINED',
  'METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID',
  'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
  'EXTERNAL_OPINION_LABELED_AS_OBSERVATION',
  'WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED',
  'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
  'COHORT_SCOPE_MISMATCH',
  'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
  'CLOCK_ORDER_INVALID',
  'ARTIFACT_CLOCK_MISMATCH',
  'CANONICAL_IDENTITY_UNRESOLVED',
  'MECHANISM_METRIC_BINDING_VIOLATION',
  'UNKNOWN_METRIC_ID',
  'MISSING_COMPONENT_CARRIES_VALUE',
  'MISSINGNESS_REASON_ABSENT',
  'OBSERVED_COMPONENT_MISSING_VALUE',
  'INCOMPATIBLE_METRIC_TRANSFORM_INPUT',
  'INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC',
  'DERIVED_EVIDENCE_REQUIRES_TRANSFORM',
  'SUPERSESSION_SELF_REFERENCE',
  'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION',
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

/** All seven clocks, each with its own meaning. None substitutes for another. */
export const rbContactEvasionClocksSchema = z
  .object({
    window_start: isoDatetimeSchema,
    window_end: isoDatetimeSchema,
    source_observed_at: isoDatetimeSchema.nullable(),
    source_generated_at: isoDatetimeSchema,
    source_available_at: isoDatetimeSchema,
    retrieved_at: isoDatetimeSchema,
    artifact_generated_at: isoDatetimeSchema,
  })
  .strict();

export const rbContactEvasionCombinedComponentDisclosureSchema = z
  .object({
    rushing_component_metric_id: nonEmptyStringSchema,
    receiving_component_metric_id: nonEmptyStringSchema,
    disclosure: nonEmptyStringSchema,
  })
  .strict();

export const rbContactEvasionMetricSchema = z
  .object({
    metric_id: nonEmptyStringSchema,
    source_native_metric_name: nonEmptyStringSchema,
    definition_ref: nonEmptyStringSchema,
    definition_version: nonEmptyStringSchema,
    unit: nonEmptyStringSchema,
    value_kind: rbContactEvasionValueKindSchema,
    directionality: rbContactEvasionDirectionalitySchema,
    minimum_eligible_opportunities: z.number().int().min(0),
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
 * The scope an observation is stated to be *eligible for*. This records cohort
 * membership inputs only — it carries no percentile, rank, threshold, or score,
 * and none may be added here (that boundary is TIBER-Ops #15, unresolved).
 */
export const rbContactEvasionCohortScopeSchema = z
  .object({
    position: rbContactEvasionPositionSchema,
    season: z.number().int().min(1900),
    season_type: rbContactEvasionSeasonTypeSchema,
    window_completeness: rbContactEvasionWindowCompletenessSchema,
    minimum_eligible_opportunities: z.number().int().min(0),
    window_completeness_disclosure: nonEmptyStringSchema.nullable(),
  })
  .strict();

export const rbContactEvasionTransformSchema = z
  .object({
    transform_version: nonEmptyStringSchema,
    input_metric_ids: z.array(nonEmptyStringSchema).min(1),
  })
  .strict();

/**
 * Source descriptor.
 *
 * Honest limitation: `access_class`, `material_kind`, `supported_opportunity_types`,
 * `promotable`, and `rights_review_ref` are **declared by the producer**. This
 * contract can prove they are internally consistent (a gated source cannot also
 * be promotable; an editorial source cannot also be a direct observation; a
 * denominator cannot exceed what the source declares it supports) — it cannot
 * prove the declaration matches reality. Pinning declarations to an admitted
 * source registry is Slice B work and is not implemented here. `promotable: true`
 * is a producer claim requiring separate promotion review; it never authorizes
 * promotion.
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
    metric: rbContactEvasionMetricSchema,
    measurement: rbContactEvasionMeasurementSchema,
    cohort_scope: rbContactEvasionCohortScopeSchema.nullable(),
    transform: rbContactEvasionTransformSchema.nullable(),
    source: rbContactEvasionSourceSchema,
    warnings: z.array(nonEmptyStringSchema),
  })
  .strict();

export const RB_CONTACT_EVASION_ARTIFACT_ID = 'rb_contact_evasion_observations_v0';
export const RB_CONTACT_EVASION_SCHEMA_VERSION =
  'rb_contact_evasion_observations_v0.1.0';

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

export type RbContactEvasionMechanismId = z.infer<
  typeof rbContactEvasionMechanismIdSchema
>;
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
export type RbContactEvasionMeasurementStatus = z.infer<
  typeof rbContactEvasionMeasurementStatusSchema
>;
export type RbContactEvasionObservation = z.infer<
  typeof rbContactEvasionObservationSchema
>;
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
        .map((violation) => `${violation.reason_code} at ${violation.path}: ${violation.detail}`)
        .join('; ')}`,
    );
    this.name = 'RbContactEvasionContractError';
    this.reasonCodes = report.reason_codes;
    this.violations = report.violations;
  }
}

/** Compare clocks as instants, so a re-formatted timestamp is not an escape hatch. */
function instant(value: string): number {
  return Date.parse(value);
}

function sameInstant(left: string, right: string | null): boolean {
  return right !== null && instant(left) === instant(right);
}

function isKnownMetricId(metricId: string): boolean {
  return Object.prototype.hasOwnProperty.call(RB_CONTACT_EVASION_METRIC_REGISTRY, metricId);
}

function checkIdentity(
  observation: RbContactEvasionObservation,
  path: string,
  push: (violation: RbContactEvasionViolation) => void,
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

function checkMetricBinding(
  observation: RbContactEvasionObservation,
  path: string,
  push: (violation: RbContactEvasionViolation) => void,
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
    referenced.push({
      metricId: inputMetricId,
      where: `${path}.transform.input_metric_ids`,
    });
  }
  for (const { metricId, where } of referenced) {
    if (!isKnownMetricId(metricId)) {
      push({
        reason_code: 'UNKNOWN_METRIC_ID',
        path: where,
        detail: `metric id "${metricId}" is not in the closed rb_contact_evasion metric registry; admitting a metric is a contract change`,
      });
    }
  }

  if (!isKnownMetricId(metric.metric_id)) {
    return;
  }
  const allowedMechanisms = RB_CONTACT_EVASION_METRIC_REGISTRY[metric.metric_id];
  if (!allowedMechanisms.includes(observation.mechanism_id)) {
    push({
      reason_code: 'MECHANISM_METRIC_BINDING_VIOLATION',
      path: `${path}.mechanism_id`,
      detail:
        allowedMechanisms.length === 0
          ? `metric "${metric.metric_id}" may never stand as mechanism evidence (it is a component, denominator, or known-inadmissible summary), but it is declared under mechanism "${observation.mechanism_id}"`
          : `metric "${metric.metric_id}" may only evidence [${allowedMechanisms.join(', ')}], but it is declared under mechanism "${observation.mechanism_id}"; evidence for one mechanism never satisfies another`,
    });
  }
}

function checkMeasurement(
  observation: RbContactEvasionObservation,
  path: string,
  push: (violation: RbContactEvasionViolation) => void,
): void {
  const { metric, measurement, cohort_scope: cohortScope } = observation;
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

  // status === 'observed'
  if (measurement.value === null || measurement.missingness_reason !== null) {
    push({
      reason_code: 'OBSERVED_COMPONENT_MISSING_VALUE',
      path: measurementPath,
      detail: `status "observed" requires a non-null value and a null missingness_reason (got value=${JSON.stringify(measurement.value)}, missingness_reason=${JSON.stringify(measurement.missingness_reason)})`,
    });
  }

  if (metric.value_kind === 'rate') {
    if (measurement.denominator === null || measurement.numerator === null) {
      push({
        reason_code: 'RATE_MISSING_DENOMINATOR',
        path: measurementPath,
        detail: `value_kind "rate" requires exact numerator and denominator metric ids and values (numerator=${JSON.stringify(measurement.numerator)}, denominator=${JSON.stringify(measurement.denominator)}); a rate without an exact denominator is not comparable to any other source's similarly named rate`,
      });
    }
    // A row declares its own metric minimum, so on its own that bar can be set
    // arbitrarily low. When the row also states a cohort, the stricter of the two
    // minimums governs, so a row cannot buy eligibility by lowering its own bar.
    const effectiveMinimum = Math.max(
      metric.minimum_eligible_opportunities,
      cohortScope?.minimum_eligible_opportunities ?? 0,
    );
    if (
      measurement.eligible_opportunities !== null &&
      measurement.eligible_opportunities < effectiveMinimum
    ) {
      push({
        reason_code: 'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
        path: measurementPath,
        detail: `eligible_opportunities ${measurement.eligible_opportunities} is below the effective minimum ${effectiveMinimum} (metric minimum ${metric.minimum_eligible_opportunities}, cohort minimum ${cohortScope?.minimum_eligible_opportunities ?? 'none'}); a below-minimum sample must be emitted as status "missing" with missingness_reason "below_minimum_sample" and no value`,
      });
    }
  }
}

function checkDenominatorSemantics(
  observation: RbContactEvasionObservation,
  path: string,
  push: (violation: RbContactEvasionViolation) => void,
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

function checkClocks(
  observation: RbContactEvasionObservation,
  envelopeGeneratedAt: string,
  path: string,
  push: (violation: RbContactEvasionViolation) => void,
): void {
  const clocks = observation.clocks;
  const clocksPath = `${path}.clocks`;

  if (
    sameInstant(clocks.retrieved_at, clocks.source_generated_at) ||
    sameInstant(clocks.retrieved_at, clocks.source_observed_at) ||
    sameInstant(clocks.retrieved_at, clocks.window_end)
  ) {
    push({
      reason_code: 'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
      path: clocksPath,
      detail: `retrieved_at (${clocks.retrieved_at}) coincides exactly with a football-window or source-generation clock (window_end=${clocks.window_end}, source_generated_at=${clocks.source_generated_at}, source_observed_at=${JSON.stringify(clocks.source_observed_at)}); retrieval time never substitutes for either`,
    });
  }

  const ordered: Array<[string, string, string, string]> = [
    ['window_start', clocks.window_start, 'window_end', clocks.window_end],
    [
      'source_generated_at',
      clocks.source_generated_at,
      'source_available_at',
      clocks.source_available_at,
    ],
    [
      'source_available_at',
      clocks.source_available_at,
      'retrieved_at',
      clocks.retrieved_at,
    ],
    [
      'retrieved_at',
      clocks.retrieved_at,
      'artifact_generated_at',
      clocks.artifact_generated_at,
    ],
  ];
  for (const [earlierName, earlier, laterName, later] of ordered) {
    if (instant(earlier) > instant(later)) {
      push({
        reason_code: 'CLOCK_ORDER_INVALID',
        path: clocksPath,
        detail: `${earlierName} (${earlier}) must not be after ${laterName} (${later})`,
      });
    }
  }

  if (clocks.source_observed_at !== null) {
    if (instant(clocks.source_observed_at) > instant(clocks.source_generated_at)) {
      push({
        reason_code: 'CLOCK_ORDER_INVALID',
        path: clocksPath,
        detail: `source_observed_at (${clocks.source_observed_at}) must not be after source_generated_at (${clocks.source_generated_at})`,
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
  push: (violation: RbContactEvasionViolation) => void,
): void {
  const { source, evidence_class: evidenceClass, measurement, transform } = observation;
  const sourcePath = `${path}.source`;

  if (RB_CONTACT_EVASION_RESTRICTED_ACCESS_CLASSES.has(source.access_class)) {
    if (source.promotable) {
      push({
        reason_code: 'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
        path: `${sourcePath}.promotable`,
        detail: `source access_class "${source.access_class}" cannot be marked promotable`,
      });
    }
    if (measurement.status === 'observed' && evidenceClass !== 'external_opinion') {
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
  push: (violation: RbContactEvasionViolation) => void,
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
  push: (violation: RbContactEvasionViolation) => void,
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

function checkDefinitionDrift(
  observations: RbContactEvasionObservation[],
  push: (violation: RbContactEvasionViolation) => void,
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
 * run (they cannot be evaluated on unshaped input) and the report says so via
 * `shape_valid: false` — so a caller can always distinguish "rejected by a
 * contract rule" from "did not parse".
 */
export function evaluateRbContactEvasionObservationsV0(
  input: unknown,
): RbContactEvasionValidationReport {
  const violations: RbContactEvasionViolation[] = [];
  const push = (violation: RbContactEvasionViolation): void => {
    violations.push(violation);
  };

  const parsed = rbContactEvasionObservationsV0Schema.safeParse(input);
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      const path = issue.path.length > 0 ? issue.path.join('.') : '<root>';
      push({
        reason_code:
          issue.code === z.ZodIssueCode.unrecognized_keys
            ? 'UNKNOWN_FIELD_PRESENT'
            : 'SCHEMA_SHAPE_INVALID',
        path,
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
    checkMetricBinding(observation, path, push);
    checkMeasurement(observation, path, push);
    checkDenominatorSemantics(observation, path, push);
    checkClocks(observation, artifact.generated_at, path, push);
    checkSourceAndEvidence(observation, artifact.artifact_position, path, push);
    checkCohortScope(observation, path, push);
    checkTransform(observation, path, push);
  });

  checkDefinitionDrift(artifact.observations, push);

  return buildReport(true, violations);
}

function buildReport(
  shapeValid: boolean,
  violations: RbContactEvasionViolation[],
): RbContactEvasionValidationReport {
  const reasonCodes = [...new Set(violations.map((violation) => violation.reason_code))].sort();
  return {
    valid: violations.length === 0,
    shape_valid: shapeValid,
    violations,
    reason_codes: reasonCodes,
  };
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
 * shape a later claim assessment reads; it is not itself an assessment.
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
