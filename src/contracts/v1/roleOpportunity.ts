import { z } from 'zod';

import {
  confidenceTierSchema,
  positionSchema,
  primaryRoleSchema,
} from './enums.js';

const shareMetricSchema = z.number().min(0).max(1);
const nonNegativeIntegerSchema = z.number().int().min(0);
const isoDatetimeSchema = z.string().datetime({ offset: true });

export const identitySchema = z.object({
  playerId: z.string().min(1),
  playerName: z.string().min(1),
  team: z.string().min(1),
  position: positionSchema,
});

export const scopeSchema = z.object({
  season: z.number().int().min(1900),
  week: z.number().int().min(1).max(22).nullable(),
});

export const roleSchema = z.object({
  primaryRole: primaryRoleSchema,
  roleTags: z.array(z.string().min(1)),
});

export const usageSchema = z.object({
  snapShare: shareMetricSchema,
  routeParticipation: shareMetricSchema,
  targetShare: shareMetricSchema,
  airYardShare: shareMetricSchema,
  carryShare: shareMetricSchema,
  rushAttemptShare: shareMetricSchema,
  teamOpportunityShare: shareMetricSchema,
  snaps: nonNegativeIntegerSchema,
  routesRun: nonNegativeIntegerSchema,
  targets: nonNegativeIntegerSchema,
  carries: nonNegativeIntegerSchema,
});

export const opportunitySchema = z.object({
  redZoneTouchShare: shareMetricSchema,
  inside10TouchShare: shareMetricSchema,
  inside5TouchShare: shareMetricSchema,
  goalLineCarryShare: shareMetricSchema,
  redZoneTouches: nonNegativeIntegerSchema,
  inside10Touches: nonNegativeIntegerSchema,
  inside5Touches: nonNegativeIntegerSchema,
  goalLineCarries: nonNegativeIntegerSchema,
});

export const confidenceSchema = z.object({
  score: shareMetricSchema,
  tier: confidenceTierSchema,
  reasons: z.array(z.string().min(1)),
});

export const sourceSchema = z.object({
  model: z.string().min(1),
  modelVersion: z.string().min(1),
  generatedAt: isoDatetimeSchema,
  inputWindow: z.string().min(1).nullable(),
  notes: z.array(z.string().min(1)),
});

export const roleOpportunityRecordSchema = identitySchema
  .merge(scopeSchema)
  .merge(roleSchema)
  .merge(usageSchema)
  .merge(opportunitySchema)
  .extend({
    confidence: confidenceSchema,
    source: sourceSchema,
  });

export const roleOpportunityArraySchema = z.array(roleOpportunityRecordSchema);

export type Identity = z.infer<typeof identitySchema>;
export type Scope = z.infer<typeof scopeSchema>;
export type Role = z.infer<typeof roleSchema>;
export type Usage = z.infer<typeof usageSchema>;
export type Opportunity = z.infer<typeof opportunitySchema>;
export type Confidence = z.infer<typeof confidenceSchema>;
export type Source = z.infer<typeof sourceSchema>;
export type RoleOpportunityRecord = z.infer<typeof roleOpportunityRecordSchema>;
export type RoleOpportunityArray = z.infer<typeof roleOpportunityArraySchema>;
