import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  TEAM_OFFENSE_SUMMARY_V1_ARTIFACT_PATH,
  TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH,
  buildTeamOffenseSummaryV1FromRawSources,
  toDeterministicTeamOffenseSummaryV1Json,
  writeTeamOffenseSummaryV1Artifact,
} from '../src/index.js';

describe('team offense summary v1 artifact export', () => {
  it('validates required fields with deterministic fixture-backed rows', () => {
    const artifact = buildTeamOffenseSummaryV1FromRawSources();
    const first = artifact[0];

    expect(first).toMatchObject({
      season: 2025,
      team: 'ARI',
    });
    expect(typeof first.points_per_game).toBe('number');
    expect(typeof first.yards_per_play).toBe('number');
    expect(typeof first.offensive_plays_per_game).toBe('number');
    expect(typeof first.touchdowns_per_game).toBe('number');
    expect(typeof first.turnover_rate).toBe('number');
  });

  it('fails closed when duplicate season/team rows are present', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-offense-summary-duplicates-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH), 'utf-8'));
    source.records.push({ ...source.records[0] });

    const invalidPath = path.join(tempRoot, 'duplicate-season-team.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildTeamOffenseSummaryV1FromRawSources({ sourcePath: invalidPath })).toThrow(
      'Duplicate team offense summary row detected',
    );
  });

  it('includes source and generated_at on every row', () => {
    const artifact = buildTeamOffenseSummaryV1FromRawSources();

    expect(artifact.every((row) => row.source.length > 0)).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
  });

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicTeamOffenseSummaryV1Json();
    const second = toDeterministicTeamOffenseSummaryV1Json();
    const committed = readFileSync(path.resolve(TEAM_OFFENSE_SUMMARY_V1_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('fails closed for unsupported mode', () => {
    expect(() => buildTeamOffenseSummaryV1FromRawSources({ mode: 'live_weekly_refresh' })).toThrow();
  });

  it('fails closed when wrapper provenance/source_path/records are missing', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-offense-summary-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH), 'utf-8'));

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

    expect(() => buildTeamOffenseSummaryV1FromRawSources({ sourcePath: missingProvenancePath })).toThrow();
    expect(() => buildTeamOffenseSummaryV1FromRawSources({ sourcePath: missingSourcePathPath })).toThrow();
    expect(() => buildTeamOffenseSummaryV1FromRawSources({ sourcePath: missingRecordsPath })).toThrow();
  });

  it('fails closed when turnover_rate is outside 0..1 bounds', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-offense-summary-turnover-bounds-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].turnover_rate = 1.2;

    const invalidPath = path.join(tempRoot, 'turnover-out-of-bounds.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildTeamOffenseSummaryV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('allows nullable optional rate fields', () => {
    const artifact = buildTeamOffenseSummaryV1FromRawSources();
    const lv = artifact.find((row) => row.team === 'LV');

    expect(lv?.scoring_drive_rate).toBeNull();
    expect(lv?.offensive_success_rate).toBeNull();
    expect(lv?.red_zone_td_rate).toBeNull();
  });

  it('allows negative offensive_epa_per_play values inside signed bounds', () => {
    const artifact = buildTeamOffenseSummaryV1FromRawSources();
    const lv = artifact.find((row) => row.team === 'LV');

    expect(lv?.offensive_epa_per_play).toBeLessThan(0);
  });

  it('fails closed when offensive_epa_per_play is outside sane bounds', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-offense-summary-epa-bounds-'));
    const source = JSON.parse(readFileSync(path.resolve(TEAM_OFFENSE_SUMMARY_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].offensive_epa_per_play = -1.1;

    const invalidPath = path.join(tempRoot, 'epa-out-of-bounds.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildTeamOffenseSummaryV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'team-offense-summary-v1-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writeTeamOffenseSummaryV1Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicTeamOffenseSummaryV1Json());
  });
});
