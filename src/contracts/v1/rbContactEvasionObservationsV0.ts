import { z } from 'zod';

/**
 * `rb_contact_evasion_observations_v0` — source-observation contract for the RB
 * contact-evasion mechanism lane (TIBER-Data #234, Slice A).
 *
 * This module is a **contract and validation surface only**. It does not build,
 * ingest, promote, normalize, rank, or score anything.
 *
 * Design rule, held across every dimension after two exact-head reviews:
 * **semantic authority lives in this file, not in the payload.** The code-owned
 * metric dictionary fixes what each metric identity means — its mechanism,
 * admissible opportunity classes, value kind, unit, directionality, numeric
 * domain, canonical inclusion rules, required caveats, and rate composition.
 * The code-owned minimum-sample rule fixes the governing sample bar. Clock
 * origins, acquisition modes, and rights dispositions are closed vocabularies
 * whose combinations are cross-checked. A row restates some of these facts for
 * inspectability and is rejected, with a stable machine-readable reason code,
 * wherever it disagrees. The full dimension-by-dimension matrix is documented
 * in `docs/contracts/rb-contact-evasion-observations-v0.md`.
 *
 * Deliberate absences: there is no score, composite, grade, ranking,
 * percentile, tier, rating, neutral default, or "elite" judgment anywhere in
 * this contract. A mechanism with no admitted evidence stays missing; it is
 * never filled from another.
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
 * How the material was actually obtained. Closed, so the automation-permission
 * cross-check binds to a machine-readable mode rather than to prose. Free-text
 * context moves to `acquisition_notes`.
 */
export const rbContactEvasionAcquisitionMethodSchema = z.enum([
  'automated_ingestion',
  'manual_citation',
  'synthetic_fixture',
  'not_acquired',
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

/**
 * The code-owned composition of each cross-class denominator. A combined
 * disclosure restates these components for inspectability; it cannot invent
 * them. Presence of a disclosure was checkable before this map existed —
 * its truth was not.
 */
export const RB_CONTACT_EVASION_COMBINED_DENOMINATOR_COMPONENTS: Readonly<
  Record<string, { rushing_component_metric_id: string; receiving_component_metric_id: string }>
> = {
  touch: {
    rushing_component_metric_id: 'rush_attempts',
    receiving_component_metric_id: 'receptions',
  },
};

/**
 * Which evidence classes each material kind may carry. Rows may label
 * conservatively (measured material cited as an opinion) but never the
 * reverse: a derived publication's figures are the source's derivations and
 * cannot be presented as a direct observation, and editorial opinion is only
 * ever an external opinion.
 */
export const RB_CONTACT_EVASION_MATERIAL_EVIDENCE_CLASSES: Readonly<
  Record<RbContactEvasionSourceMaterialKind, readonly RbContactEvasionEvidenceClass[]>
> = {
  measured_observation: ['direct', 'normalized', 'derived', 'external_opinion'],
  derived_publication: ['normalized', 'derived', 'external_opinion'],
  editorial_opinion: ['external_opinion'],
};

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
 * Which clock a timestamp actually came from. Declared origin — not timestamp
 * arithmetic — is what rejects substitution: an equality heuristic was unsound
 * in both directions (it rejected a legitimate coincidence and an invented
 * one-millisecond offset walked past it).
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

/**
 * Closed caveat identities. #234's mechanism table attaches a required warning
 * to specific observable families; a free-text `warnings` array cannot carry a
 * machine-checkable obligation, so the obligation binds to these ids instead.
 * Free-text `warnings` remain as supplementary display context.
 */
export const rbContactEvasionCaveatIdSchema = z.enum([
  'synthetic_fixture_value',
  'historical_testing_not_current_form',
  'explosive_outcome_not_speed_or_agility',
  'yac_context_and_definition_dependent',
  'forced_missed_tackle_definitions_differ_by_source',
  'cross_window_not_comparable',
  'combined_touch_denominator_disclosed',
  'snapshot_superseded',
]);

/** Content digests are closed to an admitted algorithm and format. */
export const RB_CONTACT_EVASION_DIGEST_ALGORITHMS: ReadonlySet<string> = new Set(['sha256']);
export const RB_CONTACT_EVASION_SHA256_HEX_PATTERN = /^[0-9a-f]{64}$/;

// ---------------------------------------------------------------------------
// Code-owned metric dictionary
// ---------------------------------------------------------------------------

/**
 * What a metric identity *means*, owned entirely by this contract.
 *
 * Two review rounds established the shape of this ownership: binding only
 * `metric -> mechanisms` (round one) and then only the fields the first review
 * named (round two) each left the payload free to redefine an adjacent
 * dimension. The descriptor therefore now pins EVERY semantic dimension a row
 * could otherwise author:
 *
 * - `mechanisms`: which mechanisms the metric may ever evidence. An **empty**
 *   list means it may never stand as mechanism evidence at all — a component,
 *   a denominator, or a known-inadmissible summary (a lone long gain, yards
 *   per carry, a raw touch count).
 * - `allowed_opportunity_classes`: the classes of opportunity the metric can
 *   describe. A 40-yard dash cannot be relabeled a rushing observation.
 * - `value_kind`, `unit`, `directionality`: restated by rows, never redefined.
 * - `canonical_inclusion_rules`: the canonical definition, verbatim. A row
 *   restates it for inspectability; rewriting "10 or more yards" to "5 or
 *   more yards" under the same metric id is a rejection, not a variant.
 *   Source-native wording stays inspectable in `source_native_metric_name` /
 *   `definition_ref` / `definition_version` and is drift-checked, but it never
 *   redefines the canonical metric.
 * - `required_caveat_ids`: caveats the metric must always carry (#234's
 *   per-mechanism required warnings, as machine-checkable identities).
 * - `numeric_domain` / `integer_valued`: the admissible numeric range and
 *   integrality for values of this metric, applied to emitted values and to
 *   numerator/denominator components under each component's own descriptor.
 * - `numerator_metric_id` / `denominator_metric_id` /
 *   `denominator_opportunity_type`: the exact composition of a rate. Non-rate
 *   metrics declare all three null and may not carry rate components.
 *
 * Admitting or changing a metric is a contract change, not a data decision.
 */
export interface RbContactEvasionMetricDescriptor {
  readonly mechanisms: readonly RbContactEvasionMechanismId[];
  readonly allowed_opportunity_classes: readonly RbContactEvasionOpportunityClass[];
  readonly value_kind: RbContactEvasionValueKind;
  readonly unit: string;
  readonly directionality: RbContactEvasionDirectionality;
  readonly canonical_inclusion_rules: readonly string[];
  readonly required_caveat_ids: readonly RbContactEvasionCaveatId[];
  readonly numeric_domain: 'non_negative' | 'positive';
  readonly integer_valued: boolean;
  readonly numerator_metric_id: string | null;
  readonly denominator_metric_id: string | null;
  readonly denominator_opportunity_type: RbContactEvasionOpportunityType | null;
}

interface CountDescriptorOptions {
  mechanisms?: readonly RbContactEvasionMechanismId[];
  classes: readonly RbContactEvasionOpportunityClass[];
  unit: string;
  rules: readonly string[];
  caveats?: readonly RbContactEvasionCaveatId[];
  integer?: boolean;
}

const countDescriptor = (options: CountDescriptorOptions): RbContactEvasionMetricDescriptor => ({
  mechanisms: options.mechanisms ?? [],
  allowed_opportunity_classes: options.classes,
  value_kind: 'count',
  unit: options.unit,
  directionality: 'higher_is_more_of_mechanism',
  canonical_inclusion_rules: options.rules,
  required_caveat_ids: options.caveats ?? [],
  numeric_domain: 'non_negative',
  integer_valued: options.integer ?? true,
  numerator_metric_id: null,
  denominator_metric_id: null,
  denominator_opportunity_type: null,
});

interface RateDescriptorOptions {
  mechanisms: readonly RbContactEvasionMechanismId[];
  classes: readonly RbContactEvasionOpportunityClass[];
  unit: string;
  rules: readonly string[];
  caveats?: readonly RbContactEvasionCaveatId[];
  numerator: string;
  denominator: string;
  opportunity: RbContactEvasionOpportunityType;
}

const rateDescriptor = (options: RateDescriptorOptions): RbContactEvasionMetricDescriptor => ({
  mechanisms: options.mechanisms,
  allowed_opportunity_classes: options.classes,
  value_kind: 'rate',
  unit: options.unit,
  directionality: 'higher_is_more_of_mechanism',
  canonical_inclusion_rules: options.rules,
  required_caveat_ids: options.caveats ?? [],
  numeric_domain: 'non_negative',
  integer_valued: false,
  numerator_metric_id: options.numerator,
  denominator_metric_id: options.denominator,
  denominator_opportunity_type: options.opportunity,
});

const testingDescriptor = (
  mechanisms: readonly RbContactEvasionMechanismId[],
  rules: readonly string[],
): RbContactEvasionMetricDescriptor => ({
  mechanisms,
  allowed_opportunity_classes: ['athletic_testing'],
  value_kind: 'duration_seconds',
  unit: 'seconds',
  directionality: 'lower_is_more_of_mechanism',
  canonical_inclusion_rules: rules,
  required_caveat_ids: ['historical_testing_not_current_form'],
  numeric_domain: 'positive',
  integer_valued: false,
  numerator_metric_id: null,
  denominator_metric_id: null,
  denominator_opportunity_type: null,
});

const FMT_CAVEATS = ['forced_missed_tackle_definitions_differ_by_source'] as const;
const YAC_CAVEATS = ['yac_context_and_definition_dependent'] as const;
const EXPLOSIVE_CAVEATS = ['explosive_outcome_not_speed_or_agility'] as const;
const EXPLOSIVE_10_RULE =
  'an explosive rush is a rush gaining 10 or more yards from scrimmage';
const EXPLOSIVE_15_RULE =
  'an explosive rush is a rush gaining 15 or more yards from scrimmage';
const YAC_RULE = 'yards measured from the first point of defensive contact';

export const RB_CONTACT_EVASION_METRIC_DICTIONARY: Readonly<
  Record<string, RbContactEvasionMetricDescriptor>
> = {
  // --- contact_avoidance ---
  forced_missed_tackles_count: countDescriptor({
    mechanisms: ['contact_avoidance'],
    classes: ['rushing'],
    unit: 'forced_missed_tackles',
    rules: ['rushing attempts only'],
    caveats: FMT_CAVEATS,
  }),
  forced_missed_tackles_per_rush_attempt: rateDescriptor({
    mechanisms: ['contact_avoidance'],
    classes: ['rushing'],
    unit: 'forced_missed_tackles_per_rush_attempt',
    rules: ['rushing attempts only; kneel-downs and aborted plays excluded'],
    caveats: FMT_CAVEATS,
    numerator: 'forced_missed_tackles_count',
    denominator: 'rush_attempts',
    opportunity: 'rush_attempt',
  }),
  forced_missed_tackles_per_touch: rateDescriptor({
    mechanisms: ['contact_avoidance'],
    classes: ['combined_rushing_receiving'],
    unit: 'forced_missed_tackles_per_touch',
    rules: ['rushing attempts and receptions'],
    caveats: FMT_CAVEATS,
    numerator: 'forced_missed_tackles_count',
    denominator: 'touches',
    opportunity: 'touch',
  }),
  // --- contact_survival ---
  yards_after_contact_total: countDescriptor({
    mechanisms: ['contact_survival'],
    classes: ['rushing'],
    unit: 'yards',
    rules: [YAC_RULE],
    caveats: YAC_CAVEATS,
    integer: false,
  }),
  yards_after_contact_per_rush_attempt: rateDescriptor({
    mechanisms: ['contact_survival'],
    classes: ['rushing'],
    unit: 'yards_per_rush_attempt',
    rules: ['rushing attempts only', YAC_RULE],
    caveats: YAC_CAVEATS,
    numerator: 'yards_after_contact_total',
    denominator: 'rush_attempts',
    opportunity: 'rush_attempt',
  }),
  yards_after_contact_per_contact: rateDescriptor({
    mechanisms: ['contact_survival'],
    classes: ['rushing'],
    unit: 'yards_per_contact',
    rules: ['contact events only', YAC_RULE],
    caveats: YAC_CAVEATS,
    numerator: 'yards_after_contact_total',
    denominator: 'contact_events',
    opportunity: 'contact_event',
  }),
  // --- explosiveness ---
  explosive_rushes_10_plus_count: countDescriptor({
    mechanisms: ['explosiveness'],
    classes: ['rushing'],
    unit: 'explosive_rushes',
    rules: [EXPLOSIVE_10_RULE],
    caveats: EXPLOSIVE_CAVEATS,
  }),
  explosive_rushes_10_plus_per_rush_attempt: rateDescriptor({
    mechanisms: ['explosiveness'],
    classes: ['rushing'],
    unit: 'explosive_rushes_per_rush_attempt',
    rules: ['rushing attempts only', EXPLOSIVE_10_RULE],
    caveats: EXPLOSIVE_CAVEATS,
    numerator: 'explosive_rushes_10_plus_count',
    denominator: 'rush_attempts',
    opportunity: 'rush_attempt',
  }),
  explosive_rushes_15_plus_count: countDescriptor({
    mechanisms: ['explosiveness'],
    classes: ['rushing'],
    unit: 'explosive_rushes',
    rules: [EXPLOSIVE_15_RULE],
    caveats: EXPLOSIVE_CAVEATS,
  }),
  explosive_rushes_15_plus_per_rush_attempt: rateDescriptor({
    mechanisms: ['explosiveness'],
    classes: ['rushing'],
    unit: 'explosive_rushes_per_rush_attempt',
    rules: ['rushing attempts only', EXPLOSIVE_15_RULE],
    caveats: EXPLOSIVE_CAVEATS,
    numerator: 'explosive_rushes_15_plus_count',
    denominator: 'rush_attempts',
    opportunity: 'rush_attempt',
  }),
  // --- speed ---
  verified_max_game_speed_mph: {
    mechanisms: ['speed'],
    allowed_opportunity_classes: ['rushing', 'receiving', 'combined_rushing_receiving'],
    value_kind: 'speed_mph',
    unit: 'miles_per_hour',
    directionality: 'higher_is_more_of_mechanism',
    canonical_inclusion_rules: ['regular-season offensive snaps only'],
    required_caveat_ids: [],
    numeric_domain: 'positive',
    integer_valued: false,
    numerator_metric_id: null,
    denominator_metric_id: null,
    denominator_opportunity_type: null,
  },
  forty_yard_dash_seconds: testingDescriptor(['speed'], ['single pre-draft testing trial']),
  // --- agility / change of direction ---
  three_cone_drill_seconds: testingDescriptor(
    ['agility_change_of_direction'],
    ['single pre-draft testing trial'],
  ),
  short_shuttle_seconds: testingDescriptor(
    ['agility_change_of_direction'],
    ['single pre-draft testing trial'],
  ),
  tracking_change_of_direction_events_count: countDescriptor({
    mechanisms: ['agility_change_of_direction'],
    classes: ['rushing'],
    unit: 'change_of_direction_events',
    rules: ['tracked change-of-direction events on rushing attempts'],
  }),
  tracking_change_of_direction_events_per_rush_attempt: rateDescriptor({
    mechanisms: ['agility_change_of_direction'],
    classes: ['rushing'],
    unit: 'change_of_direction_events_per_rush_attempt',
    rules: ['rushing attempts only'],
    numerator: 'tracking_change_of_direction_events_count',
    denominator: 'rush_attempts',
    opportunity: 'rush_attempt',
  }),
  // --- components, denominators, and inadmissible summaries ---
  rush_attempts: countDescriptor({
    classes: ['rushing'],
    unit: 'rush_attempts',
    rules: ['rushing attempts only'],
  }),
  receptions: countDescriptor({
    classes: ['receiving'],
    unit: 'receptions',
    rules: ['completed receptions only'],
  }),
  targets: countDescriptor({
    classes: ['receiving'],
    unit: 'targets',
    rules: ['pass targets only'],
  }),
  touches: countDescriptor({
    classes: ['combined_rushing_receiving'],
    unit: 'touches',
    rules: ['rushing attempts and receptions'],
  }),
  contact_events: countDescriptor({
    classes: ['rushing', 'receiving', 'combined_rushing_receiving'],
    unit: 'contact_events',
    rules: ['defensive contact events only'],
  }),
  testing_trials: countDescriptor({
    classes: ['athletic_testing'],
    unit: 'testing_trials',
    rules: ['athletic testing trials only'],
  }),
  rush_yards_total: countDescriptor({
    classes: ['rushing'],
    unit: 'yards',
    rules: ['rushing attempts only'],
    integer: false,
  }),
  longest_rush_yards: countDescriptor({
    classes: ['rushing'],
    unit: 'yards',
    rules: ['rushing attempts only'],
    integer: false,
  }),
  yards_per_carry: rateDescriptor({
    mechanisms: [],
    classes: ['rushing'],
    unit: 'yards_per_rush_attempt',
    rules: ['rushing attempts only'],
    numerator: 'rush_yards_total',
    denominator: 'rush_attempts',
    opportunity: 'rush_attempt',
  }),
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
 * and {@link evaluateRbContactEvasionObservationsV0} **fails closed** for any
 * observed rate in a `candidate` or `promoted` artifact: a real bar has to come
 * from an admitted rule bound in Slice B before a rate may sit in either position.
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
 * Closed, stable reason codes. Every fixture under
 * `test/fixtures/rb_contact_evasion/negative/` is rejected by exactly one of
 * these, so a rejection can be attributed to a rule rather than to "it failed
 * to parse".
 */
export const rbContactEvasionReasonCodeSchema = z.enum([
  'SCHEMA_SHAPE_INVALID',
  'UNKNOWN_FIELD_PRESENT',
  // metric identity and definition
  'UNKNOWN_METRIC_ID',
  'MECHANISM_METRIC_BINDING_VIOLATION',
  'METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE',
  'METRIC_DESCRIPTOR_CONTRADICTED',
  'CANONICAL_DEFINITION_CONTRADICTED',
  'METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID',
  'REQUIRED_CAVEAT_MISSING',
  'INAPPLICABLE_CAVEAT_DECLARED',
  // rate and measurement semantics
  'RATE_MISSING_DENOMINATOR',
  'RATE_COMPONENT_METRIC_MISMATCH',
  'RATE_DENOMINATOR_NOT_POSITIVE',
  'RATE_VALUE_INCONSISTENT_WITH_COMPONENTS',
  'RATE_COMPONENTS_ON_NON_RATE_METRIC',
  'ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH',
  'MEASUREMENT_NUMERIC_DOMAIN_VIOLATION',
  // denominators and opportunity classes
  'DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE',
  'DENOMINATOR_OPPORTUNITY_CLASS_MISMATCH',
  'RUSHING_RECEIVING_SILENTLY_COMBINED',
  'COMBINED_COMPONENT_DISCLOSURE_CONTRADICTED',
  // sample sufficiency
  'ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE',
  'MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED',
  'MINIMUM_SAMPLE_RULE_NOT_APPLICABLE',
  'BELOW_MINIMUM_SAMPLE_UNPROVABLE',
  'MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION',
  'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
  // source governance
  'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
  'EXTERNAL_OPINION_LABELED_AS_OBSERVATION',
  'MATERIAL_KIND_INCOMPATIBLE_WITH_EVIDENCE_CLASS',
  'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE',
  'STORED_EXACT_VALUE_REQUIRES_RETENTION',
  'ACQUISITION_MODE_PERMISSION_INCOMPATIBLE',
  'ACQUISITION_MODE_INCOHERENT',
  'ATTRIBUTION_METADATA_MISSING',
  'SNAPSHOT_WITHOUT_CONTENT_DIGEST',
  'CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION',
  'CONTENT_DIGEST_MALFORMED',
  'SUPERSESSION_SELF_REFERENCE',
  'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION',
  'PROMOTED_POSITION_REQUIRES_PROMOTION_GATE',
  // clocks
  'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
  'CLOCK_AVAILABILITY_CONTRADICTED',
  'CLOCK_ORDER_INVALID',
  'ARTIFACT_CLOCK_MISMATCH',
  // window scope
  'WINDOW_SCOPE_INCOHERENT',
  // cohort scope
  'WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED',
  'COHORT_SCOPE_MISMATCH',
  // identity, grain, measurement status
  'CANONICAL_IDENTITY_UNRESOLVED',
  'DUPLICATE_OBSERVATION_ID',
  'DUPLICATE_OBSERVATION_GRAIN',
  'MISSING_COMPONENT_CARRIES_VALUE',
  'MISSINGNESS_REASON_ABSENT',
  'MISSINGNESS_REASON_UNSUPPORTED',
  'MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE',
  'OBSERVED_COMPONENT_MISSING_VALUE',
  // transforms
  'INCOMPATIBLE_METRIC_TRANSFORM_INPUT',
  'INCOMPATIBILITY_REGISTRY_NOT_SYMMETRIC',
  'DERIVED_EVIDENCE_REQUIRES_TRANSFORM',
  'TRANSFORM_REQUIRES_DERIVED_EVIDENCE',
  'TRANSFORM_COMPOSITION_INCOMPLETE',
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
 * Per-row metric declaration. `value_kind`, `unit`, `directionality`, and
 * `inclusion_exclusion_rules` are restated here for inspectability but are
 * **not authoritative** — each must equal the code-owned descriptor.
 * `minimum_sample_rule_id` names the governing rule where sample governance
 * applies (rate metrics and below-minimum-sample claims); it is null on metrics
 * no rule governs, and a row can never state a threshold, only which rule
 * binds it. `source_native_metric_name`,
 * `definition_ref`, and `definition_version` are the source-native identity:
 * inspectable, drift-checked, and never a redefinition of the canonical metric.
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
    minimum_sample_rule_id: nonEmptyStringSchema.nullable(),
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
 * Honest limitation: these fields are **declared by the producer**. This
 * contract proves the declarations are internally consistent — rights follow
 * the action being taken (storing a value requires retention; automated
 * acquisition requires automation permission; a promotable claim requires
 * every disposition settled) — and fails closed on incompatible combinations.
 * It cannot prove a declaration matches reality. Pinning declarations to an
 * admitted source registry is Slice B work. `promotable: true` is a producer
 * claim requiring separate promotion review; it never authorizes promotion.
 */
export const rbContactEvasionSourceSchema = z
  .object({
    owner: nonEmptyStringSchema,
    product: nonEmptyStringSchema,
    snapshot_id: nonEmptyStringSchema,
    access_class: rbContactEvasionSourceAccessClassSchema,
    acquisition_method: rbContactEvasionAcquisitionMethodSchema,
    acquisition_notes: nonEmptyStringSchema.nullable(),
    material_kind: rbContactEvasionSourceMaterialKindSchema,
    supported_opportunity_types: z.array(rbContactEvasionOpportunityTypeSchema),
    rights_review_ref: nonEmptyStringSchema,
    permissions: rbContactEvasionSourcePermissionsSchema,
    attribution_text: nonEmptyStringSchema.nullable(),
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
    caveat_ids: z.array(rbContactEvasionCaveatIdSchema),
    warnings: z.array(nonEmptyStringSchema),
  })
  .strict();

export const RB_CONTACT_EVASION_ARTIFACT_ID = 'rb_contact_evasion_observations_v0';
export const RB_CONTACT_EVASION_SCHEMA_VERSION = 'rb_contact_evasion_observations_v0.4.0';

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
export type RbContactEvasionAcquisitionMethod = z.infer<
  typeof rbContactEvasionAcquisitionMethodSchema
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
export type RbContactEvasionCaveatId = z.infer<typeof rbContactEvasionCaveatIdSchema>;
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
 * The metric identity must mean what this contract says it means: dictionary
 * membership, descriptor agreement on every restated dimension (value kind,
 * unit, directionality, canonical inclusion rules), mechanism binding, and
 * opportunity-class admissibility.
 */
function checkMetricSemantics(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { metric, measurement, transform, scope } = observation;

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
    contradictions.push(`value_kind "${metric.value_kind}" != "${descriptor.value_kind}"`);
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

  // The canonical definition is code-owned verbatim. A row restates it for
  // inspectability; rewriting it under the same metric id is a redefinition.
  const canonical = descriptor.canonical_inclusion_rules;
  const restated = metric.inclusion_exclusion_rules;
  const rulesMatch =
    restated.length === canonical.length &&
    canonical.every((rule, index) => restated[index] === rule);
  if (!rulesMatch) {
    push({
      reason_code: 'CANONICAL_DEFINITION_CONTRADICTED',
      path: `${path}.metric.inclusion_exclusion_rules`,
      detail: `metric "${metric.metric_id}" restates inclusion/exclusion rules ${JSON.stringify(restated)} but the canonical definition is ${JSON.stringify(canonical)}; a different definition requires a different metric identity, and source-native wording belongs in source_native_metric_name / definition_ref`,
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

  if (!descriptor.allowed_opportunity_classes.includes(scope.opportunity_class)) {
    push({
      reason_code: 'METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE',
      path: `${path}.scope.opportunity_class`,
      detail: `metric "${metric.metric_id}" describes [${descriptor.allowed_opportunity_classes.join(', ')}] opportunity, but the row declares opportunity_class "${scope.opportunity_class}"; a testing measurement cannot be relabeled a game observation (nor the reverse)`,
    });
  }

  // Sample governance applies to rate metrics only. A non-rate metric naming
  // ANY rule — payload-invented or even the real code-owned one — claims a
  // governance that does not exist for it.
  if (descriptor.value_kind !== 'rate' && metric.minimum_sample_rule_id !== null) {
    push({
      reason_code: 'MINIMUM_SAMPLE_RULE_NOT_APPLICABLE',
      path: `${path}.metric.minimum_sample_rule_id`,
      detail: `metric "${metric.metric_id}" has value_kind "${descriptor.value_kind}", which no minimum-sample rule governs; minimum_sample_rule_id must be null, got "${metric.minimum_sample_rule_id}"`,
    });
  }
}

/** Required caveats are identities, not prose, so their presence is checkable. */
function checkCaveats(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const descriptor = getDescriptor(observation.metric.metric_id);
  const present = new Set(observation.caveat_ids);
  for (const required of descriptor?.required_caveat_ids ?? []) {
    if (!present.has(required)) {
      push({
        reason_code: 'REQUIRED_CAVEAT_MISSING',
        path: `${path}.caveat_ids`,
        detail: `metric "${observation.metric.metric_id}" requires caveat "${required}"; the caveat is part of the metric's meaning and cannot be dropped`,
      });
    }
  }
  // State-bound caveats are required exactly when their state holds and are
  // inadmissible otherwise — a caveat is a machine-readable claim, and a claim
  // whose state does not hold is a false declaration, not extra caution.
  const stateBound: Array<[RbContactEvasionCaveatId, boolean, string]> = [
    [
      'synthetic_fixture_value',
      observation.source.provenance_mode === 'fixture',
      'the row has fixture provenance (synthetic values always declare themselves)',
    ],
    [
      'combined_touch_denominator_disclosed',
      observation.metric.combined_component_disclosure !== null,
      'a combined-component disclosure is declared',
    ],
    [
      'snapshot_superseded',
      observation.source.superseded_by_snapshot_id !== null,
      'a superseding snapshot is declared',
    ],
  ];
  for (const [caveat, stateHolds, stateDescription] of stateBound) {
    if (stateHolds && !present.has(caveat)) {
      push({
        reason_code: 'REQUIRED_CAVEAT_MISSING',
        path: `${path}.caveat_ids`,
        detail: `caveat "${caveat}" is required because ${stateDescription}`,
      });
    }
    if (!stateHolds && present.has(caveat)) {
      push({
        reason_code: 'INAPPLICABLE_CAVEAT_DECLARED',
        path: `${path}.caveat_ids`,
        detail: `caveat "${caveat}" is declared but its state does not hold (it applies only when ${stateDescription}); a caveat is a checkable claim, not free prose`,
      });
    }
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
      return;
    }
    checkMissingnessShape(observation, path, push);
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

/**
 * Each missingness reason has one allowed measurement shape and, where the
 * reason makes a claim about the source, a source state that must support it.
 * A missing row is not a free-text apology: it is a checkable declaration.
 *
 * - `below_minimum_sample` is the one reason that MAY — and must — retain an
 *   eligible-opportunity count, because the claim is provable only against the
 *   code-owned rule and a real count. The claim must also be TRUE: an eligible
 *   count at or above the code-owned threshold disproves it. Only rate metrics
 *   have a sample gate to fall below.
 * - Every other reason must carry no eligible count. An exact count retained
 *   under `rights_blocked` or `source_unavailable` is a stored source fact
 *   with no measurement to justify it.
 * - `rights_blocked` must name an action that was actually blocked. A
 *   non-permitted retention disposition is independently sufficient (an
 *   obtained value cannot be kept). An access class supports the claim only
 *   when it is `licensed_or_gated` or `reference_only` AND the declared
 *   acquisition state proves acquisition did not occur (`not_acquired`): a
 *   successfully declared acquisition is never excused by its access label,
 *   `unavailable` has its own truthful reason (`source_unavailable`) and does
 *   not double as a rights cause, and `unknown` access proves nothing
 *   affirmative — rights uncertainty is represented by an unknown retention
 *   disposition. Redistribution/display and automation restrictions never
 *   support the claim.
 * - `source_unavailable` must be supported by access_class "unavailable".
 * - `not_measured` and `definition_incompatible` assert facts about what the
 *   source measures and how it defines it; no structural cross-check exists
 *   for them in Slice A (recorded as a residual risk).
 */
function checkMissingnessShape(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { measurement, source } = observation;
  const reason = measurement.missingness_reason;
  const measurementPath = `${path}.measurement`;
  const permissions = source.permissions;

  if (reason !== 'below_minimum_sample' && measurement.eligible_opportunities !== null) {
    push({
      reason_code: 'MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE',
      path: `${measurementPath}.eligible_opportunities`,
      detail: `missingness_reason "${reason}" admits no eligible-opportunity count, got ${measurement.eligible_opportunities}; only "below_minimum_sample" retains a count, because only that claim is proven by one`,
    });
  }

  if (reason === 'rights_blocked') {
    // Rights follow the action the claim is about, and acquisition_method
    // records what actually happened — so a declared successful acquisition is
    // never excused by its access label. Exactly two states support the claim:
    //
    // - a retention/reproduction disposition that is not "permitted",
    //   independently sufficient because an obtained value cannot be kept; or
    // - a rights-restricting access class ("licensed_or_gated" or
    //   "reference_only") TOGETHER WITH the one acquisition state that proves
    //   acquisition did not occur ("not_acquired").
    //
    // "unavailable" access has its own truthful reason, source_unavailable,
    // and does not double as a rights cause. "unknown" access proves nothing
    // affirmative — rights uncertainty is represented by an unknown retention
    // disposition, which the first path already honors. Automation
    // restrictions cannot support the claim (this vocabulary cannot declare
    // that acquisition depended on automation, and a declared automated
    // acquisition with automation prohibited is already incoherent), and
    // redistribution/display governs downstream use, never absence. Where the
    // fields cannot prove a blocked action, the claim fails closed.
    const accessSupportsRightsBlocked =
      source.acquisition_method === 'not_acquired' &&
      (source.access_class === 'licensed_or_gated' ||
        source.access_class === 'reference_only');
    const blockingState =
      permissions.retention_and_reproduction !== 'permitted' || accessSupportsRightsBlocked;
    if (!blockingState) {
      push({
        reason_code: 'MISSINGNESS_REASON_UNSUPPORTED',
        path: `${measurementPath}.missingness_reason`,
        detail: `missingness_reason "rights_blocked" is claimed with retention_and_reproduction "permitted" and acquisition_method "${source.acquisition_method}" against access_class "${source.access_class}"; a declared successful acquisition is never excused by its access label, "unavailable" belongs to source_unavailable, "unknown" access proves nothing affirmative, and redistribution/automation restrictions do not explain a missing measurement`,
      });
    }
  }

  if (reason === 'source_unavailable' && source.access_class !== 'unavailable') {
    push({
      reason_code: 'MISSINGNESS_REASON_UNSUPPORTED',
      path: `${measurementPath}.missingness_reason`,
      detail: `missingness_reason "source_unavailable" requires access_class "unavailable", got "${source.access_class}"; an unavailable source declares itself unavailable`,
    });
  }
}

/**
 * Numeric domains are per-metric, code-owned, and apply to the emitted value
 * and to each component under that component's own descriptor: finiteness,
 * the declared range, and integrality for discrete event counts.
 */
function checkNumericDomains(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { metric, measurement } = observation;
  if (measurement.status !== 'observed') {
    return;
  }

  const checkNumber = (
    value: number,
    metricId: string,
    where: string,
    role: string,
  ): void => {
    const descriptor = getDescriptor(metricId);
    if (descriptor === undefined) {
      return; // UNKNOWN_METRIC_ID already reported
    }
    const problems: string[] = [];
    if (!Number.isFinite(value)) {
      problems.push('must be finite');
    } else {
      if (descriptor.numeric_domain === 'non_negative' && value < 0) {
        problems.push('must be >= 0');
      }
      if (descriptor.numeric_domain === 'positive' && value <= 0) {
        problems.push('must be > 0');
      }
      if (descriptor.integer_valued && !Number.isInteger(value)) {
        problems.push('must be an integer (discrete event count)');
      }
    }
    if (problems.length > 0) {
      push({
        reason_code: 'MEASUREMENT_NUMERIC_DOMAIN_VIOLATION',
        path: where,
        detail: `${role} ${value} violates the code-owned numeric domain of metric "${metricId}" (${problems.join('; ')})`,
      });
    }
  };

  if (measurement.value !== null) {
    checkNumber(measurement.value, metric.metric_id, `${path}.measurement.value`, 'value');
  }
  if (measurement.numerator !== null) {
    checkNumber(
      measurement.numerator.value,
      measurement.numerator.metric_id,
      `${path}.measurement.numerator.value`,
      'numerator value',
    );
  }
  if (measurement.denominator !== null) {
    checkNumber(
      measurement.denominator.value,
      measurement.denominator.metric_id,
      `${path}.measurement.denominator.value`,
      'denominator value',
    );
  }
}

/**
 * Rate arithmetic and component identity, and the descriptor-declared null
 * component shape for every non-rate value kind. The components define the
 * rate; the emitted number never gets to disagree with them, and the sample
 * gate can never be cleared by an eligible-opportunity count unrelated to the
 * denominator it rates over.
 */
function checkRateSemantics(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { metric, measurement } = observation;
  const descriptor = getDescriptor(metric.metric_id);
  if (descriptor === undefined || measurement.status !== 'observed') {
    return;
  }
  const measurementPath = `${path}.measurement`;
  const { numerator, denominator, value } = measurement;

  if (descriptor.value_kind !== 'rate') {
    if (numerator !== null || denominator !== null) {
      push({
        reason_code: 'RATE_COMPONENTS_ON_NON_RATE_METRIC',
        path: measurementPath,
        detail: `metric "${metric.metric_id}" has value_kind "${descriptor.value_kind}" and declares no rate composition; numerator and denominator must be null (got numerator=${JSON.stringify(numerator?.metric_id ?? null)}, denominator=${JSON.stringify(denominator?.metric_id ?? null)})`,
      });
    }
    return;
  }

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

  // The eligible-opportunity count IS the denominator under this contract's
  // code-owned rule: a rate cannot clear a sample gate with a count unrelated
  // to the opportunities it actually rates over.
  if (
    measurement.eligible_opportunities !== null &&
    measurement.eligible_opportunities !== denominator.value
  ) {
    push({
      reason_code: 'ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH',
      path: `${measurementPath}.eligible_opportunities`,
      detail: `eligible_opportunities ${measurement.eligible_opportunities} must equal the rate denominator ${denominator.value}; the denominator is the eligible-opportunity count, and a divergent count would let a thin rate clear the sample gate`,
    });
  }

  if (value !== null && Number.isFinite(value)) {
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
  if (descriptor === undefined) {
    return;
  }
  const belowMinimumClaim =
    measurement.status === 'missing' &&
    measurement.missingness_reason === 'below_minimum_sample';
  const observedRate = descriptor.value_kind === 'rate' && measurement.status === 'observed';
  if (!belowMinimumClaim && !observedRate) {
    return;
  }
  const measurementPath = `${path}.measurement`;

  // Only rate metrics have a sample gate to fall below.
  if (belowMinimumClaim && descriptor.value_kind !== 'rate') {
    push({
      reason_code: 'BELOW_MINIMUM_SAMPLE_UNPROVABLE',
      path: `${measurementPath}.missingness_reason`,
      detail: `missingness_reason "below_minimum_sample" is claimed on metric "${metric.metric_id}" with value_kind "${descriptor.value_kind}", which no minimum-sample rule governs; there is no gate to fall below`,
    });
    return;
  }

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
      detail: `the only minimum-sample rule bound in this contract has authority "${RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.authority}" and cannot govern ${belowMinimumClaim ? 'a below-minimum-sample claim' : 'an observed rate'} at artifact_position "${artifactPosition}"; an admitted rule must be bound before either may sit in a candidate or promoted artifact`,
    });
    return;
  }

  const threshold =
    RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.thresholds_by_window_completeness[
      scope.window_completeness
    ];

  if (belowMinimumClaim) {
    // The claim is provable, and must be proven: an eligible count below the
    // code-owned bar. No count means nothing to prove it; a count at or above
    // the bar disproves it.
    if (measurement.eligible_opportunities === null) {
      push({
        reason_code: 'BELOW_MINIMUM_SAMPLE_UNPROVABLE',
        path: `${measurementPath}.eligible_opportunities`,
        detail: `missingness_reason "below_minimum_sample" requires the eligible-opportunity count that proves it against the code-owned minimum ${threshold} for window_completeness "${scope.window_completeness}"; with no count the claim is unprovable`,
      });
      return;
    }
    if (measurement.eligible_opportunities >= threshold) {
      push({
        reason_code: 'BELOW_MINIMUM_SAMPLE_UNPROVABLE',
        path: `${measurementPath}.eligible_opportunities`,
        detail: `missingness_reason "below_minimum_sample" is disproven: eligible_opportunities ${measurement.eligible_opportunities} meets the code-owned minimum ${threshold} for window_completeness "${scope.window_completeness}"`,
      });
    }
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

  if (measurement.eligible_opportunities < threshold) {
    push({
      reason_code: 'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
      path: measurementPath,
      detail: `eligible_opportunities ${measurement.eligible_opportunities} is below the code-owned minimum ${threshold} for window_completeness "${scope.window_completeness}"; a below-minimum sample must be emitted as status "missing" with missingness_reason "below_minimum_sample" and no value`,
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

  // A disclosure is a checkable statement, not a presence token: its structured
  // component ids must equal the code-owned composition of the combined
  // denominator, and it may only exist where a combination exists.
  if (metric.combined_component_disclosure !== null) {
    const disclosure = metric.combined_component_disclosure;
    const disclosurePath = `${path}.metric.combined_component_disclosure`;
    if (opportunityClass !== 'combined_rushing_receiving') {
      push({
        reason_code: 'COMBINED_COMPONENT_DISCLOSURE_CONTRADICTED',
        path: disclosurePath,
        detail: `a combined-component disclosure is declared under opportunity_class "${opportunityClass}", where no combination exists to disclose`,
      });
    } else {
      const canonical = RB_CONTACT_EVASION_COMBINED_DENOMINATOR_COMPONENTS.touch;
      const mismatches: string[] = [];
      if (disclosure.rushing_component_metric_id !== canonical.rushing_component_metric_id) {
        mismatches.push(
          `rushing component "${disclosure.rushing_component_metric_id}" != code-owned "${canonical.rushing_component_metric_id}"`,
        );
      }
      if (disclosure.receiving_component_metric_id !== canonical.receiving_component_metric_id) {
        mismatches.push(
          `receiving component "${disclosure.receiving_component_metric_id}" != code-owned "${canonical.receiving_component_metric_id}"`,
        );
      }
      if (mismatches.length > 0) {
        push({
          reason_code: 'COMBINED_COMPONENT_DISCLOSURE_CONTRADICTED',
          path: disclosurePath,
          detail: `the disclosure's structured components contradict the code-owned composition of the touch denominator (${mismatches.join('; ')}); a disclosure restates the combination, it does not invent one`,
        });
      }
    }
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
 * Window-scope coherence: the declared football window, week, game count, and
 * opportunity class must describe one internally consistent thing. Athletic
 * testing is the one admitted non-game event shape.
 */
function checkWindowScope(
  observation: RbContactEvasionObservation,
  path: string,
  push: Push,
): void {
  const { scope, measurement } = observation;
  const scopePath = `${path}.scope`;
  const issues: string[] = [];

  if (scope.opportunity_class === 'athletic_testing') {
    if (scope.window_completeness !== 'single_week') {
      issues.push(
        `athletic_testing is a dated non-game event and requires window_completeness "single_week", got "${scope.window_completeness}"`,
      );
    }
    if (scope.week !== null) {
      issues.push(`athletic_testing has no football week, got week=${scope.week}`);
    }
    if (scope.games_included !== 0) {
      issues.push(
        `athletic_testing includes no games, got games_included=${scope.games_included}`,
      );
    }
  } else {
    if (scope.window_completeness === 'single_week' && scope.week === null) {
      issues.push('a single-week game window must name its week');
    }
    if (scope.window_completeness !== 'single_week' && scope.week !== null) {
      issues.push(
        `window_completeness "${scope.window_completeness}" spans multiple weeks and cannot carry a single week (got week=${scope.week}); a weekly observation is a separate row`,
      );
    }
    if (measurement.status === 'observed') {
      if (scope.window_completeness === 'single_week' && scope.games_included !== 1) {
        issues.push(
          `an observed single-week game window includes exactly 1 game, got ${scope.games_included}`,
        );
      }
      if (scope.window_completeness === 'multi_week' && scope.games_included < 2) {
        issues.push(
          `an observed multi-week window includes at least 2 games, got ${scope.games_included}`,
        );
      }
      if (
        (scope.window_completeness === 'partial_season' ||
          scope.window_completeness === 'full_season') &&
        scope.games_included < 1
      ) {
        issues.push(
          `an observed ${scope.window_completeness} window cannot claim zero games; only athletic_testing is an admitted non-game event`,
        );
      }
    }
  }

  for (const issue of issues) {
    push({ reason_code: 'WINDOW_SCOPE_INCOHERENT', path: scopePath, detail: issue });
  }
}

/**
 * Clock availability, origin, and total ordering.
 *
 * Substitution is rejected by the declared clock origin, and ordering is
 * evaluated over the **subsequence of clocks that actually exist** — every
 * consecutive existing pair in the canonical order
 * observed <= generated <= available <= retrieved <= artifact_generated —
 * so a null intermediate clock never hides a reversal between its neighbors.
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
    if (RB_CONTACT_EVASION_NON_SOURCE_CLOCK_ORIGINS.has(origin) || origin === 'football_window') {
      push({
        reason_code: 'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
        path: `${provenancePath}.${name}`,
        detail: `${name} declares origin "${origin}"; retrieval, artifact-build, and football-window clocks never substitute for a source clock`,
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

  if (instant(clocks.window_start) > instant(clocks.window_end)) {
    push({
      reason_code: 'CLOCK_ORDER_INVALID',
      path: clocksPath,
      detail: `window_start (${clocks.window_start}) must not be after window_end (${clocks.window_end})`,
    });
  }

  // Total ordering over the existing clocks: filter nulls from the canonical
  // chain and compare EVERY consecutive existing pair, so absence of an
  // intermediate clock cannot hide a reversal between its neighbors.
  const chain: Array<[string, string]> = (
    [
      ['source_observed_at', clocks.source_observed_at],
      ['source_generated_at', clocks.source_generated_at],
      ['source_available_at', clocks.source_available_at],
      ['retrieved_at', clocks.retrieved_at],
      ['artifact_generated_at', clocks.artifact_generated_at],
    ] as Array<[string, string | null]>
  ).filter((entry): entry is [string, string] => entry[1] !== null);
  for (let i = 0; i + 1 < chain.length; i += 1) {
    const [earlierName, earlier] = chain[i];
    const [laterName, later] = chain[i + 1];
    if (instant(earlier) > instant(later)) {
      push({
        reason_code: 'CLOCK_ORDER_INVALID',
        path: clocksPath,
        detail: `${earlierName} (${earlier}) must not be after ${laterName} (${later}); ordering holds over every existing clock, null intermediates included`,
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

/**
 * Source governance. Rights follow the **action being taken**, never the
 * evidence label: storing any exact value requires retention; automated
 * acquisition requires automation permission; attribution obligations require
 * attribution metadata; a promotable claim requires every disposition settled.
 */
function checkSourceAndEvidence(
  observation: RbContactEvasionObservation,
  artifactPosition: RbContactEvasionArtifactPosition,
  path: string,
  push: Push,
): void {
  const { source, evidence_class: evidenceClass, measurement, transform } = observation;
  const sourcePath = `${path}.source`;
  const permissions = source.permissions;
  // ANY stored exact numeric fact counts — an eligible-opportunity count
  // retained on a missing row is a source-derived number like any other.
  const storesExactValue =
    measurement.value !== null ||
    measurement.numerator !== null ||
    measurement.denominator !== null ||
    measurement.eligible_opportunities !== null;

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

  // The material kind bounds the evidence class: conservative labeling is
  // allowed, overstating never is. Editorial keeps its dedicated code.
  if (!RB_CONTACT_EVASION_MATERIAL_EVIDENCE_CLASSES[source.material_kind].includes(evidenceClass)) {
    if (source.material_kind === 'editorial_opinion') {
      push({
        reason_code: 'EXTERNAL_OPINION_LABELED_AS_OBSERVATION',
        path: `${path}.evidence_class`,
        detail: `source material_kind "editorial_opinion" requires evidence_class "external_opinion", got "${evidenceClass}"`,
      });
    } else {
      push({
        reason_code: 'MATERIAL_KIND_INCOMPATIBLE_WITH_EVIDENCE_CLASS',
        path: `${path}.evidence_class`,
        detail: `source material_kind "${source.material_kind}" admits evidence classes [${RB_CONTACT_EVASION_MATERIAL_EVIDENCE_CLASSES[source.material_kind].join(', ')}], got "${evidenceClass}"; a derived publication's figures are the source's derivations and cannot be presented as a direct observation`,
      });
    }
  }

  // Storing an exact value is retention/reproduction of source material,
  // whatever the evidence label. An opinion whose exact figure is stored is
  // still stored.
  if (storesExactValue && permissions.retention_and_reproduction !== 'permitted') {
    push({
      reason_code: 'STORED_EXACT_VALUE_REQUIRES_RETENTION',
      path: `${sourcePath}.permissions.retention_and_reproduction`,
      detail: `an exact value is stored on this row, which is retention/reproduction of source material regardless of evidence_class "${evidenceClass}", but retention_and_reproduction is "${permissions.retention_and_reproduction}"; rights follow the action being taken`,
    });
  }

  if (
    storesExactValue &&
    permissions.attribution === 'required' &&
    (source.attribution_text === null || source.attribution_text.trim() === '')
  ) {
    push({
      reason_code: 'ATTRIBUTION_METADATA_MISSING',
      path: `${sourcePath}.attribution_text`,
      detail: 'permissions.attribution is "required" and an exact value is stored, but no attribution_text is recorded; a declared obligation requires the metadata that satisfies it',
    });
  }

  // Automated-access permission binds to the closed acquisition mode, not to
  // the evidence label.
  if (
    source.acquisition_method === 'automated_ingestion' &&
    permissions.automated_access !== 'permitted'
  ) {
    push({
      reason_code: 'ACQUISITION_MODE_PERMISSION_INCOMPATIBLE',
      path: `${sourcePath}.acquisition_method`,
      detail: `acquisition_method "automated_ingestion" requires permissions.automated_access "permitted", got "${permissions.automated_access}"; an unknown disposition is never read as permission`,
    });
  }

  // One-directional on purpose: synthetically "acquired" material can only be
  // fixture provenance, but a fixture-provenance row may honestly MODEL any
  // acquisition mode (a synthetic row simulating a gated source declares
  // "not_acquired"; one simulating a snapshot pull declares
  // "automated_ingestion"). The row-wide synthetic declaration is the
  // provenance mode plus the required synthetic caveat, not this field.
  if (source.acquisition_method === 'synthetic_fixture' && source.provenance_mode !== 'fixture') {
    push({
      reason_code: 'ACQUISITION_MODE_INCOHERENT',
      path: `${sourcePath}.acquisition_method`,
      detail: `acquisition_method "synthetic_fixture" requires provenance_mode "fixture", got "${source.provenance_mode}"; synthetically produced material cannot claim live or snapshot provenance`,
    });
  }

  if (
    source.acquisition_method === 'not_acquired' &&
    (measurement.status === 'observed' || measurement.eligible_opportunities !== null)
  ) {
    push({
      reason_code: 'ACQUISITION_MODE_INCOHERENT',
      path: `${sourcePath}.acquisition_method`,
      detail: 'acquisition_method "not_acquired" cannot back an observed measurement or a retained eligible-opportunity count; a number that was never acquired cannot be stored',
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

  if (source.content_digest !== null) {
    const digest = source.content_digest;
    const problems: string[] = [];
    if (!RB_CONTACT_EVASION_DIGEST_ALGORITHMS.has(digest.algorithm)) {
      problems.push(
        `algorithm "${digest.algorithm}" is not admitted (admitted: ${[...RB_CONTACT_EVASION_DIGEST_ALGORITHMS].join(', ')})`,
      );
    } else if (!RB_CONTACT_EVASION_SHA256_HEX_PATTERN.test(digest.value)) {
      problems.push('value is not 64 lowercase hex characters');
    }
    if (problems.length > 0) {
      push({
        reason_code: 'CONTENT_DIGEST_MALFORMED',
        path: `${sourcePath}.content_digest`,
        detail: `content digest is not a verifiable pin: ${problems.join('; ')}; an unverifiable digest is not a digest`,
      });
    }
    if (permissions.retention_and_reproduction === 'prohibited') {
      push({
        reason_code: 'CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION',
        path: `${sourcePath}.content_digest`,
        detail: 'a content digest of payload bytes cannot be recorded when retention_and_reproduction is "prohibited"',
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

  if (observation.evidence_class !== 'derived') {
    push({
      reason_code: 'TRANSFORM_REQUIRES_DERIVED_EVIDENCE',
      path: `${path}.transform`,
      detail: `a transform is declared but evidence_class is "${observation.evidence_class}"; deterministic transform lineage belongs to derived evidence only`,
    });
  }

  // A derived rate's lineage must actually contain the components the
  // descriptor declares; a transform that consumed something else did not
  // produce this metric.
  const descriptor = getDescriptor(observation.metric.metric_id);
  if (
    observation.evidence_class === 'derived' &&
    descriptor !== undefined &&
    descriptor.value_kind === 'rate'
  ) {
    const inputs = new Set(transform.input_metric_ids);
    const missing = [descriptor.numerator_metric_id, descriptor.denominator_metric_id].filter(
      (component): component is string => component !== null && !inputs.has(component),
    );
    if (missing.length > 0) {
      push({
        reason_code: 'TRANSFORM_COMPOSITION_INCOMPLETE',
        path: `${path}.transform.input_metric_ids`,
        detail: `a derived "${observation.metric.metric_id}" must consume its declared components [${descriptor.numerator_metric_id}, ${descriptor.denominator_metric_id}], but the transform lineage omits [${missing.join(', ')}]`,
      });
    }
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
    scope.opportunity_class,
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

  // No promotion gate exists in Slice A: no admitted source, no manifest, no
  // digest verification, no promotion review machinery (#224 binds those to
  // Slice B). A promoted-position artifact therefore cannot be legitimate yet
  // and fails closed as a whole.
  if (artifact.artifact_position === 'promoted') {
    push({
      reason_code: 'PROMOTED_POSITION_REQUIRES_PROMOTION_GATE',
      path: 'artifact_position',
      detail:
        'artifact_position "promoted" requires the promotion gate (manifest, digest verification, promotion review) that Slice A does not implement; nothing can sit at promoted position under this contract version',
    });
  }

  artifact.observations.forEach((observation, index) => {
    const path = `observations[${index}]`;
    checkIdentity(observation, path, push);
    checkMetricSemantics(observation, path, push);
    checkCaveats(observation, path, push);
    checkMeasurementStatus(observation, path, push);
    checkNumericDomains(observation, path, push);
    checkRateSemantics(observation, path, push);
    checkMinimumSample(observation, artifact.artifact_position, path, push);
    checkDenominatorSemantics(observation, path, push);
    checkWindowScope(observation, path, push);
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
