import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  HISTORICAL_ROOKIE_REPLAY_V0_ARTIFACT_PATH,
  HISTORICAL_ROOKIE_REPLAY_V0_SOURCE_PATH,
  buildHistoricalRookieReplayV0FromRawSources,
  toDeterministicHistoricalRookieReplayV0Json,
  writeHistoricalRookieReplayV0Artifact,
} from '../src/index.js';

describe('historical rookie replay v0 artifact export', () => {
  it('validates required row fields with deterministic fixture-backed rows', () => {
    const artifact = buildHistoricalRookieReplayV0FromRawSources();
    const first = artifact[0];

    expect(first).toMatchObject({
      replay_season: 2025,
      player_id: 'fixture.2025.RB.AshtonJeanty',
      player_name: 'Ashton Jeanty',
      position: 'RB',
      draft_round: 1,
      draft_pick: 9,
    });
    expect(Array.isArray(first.actual_weekly_ppr)).toBe(true);
    expect(typeof first.season_ppr).toBe('number');
    expect(typeof first.weekly_volatility).toBe('number');
    expect(typeof first.startable_weeks).toBe('number');
    expect(typeof first.spike_weeks).toBe('number');
    expect(typeof first.bust_weeks).toBe('number');
  });

  it('validates evidence_status enum fail-closed behavior', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'historical-rookie-replay-evidence-status-'));
    const source = JSON.parse(readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_V0_SOURCE_PATH), 'utf-8'));
    source.records[0].evidence_status = 'unknown_status';

    const invalidPath = path.join(tempRoot, 'invalid-evidence-status.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildHistoricalRookieReplayV0FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('fails closed when duplicate replay_season/player_id rows are present', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'historical-rookie-replay-duplicates-'));
    const source = JSON.parse(readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_V0_SOURCE_PATH), 'utf-8'));
    source.records.push({ ...source.records[0] });

    const invalidPath = path.join(tempRoot, 'duplicate-replay-player.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildHistoricalRookieReplayV0FromRawSources({ sourcePath: invalidPath })).toThrow(
      'Duplicate replay row detected',
    );
  });

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicHistoricalRookieReplayV0Json();
    const second = toDeterministicHistoricalRookieReplayV0Json();
    const committed = readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_V0_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('includes source and generated_at on every row', () => {
    const artifact = buildHistoricalRookieReplayV0FromRawSources();

    expect(artifact.every((row) => row.source.length > 0)).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
  });

  it('fails closed for unsupported mode', () => {
    expect(() => buildHistoricalRookieReplayV0FromRawSources({ mode: 'live_weekly_refresh' })).toThrow();
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'historical-rookie-replay-v0-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writeHistoricalRookieReplayV0Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicHistoricalRookieReplayV0Json());
  });
});
