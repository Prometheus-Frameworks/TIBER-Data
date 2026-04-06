import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import {
  type ForgeWeeklyPlayerInput,
  type ForgeWeeklyPlayerInputArray,
  forgeWeeklyPlayerInputArraySchema,
} from '../contracts/v1/forgeWeeklyPlayerInput.js';

type RawExportPayload<T> = {
  provenance: string;
  source_path: string;
  records: T[];
};

type WeeklyPlayerStatsRecord = {
  player_id: string;
  full_name: string;
  position: string;
  team: string;
  season: number;
  week: number;
  targets: number;
  receptions: number;
  rushing_attempts: number;
  rushing_yards: number;
  pass_attempts: number;
  fantasy_points_ppr: number;
};

type TeamWeekContextRecord = {
  team: string;
  season: number;
  week: number;
  team_pass_attempts: number;
  team_points: number;
};

export const FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH = 'data/raw/forge/weekly_player_stats.offline_fixture.json';
export const FORGE_WEEKLY_DERIVED_TEAM_CONTEXT_SOURCE_PATH = 'data/raw/forge/team_week_context.offline_fixture.json';
export const FORGE_WEEKLY_DERIVED_ARTIFACT_PATH =
  'data/gold/forge/forge_weekly_player_input_2024_w01.qb_offline_fixture.derived.json';

function parseRawPayload<T>(sourcePath: string): RawExportPayload<T> {
  const resolvedPath = path.resolve(sourcePath);
  const raw = readFileSync(resolvedPath, 'utf-8');
  return JSON.parse(raw) as RawExportPayload<T>;
}

function roundTo(value: number, precision: number): number {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}

export type ForgeWeeklyDerivedBuildOptions = {
  playerStatsSourcePath?: string;
  teamContextSourcePath?: string;
  season?: number;
  week?: number;
  asOf?: string;
};

export function buildForgeWeeklyDerivedArtifactFromRawSources(
  options: ForgeWeeklyDerivedBuildOptions = {},
): ForgeWeeklyPlayerInputArray {
  const playerStatsSourcePath =
    options.playerStatsSourcePath ?? FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH;
  const teamContextSourcePath =
    options.teamContextSourcePath ?? FORGE_WEEKLY_DERIVED_TEAM_CONTEXT_SOURCE_PATH;
  const season = options.season ?? 2024;
  const week = options.week ?? 1;
  const asOf = options.asOf ?? '2026-04-06T00:00:00Z';

  const playerStatsPayload = parseRawPayload<WeeklyPlayerStatsRecord>(playerStatsSourcePath);
  const teamContextPayload = parseRawPayload<TeamWeekContextRecord>(teamContextSourcePath);

  const teamContextByKey = new Map<string, TeamWeekContextRecord>();
  for (const record of teamContextPayload.records) {
    teamContextByKey.set(`${record.team}-${record.season}-${record.week}`, record);
  }

  const qbSlice = playerStatsPayload.records
    .filter((record) => record.season === season && record.week === week && record.position === 'QB')
    .sort((a, b) => a.player_id.localeCompare(b.player_id));

  const derived: ForgeWeeklyPlayerInput[] = qbSlice.map((qb) => {
    const teamContext = teamContextByKey.get(`${qb.team}-${qb.season}-${qb.week}`);
    if (!teamContext) {
      throw new Error(
        `Missing team week context for ${qb.team} season ${qb.season} week ${qb.week}. Derived export fails closed.`,
      );
    }

    const opportunities = qb.pass_attempts + qb.rushing_attempts + qb.targets;
    const snapShare =
      teamContext.team_pass_attempts > 0
        ? Math.min(1, roundTo(qb.pass_attempts / teamContext.team_pass_attempts, 4))
        : 0;

    return {
      playerId: qb.player_id,
      externalIds: {
        gsisId: qb.player_id,
      },
      playerName: qb.full_name,
      position: 'QB',
      team: qb.team,
      season: qb.season,
      week: qb.week,
      asOf,
      snaps: qb.pass_attempts + qb.rushing_attempts,
      snapShare,
      routesRun: 0,
      routeParticipation: 0,
      rushAttempts: qb.rushing_attempts,
      targets: qb.targets,
      yardsPerRouteRun: 0,
      yardsPerCarry:
        qb.rushing_attempts > 0 ? roundTo(qb.rushing_yards / qb.rushing_attempts, 3) : 0,
      catchRate: qb.targets > 0 ? roundTo(qb.receptions / qb.targets, 4) : 0,
      fantasyPointsPerOpportunity:
        opportunities > 0 ? roundTo(qb.fantasy_points_ppr / opportunities, 4) : 0,
      impliedTeamTotal: teamContext.team_points,
      spread: 0,
      opponentDefenseTier: 'average',
      expectedGameScript: 'neutral',
      injuryStatus: 'healthy',
      practiceParticipation: 'not_listed',
      activeProjection: snapShare,
      roleVolatility: roundTo(1 - snapShare, 4),
      sourceUpdatedAt: asOf,
      sourceSetId: `forge-weekly-derived-qb-slice-${season}-w${String(week).padStart(2, '0')}`,
      featureCoverage: 0.74,
      qualityFlags: [
        `source_provenance:${playerStatsPayload.provenance}`,
        `source_provenance:${teamContextPayload.provenance}`,
        'routes_and_route_participation_not_available_set_to_0_for_qb_slice',
        'spread_and_matchup_tier_not_available_set_to_neutral_defaults',
      ],
      dataConfidenceHint:
        'Narrow QB-only derived export from repo raw weekly stats + team context; several fields are neutral defaults pending broader sources.',
    };
  });

  if (derived.length === 0) {
    throw new Error(
      `No QB records found in ${playerStatsSourcePath} for season=${season}, week=${week}. Derived export fails closed.`,
    );
  }

  return forgeWeeklyPlayerInputArraySchema.parse(derived);
}

export function toDeterministicForgeWeeklyDerivedJson(
  options: ForgeWeeklyDerivedBuildOptions = {},
): string {
  const validated = buildForgeWeeklyDerivedArtifactFromRawSources(options);
  return `${JSON.stringify(validated, null, 2)}\n`;
}

export function writeForgeWeeklyDerivedArtifact(
  outputPath: string = FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  options: ForgeWeeklyDerivedBuildOptions = {},
): string {
  const artifactJson = toDeterministicForgeWeeklyDerivedJson(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}
