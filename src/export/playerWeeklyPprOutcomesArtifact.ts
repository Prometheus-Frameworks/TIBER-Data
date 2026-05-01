import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

const exportModeSchema = z.literal('historical_backtest');

const rawOutcomeRecordSchema = z.object({
  season: z.number().int().nonnegative(),
  week: z.number().int().positive(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  team: z.string().min(1),
  position: z.enum(['QB', 'RB', 'WR', 'TE']),
  opponent: z.string().min(1).nullable(),
  receptions: z.number().nonnegative().nullable(),
  targets: z.number().nonnegative().nullable(),
  receiving_yards: z.number().nullable(),
  receiving_tds: z.number().nonnegative().nullable(),
  rushing_attempts: z.number().nonnegative().nullable(),
  rushing_yards: z.number().nullable(),
  rushing_tds: z.number().nonnegative().nullable(),
  passing_yards: z.number().nullable(),
  passing_tds: z.number().nonnegative().nullable(),
  interceptions: z.number().nonnegative().nullable(),
});

const rawOutcomePayloadSchema = z.object({
  provenance: z.string().min(1),
  source_path: z.string().min(1),
  records: z.array(rawOutcomeRecordSchema),
});

const promotedOutcomeRecordSchema = z.object({
  season: z.number().int().nonnegative(),
  week: z.number().int().positive(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  team: z.string().min(1),
  position: z.enum(['QB', 'RB', 'WR', 'TE']),
  opponent: z.string().nullable(),
  receptions: z.number().nonnegative(),
  targets: z.number().nonnegative(),
  receiving_yards: z.number(),
  receiving_tds: z.number().nonnegative(),
  rushing_attempts: z.number().nonnegative(),
  rushing_yards: z.number(),
  rushing_tds: z.number().nonnegative(),
  passing_yards: z.number(),
  passing_tds: z.number().nonnegative(),
  interceptions: z.number().nonnegative(),
  ppr_points: z.number(),
  rolling_3_week_ppr: z.number(),
  rolling_5_week_ppr: z.number(),
  season_ppr: z.number(),
  games_played: z.number().int().positive(),
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type PlayerWeeklyPprOutcomesV1Record = z.infer<typeof promotedOutcomeRecordSchema>;
export type PlayerWeeklyPprOutcomesV1Array = PlayerWeeklyPprOutcomesV1Record[];

export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_PATH =
  'data/raw/evidence/player_weekly_box_scores_2025.offline_fixture.json';
export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_BACKED_SOURCE_PATH =
  'data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json';
export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH =
  'exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json';
export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_SEASON = 2025;
export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_MODE = 'historical_backtest' as const;
export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_GENERATED_AT = '2026-04-27T00:00:00Z';
export const PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_SOURCE_KIND = 'offline_fixture' as const;

const sourceKindSchema = z.enum(['offline_fixture', 'source_backed']);

export type PlayerWeeklyPprOutcomesBuildOptions = {
  sourceKind?: 'offline_fixture' | 'source_backed';
  sourcePath?: string;
  season?: number;
  mode?: string;
  generatedAt?: string;
};

function resolveSourcePath(options: PlayerWeeklyPprOutcomesBuildOptions): string {
  if (options.sourcePath) {
    return options.sourcePath;
  }

  const sourceKind = sourceKindSchema.parse(options.sourceKind ?? PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_SOURCE_KIND);
  if (sourceKind === 'source_backed') {
    return PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_BACKED_SOURCE_PATH;
  }
  return PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_PATH;
}

function parseRawPayload(sourcePath: string): RawExportPayload<z.infer<typeof rawOutcomeRecordSchema>> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return rawOutcomePayloadSchema.parse(JSON.parse(raw));
}

function assertNoDuplicatePlayerWeeks(rows: z.infer<typeof rawOutcomeRecordSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.season}-${row.week}-${row.player_id}`;
    if (seen.has(key)) {
      throw new Error(`Duplicate player-week row detected (${key}). Export fails closed.`);
    }
    seen.add(key);
  }
}

function toNumberOrZero(value: number | null): number {
  return value ?? 0;
}

function roundTo(value: number, precision: number): number {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}

export function calculatePprPoints(row: {
  receptions: number | null;
  receiving_yards: number | null;
  receiving_tds: number | null;
  rushing_yards: number | null;
  rushing_tds: number | null;
  passing_yards: number | null;
  passing_tds: number | null;
  interceptions: number | null;
}): number {
  const points =
    toNumberOrZero(row.receptions) * 1 +
    toNumberOrZero(row.receiving_yards) * 0.1 +
    toNumberOrZero(row.receiving_tds) * 6 +
    toNumberOrZero(row.rushing_yards) * 0.1 +
    toNumberOrZero(row.rushing_tds) * 6 +
    toNumberOrZero(row.passing_yards) * 0.04 +
    toNumberOrZero(row.passing_tds) * 4 -
    toNumberOrZero(row.interceptions) * 2;

  return roundTo(points, 2);
}

function rollingSum(values: number[], inclusiveIndex: number, window: number): number {
  const start = Math.max(0, inclusiveIndex - (window - 1));
  const slice = values.slice(start, inclusiveIndex + 1);
  return roundTo(slice.reduce((sum, value) => sum + value, 0), 2);
}

export function buildPlayerWeeklyPprOutcomesV1FromRawSources(
  options: PlayerWeeklyPprOutcomesBuildOptions = {},
): PlayerWeeklyPprOutcomesV1Array {
  const sourcePath = resolveSourcePath(options);
  const season = options.season ?? PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_SEASON;
  const mode = exportModeSchema.parse(options.mode ?? PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_MODE);
  const generatedAt = options.generatedAt ?? PLAYER_WEEKLY_PPR_OUTCOMES_V1_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') {
    throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  }

  z.string().datetime({ offset: true }).parse(generatedAt);

  const payload = parseRawPayload(sourcePath);
  assertNoDuplicatePlayerWeeks(payload.records);

  const seasonRows = payload.records.filter((row) => row.season === season);
  if (seasonRows.length === 0) {
    throw new Error(`No player weekly outcome rows found for season=${season}. Export fails closed.`);
  }

  const byPlayer = new Map<string, z.infer<typeof rawOutcomeRecordSchema>[]>();
  for (const row of seasonRows) {
    const key = row.player_id;
    const group = byPlayer.get(key) ?? [];
    group.push(row);
    byPlayer.set(key, group);
  }

  const output: PlayerWeeklyPprOutcomesV1Array = [];
  for (const [, rows] of byPlayer) {
    const ordered = [...rows].sort((a, b) => a.week - b.week);
    const pprByWeek = ordered.map((row) => calculatePprPoints(row));

    for (let index = 0; index < ordered.length; index += 1) {
      const row = ordered[index];
      const seasonPpr = roundTo(pprByWeek.slice(0, index + 1).reduce((sum, value) => sum + value, 0), 2);
      output.push({
        season: row.season,
        week: row.week,
        player_id: row.player_id,
        player_name: row.player_name,
        team: row.team,
        position: row.position,
        opponent: row.opponent,
        receptions: toNumberOrZero(row.receptions),
        targets: toNumberOrZero(row.targets),
        receiving_yards: toNumberOrZero(row.receiving_yards),
        receiving_tds: toNumberOrZero(row.receiving_tds),
        rushing_attempts: toNumberOrZero(row.rushing_attempts),
        rushing_yards: toNumberOrZero(row.rushing_yards),
        rushing_tds: toNumberOrZero(row.rushing_tds),
        passing_yards: toNumberOrZero(row.passing_yards),
        passing_tds: toNumberOrZero(row.passing_tds),
        interceptions: toNumberOrZero(row.interceptions),
        ppr_points: pprByWeek[index],
        rolling_3_week_ppr: rollingSum(pprByWeek, index, 3),
        rolling_5_week_ppr: rollingSum(pprByWeek, index, 5),
        season_ppr: seasonPpr,
        games_played: index + 1,
        source: `${payload.provenance}:${payload.source_path}`,
        generated_at: generatedAt,
      });
    }
  }

  const deterministic = output.sort((a, b) => {
    if (a.season !== b.season) return a.season - b.season;
    if (a.week !== b.week) return a.week - b.week;
    return a.player_id.localeCompare(b.player_id);
  });

  return z.array(promotedOutcomeRecordSchema).parse(deterministic);
}

export function toDeterministicPlayerWeeklyPprOutcomesV1Json(
  options: PlayerWeeklyPprOutcomesBuildOptions = {},
): string {
  const artifact = buildPlayerWeeklyPprOutcomesV1FromRawSources(options);
  return `${JSON.stringify(artifact, null, 2)}\n`;
}

export function writePlayerWeeklyPprOutcomesV1Artifact(
  outputPath: string = PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH,
  options: PlayerWeeklyPprOutcomesBuildOptions = {},
): string {
  const artifactJson = toDeterministicPlayerWeeklyPprOutcomesV1Json(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
