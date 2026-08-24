import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

// Imported through the package barrel on purpose: these are the guarantees the
// published surface promises, so they must be proven at that boundary and not
// against internal helpers.
import {
  RB_CONTACT_EVASION_ARTIFACT_ID,
  RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES,
  RB_CONTACT_EVASION_METRIC_REGISTRY,
  RB_CONTACT_EVASION_SCHEMA_VERSION,
  RbContactEvasionContractError,
  evaluateRbContactEvasionObservationsV0,
  findRbContactEvasionIncompatibilityAsymmetries,
  isRbContactEvasionObservationsV0,
  rbContactEvasionEvidenceClassSchema,
  rbContactEvasionMechanismIdSchema,
  rbContactEvasionReasonCodeSchema,
  rbContactEvasionSourceAccessClassSchema,
  summarizeRbContactEvasionMechanismCoverage,
  validateRbContactEvasionObservationsV0,
  type RbContactEvasionObservationsV0,
  type RbContactEvasionReasonCode,
} from '../src/index.js';

const FIXTURE_ROOT = path.resolve('test/fixtures/rb_contact_evasion');
const SCHEMA_PATH = path.resolve('schemas/rb_contact_evasion_observations_v0.schema.json');
const BUCKY_GSIS_ID = '00-0039361';

function loadFixture(kind: 'positive' | 'negative', name: string): unknown {
  return JSON.parse(readFileSync(path.join(FIXTURE_ROOT, kind, name), 'utf-8'));
}

function fixtureNames(kind: 'positive' | 'negative'): string[] {
  return readdirSync(path.join(FIXTURE_ROOT, kind))
    .filter((name) => name.endsWith('.json'))
    .sort();
}

/** The P1–P7 corpus required by TIBER-Data #234 Slice A. */
const POSITIVE_FIXTURES: ReadonlyArray<[string, string]> = [
  ['P1 complete derived explosiveness rate', 'p1_complete_derived_explosiveness_rate.json'],
  ['P2 raw count without denominator', 'p2_raw_count_without_denominator.json'],
  ['P3 correctly classified historical testing', 'p3_historical_testing_classified.json'],
  ['P4 rights-blocked missing component', 'p4_rights_blocked_missing_component.json'],
  ['P5 declared snapshot supersession', 'p5_declared_snapshot_supersession.json'],
  ['P6 weekly and season windows coexisting', 'p6_weekly_and_season_windows_coexist.json'],
  ['P7 Bucky receipt remains partial', 'p7_bucky_receipt_remains_partial.json'],
];

/**
 * The N1–N15 corpus. Each entry pins the fixture to the ONE reason code it must
 * be rejected by — not merely "it was rejected".
 */
const NEGATIVE_FIXTURES: ReadonlyArray<[string, string, RbContactEvasionReasonCode]> = [
  ['N1 missing denominator', 'n01_rate_missing_denominator.json', 'RATE_MISSING_DENOMINATOR'],
  [
    'N2 unsupported touches denominator',
    'n02_denominator_unsupported_by_source.json',
    'DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE',
  ],
  [
    'N3 silently combined rushing and receiving',
    'n03_rushing_receiving_silently_combined.json',
    'RUSHING_RECEIVING_SILENTLY_COMBINED',
  ],
  [
    'N4 definition drift',
    'n04_metric_definition_drift.json',
    'METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID',
  ],
  [
    'N5 reference-only source marked promotable and direct',
    'n05_reference_only_source_overclaimed.json',
    'RESTRICTED_SOURCE_ACCESS_OVERCLAIMED',
  ],
  [
    'N6 external opinion labeled as observation',
    'n06_external_opinion_labeled_observation.json',
    'EXTERNAL_OPINION_LABELED_AS_OBSERVATION',
  ],
  [
    'N7 partial/full-season comparison without disclosure',
    'n07_partial_full_window_comparison_undisclosed.json',
    'WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED',
  ],
  [
    'N8 below-minimum rate',
    'n08_below_minimum_sample_rate_emitted.json',
    'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
  ],
  ['N9 wrong cohort position or season type', 'n09_cohort_scope_mismatch.json', 'COHORT_SCOPE_MISMATCH'],
  [
    'N10 retrieval clock substituted for source clock',
    'n10_retrieval_clock_substituted.json',
    'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
  ],
  [
    'N11 unresolved canonical identity',
    'n11_canonical_identity_unresolved.json',
    'CANONICAL_IDENTITY_UNRESOLVED',
  ],
  [
    'N12 misclassified 40-yard dash, long gain, or yards per carry',
    'n12_mechanism_metric_binding_violation.json',
    'MECHANISM_METRIC_BINDING_VIOLATION',
  ],
  [
    'N13 default value supplied for a missing component',
    'n13_default_value_for_missing_component.json',
    'MISSING_COMPONENT_CARRIES_VALUE',
  ],
  [
    'N14 transform consuming incompatible metrics',
    'n14_incompatible_transform_inputs.json',
    'INCOMPATIBLE_METRIC_TRANSFORM_INPUT',
  ],
  [
    'N15 fixture provenance in candidate position',
    'n15_fixture_provenance_in_candidate_position.json',
    'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION',
  ],
];

describe('rb_contact_evasion_observations_v0 positive fixtures P1-P7', () => {
  it('covers exactly the P1-P7 corpus with no unlisted fixtures', () => {
    expect(fixtureNames('positive')).toEqual(POSITIVE_FIXTURES.map(([, file]) => file).sort());
  });

  it.each(POSITIVE_FIXTURES)('%s validates through the public gate', (_label, file) => {
    const payload = loadFixture('positive', file);
    const report = evaluateRbContactEvasionObservationsV0(payload);
    expect(report.violations).toEqual([]);
    expect(report.valid).toBe(true);
    expect(isRbContactEvasionObservationsV0(payload)).toBe(true);
    const artifact = validateRbContactEvasionObservationsV0(payload);
    expect(artifact.artifact_id).toBe(RB_CONTACT_EVASION_ARTIFACT_ID);
    expect(artifact.schema_version).toBe(RB_CONTACT_EVASION_SCHEMA_VERSION);
    // Nothing in this contract may ever sit in a promoted position by fixture.
    expect(artifact.artifact_position).toBe('fixture_only');
  });

  it('P2 carries a raw count with no denominator and is not a rate', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p2_raw_count_without_denominator.json'),
    );
    const [observation] = artifact.observations;
    expect(observation.metric.value_kind).toBe('count');
    expect(observation.measurement.denominator).toBeNull();
    expect(observation.measurement.numerator).toBeNull();
  });

  it('P3 classifies historical testing under speed, never under a contact mechanism', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p3_historical_testing_classified.json'),
    );
    const [observation] = artifact.observations;
    expect(observation.metric.metric_id).toBe('forty_yard_dash_seconds');
    expect(observation.mechanism_id).toBe('speed');
    expect(observation.scope.opportunity_class).toBe('athletic_testing');
    expect(RB_CONTACT_EVASION_METRIC_REGISTRY.forty_yard_dash_seconds).toEqual(['speed']);
  });

  it('P4 keeps a rights-blocked component missing with no value of any kind', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p4_rights_blocked_missing_component.json'),
    );
    const [observation] = artifact.observations;
    expect(observation.source.access_class).toBe('licensed_or_gated');
    expect(observation.source.promotable).toBe(false);
    expect(observation.measurement.status).toBe('missing');
    expect(observation.measurement.missingness_reason).toBe('rights_blocked');
    expect(observation.measurement.value).toBeNull();
    expect(observation.measurement.numerator).toBeNull();
    expect(observation.measurement.denominator).toBeNull();
  });

  it('P5 declares supersession explicitly and never self-references', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p5_declared_snapshot_supersession.json'),
    );
    const [observation] = artifact.observations;
    expect(observation.source.provenance_mode).toBe('snapshot');
    expect(observation.source.superseded_by_snapshot_id).toBe('synthetic-snapshot-2025-02-11');
    expect(observation.source.superseded_by_snapshot_id).not.toBe(observation.source.snapshot_id);
  });

  it('P6 keeps a weekly and a season window as separate rows under one metric identity', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p6_weekly_and_season_windows_coexist.json'),
    );
    const completeness = artifact.observations.map((row) => row.scope.window_completeness);
    expect(completeness).toEqual(['single_week', 'full_season']);
    const definitions = new Set(
      artifact.observations.map((row) => row.metric.definition_version),
    );
    // Coexisting windows share ONE unchanged definition; drift would be N4.
    expect(definitions.size).toBe(1);
    expect(artifact.observations[0].scope.week).toBe(12);
    expect(artifact.observations[1].scope.week).toBeNull();
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
    // The two unsupported mechanisms stay missing; they are never filled from
    // the three that are observed.
    expect(coverage.speed.status).toBe('known_missing');
    expect(coverage.agility_change_of_direction.status).toBe('known_missing');
    expect(coverage.speed.observed_observation_ids).toEqual([]);
    expect(coverage.agility_change_of_direction.observed_observation_ids).toEqual([]);
    // The receipt is a per-mechanism ledger, never a rolled-up number.
    const serialized = JSON.stringify(coverage);
    expect(serialized).not.toMatch(/score|composite|grade|rank|percentile|elite|overall/i);
    for (const entry of Object.values(coverage)) {
      expect(Object.keys(entry).sort()).toEqual([
        'missing_observation_ids',
        'observed_observation_ids',
        'status',
      ]);
    }
  });

  it('an unknown mechanism id in a receipt query yields no evidence at all', () => {
    const artifact = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p7_bucky_receipt_remains_partial.json'),
    );
    const coverage = summarizeRbContactEvasionMechanismCoverage(artifact, '00-0000001');
    for (const entry of Object.values(coverage)) {
      expect(entry.status).toBe('no_admitted_observation');
    }
  });
});

describe('rb_contact_evasion_observations_v0 negative fixtures N1-N15', () => {
  it('covers exactly the N1-N15 corpus with no unlisted fixtures', () => {
    expect(fixtureNames('negative')).toEqual(NEGATIVE_FIXTURES.map(([, file]) => file).sort());
  });

  it('assigns a distinct reason code to every negative fixture', () => {
    const codes = NEGATIVE_FIXTURES.map(([, , code]) => code);
    expect(new Set(codes).size).toBe(codes.length);
    expect(codes.length).toBe(15);
  });

  it.each(NEGATIVE_FIXTURES)(
    '%s is rejected for its own reason, after parsing cleanly',
    (_label, file, expectedCode) => {
      const payload = loadFixture('negative', file);
      const report = evaluateRbContactEvasionObservationsV0(payload);

      // The point of the corpus: the fixture must be structurally well-formed,
      // so its rejection is attributable to the named contract rule rather than
      // to an earlier parse failure.
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

  it.each(NEGATIVE_FIXTURES)(
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
    expect(rbContactEvasionMechanismIdSchema.safeParse('unknown').success).toBe(false);
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

  it('binds every registered metric to at most its own mechanisms', () => {
    for (const [metricId, mechanisms] of Object.entries(RB_CONTACT_EVASION_METRIC_REGISTRY)) {
      for (const mechanism of mechanisms) {
        expect(rbContactEvasionMechanismIdSchema.safeParse(mechanism).success).toBe(true);
      }
      // A metric that could evidence two mechanisms would let evidence for one
      // silently satisfy another. None may.
      expect(new Set(mechanisms).size).toBeLessThanOrEqual(1);
      expect(metricId).toMatch(/^[a-z0-9_]+$/);
    }
    // The known-inadmissible summaries are bound to no mechanism at all.
    expect(RB_CONTACT_EVASION_METRIC_REGISTRY.yards_per_carry).toEqual([]);
    expect(RB_CONTACT_EVASION_METRIC_REGISTRY.longest_rush_yards).toEqual([]);
    expect(RB_CONTACT_EVASION_METRIC_REGISTRY.rush_attempts).toEqual([]);
  });

  it('keeps incompatible_with relationships symmetric', () => {
    expect(findRbContactEvasionIncompatibilityAsymmetries()).toEqual([]);
    for (const [left, rights] of Object.entries(RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES)) {
      for (const right of rights) {
        expect(RB_CONTACT_EVASION_METRIC_INCOMPATIBILITIES[right]?.has(left)).toBe(true);
      }
    }
    // An asymmetric index is itself a reported violation, not a silent pass.
    expect(
      findRbContactEvasionIncompatibilityAsymmetries({ a: new Set(['b']), b: new Set() }),
    ).toEqual([{ from: 'a', to: 'b' }]);
  });

  it('rejects unknown fields at every level rather than ignoring them', () => {
    const base = loadFixture('positive', 'p1_complete_derived_explosiveness_rate.json') as Record<
      string,
      unknown
    >;
    const withRootExtra = { ...base, elusiveness_score: 0.9 };
    const rootReport = evaluateRbContactEvasionObservationsV0(withRootExtra);
    expect(rootReport.shape_valid).toBe(false);
    expect(rootReport.reason_codes).toContain('UNKNOWN_FIELD_PRESENT');

    const withRowExtra = JSON.parse(JSON.stringify(base)) as RbContactEvasionObservationsV0;
    (withRowExtra.observations[0] as unknown as Record<string, unknown>).elusiveness_grade = 'A';
    const rowReport = evaluateRbContactEvasionObservationsV0(withRowExtra);
    expect(rowReport.shape_valid).toBe(false);
    expect(rowReport.reason_codes).toContain('UNKNOWN_FIELD_PRESENT');

    const withNestedExtra = JSON.parse(JSON.stringify(base)) as RbContactEvasionObservationsV0;
    (withNestedExtra.observations[0].measurement as unknown as Record<string, unknown>).percentile =
      0.91;
    const nestedReport = evaluateRbContactEvasionObservationsV0(withNestedExtra);
    expect(nestedReport.shape_valid).toBe(false);
    expect(nestedReport.reason_codes).toContain('UNKNOWN_FIELD_PRESENT');
  });

  it('reports shape failure distinctly from contract rejection', () => {
    const shapeReport = evaluateRbContactEvasionObservationsV0({ artifact_id: 'wrong' });
    expect(shapeReport.shape_valid).toBe(false);
    expect(shapeReport.valid).toBe(false);
    const contractReport = evaluateRbContactEvasionObservationsV0(
      loadFixture('negative', 'n01_rate_missing_denominator.json'),
    );
    expect(contractReport.shape_valid).toBe(true);
    expect(contractReport.valid).toBe(false);
  });

  it('exposes no score, composite, grade, ranking, or fantasy vocabulary anywhere', () => {
    const forbidden =
      /score|composite|grade|ranking|rank_|percentile|tier|rating|fantasy|overall|elite|neutral_default/i;
    const schemaText = readFileSync(SCHEMA_PATH, 'utf-8');
    const schema = JSON.parse(schemaText) as unknown;

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

    // Same guarantee on the vocabularies a consumer can actually emit.
    for (const enumSchema of [
      rbContactEvasionMechanismIdSchema,
      rbContactEvasionEvidenceClassSchema,
      rbContactEvasionSourceAccessClassSchema,
      rbContactEvasionReasonCodeSchema,
    ]) {
      for (const option of enumSchema.options) {
        // "MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED" and friends are reason codes,
        // never emittable values; none of them name a score or a judgment.
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
  });

  it('never lets a fixture-provenance row sit in a candidate or promoted artifact', () => {
    const base = loadFixture(
      'positive',
      'p1_complete_derived_explosiveness_rate.json',
    ) as RbContactEvasionObservationsV0;
    for (const position of ['candidate', 'promoted'] as const) {
      const report = evaluateRbContactEvasionObservationsV0({
        ...base,
        artifact_position: position,
      });
      expect(report.reason_codes).toContain('FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION');
    }
  });

  it('treats a re-formatted retrieval timestamp as the same instant, not an escape hatch', () => {
    const base = JSON.parse(
      JSON.stringify(loadFixture('negative', 'n10_retrieval_clock_substituted.json')),
    ) as RbContactEvasionObservationsV0;
    // Same instant, different textual offset. The rule compares instants.
    base.observations[0].clocks.retrieved_at = '2025-01-08T10:00:00+01:00';
    const report = evaluateRbContactEvasionObservationsV0(base);
    expect(report.reason_codes).toEqual(['RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK']);
  });

  it('rejects an unregistered metric id instead of admitting it by default', () => {
    const base = JSON.parse(
      JSON.stringify(loadFixture('positive', 'p2_raw_count_without_denominator.json')),
    ) as RbContactEvasionObservationsV0;
    base.observations[0].metric.metric_id = 'elusiveness_index';
    const report = evaluateRbContactEvasionObservationsV0(base);
    expect(report.shape_valid).toBe(true);
    expect(report.reason_codes).toContain('UNKNOWN_METRIC_ID');
  });

  it('distinguishes a missing value from a missing reason from an empty observation', () => {
    const base = JSON.parse(
      JSON.stringify(loadFixture('positive', 'p4_rights_blocked_missing_component.json')),
    ) as RbContactEvasionObservationsV0;

    // A missing component that drops its reason is not the same defect as one
    // that carries a value; the codes must not be conflated.
    const noReason = JSON.parse(JSON.stringify(base)) as RbContactEvasionObservationsV0;
    noReason.observations[0].measurement.missingness_reason = null;
    expect(evaluateRbContactEvasionObservationsV0(noReason).reason_codes).toEqual([
      'MISSINGNESS_REASON_ABSENT',
    ]);

    // An "observed" row with no value is a third, separate defect.
    const observedWithoutValue = JSON.parse(
      JSON.stringify(loadFixture('positive', 'p2_raw_count_without_denominator.json')),
    ) as RbContactEvasionObservationsV0;
    observedWithoutValue.observations[0].measurement.value = null;
    expect(evaluateRbContactEvasionObservationsV0(observedWithoutValue).reason_codes).toEqual([
      'OBSERVED_COMPONENT_MISSING_VALUE',
    ]);
  });

  it('will not let a row buy eligibility by lowering its own minimum-sample bar', () => {
    const base = JSON.parse(
      JSON.stringify(loadFixture('negative', 'n08_below_minimum_sample_rate_emitted.json')),
    ) as RbContactEvasionObservationsV0;

    // Drop the row's own metric minimum below its sample: with no cohort stated,
    // the row does set its own bar, and this is the documented residual risk.
    const selfLowered = JSON.parse(JSON.stringify(base)) as RbContactEvasionObservationsV0;
    selfLowered.observations[0].metric.minimum_eligible_opportunities = 5;
    expect(evaluateRbContactEvasionObservationsV0(selfLowered).valid).toBe(true);

    // But once a cohort is stated, the stricter minimum governs and the same
    // self-lowering no longer buys eligibility.
    const withCohort = JSON.parse(JSON.stringify(selfLowered)) as RbContactEvasionObservationsV0;
    withCohort.observations[0].cohort_scope = {
      position: 'RB',
      season: 2024,
      season_type: 'REG',
      window_completeness: 'multi_week',
      minimum_eligible_opportunities: 40,
      window_completeness_disclosure: null,
    };
    expect(evaluateRbContactEvasionObservationsV0(withCohort).reason_codes).toEqual([
      'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
    ]);
  });

  it('every reason code used by the corpus is in the closed reason-code enum', () => {
    for (const [, , code] of NEGATIVE_FIXTURES) {
      expect(rbContactEvasionReasonCodeSchema.safeParse(code).success).toBe(true);
    }
  });
});
