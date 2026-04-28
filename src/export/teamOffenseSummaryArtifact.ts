import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

const exportModeSchema = z.literal('historical_backtest');

const optionalRateFieldSchema = z.number().min(0).max(1).nullable();
const optionalEpaFieldSchema = z.number().min(-1).max(1).nullable();

const rawTeamOffenseSummaryRecordSchema = z.object({
  season: z.number().int().nonnegative(),
  team: z.string().min(1),
  points_per_game: z.number().nonnegative(),
  yards_per_play: z.number().nonnegative(),
  offensive_plays_per_game: z.number().nonnegative(),
  touchdowns_per_game: z.number().nonnegative(),
  scoring_drive_rate: optionalRateFieldSchema,
  turnover_rate: z.number().min(0).max(1),
  offensive_epa_per_play: optionalEpaFieldSchema,
  offensive_success_rate: optionalRateFieldSchema,
  red_zone_td_rate: optionalRateFieldSchema,
  third_down_conversion_rate: optionalRateFieldSchema,
});

const rawTeamOffenseSummaryPayloadSchema = z.object({
  provenance: z.string().min(1),
  source_path: z.string().min(1),
  records: z.array(rawTeamOffenseSummaryRecordSchema).min(1),
});

const promotedTeamOffenseSummaryRecordSchema = rawTeamOffenseSummaryRecordSchema.extend({
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type TeamOffenseSummaryV1Record = z.infer<typeof promotedTeamOffenseSummaryRecordSchema>;
export type TeamOffenseSummaryV1Array = TeamOffenseSummaryV1Record[];

export const TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH = 'data/raw/evidence/team_offense_summary_2025.offline_fixture.json';
export const TEAM_OFFENSE_SUMMARY_V1_ARTIFACT_PATH = 'exports/promoted/nfl/team_offense_summary_v1.json';
export const TEAM_OFFENSE_SUMMARY_V1_DEFAULT_SEASON = 2025;
export const TEAM_OFFENSE_SUMMARY_V1_DEFAULT_MODE = 'historical_backtest' as const;
export const TEAM_OFFENSE_SUMMARY_V1_DEFAULT_GENERATED_AT = '2026-04-28T00:00:00Z';

export type TeamOffenseSummaryBuildOptions = {
  sourcePath?: string;
  season?: number;
  mode?: string;
  generatedAt?: string;
};

function parseRawPayload(sourcePath: string): RawExportPayload<z.infer<typeof rawTeamOffenseSummaryRecordSchema>> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return rawTeamOffenseSummaryPayloadSchema.parse(JSON.parse(raw));
}

function assertNoDuplicateSeasonTeamRows(rows: z.infer<typeof rawTeamOffenseSummaryRecordSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.season}-${row.team}`;
    if (seen.has(key)) {
      throw new Error(`Duplicate team offense summary row detected (${key}). Export fails closed.`);
    }
    seen.add(key);
  }
}

export function buildTeamOffenseSummaryV1FromRawSources(
  options: TeamOffenseSummaryBuildOptions = {},
): TeamOffenseSummaryV1Array {
  const sourcePath = options.sourcePath ?? TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH;
  const season = options.season ?? TEAM_OFFENSE_SUMMARY_V1_DEFAULT_SEASON;
  const mode = exportModeSchema.parse(options.mode ?? TEAM_OFFENSE_SUMMARY_V1_DEFAULT_MODE);
  const generatedAt = options.generatedAt ?? TEAM_OFFENSE_SUMMARY_V1_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') {
    throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  }

  z.string().datetime({ offset: true }).parse(generatedAt);

  const payload = parseRawPayload(sourcePath);
  assertNoDuplicateSeasonTeamRows(payload.records);

  const seasonRows = payload.records.filter((row) => row.season === season);
  if (seasonRows.length === 0) {
    throw new Error(`No team offense summary rows found for season=${season}. Export fails closed.`);
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

  return z.array(promotedTeamOffenseSummaryRecordSchema).parse(deterministic);
}

export function toDeterministicTeamOffenseSummaryV1Json(options: TeamOffenseSummaryBuildOptions = {}): string {
  const artifact = buildTeamOffenseSummaryV1FromRawSources(options);
  return `${JSON.stringify(artifact, null, 2)}\n`;
}

export function writeTeamOffenseSummaryV1Artifact(
  outputPath: string = TEAM_OFFENSE_SUMMARY_V1_ARTIFACT_PATH,
  options: TeamOffenseSummaryBuildOptions = {},
): string {
  const artifactJson = toDeterministicTeamOffenseSummaryV1Json(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
