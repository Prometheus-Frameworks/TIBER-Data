import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  HISTORICAL_ROOKIE_REPLAY_READINESS_V0_ARTIFACT_PATH,
  HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_REPLAY_PATH,
  HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_ROSTER_PATH,
  HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_OFFENSE_SUMMARY_PATH,
  HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_PACE_PASS_PATH,
  buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts,
  toDeterministicHistoricalRookieReplayReadinessV0Json,
  writeHistoricalRookieReplayReadinessV0Artifact,
} from '../src/index.js';

describe('historical rookie replay readiness v0 artifact export', () => {
  it('validates required output fields', () => {
    const artifact = buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts();
    const first = artifact[0];
    expect(first).toHaveProperty('replay_season');
    expect(first).toHaveProperty('player_id');
    expect(first).toHaveProperty('expected_team');
    expect(first).toHaveProperty('team_context_ready');
    expect(Array.isArray(first.missing_evidence)).toBe(true);
  });

  it('validates source/generated_at presence', () => {
    const artifact = buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts();
    expect(artifact.every((row) => row.source.length > 0)).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
  });

  it('validates deterministic parity with committed promoted artifact', () => {
    const first = toDeterministicHistoricalRookieReplayReadinessV0Json();
    const second = toDeterministicHistoricalRookieReplayReadinessV0Json();
    const committed = readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_READINESS_V0_ARTIFACT_PATH), 'utf-8');
    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('validates unsupported mode fails closed', () => {
    expect(() => buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts({ mode: 'live_weekly_refresh' })).toThrow();
  });

  it('validates duplicate replay player fails closed', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'readiness-dup-replay-'));
    const replay = JSON.parse(readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_REPLAY_PATH), 'utf-8'));
    replay.push({ ...replay[0] });
    const replayPath = path.join(tempRoot, 'replay.json');
    writeFileSync(replayPath, JSON.stringify(replay, null, 2), 'utf-8');
    expect(() => buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts({ replayPath })).toThrow('Duplicate replay row detected');
  });

  it('validates duplicate roster season/week/player_id fails closed', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'readiness-dup-roster-'));
    const roster = JSON.parse(readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_ROSTER_PATH), 'utf-8'));
    roster.push({ ...roster[0] });
    const rosterPath = path.join(tempRoot, 'roster.json');
    writeFileSync(rosterPath, JSON.stringify(roster, null, 2), 'utf-8');
    expect(() => buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts({ rosterPath })).toThrow('Duplicate roster row detected');
  });

  it('validates duplicate team environment season/team fails closed', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'readiness-dup-team-'));
    const pace = JSON.parse(readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_TEAM_PACE_PASS_PATH), 'utf-8'));
    pace.push({ ...pace[0] });
    const pacePath = path.join(tempRoot, 'pace.json');
    writeFileSync(pacePath, JSON.stringify(pace, null, 2), 'utf-8');
    expect(() => buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts({ teamPacePassPath: pacePath })).toThrow(
      'Duplicate team_pace_pass_environment row detected',
    );
  });

  it('validates missing input artifact fails closed', () => {
    expect(() => buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts({ replayPath: 'missing.json' })).toThrow(
      'Required artifact is missing',
    );
  });

  it('validates no fuzzy name matching is performed', () => {
    const artifact = buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts();
    const emeka = artifact.find((row) => row.player_name === 'Emeka Egbuka');
    expect(emeka?.roster_identity_found).toBe(false);
    expect(emeka?.readiness_status).toBe('missing_identity');
  });

  it('validates missing identity produces missing_identity status', () => {
    const artifact = buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts();
    expect(artifact.every((row) => row.readiness_status === 'missing_identity')).toBe(true);
  });

  it('validates full match produces ready status if fixture IDs support one', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'readiness-ready-'));
    const replay = JSON.parse(readFileSync(path.resolve(HISTORICAL_ROOKIE_REPLAY_READINESS_V0_SOURCE_REPLAY_PATH), 'utf-8'));
    replay[0].player_id = 'fixture_ashton_jeanty';
    const replayPath = path.join(tempRoot, 'replay-ready.json');
    writeFileSync(replayPath, JSON.stringify(replay, null, 2), 'utf-8');

    const artifact = buildHistoricalRookieReplayReadinessV0FromPromotedArtifacts({ replayPath });
    const ashton = artifact.find((row) => row.player_id === 'fixture_ashton_jeanty');
    expect(ashton?.readiness_status).toBe('ready');
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'readiness-write-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writeHistoricalRookieReplayReadinessV0Artifact(outputPath);
    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicHistoricalRookieReplayReadinessV0Json());
  });
});
