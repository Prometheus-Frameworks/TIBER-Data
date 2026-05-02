import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

const exportModeSchema = z.literal('historical_backtest');

const rawUsageRecordSchema = z.object({
  season: z.number().int().nonnegative(),
  week: z.number().int().positive(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  team: z.string().min(1),
  position: z.enum(['QB', 'RB', 'WR', 'TE']),
  opponent: z.string().min(1),
  targets: z.number().nonnegative(),
  receptions: z.number().nonnegative(),
  routes_run: z.number().nonnegative().nullable(),
  route_participation: z.number().min(0).max(1).nullable(),
  target_share: z.number().min(0).max(1),
  air_yards: z.number(),
  air_yards_share: z.number().min(0).max(1),
  rushing_attempts: z.number().nonnegative(),
  team_rushing_attempts: z.number().nonnegative().nullable(),
  rush_share: z.number().min(0).max(1).nullable(),
  red_zone_targets: z.number().nonnegative().nullable(),
  red_zone_carries: z.number().nonnegative().nullable(),
  snap_share: z.number().min(0).max(1).nullable(),
});

const rawUsagePayloadSchema = z.object({
  provenance: z.string().min(1),
  source_path: z.string().min(1),
  records: z.array(rawUsageRecordSchema),
});

const promotedUsageRecordSchema = rawUsageRecordSchema.extend({
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type PlayerWeeklyUsageV1Record = z.infer<typeof promotedUsageRecordSchema>;
export type PlayerWeeklyUsageV1Array = PlayerWeeklyUsageV1Record[];

export const PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH =
  'data/raw/evidence/player_weekly_usage_2025.offline_fixture.json';
export const PLAYER_WEEKLY_USAGE_V1_SOURCE_BACKED_SOURCE_PATH =
  'data/processed/evidence/player_weekly_usage_2025.source_backed.json';
export const PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH = 'exports/promoted/nfl/player_weekly_usage_v1.json';
export const PLAYER_WEEKLY_USAGE_V1_DEFAULT_SEASON = 2025;
export const PLAYER_WEEKLY_USAGE_V1_DEFAULT_MODE = 'historical_backtest' as const;
export const PLAYER_WEEKLY_USAGE_V1_DEFAULT_GENERATED_AT = '2026-04-27T00:00:00Z';
export const PLAYER_WEEKLY_USAGE_V1_DEFAULT_SOURCE_KIND = 'offline_fixture' as const;

const sourceKindSchema = z.enum(['offline_fixture', 'source_backed']);

export type PlayerWeeklyUsageBuildOptions = {
  sourceKind?: 'offline_fixture' | 'source_backed';
  sourcePath?: string;
  season?: number;
  mode?: string;
  generatedAt?: string;
};


function resolveSourcePath(options: PlayerWeeklyUsageBuildOptions): string {
  if (options.sourcePath) {
    return options.sourcePath;
  }

  const sourceKind = sourceKindSchema.parse(options.sourceKind ?? PLAYER_WEEKLY_USAGE_V1_DEFAULT_SOURCE_KIND);
  if (sourceKind === 'source_backed') {
    return PLAYER_WEEKLY_USAGE_V1_SOURCE_BACKED_SOURCE_PATH;
  }
  return PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH;
}

function parseRawPayload(sourcePath: string): RawExportPayload<z.infer<typeof rawUsageRecordSchema>> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return rawUsagePayloadSchema.parse(JSON.parse(raw));
}

function assertNoDuplicatePlayerWeeks(rows: z.infer<typeof rawUsageRecordSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.season}-${row.week}-${row.player_id}`;
    if (seen.has(key)) {
      throw new Error(`Duplicate player-week row detected (${key}). Export fails closed.`);
    }
    seen.add(key);
  }
}

export function buildPlayerWeeklyUsageV1FromRawSources(
  options: PlayerWeeklyUsageBuildOptions = {},
): PlayerWeeklyUsageV1Array {
  const sourcePath = resolveSourcePath(options);
  const season = options.season ?? PLAYER_WEEKLY_USAGE_V1_DEFAULT_SEASON;
  const mode = exportModeSchema.parse(options.mode ?? PLAYER_WEEKLY_USAGE_V1_DEFAULT_MODE);
  const generatedAt = options.generatedAt ?? PLAYER_WEEKLY_USAGE_V1_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') {
    throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  }

  z.string().datetime({ offset: true }).parse(generatedAt);

  const payload = parseRawPayload(sourcePath);
  assertNoDuplicatePlayerWeeks(payload.records);

  const seasonRows = payload.records.filter((row) => row.season === season);
  if (seasonRows.length === 0) {
    throw new Error(`No player weekly usage rows found for season=${season}. Export fails closed.`);
  }

  const deterministic = seasonRows
    .map((row) => ({
      ...row,
      source: `${payload.provenance}:${payload.source_path}`,
      generated_at: generatedAt,
    }))
    .sort((a, b) => {
      if (a.season !== b.season) return a.season - b.season;
      if (a.week !== b.week) return a.week - b.week;
      return a.player_id.localeCompare(b.player_id);
    });

  return z.array(promotedUsageRecordSchema).parse(deterministic);
}

export function toDeterministicPlayerWeeklyUsageV1Json(options: PlayerWeeklyUsageBuildOptions = {}): string {
  const artifact = buildPlayerWeeklyUsageV1FromRawSources(options);
  return `${JSON.stringify(artifact, null, 2)}\n`;
}

export function writePlayerWeeklyUsageV1Artifact(
  outputPath: string = PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH,
  options: PlayerWeeklyUsageBuildOptions = {},
): string {
  const artifactJson = toDeterministicPlayerWeeklyUsageV1Json(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
