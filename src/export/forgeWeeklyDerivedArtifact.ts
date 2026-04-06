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
  position: 'QB' | 'RB' | 'WR' | 'TE';
  team: string;
  season: number;
  week: number;
  targets: number;
  receptions: number;
  receiving_yards: number;
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
  team_rush_attempts: number;
  team_points: number;
};

export const FORGE_WEEKLY_DERIVED_PLAYER_STATS_SOURCE_PATH =
  'data/raw/forge/weekly_player_stats.offline_fixture.json';
export const FORGE_WEEKLY_DERIVED_TEAM_CONTEXT_SOURCE_PATH =
  'data/raw/forge/team_week_context.offline_fixture.json';
export const FORGE_WEEKLY_DERIVED_ARTIFACT_PATH =
  'data/gold/forge/forge_weekly_player_input_2024_w01.qb_offline_fixture.derived.json';
export const FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH =
  'data/gold/forge/forge_weekly_player_input_2024_w01.skill_offline_fixture.derived.json';
export const FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS = [1, 2, 3] as const;

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

export type ForgeWeeklySkillDerivedBuildForWeeksOptions = Omit<ForgeWeeklyDerivedBuildOptions, 'week'> & {
  weeks?: number[];
};

export type ForgeWeeklySkillDerivedArtifactByWeek = {
  season: number;
  week: number;
  artifact: ForgeWeeklyPlayerInputArray;
};

function getSources(options: ForgeWeeklyDerivedBuildOptions) {
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

  return {
    season,
    week,
    asOf,
    playerStatsPayload,
    teamContextPayload,
    teamContextByKey,
    playerStatsSourcePath,
  };
}

function assertDerivedCoverageChecks(
  derived: ForgeWeeklyPlayerInputArray,
  season: number,
  week: number,
  expectedPositions: ForgeWeeklyPlayerInput['position'][],
): void {
  if (derived.length === 0) {
    throw new Error(`Derived artifact for season=${season}, week=${week} is empty. Export fails closed.`);
  }

  for (const record of derived) {
    if (record.season !== season || record.week !== week) {
      throw new Error(
        `Derived record metadata mismatch: expected season=${season}, week=${week} but found season=${record.season}, week=${record.week}.`,
      );
    }

    if (!record.sourceSetId.includes(`${season}-w${String(week).padStart(2, '0')}`)) {
      throw new Error(
        `Derived record sourceSetId mismatch for ${record.playerId}: ${record.sourceSetId}. Export fails closed.`,
      );
    }
  }

  const observedPositions = [...new Set(derived.map((record) => record.position))].sort();
  const expectedSorted = [...new Set(expectedPositions)].sort();
  for (const expectedPosition of expectedSorted) {
    if (!observedPositions.includes(expectedPosition)) {
      throw new Error(
        `Missing expected position ${expectedPosition} for season=${season}, week=${week}. Export fails closed.`,
      );
    }
  }

  const ids = derived.map((record) => record.playerId);
  const sortedIds = [...ids].sort((a, b) => a.localeCompare(b));
  if (ids.join('|') !== sortedIds.join('|')) {
    throw new Error(`Derived records are not deterministically sorted for season=${season}, week=${week}.`);
  }
}

function deriveQbRecord(
  qb: WeeklyPlayerStatsRecord,
  teamContext: TeamWeekContextRecord,
  asOf: string,
  playerStatsProvenance: string,
  teamContextProvenance: string,
): ForgeWeeklyPlayerInput {
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
    yardsPerCarry: qb.rushing_attempts > 0 ? roundTo(qb.rushing_yards / qb.rushing_attempts, 3) : 0,
    catchRate: qb.targets > 0 ? roundTo(qb.receptions / qb.targets, 4) : 0,
    fantasyPointsPerOpportunity: opportunities > 0 ? roundTo(qb.fantasy_points_ppr / opportunities, 4) : 0,
    impliedTeamTotal: teamContext.team_points,
    spread: 0,
    opponentDefenseTier: 'average',
    expectedGameScript: 'neutral',
    injuryStatus: 'healthy',
    practiceParticipation: 'not_listed',
    activeProjection: snapShare,
    roleVolatility: roundTo(1 - snapShare, 4),
    sourceUpdatedAt: asOf,
    sourceSetId: `forge-weekly-derived-qb-slice-${qb.season}-w${String(qb.week).padStart(2, '0')}`,
    featureCoverage: 0.74,
    qualityFlags: [
      `source_provenance:${playerStatsProvenance}`,
      `source_provenance:${teamContextProvenance}`,
      'routes_and_route_participation_not_available_set_to_0_for_qb_slice',
      'spread_and_matchup_tier_not_available_set_to_neutral_defaults',
    ],
    dataConfidenceHint:
      'Narrow QB-only derived export from repo raw weekly stats + team context; several fields are neutral defaults pending broader sources.',
  };
}

function deriveSkillRecord(
  player: WeeklyPlayerStatsRecord,
  teamContext: TeamWeekContextRecord,
  asOf: string,
  playerStatsProvenance: string,
  teamContextProvenance: string,
): ForgeWeeklyPlayerInput {
  const opportunities = player.pass_attempts + player.rushing_attempts + player.targets;
  const teamOpportunities = teamContext.team_pass_attempts + teamContext.team_rush_attempts;
  const snapShare = teamOpportunities > 0 ? Math.min(1, roundTo(opportunities / teamOpportunities, 4)) : 0;

  return {
    playerId: player.player_id,
    externalIds: {
      gsisId: player.player_id,
    },
    playerName: player.full_name,
    position: player.position,
    team: player.team,
    season: player.season,
    week: player.week,
    asOf,
    snaps: opportunities,
    snapShare,
    routesRun: 0,
    routeParticipation: 0,
    rushAttempts: player.rushing_attempts,
    targets: player.targets,
    yardsPerRouteRun: 0,
    yardsPerCarry:
      player.rushing_attempts > 0 ? roundTo(player.rushing_yards / player.rushing_attempts, 3) : 0,
    catchRate: player.targets > 0 ? roundTo(player.receptions / player.targets, 4) : 0,
    fantasyPointsPerOpportunity:
      opportunities > 0 ? roundTo(player.fantasy_points_ppr / opportunities, 4) : 0,
    impliedTeamTotal: teamContext.team_points,
    spread: 0,
    opponentDefenseTier: 'average',
    expectedGameScript: 'neutral',
    injuryStatus: 'healthy',
    practiceParticipation: 'not_listed',
    activeProjection: snapShare,
    roleVolatility: roundTo(1 - snapShare, 4),
    sourceUpdatedAt: asOf,
    sourceSetId: `forge-weekly-derived-skill-slice-${player.season}-w${String(player.week).padStart(2, '0')}`,
    featureCoverage: 0.67,
    qualityFlags: [
      `source_provenance:${playerStatsProvenance}`,
      `source_provenance:${teamContextProvenance}`,
      'snaps_and_snap_share_approximated_from_player_opportunities_vs_team_pass_plus_rush_attempts',
      'routes_and_route_participation_not_available_set_to_0_for_skill_slice',
      'spread_and_matchup_tier_not_available_set_to_neutral_defaults',
    ],
    dataConfidenceHint:
      'Broader skill-position derived export (QB/RB/WR/TE) from repo offline fixture support data for engine sanity checks; not production feed parity.',
  };
}

export function buildForgeWeeklyDerivedArtifactFromRawSources(
  options: ForgeWeeklyDerivedBuildOptions = {},
): ForgeWeeklyPlayerInputArray {
  const { season, week, asOf, playerStatsPayload, teamContextPayload, teamContextByKey, playerStatsSourcePath } =
    getSources(options);

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

    return deriveQbRecord(
      qb,
      teamContext,
      asOf,
      playerStatsPayload.provenance,
      teamContextPayload.provenance,
    );
  });

  if (derived.length === 0) {
    throw new Error(
      `No QB records found in ${playerStatsSourcePath} for season=${season}, week=${week}. Derived export fails closed.`,
    );
  }

  const validated = forgeWeeklyPlayerInputArraySchema.parse(derived);
  assertDerivedCoverageChecks(validated, season, week, ['QB']);
  return validated;
}

export function buildForgeWeeklySkillDerivedArtifactFromRawSources(
  options: ForgeWeeklyDerivedBuildOptions = {},
): ForgeWeeklyPlayerInputArray {
  const { season, week, asOf, playerStatsPayload, teamContextPayload, teamContextByKey, playerStatsSourcePath } =
    getSources(options);

  const skillSlice = playerStatsPayload.records
    .filter((record) => record.season === season && record.week === week)
    .sort((a, b) => a.player_id.localeCompare(b.player_id));

  const derived: ForgeWeeklyPlayerInput[] = skillSlice.map((player) => {
    const teamContext = teamContextByKey.get(`${player.team}-${player.season}-${player.week}`);
    if (!teamContext) {
      throw new Error(
        `Missing team week context for ${player.team} season ${player.season} week ${player.week}. Derived export fails closed.`,
      );
    }

    return deriveSkillRecord(
      player,
      teamContext,
      asOf,
      playerStatsPayload.provenance,
      teamContextPayload.provenance,
    );
  });

  if (derived.length === 0) {
    throw new Error(
      `No skill-position records found in ${playerStatsSourcePath} for season=${season}, week=${week}. Derived export fails closed.`,
    );
  }

  const expectedPositions = skillSlice.map((record) => record.position);
  const validated = forgeWeeklyPlayerInputArraySchema.parse(derived);
  assertDerivedCoverageChecks(validated, season, week, expectedPositions);
  return validated;
}

export function buildForgeWeeklySkillDerivedArtifactsForWeeks(
  options: ForgeWeeklySkillDerivedBuildForWeeksOptions = {},
): ForgeWeeklySkillDerivedArtifactByWeek[] {
  const season = options.season ?? 2024;
  const requestedWeeks = options.weeks ?? [...FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS];
  const weeks = [...new Set(requestedWeeks)].sort((a, b) => a - b);

  if (weeks.length === 0) {
    throw new Error('No weeks requested for skill-derived weekly export. Export fails closed.');
  }

  return weeks.map((week) => ({
    season,
    week,
    artifact: buildForgeWeeklySkillDerivedArtifactFromRawSources({ ...options, season, week }),
  }));
}

export function getForgeWeeklySkillDerivedArtifactPath(season: number, week: number): string {
  return `data/gold/forge/forge_weekly_player_input_${season}_w${String(week).padStart(2, '0')}.skill_offline_fixture.derived.json`;
}

export function toDeterministicForgeWeeklyDerivedJson(
  options: ForgeWeeklyDerivedBuildOptions = {},
): string {
  const validated = buildForgeWeeklyDerivedArtifactFromRawSources(options);
  return `${JSON.stringify(validated, null, 2)}\n`;
}

export function toDeterministicForgeWeeklySkillDerivedJson(
  options: ForgeWeeklyDerivedBuildOptions = {},
): string {
  const validated = buildForgeWeeklySkillDerivedArtifactFromRawSources(options);
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

export function writeForgeWeeklySkillDerivedArtifact(
  outputPath: string = FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH,
  options: ForgeWeeklyDerivedBuildOptions = {},
): string {
  const artifactJson = toDeterministicForgeWeeklySkillDerivedJson(options);
  const resolvedPath = path.resolve(outputPath);

  mkdirSync(path.dirname(resolvedPath), { recursive: true });
  writeFileSync(resolvedPath, artifactJson, 'utf-8');

  return resolvedPath;
}

export function writeForgeWeeklySkillDerivedArtifactsForWeeks(
  outputRoot: string = 'data/gold/forge',
  options: ForgeWeeklySkillDerivedBuildForWeeksOptions = {},
): string[] {
  const artifactsByWeek = buildForgeWeeklySkillDerivedArtifactsForWeeks(options);

  return artifactsByWeek.map(({ season, week, artifact }) => {
    const defaultPath = getForgeWeeklySkillDerivedArtifactPath(season, week);
    const outputPath =
      outputRoot === 'data/gold/forge'
        ? defaultPath
        : path.join(outputRoot, path.basename(defaultPath));

    const resolvedPath = path.resolve(outputPath);
    mkdirSync(path.dirname(resolvedPath), { recursive: true });
    writeFileSync(resolvedPath, `${JSON.stringify(artifact, null, 2)}\n`, 'utf-8');
    return resolvedPath;
  });
}
