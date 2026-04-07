import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS,
  buildForgeWeeklyDerivedArtifactFromRawSources,
  buildForgeWeeklySkillDerivedArtifactFromRawSources,
  buildForgeWeeklySkillDerivedArtifactsForWeeks,
  forgeWeeklyPlayerInputArraySchema,
  getForgeWeeklySkillSupportedWeeksFromRawSources,
  getForgeWeeklySkillDerivedArtifactPath,
  toDeterministicForgeWeeklyDerivedJson,
  toDeterministicForgeWeeklySampleJson,
  toDeterministicForgeWeeklySkillDerivedJson,
  writeForgeWeeklyDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifactsForWeeks,
} from '../src/index.js';

describe('forge weekly derived artifact export lanes', () => {
  it('builds a QB-only derived artifact that validates against ForgeWeeklyPlayerInput', () => {
    const artifact = buildForgeWeeklyDerivedArtifactFromRawSources();
    const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);

    expect(parsed).toHaveLength(2);
    expect(parsed.every((record) => record.position === 'QB')).toBe(true);
    expect(parsed.map((record) => record.playerId)).toEqual(['00-0033901', '00-0037183']);
  });

  it('builds broader skill-position artifacts for multiple weeks', () => {
    const artifacts = buildForgeWeeklySkillDerivedArtifactsForWeeks();
    const supportedWeeks = getForgeWeeklySkillSupportedWeeksFromRawSources({ season: 2024 });

    expect(supportedWeeks).toEqual([1, 2, 3, 4, 5, 6]);
    expect(artifacts.map((artifact) => artifact.week)).toEqual(supportedWeeks);

    for (const { season, week, artifact } of artifacts) {
      const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);
      expect(parsed).toHaveLength(8);
      expect([...new Set(parsed.map((record) => record.position))].sort()).toEqual([
        'QB',
        'RB',
        'TE',
        'WR',
      ]);
      expect(parsed.every((record) => record.season === season && record.week === week)).toBe(true);
      expect(parsed.every((record) => record.practiceParticipation === 'none')).toBe(true);
      expect(parsed.every((record) => record.opponentDefenseTier === 'neutral')).toBe(true);
      expect(parsed.every((record) => record.activeProjection === 1)).toBe(true);
      expect(parsed.every((record) => record.fantasyPointsPerOpportunity <= 3)).toBe(true);
      expect(parsed.every((record) => (record.qualityFlags ?? []).length === new Set(record.qualityFlags ?? []).size)).toBe(
        true,
      );
      expect(parsed.map((record) => record.playerId)).toEqual([
        '00-0033901',
        '00-0036976',
        '00-0037183',
        '00-0037834',
        '00-0038047',
        '00-0038122',
        '00-0038134',
        '00-0039152',
      ]);
    }
  });

  it('serializes week 6 audit players with cleaner semantic defaults', () => {
    const weekSix = buildForgeWeeklySkillDerivedArtifactFromRawSources({ season: 2024, week: 6 });
    const byName = new Map(weekSix.map((record) => [record.playerName, record]));

    const gibbs = byName.get('Jahmyr Gibbs');
    const stBrown = byName.get('Amon-Ra St. Brown');
    const goff = byName.get('Jared Goff');
    const robinson = byName.get('Bijan Robinson');
    const pitts = byName.get('Kyle Pitts');

    expect(gibbs?.activeProjection).toBe(1);
    expect(stBrown?.routeParticipation).toBeGreaterThan(0);
    expect(goff?.opponentDefenseTier).toBe('neutral');
    expect(robinson?.practiceParticipation).toBe('none');
    expect(new Set(weekSix.map((record) => record.roleVolatility)).size).toBeGreaterThan(1);
    expect(new Set(weekSix.map((record) => record.featureCoverage)).size).toBeGreaterThan(1);
    expect(gibbs?.qualityFlags).toContain(
      'role_volatility_derived_from_recent_opportunity_share_and_role_mix_changes',
    );
    expect(goff?.qualityFlags).toContain('routes_and_route_participation_not_available_set_to_0_for_qb_rows');
    expect(pitts?.qualityFlags).toContain(
      'routes_and_route_participation_approximated_from_team_pass_attempts_and_player_target_volume',
    );
  });

  it('uses fallback role-volatility defaults only when history is unavailable', () => {
    const weekOne = buildForgeWeeklySkillDerivedArtifactFromRawSources({ season: 2024, week: 1 });
    expect(weekOne.every((record) => record.roleVolatility === 0.5)).toBe(true);
    expect(
      weekOne.every((record) =>
        (record.qualityFlags ?? []).includes('role_volatility_defaulted_to_neutral_midpoint_due_to_missing_multigame_history'),
      ),
    ).toBe(true);

    const weekSix = buildForgeWeeklySkillDerivedArtifactFromRawSources({ season: 2024, week: 6 });
    expect(weekSix.some((record) => record.roleVolatility !== 0.5)).toBe(true);
    expect(
      weekSix.every((record) =>
        (record.qualityFlags ?? []).includes('role_volatility_derived_from_recent_opportunity_share_and_role_mix_changes'),
      ),
    ).toBe(true);
  });

  it('is deterministic and matches committed derived artifacts', () => {
    const firstQbPass = toDeterministicForgeWeeklyDerivedJson();
    const secondQbPass = toDeterministicForgeWeeklyDerivedJson();
    const committedQb = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH), 'utf-8');

    expect(firstQbPass).toEqual(secondQbPass);
    expect(firstQbPass).toEqual(committedQb);

    for (const week of FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS) {
      const firstSkillPass = toDeterministicForgeWeeklySkillDerivedJson({ week });
      const secondSkillPass = toDeterministicForgeWeeklySkillDerivedJson({ week });
      const committedSkill = readFileSync(
        path.resolve(getForgeWeeklySkillDerivedArtifactPath(2024, week)),
        'utf-8',
      );

      expect(firstSkillPass).toEqual(secondSkillPass);
      expect(firstSkillPass).toEqual(committedSkill);
    }
  });

  it('fails closed for missing week support in raw fixtures', () => {
    expect(() =>
      buildForgeWeeklySkillDerivedArtifactFromRawSources({
        season: 2024,
        week: 7,
      }),
    ).toThrow('No skill-position records found');
  });

  it('fails closed when multi-week export requests unsupported weeks', () => {
    expect(() =>
      buildForgeWeeklySkillDerivedArtifactsForWeeks({
        season: 2024,
        weeks: [1, 2, 7],
      }),
    ).toThrow('Requested unsupported skill-derived weeks (7)');
  });

  it('fails closed when source path is missing', () => {
    expect(() =>
      buildForgeWeeklySkillDerivedArtifactFromRawSources({
        playerStatsSourcePath: 'data/raw/does_not_exist.json',
      }),
    ).toThrow();
  });

  it('fails closed when source records are invalid for the selected slice', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-derived-invalid-'));
    const invalidPlayerStatsPath = path.join(tempRoot, 'weekly_player_stats.invalid.json');

    writeFileSync(
      invalidPlayerStatsPath,
      JSON.stringify(
        {
          provenance: 'test',
          source_path: FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH,
          records: [
            {
              player_id: '00-0033901',
              full_name: 'Jared Goff',
              position: 'QB',
              team: 'DET',
              season: 2024,
              week: 1,
              targets: -2,
              receptions: 0,
              receiving_yards: 0,
              rushing_attempts: 3,
              rushing_yards: 7,
              pass_attempts: 28,
              fantasy_points_ppr: 17.7,
            },
          ],
        },
        null,
        2,
      ),
      'utf-8',
    );

    expect(() =>
      buildForgeWeeklySkillDerivedArtifactFromRawSources({
        playerStatsSourcePath: invalidPlayerStatsPath,
      }),
    ).toThrow();
  });

  it('fixture-derived sample export remains available and deterministic', () => {
    const sampleJson = toDeterministicForgeWeeklySampleJson();
    expect(sampleJson).toContain('forge-weekly-input-fixtures-v1');
  });

  it('writes deterministic derived artifact files to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-derived-'));
    const qbOutputPath = path.join(tempRoot, 'qb.artifact.json');
    const skillOutputPath = path.join(tempRoot, 'skill.artifact.json');

    const writtenQb = writeForgeWeeklyDerivedArtifact(qbOutputPath);
    const writtenSkill = writeForgeWeeklySkillDerivedArtifact(skillOutputPath);

    const qbFileContents = readFileSync(writtenQb, 'utf-8');
    const skillFileContents = readFileSync(writtenSkill, 'utf-8');

    expect(writtenQb).toEqual(path.resolve(qbOutputPath));
    expect(writtenSkill).toEqual(path.resolve(skillOutputPath));
    expect(qbFileContents).toEqual(toDeterministicForgeWeeklyDerivedJson());
    expect(skillFileContents).toEqual(toDeterministicForgeWeeklySkillDerivedJson());
  });

  it('writes deterministic weekly skill artifacts for the configured week set', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-skill-multi-'));

    const outputPaths = writeForgeWeeklySkillDerivedArtifactsForWeeks(tempRoot);

    expect(outputPaths).toHaveLength(FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS.length);

    for (const week of FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS) {
      const basename = path.basename(getForgeWeeklySkillDerivedArtifactPath(2024, week));
      const outputPath = path.resolve(path.join(tempRoot, basename));
      const written = readFileSync(outputPath, 'utf-8');

      expect(outputPaths).toContain(outputPath);
      expect(written).toEqual(toDeterministicForgeWeeklySkillDerivedJson({ week }));
    }
  });

  it('keeps backward compatibility for the original skill artifact path', () => {
    const weekOneCommitted = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH), 'utf-8');
    expect(weekOneCommitted).toEqual(toDeterministicForgeWeeklySkillDerivedJson({ week: 1 }));
  });
});
