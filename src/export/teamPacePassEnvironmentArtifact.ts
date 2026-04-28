import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

const exportModeSchema = z.literal('historical_backtest');

const rateFieldSchema = z.number().min(0).max(1);

const rawTeamPacePassEnvironmentRecordSchema = z.object({
  season: z.number().int().nonnegative(),
  team: z.string().min(1),
  plays_per_game: z.number().nonnegative(),
  neutral_pass_rate: rateFieldSchema,
  pass_rate_over_expected: rateFieldSchema.nullable(),
  dropbacks_per_game: z.number().nonnegative(),
  seconds_per_snap: z.number().positive().nullable(),
  red_zone_pass_rate: rateFieldSchema,
  wr_target_share: rateFieldSchema,
  te_target_share: rateFieldSchema,
  rb_target_share: rateFieldSchema,
});

const rawTeamPacePassEnvironmentPayloadSchema = z.object({
  provenance: z.string().min(1),
  source_path: z.string().min(1),
  records: z.array(rawTeamPacePassEnvironmentRecordSchema).min(1),
});

const promotedTeamPacePassEnvironmentRecordSchema = rawTeamPacePassEnvironmentRecordSchema.extend({
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type TeamPacePassEnvironmentV1Record = z.infer<typeof promotedTeamPacePassEnvironmentRecordSchema>;
export type TeamPacePassEnvironmentV1Array = TeamPacePassEnvironmentV1Record[];

export const TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH =
  'data/raw/evidence/team_pace_pass_environment_2025.offline_fixture.json';
export const TEAM_PACE_PASS_ENVIRONMENT_V1_ARTIFACT_PATH =
  'exports/promoted/nfl/team_pace_pass_environment_v1.json';
export const TEAM_PACE_PASS_ENVIRONMENT_V1_DEFAULT_SEASON = 2025;
export const TEAM_PACE_PASS_ENVIRONMENT_V1_DEFAULT_MODE = 'historical_backtest' as const;
export const TEAM_PACE_PASS_ENVIRONMENT_V1_DEFAULT_GENERATED_AT = '2026-04-27T00:00:00Z';

export type TeamPacePassEnvironmentBuildOptions = {
  sourcePath?: string;
  season?: number;
  mode?: string;
  generatedAt?: string;
};

function parseRawPayload(
  sourcePath: string,
): RawExportPayload<z.infer<typeof rawTeamPacePassEnvironmentRecordSchema>> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return rawTeamPacePassEnvironmentPayloadSchema.parse(JSON.parse(raw));
}

function assertNoDuplicateSeasonTeamRows(rows: z.infer<typeof rawTeamPacePassEnvironmentRecordSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.season}-${row.team}`;
    if (seen.has(key)) {
      throw new Error(`Duplicate team environment row detected (${key}). Export fails closed.`);
    }
    seen.add(key);
  }
}

export function buildTeamPacePassEnvironmentV1FromRawSources(
  options: TeamPacePassEnvironmentBuildOptions = {},
): TeamPacePassEnvironmentV1Array {
  const sourcePath = options.sourcePath ?? TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH;
  const season = options.season ?? TEAM_PACE_PASS_ENVIRONMENT_V1_DEFAULT_SEASON;
  const mode = exportModeSchema.parse(options.mode ?? TEAM_PACE_PASS_ENVIRONMENT_V1_DEFAULT_MODE);
  const generatedAt = options.generatedAt ?? TEAM_PACE_PASS_ENVIRONMENT_V1_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') {
    throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  }

  z.string().datetime({ offset: true }).parse(generatedAt);

  const payload = parseRawPayload(sourcePath);
  assertNoDuplicateSeasonTeamRows(payload.records);

  const seasonRows = payload.records.filter((row) => row.season === season);
  if (seasonRows.length === 0) {
    throw new Error(`No team pace/pass environment rows found for season=${season}. Export fails closed.`);
  }

  const deterministic = seasonRows
    .map((row) => ({
      ...row,
      source: `${payload.provenance}:${payload.source_path}`,
      generated_at: generatedAt,
    }))
    .sort((a, b) => {
      if (a.season !== b.season) return a.season - b.season;
      return a.team.localeCompare(b.team);
    });

  return z.array(promotedTeamPacePassEnvironmentRecordSchema).parse(deterministic);
}

export function toDeterministicTeamPacePassEnvironmentV1Json(
  options: TeamPacePassEnvironmentBuildOptions = {},
): string {
  const artifact = buildTeamPacePassEnvironmentV1FromRawSources(options);
  return `${JSON.stringify(artifact, null, 2)}\n`;
}

export function writeTeamPacePassEnvironmentV1Artifact(
  outputPath: string = TEAM_PACE_PASS_ENVIRONMENT_V1_ARTIFACT_PATH,
  options: TeamPacePassEnvironmentBuildOptions = {},
): string {
  const artifactJson = toDeterministicTeamPacePassEnvironmentV1Json(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
