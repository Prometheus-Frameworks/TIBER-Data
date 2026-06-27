import { z } from 'zod';

const isoDatetimeSchema = z.string().datetime({ offset: true });
const nullableNumberSchema = z.number().nullable();
const nonEmptyStringSchema = z.string().min(1);

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

/**
 * Content checksum / immutable pin for a consumed source.
 *
 * A mutable release-asset URL is not a deterministic source pin (see the
 * #171/#172 governance-blockers audit). A future governed promotion records a
 * checksum and/or an immutable source ref so a rebuild can prove it consumed
 * the same bytes. This schema only lets the contract *represent* that metadata;
 * it does not generate or assert any pin here.
 */
export const teamWeekRawSourceChecksumSchema = z
  .object({
    algorithm: nonEmptyStringSchema, // e.g. "sha256"
    value: nonEmptyStringSchema,
  })
  .strict();

export const teamWeekRawInputSourceSchema = z.object({
  source: nonEmptyStringSchema,
  sourceType: teamWeekRawSourceTypeSchema,
  sourceSnapshotAt: isoDatetimeSchema.nullable().optional(),
  notes: nonEmptyStringSchema.optional(),
  // Optional lineage / source-pin metadata. All optional so existing artifacts
  // remain valid; a future governed promotion populates what it needs.
  sourceRefs: z.array(nonEmptyStringSchema).optional(),
  retrievalMethod: nonEmptyStringSchema.optional(),
  retrievalTimestamp: isoDatetimeSchema.optional(),
  packageVersion: nonEmptyStringSchema.optional(),
  sourceUrlOrDatasetId: nonEmptyStringSchema.optional(),
  transformCodePath: nonEmptyStringSchema.optional(),
  checksum: teamWeekRawSourceChecksumSchema.optional(),
  immutableSourceRef: nonEmptyStringSchema.optional(),
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

/**
 * Governance status/source. `governed` is only ever a true claim when paired
 * with an explicit producer-set marker. The schema refuses to encode a
 * `governed` status without `explicit_marker`, so a governed claim cannot be
 * expressed by path, name, build success, validation, or downstream need.
 */
export const teamWeekRawGovernanceStatusSchema = z.enum(['ungoverned', 'governed']);
export const teamWeekRawGovernanceSourceSchema = z.enum(['not_set', 'explicit_marker']);

export const teamWeekRawGovernanceSchema = z
  .object({
    governanceStatus: teamWeekRawGovernanceStatusSchema,
    governanceSource: teamWeekRawGovernanceSourceSchema,
    notes: nonEmptyStringSchema.optional(),
    // e.g. a promotion-review doc path or PR reference.
    reviewRefs: z.array(nonEmptyStringSchema).optional(),
  })
  .superRefine((governance, ctx) => {
    if (
      governance.governanceStatus === 'governed' &&
      governance.governanceSource !== 'explicit_marker'
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          'governanceStatus "governed" requires governanceSource "explicit_marker"',
        path: ['governanceSource'],
      });
    }
  });

/**
 * Per-field readiness vocabulary.
 *
 * - `available`        — real source values present.
 * - `partial_nulls`    — present, with some legitimately-null rows (e.g. a
 *                        zero-denominator ratio). Not a deferral.
 * - `deferred`         — intentionally not sourced yet for this lane.
 * - `insufficient_data`— no governed source of adequate quality exists.
 * - `unavailable`      — no source available at all.
 *
 * `deferred` / `insufficient_data` / `unavailable` all mean the field's null is
 * *unknown*, never zero. Downstream consumers must surface that, not coerce it.
 */
export const teamWeekRawFieldReadinessStatusSchema = z.enum([
  'available',
  'partial_nulls',
  'deferred',
  'insufficient_data',
  'unavailable',
]);

export const teamWeekRawFieldReadinessSchema = z.record(
  nonEmptyStringSchema,
  teamWeekRawFieldReadinessStatusSchema,
);

export const teamWeekRawMetadataV0Schema = z.object({
  provenanceStatus: teamWeekRawProvenanceStatusSchema,
  provenanceNotes: z.array(nonEmptyStringSchema),
  inputSources: z.array(teamWeekRawInputSourceSchema),
  coverage: teamWeekRawCoverageSchema,
  // --- Additive, backward-compatible metadata (all optional) ---
  // Governance marker (absent => treated as ungoverned; see resolver below).
  governance: teamWeekRawGovernanceSchema.optional(),
  // Field-readiness / deferred metadata.
  deferredFields: z.array(nonEmptyStringSchema).optional(),
  deferredFieldReasons: z.record(nonEmptyStringSchema, nonEmptyStringSchema).optional(),
  fieldReadiness: teamWeekRawFieldReadinessSchema.optional(),
  // Validation / lineage references.
  validationReportPath: nonEmptyStringSchema.optional(),
  lineageManifestPath: nonEmptyStringSchema.optional(),
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
  // pressureRateAllowed is optional/non-blocking for this lane per the
  // #173/#174 disposition decision. When present-and-null (or omitted) it means
  // unknown/unavailable, paired with field-readiness/deferred metadata above —
  // it must never be zero-filled. Real pressure sourcing is additive later.
  pressureRateAllowed: nullableNumberSchema.optional(),
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
  sourceArtifacts: z.array(nonEmptyStringSchema),
  metadata: teamWeekRawMetadataV0Schema,
  rows: z.array(teamWeekRawRowV0Schema),
});

export type TeamWeekRawProvenanceStatus = z.infer<
  typeof teamWeekRawProvenanceStatusSchema
>;
export type TeamWeekRawSourceType = z.infer<typeof teamWeekRawSourceTypeSchema>;
export type TeamWeekRawInputSource = z.infer<typeof teamWeekRawInputSourceSchema>;
export type TeamWeekRawSourceChecksum = z.infer<typeof teamWeekRawSourceChecksumSchema>;
export type TeamWeekRawCoverageV0 = z.infer<typeof teamWeekRawCoverageSchema>;
export type TeamWeekRawGovernanceStatus = z.infer<
  typeof teamWeekRawGovernanceStatusSchema
>;
export type TeamWeekRawGovernanceSource = z.infer<
  typeof teamWeekRawGovernanceSourceSchema
>;
export type TeamWeekRawGovernance = z.infer<typeof teamWeekRawGovernanceSchema>;
export type TeamWeekRawFieldReadinessStatus = z.infer<
  typeof teamWeekRawFieldReadinessStatusSchema
>;
export type TeamWeekRawFieldReadiness = z.infer<typeof teamWeekRawFieldReadinessSchema>;
export type TeamWeekRawMetadataV0 = z.infer<typeof teamWeekRawMetadataV0Schema>;
export type TeamWeekRawRowV0 = z.infer<typeof teamWeekRawRowV0Schema>;
export type TeamWeekRawArtifactV0 = z.infer<typeof teamWeekRawArtifactV0Schema>;

/** Field-readiness statuses that mean "value is unknown, never zero". */
export const TEAM_WEEK_RAW_DEFERRED_READINESS_STATUSES: ReadonlySet<TeamWeekRawFieldReadinessStatus> =
  new Set(['deferred', 'insufficient_data', 'unavailable']);

/**
 * Shape-only parse (Zod). Validates the envelope structure/types but does NOT
 * enforce cross-field contract rules (deferred-field laundering,
 * governance/provenance agreement). Use {@link validateTeamWeekRawArtifactV0}
 * as the contract gate; use this only when you explicitly want shape-only
 * parsing. `teamWeekRawArtifactV0Schema` is the same shape-only check.
 */
export function parseTeamWeekRawArtifactV0Shape(input: unknown): TeamWeekRawArtifactV0 {
  return teamWeekRawArtifactV0Schema.parse(input);
}

/**
 * Full contract gate: shape parse PLUS the cross-field rules in
 * {@link findTeamWeekRawContractViolations} (no zero-filled deferred fields, and
 * governance marker must agree with `provenanceStatus`). Throws on either a
 * shape error or a contract violation.
 */
export function validateTeamWeekRawArtifactV0(input: unknown): TeamWeekRawArtifactV0 {
  const artifact = teamWeekRawArtifactV0Schema.parse(input);
  const violations = findTeamWeekRawContractViolations(artifact);
  if (violations.length > 0) {
    throw new Error(`team_week_raw_v0 contract violations: ${violations.join('; ')}`);
  }
  return artifact;
}

export function isTeamWeekRawArtifactV0(
  input: unknown,
): input is TeamWeekRawArtifactV0 {
  const parsed = teamWeekRawArtifactV0Schema.safeParse(input);
  if (!parsed.success) {
    return false;
  }
  return findTeamWeekRawContractViolations(parsed.data).length === 0;
}

/**
 * Resolve governance fail-closed. Absent, malformed, or unrecognized governance
 * resolves to ungoverned/not_set. `isGoverned` is true only when an explicit
 * `governed` + `explicit_marker` marker AND the canonical
 * `provenanceStatus: governed_real_data` label agree — never inferred from a
 * marker alone, and never from path, name, build, validation, or downstream
 * need. If the marker claims governed but provenance disagrees, this resolves
 * fail-closed to ungoverned (the inconsistency is also rejected by
 * `validateTeamWeekRawArtifactV0`).
 */
export function resolveTeamWeekRawGovernance(
  metadata: { governance?: unknown; provenanceStatus?: unknown } | null | undefined,
): {
  governanceStatus: TeamWeekRawGovernanceStatus;
  governanceSource: TeamWeekRawGovernanceSource;
  isGoverned: boolean;
} {
  const failClosed = {
    governanceStatus: 'ungoverned' as const,
    governanceSource: 'not_set' as const,
    isGoverned: false,
  };
  if (!metadata || typeof metadata !== 'object') {
    return failClosed;
  }
  const parsed = teamWeekRawGovernanceSchema.safeParse(metadata.governance);
  if (!parsed.success) {
    return failClosed;
  }
  const governance = parsed.data;
  const markerGoverned =
    governance.governanceStatus === 'governed' &&
    governance.governanceSource === 'explicit_marker';
  // The governed marker and the canonical provenance label must agree.
  const provenanceGoverned = metadata.provenanceStatus === 'governed_real_data';
  const isGoverned = markerGoverned && provenanceGoverned;
  return {
    governanceStatus: isGoverned ? 'governed' : 'ungoverned',
    governanceSource: governance.governanceSource,
    isGoverned,
  };
}

export function isTeamWeekRawArtifactGoverned(
  artifact: Pick<TeamWeekRawArtifactV0, 'metadata'>,
): boolean {
  return resolveTeamWeekRawGovernance(artifact.metadata).isGoverned;
}

/** Read a field's readiness status, or `undefined` if none is recorded. */
export function getTeamWeekRawFieldReadiness(
  metadata: Pick<TeamWeekRawMetadataV0, 'fieldReadiness'>,
  field: string,
): TeamWeekRawFieldReadinessStatus | undefined {
  return metadata.fieldReadiness?.[field];
}

/**
 * A field is deferred (its null means "unknown, not zero") when it is listed in
 * `deferredFields` or its `fieldReadiness` status is one of the deferred
 * statuses.
 */
export function isTeamWeekRawFieldDeferred(
  metadata: Pick<TeamWeekRawMetadataV0, 'deferredFields' | 'fieldReadiness'>,
  field: string,
): boolean {
  if (metadata.deferredFields?.includes(field)) {
    return true;
  }
  const readiness = metadata.fieldReadiness?.[field];
  return (
    readiness !== undefined && TEAM_WEEK_RAW_DEFERRED_READINESS_STATUSES.has(readiness)
  );
}

/** Convenience: is `pressureRateAllowed` deferred for this lane? */
export function isPressureRateAllowedDeferred(
  metadata: Pick<TeamWeekRawMetadataV0, 'deferredFields' | 'fieldReadiness'>,
): boolean {
  return isTeamWeekRawFieldDeferred(metadata, 'pressureRateAllowed');
}

/**
 * Detect deferred-field contradictions: a field marked deferred/unavailable
 * (its null means "unknown") that nonetheless carries a numeric value on some
 * row. This is the machine check against null-to-zero laundering / backfill of
 * a deferred field — a deferred field must stay null, never `0` or any number.
 * Returns one entry per offending (field, row).
 */
export function findTeamWeekRawDeferredFieldViolations(
  artifact: Pick<TeamWeekRawArtifactV0, 'metadata' | 'rows'>,
): Array<{ field: string; rowIndex: number; value: number }> {
  const deferred = new Set<string>(artifact.metadata.deferredFields ?? []);
  if (artifact.metadata.fieldReadiness) {
    for (const [field, status] of Object.entries(artifact.metadata.fieldReadiness)) {
      if (TEAM_WEEK_RAW_DEFERRED_READINESS_STATUSES.has(status)) {
        deferred.add(field);
      }
    }
  }
  const violations: Array<{ field: string; rowIndex: number; value: number }> = [];
  artifact.rows.forEach((row, rowIndex) => {
    for (const field of deferred) {
      const value = (row as Record<string, unknown>)[field];
      if (typeof value === 'number') {
        violations.push({ field, rowIndex, value });
      }
    }
  });
  return violations;
}

/**
 * Cross-field contract rules that the Zod shape schema cannot express. Returns
 * a human-readable issue per violation (empty array means contract-valid):
 *
 * 1. No deferred field carries a numeric value on any row (anti-laundering).
 * 2. If the governance marker claims governed (`governed` + `explicit_marker`),
 *    `provenanceStatus` must agree (`governed_real_data`). A governed marker
 *    paired with a non-governed provenance label is a contradiction.
 */
export function findTeamWeekRawContractViolations(
  artifact: Pick<TeamWeekRawArtifactV0, 'metadata' | 'rows'>,
): string[] {
  const issues: string[] = [];
  for (const violation of findTeamWeekRawDeferredFieldViolations(artifact)) {
    issues.push(
      `deferred field "${violation.field}" has numeric value ${violation.value} at row ${violation.rowIndex} (deferred fields must be null, never zero-filled)`,
    );
  }
  const governance = teamWeekRawGovernanceSchema.safeParse(artifact.metadata.governance);
  if (
    governance.success &&
    governance.data.governanceStatus === 'governed' &&
    governance.data.governanceSource === 'explicit_marker' &&
    artifact.metadata.provenanceStatus !== 'governed_real_data'
  ) {
    issues.push(
      `governance marker is governed/explicit_marker but provenanceStatus is "${artifact.metadata.provenanceStatus}" (a governed marker requires provenanceStatus "governed_real_data")`,
    );
  }
  return issues;
}
