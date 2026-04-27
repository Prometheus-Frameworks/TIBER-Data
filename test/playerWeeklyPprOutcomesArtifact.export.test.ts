import { mkdtempSync, readFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH,
  buildPlayerWeeklyPprOutcomesV1FromRawSources,
  calculatePprPoints,
  toDeterministicPlayerWeeklyPprOutcomesV1Json,
  writePlayerWeeklyPprOutcomesV1Artifact,
} from '../src/index.js';

describe('player weekly ppr outcomes v1 artifact export', () => {
  it('calculates ppr points with explicit null-to-zero handling', () => {
    expect(
      calculatePprPoints({
        receptions: 8,
        receiving_yards: 95,
        receiving_tds: 1,
        rushing_yards: null,
        rushing_tds: null,
        passing_yards: null,
        passing_tds: null,
        interceptions: null,
      }),
    ).toBe(23.5);
  });

  it('builds rolling 3-week and 5-week totals deterministically', () => {
    const artifact = buildPlayerWeeklyPprOutcomesV1FromRawSources();
    const hurtsRows = artifact.filter((row) => row.player_id === '00-0034796').sort((a, b) => a.week - b.week);

    expect(hurtsRows.map((row) => row.ppr_points)).toEqual([25.72, 28.18, 19.64]);
    expect(hurtsRows.map((row) => row.rolling_3_week_ppr)).toEqual([25.72, 53.9, 73.54]);
    expect(hurtsRows.map((row) => row.rolling_5_week_ppr)).toEqual([25.72, 53.9, 73.54]);
    expect(hurtsRows.map((row) => row.season_ppr)).toEqual([25.72, 53.9, 73.54]);
    expect(hurtsRows.map((row) => row.games_played)).toEqual([1, 2, 3]);
  });

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicPlayerWeeklyPprOutcomesV1Json();
    const second = toDeterministicPlayerWeeklyPprOutcomesV1Json();
    const committed = readFileSync(path.resolve(PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-ppr-outcomes-v1-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writePlayerWeeklyPprOutcomesV1Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicPlayerWeeklyPprOutcomesV1Json());
  });

  it('fails closed for unsupported mode', () => {
    expect(() => buildPlayerWeeklyPprOutcomesV1FromRawSources({ mode: 'live_weekly_refresh' })).toThrow();
  });
});
