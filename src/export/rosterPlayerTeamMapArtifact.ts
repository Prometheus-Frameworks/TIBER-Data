import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

const exportModeSchema = z.literal('historical_backtest');

const activeRosterStatusSchema = z.enum([
  'active',
  'inactive',
  'practice_squad',
  'injured_reserve',
  'unknown',
  'fixture_only',
]);

const sourceStatusSchema = z.enum([
  'offline_fixture',
  'source_verified',
  'needs_verification',
  'stale_or_missing_data',
]);

const rawRosterPlayerTeamMapRecordSchema = z.object({
  season: z.number().int().nonnegative(),
  week: z.number().int().positive(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  position: z.enum(['QB', 'RB', 'WR', 'TE']),
  team: z.string().min(1),
  active_roster_status: activeRosterStatusSchema,
  source_status: sourceStatusSchema,
});

const rawRosterPlayerTeamMapPayloadSchema = z.object({
  provenance: z.string().min(1),
  source_path: z.string().min(1),
  records: z.array(rawRosterPlayerTeamMapRecordSchema),
});

const promotedRosterPlayerTeamMapRecordSchema = rawRosterPlayerTeamMapRecordSchema.extend({
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type RosterPlayerTeamMapV1Record = z.infer<typeof promotedRosterPlayerTeamMapRecordSchema>;
export type RosterPlayerTeamMapV1Array = RosterPlayerTeamMapV1Record[];

export const ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH =
  'data/raw/evidence/roster_player_team_map_2025.offline_fixture.json';
export const ROSTER_PLAYER_TEAM_MAP_V1_ARTIFACT_PATH = 'exports/promoted/nfl/roster_player_team_map_v1.json';
export const ROSTER_PLAYER_TEAM_MAP_V1_DEFAULT_SEASON = 2025;
export const ROSTER_PLAYER_TEAM_MAP_V1_DEFAULT_MODE = 'historical_backtest' as const;
export const ROSTER_PLAYER_TEAM_MAP_V1_DEFAULT_GENERATED_AT = '2026-04-28T00:00:00Z';

export type RosterPlayerTeamMapBuildOptions = {
  sourcePath?: string;
  season?: number;
  mode?: string;
  generatedAt?: string;
};

function parseRawPayload(sourcePath: string): RawExportPayload<z.infer<typeof rawRosterPlayerTeamMapRecordSchema>> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return rawRosterPlayerTeamMapPayloadSchema.parse(JSON.parse(raw));
}

function assertNoDuplicateSeasonWeekPlayerRows(rows: z.infer<typeof rawRosterPlayerTeamMapRecordSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.season}-${row.week}-${row.player_id}`;
    if (seen.has(key)) {
      throw new Error(`Duplicate roster player/team row detected (${key}). Export fails closed.`);
    }
    seen.add(key);
  }
}

export function buildRosterPlayerTeamMapV1FromRawSources(
  options: RosterPlayerTeamMapBuildOptions = {},
): RosterPlayerTeamMapV1Array {
  const sourcePath = options.sourcePath ?? ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH;
  const season = options.season ?? ROSTER_PLAYER_TEAM_MAP_V1_DEFAULT_SEASON;
  const mode = exportModeSchema.parse(options.mode ?? ROSTER_PLAYER_TEAM_MAP_V1_DEFAULT_MODE);
  const generatedAt = options.generatedAt ?? ROSTER_PLAYER_TEAM_MAP_V1_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') {
    throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  }

  z.string().datetime({ offset: true }).parse(generatedAt);

  const payload = parseRawPayload(sourcePath);
  assertNoDuplicateSeasonWeekPlayerRows(payload.records);

  const seasonRows = payload.records.filter((row) => row.season === season);
  if (seasonRows.length === 0) {
    throw new Error(`No roster player/team rows found for season=${season}. Export fails closed.`);
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
      const teamSort = a.team.localeCompare(b.team);
      if (teamSort !== 0) return teamSort;
      return a.player_id.localeCompare(b.player_id);
    });

  return z.array(promotedRosterPlayerTeamMapRecordSchema).parse(deterministic);
}

export function toDeterministicRosterPlayerTeamMapV1Json(options: RosterPlayerTeamMapBuildOptions = {}): string {
  const artifact = buildRosterPlayerTeamMapV1FromRawSources(options);
  return `${JSON.stringify(artifact, null, 2)}\n`;
}

export function writeRosterPlayerTeamMapV1Artifact(
  outputPath: string = ROSTER_PLAYER_TEAM_MAP_V1_ARTIFACT_PATH,
  options: RosterPlayerTeamMapBuildOptions = {},
): string {
  const artifactJson = toDeterministicRosterPlayerTeamMapV1Json(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
