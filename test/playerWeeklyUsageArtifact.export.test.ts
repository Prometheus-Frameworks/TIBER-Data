import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH,
  PLAYER_WEEKLY_USAGE_V1_SOURCE_PATH,
  buildPlayerWeeklyUsageV1FromRawSources,
  toDeterministicPlayerWeeklyUsageV1Json,
  writePlayerWeeklyUsageV1Artifact,
} from '../src/index.js';

describe('player weekly usage v1 artifact export', () => {
  it('validates required usage fields by parsing fixture-backed rows', () => {
    const artifact = buildPlayerWeeklyUsageV1FromRawSources();
    const first = artifact[0];

    expect(first).toMatchObject({
      season: 2025,
      week: 1,
      player_id: '00-0034796',
      player_name: 'Jalen Hurts',
      team: 'PHI',
      position: 'QB',
      opponent: 'DAL',
    });
    expect(typeof first.targets).toBe('number');
    expect(typeof first.routes_run).toBe('number');
    expect(typeof first.route_participation).toBe('number');
    expect(typeof first.target_share).toBe('number');
    expect(typeof first.rush_share).toBe('number');
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

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicPlayerWeeklyUsageV1Json();
    const second = toDeterministicPlayerWeeklyUsageV1Json();
    const committed = readFileSync(path.resolve(PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'player-weekly-usage-v1-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writePlayerWeeklyUsageV1Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicPlayerWeeklyUsageV1Json());
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
