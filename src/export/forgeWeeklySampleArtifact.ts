import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { mixedForgeWeeklyExamples } from '../contracts/v1/forgeWeeklyExamples.js';
import {
  type ForgeWeeklyPlayerInputArray,
  forgeWeeklyPlayerInputArraySchema,
} from '../contracts/v1/forgeWeeklyPlayerInput.js';

export const FORGE_WEEKLY_SAMPLE_ARTIFACT_PATH =
  'data/gold/forge/forge_weekly_player_input_2025_w12.sample.json';

export function buildForgeWeeklySampleArtifactFromFixtures(
  fixtures: unknown = mixedForgeWeeklyExamples,
): ForgeWeeklyPlayerInputArray {
  return forgeWeeklyPlayerInputArraySchema.parse(fixtures);
}

export function toDeterministicForgeWeeklySampleJson(
  fixtures: unknown = mixedForgeWeeklyExamples,
): string {
  const validated = buildForgeWeeklySampleArtifactFromFixtures(fixtures);
  return `${JSON.stringify(validated, null, 2)}\n`;
}

export function writeForgeWeeklySampleArtifact(
  outputPath: string = FORGE_WEEKLY_SAMPLE_ARTIFACT_PATH,
  fixtures: unknown = mixedForgeWeeklyExamples,
): string {
  const artifactJson = toDeterministicForgeWeeklySampleJson(fixtures);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
