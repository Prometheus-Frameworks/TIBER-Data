import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH,
  PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_BACKED_SOURCE_PATH,
  PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_PATH,
  buildPlayerWeeklyPprOutcomesV1FromRawSources,
  calculatePprPoints,
  toDeterministicPlayerWeeklyPprOutcomesV1Json,
  writePlayerWeeklyPprOutcomesV1Artifact,
} from '../src/index.js';


const normalizeLineEndings = (value: string): string => value.replace(/\r\n/g, '\n');

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



  it('defaults to fixture source and keeps existing scaffold behavior', () => {
    const defaultRows = buildPlayerWeeklyPprOutcomesV1FromRawSources();
    const explicitFixtureRows = buildPlayerWeeklyPprOutcomesV1FromRawSources({ sourceKind: 'offline_fixture' });

    expect(defaultRows).toEqual(explicitFixtureRows);
  });

  it('supports source_backed lane when source artifact exists and fails closed otherwise', () => {
    if (!existsSync(path.resolve(PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_BACKED_SOURCE_PATH))) {
      expect(() => buildPlayerWeeklyPprOutcomesV1FromRawSources({ sourceKind: 'source_backed' })).toThrow(
        PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_BACKED_SOURCE_PATH,
      );
      return;
    }

    const sourceBackedRows = buildPlayerWeeklyPprOutcomesV1FromRawSources({ sourceKind: 'source_backed' });
    expect(sourceBackedRows.length).toBeGreaterThan(0);
    expect(sourceBackedRows.every((row) => row.source.includes('nflreadpy.load_player_stats'))).toBe(true);
    expect(sourceBackedRows.every((row) => row.generated_at.length > 0)).toBe(true);
    expect(sourceBackedRows.every((row) => ['QB', 'RB', 'WR', 'TE'].includes(row.position))).toBe(true);

    const first = toDeterministicPlayerWeeklyPprOutcomesV1Json({ sourceKind: 'source_backed' });
    const second = toDeterministicPlayerWeeklyPprOutcomesV1Json({ sourceKind: 'source_backed' });
    const committed = readFileSync(path.resolve(PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_BACKED_SOURCE_PATH), 'utf-8');
    expect(first).toEqual(second);
    expect(normalizeLineEndings(first)).toEqual(normalizeLineEndings(committed));
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

  it('fails closed when provenance is missing from raw payload wrapper', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-ppr-outcomes-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_PATH), 'utf-8'));
    delete source.provenance;

    const invalidPath = path.join(tempRoot, 'missing-provenance.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyPprOutcomesV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('fails closed when source_path is missing from raw payload wrapper', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-ppr-outcomes-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_PATH), 'utf-8'));
    delete source.source_path;

    const invalidPath = path.join(tempRoot, 'missing-source-path.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyPprOutcomesV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('fails closed when duplicate player-week rows are present', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-ppr-outcomes-duplicates-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_PPR_OUTCOMES_V1_SOURCE_PATH), 'utf-8'));
    source.records.push({ ...source.records[0] });

    const invalidPath = path.join(tempRoot, 'duplicate-player-week.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyPprOutcomesV1FromRawSources({ sourcePath: invalidPath })).toThrow(
      'Duplicate player-week row detected',
    );
  });
});
