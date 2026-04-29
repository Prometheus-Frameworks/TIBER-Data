import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  ROSTER_PLAYER_TEAM_MAP_V1_ARTIFACT_PATH,
  ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_BACKED_SOURCE_PATH,
  ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH,
  buildRosterPlayerTeamMapV1FromRawSources,
  toDeterministicRosterPlayerTeamMapV1Json,
  writeRosterPlayerTeamMapV1Artifact,
} from '../src/index.js';

describe('roster player/team map v1 artifact export', () => {
  it('validates required fields with deterministic fixture-backed rows', () => {
    const artifact = buildRosterPlayerTeamMapV1FromRawSources();
    const first = artifact[0];

    expect(first).toMatchObject({
      season: 2025,
      week: 1,
      team: 'BAL',
    });
    expect(typeof first.player_id).toBe('string');
    expect(typeof first.player_name).toBe('string');
    expect(typeof first.position).toBe('string');
  });

  it('fails closed when duplicate season/week/player_id rows are present', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'roster-player-team-map-duplicates-'));
    const source = JSON.parse(readFileSync(path.resolve(ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH), 'utf-8'));
    source.records.push({ ...source.records[0] });

    const invalidPath = path.join(tempRoot, 'duplicate-season-week-player-id.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourcePath: invalidPath })).toThrow(
      'Duplicate roster player/team row detected',
    );
  });

  it('includes source and generated_at on every row', () => {
    const artifact = buildRosterPlayerTeamMapV1FromRawSources();

    expect(artifact.every((row) => row.source.length > 0)).toBe(true);
    expect(artifact.every((row) => row.generated_at.length > 0)).toBe(true);
  });

  it('is deterministic and matches committed promoted artifact', () => {
    const first = toDeterministicRosterPlayerTeamMapV1Json();
    const second = toDeterministicRosterPlayerTeamMapV1Json();
    const committed = readFileSync(path.resolve(ROSTER_PLAYER_TEAM_MAP_V1_ARTIFACT_PATH), 'utf-8');

    expect(first).toEqual(second);
    expect(first).toEqual(committed);
  });

  it('fails closed for unsupported mode', () => {
    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ mode: 'live_weekly_refresh' })).toThrow();
  });

  it('fails closed when wrapper provenance/source_path/records are missing', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'roster-player-team-map-wrapper-'));
    const source = JSON.parse(readFileSync(path.resolve(ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH), 'utf-8'));

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

    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourcePath: missingProvenancePath })).toThrow();
    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourcePath: missingSourcePathPath })).toThrow();
    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourcePath: missingRecordsPath })).toThrow();
  });

  it('validates active_roster_status enum', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'roster-player-team-map-status-'));
    const source = JSON.parse(readFileSync(path.resolve(ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].active_roster_status = 'suspended';

    const invalidPath = path.join(tempRoot, 'invalid-active-roster-status.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('validates source_status enum', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'roster-player-team-map-source-status-'));
    const source = JSON.parse(readFileSync(path.resolve(ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_PATH), 'utf-8'));
    source.records[0].source_status = 'unknown_source';

    const invalidPath = path.join(tempRoot, 'invalid-source-status.json');
    writeFileSync(invalidPath, JSON.stringify(source, null, 2), 'utf-8');

    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourcePath: invalidPath })).toThrow();
  });

  it('defaults to fixture source and keeps existing scaffold behavior', () => {
    const defaultRows = buildRosterPlayerTeamMapV1FromRawSources();
    const explicitFixtureRows = buildRosterPlayerTeamMapV1FromRawSources({ sourceKind: 'offline_fixture' });

    expect(defaultRows).toEqual(explicitFixtureRows);
  });

  it('fails closed when source_backed source path is requested but missing', () => {
    expect(() => buildRosterPlayerTeamMapV1FromRawSources({ sourceKind: 'source_backed' })).toThrow(
      ROSTER_PLAYER_TEAM_MAP_V1_SOURCE_BACKED_SOURCE_PATH,
    );
  });

  it('maps Tetairoa McMillan to CAR', () => {
    const artifact = buildRosterPlayerTeamMapV1FromRawSources();
    const tet = artifact.find((row) => row.player_name === 'Tetairoa McMillan');

    expect(tet?.team).toBe('CAR');
  });

  it('writes deterministic output to disk', () => {
    const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'roster-player-team-map-v1-'));
    const outputPath = path.join(tempRoot, 'artifact.json');
    const written = writeRosterPlayerTeamMapV1Artifact(outputPath);

    expect(written).toEqual(path.resolve(outputPath));
    expect(readFileSync(written, 'utf-8')).toEqual(toDeterministicRosterPlayerTeamMapV1Json());
  });
});
