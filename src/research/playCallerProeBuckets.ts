export const PLAY_CALLER_PROE_BUCKETS = [
  'overall',
  'outside_rz_1st_10',
  'outside_rz_2nd_8_plus',
  'outside_rz_2nd_3_to_7',
  'outside_rz_2nd_1_to_2',
  'outside_rz_3rd_5_plus',
  'outside_rz_3rd_3_to_4',
  'outside_rz_3rd_1_to_2',
  'red_zone_inside_20',
  'red_zone_inside_5',
] as const;

export type PlayCallerProeBucket = (typeof PLAY_CALLER_PROE_BUCKETS)[number];

export type PlayCallerProeBucketInput = {
  down?: unknown;
  ydstogo?: unknown;
  yardline_100?: unknown;
};

const toFiniteNumber = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const normalizedValue = typeof value === 'string' ? value.trim() : value;

  if (normalizedValue === '') {
    return null;
  }

  const numericValue = Number(normalizedValue);
  return Number.isFinite(numericValue) ? numericValue : null;
};

export const classifyPlayCallerProeBuckets = (
  row: PlayCallerProeBucketInput,
): PlayCallerProeBucket[] => {
  const buckets: PlayCallerProeBucket[] = ['overall'];
  const yardline100 = toFiniteNumber(row.yardline_100);

  if (yardline100 === null) {
    return buckets;
  }

  if (yardline100 <= 20) {
    buckets.push('red_zone_inside_20');

    if (yardline100 <= 5) {
      buckets.push('red_zone_inside_5');
    }

    return buckets;
  }

  const down = toFiniteNumber(row.down);
  const ydstogo = toFiniteNumber(row.ydstogo);

  if (down === null || ydstogo === null) {
    return buckets;
  }

  if (down === 1 && ydstogo === 10) {
    buckets.push('outside_rz_1st_10');
  }

  if (down === 2 && ydstogo >= 8) {
    buckets.push('outside_rz_2nd_8_plus');
  }

  if (down === 2 && ydstogo >= 3 && ydstogo <= 7) {
    buckets.push('outside_rz_2nd_3_to_7');
  }

  if (down === 2 && ydstogo >= 1 && ydstogo <= 2) {
    buckets.push('outside_rz_2nd_1_to_2');
  }

  if (down === 3 && ydstogo >= 5) {
    buckets.push('outside_rz_3rd_5_plus');
  }

  if (down === 3 && ydstogo >= 3 && ydstogo <= 4) {
    buckets.push('outside_rz_3rd_3_to_4');
  }

  if (down === 3 && ydstogo >= 1 && ydstogo <= 2) {
    buckets.push('outside_rz_3rd_1_to_2');
  }

  return buckets;
};
