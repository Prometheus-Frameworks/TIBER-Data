import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { z } from 'zod';

const exportModeSchema = z.literal('historical_backtest');
const readinessStatusSchema = z.enum([
  'ready',
  'partial',
  'missing_identity',
  'missing_team_context',
  'mismatch',
  'stale_or_missing_data',
]);

const replayRowSchema = z.object({
  replay_season: z.number().int().nonnegative(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  position: z.string().min(1),
  nfl_team: z.string().min(1),
});

const rosterRowSchema = z.object({
  season: z.number().int().nonnegative(),
  week: z.number().int().positive(),
  player_id: z.string().min(1),
  team: z.string().min(1),
});

const teamContextRowSchema = z.object({
  season: z.number().int().nonnegative(),
  team: z.string().min(1),
});

const readinessRowSchema = z.object({
  replay_season: z.number().int().nonnegative(),
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  position: z.string().min(1),
  expected_team: z.string().min(1),
  roster_team: z.string().min(1).nullable(),
  roster_identity_found: z.boolean(),
  team_pace_pass_found: z.boolean(),
  team_offense_summary_found: z.boolean(),
  team_context_ready: z.boolean(),
  missing_evidence: z.array(z.string().min(1)),
  readiness_status: readinessStatusSchema,
  readiness_notes: z.string(),
  source: z.string().min(1),
  generated_at: z.string().datetime({ offset: true }),
});

export type HistoricalRookieReplayReadinessV0Record = z.infer<typeof readinessRowSchema>;
export type HistoricalRookieReplayReadinessV0Array = HistoricalRookieReplayReadinessV0Record[];

export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_ARTIFACT_PATH =
  'exports/promoted/rookie-replay/historical_rookie_replay_readiness_v0.json';
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_REPLAY_PATH =
  'exports/promoted/rookie-replay/historical_rookie_replay_v0.json';
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_ROSTER_PATH =
  'exports/promoted/nfl/roster_player_team_map_v1.json';
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_PACE_PASS_PATH =
  'exports/promoted/nfl/team_pace_pass_environment_v1.json';
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_OFFENSE_SUMMARY_PATH =
  'exports/promoted/nfl/team_offense_summary_v1.json';
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_SEASON = 2025;
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_MODE = 'historical_backtest' as const;
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_ROSTER_WEEK = 1;
export const HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_GENERATED_AT = '2026-04-28T00:00:00Z';

export type HistoricalRookieReplayReadinessBuildOptions = {
  replayPath?: string;
  rosterPath?: string;
  teamPacePassPath?: string;
  teamOffenseSummaryPath?: string;
  replaySeason?: number;
  rosterWeek?: number;
  mode?: string;
  generatedAt?: string;
};

function readRequiredJson(pathValue: string): unknown {
  const resolved = path.resolve(pathValue);
  if (!existsSync(resolved)) {
    throw new Error(`Required artifact is missing: ${resolved}. Export fails closed.`);
  }

  return JSON.parse(readFileSync(resolved, 'utf-8'));
}

function assertNoDuplicateReplayRows(rows: z.infer<typeof replayRowSchema>[]): void {
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.replay_season}-${row.player_id}`;
    if (seen.has(key)) throw new Error(`Duplicate replay row detected (${key}). Export fails closed.`);
    seen.add(key);
  }
}

function assertNoDuplicateRosterRows(rows: z.infer<typeof rosterRowSchema>[], replaySeason: number): void {
  const seen = new Set<string>();
  for (const row of rows) {
    if (row.season !== replaySeason) continue;
    const key = `${row.season}-${row.week}-${row.player_id}`;
    if (seen.has(key)) throw new Error(`Duplicate roster row detected (${key}). Export fails closed.`);
    seen.add(key);
  }
}

function assertNoDuplicateTeamRows(rows: z.infer<typeof teamContextRowSchema>[], replaySeason: number, label: string): void {
  const seen = new Set<string>();
  for (const row of rows) {
    if (row.season !== replaySeason) continue;
    const key = `${row.season}-${row.team}`;
    if (seen.has(key)) throw new Error(`Duplicate ${label} row detected (${key}). Export fails closed.`);
    seen.add(key);
  }
}

export function buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts(
  options: HistoricalRookieReplayReadinessBuildOptions = {},
): HistoricalRookieReplayReadinessV0Array {
  const mode = exportModeSchema.parse(options.mode ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_MODE);
  const replaySeason = options.replaySeason ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_SEASON;
  const rosterWeek = z.number().int().positive().parse(
    options.rosterWeek ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_ROSTER_WEEK,
  );
  const generatedAt = options.generatedAt ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_DEFAULT_GENERATED_AT;

  if (mode !== 'historical_backtest') throw new Error(`Unsupported mode ${mode}. Only historical_backtest is allowed.`);
  z.string().datetime({ offset: true }).parse(generatedAt);

  const replayRows = z.array(replayRowSchema).parse(readRequiredJson(options.replayPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_REPLAY_PATH));
  const rosterRows = z.array(rosterRowSchema).parse(readRequiredJson(options.rosterPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_ROSTER_PATH));
  const paceRows = z.array(teamContextRowSchema).parse(readRequiredJson(options.teamPacePassPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_PACE_PASS_PATH));
  const offenseRows = z.array(teamContextRowSchema).parse(readRequiredJson(options.teamOffenseSummaryPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_OFFENSE_SUMMARY_PATH));

  assertNoDuplicateReplayRows(replayRows);
  assertNoDuplicateRosterRows(rosterRows, replaySeason);
  assertNoDuplicateTeamRows(paceRows, replaySeason, 'team_pace_pass_environment');
  assertNoDuplicateTeamRows(offenseRows, replaySeason, 'team_offense_summary');

  const seasonReplayRows = replayRows.filter((row) => row.replay_season === replaySeason);
  if (seasonReplayRows.length === 0) {
    throw new Error(`No replay rows found for replay_season=${replaySeason}. Export fails closed.`);
  }

  const rosterByPlayerId = new Map(
    rosterRows
      .filter((row) => row.season === replaySeason && row.week === rosterWeek)
      .map((row) => [row.player_id, row]),
  );
  const paceTeams = new Set(paceRows.filter((row) => row.season === replaySeason).map((row) => row.team));
  const offenseTeams = new Set(offenseRows.filter((row) => row.season === replaySeason).map((row) => row.team));

  const source = [
    `replay:${options.replayPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_REPLAY_PATH}`,
    `roster:${options.rosterPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_ROSTER_PATH}#week=${rosterWeek}`,
    `team_pace_pass:${options.teamPacePassPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_PACE_PASS_PATH}`,
    `team_offense_summary:${options.teamOffenseSummaryPath ?? HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_OFFENSE_SUMMARY_PATH}`,
  ].join('|');

  const out = seasonReplayRows
    .map((replayRow) => {
      const expectedTeam = replayRow.nfl_team;
      const roster = rosterByPlayerId.get(replayRow.player_id);
      const rosterIdentityFound = Boolean(roster);
      const rosterTeam = roster?.team ?? null;
      const teamForContext = rosterTeam ?? expectedTeam;
      const teamPacePassFound = paceTeams.has(teamForContext);
      const teamOffenseSummaryFound = offenseTeams.has(teamForContext);
      const teamContextReady = rosterIdentityFound && teamPacePassFound && teamOffenseSummaryFound;

      const missingEvidence: string[] = [];
      if (!rosterIdentityFound) missingEvidence.push('roster_identity');
      if (!teamPacePassFound) missingEvidence.push('team_pace_pass_environment');
      if (!teamOffenseSummaryFound) missingEvidence.push('team_offense_summary');

      let readinessStatus: z.infer<typeof readinessStatusSchema> = 'stale_or_missing_data';
      let readinessNotes = 'Readiness unresolved due to stale or missing data.';

      if (!rosterIdentityFound) {
        readinessStatus = 'missing_identity';
        readinessNotes = 'No exact player_id match in roster map; name fallback is not allowed in v0.';
      } else if (rosterTeam !== expectedTeam) {
        readinessStatus = 'mismatch';
        readinessNotes = `Roster team (${rosterTeam}) differs from expected replay team (${expectedTeam}).`;
      } else if (teamPacePassFound && teamOffenseSummaryFound) {
        readinessStatus = 'ready';
        readinessNotes = 'Identity and team context artifacts are present for replay join.';
      } else if (!teamPacePassFound && !teamOffenseSummaryFound) {
        readinessStatus = 'missing_team_context';
        readinessNotes = 'Identity found, but both team context artifacts are missing.';
      } else {
        readinessStatus = 'partial';
        readinessNotes = 'Identity found, but one team context artifact is missing.';
      }

      return {
        replay_season: replayRow.replay_season,
        player_id: replayRow.player_id,
        player_name: replayRow.player_name,
        position: replayRow.position,
        expected_team: expectedTeam,
        roster_team: rosterTeam,
        roster_identity_found: rosterIdentityFound,
        team_pace_pass_found: teamPacePassFound,
        team_offense_summary_found: teamOffenseSummaryFound,
        team_context_ready: teamContextReady,
        missing_evidence: missingEvidence,
        readiness_status: readinessStatus,
        readiness_notes: readinessNotes,
        source,
        generated_at: generatedAt,
      };
    })
    .sort((a, b) => (a.replay_season === b.replay_season ? a.player_id.localeCompare(b.player_id) : a.replay_season - b.replay_season));

  return z.array(readinessRowSchema).parse(out);
}

export function toDeterministicHistoricalRookieReplayReadinessV0Json(
  options: HistoricalRookieReplayReadinessBuildOptions = {},
): string {
  return `${JSON.stringify(buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts(options), null, 2)}\n`;
}

export function writeHistoricalRookieReplayReadinessV0Artifact(
  outputPath: string = HISTORICAL_ROOKIE_REPLAY_READINESS_V0_ARTIFACT_PATH,
  options: HistoricalRookieReplayReadinessBuildOptions = {},
): string {
  const artifactJson = toDeterministicHistoricalRookieReplayReadinessV0Json(options);
  const resolvedPath = path.resolve(outputPath);
  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');
  return resolvedPath;
}
