import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH,
  buildForgeWeeklyDerivedArtifactFromRawSources,
  buildForgeWeeklySkillDerivedArtifactFromRawSources,
  forgeWeeklyPlayerInputArraySchema,
  toDeterministicForgeWeeklyDerivedJson,
  toDeterministicForgeWeeklySampleJson,
  toDeterministicForgeWeeklySkillDerivedJson,
  writeForgeWeeklyDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifact,
} from '../src/index.js';

describe('forge weekly derived artifact export lanes', () => {
  it('builds a QB-only derived artifact that validates against ForgeWeeklyPlayerInput', () => {
    const artifact = buildForgeWeeklyDerivedArtifactFromRawSources();
    const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);

    expect(parsed).toHaveLength(2);
    expect(parsed.every((record) => record.position === 'QB')).toBe(true);
    expect(parsed.map((record) => record.playerId)).toEqual(['00-0033901', '00-0037183']);
  });

  it('builds a broader skill-position derived artifact for the same week', () => {
    const artifact = buildForgeWeeklySkillDerivedArtifactFromRawSources();
    const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);

    expect(parsed).toHaveLength(8);
    expect([...new Set(parsed.map((record) => record.position))].sort()).toEqual(['QB', 'RB', 'TE', 'WR']);
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
  });

  it('is deterministic and matches both committed derived artifacts', () => {
    const firstQbPass = toDeterministicForgeWeeklyDerivedJson();
    const secondQbPass = toDeterministicForgeWeeklyDerivedJson();
    const committedQb = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH), 'utf-8');

    const firstSkillPass = toDeterministicForgeWeeklySkillDerivedJson();
    const secondSkillPass = toDeterministicForgeWeeklySkillDerivedJson();
    const committedSkill = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH), 'utf-8');

    expect(firstQbPass).toEqual(secondQbPass);
    expect(firstQbPass).toEqual(committedQb);
    expect(firstSkillPass).toEqual(secondSkillPass);
    expect(firstSkillPass).toEqual(committedSkill);
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
});
