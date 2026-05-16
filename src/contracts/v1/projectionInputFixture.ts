import { z } from 'zod';

const nonEmptyStringSchema = z.string().trim().min(1);
const seasonSchema = z.number().int().min(1900);
const weekSchema = z.number().int().min(1).max(22);
const finiteNumberSchema = z.number().finite();
const nonNegativeFiniteNumberSchema = finiteNumberSchema.min(0);
const positiveFiniteNumberSchema = finiteNumberSchema.positive();
const teamCodeSchema = z.string().regex(/^[A-Z]{2,4}$/);
const playerPositionSchema = z.enum(['QB', 'RB', 'WR', 'TE']);

export const projectionInputFixtureContractVersionSchema = z.literal(
  'tiber-data.projection-input-fixture.v1.0.0',
);

export const projectionInputFixtureScopeSchema = z
  .object({
    kind: z.literal('bounded_rehearsal_fixture'),
    production_coverage_claim: z.literal(false),
    projection_label: nonEmptyStringSchema,
    evidence_window: nonEmptyStringSchema,
    notes: z.array(nonEmptyStringSchema).nonempty(),
  })
  .strict();

export const projectionInputFixtureSourceDatasetRefSchema = z
  .object({
    name: nonEmptyStringSchema,
    path: nonEmptyStringSchema,
    version: nonEmptyStringSchema.optional(),
    provenance: nonEmptyStringSchema.optional(),
    source_path: nonEmptyStringSchema.optional(),
    usage: nonEmptyStringSchema,
  })
  .strict();

export const projectionInputFixtureIdentityRefSchema = z
  .object({
    source_paths: z.array(nonEmptyStringSchema).nonempty(),
    identity_fields: z
      .array(z.enum(['player_id', 'player_name', 'team', 'position', 'season', 'week']))
      .nonempty(),
    projection_label_policy: nonEmptyStringSchema,
  })
  .strict();

export const projectionInputFixtureProjectionContextSchema = z
  .object({
    season: seasonSchema,
    week: weekSchema,
    league: z.literal('NFL'),
    scoring_format: z.literal('PPR'),
    fixture_only: z.literal(true),
    production_ingestion: z.literal(false),
    source_evidence_season: seasonSchema,
    source_evidence_week: weekSchema,
  })
  .strict();

const lineupNumberRecordSchema = (keys: [string, ...string[]]) =>
  z.object(
    Object.fromEntries(keys.map((key) => [key, nonNegativeFiniteNumberSchema])) as Record<
      (typeof keys)[number],
      typeof nonNegativeFiniteNumberSchema
    >,
  );

export const projectionInputFixtureLeagueContextSchema = z
  .object({
    teams: positiveFiniteNumberSchema,
    starters: lineupNumberRecordSchema(['QB', 'RB', 'WR', 'TE'])
      .extend({ FLEX: nonNegativeFiniteNumberSchema.optional() })
      .strict(),
    flex_allocation: lineupNumberRecordSchema(['RB', 'WR', 'TE']).strict().optional(),
    replacement_buffer: lineupNumberRecordSchema(['QB', 'RB', 'WR', 'TE']).strict().optional(),
  })
  .strict();

export const projectionInputFixturePlayerOpportunitySchema = z
  .object({
    player_id: nonEmptyStringSchema,
    player_name: nonEmptyStringSchema,
    team: teamCodeSchema,
    position: playerPositionSchema,
    season: seasonSchema,
    week: weekSchema,
    routes_pg: nonNegativeFiniteNumberSchema.optional(),
    route_participation: nonNegativeFiniteNumberSchema.optional(),
    targets_per_route: nonNegativeFiniteNumberSchema.optional(),
    targets_pg: nonNegativeFiniteNumberSchema.optional(),
    carries_pg: nonNegativeFiniteNumberSchema.optional(),
    pass_attempts_pg: nonNegativeFiniteNumberSchema.optional(),
    yards_per_target: nonNegativeFiniteNumberSchema.optional(),
    yards_per_carry: nonNegativeFiniteNumberSchema.optional(),
    yards_per_reception: nonNegativeFiniteNumberSchema.optional(),
    catch_rate: nonNegativeFiniteNumberSchema.max(1).optional(),
    pass_yards_per_attempt: nonNegativeFiniteNumberSchema.optional(),
    red_zone_carries_pg: nonNegativeFiniteNumberSchema.optional(),
    red_zone_targets_pg: nonNegativeFiniteNumberSchema.optional(),
    games_sampled: positiveFiniteNumberSchema.optional(),
    team_pass_rate_environment: nonNegativeFiniteNumberSchema.optional(),
    team_pace: nonNegativeFiniteNumberSchema.optional(),
    offensive_environment: nonNegativeFiniteNumberSchema.optional(),
  })
  .strict();

export const projectionInputFixtureMissingFieldSeveritySchema = z.literal('warning');

export const projectionInputFixtureMissingFieldSchema = z
  .object({
    field: nonEmptyStringSchema,
    severity: projectionInputFixtureMissingFieldSeveritySchema,
    reason: nonEmptyStringSchema,
    player_id: nonEmptyStringSchema.optional(),
    impact: nonEmptyStringSchema.optional(),
  })
  .strict();

export const projectionInputFixtureBundleSchema = z
  .object({
    input_contract_version: projectionInputFixtureContractVersionSchema,
    tiber_data_schema_version: nonEmptyStringSchema,
    fixture_scope: projectionInputFixtureScopeSchema,
    source_dataset_refs: z.array(projectionInputFixtureSourceDatasetRefSchema).nonempty(),
    identity_ref: projectionInputFixtureIdentityRefSchema,
    projection_context: projectionInputFixtureProjectionContextSchema,
    league_context: projectionInputFixtureLeagueContextSchema,
    player_opportunities: z.array(projectionInputFixturePlayerOpportunitySchema).nonempty(),
    missing_fields: z.array(projectionInputFixtureMissingFieldSchema),
    adapter_warnings: z.array(nonEmptyStringSchema),
  })
  .strict();

export function validateProjectionInputFixtureBundle(
  input: unknown,
): ProjectionInputFixtureBundle {
  return projectionInputFixtureBundleSchema.parse(input);
}

export function isProjectionInputFixtureBundle(
  input: unknown,
): input is ProjectionInputFixtureBundle {
  return projectionInputFixtureBundleSchema.safeParse(input).success;
}

export type ProjectionInputFixtureContractVersion = z.infer<
  typeof projectionInputFixtureContractVersionSchema
>;
export type ProjectionInputFixtureScope = z.infer<typeof projectionInputFixtureScopeSchema>;
export type ProjectionInputFixtureSourceDatasetRef = z.infer<
  typeof projectionInputFixtureSourceDatasetRefSchema
>;
export type ProjectionInputFixtureIdentityRef = z.infer<
  typeof projectionInputFixtureIdentityRefSchema
>;
export type ProjectionInputFixtureProjectionContext = z.infer<
  typeof projectionInputFixtureProjectionContextSchema
>;
export type ProjectionInputFixtureLeagueContext = z.infer<
  typeof projectionInputFixtureLeagueContextSchema
>;
export type ProjectionInputFixturePlayerOpportunity = z.infer<
  typeof projectionInputFixturePlayerOpportunitySchema
>;
export type ProjectionInputFixtureMissingFieldSeverity = z.infer<
  typeof projectionInputFixtureMissingFieldSeveritySchema
>;
export type ProjectionInputFixtureMissingField = z.infer<
  typeof projectionInputFixtureMissingFieldSchema
>;
export type ProjectionInputFixtureBundle = z.infer<typeof projectionInputFixtureBundleSchema>;
