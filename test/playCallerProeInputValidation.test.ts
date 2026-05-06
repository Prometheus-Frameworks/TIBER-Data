import { describe, expect, it } from 'vitest';

import syntheticRows from './fixtures/play_caller_proe_pbp.synthetic.json' with { type: 'json' };
import {
  PLAY_CALLER_PROE_BUCKET_CLASSIFICATION_FIELDS,
  PLAY_CALLER_PROE_EXPECTED_PASS_FIELDS,
  PLAY_CALLER_PROE_REQUIRED_INPUT_FIELDS,
  validatePlayCallerProeInputRows,
} from '../src/research/playCallerProeInputValidation.js';

describe('play-caller PROE input validation scaffold', () => {
  it('documents required expected-pass and bucket-classification fields', () => {
    expect(PLAY_CALLER_PROE_EXPECTED_PASS_FIELDS).toEqual(['pass', 'xpass', 'pass_oe']);
    expect(PLAY_CALLER_PROE_BUCKET_CLASSIFICATION_FIELDS).toEqual([
      'down',
      'ydstogo',
      'yardline_100',
    ]);
    expect(PLAY_CALLER_PROE_REQUIRED_INPUT_FIELDS).toEqual([
      'season',
      'week',
      'game_id',
      'posteam',
      'down',
      'ydstogo',
      'yardline_100',
      'pass',
      'xpass',
      'pass_oe',
    ]);
  });

  it('flags rows missing expected-pass fields', () => {
    const result = validatePlayCallerProeInputRows(syntheticRows);

    expect(result.issues).toContainEqual({
      rowIndex: 2,
      code: 'missing_expected_pass_fields',
      fields: ['xpass', 'pass_oe'],
    });
  });

  it('flags rows missing down/distance fields', () => {
    const result = validatePlayCallerProeInputRows(syntheticRows);

    expect(result.issues).toContainEqual({
      rowIndex: 3,
      code: 'missing_down_distance_fields',
      fields: ['down', 'ydstogo'],
    });
  });

  it('flags rows missing yardline_100', () => {
    const result = validatePlayCallerProeInputRows(syntheticRows);

    expect(result.issues).toContainEqual({
      rowIndex: 4,
      code: 'missing_yardline_100',
      fields: ['yardline_100'],
    });
  });

  it('classifies red zone rows without fabricating aggregation output', () => {
    const result = validatePlayCallerProeInputRows(syntheticRows);

    expect(result.rows[1]?.buckets).toEqual(['overall', 'red_zone_inside_20', 'red_zone_inside_5']);
  });

  it('classifies outside-red-zone down/distance rows without fabricating aggregation output', () => {
    const result = validatePlayCallerProeInputRows(syntheticRows);

    expect(result.rows[0]?.buckets).toEqual(['overall', 'outside_rz_1st_10']);
  });
});
