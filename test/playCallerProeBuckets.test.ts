import { describe, expect, it } from 'vitest';

import { classifyPlayCallerProeBuckets } from '../src/research/playCallerProeBuckets.js';

describe('play-caller PROE bucket classifier', () => {
  it('always includes overall', () => {
    expect(classifyPlayCallerProeBuckets({ yardline_100: 50 })).toContain('overall');
  });

  it('classifies 1st and 10 outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 1, ydstogo: 10, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_1st_10',
    ]);
  });

  it('classifies 2nd and 8+ outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 2, ydstogo: 8, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_2nd_8_plus',
    ]);
  });

  it('classifies 2nd and 3-7 outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 2, ydstogo: 5, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_2nd_3_to_7',
    ]);
  });

  it('classifies 2nd and 1-2 outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 2, ydstogo: 2, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_2nd_1_to_2',
    ]);
  });

  it('classifies 3rd and 5+ outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 3, ydstogo: 5, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_3rd_5_plus',
    ]);
  });

  it('classifies 3rd and 3-4 outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 3, ydstogo: 4, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_3rd_3_to_4',
    ]);
  });

  it('classifies 3rd and 1-2 outside red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 3, ydstogo: 1, yardline_100: 60 })).toEqual([
      'overall',
      'outside_rz_3rd_1_to_2',
    ]);
  });

  it('classifies inside 20 red zone', () => {
    expect(classifyPlayCallerProeBuckets({ down: 1, ydstogo: 10, yardline_100: 20 })).toEqual([
      'overall',
      'red_zone_inside_20',
    ]);
  });

  it('classifies inside 5 red zone with both red zone buckets', () => {
    expect(classifyPlayCallerProeBuckets({ down: 1, ydstogo: 10, yardline_100: 5 })).toEqual([
      'overall',
      'red_zone_inside_20',
      'red_zone_inside_5',
    ]);
  });

  it('does not add outside_rz bucket for a red zone row', () => {
    expect(classifyPlayCallerProeBuckets({ down: 1, ydstogo: 10, yardline_100: 10 })).not.toContain(
      'outside_rz_1st_10',
    );
  });

  it('returns only overall when yardline is missing', () => {
    expect(classifyPlayCallerProeBuckets({ down: 1, ydstogo: 10 })).toEqual(['overall']);
    expect(
      classifyPlayCallerProeBuckets({ down: 1, ydstogo: 10, yardline_100: 'not numeric' }),
    ).toEqual(['overall']);
  });

  it('can classify red zone buckets when down and ydstogo are missing', () => {
    expect(classifyPlayCallerProeBuckets({ yardline_100: 4 })).toEqual([
      'overall',
      'red_zone_inside_20',
      'red_zone_inside_5',
    ]);
  });
});
