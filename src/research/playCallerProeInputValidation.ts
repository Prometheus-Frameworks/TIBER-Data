import {
  classifyPlayCallerProeBuckets,
  type PlayCallerProeBucket,
} from './playCallerProeBuckets.js';

export const PLAY_CALLER_PROE_IDENTITY_FIELDS = ['season', 'week', 'game_id', 'posteam'] as const;
export const PLAY_CALLER_PROE_BUCKET_CLASSIFICATION_FIELDS = [
  'down',
  'ydstogo',
  'yardline_100',
] as const;
export const PLAY_CALLER_PROE_EXPECTED_PASS_FIELDS = ['pass', 'xpass', 'pass_oe'] as const;
export const PLAY_CALLER_PROE_REQUIRED_INPUT_FIELDS = [
  ...PLAY_CALLER_PROE_IDENTITY_FIELDS,
  ...PLAY_CALLER_PROE_BUCKET_CLASSIFICATION_FIELDS,
  ...PLAY_CALLER_PROE_EXPECTED_PASS_FIELDS,
] as const;

export type PlayCallerProeRequiredInputField =
  (typeof PLAY_CALLER_PROE_REQUIRED_INPUT_FIELDS)[number];

export type PlayCallerProeValidationIssueCode =
  | 'missing_identity_fields'
  | 'missing_down_distance_fields'
  | 'missing_yardline_100'
  | 'missing_expected_pass_fields';

export type PlayCallerProeInputRow = Record<string, unknown>;

export type PlayCallerProeValidationIssue = {
  rowIndex: number;
  code: PlayCallerProeValidationIssueCode;
  fields: PlayCallerProeRequiredInputField[];
};

export type PlayCallerProeValidatedInputRow = {
  rowIndex: number;
  buckets: PlayCallerProeBucket[];
  row: PlayCallerProeInputRow;
};

export type PlayCallerProeValidationResult = {
  issues: PlayCallerProeValidationIssue[];
  rows: PlayCallerProeValidatedInputRow[];
};

const hasPresentValue = (
  row: PlayCallerProeInputRow,
  field: PlayCallerProeRequiredInputField,
): boolean => {
  const value = row[field];
  return value !== null && value !== undefined && value !== '';
};

const missingFields = <Field extends PlayCallerProeRequiredInputField>(
  row: PlayCallerProeInputRow,
  fields: readonly Field[],
): Field[] => fields.filter((field) => !hasPresentValue(row, field));

export const validatePlayCallerProeInputRows = (
  rows: PlayCallerProeInputRow[],
): PlayCallerProeValidationResult => {
  const issues: PlayCallerProeValidationIssue[] = [];

  const validatedRows = rows.map((row, rowIndex) => {
    const missingIdentityFields = missingFields(row, PLAY_CALLER_PROE_IDENTITY_FIELDS);
    const missingDownDistanceFields = missingFields(row, ['down', 'ydstogo'] as const);
    const missingYardline100 = missingFields(row, ['yardline_100'] as const);
    const missingExpectedPassFields = missingFields(row, PLAY_CALLER_PROE_EXPECTED_PASS_FIELDS);

    if (missingIdentityFields.length > 0) {
      issues.push({ rowIndex, code: 'missing_identity_fields', fields: [...missingIdentityFields] });
    }

    if (missingDownDistanceFields.length > 0) {
      issues.push({
        rowIndex,
        code: 'missing_down_distance_fields',
        fields: [...missingDownDistanceFields],
      });
    }

    if (missingYardline100.length > 0) {
      issues.push({ rowIndex, code: 'missing_yardline_100', fields: [...missingYardline100] });
    }

    if (missingExpectedPassFields.length > 0) {
      issues.push({
        rowIndex,
        code: 'missing_expected_pass_fields',
        fields: [...missingExpectedPassFields],
      });
    }

    return {
      rowIndex,
      buckets: classifyPlayCallerProeBuckets(row),
      row,
    } satisfies PlayCallerProeValidatedInputRow;
  });

  return { issues, rows: validatedRows };
};
