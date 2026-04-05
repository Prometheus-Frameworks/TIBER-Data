import { z } from 'zod';

import {
  expectedGameScriptSchema,
  injuryStatusSchema,
  opponentDefenseTierSchema,
  positionSchema,
  practiceParticipationSchema,
} from './enums.js';

const shareMetricSchema = z.number().min(0).max(1);
const nonNegativeIntegerSchema = z.number().int().min(0);
const nonNegativeNumberSchema = z.number().min(0);
const seasonSchema = z.number().int().min(1900);
const weekSchema = z.number().int().min(1).max(22);
const isoDatetimeSchema = z.string().datetime({ offset: true });
const teamCodeSchema = z.string().regex(/^[A-Z]{2,4}$/);

export const forgePlayerExternalIdsSchema = z
  .object({
    gsisId: z.string().min(1).nullable(),
    pfrId: z.string().min(1).nullable(),
    sleeperId: z.string().min(1).nullable(),
  })
  .partial();

export const forgeIdentitySchema = z.object({
  playerId: z.string().min(1),
  externalIds: forgePlayerExternalIdsSchema.optional(),
  playerName: z.string().min(1),
  position: positionSchema,
  team: teamCodeSchema,
});

export const forgeScopeSchema = z.object({
  season: seasonSchema,
  week: weekSchema,
  asOf: isoDatetimeSchema,
});

export const forgeUsageSchema = z.object({
  snaps: nonNegativeIntegerSchema,
  snapShare: shareMetricSchema,
  routesRun: nonNegativeIntegerSchema,
  routeParticipation: shareMetricSchema,
  rushAttempts: nonNegativeIntegerSchema,
  targets: nonNegativeIntegerSchema,
});

export const forgeEfficiencySchema = z.object({
  yardsPerRouteRun: nonNegativeNumberSchema,
  yardsPerCarry: nonNegativeNumberSchema,
  catchRate: shareMetricSchema,
  fantasyPointsPerOpportunity: nonNegativeNumberSchema,
});

export const forgeTeamContextSchema = z.object({
  impliedTeamTotal: z.number().min(0).max(80),
  spread: z.number().min(-40).max(40),
  opponentDefenseTier: opponentDefenseTierSchema,
  expectedGameScript: expectedGameScriptSchema,
});

export const forgeStabilitySchema = z.object({
  injuryStatus: injuryStatusSchema,
  practiceParticipation: practiceParticipationSchema,
  activeProjection: shareMetricSchema,
  roleVolatility: shareMetricSchema,
});

export const forgeProvenanceSchema = z.object({
  sourceUpdatedAt: isoDatetimeSchema,
  sourceSetId: z.string().min(1),
  featureCoverage: shareMetricSchema,
  qualityFlags: z.array(z.string().min(1)).optional(),
  dataConfidenceHint: z.string().min(1).optional(),
});

export const forgeWeeklyPlayerInputSchema = forgeIdentitySchema
  .merge(forgeScopeSchema)
  .merge(forgeUsageSchema)
  .merge(forgeEfficiencySchema)
  .merge(forgeTeamContextSchema)
  .merge(forgeStabilitySchema)
  .merge(forgeProvenanceSchema);

export const forgeWeeklyPlayerInputArraySchema = z.array(forgeWeeklyPlayerInputSchema);

export type ForgePlayerExternalIds = z.infer<typeof forgePlayerExternalIdsSchema>;
export type ForgeIdentity = z.infer<typeof forgeIdentitySchema>;
export type ForgeScope = z.infer<typeof forgeScopeSchema>;
export type ForgeUsage = z.infer<typeof forgeUsageSchema>;
export type ForgeEfficiency = z.infer<typeof forgeEfficiencySchema>;
export type ForgeTeamContext = z.infer<typeof forgeTeamContextSchema>;
export type ForgeStability = z.infer<typeof forgeStabilitySchema>;
export type ForgeProvenance = z.infer<typeof forgeProvenanceSchema>;
export type ForgeWeeklyPlayerInput = z.infer<typeof forgeWeeklyPlayerInputSchema>;
export type ForgeWeeklyPlayerInputArray = z.infer<typeof forgeWeeklyPlayerInputArraySchema>;
