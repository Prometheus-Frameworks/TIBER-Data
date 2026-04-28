import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  TEAM_PACE_PASS_ENVIRONMENT_V1_ARTIFACT_PATH,
  TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH,
  buildTeamPacePassEnvironmentV1FromRawSources,
  toDeterministicTeamPacePassEnvironmentV1Json,
  writeTeamPacePassEnvironmentV1Artifact,
} from '../src/index.js';

describe('team pace/pass environment v1 artifact export', () => {
  it('validates required fields with deterministic fixture-backed rows', () => {
    const artifact = buildTeamPacePassEnvironmentV1FromRawSources();
    const first = artifact[0];

    expect(first).toMatchObject({
      season: 2025,
      team: 'ARI',
    });
    expect(typeof first.plays_per_game).toBe('number');
    expect(typeof first.neutral_pass_rate).toBe('number');
    expect(typeof first.dropbacks_per_game).toBe('number');
    expect(typeof first.red_zone_pass_rate).toBe('number');
    expect(typeof first.wr_target_share).toBe('number');
    expect(typeof first.te_target_share).toBe('number');
    expect(typeof first.rb_target_share).toBe('number');
  });

  it('fails closed when duplicate season/team rows are present', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-pace-pass-environment-duplicates-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH), 'utf-8'));
    source.records.push({ ...source.records[0] });

    const invalidPath = path.join(tempRoot, 'duplicate-season-team.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: invalidPath })).toThrow(
      'Duplicate team environment row detected',
    );
  });

  it('fails closed when wrapper provenance/source_path/records are missing', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-pace-pass-environment-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH), 'utf-8'));

    const missingProvenancePath = path.join(tempRoot, 'missing-provenance.json');
    const missingSourcePathPath = path.join(tempRoot, 'missing-source-path.json');
    const missingRecordsPath = path.join(tempRoot, 'missing-records.json');

    const missingProvenance = { ...source };
    const missingSourcePath = { ...source };
    const missingRecords = { ...source };
    delete missingProvenance.provenance;
    delete missingSourcePath.source_path;
    delete missingRecords.records;

    writeFileSync(missingProvenancePath, JSON.stringify(missingProvenance, null, 2), 'utf-8');
    writeFileSync(missingSourcePathPath, JSON.stringify(missingSourcePath, null, 2), 'utf-8');
    writeFileSync(missingRecordsPath, JSON.stringify(missingRecords, null, 2), 'utf-8');

    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: missingProvenancePath })).toThrow();
    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: missingSourcePathPath })).toThrow();
    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: missingRecordsPath })).toThrow();
  });

  it('includes source and generated_at on every row', () => {
    const artifact = buildTeamPacePassEnvironmentV1FromRawSources();

    expect(artifact.every((row) => row.source.length > 0)).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
  });

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicTeamPacePassEnvironmentV1Json();
    const second = toDeterministicTeamPacePassEnvironmentV1Json();
    const committed = readFileSync(path.resolve(TEAM_PACE_PASS_ENVIRONMENT_V1_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('fails closed for unsupported mode', () => {
    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ mode: 'live_weekly_refresh' })).toThrow();
  });

  it('allows negative pass_rate_over_expected values in signed delta bounds', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-pace-pass-environment-proe-negative-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].pass_rate_over_expected = -0.031;

    const validPath = path.join(tempRoot, 'proe-negative.json');
    writeFileSync(validPath, JSON.stringify(source, null, 2), 'utf-8');

    const artifact = buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: validPath });
    expect(artifact.find((row) => row.team === 'ARI')?.pass_rate_over_expected).toBe(-0.031);
  });

  it('fails closed when pass_rate_over_expected is outside -1..1 bounds', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-pace-pass-environment-proe-bounds-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].pass_rate_over_expected = -1.1;

    const invalidPath = path.join(tempRoot, 'proe-out-of-bounds.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('fails closed when rate/share fields are outside 0..1 bounds', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-pace-pass-environment-rate-bounds-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_PACE_PASS_ENVIRONMENT_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].neutral_pass_rate = 1.1;

    const invalidPath = path.join(tempRoot, 'rate-out-of-bounds.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildTeamPacePassEnvironmentV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-pace-pass-environment-v1-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writeTeamPacePassEnvironmentV1Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicTeamPacePassEnvironmentV1Json());
  });
});
