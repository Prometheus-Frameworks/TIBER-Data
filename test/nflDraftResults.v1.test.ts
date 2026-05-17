import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  NFL_DRAFT_RESULTS_V1_PROMOTED_EXPORT_PATH_TEMPLATE,
  nflDraftResultRecordSchema,
  promotedNflDraftResultsPath,
  validateNflDraftResultsArtifact,
} from '../src/index.js';

const FIXTURE_PATH = 'test/fixtures/nfl_draft_results_2026.contract_fixture.json';
const PROMOTED_2026_PATH = 'exports/promoted/nfl_draft_results/nfl_draft_results_2026.json';

function loadJson(relativePath: string): unknown {
  return JSON.parse(readFileSync(path.resolve(relativePath), 'utf-8'));
}

function loadFixture(): unknown {
  return loadJson(FIXTURE_PATH);
}

describe('nfl draft results v1 contract', () => {
  it('validates the bounded one-year contract fixture without claiming official coverage', () => {
    const artifact = validateNflDraftResultsArtifact(loadFixture());

    expect(artifact).toHaveLength(1);
    expect(artifact[0]).toMatchObject({
      draft_year: 2026,
      player_id: null,
      source_url: null,
      provenance_status: 'fixture_only',
      source: 'contract_validation_fixture_not_official_draft_result',
    });
  });

  it('validates the officially promoted 2026 artifact with source-backed unresolved player IDs', () => {
    const artifact = validateNflDraftResultsArtifact(loadJson(PROMOTED_2026_PATH));

    expect(artifact).toHaveLength(257);
    expect(artifact.map((row) => row.overall_pick)).toEqual(Array.from({ length: 257 }, (_, index) => index + 1));
    expect(new Set(artifact.map((row) => row.draft_year))).toEqual(new Set([2026]));
    expect(new Set(artifact.map((row) => row.provenance_status))).toEqual(
      new Set(['source_verified_player_id_unresolved']),
    );

    for (const row of artifact) {
      expect(row.player_id).toBeNull();
      expect(row.source).toBe('NBC Sports ProFootballTalk 2026 NFL Draft picks full tracker, published 2026-04-25');
      expect(row.source_url).toBe(
        'https://www.nbcsports.com/nfl/profootballtalk/news/2026-nfl-draft-picks-full-tracker-of-every-selection-rounds-1-7',
      );
      expect(row.provenance_status).not.toBe('fixture_only');
      expect(row.provenance_status).not.toBe('needs_verification');
    }

    expect(artifact[0]).toMatchObject({
      player_name: 'Fernando Mendoza',
      position: 'QB',
      team: 'Las Vegas Raiders',
      round: 1,
      pick_in_round: 1,
      overall_pick: 1,
    });
    expect(artifact[256]).toMatchObject({
      player_name: 'Red Murdock',
      position: 'LB',
      team: 'Denver Broncos',
      round: 7,
      pick_in_round: 41,
      overall_pick: 257,
    });
  });

  it('documents the promoted export path template and formats a concrete year path', () => {
    expect(NFL_DRAFT_RESULTS_V1_PROMOTED_EXPORT_PATH_TEMPLATE).toBe(
      'exports/promoted/nfl_draft_results/nfl_draft_results_{year}.json',
    );
    expect(promotedNflDraftResultsPath(2026)).toBe(
      'exports/promoted/nfl_draft_results/nfl_draft_results_2026.json',
    );
  });

  it('requires positive draft pick integers and a valid draft year', () => {
    const [row] = validateNflDraftResultsArtifact(loadFixture());

    expect(() => nflDraftResultRecordSchema.parse({ ...row, round: 0 })).toThrow();
    expect(() => nflDraftResultRecordSchema.parse({ ...row, pick_in_round: -1 })).toThrow();
    expect(() => nflDraftResultRecordSchema.parse({ ...row, overall_pick: 0 })).toThrow();
    expect(() => nflDraftResultRecordSchema.parse({ ...row, draft_year: 1935 })).toThrow();
  });

  it('requires core identity, provenance, and timestamp fields', () => {
    const [row] = validateNflDraftResultsArtifact(loadFixture());

    for (const field of ['player_name', 'position', 'team', 'source', 'generated_at', 'provenance_status']) {
      expect(() => nflDraftResultRecordSchema.parse({ ...row, [field]: '' })).toThrow();
    }
  });

  it('allows null player_id only when the provenance status makes unresolved identity explicit', () => {
    const [row] = validateNflDraftResultsArtifact(loadFixture());

    expect(() =>
      nflDraftResultRecordSchema.parse({
        ...row,
        provenance_status: 'source_verified',
      }),
    ).toThrow();

    expect(
      nflDraftResultRecordSchema.parse({
        ...row,
        provenance_status: 'source_verified_player_id_unresolved',
      }).player_id,
    ).toBeNull();

    expect(() =>
      nflDraftResultRecordSchema.parse({
        ...row,
        player_id: 'draft-player-1',
        provenance_status: 'source_verified_player_id_unresolved',
      }),
    ).toThrow();
  });
});
