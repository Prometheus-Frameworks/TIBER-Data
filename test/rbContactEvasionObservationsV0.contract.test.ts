import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

// Imported through the package barrel on purpose: these are the guarantees the
// published surface promises, so they must be proven at that boundary and not
// against internal helpers.
import {
  RB_CONTACT_EVASION_ARTIFACT_ID,
  RB_CONTACT_EVASION_METRIC_DICTIONARY,
  RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES,
  RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE,
  RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID,
  RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS,
  RB_CONTACT_EVASION_SCHEMA_VERSION,
  RbContactEvasionContractError,
  evaluateRbContactEvasionObservationsV0,
  findRbContactEvasionIncompatibilityAsymmetries,
  isRbContactEvasionObservationsV0,
  rbContactEvasionCaveatIdSchema,
  rbContactEvasionEvidenceClassSchema,
  rbContactEvasionExpectedRate,
  rbContactEvasionGrainKey,
  rbContactEvasionMechanismIdSchema,
  rbContactEvasionReasonCodeSchema,
  rbContactEvasionSourceAccessClassSchema,
  summarizeRbContactEvasionMechanismCoverage,
  validateRbContactEvasionObservationsV0,
  type RbContactEvasionAcquisitionMethod,
  type RbContactEvasionArtifactPosition,
  type RbContactEvasionEvidenceClass,
  type RbContactEvasionObservation,
  type RbContactEvasionObservationsV0,
  type RbContactEvasionOpportunityClass,
  type RbContactEvasionProvenanceMode,
  type RbContactEvasionReasonCode,
  type RbContactEvasionWindowCompleteness,
} from '../src/index.js';

const FIXTURE_ROOT = path.resolve('test/fixtures/rb_contact_evasion');
const SCHEMA_PATH = path.resolve('schemas/rb_contact_evasion_observations_v0.schema.json');
const BUCKY_GSIS_ID = '00-0039361';

function loadFixture(kind: 'positive' | 'negative', name: string): unknown {
  return JSON.parse(readFileSync(path.join(FIXTURE_ROOT, kind, name), 'utf-8'));
}

function mutable(kind: 'positive' | 'negative', name: string): RbContactEvasionObservationsV0 {
  return JSON.parse(
    JSON.stringify(loadFixture(kind, name)),
  ) as RbContactEvasionObservationsV0;
}

function fixtureNames(kind: 'positive' | 'negative'): string[] {
  return readdirSync(path.join(FIXTURE_ROOT, kind))
    .filter((name) => name.endsWith('.json'))
    .sort();
}

function evaluate(artifact: unknown) {
  return evaluateRbContactEvasionObservationsV0(artifact);
}

// ---------------------------------------------------------------------------
// Synthetic row builder for cross-product suites. Builds a fully coherent row
// for any dictionary metric so that each cross-product perturbs exactly one
// dimension against an otherwise valid baseline.
// ---------------------------------------------------------------------------

const GENERATED_AT = '2026-08-24T00:00:00+00:00';

interface BuildOptions {
  opportunityClass?: RbContactEvasionOpportunityClass;
  evidenceClass?: RbContactEvasionEvidenceClass;
  acquisitionMethod?: RbContactEvasionAcquisitionMethod;
  provenanceMode?: RbContactEvasionProvenanceMode;
  windowCompleteness?: RbContactEvasionWindowCompleteness;
  week?: number | null;
  gamesIncluded?: number;
  retention?: 'permitted' | 'prohibited' | 'unknown';
  automation?: 'permitted' | 'prohibited' | 'unknown';
  observationId?: string;
}

function buildObservation(metricId: string, options: BuildOptions = {}): RbContactEvasionObservation {
  const descriptor = RB_CONTACT_EVASION_METRIC_DICTIONARY[metricId];
  if (descriptor === undefined) {
    throw new Error(`unknown metric in test builder: ${metricId}`);
  }
  const opportunityClass =
    options.opportunityClass ?? descriptor.allowed_opportunity_classes[0];
  const testing = opportunityClass === 'athletic_testing';
  const evidenceClass = options.evidenceClass ?? 'direct';
  const provenanceMode = options.provenanceMode ?? 'fixture';
  const acquisitionMethod =
    options.acquisitionMethod ?? (provenanceMode === 'fixture' ? 'synthetic_fixture' : 'automated_ingestion');
  const windowCompleteness =
    options.windowCompleteness ?? (testing ? 'single_week' : 'full_season');

  const clocks = testing
    ? {
        window_start: '2024-02-29T00:00:00+00:00',
        window_end: '2024-03-01T00:00:00+00:00',
        source_observed_at: '2024-03-01T18:00:00+00:00',
        source_generated_at: '2024-03-02T12:00:00+00:00',
        source_available_at: '2024-03-03T09:00:00+00:00',
        retrieved_at: '2024-03-04T15:30:00+00:00',
        artifact_generated_at: GENERATED_AT,
      }
    : {
        window_start: '2024-09-05T00:00:00+00:00',
        window_end: '2025-01-06T00:00:00+00:00',
        source_observed_at: '2025-01-06T04:00:00+00:00',
        source_generated_at: '2025-01-07T12:00:00+00:00',
        source_available_at: '2025-01-08T09:00:00+00:00',
        retrieved_at: '2025-01-09T15:30:00+00:00',
        artifact_generated_at: GENERATED_AT,
      };

  let value: number;
  let numerator: { metric_id: string; value: number } | null = null;
  let denominator: {
    metric_id: string;
    value: number;
    opportunity_type: NonNullable<typeof descriptor.denominator_opportunity_type>;
  } | null = null;
  let eligible: number | null = null;
  if (descriptor.value_kind === 'rate') {
    numerator = { metric_id: descriptor.numerator_metric_id!, value: 26 };
    denominator = {
      metric_id: descriptor.denominator_metric_id!,
      value: 203,
      opportunity_type: descriptor.denominator_opportunity_type!,
    };
    value = rbContactEvasionExpectedRate(26, 203);
    eligible = 203;
  } else if (descriptor.value_kind === 'duration_seconds') {
    value = 4.55;
    eligible = 1;
  } else if (descriptor.value_kind === 'speed_mph') {
    value = 20.5;
  } else {
    value = 62;
  }

  return {
    observation_id: options.observationId ?? `built-${metricId}-${opportunityClass}`,
    mechanism_id: descriptor.mechanisms[0] ?? 'contact_avoidance',
    evidence_class: evidenceClass,
    identity: {
      gsis_id: '00-0000001',
      identity_resolution: 'canonical_gsis_id',
      provider_player_id: null,
      display_name_non_authoritative: null,
    },
    scope: {
      position_at_window: 'RB',
      season: 2024,
      season_type: testing ? 'PRE' : 'REG',
      week: options.week !== undefined ? options.week : testing || windowCompleteness !== 'single_week' ? null : 12,
      games_included:
        options.gamesIncluded !== undefined
          ? options.gamesIncluded
          : testing
            ? 0
            : windowCompleteness === 'single_week'
              ? 1
              : windowCompleteness === 'multi_week'
                ? 2
                : 17,
      window_completeness: windowCompleteness,
      opportunity_class: opportunityClass,
    },
    clocks,
    clock_provenance: {
      window_start: 'football_window',
      window_end: 'football_window',
      source_observed_at: 'source_supplied',
      source_generated_at: 'source_supplied',
      source_available_at: 'source_supplied',
      retrieved_at: 'retrieval_clock',
      artifact_generated_at: 'artifact_build_clock',
    },
    metric: {
      metric_id: metricId,
      source_native_metric_name: `synthetic source-native name for ${metricId}`,
      definition_ref: 'docs/contracts/rb-contact-evasion-observations-v0.md#metric-dictionary',
      definition_version: 'synthetic-def-2024.1',
      unit: descriptor.unit,
      value_kind: descriptor.value_kind,
      directionality: descriptor.directionality,
      minimum_sample_rule_id:
        descriptor.value_kind === 'rate' ? RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID : null,
      inclusion_exclusion_rules: [...descriptor.canonical_inclusion_rules],
      combined_component_disclosure:
        opportunityClass === 'combined_rushing_receiving'
          ? {
              rushing_component_metric_id: 'rush_attempts',
              receiving_component_metric_id: 'receptions',
              disclosure:
                'the touch denominator combines rushing attempts and receptions; the components are named and not silently merged',
            }
          : null,
    },
    measurement: {
      status: 'observed',
      missingness_reason: null,
      value,
      numerator,
      denominator,
      eligible_opportunities: eligible,
    },
    cohort_scope: null,
    transform:
      evidenceClass === 'derived'
        ? {
            transform_version: 'rb_contact_evasion_rate_v0.1.0',
            input_metric_ids:
              descriptor.value_kind === 'rate'
                ? [descriptor.numerator_metric_id!, descriptor.denominator_metric_id!]
                : [metricId],
          }
        : null,
    source: {
      owner: 'example_open_provider',
      product: 'synthetic_cross_product_source',
      snapshot_id: 'synthetic-snapshot-2025-01-07',
      access_class: 'open_and_ingestible',
      acquisition_method: acquisitionMethod,
      acquisition_notes: 'synthetic cross-product row; no external source was accessed',
      material_kind: 'measured_observation',
      supported_opportunity_types: [
        'rush_attempt',
        'reception',
        'target',
        'touch',
        'contact_event',
        'testing_trial',
      ],
      rights_review_ref:
        'docs/contracts/rb-contact-evasion-observations-v0.md#source-access-and-rights',
      permissions: {
        attribution: 'required',
        retention_and_reproduction: options.retention ?? 'permitted',
        redistribution_and_display: 'permitted',
        automated_access: options.automation ?? 'permitted',
      },
      attribution_text: 'synthetic attribution statement (contract test)',
      content_digest:
        provenanceMode === 'snapshot' ? { algorithm: 'sha256', value: '0'.repeat(64) } : null,
      promotable: false,
      provenance_mode: provenanceMode,
      superseded_by_snapshot_id: null,
    },
    caveat_ids: [
      ...(provenanceMode === 'fixture' ? (['synthetic_fixture_value'] as const) : []),
      ...(opportunityClass === 'combined_rushing_receiving'
        ? (['combined_touch_denominator_disclosed'] as const)
        : []),
      ...descriptor.required_caveat_ids,
    ],
    warnings: [
      'synthetic contract-fixture value; not acquired provider data and not evidence about any real player',
    ],
  };
}

function buildArtifact(
  observations: RbContactEvasionObservation[],
  position: RbContactEvasionArtifactPosition = 'fixture_only',
): RbContactEvasionObservationsV0 {
  return {
    artifact_id: RB_CONTACT_EVASION_ARTIFACT_ID,
    schema_version: RB_CONTACT_EVASION_SCHEMA_VERSION,
    artifact_position: position,
    generated_at: GENERATED_AT,
    contract_ref: 'docs/contracts/rb-contact-evasion-observations-v0.md',
    observations,
  };
}

// ---------------------------------------------------------------------------
// Fixture corpus
// ---------------------------------------------------------------------------

const MANDATED_POSITIVE: ReadonlyArray<[string, string]> = [
  ['P1 complete derived explosiveness rate', 'p1_complete_derived_explosiveness_rate.json'],
  ['P2 raw count without denominator', 'p2_raw_count_without_denominator.json'],
  ['P3 correctly classified historical testing', 'p3_historical_testing_classified.json'],
  ['P4 rights-blocked missing component', 'p4_rights_blocked_missing_component.json'],
  ['P5 declared snapshot supersession', 'p5_declared_snapshot_supersession.json'],
  ['P6 weekly and season windows coexisting', 'p6_weekly_and_season_windows_coexist.json'],
  ['P7 Bucky receipt remains partial', 'p7_bucky_receipt_remains_partial.json'],
];

const SUPPLEMENTARY_POSITIVE: ReadonlyArray<[string, string]> = [
  ['P8 absent source clock stays null', 'p8_absent_source_clock_stays_null.json'],
  ['P9 below-minimum sample honestly missing and provable', 'p9_below_minimum_sample_provable.json'],
];

const MANDATED_NEGATIVE: ReadonlyArray<[string, string, RbContactEvasionReasonCode]> = [
  ['N1 missing denominator', 'n01_rate_missing_denominator.json', 'RATE_MISSING_DENOMINATOR'],
  ['N2 unsupported touches denominator', 'n02_denominator_unsupported_by_source.json', 'DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE'],
  ['N3 silently combined rushing and receiving', 'n03_rushing_receiving_silently_combined.json', 'RUSHING_RECEIVING_SILENTLY_COMBINED'],
  ['N4 definition drift', 'n04_metric_definition_drift.json', 'METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID'],
  ['N5 reference-only source marked promotable and direct', 'n05_reference_only_source_overclaimed.json', 'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED'],
  ['N6 external opinion labeled as observation', 'n06_external_opinion_labeled_observation.json', 'EXTERNAL_OPINION_LABELED_AS_OBSERVATION'],
  ['N7 partial/full-season comparison without disclosure', 'n07_partial_full_window_comparison_undisclosed.json', 'WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED'],
  ['N8 below-minimum rate', 'n08_below_minimum_sample_rate_emitted.json', 'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED'],
  ['N9 wrong cohort position or season type', 'n09_cohort_scope_mismatch.json', 'COHORT_SCOPE_MISMATCH'],
  ['N10 retrieval clock substituted for source clock', 'n10_retrieval_clock_substituted.json', 'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK'],
  ['N11 unresolved canonical identity', 'n11_canonical_identity_unresolved.json', 'CANONICAL_IDENTITY_UNRESOLVED'],
  ['N12 misclassified 40-yard dash, long gain, or yards per carry', 'n12_mechanism_metric_binding_violation.json', 'MECHANISM_METRIC_BINDING_VIOLATION'],
  ['N13 default value supplied for a missing component', 'n13_default_value_for_missing_component.json', 'MISSING_COMPONENT_CARRIES_VALUE'],
  ['N14 transform consuming incompatible metrics', 'n14_incompatible_transform_inputs.json', 'INCOMPATIBLE_METRIC_TRANSFORM_INPUT'],
  ['N15 fixture provenance in candidate position', 'n15_fixture_provenance_in_candidate_position.json', 'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION'],
];

const SECOND_ROUND_NEGATIVE: ReadonlyArray<[string, string, RbContactEvasionReasonCode]> = [
  ['N16 promotable without redistribution permission', 'n16_promotable_without_permissions.json', 'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE'],
  ['N17 stored value without retention', 'n17_direct_observation_without_retention.json', 'STORED_EXACT_VALUE_REQUIRES_RETENTION'],
  ['N18 snapshot without content digest', 'n18_snapshot_without_content_digest.json', 'SNAPSHOT_WITHOUT_CONTENT_DIGEST'],
  ['N19 duplicate observation id', 'n19_duplicate_observation_id.json', 'DUPLICATE_OBSERVATION_ID'],
  ['N20 duplicate canonical grain', 'n20_duplicate_observation_grain.json', 'DUPLICATE_OBSERVATION_GRAIN'],
  ['N21 rate value inconsistent with components', 'n21_rate_value_inconsistent_with_components.json', 'RATE_VALUE_INCONSISTENT_WITH_COMPONENTS'],
  ['N22 known-but-wrong rate component', 'n22_rate_component_metric_mismatch.json', 'RATE_COMPONENT_METRIC_MISMATCH'],
  ['N23 non-positive rate denominator', 'n23_rate_denominator_not_positive.json', 'RATE_DENOMINATOR_NOT_POSITIVE'],
  ['N24 metric descriptor contradicted', 'n24_metric_descriptor_contradicted.json', 'METRIC_DESCRIPTOR_CONTRADICTED'],
  ['N25 eligible opportunities absent on a rate', 'n25_eligible_opportunities_absent.json', 'ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE'],
  ['N26 clock availability contradicted', 'n26_clock_availability_contradicted.json', 'CLOCK_AVAILABILITY_CONTRADICTED'],
  ['N27 minimum-sample rule not code-owned', 'n27_minimum_sample_rule_not_code_owned.json', 'MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED'],
  ['N28 minimum-sample rule not admitted for position', 'n28_minimum_sample_rule_not_admitted_for_position.json', 'MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION'],
];

const CONVERGENCE_NEGATIVE: ReadonlyArray<[string, string, RbContactEvasionReasonCode]> = [
  ['N29 testing metric relabeled a game observation', 'n29_metric_opportunity_class_incompatible.json', 'METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE'],
  ['N30 canonical definition rewritten under a stable id', 'n30_canonical_definition_contradicted.json', 'CANONICAL_DEFINITION_CONTRADICTED'],
  ['N31 derived transform omits its declared components', 'n31_transform_composition_incomplete.json', 'TRANSFORM_COMPOSITION_INCOMPLETE'],
  ['N32 mandatory caveat dropped', 'n32_required_caveat_missing.json', 'REQUIRED_CAVEAT_MISSING'],
  ['N33 sample gate cleared by an unrelated eligible count', 'n33_eligible_opportunities_denominator_mismatch.json', 'ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH'],
  ['N34 negative event count with a consistent negative rate', 'n34_measurement_numeric_domain_violation.json', 'MEASUREMENT_NUMERIC_DOMAIN_VIOLATION'],
  ['N35 count metric carrying rate components', 'n35_rate_components_on_non_rate_metric.json', 'RATE_COMPONENTS_ON_NON_RATE_METRIC'],
  ['N36 clock reversal hidden behind a null intermediate', 'n36_clock_order_invalid_across_null.json', 'CLOCK_ORDER_INVALID'],
  ['N37 automated ingestion without automation permission', 'n37_acquisition_mode_permission_incompatible.json', 'ACQUISITION_MODE_PERMISSION_INCOMPATIBLE'],
  ['N38 required attribution without attribution metadata', 'n38_attribution_metadata_missing.json', 'ATTRIBUTION_METADATA_MISSING'],
  ['N39 unverifiable content digest', 'n39_content_digest_malformed.json', 'CONTENT_DIGEST_MALFORMED'],
  ['N40 full-season window carrying a week', 'n40_window_scope_incoherent.json', 'WINDOW_SCOPE_INCOHERENT'],
  ['N41 transform lineage on non-derived evidence', 'n41_transform_requires_derived_evidence.json', 'TRANSFORM_REQUIRES_DERIVED_EVIDENCE'],
  ['N42 synthetic acquisition with live provenance', 'n42_acquisition_mode_incoherent.json', 'ACQUISITION_MODE_INCOHERENT'],
];

/** N43-N49: the missingness-and-declaration round, one fixture per new rule. */
const MISSINGNESS_NEGATIVE: ReadonlyArray<[string, string, RbContactEvasionReasonCode]> = [
  ['N43 rights-blocked claim against a fully open source', 'n43_missingness_reason_unsupported.json', 'MISSINGNESS_REASON_UNSUPPORTED'],
  ['N44 missing row retaining an unjustified eligible count', 'n44_missingness_eligible_count_inadmissible.json', 'MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE'],
  ['N45 below-minimum claim without its proving count', 'n45_below_minimum_sample_unprovable.json', 'BELOW_MINIMUM_SAMPLE_UNPROVABLE'],
  ['N46 combined disclosure naming wrong components', 'n46_combined_component_disclosure_contradicted.json', 'COMBINED_COMPONENT_DISCLOSURE_CONTRADICTED'],
  ['N47 synthetic caveat on live provenance', 'n47_inapplicable_caveat_declared.json', 'INAPPLICABLE_CAVEAT_DECLARED'],
  ['N48 count metric naming a sample rule', 'n48_minimum_sample_rule_not_applicable.json', 'MINIMUM_SAMPLE_RULE_NOT_APPLICABLE'],
  ['N49 derived publication labeled a direct observation', 'n49_material_kind_incompatible_with_evidence_class.json', 'MATERIAL_KIND_INCOMPATIBLE_WITH_EVIDENCE_CLASS'],
];

const ALL_POSITIVE = [...MANDATED_POSITIVE, ...SUPPLEMENTARY_POSITIVE];
const ALL_NEGATIVE = [
  ...MANDATED_NEGATIVE,
  ...SECOND_ROUND_NEGATIVE,
  ...CONVERGENCE_NEGATIVE,
  ...MISSINGNESS_NEGATIVE,
];

describe('rb_contact_evasion_observations_v0 positive fixtures', () => {
  it('covers exactly the positive corpus with no unlisted fixtures', () => {
    expect(fixtureNames('positive')).toEqual(ALL_POSITIVE.map(([, file]) => file).sort());
  });

  it.each(ALL_POSITIVE)('%s validates through the public gate', (_label, file) => {
    const payload = loadFixture('positive', file);
    const report = evaluate(payload);
    expect(report.violations).toEqual([]);
    expect(report.valid).toBe(true);
    expect(isRbContactEvasionObservationsV0(payload)).toBe(true);
    const artifact = validateRbContactEvasionObservationsV0(payload);
    expect(artifact.artifact_id).toBe(RB_CONTACT_EVASION_ARTIFACT_ID);
    expect(artifact.schema_version).toBe(RB_CONTACT_EVASION_SCHEMA_VERSION);
    expect(artifact.artifact_position).toBe('fixture_only');
  });

  it('P2 carries a raw count with no denominator and is not a rate', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p2_raw_count_without_denominator.json'),
    ).observations;
    expect(observation.metric.value_kind).toBe('count');
    expect(observation.measurement.denominator).toBeNull();
    expect(observation.measurement.numerator).toBeNull();
  });

  it('P3 classifies historical testing under speed and athletic_testing, with the mandatory caveat', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p3_historical_testing_classified.json'),
    ).observations;
    expect(observation.metric.metric_id).toBe('forty_yard_dash_seconds');
    expect(observation.mechanism_id).toBe('speed');
    expect(observation.scope.opportunity_class).toBe('athletic_testing');
    expect(observation.caveat_ids).toContain('historical_testing_not_current_form');
    expect(
      RB_CONTACT_EVASION_METRIC_DICTIONARY.forty_yard_dash_seconds.allowed_opportunity_classes,
    ).toEqual(['athletic_testing']);
  });

  it('P4 keeps a rights-blocked component missing with no value of any kind', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p4_rights_blocked_missing_component.json'),
    ).observations;
    expect(observation.source.access_class).toBe('licensed_or_gated');
    expect(observation.source.promotable).toBe(false);
    expect(observation.source.acquisition_method).toBe('not_acquired');
    expect(observation.measurement.status).toBe('missing');
    expect(observation.measurement.missingness_reason).toBe('rights_blocked');
    expect(observation.measurement.value).toBeNull();
  });

  it('P5 declares supersession and pins the snapshot with a well-formed digest', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p5_declared_snapshot_supersession.json'),
    ).observations;
    expect(observation.source.provenance_mode).toBe('snapshot');
    expect(observation.source.content_digest?.algorithm).toBe('sha256');
    expect(observation.source.content_digest?.value).toMatch(/^[0-9a-f]{64}$/);
    expect(observation.caveat_ids).toContain('snapshot_superseded');
    expect(observation.source.superseded_by_snapshot_id).toBe('synthetic-snapshot-2025-02-11');
    expect(observation.source.superseded_by_snapshot_id).not.toBe(observation.source.snapshot_id);
  });

  it('P6 keeps a weekly and a season window as separate rows and separate grains', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p6_weekly_and_season_windows_coexist.json'),
    );
    expect(artifact.observations.map((row) => row.scope.window_completeness)).toEqual([
      'single_week',
      'full_season',
    ]);
    expect(artifact.observations[0].scope.week).toBe(12);
    expect(artifact.observations[1].scope.week).toBeNull();
    expect(new Set(artifact.observations.map((row) => row.metric.definition_version)).size).toBe(1);
    expect(rbContactEvasionGrainKey(artifact.observations[0])).not.toBe(
      rbContactEvasionGrainKey(artifact.observations[1]),
    );
  });

  it('P7 returns a Bucky receipt that stays partial and emits no composite', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p7_bucky_receipt_remains_partial.json'),
    );
    for (const observation of artifact.observations) {
      expect(observation.identity.gsis_id).toBe(BUCKY_GSIS_ID);
      expect(observation.identity.identity_resolution).toBe('canonical_gsis_id');
    }
    const coverage = summarizeRbContactEvasionMechanismCoverage(artifact, BUCKY_GSIS_ID);
    expect(coverage.contact_avoidance.status).toBe('observed');
    expect(coverage.contact_survival.status).toBe('observed');
    expect(coverage.explosiveness.status).toBe('observed');
    expect(coverage.speed.status).toBe('known_missing');
    expect(coverage.agility_change_of_direction.status).toBe('known_missing');
    expect(coverage.speed.observed_observation_ids).toEqual([]);
    expect(coverage.agility_change_of_direction.observed_observation_ids).toEqual([]);
    expect(JSON.stringify(coverage)).not.toMatch(
      /score|composite|grade|rank|percentile|elite|overall/i,
    );
    for (const entry of Object.values(coverage)) {
      expect(Object.keys(entry).sort()).toEqual([
        'missing_observation_ids',
        'observed_observation_ids',
        'status',
      ]);
    }
  });

  it('P8 keeps an unavailable source clock null rather than backfilling it', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p8_absent_source_clock_stays_null.json'),
    ).observations;
    expect(observation.clocks.source_generated_at).toBeNull();
    expect(observation.clock_provenance.source_generated_at).toBe('not_supplied_by_source');
    expect(observation.clocks.retrieved_at).not.toBeNull();
  });

  it('an unknown player in a receipt query yields no evidence at all', () => {
    const coverage = summarizeRbContactEvasionMechanismCoverage(
      validateRbContactEvasionObservationsV0(
        loadFixture('positive', 'p7_bucky_receipt_remains_partial.json'),
      ),
      '00-0000001',
    );
    for (const entry of Object.values(coverage)) {
      expect(entry.status).toBe('no_admitted_observation');
    }
  });
});

describe('rb_contact_evasion_observations_v0 negative fixtures', () => {
  it('covers exactly the negative corpus with no unlisted fixtures', () => {
    expect(fixtureNames('negative')).toEqual(ALL_NEGATIVE.map(([, file]) => file).sort());
  });

  it('keeps the #234-mandated N1-N15 corpus intact and distinctly coded', () => {
    const codes = MANDATED_NEGATIVE.map(([, , code]) => code);
    expect(codes.length).toBe(15);
    expect(new Set(codes).size).toBe(15);
  });

  it('assigns a distinct reason code to every negative fixture', () => {
    const codes = ALL_NEGATIVE.map(([, , code]) => code);
    expect(new Set(codes).size).toBe(codes.length);
  });

  it.each(ALL_NEGATIVE)(
    '%s is rejected for its own reason, after parsing cleanly',
    (_label, file, expectedCode) => {
      const report = evaluate(loadFixture('negative', file));
      expect(report.shape_valid).toBe(true);
      expect(report.reason_codes).not.toContain('SCHEMA_SHAPE_INVALID');
      expect(report.reason_codes).not.toContain('UNKNOWN_FIELD_PRESENT');
      expect(report.valid).toBe(false);
      expect(report.reason_codes).toEqual([expectedCode]);
      expect(report.violations.length).toBeGreaterThan(0);
      for (const violation of report.violations) {
        expect(violation.reason_code).toBe(expectedCode);
        expect(violation.path).toMatch(/^observations\[\d+\]/);
        expect(violation.detail.length).toBeGreaterThan(0);
      }
    },
  );

  it.each(ALL_NEGATIVE)(
    '%s is rejected at the public gate, not only by the report helper',
    (_label, file, expectedCode) => {
      const payload = loadFixture('negative', file);
      expect(isRbContactEvasionObservationsV0(payload)).toBe(false);
      expect(() => validateRbContactEvasionObservationsV0(payload)).toThrow(
        RbContactEvasionContractError,
      );
      try {
        validateRbContactEvasionObservationsV0(payload);
        throw new Error('expected the contract gate to throw');
      } catch (error) {
        expect(error).toBeInstanceOf(RbContactEvasionContractError);
        const contractError = error as RbContactEvasionContractError;
        expect(contractError.reasonCodes).toEqual([expectedCode]);
        expect(contractError.message).toContain(expectedCode);
      }
    },
  );
});

/**
 * Exact-attack regression locks. Every escape reproduced by the second and
 * third exact-head reviews is re-applied here through the public evaluator and
 * must stay rejected by a named semantic reason code.
 */
describe('rb_contact_evasion_observations_v0 review-round escapes, at the public boundary', () => {
  const P1 = () => mutable('positive', 'p1_complete_derived_explosiveness_rate.json');
  const P2 = () => mutable('positive', 'p2_raw_count_without_denominator.json');
  const P3 = () => mutable('positive', 'p3_historical_testing_classified.json');
  const P8 = () => mutable('positive', 'p8_absent_source_clock_stays_null.json');

  describe('round two: payload-owned semantics', () => {
    it('rejects an emitted value unrelated to its own numerator and denominator', () => {
      const artifact = P1();
      artifact.observations[0].measurement.value = 0.999;
      expect(evaluate(artifact).reason_codes).toEqual(['RATE_VALUE_INCONSISTENT_WITH_COMPONENTS']);
    });

    it('rejects a known-but-wrong numerator metric id', () => {
      const artifact = P1();
      artifact.observations[0].measurement.numerator = { metric_id: 'receptions', value: 26 };
      expect(evaluate(artifact).reason_codes).toEqual(['RATE_COMPONENT_METRIC_MISMATCH']);
    });

    it('rejects a zero denominator', () => {
      const artifact = P1();
      artifact.observations[0].measurement.denominator!.value = 0;
      expect(evaluate(artifact).reason_codes).toEqual(['RATE_DENOMINATOR_NOT_POSITIVE']);
    });

    it('rejects a rewritten unit and a flipped directionality', () => {
      const artifact = P1();
      artifact.observations[0].metric.unit = 'bananas';
      artifact.observations[0].metric.directionality = 'lower_is_more_of_mechanism';
      expect(evaluate(artifact).reason_codes).toEqual(['METRIC_DESCRIPTOR_CONTRADICTED']);
    });

    it('owns the rate rounding rather than letting the row imply it', () => {
      expect(RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS).toBe(3);
      expect(rbContactEvasionExpectedRate(26, 203)).toBe(0.128);
      expect(rbContactEvasionExpectedRate(694, 203)).toBe(3.419);
    });

    it('rejects an observed rate with no eligible-opportunity count', () => {
      const artifact = P1();
      artifact.observations[0].measurement.eligible_opportunities = null;
      expect(evaluate(artifact).reason_codes).toEqual(['ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE']);
    });

    it('gives the row no threshold field to lower — only a rule id it must match', () => {
      const artifact = P1();
      expect(
        (artifact.observations[0].metric as unknown as Record<string, unknown>)
          .minimum_eligible_opportunities,
      ).toBeUndefined();
      artifact.observations[0].metric.minimum_sample_rule_id = 'row_declared_minimum_of_one';
      expect(evaluate(artifact).reason_codes).toEqual(['MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED']);
    });

    it('fails closed for an observed rate outside fixture_only position', () => {
      const artifact = P1();
      artifact.artifact_position = 'candidate';
      artifact.observations[0].source.provenance_mode = 'live';
      artifact.observations[0].source.acquisition_method = 'automated_ingestion';
      artifact.observations[0].caveat_ids = artifact.observations[0].caveat_ids.filter(
        (caveat) => caveat !== 'synthetic_fixture_value',
      );
      expect(evaluate(artifact).reason_codes).toEqual(['MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION']);
    });

    it('rejects a substituted retrieval clock even when an offset hides the copy', () => {
      const artifact = P1();
      artifact.observations[0].clock_provenance.source_generated_at = 'retrieval_clock';
      expect(evaluate(artifact).reason_codes).toEqual(['RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK']);
    });

    it('no longer rejects a legitimately coincident instant', () => {
      const artifact = P1();
      const clocks = artifact.observations[0].clocks;
      clocks.source_generated_at = '2025-01-09T15:30:00+00:00';
      clocks.source_available_at = '2025-01-09T15:30:00+00:00';
      clocks.source_observed_at = '2025-01-09T15:30:00+00:00';
      clocks.retrieved_at = '2025-01-09T15:30:00+00:00';
      expect(evaluate(artifact).valid).toBe(true);
    });

    it('rejects a verbatim duplicated observation and both partial duplicates', () => {
      const verbatim = P1();
      verbatim.observations.push(JSON.parse(JSON.stringify(verbatim.observations[0])));
      expect(evaluate(verbatim).reason_codes).toEqual([
        'DUPLICATE_OBSERVATION_GRAIN',
        'DUPLICATE_OBSERVATION_ID',
      ]);

      const grainOnly = P1();
      const renamed = JSON.parse(
        JSON.stringify(grainOnly.observations[0]),
      ) as RbContactEvasionObservation;
      renamed.observation_id = 'renamed-duplicate-grain';
      grainOnly.observations.push(renamed);
      expect(evaluate(grainOnly).reason_codes).toEqual(['DUPLICATE_OBSERVATION_GRAIN']);
    });
  });

  describe('round three: adjacent fields still payload-owned', () => {
    it('F1a: a 40-yard dash cannot be relabeled a rushing observation', () => {
      const artifact = P3();
      artifact.observations[0].scope = {
        ...artifact.observations[0].scope,
        opportunity_class: 'rushing',
        window_completeness: 'full_season',
        games_included: 17,
      };
      expect(evaluate(artifact).reason_codes).toEqual(['METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE']);
    });

    it('F1b: the canonical inclusion rule cannot be rewritten under the same id', () => {
      const artifact = P1();
      artifact.observations[0].metric.inclusion_exclusion_rules = [
        'rushing attempts only',
        'an explosive rush is a rush gaining 5 or more yards from scrimmage',
      ];
      expect(evaluate(artifact).reason_codes).toEqual(['CANONICAL_DEFINITION_CONTRADICTED']);
    });

    it('F1c: a derived rate transform must consume its declared components', () => {
      const artifact = P1();
      artifact.observations[0].transform!.input_metric_ids = ['receptions'];
      expect(evaluate(artifact).reason_codes).toEqual(['TRANSFORM_COMPOSITION_INCOMPLETE']);
    });

    it('F1d: the mandatory historical-testing caveat cannot be dropped', () => {
      const artifact = P3();
      artifact.observations[0].caveat_ids = ['synthetic_fixture_value'];
      expect(evaluate(artifact).reason_codes).toEqual(['REQUIRED_CAVEAT_MISSING']);
    });

    it('F2a: a rate cannot clear the sample gate with an unrelated eligible count', () => {
      const artifact = P1();
      artifact.observations[0].measurement.denominator!.value = 5;
      artifact.observations[0].measurement.value = rbContactEvasionExpectedRate(26, 5);
      // eligible_opportunities stays 203 — the exact laundering from review
      expect(evaluate(artifact).reason_codes).toEqual(['ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH']);
    });

    it('F2b: a negative event count is rejected even with consistent arithmetic', () => {
      const artifact = P1();
      artifact.observations[0].measurement.numerator!.value = -1;
      artifact.observations[0].measurement.value = rbContactEvasionExpectedRate(-1, 203);
      const report = evaluate(artifact);
      expect(report.reason_codes).toEqual(['MEASUREMENT_NUMERIC_DOMAIN_VIOLATION']);
    });

    it('F2c: a count metric cannot carry rate components', () => {
      const artifact = P2();
      artifact.observations[0].measurement.numerator = {
        metric_id: 'forced_missed_tackles_count',
        value: 62,
      };
      artifact.observations[0].measurement.denominator = {
        metric_id: 'rush_attempts',
        value: 203,
        opportunity_type: 'rush_attempt',
      };
      expect(evaluate(artifact).reason_codes).toEqual(['RATE_COMPONENTS_ON_NON_RATE_METRIC']);
    });

    it('F3-adjacent: a clock declared source-supplied that carries no timestamp is contradicted', () => {
      const artifact = P1();
      artifact.observations[0].clocks.source_generated_at = null;
      // Origin still claims the source supplied it, so absence is a contradiction.
      expect(evaluate(artifact).reason_codes).toEqual(['CLOCK_AVAILABILITY_CONTRADICTED']);
    });

    it('F3: ordering holds across a null intermediate clock', () => {
      const artifact = P8();
      const observation = artifact.observations[0];
      observation.clocks.source_observed_at = '2025-01-08T10:00:00+00:00';
      observation.clock_provenance.source_observed_at = 'source_supplied';
      // generated stays null; available (09:00) is BEFORE observed (10:00)
      expect(evaluate(artifact).reason_codes).toEqual(['CLOCK_ORDER_INVALID']);
    });

    it('F4a: a stored exact value requires retention whatever the evidence label', () => {
      const artifact = P1();
      const observation = artifact.observations[0];
      observation.evidence_class = 'external_opinion';
      observation.transform = null;
      observation.source.access_class = 'reference_only';
      observation.source.material_kind = 'editorial_opinion';
      observation.source.acquisition_method = 'manual_citation';
      observation.source.provenance_mode = 'fixture';
      observation.source.permissions.retention_and_reproduction = 'prohibited';
      observation.source.permissions.automated_access = 'prohibited';
      expect(evaluate(artifact).reason_codes).toEqual(['STORED_EXACT_VALUE_REQUIRES_RETENTION']);
    });

    it('F4b: automated acquisition requires automation permission, bound to the closed mode', () => {
      const artifact = P1();
      artifact.observations[0].source.provenance_mode = 'live';
      artifact.observations[0].source.acquisition_method = 'automated_ingestion';
      artifact.observations[0].source.permissions.automated_access = 'unknown';
      artifact.observations[0].caveat_ids = artifact.observations[0].caveat_ids.filter(
        (caveat) => caveat !== 'synthetic_fixture_value',
      );
      expect(evaluate(artifact).reason_codes).toEqual(['ACQUISITION_MODE_PERMISSION_INCOMPATIBLE']);
    });

    it('F4c: a required attribution obligation requires attribution metadata', () => {
      const artifact = P1();
      artifact.observations[0].source.attribution_text = null;
      expect(evaluate(artifact).reason_codes).toEqual(['ATTRIBUTION_METADATA_MISSING']);
    });

    it('F4d: a content digest is closed to an admitted algorithm and format', () => {
      const artifact = P1();
      artifact.observations[0].source.provenance_mode = 'snapshot';
      artifact.observations[0].source.acquisition_method = 'automated_ingestion';
      artifact.observations[0].caveat_ids = artifact.observations[0].caveat_ids.filter(
        (caveat) => caveat !== 'synthetic_fixture_value',
      );
      artifact.observations[0].source.content_digest = { algorithm: 'trust_me', value: 'x' };
      expect(evaluate(artifact).reason_codes).toEqual(['CONTENT_DIGEST_MALFORMED']);
    });

    it('F5a: a full-season row cannot carry a week', () => {
      const artifact = P1();
      artifact.observations[0].scope.week = 12;
      expect(evaluate(artifact).reason_codes).toEqual(['WINDOW_SCOPE_INCOHERENT']);
    });

    it('F5b: a single-week game row must name its week', () => {
      const artifact = P1();
      artifact.observations[0].scope.window_completeness = 'single_week';
      artifact.observations[0].scope.games_included = 1;
      artifact.observations[0].cohort_scope = null;
      // week stays null
      expect(evaluate(artifact).reason_codes).toEqual(['WINDOW_SCOPE_INCOHERENT']);
    });

    it('F5c: an observed game window cannot claim zero games', () => {
      const artifact = P1();
      artifact.observations[0].scope.games_included = 0;
      expect(evaluate(artifact).reason_codes).toEqual(['WINDOW_SCOPE_INCOHERENT']);
    });
  });
});

/**
 * Round-four escape locks: the missingness-and-declaration findings. Each
 * exact attack reproduced by the third exact-head review is re-applied through
 * the public evaluator.
 */
describe('round four: missingness and declarations were self-declaring', () => {
  const P1 = () => mutable('positive', 'p1_complete_derived_explosiveness_rate.json');
  const P2 = () => mutable('positive', 'p2_raw_count_without_denominator.json');
  const P4 = () => mutable('positive', 'p4_rights_blocked_missing_component.json');
  const P9 = () => mutable('positive', 'p9_below_minimum_sample_provable.json');

  it('G1: a missing row cannot retain an eligible count without retention rights', () => {
    // The reviewer's exact attack: rights_blocked, components nulled, eligible
    // kept at 203, reference-only editorial source with retention prohibited.
    const artifact = P1();
    const observation = artifact.observations[0];
    observation.measurement.status = 'missing';
    observation.measurement.missingness_reason = 'rights_blocked';
    observation.measurement.value = null;
    observation.measurement.numerator = null;
    observation.measurement.denominator = null;
    observation.evidence_class = 'external_opinion';
    observation.transform = null;
    observation.source.access_class = 'reference_only';
    observation.source.material_kind = 'editorial_opinion';
    observation.source.acquisition_method = 'manual_citation';
    observation.source.permissions.retention_and_reproduction = 'prohibited';
    const report = evaluate(artifact);
    expect(report.valid).toBe(false);
    // The retained count is inadmissible under this reason AND is a stored
    // exact fact requiring retention. Both rules bite; neither alone carried it.
    expect(report.reason_codes).toContain('MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE');
    expect(report.reason_codes).toContain('STORED_EXACT_VALUE_REQUIRES_RETENTION');
  });

  it('G1: eligible_opportunities participates in retention and attribution as a stored fact', () => {
    const artifact = P9();
    artifact.observations[0].source.permissions.retention_and_reproduction = 'prohibited';
    expect(evaluate(artifact).reason_codes).toEqual(['STORED_EXACT_VALUE_REQUIRES_RETENTION']);

    const attribution = P9();
    attribution.observations[0].source.attribution_text = null;
    expect(evaluate(attribution).reason_codes).toEqual(['ATTRIBUTION_METADATA_MISSING']);

    const notAcquired = P9();
    notAcquired.observations[0].source.acquisition_method = 'not_acquired';
    notAcquired.observations[0].source.provenance_mode = 'fixture';
    expect(evaluate(notAcquired).reason_codes).toEqual(['ACQUISITION_MODE_INCOHERENT']);
  });

  it('G1: below_minimum_sample stays expressible and provable (P9), and is policed', () => {
    expect(evaluate(loadFixture('positive', 'p9_below_minimum_sample_provable.json')).violations).toEqual([]);

    // No count -> unprovable.
    const unprovable = P9();
    unprovable.observations[0].measurement.eligible_opportunities = null;
    expect(evaluate(unprovable).reason_codes).toEqual(['BELOW_MINIMUM_SAMPLE_UNPROVABLE']);

    // Count meeting the bar -> disproven.
    const disproven = P9();
    disproven.observations[0].measurement.eligible_opportunities = 20;
    expect(evaluate(disproven).reason_codes).toEqual(['BELOW_MINIMUM_SAMPLE_UNPROVABLE']);

    // On a non-rate metric there is no gate to fall below.
    const nonRate = P2();
    nonRate.observations[0].measurement.status = 'missing';
    nonRate.observations[0].measurement.missingness_reason = 'below_minimum_sample';
    nonRate.observations[0].measurement.value = null;
    expect(evaluate(nonRate).reason_codes).toEqual(['BELOW_MINIMUM_SAMPLE_UNPROVABLE']);

    // Outside fixture_only the governing rule is not admitted, for claims as
    // for observed rates.
    const candidate = P9();
    candidate.artifact_position = 'candidate';
    candidate.observations[0].source.provenance_mode = 'live';
    candidate.observations[0].source.acquisition_method = 'automated_ingestion';
    candidate.observations[0].caveat_ids = candidate.observations[0].caveat_ids.filter(
      (caveat) => caveat !== 'synthetic_fixture_value',
    );
    expect(evaluate(candidate).reason_codes).toEqual(['MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION']);
  });

  it('G1: missingness reasons are policed against the declared source state', () => {
    // rights_blocked against a fully open, fully permitted source.
    const openRights = P4();
    openRights.observations[0].source = {
      ...openRights.observations[0].source,
      access_class: 'open_and_ingestible',
      acquisition_method: 'synthetic_fixture',
      permissions: {
        attribution: 'not_required',
        retention_and_reproduction: 'permitted',
        redistribution_and_display: 'permitted',
        automated_access: 'permitted',
      },
    };
    expect(evaluate(openRights).reason_codes).toEqual(['MISSINGNESS_REASON_UNSUPPORTED']);

    // source_unavailable without access_class "unavailable".
    const unavailable = P4();
    unavailable.observations[0].measurement.missingness_reason = 'source_unavailable';
    expect(evaluate(unavailable).reason_codes).toEqual(['MISSINGNESS_REASON_UNSUPPORTED']);

    // An unrelated eligible count under rights_blocked (state itself valid).
    const withCount = P4();
    withCount.observations[0].measurement.eligible_opportunities = 203;
    const report = evaluate(withCount);
    expect(report.reason_codes).toContain('MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE');
  });

  it('G2: a combined disclosure must restate the code-owned composition', () => {
    const artifact = mutable('negative', 'n02_denominator_unsupported_by_source.json');
    const observation = artifact.observations[0];
    observation.source.supported_opportunity_types = ['rush_attempt', 'reception', 'touch'];
    observation.metric.combined_component_disclosure = {
      rushing_component_metric_id: 'testing_trials',
      receiving_component_metric_id: 'testing_trials',
      disclosure: 'components exist',
    };
    expect(evaluate(artifact).reason_codes).toEqual(['COMBINED_COMPONENT_DISCLOSURE_CONTRADICTED']);

    // A disclosure with no combination to disclose is equally contradicted.
    const uncombined = P1();
    uncombined.observations[0].metric.combined_component_disclosure = {
      rushing_component_metric_id: 'rush_attempts',
      receiving_component_metric_id: 'receptions',
      disclosure: 'nothing is combined here',
    };
    const report = evaluate(uncombined);
    expect(report.reason_codes).toContain('COMBINED_COMPONENT_DISCLOSURE_CONTRADICTED');
  });

  it('G2: the combined caveat binds to the verified disclosure in both directions', () => {
    // Disclosure present, caveat dropped -> required.
    const missingCaveat = mutable('negative', 'n02_denominator_unsupported_by_source.json');
    missingCaveat.observations[0].source.supported_opportunity_types = [
      'rush_attempt',
      'reception',
      'touch',
    ];
    missingCaveat.observations[0].caveat_ids = missingCaveat.observations[0].caveat_ids.filter(
      (caveat) => caveat !== 'combined_touch_denominator_disclosed',
    );
    expect(evaluate(missingCaveat).reason_codes).toEqual(['REQUIRED_CAVEAT_MISSING']);

    // Caveat without a disclosure -> a false claim.
    const falseClaim = P1();
    falseClaim.observations[0].caveat_ids = [
      ...falseClaim.observations[0].caveat_ids,
      'combined_touch_denominator_disclosed',
    ];
    expect(evaluate(falseClaim).reason_codes).toEqual(['INAPPLICABLE_CAVEAT_DECLARED']);

    // Same discipline for the supersession caveat.
    const staleSupersession = P1();
    staleSupersession.observations[0].caveat_ids = [
      ...staleSupersession.observations[0].caveat_ids,
      'snapshot_superseded',
    ];
    expect(evaluate(staleSupersession).reason_codes).toEqual(['INAPPLICABLE_CAVEAT_DECLARED']);
  });

  it('G3: no payload-invented sample rule validates on any value kind', () => {
    // The reviewer's exact attack: a count naming "payload_invented_rule".
    const invented = P2();
    invented.observations[0].metric.minimum_sample_rule_id = 'payload_invented_rule';
    expect(evaluate(invented).reason_codes).toEqual(['MINIMUM_SAMPLE_RULE_NOT_APPLICABLE']);

    // Even the real code-owned rule is a false claim on a metric it does not govern.
    const codeOwnedOnCount = P2();
    codeOwnedOnCount.observations[0].metric.minimum_sample_rule_id =
      RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID;
    expect(evaluate(codeOwnedOnCount).reason_codes).toEqual(['MINIMUM_SAMPLE_RULE_NOT_APPLICABLE']);

    // A rate declaring null has abandoned the rule that governs it.
    const rateNull = P1();
    rateNull.observations[0].metric.minimum_sample_rule_id = null;
    expect(evaluate(rateNull).reason_codes).toEqual(['MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED']);
  });

  it('G3-adjacent: material kind bounds the evidence class, conservative only', () => {
    const artifact = P1();
    artifact.observations[0].source.material_kind = 'derived_publication';
    artifact.observations[0].evidence_class = 'direct';
    artifact.observations[0].transform = null;
    expect(evaluate(artifact).reason_codes).toEqual(['MATERIAL_KIND_INCOMPATIBLE_WITH_EVIDENCE_CLASS']);
  });
});

describe('round five: rights_blocked must name the blocked action', () => {
  const P4 = () => mutable('positive', 'p4_rights_blocked_missing_component.json');

  function openManualP4(
    permissions: Partial<RbContactEvasionObservation['source']['permissions']>,
  ): RbContactEvasionObservationsV0 {
    const artifact = P4();
    const observation = artifact.observations[0];
    observation.source.access_class = 'open_and_ingestible';
    observation.source.acquisition_method = 'manual_citation';
    observation.source.permissions = {
      attribution: 'not_required',
      retention_and_reproduction: 'permitted',
      redistribution_and_display: 'permitted',
      automated_access: 'permitted',
      ...permissions,
    };
    return artifact;
  }

  it('the valid P4 gated/not-acquired case is preserved', () => {
    expect(evaluate(P4()).violations).toEqual([]);
  });

  it('H1: an automation restriction alone cannot excuse a manually acquirable measurement', () => {
    const artifact = openManualP4({ automated_access: 'prohibited' });
    expect(evaluate(artifact).reason_codes).toEqual(['MISSINGNESS_REASON_UNSUPPORTED']);
  });

  it('H2: a redistribution restriction governs downstream use, not absence', () => {
    const artifact = openManualP4({ redistribution_and_display: 'prohibited' });
    expect(evaluate(artifact).reason_codes).toEqual(['MISSINGNESS_REASON_UNSUPPORTED']);
  });

  it('a non-permitted retention disposition supports the claim on its own', () => {
    for (const retention of ['prohibited', 'unknown'] as const) {
      const artifact = openManualP4({ retention_and_reproduction: retention });
      expect(evaluate(artifact).violations).toEqual([]);
    }
  });

  it('a rights-restricting access class supports the claim only when acquisition did not occur', () => {
    const notAcquired = openManualP4({});
    notAcquired.observations[0].source.access_class = 'licensed_or_gated';
    notAcquired.observations[0].source.acquisition_method = 'not_acquired';
    expect(evaluate(notAcquired).violations).toEqual([]);

    // The same access label with a declared successful manual acquisition
    // proves nothing was blocked.
    const acquired = openManualP4({});
    acquired.observations[0].source.access_class = 'licensed_or_gated';
    expect(evaluate(acquired).reason_codes).toEqual(['MISSINGNESS_REASON_UNSUPPORTED']);
  });
});

describe('round six: a successful acquisition is never excused by its access label', () => {
  const P4 = () => mutable('positive', 'p4_rights_blocked_missing_component.json');
  const allPermitted: RbContactEvasionObservation['source']['permissions'] = {
    attribution: 'not_required',
    retention_and_reproduction: 'permitted',
    redistribution_and_display: 'permitted',
    automated_access: 'permitted',
  };

  function rightsRow(
    accessClass: (typeof rbContactEvasionSourceAccessClassSchema.options)[number],
    acquisition: RbContactEvasionAcquisitionMethod,
    permissions: Partial<RbContactEvasionObservation['source']['permissions']> = {},
  ): RbContactEvasionObservationsV0 {
    const artifact = P4();
    const observation = artifact.observations[0];
    observation.source.access_class = accessClass;
    observation.source.acquisition_method = acquisition;
    observation.source.permissions = { ...allPermitted, ...permissions };
    return artifact;
  }

  it('lock 1: gated + successful automated ingestion + all permitted -> unsupported', () => {
    expect(evaluate(rightsRow('licensed_or_gated', 'automated_ingestion')).reason_codes).toEqual([
      'MISSINGNESS_REASON_UNSUPPORTED',
    ]);
  });

  it('lock 2: unavailable + successful automated ingestion -> rejected', () => {
    expect(evaluate(rightsRow('unavailable', 'automated_ingestion')).reason_codes).toEqual([
      'MISSINGNESS_REASON_UNSUPPORTED',
    ]);
  });

  it('lock 3: unavailable + not acquired + source_unavailable -> valid', () => {
    const artifact = rightsRow('unavailable', 'not_acquired');
    artifact.observations[0].measurement.missingness_reason = 'source_unavailable';
    expect(evaluate(artifact).violations).toEqual([]);
  });

  it('lock 4: unavailable + not acquired + rights_blocked -> rejected', () => {
    expect(evaluate(rightsRow('unavailable', 'not_acquired')).reason_codes).toEqual([
      'MISSINGNESS_REASON_UNSUPPORTED',
    ]);
  });

  it('lock 5: unknown access + all permitted + rights_blocked -> rejected', () => {
    expect(evaluate(rightsRow('unknown', 'not_acquired')).reason_codes).toEqual([
      'MISSINGNESS_REASON_UNSUPPORTED',
    ]);
  });

  it('lock 6: licensed/gated or reference-only + not_acquired -> valid', () => {
    for (const accessClass of ['licensed_or_gated', 'reference_only'] as const) {
      expect(evaluate(rightsRow(accessClass, 'not_acquired')).violations).toEqual([]);
    }
  });

  it('lock 7: open access + retention prohibited or unknown -> valid', () => {
    for (const retention of ['prohibited', 'unknown'] as const) {
      const artifact = rightsRow('open_and_ingestible', 'manual_citation', {
        retention_and_reproduction: retention,
      });
      expect(evaluate(artifact).violations).toEqual([]);
    }
  });
});

describe('round seven: source_unavailable requires proven non-acquisition', () => {
  const P4 = () => mutable('positive', 'p4_rights_blocked_missing_component.json');

  function unavailableRow(
    acquisition: RbContactEvasionAcquisitionMethod,
  ): RbContactEvasionObservationsV0 {
    const artifact = P4();
    const observation = artifact.observations[0];
    observation.measurement.missingness_reason = 'source_unavailable';
    observation.source.access_class = 'unavailable';
    observation.source.acquisition_method = acquisition;
    observation.source.permissions = {
      attribution: 'not_required',
      retention_and_reproduction: 'permitted',
      redistribution_and_display: 'permitted',
      automated_access: 'permitted',
    };
    return artifact;
  }

  it.each(['automated_ingestion', 'manual_citation', 'synthetic_fixture'] as const)(
    'a successful "%s" acquisition cannot blame an unavailable source',
    (acquisition) => {
      expect(evaluate(unavailableRow(acquisition)).reason_codes).toEqual([
        'MISSINGNESS_REASON_UNSUPPORTED',
      ]);
    },
  );

  it('the unavailable + not_acquired + source_unavailable control stays valid', () => {
    expect(evaluate(unavailableRow('not_acquired')).violations).toEqual([]);
  });
});

describe('round eight: proven non-acquisition cannot hold a retained snapshot', () => {
  const P4 = () => mutable('positive', 'p4_rights_blocked_missing_component.json');
  const P5 = () => mutable('positive', 'p5_declared_snapshot_supersession.json');

  function snapshotAttack(
    reason: 'rights_blocked' | 'source_unavailable',
    accessClass: 'licensed_or_gated' | 'unavailable',
  ): RbContactEvasionObservationsV0 {
    const artifact = P4();
    const observation = artifact.observations[0];
    observation.measurement.missingness_reason = reason;
    observation.source.access_class = accessClass;
    observation.source.acquisition_method = 'not_acquired';
    observation.source.provenance_mode = 'snapshot';
    observation.source.content_digest = { algorithm: 'sha256', value: 'a'.repeat(64) };
    observation.source.permissions = {
      attribution: 'not_required',
      retention_and_reproduction: 'permitted',
      redistribution_and_display: 'prohibited',
      automated_access: 'permitted',
    };
    observation.caveat_ids = observation.caveat_ids.filter(
      (caveat) => caveat !== 'synthetic_fixture_value',
    );
    return artifact;
  }

  it('K1: rights_blocked + not_acquired + digest-pinned snapshot is incoherent', () => {
    expect(evaluate(snapshotAttack('rights_blocked', 'licensed_or_gated')).reason_codes).toEqual([
      'ACQUISITION_MODE_INCOHERENT',
    ]);
  });

  it('K2: source_unavailable + not_acquired + digest-pinned snapshot is incoherent', () => {
    expect(evaluate(snapshotAttack('source_unavailable', 'unavailable')).reason_codes).toEqual([
      'ACQUISITION_MODE_INCOHERENT',
    ]);
  });

  it('every admitted snapshot acquisition mode stays representable with its digest', () => {
    // automated_ingestion: P5 as committed.
    expect(evaluate(P5()).violations).toEqual([]);
    // manual_citation: the other admitted mode.
    const manual = P5();
    manual.observations[0].source.acquisition_method = 'manual_citation';
    manual.observations[0].source.acquisition_notes =
      'synthetic simulation of a manually cited snapshot';
    expect(evaluate(manual).violations).toEqual([]);
  });

  it('live provenance stays compatible with not_acquired (known but inaccessible source)', () => {
    const artifact = P4();
    const observation = artifact.observations[0];
    observation.source.provenance_mode = 'live';
    observation.caveat_ids = observation.caveat_ids.filter(
      (caveat) => caveat !== 'synthetic_fixture_value',
    );
    expect(evaluate(artifact).violations).toEqual([]);
  });
});

describe('cross-product: acquisition method x provenance mode x digest x measurement status', () => {
  const acquisitions: RbContactEvasionAcquisitionMethod[] = [
    'automated_ingestion',
    'manual_citation',
    'synthetic_fixture',
    'not_acquired',
  ];
  const provenances: RbContactEvasionProvenanceMode[] = ['live', 'snapshot', 'fixture'];
  const digests = ['none', 'sha256'] as const;
  const statuses = ['observed', 'missing'] as const;

  for (const acquisition of acquisitions) {
    for (const provenance of provenances) {
      for (const digest of digests) {
        for (const status of statuses) {
          const expected = new Set<RbContactEvasionReasonCode>();
          if (acquisition === 'synthetic_fixture' && provenance !== 'fixture') {
            expected.add('ACQUISITION_MODE_INCOHERENT');
          }
          if (acquisition === 'not_acquired' && provenance === 'snapshot') {
            expected.add('ACQUISITION_MODE_INCOHERENT');
          }
          if (acquisition === 'not_acquired' && status === 'observed') {
            expected.add('ACQUISITION_MODE_INCOHERENT');
          }
          if (provenance === 'snapshot' && digest === 'none') {
            expected.add('SNAPSHOT_WITHOUT_CONTENT_DIGEST');
          }
          const sorted = [...expected].sort();
          it(`${acquisition} / ${provenance} / digest=${digest} / ${status} -> ${
            sorted.length === 0 ? 'valid' : sorted.join(',')
          }`, () => {
            const observation = buildObservation('forced_missed_tackles_count', {
              acquisitionMethod: acquisition,
              provenanceMode: provenance,
            });
            observation.source.content_digest =
              digest === 'sha256' ? { algorithm: 'sha256', value: 'b'.repeat(64) } : null;
            if (status === 'missing') {
              observation.measurement = {
                status: 'missing',
                missingness_reason: 'not_measured',
                value: null,
                numerator: null,
                denominator: null,
                eligible_opportunities: null,
              };
            }
            const report = evaluate(buildArtifact([observation]));
            expect(report.shape_valid).toBe(true);
            expect(report.reason_codes).toEqual(sorted);
          });
        }
      }
    }
  }
});

describe('cross-product: access class x all acquisition modes for source_unavailable', () => {
  const accessClasses = rbContactEvasionSourceAccessClassSchema.options;
  const acquisitions: RbContactEvasionAcquisitionMethod[] = [
    'automated_ingestion',
    'manual_citation',
    'synthetic_fixture',
    'not_acquired',
  ];
  const permissionVariants = [
    ['all_permitted', 'permitted'],
    ['automation_prohibited', 'prohibited'],
  ] as const;

  for (const accessClass of accessClasses) {
    for (const acquisition of acquisitions) {
      for (const [variantName, automation] of permissionVariants) {
        const expected: RbContactEvasionReasonCode[] = [];
        if (acquisition === 'automated_ingestion' && automation !== 'permitted') {
          expected.push('ACQUISITION_MODE_PERMISSION_INCOMPATIBLE');
        }
        if (!(accessClass === 'unavailable' && acquisition === 'not_acquired')) {
          expected.push('MISSINGNESS_REASON_UNSUPPORTED');
        }
        expected.sort();
        it(`${accessClass} / ${acquisition} / ${variantName} -> ${
          expected.length === 0 ? 'valid' : expected.join(',')
        }`, () => {
          const artifact = mutable('positive', 'p4_rights_blocked_missing_component.json');
          const observation = artifact.observations[0];
          observation.measurement.missingness_reason = 'source_unavailable';
          observation.source.access_class = accessClass;
          observation.source.acquisition_method = acquisition;
          observation.source.permissions = {
            attribution: 'not_required',
            retention_and_reproduction: 'permitted',
            redistribution_and_display: 'permitted',
            automated_access: automation,
          };
          const report = evaluate(artifact);
          expect(report.shape_valid).toBe(true);
          expect(report.reason_codes).toEqual(expected);
        });
      }
    }
  }
});

describe('cross-product: access class x all acquisition modes x permission variant for rights_blocked', () => {
  const accessClasses = rbContactEvasionSourceAccessClassSchema.options;
  const acquisitions: RbContactEvasionAcquisitionMethod[] = [
    'automated_ingestion',
    'manual_citation',
    'synthetic_fixture',
    'not_acquired',
  ];
  const permissionVariants = [
    ['all_permitted', {}],
    ['retention_prohibited', { retention_and_reproduction: 'prohibited' }],
    ['retention_unknown', { retention_and_reproduction: 'unknown' }],
    ['redistribution_prohibited', { redistribution_and_display: 'prohibited' }],
    ['automation_prohibited', { automated_access: 'prohibited' }],
  ] as const;

  for (const accessClass of accessClasses) {
    for (const acquisition of acquisitions) {
      for (const [variantName, variant] of permissionVariants) {
        const retention =
          (variant as { retention_and_reproduction?: string }).retention_and_reproduction ??
          'permitted';
        const automation =
          (variant as { automated_access?: string }).automated_access ?? 'permitted';
        // Expected code set, from the action-sensitive model:
        const expected: RbContactEvasionReasonCode[] = [];
        if (acquisition === 'automated_ingestion' && automation !== 'permitted') {
          expected.push('ACQUISITION_MODE_PERMISSION_INCOMPATIBLE');
        }
        const accessSupports =
          acquisition === 'not_acquired' &&
          (accessClass === 'licensed_or_gated' || accessClass === 'reference_only');
        if (!(retention !== 'permitted' || accessSupports)) {
          expected.push('MISSINGNESS_REASON_UNSUPPORTED');
        }
        expected.sort();
        it(`${accessClass} / ${acquisition} / ${variantName} -> ${
          expected.length === 0 ? 'valid' : expected.join(',')
        }`, () => {
          const artifact = mutable('positive', 'p4_rights_blocked_missing_component.json');
          const observation = artifact.observations[0];
          observation.source.access_class = accessClass;
          observation.source.acquisition_method = acquisition;
          // synthetic acquisition requires fixture provenance; P4 already is.
          observation.source.permissions = {
            attribution: 'not_required',
            retention_and_reproduction: 'permitted',
            redistribution_and_display: 'permitted',
            automated_access: 'permitted',
            ...variant,
          };
          const report = evaluate(artifact);
          expect(report.shape_valid).toBe(true);
          expect(report.reason_codes).toEqual(expected);
        });
      }
    }
  }
});

describe('cross-product: material kind x evidence class', () => {
  const materials = ['measured_observation', 'derived_publication', 'editorial_opinion'] as const;
  const evidences: RbContactEvasionEvidenceClass[] = [
    'direct',
    'normalized',
    'derived',
    'external_opinion',
  ];
  const allowed: Record<string, readonly RbContactEvasionEvidenceClass[]> = {
    measured_observation: ['direct', 'normalized', 'derived', 'external_opinion'],
    derived_publication: ['normalized', 'derived', 'external_opinion'],
    editorial_opinion: ['external_opinion'],
  };
  for (const material of materials) {
    for (const evidence of evidences) {
      const ok = allowed[material].includes(evidence);
      it(`${material} x ${evidence} -> ${ok ? 'valid' : 'rejected semantically'}`, () => {
        const observation = buildObservation('forced_missed_tackles_count', {
          evidenceClass: evidence,
        });
        observation.source.material_kind = material;
        const report = evaluate(buildArtifact([observation]));
        expect(report.shape_valid).toBe(true);
        if (ok) {
          expect(report.violations).toEqual([]);
        } else {
          expect(report.reason_codes).toEqual(
            material === 'editorial_opinion'
              ? ['EXTERNAL_OPINION_LABELED_AS_OBSERVATION']
              : ['MATERIAL_KIND_INCOMPATIBLE_WITH_EVIDENCE_CLASS'],
          );
        }
      });
    }
  }
});

describe('cross-product: missingness reason x eligible count x source state', () => {
  const reasons = [
    'rights_blocked',
    'source_unavailable',
    'below_minimum_sample',
    'not_measured',
    'definition_incompatible',
  ] as const;

  function missingRow(
    reason: (typeof reasons)[number],
    eligible: number | null,
  ): RbContactEvasionObservationsV0 {
    const observation = buildObservation('forced_missed_tackles_per_rush_attempt', {
      windowCompleteness: 'multi_week',
      gamesIncluded: 2,
    });
    observation.measurement = {
      status: 'missing',
      missingness_reason: reason,
      value: null,
      numerator: null,
      denominator: null,
      eligible_opportunities: eligible,
    };
    // Give each reason a supporting source state so the sweep isolates the
    // eligible-count dimension. rights_blocked support requires the declared
    // acquisition state to prove acquisition did not occur.
    if (reason === 'rights_blocked') {
      observation.source.access_class = 'licensed_or_gated';
      observation.source.acquisition_method = 'not_acquired';
    } else if (reason === 'source_unavailable') {
      observation.source.access_class = 'unavailable';
      observation.source.acquisition_method = 'not_acquired';
    }
    return buildArtifact([observation]);
  }

  for (const reason of reasons) {
    for (const eligible of [null, 12, 203] as const) {
      let expected: RbContactEvasionReasonCode[];
      if (reason === 'below_minimum_sample') {
        // multi_week threshold is 20: 12 proves the claim, null cannot, 203 disproves it.
        expected = eligible === 12 ? [] : ['BELOW_MINIMUM_SAMPLE_UNPROVABLE'];
      } else if (eligible === null) {
        expected = [];
      } else if (reason === 'rights_blocked' || reason === 'source_unavailable') {
        // A retained count under a not_acquired source is doubly wrong: the
        // count is inadmissible for the reason AND incoherent with the
        // declared non-acquisition.
        expected = ['ACQUISITION_MODE_INCOHERENT', 'MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE'];
      } else {
        expected = ['MISSINGNESS_ELIGIBLE_COUNT_INADMISSIBLE'];
      }
      it(`${reason} with eligible=${JSON.stringify(eligible)} -> ${
        expected.length === 0 ? 'valid' : expected.join(',')
      }`, () => {
        const report = evaluate(missingRow(reason, eligible));
        expect(report.shape_valid).toBe(true);
        expect(report.reason_codes).toEqual(expected);
      });
    }
  }
});

// ---------------------------------------------------------------------------
// Cross-product adversarial suites: invalid combinations must fail at the
// public evaluator for a semantic reason, not merely schema parsing.
// ---------------------------------------------------------------------------

describe('cross-product: every metric x every opportunity class', () => {
  const metricIds = Object.keys(RB_CONTACT_EVASION_METRIC_DICTIONARY);
  const classes: RbContactEvasionOpportunityClass[] = [
    'rushing',
    'receiving',
    'combined_rushing_receiving',
    'athletic_testing',
  ];

  for (const metricId of metricIds) {
    const descriptor = RB_CONTACT_EVASION_METRIC_DICTIONARY[metricId];
    for (const opportunityClass of classes) {
      const allowed = descriptor.allowed_opportunity_classes.includes(opportunityClass);
      const evidences = descriptor.mechanisms.length > 0;
      const label = `${metricId} under ${opportunityClass} -> ${
        evidences && allowed ? 'valid' : 'rejected semantically'
      }`;
      it(label, () => {
        const artifact = buildArtifact([
          buildObservation(metricId, { opportunityClass }),
        ]);
        const report = evaluate(artifact);
        expect(report.shape_valid).toBe(true);
        if (!evidences) {
          // Components and inadmissible summaries can never be row evidence.
          expect(report.valid).toBe(false);
          expect(report.reason_codes).toContain('MECHANISM_METRIC_BINDING_VIOLATION');
        } else if (allowed) {
          expect(report.violations).toEqual([]);
        } else {
          expect(report.valid).toBe(false);
          expect(report.reason_codes).toContain('METRIC_OPPORTUNITY_CLASS_INCOMPATIBLE');
        }
      });
    }
  }
});

describe('cross-product: every value kind x component presence', () => {
  const representatives: ReadonlyArray<[string, 'rate' | 'count' | 'duration_seconds' | 'speed_mph']> = [
    ['forced_missed_tackles_per_rush_attempt', 'rate'],
    ['forced_missed_tackles_count', 'count'],
    ['forty_yard_dash_seconds', 'duration_seconds'],
    ['verified_max_game_speed_mph', 'speed_mph'],
  ];
  const presences = ['none', 'numerator_only', 'denominator_only', 'both'] as const;

  for (const [metricId, valueKind] of representatives) {
    for (const presence of presences) {
      const isRate = valueKind === 'rate';
      const expectedValid = isRate ? presence === 'both' : presence === 'none';
      it(`${valueKind} metric with components "${presence}" -> ${expectedValid ? 'valid' : 'rejected semantically'}`, () => {
        const observation = buildObservation(metricId);
        const rateComponents = {
          numerator: { metric_id: 'forced_missed_tackles_count', value: 62 },
          denominator: {
            metric_id: 'rush_attempts',
            value: 203,
            opportunity_type: 'rush_attempt' as const,
          },
        };
        const declared = RB_CONTACT_EVASION_METRIC_DICTIONARY[metricId];
        const numerator = isRate
          ? { metric_id: declared.numerator_metric_id!, value: 26 }
          : rateComponents.numerator;
        const denominator = isRate
          ? {
              metric_id: declared.denominator_metric_id!,
              value: 203,
              opportunity_type: declared.denominator_opportunity_type!,
            }
          : rateComponents.denominator;
        observation.measurement.numerator =
          presence === 'numerator_only' || presence === 'both' ? numerator : null;
        observation.measurement.denominator =
          presence === 'denominator_only' || presence === 'both' ? denominator : null;
        if (isRate && presence === 'both') {
          observation.measurement.value = rbContactEvasionExpectedRate(26, 203);
          observation.measurement.eligible_opportunities = 203;
        }
        const report = evaluate(buildArtifact([observation]));
        expect(report.shape_valid).toBe(true);
        if (expectedValid) {
          expect(report.violations).toEqual([]);
        } else {
          expect(report.valid).toBe(false);
          // A foreign denominator may additionally trip class-compatibility
          // rules (e.g. a rush-attempt denominator under athletic_testing);
          // the non-rate component rule must fire regardless.
          expect(report.reason_codes).toContain(
            isRate ? 'RATE_MISSING_DENOMINATOR' : 'RATE_COMPONENTS_ON_NON_RATE_METRIC',
          );
          expect(report.reason_codes).not.toContain('SCHEMA_SHAPE_INVALID');
        }
      });
    }
  }
});

describe('cross-product: rate denominator x eligible-opportunity equality', () => {
  for (const [denominatorValue, eligible, expectedValid] of [
    [203, 203, true],
    [203, 202, false],
    [5, 203, false],
    [50, 40, false],
  ] as const) {
    it(`denominator ${denominatorValue} with eligible ${eligible} -> ${expectedValid ? 'valid' : 'rejected'}`, () => {
      const observation = buildObservation('forced_missed_tackles_per_rush_attempt');
      observation.measurement.denominator!.value = denominatorValue;
      observation.measurement.value = rbContactEvasionExpectedRate(26, denominatorValue);
      observation.measurement.eligible_opportunities = eligible;
      const report = evaluate(buildArtifact([observation]));
      if (expectedValid) {
        expect(report.violations).toEqual([]);
      } else {
        expect(report.reason_codes).toContain('ELIGIBLE_OPPORTUNITIES_DENOMINATOR_MISMATCH');
      }
    });
  }
});

describe('cross-product: numeric domains per metric', () => {
  it('rejects negative, fractional-where-integer, and non-finite event counts', () => {
    for (const badValue of [-1, 62.5, Number.POSITIVE_INFINITY]) {
      const observation = buildObservation('forced_missed_tackles_count');
      observation.measurement.value = badValue;
      const report = evaluate(buildArtifact([observation]));
      expect(report.shape_valid).toBe(true);
      expect(report.reason_codes).toContain('MEASUREMENT_NUMERIC_DOMAIN_VIOLATION');
    }
  });

  it('rejects zero and negative durations under a positive domain', () => {
    for (const badValue of [0, -4.55]) {
      const observation = buildObservation('forty_yard_dash_seconds');
      observation.measurement.value = badValue;
      const report = evaluate(buildArtifact([observation]));
      expect(report.reason_codes).toContain('MEASUREMENT_NUMERIC_DOMAIN_VIOLATION');
    }
  });

  it('accepts zero for a non-negative count and fractional yardage totals', () => {
    const zeroCount = buildObservation('forced_missed_tackles_count');
    zeroCount.measurement.value = 0;
    expect(evaluate(buildArtifact([zeroCount])).violations).toEqual([]);
  });

  it('applies each component metric domain to numerator and denominator values', () => {
    const observation = buildObservation('forced_missed_tackles_per_rush_attempt');
    observation.measurement.numerator!.value = 26.5;
    observation.measurement.value = rbContactEvasionExpectedRate(26.5, 203);
    const report = evaluate(buildArtifact([observation]));
    expect(report.reason_codes).toContain('MEASUREMENT_NUMERIC_DOMAIN_VIOLATION');
  });
});

describe('cross-product: every nullable source-clock combination with total ordering', () => {
  // Canonical chain positions: observed, generated, available, then retrieved.
  const times = [
    '2025-01-06T04:00:00+00:00',
    '2025-01-07T12:00:00+00:00',
    '2025-01-08T09:00:00+00:00',
    '2025-01-09T15:30:00+00:00',
  ];
  const names = ['source_observed_at', 'source_generated_at', 'source_available_at'] as const;

  for (let mask = 0; mask < 8; mask += 1) {
    const present = names.filter((_, index) => (mask & (1 << index)) !== 0);
    const label = present.length > 0 ? present.join('+') : 'no source clocks';

    const applyPattern = (
      observation: RbContactEvasionObservation,
      values: readonly string[],
    ): void => {
      let cursor = 0;
      for (const name of names) {
        if (present.includes(name)) {
          observation.clocks[name] = values[cursor];
          observation.clock_provenance[name] = 'source_supplied';
          cursor += 1;
        } else {
          observation.clocks[name] = null;
          observation.clock_provenance[name] = 'not_supplied_by_source';
        }
      }
      observation.clocks.retrieved_at = values[cursor];
    };

    it(`${label}: in-order instants validate`, () => {
      const observation = buildObservation('forced_missed_tackles_count');
      applyPattern(observation, times.slice(0, present.length + 1));
      expect(evaluate(buildArtifact([observation])).violations).toEqual([]);
    });

    // Reverse each consecutive existing pair in the chain (including into
    // retrieved_at) and require a semantic ordering rejection.
    for (let pair = 0; pair < present.length; pair += 1) {
      it(`${label}: reversal at existing pair ${pair} is rejected`, () => {
        const observation = buildObservation('forced_missed_tackles_count');
        const values = [...times.slice(0, present.length + 1)];
        [values[pair], values[pair + 1]] = [values[pair + 1], values[pair]];
        applyPattern(observation, values);
        const report = evaluate(buildArtifact([observation]));
        expect(report.shape_valid).toBe(true);
        expect(report.reason_codes).toContain('CLOCK_ORDER_INVALID');
      });
    }
  }
});

describe('cross-product: evidence class x acquisition mode x permission dispositions', () => {
  const evidenceClasses: RbContactEvasionEvidenceClass[] = [
    'direct',
    'normalized',
    'derived',
    'external_opinion',
  ];
  const modes: RbContactEvasionAcquisitionMethod[] = [
    'automated_ingestion',
    'manual_citation',
    'synthetic_fixture',
    'not_acquired',
  ];
  const dispositions = ['permitted', 'prohibited', 'unknown'] as const;

  for (const evidenceClass of evidenceClasses) {
    for (const mode of modes) {
      for (const retention of dispositions) {
        for (const automation of dispositions) {
          // A stored exact value, open access, attribution satisfied. Expected
          // rejections derive from the invariant matrix, dimension H.
          const expected = new Set<RbContactEvasionReasonCode>();
          if (retention !== 'permitted') {
            expected.add('STORED_EXACT_VALUE_REQUIRES_RETENTION');
          }
          if (mode === 'automated_ingestion' && automation !== 'permitted') {
            expected.add('ACQUISITION_MODE_PERMISSION_INCOMPATIBLE');
          }
          if (mode === 'not_acquired') {
            expected.add('ACQUISITION_MODE_INCOHERENT');
          }
          const label = `${evidenceClass} / ${mode} / retention=${retention} / automation=${automation} -> ${
            expected.size === 0 ? 'valid' : [...expected].sort().join(',')
          }`;
          it(label, () => {
            const observation = buildObservation('forced_missed_tackles_count', {
              evidenceClass,
              acquisitionMethod: mode,
              provenanceMode: mode === 'synthetic_fixture' ? 'fixture' : 'live',
              retention,
              automation,
            });
            if (mode !== 'synthetic_fixture') {
              observation.caveat_ids = observation.caveat_ids.filter(
                (caveat) => caveat !== 'synthetic_fixture_value',
              );
            }
            const report = evaluate(buildArtifact([observation]));
            expect(report.shape_valid).toBe(true);
            expect(report.reason_codes).toEqual([...expected].sort());
          });
        }
      }
    }
  }
});

describe('cross-product: artifact position x provenance mode x minimum-rule authority', () => {
  const positions: RbContactEvasionArtifactPosition[] = ['fixture_only', 'candidate', 'promoted'];
  const provenances: RbContactEvasionProvenanceMode[] = ['live', 'snapshot', 'fixture'];

  for (const position of positions) {
    for (const provenance of provenances) {
      for (const kind of ['count', 'rate'] as const) {
        const expected = new Set<RbContactEvasionReasonCode>();
        if (provenance === 'fixture' && position !== 'fixture_only') {
          expected.add('FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION');
        }
        if (kind === 'rate' && position !== 'fixture_only') {
          expected.add('MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION');
        }
        if (position === 'promoted') {
          expected.add('PROMOTED_POSITION_REQUIRES_PROMOTION_GATE');
        }
        const label = `${position} / ${provenance} / ${kind} -> ${
          expected.size === 0 ? 'valid' : [...expected].sort().join(',')
        }`;
        it(label, () => {
          const metricId =
            kind === 'rate'
              ? 'forced_missed_tackles_per_rush_attempt'
              : 'forced_missed_tackles_count';
          const observation = buildObservation(metricId, { provenanceMode: provenance });
          const report = evaluate(buildArtifact([observation], position));
          expect(report.shape_valid).toBe(true);
          expect(report.reason_codes).toEqual([...expected].sort());
        });
      }
    }
  }
});

describe('cross-product: window completeness x week presence x opportunity class', () => {
  const completenesses: RbContactEvasionWindowCompleteness[] = [
    'single_week',
    'multi_week',
    'partial_season',
    'full_season',
  ];

  // Game class: week must be present iff single_week; observed game counts per window.
  for (const completeness of completenesses) {
    for (const week of [null, 12] as const) {
      const expectedValid = completeness === 'single_week' ? week !== null : week === null;
      it(`rushing / ${completeness} / week=${JSON.stringify(week)} -> ${
        expectedValid ? 'valid' : 'rejected'
      }`, () => {
        const observation = buildObservation('forced_missed_tackles_count', {
          windowCompleteness: completeness,
          week,
        });
        const report = evaluate(buildArtifact([observation]));
        expect(report.shape_valid).toBe(true);
        if (expectedValid) {
          expect(report.violations).toEqual([]);
        } else {
          expect(report.reason_codes).toEqual(['WINDOW_SCOPE_INCOHERENT']);
        }
      });
    }
  }

  // Athletic testing: only single_week + week null + games 0 is coherent.
  for (const completeness of completenesses) {
    const expectedValid = completeness === 'single_week';
    it(`athletic_testing / ${completeness} -> ${expectedValid ? 'valid' : 'rejected'}`, () => {
      const observation = buildObservation('forty_yard_dash_seconds', {
        windowCompleteness: completeness,
        week: null,
        gamesIncluded: 0,
      });
      const report = evaluate(buildArtifact([observation]));
      expect(report.shape_valid).toBe(true);
      if (expectedValid) {
        expect(report.violations).toEqual([]);
      } else {
        expect(report.reason_codes).toEqual(['WINDOW_SCOPE_INCOHERENT']);
      }
    });
  }

  it('observed game windows reject incoherent game counts per completeness', () => {
    for (const [completeness, games] of [
      ['single_week', 0],
      ['single_week', 2],
      ['multi_week', 1],
      ['partial_season', 0],
      ['full_season', 0],
    ] as const) {
      const observation = buildObservation('forced_missed_tackles_count', {
        windowCompleteness: completeness,
        week: completeness === 'single_week' ? 12 : null,
        gamesIncluded: games,
      });
      const report = evaluate(buildArtifact([observation]));
      expect(report.reason_codes).toEqual(['WINDOW_SCOPE_INCOHERENT']);
    }
  });
});

// ---------------------------------------------------------------------------
// Structural invariants
// ---------------------------------------------------------------------------

describe('rb_contact_evasion_observations_v0 structural invariants', () => {
  it('closes the mechanism universe to the five named mechanisms', () => {
    expect(rbContactEvasionMechanismIdSchema.options).toEqual([
      'speed',
      'agility_change_of_direction',
      'contact_avoidance',
      'contact_survival',
      'explosiveness',
    ]);
    expect(rbContactEvasionMechanismIdSchema.safeParse('elusiveness').success).toBe(false);
  });

  it('closes the evidence and source-access vocabularies', () => {
    expect(rbContactEvasionEvidenceClassSchema.options).toEqual([
      'direct',
      'normalized',
      'derived',
      'external_opinion',
    ]);
    expect(rbContactEvasionSourceAccessClassSchema.options).toEqual([
      'open_and_ingestible',
      'public_but_terms_constrained',
      'licensed_or_gated',
      'reference_only',
      'unavailable',
      'unknown',
    ]);
  });

  it('owns a complete, coherent descriptor for every metric', () => {
    for (const [metricId, descriptor] of Object.entries(RB_CONTACT_EVASION_METRIC_DICTIONARY)) {
      expect(metricId).toMatch(/^[a-z0-9_]+$/);
      // A metric that could evidence two mechanisms would let evidence for one
      // silently satisfy another. None may.
      expect(descriptor.mechanisms.length).toBeLessThanOrEqual(1);
      expect(descriptor.allowed_opportunity_classes.length).toBeGreaterThan(0);
      expect(descriptor.canonical_inclusion_rules.length).toBeGreaterThan(0);
      for (const caveat of descriptor.required_caveat_ids) {
        expect(rbContactEvasionCaveatIdSchema.safeParse(caveat).success).toBe(true);
      }
      if (descriptor.value_kind === 'rate') {
        expect(descriptor.numerator_metric_id).not.toBeNull();
        expect(descriptor.denominator_metric_id).not.toBeNull();
        expect(descriptor.denominator_opportunity_type).not.toBeNull();
        expect(
          RB_CONTACT_EVASION_METRIC_DICTIONARY[descriptor.numerator_metric_id!],
        ).toBeDefined();
        expect(
          RB_CONTACT_EVASION_METRIC_DICTIONARY[descriptor.denominator_metric_id!],
        ).toBeDefined();
      } else {
        expect(descriptor.numerator_metric_id).toBeNull();
        expect(descriptor.denominator_metric_id).toBeNull();
        expect(descriptor.denominator_opportunity_type).toBeNull();
      }
    }
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.yards_per_carry.mechanisms).toEqual([]);
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.longest_rush_yards.mechanisms).toEqual([]);
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.rush_attempts.mechanisms).toEqual([]);
    // Testing metrics can never describe game opportunity.
    expect(
      RB_CONTACT_EVASION_METRIC_DICTIONARY.forty_yard_dash_seconds.allowed_opportunity_classes,
    ).toEqual(['athletic_testing']);
  });

  it('keeps incompatible_with relationships symmetric', () => {
    expect(findRbContactEvasionIncompatibilityAsymmetries()).toEqual([]);
    for (const [left, rights] of Object.entries(RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES)) {
      for (const right of rights) {
        expect(RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES[right]?.has(left)).toBe(true);
      }
    }
    expect(
      findRbContactEvasionIncompatibilityAsymmetries({ a: new Set(['b']), b: new Set() }),
    ).toEqual([{ from: 'a', to: 'b' }]);
  });

  it('rejects unknown fields at every level rather than ignoring them', () => {
    const base = loadFixture(
      'positive',
      'p1_complete_derived_explosiveness_rate.json',
    ) as Record<string, unknown>;
    const rootReport = evaluate({ ...base, elusiveness_score: 0.9 });
    expect(rootReport.shape_valid).toBe(false);
    expect(rootReport.reason_codes).toContain('UNKNOWN_FIELD_PRESENT');

    for (const mutate of [
      (artifact: RbContactEvasionObservationsV0) => {
        (artifact.observations[0] as unknown as Record<string, unknown>).elusiveness_grade = 'A';
      },
      (artifact: RbContactEvasionObservationsV0) => {
        (artifact.observations[0].measurement as unknown as Record<string, unknown>).percentile =
          0.91;
      },
      (artifact: RbContactEvasionObservationsV0) => {
        (
          artifact.observations[0].source.permissions as unknown as Record<string, unknown>
        ).sublicensing = 'permitted';
      },
      (artifact: RbContactEvasionObservationsV0) => {
        (
          artifact.observations[0].clock_provenance as unknown as Record<string, unknown>
        ).extra_clock = 'retrieval_clock';
      },
    ]) {
      const artifact = mutable('positive', 'p1_complete_derived_explosiveness_rate.json');
      mutate(artifact);
      const report = evaluate(artifact);
      expect(report.shape_valid).toBe(false);
      expect(report.reason_codes).toContain('UNKNOWN_FIELD_PRESENT');
    }
  });

  it('reports shape failure distinctly from contract rejection', () => {
    const shapeReport = evaluate({ artifact_id: 'wrong' });
    expect(shapeReport.shape_valid).toBe(false);
    expect(shapeReport.valid).toBe(false);
    const contractReport = evaluate(loadFixture('negative', 'n01_rate_missing_denominator.json'));
    expect(contractReport.shape_valid).toBe(true);
    expect(contractReport.valid).toBe(false);
  });

  it('distinguishes a missing value from a missing reason from an empty observation', () => {
    const noReason = mutable('positive', 'p4_rights_blocked_missing_component.json');
    noReason.observations[0].measurement.missingness_reason = null;
    expect(evaluate(noReason).reason_codes).toEqual(['MISSINGNESS_REASON_ABSENT']);

    const observedWithoutValue = mutable('positive', 'p2_raw_count_without_denominator.json');
    observedWithoutValue.observations[0].measurement.value = null;
    expect(evaluate(observedWithoutValue).reason_codes).toEqual(['OBSERVED_COMPONENT_MISSING_VALUE']);
  });

  it('exposes no score, composite, grade, ranking, or fantasy vocabulary anywhere', () => {
    const forbidden =
      /score|composite|grade|ranking|rank_|percentile|tier|rating|fantasy|overall|elite|neutral_default/i;
    const schema = JSON.parse(readFileSync(SCHEMA_PATH, 'utf-8')) as unknown;

    const offenders: string[] = [];
    const walkPropertyNames = (node: unknown, trail: string): void => {
      if (Array.isArray(node)) {
        node.forEach((item, index) => walkPropertyNames(item, `${trail}[${index}]`));
        return;
      }
      if (node === null || typeof node !== 'object') {
        return;
      }
      for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
        if (key === 'properties' && value !== null && typeof value === 'object') {
          for (const propertyName of Object.keys(value as Record<string, unknown>)) {
            if (forbidden.test(propertyName)) {
              offenders.push(`${trail}.${propertyName}`);
            }
          }
        }
        walkPropertyNames(value, `${trail}.${key}`);
      }
    };
    walkPropertyNames(schema, '$');
    expect(offenders).toEqual([]);

    for (const enumSchema of [
      rbContactEvasionMechanismIdSchema,
      rbContactEvasionEvidenceClassSchema,
      rbContactEvasionSourceAccessClassSchema,
      rbContactEvasionCaveatIdSchema,
      rbContactEvasionReasonCodeSchema,
    ]) {
      for (const option of enumSchema.options) {
        expect(option).not.toMatch(/score|composite|grade|percentile|fantasy|elite/i);
      }
    }
  });

  it('mirrors the contract vocabularies exactly in the committed JSON schema', () => {
    const schema = JSON.parse(readFileSync(SCHEMA_PATH, 'utf-8')) as {
      properties: Record<string, { const?: string }>;
      $defs: Record<string, { enum?: string[] }>;
    };
    expect(schema.properties.artifact_id.const).toBe(RB_CONTACT_EVASION_ARTIFACT_ID);
    expect(schema.properties.schema_version.const).toBe(RB_CONTACT_EVASION_SCHEMA_VERSION);
    expect(schema.$defs.mechanismId.enum).toEqual(rbContactEvasionMechanismIdSchema.options);
    expect(schema.$defs.evidenceClass.enum).toEqual(rbContactEvasionEvidenceClassSchema.options);
    expect(schema.$defs.sourceAccessClass.enum).toEqual(
      rbContactEvasionSourceAccessClassSchema.options,
    );
    expect(schema.$defs.provenanceMode.enum).toEqual(['live', 'snapshot', 'fixture']);
    expect(schema.$defs.caveatId.enum).toEqual(rbContactEvasionCaveatIdSchema.options);
    expect(schema.$defs.acquisitionMethod.enum).toEqual([
      'automated_ingestion',
      'manual_citation',
      'synthetic_fixture',
      'not_acquired',
    ]);
    expect(schema.$defs.clockProvenance.enum).toEqual([
      'football_window',
      'source_supplied',
      'not_supplied_by_source',
      'retrieval_clock',
      'artifact_build_clock',
    ]);
  });

  it('rejects an unregistered metric id instead of admitting it by default', () => {
    const artifact = mutable('positive', 'p2_raw_count_without_denominator.json');
    artifact.observations[0].metric.metric_id = 'elusiveness_index';
    const report = evaluate(artifact);
    expect(report.shape_valid).toBe(true);
    expect(report.reason_codes).toContain('UNKNOWN_METRIC_ID');
  });

  it('keeps the minimum-sample rule fixture-only in its own declaration', () => {
    expect(RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.rule_id).toBe(
      RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID,
    );
    expect(RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.authority).toBe('fixture_only_placeholder');
  });

  it('every reason code used by the corpus is in the closed reason-code enum', () => {
    for (const [, , code] of ALL_NEGATIVE) {
      expect(rbContactEvasionReasonCodeSchema.safeParse(code).success).toBe(true);
    }
  });
});
