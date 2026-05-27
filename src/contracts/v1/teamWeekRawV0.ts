import { z } from 'zod';

const isoDatetimeSchema = z.string().datetime({ offset: true });
const nullableNumberSchema = z.number().nullable();

export const teamWeekRawProvenanceStatusSchema = z.enum([
  'fixture_scaffold',
  'sample',
  'partial_real_data',
  'governed_real_data',
  'unknown_provenance',
]);

export const teamWeekRawSourceTypeSchema = z.enum([
  'fixture',
  'sample',
  'nflverse',
  'manual_verified',
  'governed_artifact',
  'unknown',
]);

export const teamWeekRawInputSourceSchema = z.object({
  source: z.string().min(1),
  sourceType: teamWeekRawSourceTypeSchema,
  sourceSnapshotAt: isoDatetimeSchema.nullable().optional(),
  notes: z.string().min(1).optional(),
});

export const teamWeekRawCoverageSchema = z.object({
  season: z.number().int().min(1900),
  expectedTeams: z.array(z.string().min(2)),
  presentTeams: z.array(z.string().min(2)),
  missingTeams: z.array(z.string().min(2)),
  unexpectedTeams: z.array(z.string().min(2)),
  weeks: z.array(z.number().int().min(1).max(22)),
  expectedWeeks: z.array(z.number().int().min(1).max(22)),
  isFullLeague: z.boolean(),
  isFullRegularSeasonCalendar: z.boolean(),
  expectedTeamGameRows: z.number().int().min(0).nullable(),
  actualTeamGameRows: z.number().int().min(0),
  byeWeeksHandled: z.boolean(),
});

export const teamWeekRawMetadataV0Schema = z.object({
  provenanceStatus: teamWeekRawProvenanceStatusSchema,
  provenanceNotes: z.array(z.string().min(1)),
  inputSources: z.array(teamWeekRawInputSourceSchema),
  coverage: teamWeekRawCoverageSchema,
});

export const teamWeekRawRowV0Schema = z.object({
  season: z.number().int().min(1900),
  week: z.number().int().min(1).max(22),
  teamCode: z.string().min(2),
  opponentCode: z.string().min(2),
  gameId: z.string().min(1).nullable().optional(),
  isByeWeek: z.boolean().optional(),
  pointsFor: nullableNumberSchema,
  pointsAgainst: nullableNumberSchema,
  offensivePlays: nullableNumberSchema,
  neutralPlays: nullableNumberSchema,
  secondsPerPlay: nullableNumberSchema,
  passRate: nullableNumberSchema,
  neutralPassRate: nullableNumberSchema,
  rushRate: nullableNumberSchema,
  epaPerPlay: nullableNumberSchema,
  passEpaPerPlay: nullableNumberSchema,
  rushEpaPerPlay: nullableNumberSchema,
  successRate: nullableNumberSchema,
  explosivePlayRate: nullableNumberSchema,
  drives: nullableNumberSchema,
  pointsPerDrive: nullableNumberSchema,
  redZoneTrips: nullableNumberSchema,
  redZoneTdRate: nullableNumberSchema,
  sacksAllowed: nullableNumberSchema,
  pressureRateAllowed: nullableNumberSchema,
  turnovers: nullableNumberSchema,
  fantasyPointsForQB: nullableNumberSchema,
  fantasyPointsForRB: nullableNumberSchema,
  fantasyPointsForWR: nullableNumberSchema,
  fantasyPointsForTE: nullableNumberSchema,
  fantasyPointsAllowedQB: nullableNumberSchema,
  fantasyPointsAllowedRB: nullableNumberSchema,
  fantasyPointsAllowedWR: nullableNumberSchema,
  fantasyPointsAllowedTE: nullableNumberSchema,
  qbPassAllowed: nullableNumberSchema.optional(),
  qbRushAllowed: nullableNumberSchema.optional(),
  rbRushAllowed: nullableNumberSchema.optional(),
  rbRecAllowed: nullableNumberSchema.optional(),
  wrSlotAllowed: nullableNumberSchema.optional(),
  wrWideAllowed: nullableNumberSchema.optional(),
  teInlineAllowed: nullableNumberSchema.optional(),
  teSplitAllowed: nullableNumberSchema.optional(),
});

export const teamWeekRawArtifactV0Schema = z.object({
  artifact: z.literal('team_week_raw_v0'),
  generatedAt: isoDatetimeSchema,
  season: z.number().int().min(1900),
  sourceArtifacts: z.array(z.string().min(1)),
  metadata: teamWeekRawMetadataV0Schema,
  rows: z.array(teamWeekRawRowV0Schema),
});

export type TeamWeekRawProvenanceStatus = z.infer<
  typeof teamWeekRawProvenanceStatusSchema
>;
export type TeamWeekRawSourceType = z.infer<typeof teamWeekRawSourceTypeSchema>;
export type TeamWeekRawInputSource = z.infer<typeof teamWeekRawInputSourceSchema>;
export type TeamWeekRawCoverageV0 = z.infer<typeof teamWeekRawCoverageSchema>;
export type TeamWeekRawMetadataV0 = z.infer<typeof teamWeekRawMetadataV0Schema>;
export type TeamWeekRawRowV0 = z.infer<typeof teamWeekRawRowV0Schema>;
export type TeamWeekRawArtifactV0 = z.infer<typeof teamWeekRawArtifactV0Schema>;
