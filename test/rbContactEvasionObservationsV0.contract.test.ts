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
  rbContactEvasionEvidenceClassSchema,
  rbContactEvasionExpectedRate,
  rbContactEvasionGrainKey,
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

/** Deep clone of a fixture, typed for mutation. */
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

/** P1–P7, the corpus TIBER-Data #234 mandates. */
const MANDATED_POSITIVE: ReadonlyArray<[string, string]> = [
  ['P1 complete derived explosiveness rate', 'p1_complete_derived_explosiveness_rate.json'],
  ['P2 raw count without denominator', 'p2_raw_count_without_denominator.json'],
  ['P3 correctly classified historical testing', 'p3_historical_testing_classified.json'],
  ['P4 rights-blocked missing component', 'p4_rights_blocked_missing_component.json'],
  ['P5 declared snapshot supersession', 'p5_declared_snapshot_supersession.json'],
  ['P6 weekly and season windows coexisting', 'p6_weekly_and_season_windows_coexist.json'],
  ['P7 Bucky receipt remains partial', 'p7_bucky_receipt_remains_partial.json'],
];

/** Added in the review-repair round. */
const SUPPLEMENTARY_POSITIVE: ReadonlyArray<[string, string]> = [
  ['P8 absent source clock stays null', 'p8_absent_source_clock_stays_null.json'],
];

/**
 * N1–N15, the corpus #234 mandates. Each entry pins the fixture to the ONE
 * reason code it must be rejected by — not merely "it was rejected".
 */
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

/** N16–N28: one fixture per escape the first exact-head review reproduced. */
const SUPPLEMENTARY_NEGATIVE: ReadonlyArray<[string, string, RbContactEvasionReasonCode]> = [
  ['N16 promotable without redistribution permission', 'n16_promotable_without_permissions.json', 'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE'],
  ['N17 direct observation without retention/automation', 'n17_direct_observation_without_retention.json', 'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_EVIDENCE_CLASS'],
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

const ALL_POSITIVE = [...MANDATED_POSITIVE, ...SUPPLEMENTARY_POSITIVE];
const ALL_NEGATIVE = [...MANDATED_NEGATIVE, ...SUPPLEMENTARY_NEGATIVE];

describe('rb_contact_evasion_observations_v0 positive fixtures', () => {
  it('covers exactly the positive corpus with no unlisted fixtures', () => {
    expect(fixtureNames('positive')).toEqual(ALL_POSITIVE.map(([, file]) => file).sort());
  });

  it.each(ALL_POSITIVE)('%s validates through the public gate', (_label, file) => {
    const payload = loadFixture('positive', file);
    const report = evaluateRbContactEvasionObservationsV0(payload);
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

  it('P3 classifies historical testing under speed, never under a contact mechanism', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p3_historical_testing_classified.json'),
    ).observations;
    expect(observation.metric.metric_id).toBe('forty_yard_dash_seconds');
    expect(observation.mechanism_id).toBe('speed');
    expect(observation.scope.opportunity_class).toBe('athletic_testing');
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.forty_yard_dash_seconds.mechanisms).toEqual([
      'speed',
    ]);
  });

  it('P4 keeps a rights-blocked component missing with no value of any kind', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p4_rights_blocked_missing_component.json'),
    ).observations;
    expect(observation.source.access_class).toBe('licensed_or_gated');
    expect(observation.source.promotable).toBe(false);
    expect(observation.source.permissions.retention_and_reproduction).toBe('prohibited');
    expect(observation.measurement.status).toBe('missing');
    expect(observation.measurement.missingness_reason).toBe('rights_blocked');
    expect(observation.measurement.value).toBeNull();
  });

  it('P5 declares supersession and pins the snapshot with a content digest', () => {
    const [observation] = validateRbContactEvasionObservationsV0(
      loadFixture('positive', 'p5_declared_snapshot_supersession.json'),
    ).observations;
    expect(observation.source.provenance_mode).toBe('snapshot');
    expect(observation.source.content_digest?.algorithm).toBe('sha256');
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
    expect(new Set(artifact.observations.map((row) => row.metric.definition_version)).size).toBe(1);
    // Coexisting windows are distinct grains, so uniqueness does not reject them.
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
      const report = evaluateRbContactEvasionObservationsV0(loadFixture('negative', file));
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
 * Public-boundary evidence for every escape the first exact-head review
 * reproduced. Each test re-applies the reviewer's exact mutation to the public
 * evaluator and asserts it is now rejected by a named reason code. These are
 * the regression locks on that review round.
 */
describe('rb_contact_evasion_observations_v0 review-round escapes, at the public boundary', () => {
  const P1 = () => mutable('positive', 'p1_complete_derived_explosiveness_rate.json');

  describe('R1 — payload could redefine what a known metric means', () => {
    it('rejects an emitted value unrelated to its own numerator and denominator', () => {
      const artifact = P1();
      artifact.observations[0].measurement.value = 0.999;
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'RATE_VALUE_INCONSISTENT_WITH_COMPONENTS',
      ]);
    });

    it('rejects a known-but-wrong numerator metric id', () => {
      const artifact = P1();
      artifact.observations[0].measurement.numerator = {
        metric_id: 'receptions',
        value: 26,
      };
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'RATE_COMPONENT_METRIC_MISMATCH',
      ]);
    });

    it('rejects a zero denominator', () => {
      const artifact = P1();
      artifact.observations[0].measurement.denominator!.value = 0;
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'RATE_DENOMINATOR_NOT_POSITIVE',
      ]);
    });

    it('rejects a rewritten unit and a flipped directionality', () => {
      const artifact = P1();
      artifact.observations[0].metric.unit = 'bananas';
      artifact.observations[0].metric.directionality = 'lower_is_more_of_mechanism';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'METRIC_DESCRIPTOR_CONTRADICTED',
      ]);
    });

    it('owns the rate rounding rather than letting the row imply it', () => {
      expect(RB_CONTACT_EVASION_RATE_ROUNDING_DECIMALS).toBe(3);
      expect(rbContactEvasionExpectedRate(26, 203)).toBe(0.128);
      expect(rbContactEvasionExpectedRate(694, 203)).toBe(3.419);
    });
  });

  describe('R2 — minimum sample could be bypassed or self-set', () => {
    it('rejects an observed rate with no eligible-opportunity count', () => {
      const artifact = P1();
      artifact.observations[0].measurement.eligible_opportunities = null;
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE',
      ]);
    });

    it('gives the row no threshold field to lower — only a rule id it must match', () => {
      const artifact = P1();
      expect(
        (artifact.observations[0].metric as unknown as Record<string, unknown>)
          .minimum_eligible_opportunities,
      ).toBeUndefined();
      expect(
        (artifact.observations[0].cohort_scope as unknown as Record<string, unknown>)
          .minimum_eligible_opportunities,
      ).toBeUndefined();
      artifact.observations[0].metric.minimum_sample_rule_id = 'row_declared_minimum_of_one';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED',
      ]);
    });

    it('takes the governing threshold from the code-owned rule, keyed by window', () => {
      expect(RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.rule_id).toBe(
        RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE_ID,
      );
      // The thresholds are fixture placeholders, and the rule says so in code.
      expect(RB_CONTACT_EVASION_MINIMUM_SAMPLE_RULE.authority).toBe('fixture_only_placeholder');
      const artifact = P1();
      artifact.observations[0].measurement.eligible_opportunities = 39;
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED',
      ]);
    });

    it('fails closed for an observed rate outside fixture_only position', () => {
      for (const position of ['candidate', 'promoted'] as const) {
        const artifact = P1();
        artifact.artifact_position = position;
        artifact.observations[0].source.provenance_mode = 'live';
        expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
          'MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION',
        ]);
      }
    });
  });

  describe('R3 — clocks could not represent absence, and equality was not provenance', () => {
    it('lets an unavailable source clock be null instead of forcing a backfill', () => {
      const artifact = P1();
      artifact.observations[0].clocks.source_generated_at = null;
      artifact.observations[0].clock_provenance.source_generated_at = 'not_supplied_by_source';
      artifact.observations[0].clocks.source_observed_at = null;
      artifact.observations[0].clock_provenance.source_observed_at = 'not_supplied_by_source';
      expect(evaluateRbContactEvasionObservationsV0(artifact).valid).toBe(true);
    });

    it('rejects a substituted retrieval clock even when an offset hides the copy', () => {
      const artifact = P1();
      const clocks = artifact.observations[0].clocks;
      // The exact escape from review: an invented one-millisecond offset that
      // preserved ordering and defeated the old equality heuristic.
      clocks.source_observed_at = '2025-01-09T15:29:59.998+00:00';
      clocks.source_generated_at = '2025-01-09T15:29:59.999+00:00';
      clocks.source_available_at = '2025-01-09T15:29:59.999+00:00';
      clocks.retrieved_at = '2025-01-09T15:30:00.000+00:00';
      artifact.observations[0].clock_provenance.source_generated_at = 'retrieval_clock';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
      ]);
    });

    it('no longer rejects a legitimately coincident instant', () => {
      const artifact = P1();
      const clocks = artifact.observations[0].clocks;
      clocks.source_generated_at = '2025-01-09T15:30:00+00:00';
      clocks.source_available_at = '2025-01-09T15:30:00+00:00';
      clocks.retrieved_at = '2025-01-09T15:30:00+00:00';
      expect(evaluateRbContactEvasionObservationsV0(artifact).valid).toBe(true);
    });

    it('rejects a clock declared absent that nonetheless carries a timestamp', () => {
      const artifact = P1();
      artifact.observations[0].clock_provenance.source_generated_at = 'not_supplied_by_source';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'CLOCK_AVAILABILITY_CONTRADICTED',
      ]);
    });

    it('rejects a clock declared source-supplied that carries no timestamp', () => {
      const artifact = P1();
      artifact.observations[0].clocks.source_generated_at = null;
      // Origin still claims the source supplied it, so absence is a contradiction.
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'CLOCK_AVAILABILITY_CONTRADICTED',
      ]);
    });

    it('rejects a window or artifact clock claiming to be a source clock', () => {
      const artifact = P1();
      artifact.observations[0].clock_provenance.source_available_at = 'artifact_build_clock';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK',
      ]);
    });
  });

  describe('R4 — source governance facts were unrepresentable', () => {
    it('rejects a promotable claim that the stated permissions do not support', () => {
      const artifact = P1();
      artifact.observations[0].source.access_class = 'public_but_terms_constrained';
      artifact.observations[0].source.promotable = true;
      artifact.observations[0].source.permissions.redistribution_and_display = 'prohibited';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE',
      ]);
    });

    it('treats an unknown disposition as a blocker, never as permission', () => {
      // Attribution gates promotability only, which isolates the "unknown is
      // not permission" claim to one rule.
      const unknownAttribution = P1();
      unknownAttribution.observations[0].source.promotable = true;
      unknownAttribution.observations[0].source.permissions.attribution = 'unknown';
      expect(evaluateRbContactEvasionObservationsV0(unknownAttribution).reason_codes).toEqual([
        'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE',
      ]);

      // An unknown automated-access disposition blocks both promotability and
      // storing the exact observed value. Both rejections are correct.
      const unknownAccess = P1();
      unknownAccess.observations[0].source.promotable = true;
      unknownAccess.observations[0].source.permissions.automated_access = 'unknown';
      expect(evaluateRbContactEvasionObservationsV0(unknownAccess).reason_codes).toEqual([
        'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_EVIDENCE_CLASS',
        'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE',
      ]);
    });

    it('rejects storing an exact observed value without retention and automation', () => {
      const artifact = P1();
      artifact.observations[0].source.permissions.retention_and_reproduction = 'prohibited';
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_EVIDENCE_CLASS',
      ]);
    });

    it('requires a content digest for a snapshot and forbids one retention prohibits', () => {
      const missingDigest = P1();
      missingDigest.observations[0].source.provenance_mode = 'snapshot';
      expect(evaluateRbContactEvasionObservationsV0(missingDigest).reason_codes).toEqual([
        'SNAPSHOT_WITHOUT_CONTENT_DIGEST',
      ]);

      const digestWithoutRetention = mutable(
        'positive',
        'p4_rights_blocked_missing_component.json',
      );
      digestWithoutRetention.observations[0].source.content_digest = {
        algorithm: 'sha256',
        value: '0'.repeat(64),
      };
      expect(
        evaluateRbContactEvasionObservationsV0(digestWithoutRetention).reason_codes,
      ).toEqual(['CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION']);
    });
  });

  describe('R5 — artifact-level identity and grain were unenforced', () => {
    it('rejects a verbatim duplicated observation', () => {
      const artifact = P1();
      artifact.observations.push(JSON.parse(JSON.stringify(artifact.observations[0])));
      const report = evaluateRbContactEvasionObservationsV0(artifact);
      expect(report.valid).toBe(false);
      expect(report.reason_codes).toEqual([
        'DUPLICATE_OBSERVATION_GRAIN',
        'DUPLICATE_OBSERVATION_ID',
      ]);
    });

    it('rejects a repeated canonical grain even under a fresh observation id', () => {
      const artifact = P1();
      const clone = JSON.parse(
        JSON.stringify(artifact.observations[0]),
      ) as (typeof artifact.observations)[number];
      clone.observation_id = 'p1-explosiveness-derived-rate-renamed';
      artifact.observations.push(clone);
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'DUPLICATE_OBSERVATION_GRAIN',
      ]);
    });

    it('rejects a reused observation id even across different grains', () => {
      const artifact = P1();
      const clone = JSON.parse(
        JSON.stringify(artifact.observations[0]),
      ) as (typeof artifact.observations)[number];
      clone.scope.week = 12;
      clone.scope.games_included = 1;
      clone.scope.window_completeness = 'single_week';
      clone.clocks.window_start = '2024-11-24T00:00:00+00:00';
      clone.clocks.window_end = '2024-11-25T00:00:00+00:00';
      clone.measurement.numerator = { metric_id: 'explosive_rushes_10_plus_count', value: 4 };
      clone.measurement.denominator = {
        metric_id: 'rush_attempts',
        value: 19,
        opportunity_type: 'rush_attempt',
      };
      clone.measurement.value = rbContactEvasionExpectedRate(4, 19);
      clone.measurement.eligible_opportunities = 19;
      clone.cohort_scope = null;
      artifact.observations.push(clone);
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toEqual([
        'DUPLICATE_OBSERVATION_ID',
      ]);
    });
  });
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

  it('owns every metric descriptor in code, coherently', () => {
    for (const [metricId, descriptor] of Object.entries(RB_CONTACT_EVASION_METRIC_DICTIONARY)) {
      expect(metricId).toMatch(/^[a-z0-9_]+$/);
      for (const mechanism of descriptor.mechanisms) {
        expect(rbContactEvasionMechanismIdSchema.safeParse(mechanism).success).toBe(true);
      }
      // A metric that could evidence two mechanisms would let evidence for one
      // silently satisfy another. None may.
      expect(descriptor.mechanisms.length).toBeLessThanOrEqual(1);
      if (descriptor.value_kind === 'rate') {
        // A rate descriptor must name real component metrics and an opportunity type.
        expect(descriptor.numerator_metric_id).not.toBeNull();
        expect(descriptor.denominator_metric_id).not.toBeNull();
        expect(descriptor.denominator_opportunity_type).not.toBeNull();
        expect(RB_CONTACT_EVASION_METRIC_DICTIONARY[descriptor.numerator_metric_id!]).toBeDefined();
        expect(
          RB_CONTACT_EVASION_METRIC_DICTIONARY[descriptor.denominator_metric_id!],
        ).toBeDefined();
      } else {
        expect(descriptor.numerator_metric_id).toBeNull();
        expect(descriptor.denominator_metric_id).toBeNull();
        expect(descriptor.denominator_opportunity_type).toBeNull();
      }
    }
    // The known-inadmissible summaries are bound to no mechanism at all.
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.yards_per_carry.mechanisms).toEqual([]);
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.longest_rush_yards.mechanisms).toEqual([]);
    expect(RB_CONTACT_EVASION_METRIC_DICTIONARY.rush_attempts.mechanisms).toEqual([]);
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

    const rootReport = evaluateRbContactEvasionObservationsV0({
      ...base,
      elusiveness_score: 0.9,
    });
    expect(rootReport.shape_valid).toBe(false);
    expect(rootReport.reason_codes).toContain('UNKNOWN_FIELD_PRESENT');

    const withRowExtra = mutable('positive', 'p1_complete_derived_explosiveness_rate.json');
    (withRowExtra.observations[0] as unknown as Record<string, unknown>).elusiveness_grade = 'A';
    expect(evaluateRbContactEvasionObservationsV0(withRowExtra).reason_codes).toContain(
      'UNKNOWN_FIELD_PRESENT',
    );

    const withNestedExtra = mutable('positive', 'p1_complete_derived_explosiveness_rate.json');
    (
      withNestedExtra.observations[0].measurement as unknown as Record<string, unknown>
    ).percentile = 0.91;
    expect(evaluateRbContactEvasionObservationsV0(withNestedExtra).reason_codes).toContain(
      'UNKNOWN_FIELD_PRESENT',
    );

    const withPermissionExtra = mutable('positive', 'p1_complete_derived_explosiveness_rate.json');
    (
      withPermissionExtra.observations[0].source.permissions as unknown as Record<string, unknown>
    ).sublicensing = 'permitted';
    expect(evaluateRbContactEvasionObservationsV0(withPermissionExtra).reason_codes).toContain(
      'UNKNOWN_FIELD_PRESENT',
    );
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

  it('distinguishes a missing value from a missing reason from an empty observation', () => {
    const noReason = mutable('positive', 'p4_rights_blocked_missing_component.json');
    noReason.observations[0].measurement.missingness_reason = null;
    expect(evaluateRbContactEvasionObservationsV0(noReason).reason_codes).toEqual([
      'MISSINGNESS_REASON_ABSENT',
    ]);

    const observedWithoutValue = mutable('positive', 'p2_raw_count_without_denominator.json');
    observedWithoutValue.observations[0].measurement.value = null;
    expect(evaluateRbContactEvasionObservationsV0(observedWithoutValue).reason_codes).toEqual([
      'OBSERVED_COMPONENT_MISSING_VALUE',
    ]);
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
    expect(schema.$defs.clockProvenance.enum).toEqual([
      'football_window',
      'source_supplied',
      'not_supplied_by_source',
      'retrieval_clock',
      'artifact_build_clock',
    ]);
  });

  it('never lets a fixture-provenance row sit in a candidate or promoted artifact', () => {
    const base = mutable('positive', 'p2_raw_count_without_denominator.json');
    for (const position of ['candidate', 'promoted'] as const) {
      const artifact = { ...base, artifact_position: position };
      expect(evaluateRbContactEvasionObservationsV0(artifact).reason_codes).toContain(
        'FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION',
      );
    }
  });

  it('rejects an unregistered metric id instead of admitting it by default', () => {
    const artifact = mutable('positive', 'p2_raw_count_without_denominator.json');
    artifact.observations[0].metric.metric_id = 'elusiveness_index';
    const report = evaluateRbContactEvasionObservationsV0(artifact);
    expect(report.shape_valid).toBe(true);
    expect(report.reason_codes).toContain('UNKNOWN_METRIC_ID');
  });

  it('every reason code used by the corpus is in the closed reason-code enum', () => {
    for (const [, , code] of ALL_NEGATIVE) {
      expect(rbContactEvasionReasonCodeSchema.safeParse(code).success).toBe(true);
    }
  });
});
