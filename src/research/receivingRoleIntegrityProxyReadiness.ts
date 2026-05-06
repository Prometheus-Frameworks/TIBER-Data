export const RECEIVING_ROLE_PROXY_IDENTITY_FIELDS = [
  'season',
  'week',
  'player_id',
  'player_name',
  'team',
  'position',
] as const;

export const RECEIVING_ROLE_PROXY_GAME_IDENTIFIER_CANDIDATE_FIELDS = [
  'game_id',
  'nflverse_game_id',
] as const;

export const RECEIVING_ROLE_PROXY_SNAP_FIELDS = ['offense_snaps', 'snap_share'] as const;

export const RECEIVING_ROLE_PROXY_PARTICIPATION_DENOMINATOR_CANDIDATE_FIELDS = [
  'pass_play_participation',
  'pass_play_participation_proxy',
  'pass_play_participation_count',
  'offense_pass_play_participation',
] as const;

export const RECEIVING_ROLE_PROXY_JOINABLE_USAGE_FIELDS = [
  'targets',
  'receptions',
  'receiving_yards',
] as const;

export const RECEIVING_ROLE_PROXY_BLOCKED_TRUE_ROUTE_FIELDS = [
  'routes_run',
  'route_share',
  'targets_per_route',
  'tprr',
  'yards_per_route_run',
  'yprr',
] as const;

export const RECEIVING_ROLE_PROXY_REQUIRED_BASE_FIELDS = [
  ...RECEIVING_ROLE_PROXY_IDENTITY_FIELDS,
  ...RECEIVING_ROLE_PROXY_SNAP_FIELDS,
] as const;

export type ReceivingRoleProxyIdentityField = (typeof RECEIVING_ROLE_PROXY_IDENTITY_FIELDS)[number];
export type ReceivingRoleProxyGameIdentifierCandidateField =
  (typeof RECEIVING_ROLE_PROXY_GAME_IDENTIFIER_CANDIDATE_FIELDS)[number];
export type ReceivingRoleProxySnapField = (typeof RECEIVING_ROLE_PROXY_SNAP_FIELDS)[number];
export type ReceivingRoleProxyJoinableUsageField =
  (typeof RECEIVING_ROLE_PROXY_JOINABLE_USAGE_FIELDS)[number];
export type ReceivingRoleProxyBlockedTrueRouteField =
  (typeof RECEIVING_ROLE_PROXY_BLOCKED_TRUE_ROUTE_FIELDS)[number];
export type ReceivingRoleProxyParticipationDenominatorCandidateField =
  (typeof RECEIVING_ROLE_PROXY_PARTICIPATION_DENOMINATOR_CANDIDATE_FIELDS)[number];
export type ReceivingRoleProxyRequiredBaseField =
  (typeof RECEIVING_ROLE_PROXY_REQUIRED_BASE_FIELDS)[number];

export type ReceivingRoleProxyValidationIssueCode =
  | 'missing_identity_fields'
  | 'missing_game_identifier_fields'
  | 'missing_snap_fields'
  | 'missing_pass_play_participation_proxy'
  | 'missing_joinable_receiving_usage_fields'
  | 'unsupported_true_route_claim_fields';

export type ReceivingRoleProxyReadinessStatus =
  | 'ready_for_proxy_research'
  | 'blocked_missing_shape'
  | 'blocked_true_route_claim';

export type ReceivingRoleProxyInputRow = Record<string, unknown>;

export type ReceivingRoleProxyValidationIssue = {
  rowIndex: number;
  code: ReceivingRoleProxyValidationIssueCode;
  fields: string[];
};

export type ReceivingRoleProxyValidatedInputRow = {
  rowIndex: number;
  row: ReceivingRoleProxyInputRow;
  gameIdentifierField: ReceivingRoleProxyGameIdentifierCandidateField | null;
  participationDenominatorField: ReceivingRoleProxyParticipationDenominatorCandidateField | null;
  status: ReceivingRoleProxyReadinessStatus;
};

export type ReceivingRoleProxyValidationResult = {
  issues: ReceivingRoleProxyValidationIssue[];
  rows: ReceivingRoleProxyValidatedInputRow[];
};

const hasPresentValue = (row: ReceivingRoleProxyInputRow, field: string): boolean => {
  const value = row[field];
  return value !== null && value !== undefined && value !== '';
};

const missingFields = <Field extends string>(
  row: ReceivingRoleProxyInputRow,
  fields: readonly Field[],
): Field[] => fields.filter((field) => !hasPresentValue(row, field));

const presentFields = <Field extends string>(
  row: ReceivingRoleProxyInputRow,
  fields: readonly Field[],
): Field[] => fields.filter((field) => hasPresentValue(row, field));

const firstPresentField = <Field extends string>(
  row: ReceivingRoleProxyInputRow,
  fields: readonly Field[],
): Field | null => fields.find((field) => hasPresentValue(row, field)) ?? null;

export const validateReceivingRoleProxyInputRows = (
  rows: ReceivingRoleProxyInputRow[],
): ReceivingRoleProxyValidationResult => {
  const issues: ReceivingRoleProxyValidationIssue[] = [];

  const validatedRows = rows.map((row, rowIndex) => {
    const missingIdentityFields = missingFields(row, RECEIVING_ROLE_PROXY_IDENTITY_FIELDS);
    const gameIdentifierField = firstPresentField(
      row,
      RECEIVING_ROLE_PROXY_GAME_IDENTIFIER_CANDIDATE_FIELDS,
    );
    const missingSnapFields = missingFields(row, RECEIVING_ROLE_PROXY_SNAP_FIELDS);
    const missingJoinableUsageFields = missingFields(row, RECEIVING_ROLE_PROXY_JOINABLE_USAGE_FIELDS);
    const blockedTrueRouteFields = presentFields(row, RECEIVING_ROLE_PROXY_BLOCKED_TRUE_ROUTE_FIELDS);
    const participationDenominatorField = firstPresentField(
      row,
      RECEIVING_ROLE_PROXY_PARTICIPATION_DENOMINATOR_CANDIDATE_FIELDS,
    );

    if (missingIdentityFields.length > 0) {
      issues.push({
        rowIndex,
        code: 'missing_identity_fields',
        fields: [...missingIdentityFields],
      });
    }

    if (!gameIdentifierField) {
      issues.push({
        rowIndex,
        code: 'missing_game_identifier_fields',
        fields: [...RECEIVING_ROLE_PROXY_GAME_IDENTIFIER_CANDIDATE_FIELDS],
      });
    }

    if (missingSnapFields.length > 0) {
      issues.push({ rowIndex, code: 'missing_snap_fields', fields: [...missingSnapFields] });
    }

    if (!participationDenominatorField) {
      issues.push({
        rowIndex,
        code: 'missing_pass_play_participation_proxy',
        fields: [...RECEIVING_ROLE_PROXY_PARTICIPATION_DENOMINATOR_CANDIDATE_FIELDS],
      });
    }

    if (missingJoinableUsageFields.length > 0) {
      issues.push({
        rowIndex,
        code: 'missing_joinable_receiving_usage_fields',
        fields: [...missingJoinableUsageFields],
      });
    }

    if (blockedTrueRouteFields.length > 0) {
      issues.push({
        rowIndex,
        code: 'unsupported_true_route_claim_fields',
        fields: [...blockedTrueRouteFields],
      });
    }

    const hasMissingShape =
      missingIdentityFields.length > 0 ||
      !gameIdentifierField ||
      missingSnapFields.length > 0 ||
      missingJoinableUsageFields.length > 0 ||
      !participationDenominatorField;

    const status: ReceivingRoleProxyReadinessStatus =
      blockedTrueRouteFields.length > 0
        ? 'blocked_true_route_claim'
        : hasMissingShape
          ? 'blocked_missing_shape'
          : 'ready_for_proxy_research';

    return {
      rowIndex,
      row,
      gameIdentifierField,
      participationDenominatorField,
      status,
    } satisfies ReceivingRoleProxyValidatedInputRow;
  });

  return { issues, rows: validatedRows };
};
