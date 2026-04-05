import { mkdtempSync, readFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  FORGE_WEEKLY_SAMPLE_ARTIFACT_PATH,
  buildForgeWeeklySampleArtifactFromFixtures,
  forgeWeeklyPlayerInputArraySchema,
  mixedForgeWeeklyExamples,
  toDeterministicForgeWeeklySampleJson,
  writeForgeWeeklySampleArtifact,
} from '../src/index.js';

describe('forge weekly sample artifact export groundwork', () => {
  it('builds a fixture-derived artifact that validates against the array schema', () => {
    const artifact = buildForgeWeeklySampleArtifactFromFixtures();
    expect(forgeWeeklyPlayerInputArraySchema.parse(artifact)).toEqual(mixedForgeWeeklyExamples);
  });

  it('is deterministic and matches the committed canonical sample artifact', () => {
    const firstPass = toDeterministicForgeWeeklySampleJson();
    const secondPass = toDeterministicForgeWeeklySampleJson();
    const committed = readFileSync(path.resolve(FORGE_WEEKLY_SAMPLE_ARTIFACT_PATH), 'utf-8');

    expect(firstPass).toEqual(secondPass);
    expect(firstPass).toEqual(committed);
  });

  it('fails closed when a fixture mutation violates schema validation', () => {
    const invalidFixtures = mixedForgeWeeklyExamples.map((record, index) =>
      index === 0 ? { ...record, featureCoverage: 2 } : record,
    );

    expect(() => buildForgeWeeklySampleArtifactFromFixtures(invalidFixtures)).toThrow();
  });

  it('writes a deterministic artifact file to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'forge-weekly-sample-'));
    const outputPath = path.join(tempRoot, 'artifact.json');

    const written = writeForgeWeeklySampleArtifact(outputPath);
    const fileContents = readFileSync(written, 'utf-8');

    expect(written).toEqual(path.resolve(outputPath));
    expect(fileContents).toEqual(toDeterministicForgeWeeklySampleJson());
  });
});
