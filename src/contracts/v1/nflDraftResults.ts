import { z } from 'zod';

const nflDraftYearSchema = z.number().int().min(1936);
const positiveIntegerSchema = z.number().int().positive();
const nonEmptyStringSchema = z.string().trim().min(1);
const optionalSourceUrlSchema = z.string().url().nullable();

export const nflDraftResultProvenanceStatusSchema = z.enum([
  'source_verified',
  'source_verified_player_id_unresolved',
  'needs_verification',
  'fixture_only',
]);

export const nflDraftResultRecordSchema = z
  .object({
    draft_year: nflDraftYearSchema,
    player_id: nonEmptyStringSchema.nullable(),
    player_name: nonEmptyStringSchema,
    position: nonEmptyStringSchema,
    team: nonEmptyStringSchema,
    round: positiveIntegerSchema,
    pick_in_round: positiveIntegerSchema,
    overall_pick: positiveIntegerSchema,
    source: nonEmptyStringSchema,
    source_url: optionalSourceUrlSchema,
    generated_at: z.string().datetime({ offset: true }),
    provenance_status: nflDraftResultProvenanceStatusSchema,
  })
  .strict()
  .superRefine((row, ctx) => {
    if (row.player_id === null && row.provenance_status === 'source_verified') {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['player_id'],
        message:
          'player_id may be null only when provenance_status explicitly marks the row as unresolved, needs_verification, or fixture_only.',
      });
    }

    if (row.player_id !== null && row.provenance_status === 'source_verified_player_id_unresolved') {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['provenance_status'],
        message: 'source_verified_player_id_unresolved is reserved for rows with player_id=null.',
      });
    }
  });

export const nflDraftResultsArtifactSchema = z.array(nflDraftResultRecordSchema).nonempty();

export const NFL_DRAFT_RESULTS_V1_CONTRACT_VERSION = 'tiber-data.nfl-draft-results.v1.0.0';
export const NFL_DRAFT_RESULTS_V1_PROMOTED_EXPORT_PATH_TEMPLATE =
  'exports/promoted/nfl_draft_results/nfl_draft_results_{year}.json';

export function promotedNflDraftResultsPath(year: number): string {
  const parsedYear = nflDraftYearSchema.parse(year);
  return `exports/promoted/nfl_draft_results/nfl_draft_results_${parsedYear}.json`;
}

export function validateNflDraftResultRecord(input: unknown): NflDraftResultRecord {
  return nflDraftResultRecordSchema.parse(input);
}

export function validateNflDraftResultsArtifact(input: unknown): NflDraftResultsArtifact {
  return nflDraftResultsArtifactSchema.parse(input);
}

export type NflDraftResultProvenanceStatus = z.infer<typeof nflDraftResultProvenanceStatusSchema>;
export type NflDraftResultRecord = z.infer<typeof nflDraftResultRecordSchema>;
export type NflDraftResultsArtifact = z.infer<typeof nflDraftResultsArtifactSchema>;
