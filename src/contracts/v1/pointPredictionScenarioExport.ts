import { z } from 'zod';

const nonEmptyStringSchema = z.string().trim().min(1);
const seasonSchema = z.number().int().min(1900);
const weekSchema = z.number().int().min(1).max(22);
const finiteNumberSchema = z.number().finite();
const shareMetricSchema = finiteNumberSchema.min(0).max(1);
const teamCodeSchema = z.string().regex(/^[A-Z]{2,4}$/);
const playerPositionSchema = z.enum(['QB', 'RB', 'WR', 'TE']);
const isoDatetimeSchema = z.string().datetime({ offset: true });

export const POINT_PREDICTION_SCENARIO_EXPORT_CONTRACT_VERSION =
  'tiber-data.point-prediction-scenario-export.v1.0.0';

export const POINT_PREDICTION_SCENARIO_EXPORT_PROMOTED_FIXTURE_PATH =
  'exports/promoted/point_prediction_model/point_prediction_scenario_export_v1.fixture.json';

export const pointPredictionScenarioExportContractVersionSchema = z.literal(
  POINT_PREDICTION_SCENARIO_EXPORT_CONTRACT_VERSION,
);

export const pointPredictionScenarioTypeSchema = z.enum([
  'injury_absence',
  'injury_return',
  'role_change',
  'depth_chart_change',
  'team_environment_change',
  'weather',
  'custom',
]);

export const pointPredictionScenarioEventTypeSchema = z.enum([
  'player_out',
  'player_limited',
  'player_returning',
  'starter_change',
  'target_share_shift',
  'rush_share_shift',
  'pace_shift',
  'pass_rate_shift',
  'weather_adjustment',
  'manual_scenario',
]);

export const pointPredictionScenarioConfidenceTierSchema = z.enum(['low', 'medium', 'high']);

export const pointPredictionScenarioArtifactStatusSchema = z.enum([
  'fixture_only',
  'promoted_source_backed',
]);

export const pointPredictionScenarioProvenanceSchema = z
  .object({
    source_repo: z.literal('Point-prediction-model'),
    source_artifact: nonEmptyStringSchema,
    source_run_id: nonEmptyStringSchema.optional(),
    source_commit: nonEmptyStringSchema.optional(),
    tiber_data_contract_owner: z.literal('TIBER-Data'),
    emitted_by: nonEmptyStringSchema,
    validated_by: nonEmptyStringSchema,
    notes: z.array(nonEmptyStringSchema),
  })
  .strict();

export const pointPredictionScenarioPlayerIdentitySchema = z
  .object({
    player_id: nonEmptyStringSchema,
    player_name: nonEmptyStringSchema,
    source_player_id: nonEmptyStringSchema.optional(),
  })
  .strict();

export const pointPredictionScenarioRowSchema = z
  .object({
    player: pointPredictionScenarioPlayerIdentitySchema,
    team: teamCodeSchema,
    position: playerPositionSchema,
    baseline_projection: finiteNumberSchema,
    adjusted_projection: finiteNumberSchema,
    delta: finiteNumberSchema,
    confidence_score: shareMetricSchema,
    confidence_tier: pointPredictionScenarioConfidenceTierSchema,
    confidence_notes: z.array(nonEmptyStringSchema),
    explanation: nonEmptyStringSchema,
    notes: z.array(nonEmptyStringSchema),
  })
  .strict()
  .superRefine((row, ctx) => {
    const expectedDelta = Number((row.adjusted_projection - row.baseline_projection).toFixed(4));
    const actualDelta = Number(row.delta.toFixed(4));

    if (actualDelta !== expectedDelta) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['delta'],
        message: 'delta must equal adjusted_projection - baseline_projection when rounded to 4 decimals.',
      });
    }
  });

export const pointPredictionScenarioExportSchema = z
  .object({
    contract_version: pointPredictionScenarioExportContractVersionSchema,
    artifact_status: pointPredictionScenarioArtifactStatusSchema,
    scenario_id: nonEmptyStringSchema,
    scenario_name: nonEmptyStringSchema,
    scenario_type: pointPredictionScenarioTypeSchema,
    event_type: pointPredictionScenarioEventTypeSchema,
    season: seasonSchema,
    week: weekSchema,
    model_version: nonEmptyStringSchema,
    generated_at: isoDatetimeSchema,
    provenance: pointPredictionScenarioProvenanceSchema,
    rows: z.array(pointPredictionScenarioRowSchema).nonempty(),
  })
  .strict();

export function validatePointPredictionScenarioExport(
  input: unknown,
): PointPredictionScenarioExport {
  return pointPredictionScenarioExportSchema.parse(input);
}

export function isPointPredictionScenarioExport(
  input: unknown,
): input is PointPredictionScenarioExport {
  return pointPredictionScenarioExportSchema.safeParse(input).success;
}

export type PointPredictionScenarioType = z.infer<typeof pointPredictionScenarioTypeSchema>;
export type PointPredictionScenarioEventType = z.infer<typeof pointPredictionScenarioEventTypeSchema>;
export type PointPredictionScenarioConfidenceTier = z.infer<
  typeof pointPredictionScenarioConfidenceTierSchema
>;
export type PointPredictionScenarioArtifactStatus = z.infer<
  typeof pointPredictionScenarioArtifactStatusSchema
>;
export type PointPredictionScenarioProvenance = z.infer<
  typeof pointPredictionScenarioProvenanceSchema
>;
export type PointPredictionScenarioPlayerIdentity = z.infer<
  typeof pointPredictionScenarioPlayerIdentitySchema
>;
export type PointPredictionScenarioRow = z.infer<typeof pointPredictionScenarioRowSchema>;
export type PointPredictionScenarioExport = z.infer<typeof pointPredictionScenarioExportSchema>;
