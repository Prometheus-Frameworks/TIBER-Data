import { z } from 'zod';

export const nflmetaText = z.string().min(1).max(256).regex(/\S/);
export const nflmetaHash = z.string().regex(/^[a-f0-9]{64}$/);
export const nflmetaInteger = z.number().int().safe().nonnegative();
export const nflmetaTimestamp = z.string().datetime({ offset: true });
export const nflmetaDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine(value => {
  const time = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) === value;
}, 'Invalid calendar date');

/** This receipt describes an invented test observation, never provider acquisition. */
export const nflmetaSyntheticReceiptSchema = z.object({
  fixtureId: z.string().regex(/^synthetic-[a-z0-9-]+$/),
  receivedAt: nflmetaTimestamp,
}).strict();

export function nflmetaSyntheticEvidence(receipt: unknown) {
  return {
    contract: 'tiber_nflmeta_synthetic_v0' as const,
    provenance: 'synthetic_only' as const,
    provider: 'nflmeta' as const,
    ...nflmetaSyntheticReceiptSchema.parse(receipt),
    providerPublishedAt: null,
    upstreamLineage: 'unqualified' as const,
    independentVerification: 'not_performed' as const,
    sourceAdmission: 'not_admitted' as const,
    retentionRights: 'unresolved' as const,
    replayRights: 'unresolved' as const,
  };
}
