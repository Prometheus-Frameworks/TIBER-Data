import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH,
  buildForgeWeeklyDerivedArtifactFromRawSources,
  forgeWeeklyPlayerInputArraySchema,
  toDeterministicForgeWeeklyDerivedJson,
  toDeterministicForgeWeeklySampleJson,
  writeForgeWeeklyDerivedArtifact,
} from '../src/index.js';

describe('forge weekly derived artifact export (first narrow real-ish slice)', () => {
  it('builds a QB-only derived artifact that validates against ForgeWeeklyPlayerInput', () => {
    const artifact = buildForgeWeeklyDerivedArtifactFromRawSources();
    const parsed = forgeWeeklyPlayerInputArraySchema.parse(artifact);

    expect(parsed).toHaveLength(2);
    expect(parsed.every((record) => record.position === 'QB')).toBe(true);
    expect(parsed.map((record) => record.playerId)).toEqual(['00-0033901', '00-0037183']);
  });

  it('is deterministic and matches the committed derived artifact', () => {
    const firstPass = toDeterministicForgeWeeklyDerivedJson();
    const secondPass = toDeterministicForgeWeeklyDerivedJson();
    const committed = readFileSync(path.resolve(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH), 'utf-8');

    expect(firstPass).toEqual(secondPass);
    expect(firstPass).toEqual(committed);
  });

  it('fails closed when source path is missing', () => {
    expect(() =>
      buildForgeWeeklyDerivedArtifactFromRawSources({
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
      buildForgeWeeklyDerivedArtifactFromRawSources({
        playerStatsSourcePath: invalidPlayerStatsPath,
      }),
    ).toThrow();
  });

  it('fixture-derived sample export remains available and deterministic', () => {
    const sampleJson = toDeterministicForgeWeeklySampleJson();
    expect(sampleJson).toContain('forge-weekly-input-fixtures-v1');
  });

  it('writes a deterministic derived artifact file to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-derived-'));
    const outputPath = path.join(tempRoot, 'artifact.json');

    const written = writeForgeWeeklyDerivedArtifact(outputPath);
    const fileContents = readFileSync(written, 'utf-8');

    expect(written).toEqual(path.resolve(outputPath));
    expect(fileContents).toEqual(toDeterministicForgeWeeklyDerivedJson());
  });
});
