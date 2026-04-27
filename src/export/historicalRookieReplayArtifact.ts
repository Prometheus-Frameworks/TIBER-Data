import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

const exportModeSchema = z.literal('historical_backtest');

const evidenceStatusSchema = z.enum([
  'supported',
  'partially_supported',
  'contradicted',
  'needs_verification',
  'stale_or_missing_data',
]);

const rawReplayRecordSchema = z.object({
  replay_season: z.number().int().nonnegative(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  position: z.enum(['QB', 'RB', 'WR', 'TE']),
  draft_round: z.number().int().positive(),
  draft_pick: z.number().int().positive(),
  nfl_team: z.string().min(1),
  archetype_label: z.string().min(1),
  archetype_comp_2026: z.string().min(1),
  pre_draft_grade: z.number(),
  post_draft_context_tags: z.array(z.string().min(1)),
  expected_role: z.string().min(1),
  actual_weekly_ppr: z.array(z.number()).min(1),
  role_materialized: z.boolean(),
  target_share_materialized: z.boolean(),
  environment_supported: z.boolean(),
  model_was_right_for_wrong_reason: z.boolean(),
  model_was_wrong_for_right_reason: z.boolean(),
  evidence_status: evidenceStatusSchema,
  notes: z.string(),
});

const rawReplayPayloadSchema = z.object({
  provenance: z.string().min(1),
  source_path: z.string().min(1),
  records: z.array(rawReplayRecordSchema).min(1),
});

const promotedReplayRecordSchema = rawReplayRecordSchema.extend({
  season_ppr: z.number(),
  games_played: z.number().int().nonnegative(),
  startable_weeks: z.number().int().nonnegative(),
  spike_weeks: z.number().int().nonnegative(),
  bust_weeks: z.number().int().nonnegative(),
  weekly_volatility: z.number().nonnegative(),
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type HistoricalRookieReplayV0Record = z.infer<typeof promotedReplayRecordSchema>;
export type HistoricalRookieReplayV0Array = HistoricalRookieReplayV0Record[];

export const HISTORICAL_ROOKIE_REPLAY_V0_SOURCE_PATH =
  'data/raw/evidence/historical_rookie_replay_2025.offline_fixture.json';
export const HISTORICAL_ROOKIE_REPLAY_V0_ARTIFACT_PATH =
  'exports/promoted/rookie-replay/historical_rookie_replay_v0.json';
export const HISTORICAL_ROOKIE_REPLAY_V0_DEFAULT_SEASON = 2025;
export const HISTORICAL_ROOKIE_REPLAY_V0_DEFAULT_MODE = 'historical_backtest' as const;
export const HISTORICAL_ROOKIE_REPLAY_V0_DEFAULT_GENERATED_AT = '2026-04-27T00:00:00Z';

const STARTABLE_PPR_THRESHOLD = 12;
const SPIKE_PPR_THRESHOLD = 20;
const BUST_PPR_THRESHOLD = 8;

export type HistoricalRookieReplayBuildOptions = {
  sourcePath?: string;
  replaySeason?: number;
  mode?: string;
  generatedAt?: string;
};

function parseRawPayload(sourcePath: string): RawExportPayload<z.infer<typeof rawReplayRecordSchema>> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return rawReplayPayloadSchema.parse(JSON.parse(raw));
}

function assertNoDuplicateReplayPlayers(rows: z.infer<typeof rawReplayRecordSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.replay_season}-${row.player_id}`;
    if (seen.has(key)) {
      throw new Error(`Duplicate replay row detected (${key}). Export fails closed.`);
    }
    seen.add(key);
  }
}

function roundTo(value: number, precision: number): number {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}

function calculateSeasonPpr(actualWeeklyPpr: number[]): number {
  return roundTo(actualWeeklyPpr.reduce((sum, value) => sum + value, 0), 2);
}

function calculateWeeklyVolatility(actualWeeklyPpr: number[]): number {
  const mean = actualWeeklyPpr.reduce((sum, value) => sum + value, 0) / actualWeeklyPpr.length;
  const variance =
    actualWeeklyPpr.reduce((sum, value) => sum + (value - mean) ** 2, 0) / actualWeeklyPpr.length;

  return roundTo(Math.sqrt(variance), 4);
}

export function buildHistoricalRookieReplayV0FromRawSources(
  options: HistoricalRookieReplayBuildOptions = {},
): HistoricalRookieReplayV0Array {
  const sourcePath = options.sourcePath ?? HISTORICAL_ROOKIE_REPLAY_V0_SOURCE_PATH;
  const replaySeason = options.replaySeason ?? HISTORICAL_ROOKIE_REPLAY_V0_DEFAULT_SEASON;
  const mode = exportModeSchema.parse(options.mode ?? HISTORICAL_ROOKIE_REPLAY_V0_DEFAULT_MODE);
  const generatedAt = options.generatedAt ?? HISTORICAL_ROOKIE_REPLAY_V0_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') {
    throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  }

  z.string().datetime({ offset: true }).parse(generatedAt);

  const payload = parseRawPayload(sourcePath);
  assertNoDuplicateReplayPlayers(payload.records);

  const seasonRows = payload.records.filter((row) => row.replay_season === replaySeason);
  if (seasonRows.length === 0) {
    throw new Error(`No historical rookie replay rows found for replay_season=${replaySeason}. Export fails closed.`);
  }

  const deterministic = seasonRows
    .map((row) => {
      const actualWeeklyPpr = [...row.actual_weekly_ppr];
      const seasonPpr = calculateSeasonPpr(actualWeeklyPpr);
      const gamesPlayed = actualWeeklyPpr.length;
      const startableWeeks = actualWeeklyPpr.filter((points) => points >= STARTABLE_PPR_THRESHOLD).length;
      const spikeWeeks = actualWeeklyPpr.filter((points) => points >= SPIKE_PPR_THRESHOLD).length;
      const bustWeeks = actualWeeklyPpr.filter((points) => points < BUST_PPR_THRESHOLD).length;
      const weeklyVolatility = calculateWeeklyVolatility(actualWeeklyPpr);

      return {
        ...row,
        actual_weekly_ppr: actualWeeklyPpr,
        season_ppr: seasonPpr,
        games_played: gamesPlayed,
        startable_weeks: startableWeeks,
        spike_weeks: spikeWeeks,
        bust_weeks: bustWeeks,
        weekly_volatility: weeklyVolatility,
        source: `${payload.provenance}:${payload.source_path}`,
        generated_at: generatedAt,
      };
    })
    .sort((a, b) => {
      if (a.replay_season !== b.replay_season) return a.replay_season - b.replay_season;
      return a.player_id.localeCompare(b.player_id);
    });

  return z.array(promotedReplayRecordSchema).parse(deterministic);
}

export function toDeterministicHistoricalRookieReplayV0Json(
  options: HistoricalRookieReplayBuildOptions = {},
): string {
  const artifact = buildHistoricalRookieReplayV0FromRawSources(options);
  return `${JSON.stringify(artifact, null, 2)}\n`;
}

export function writeHistoricalRookieReplayV0Artifact(
  outputPath: string = HISTORICAL_ROOKIE_REPLAY_V0_ARTIFACT_PATH,
  options: HistoricalRookieReplayBuildOptions = {},
): string {
  const artifactJson = toDeterministicHistoricalRookieReplayV0Json(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
