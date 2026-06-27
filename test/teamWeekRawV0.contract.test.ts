import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  findTeamWeekRawDeferredFieldViolations,
  getTeamWeekRawFieldReadiness,
  isPressureRateAllowedDeferred,
  isTeamWeekRawArtifactGoverned,
  isTeamWeekRawArtifactV0,
  isTeamWeekRawFieldDeferred,
  resolveTeamWeekRawGovernance,
  teamWeekRawArtifactV0Schema,
  teamWeekRawGovernanceSchema,
  validateTeamWeekRawArtifactV0,
  type TeamWeekRawArtifactV0,
} from '../src/index.js';

const CANDIDATE_PATH =
  'exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json';

function loadCandidate(): unknown {
  return JSON.parse(readFileSync(path.resolve(CANDIDATE_PATH), 'utf-8'));
}

/** Minimal valid artifact for focused metadata/row assertions. */
function baseArtifact(): TeamWeekRawArtifactV0 {
  return {
    artifact: 'team_week_raw_v0',
    generatedAt: '2026-06-25T19:20:51+00:00',
    season: 2024,
    sourceArtifacts: ['nflverse-data:pbp/play_by_play_2024'],
    metadata: {
      provenanceStatus: 'partial_real_data',
      provenanceNotes: ['ungoverned candidate'],
      inputSources: [
        {
          source: 'https://example.invalid/pbp_2024.parquet',
          sourceType: 'nflverse',
          sourceSnapshotAt: '2026-06-25T19:20:36+00:00',
        },
      ],
      coverage: {
        season: 2024,
        expectedTeams: ['KC', 'BAL'],
        presentTeams: ['KC', 'BAL'],
        missingTeams: [],
        unexpectedTeams: [],
        weeks: [1],
        expectedWeeks: [1],
        isFullLeague: false,
        isFullRegularSeasonCalendar: false,
        expectedTeamGameRows: 2,
        actualTeamGameRows: 2,
        byeWeeksHandled: true,
      },
    },
    rows: [
      {
        season: 2024,
        week: 1,
        teamCode: 'KC',
        opponentCode: 'BAL',
        pointsFor: 27,
        pointsAgainst: 20,
        offensivePlays: 50,
        neutralPlays: 40,
        secondsPerPlay: 23.55,
        passRate: 0.6,
        neutralPassRate: 0.55,
        rushRate: 0.4,
        epaPerPlay: 0.2,
        passEpaPerPlay: 0.3,
        rushEpaPerPlay: 0.05,
        successRate: 0.45,
        explosivePlayRate: 0.1,
        drives: 10,
        pointsPerDrive: 2.7,
        redZoneTrips: 3,
        redZoneTdRate: 0.33,
        sacksAllowed: 2,
        pressureRateAllowed: null,
        turnovers: 1,
        fantasyPointsForQB: null,
        fantasyPointsForRB: null,
        fantasyPointsForWR: null,
        fantasyPointsForTE: null,
        fantasyPointsAllowedQB: null,
        fantasyPointsAllowedRB: null,
        fantasyPointsAllowedWR: null,
        fantasyPointsAllowedTE: null,
      },
    ],
  };
}

describe('team_week_raw_v0 contract: committed 2024 candidate', () => {
  it('still validates against the revised schema (backward compatible)', () => {
    const candidate = validateTeamWeekRawArtifactV0(loadCandidate());
    expect(candidate.artifact).toBe('team_week_raw_v0');
    expect(candidate.rows).toHaveLength(544);
  });

  it('preserves governance / deferred / lineage metadata through parse', () => {
    const candidate = validateTeamWeekRawArtifactV0(loadCandidate());
    expect(candidate.metadata.governance).toEqual({
      governanceStatus: 'ungoverned',
      governanceSource: 'not_set',
      notes: expect.any(String),
    });
    expect(candidate.metadata.deferredFields).toContain('pressureRateAllowed');
    expect(candidate.metadata.deferredFieldReasons?.pressureRateAllowed).toEqual(
      expect.any(String),
    );
    expect(candidate.metadata.validationReportPath).toEqual(expect.any(String));
    expect(candidate.metadata.lineageManifestPath).toEqual(expect.any(String));
  });

  it('resolves the candidate fail-closed as ungoverned, not governed', () => {
    const candidate = validateTeamWeekRawArtifactV0(loadCandidate());
    expect(isTeamWeekRawArtifactGoverned(candidate)).toBe(false);
    expect(resolveTeamWeekRawGovernance(candidate.metadata)).toEqual({
      governanceStatus: 'ungoverned',
      governanceSource: 'not_set',
      isGoverned: false,
    });
  });

  it('treats pressureRateAllowed as deferred (unknown), never zero', () => {
    const candidate = validateTeamWeekRawArtifactV0(loadCandidate());
    expect(isPressureRateAllowedDeferred(candidate.metadata)).toBe(true);
    const nonNull = candidate.rows.filter((r) => r.pressureRateAllowed !== null);
    expect(nonNull).toHaveLength(0);
  });
});

describe('team_week_raw_v0 contract: governance fail-closed semantics', () => {
  it('accepts a governed marker only with explicit_marker', () => {
    const artifact = baseArtifact();
    artifact.metadata.governance = {
      governanceStatus: 'governed',
      governanceSource: 'explicit_marker',
      reviewRefs: ['docs/reviews/some-promotion-review.md'],
    };
    const parsed = validateTeamWeekRawArtifactV0(artifact);
    expect(isTeamWeekRawArtifactGoverned(parsed)).toBe(true);
    expect(resolveTeamWeekRawGovernance(parsed.metadata).isGoverned).toBe(true);
  });

  it('rejects governed without explicit_marker (no path to governed by default)', () => {
    const artifact = baseArtifact();
    // Type-valid enum values, but a semantically invalid combination the
    // schema's superRefine rejects.
    artifact.metadata.governance = {
      governanceStatus: 'governed',
      governanceSource: 'not_set',
    };
    expect(teamWeekRawArtifactV0Schema.safeParse(artifact).success).toBe(false);
  });

  it('absent governance resolves fail-closed to ungoverned', () => {
    const artifact = baseArtifact();
    expect(artifact.metadata.governance).toBeUndefined();
    expect(resolveTeamWeekRawGovernance(artifact.metadata)).toEqual({
      governanceStatus: 'ungoverned',
      governanceSource: 'not_set',
      isGoverned: false,
    });
  });

  it('unrecognized governance fails parse and resolves fail-closed', () => {
    const raw = baseArtifact() as unknown as {
      metadata: { governance?: unknown };
    };
    raw.metadata.governance = { governanceStatus: 'totally_governed' };
    expect(teamWeekRawArtifactV0Schema.safeParse(raw).success).toBe(false);
    // resolver does not trust unmodeled/garbage governance
    expect(resolveTeamWeekRawGovernance(raw.metadata).isGoverned).toBe(false);
    expect(resolveTeamWeekRawGovernance(raw.metadata).governanceStatus).toBe('ungoverned');
  });

  it('never infers governance from a governed-sounding artifact path or status alone', () => {
    // An ungoverned status with an explicit_marker source must NOT be governed.
    const governance = teamWeekRawGovernanceSchema.parse({
      governanceStatus: 'ungoverned',
      governanceSource: 'explicit_marker',
    });
    expect(governance.governanceStatus).toBe('ungoverned');
    expect(
      resolveTeamWeekRawGovernance({ governance }).isGoverned,
    ).toBe(false);
  });
});

describe('team_week_raw_v0 contract: field-readiness and pressure posture', () => {
  it('parses pressure null + deferred readiness and treats null as unknown', () => {
    const artifact = baseArtifact();
    artifact.metadata.deferredFields = ['pressureRateAllowed'];
    artifact.metadata.deferredFieldReasons = {
      pressureRateAllowed: 'no confirmed governed pressure-rate source',
    };
    artifact.metadata.fieldReadiness = {
      pressureRateAllowed: 'deferred',
      epaPerPlay: 'available',
      redZoneTdRate: 'partial_nulls',
    };
    const parsed = validateTeamWeekRawArtifactV0(artifact);
    expect(getTeamWeekRawFieldReadiness(parsed.metadata, 'pressureRateAllowed')).toBe(
      'deferred',
    );
    expect(isPressureRateAllowedDeferred(parsed.metadata)).toBe(true);
    expect(parsed.rows[0].pressureRateAllowed).toBeNull();
  });

  it('treats insufficient_data and unavailable as deferred, available/partial_nulls as not', () => {
    const make = (status: string) =>
      ({ fieldReadiness: { x: status } }) as never;
    expect(isTeamWeekRawFieldDeferred(make('insufficient_data'), 'x')).toBe(true);
    expect(isTeamWeekRawFieldDeferred(make('unavailable'), 'x')).toBe(true);
    expect(isTeamWeekRawFieldDeferred(make('deferred'), 'x')).toBe(true);
    expect(isTeamWeekRawFieldDeferred(make('available'), 'x')).toBe(false);
    expect(isTeamWeekRawFieldDeferred(make('partial_nulls'), 'x')).toBe(false);
  });

  it('allows pressureRateAllowed to be omitted entirely (optional)', () => {
    const artifact = baseArtifact();
    delete (artifact.rows[0] as { pressureRateAllowed?: number | null })
      .pressureRateAllowed;
    expect(isTeamWeekRawArtifactV0(artifact)).toBe(true);
  });

  it('flags a zero-filled deferred field as a violation (no null-to-zero laundering)', () => {
    const artifact = baseArtifact();
    artifact.metadata.deferredFields = ['pressureRateAllowed'];
    artifact.rows[0].pressureRateAllowed = 0; // zero-fill of a deferred field
    const parsed = validateTeamWeekRawArtifactV0(artifact);
    const violations = findTeamWeekRawDeferredFieldViolations(parsed);
    expect(violations).toEqual([
      { field: 'pressureRateAllowed', rowIndex: 0, value: 0 },
    ]);
  });

  it('reports no deferred-field violations for the honest null-deferred candidate', () => {
    const candidate = validateTeamWeekRawArtifactV0(loadCandidate());
    expect(findTeamWeekRawDeferredFieldViolations(candidate)).toEqual([]);
  });
});

describe('team_week_raw_v0 contract: lineage / source-pin metadata', () => {
  it('represents checksum and immutable source pin on input sources', () => {
    const artifact = baseArtifact();
    artifact.metadata.inputSources[0].sourceRefs = ['nflverse-data:pbp/play_by_play_2024'];
    artifact.metadata.inputSources[0].retrievalMethod = 'nflreadpy.load_pbp([2024])';
    artifact.metadata.inputSources[0].retrievalTimestamp = '2026-06-25T19:20:36+00:00';
    artifact.metadata.inputSources[0].packageVersion = '0.1.5';
    artifact.metadata.inputSources[0].checksum = {
      algorithm: 'sha256',
      value: 'a'.repeat(64),
    };
    artifact.metadata.inputSources[0].immutableSourceRef =
      'nflverse-data@some-immutable-release-tag';
    const parsed = validateTeamWeekRawArtifactV0(artifact);
    expect(parsed.metadata.inputSources[0].checksum).toEqual({
      algorithm: 'sha256',
      value: 'a'.repeat(64),
    });
    expect(parsed.metadata.inputSources[0].immutableSourceRef).toEqual(expect.any(String));
  });

  it('represents validation and lineage manifest paths', () => {
    const artifact = baseArtifact();
    artifact.metadata.validationReportPath = 'exports/.../candidate.validation.json';
    artifact.metadata.lineageManifestPath = 'data/manifests/candidate.manifest.json';
    const parsed = validateTeamWeekRawArtifactV0(artifact);
    expect(parsed.metadata.validationReportPath).toEqual(expect.any(String));
    expect(parsed.metadata.lineageManifestPath).toEqual(expect.any(String));
  });
});
