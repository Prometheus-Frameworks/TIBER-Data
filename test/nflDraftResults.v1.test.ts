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

function loadFixture(): unknown {
  return JSON.parse(readFileSync(path.resolve(FIXTURE_PATH), 'utf-8'));
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
