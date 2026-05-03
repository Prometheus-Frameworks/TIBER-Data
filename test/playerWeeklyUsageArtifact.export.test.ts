import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH,
  PLAYER_WEEKLY_USAGE_V1_SOURCE_BACKED_SOURCE_PATH,
  PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH,
  buildPlayerWeeklyUsageV1FromRawSources,
  toDeterministicPlayerWeeklyUsageV1Json,
  writePlayerWeeklyUsageV1Artifact,
} from '../src/index.js';

const normalizeNewlines = (value: string): string => value.replace(/\r\n/g, '\n');

describe('player weekly usage v1 artifact export', () => {
  it('validates required usage fields by parsing fixture-backed rows', () => {
    const artifact = buildPlayerWeeklyUsageV1FromRawSources();
    const first = artifact[0];

    expect(first).toMatchObject({ season: 2025, week: 1, player_id: '00-0034796' });
    expect(typeof first.targets).toBe('number');
    expect(typeof first.routes_run).toBe('number');
    expect(typeof first.route_participation).toBe('number');
    expect(typeof first.target_share).toBe('number');
    expect(typeof first.rush_share).toBe('number');
  });

  it('treats offline_fixture sourceKind as the default behavior', () => {
    const byDefault = toDeterministicPlayerWeeklyUsageV1Json();
    const byExplicitOffline = toDeterministicPlayerWeeklyUsageV1Json({ sourceKind: 'offline_fixture' });

    expect(byExplicitOffline).toEqual(byDefault);
  });

  it('fails closed when source_backed source file is missing', () => {
    expect(() =>
      buildPlayerWeeklyUsageV1FromRawSources({
        sourceKind: 'source_backed',
        sourcePath: path.join(os.tmpdir(), 'missing-player-usage-source-backed.json'),
      }),
    ).toThrow();
  });

  it('supports source_backed lane when source-backed file exists', () => {
    if (!existsSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_BACKED_SOURCE_PATH))) {
      return;
    }
    const artifact = buildPlayerWeeklyUsageV1FromRawSources({ sourceKind: 'source_backed' });

    expect(artifact.length).toBeGreaterThan(0);
    expect(artifact.every((row) => row.source.includes('nflreadpy.load_player_stats'))).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
    expect(artifact.every((row) => ['QB', 'RB', 'WR', 'TE'].includes(row.position))).toBe(true);
    expect(artifact.every((row) => typeof row.targets === 'number')).toBe(true);
    expect(artifact.every((row) => row.routes_run === null)).toBe(true);
    expect(artifact.every((row) => row.route_participation === null)).toBe(true);
    expect(artifact.every((row) => row.team_rushing_attempts === null)).toBe(true);
    expect(artifact.every((row) => row.rush_share === null)).toBe(true);
    expect(artifact.every((row) => row.red_zone_targets === null)).toBe(true);
    expect(artifact.every((row) => row.red_zone_carries === null)).toBe(true);
    expect(artifact.every((row) => row.snap_share === null)).toBe(true);
  });

  it('source_backed deterministic JSON generation is stable across two calls', () => {
    if (!existsSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_BACKED_SOURCE_PATH))) {
      return;
    }
    const first = toDeterministicPlayerWeeklyUsageV1Json({ sourceKind: 'source_backed' });
    const second = toDeterministicPlayerWeeklyUsageV1Json({ sourceKind: 'source_backed' });

    expect(first).toEqual(second);
  });

  it('fails closed when duplicate season/week/player_id rows are present', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-duplicates-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH), 'utf-8'));
    source.records.push({ ...source.records[0] });

    const invalidPath = path.join(tempRoot, 'duplicate-player-week.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyUsageV1FromRawSources({ sourcePath: invalidPath })).toThrow(
      'Duplicate player-week row detected',
    );
  });

  it('parses source-backed rows with negative air_yards_share', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-negative-air-yards-share-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH), 'utf-8'));
    source.records = [
      {
        ...source.records[0],
        target_share: 0.2,
        air_yards_share: -0.15,
      },
    ];
    source.provenance = 'nflreadpy.load_player_stats';
    source.source_path = 'nflverse player stats via nflreadpy';

    const sourceBackedPath = path.join(tempRoot, 'source-backed-negative-air-yards-share.json');
    writeFileSync(sourceBackedPath, JSON.stringify(source, null, 2), 'utf-8');

    const artifact = buildPlayerWeeklyUsageV1FromRawSources({
      sourceKind: 'source_backed',
      sourcePath: sourceBackedPath,
    });

    expect(artifact).toHaveLength(1);
    expect(artifact[0]?.air_yards_share).toBe(-0.15);
  });

  it('fails closed when target_share is out of [0, 1] bounds', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-invalid-target-share-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH), 'utf-8'));
    source.records = [
      {
        ...source.records[0],
        target_share: -0.01,
      },
    ];

    const invalidPath = path.join(tempRoot, 'invalid-target-share.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyUsageV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicPlayerWeeklyUsageV1Json();
    const second = toDeterministicPlayerWeeklyUsageV1Json();
    const committed = readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(normalizeNewlines(first)).toEqual(normalizeNewlines(committed));
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-v1-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writePlayerWeeklyUsageV1Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(normalizeNewlines(readFileSync(written, 'utf-8'))).toEqual(
      normalizeNewlines(toDeterministicPlayerWeeklyUsageV1Json()),
    );
  });

  it('fails closed when provenance is missing from raw payload wrapper', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH), 'utf-8'));
    delete source.provenance;

    const invalidPath = path.join(tempRoot, 'missing-provenance.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyUsageV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('fails closed when source_path is missing from raw payload wrapper', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH), 'utf-8'));
    delete source.source_path;

    const invalidPath = path.join(tempRoot, 'missing-source-path.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildPlayerWeeklyUsageV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('includes source and generated_at on every row', () => {
    const artifact = buildPlayerWeeklyUsageV1FromRawSources();

    expect(artifact.every((row) => row.source.length > 0)).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
  });

  it('fails closed for unsupported mode', () => {
    expect(() => buildPlayerWeeklyUsageV1FromRawSources({ mode: 'live_weekly_refresh' })).toThrow();
  });

});
