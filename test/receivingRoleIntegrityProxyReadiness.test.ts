import { describe, expect, it } from 'vitest';

import syntheticRows from './fixtures/receiving_role_integrity_proxy.synthetic.json' with { type: 'json' };
import {
  RECEIVING_ROLE_PROXY_BLOCKED_TRUE_ROUTE_FIELDS,
  RECEIVING_ROLE_PROXY_GAME_IDENTIFIER_CANDIDATE_FIELDS,
  RECEIVING_ROLE_PROXY_IDENTITY_FIELDS,
  RECEIVING_ROLE_PROXY_JOINABLE_USAGE_FIELDS,
  RECEIVING_ROLE_PROXY_PARTICIPATION_DENOMINATOR_CANDIDATE_FIELDS,
  RECEIVING_ROLE_PROXY_REQUIRED_BASE_FIELDS,
  RECEIVING_ROLE_PROXY_SNAP_FIELDS,
  validateReceivingRoleProxyInputRows,
} from '../src/research/receivingRoleIntegrityProxyReadiness.js';

describe('Receiving Role Integrity proxy readiness scaffold', () => {
  it('documents expected public-source shape without true route claims', () => {
    expect(RECEIVING_ROLE_PROXY_IDENTITY_FIELDS).toEqual([
      'season',
      'week',
      'player_id',
      'player_name',
      'team',
      'position',
    ]);
    expect(RECEIVING_ROLE_PROXY_GAME_IDENTIFIER_CANDIDATE_FIELDS).toEqual([
      'game_id',
      'nflverse_game_id',
    ]);
    expect(RECEIVING_ROLE_PROXY_SNAP_FIELDS).toEqual(['offense_snaps', 'snap_share']);
    expect(RECEIVING_ROLE_PROXY_REQUIRED_BASE_FIELDS).toEqual([
      'season',
      'week',
      'player_id',
      'player_name',
      'team',
      'position',
      'offense_snaps',
      'snap_share',
    ]);
    expect(RECEIVING_ROLE_PROXY_PARTICIPATION_DENOMINATOR_CANDIDATE_FIELDS).toEqual([
      'pass_play_participation',
      'pass_play_participation_proxy',
      'pass_play_participation_count',
      'offense_pass_play_participation',
    ]);
    expect(RECEIVING_ROLE_PROXY_JOINABLE_USAGE_FIELDS).toEqual([
      'targets',
      'receptions',
      'receiving_yards',
    ]);
    expect(RECEIVING_ROLE_PROXY_BLOCKED_TRUE_ROUTE_FIELDS).toContain('routes_run');
  });

  it('classifies a complete proxy-shaped row as ready for proxy research only', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.rows[0]).toMatchObject({
      rowIndex: 0,
      gameIdentifierField: 'game_id',
      participationDenominatorField: 'pass_play_participation',
      status: 'ready_for_proxy_research',
    });
  });

  it('classifies a complete proxy-shaped row with nflverse_game_id as ready', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.rows[1]).toMatchObject({
      rowIndex: 1,
      gameIdentifierField: 'nflverse_game_id',
      participationDenominatorField: 'pass_play_participation',
      status: 'ready_for_proxy_research',
    });
  });

  it('fails closed when neither game identifier candidate is present', () => {
    const result = validateReceivingRoleProxyInputRows([
      {
        season: 2025,
        week: 1,
        player_id: '00-0030006',
        player_name: 'Example Missing Game Id',
        team: 'ARI',
        position: 'WR',
        offense_snaps: 18,
        snap_share: 0.28,
        pass_play_participation: 9,
        targets: 1,
        receptions: 1,
        receiving_yards: 7,
      },
    ]);

    expect(result.rows[0]).toMatchObject({
      rowIndex: 0,
      gameIdentifierField: null,
      status: 'blocked_missing_shape',
    });
    expect(result.issues).toContainEqual({
      rowIndex: 0,
      code: 'missing_game_identifier_fields',
      fields: ['game_id', 'nflverse_game_id'],
    });
  });

  it('flags rows without a pass-play participation proxy denominator', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.rows[2]).toMatchObject({
      rowIndex: 2,
      participationDenominatorField: null,
      status: 'blocked_missing_shape',
    });
    expect(result.issues).toContainEqual({
      rowIndex: 2,
      code: 'missing_pass_play_participation_proxy',
      fields: [
        'pass_play_participation',
        'pass_play_participation_proxy',
        'pass_play_participation_count',
        'offense_pass_play_participation',
      ],
    });
  });

  it('flags rows missing joinable receiving usage fields', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.issues).toContainEqual({
      rowIndex: 3,
      code: 'missing_joinable_receiving_usage_fields',
      fields: ['receiving_yards'],
    });
  });

  it('blocks unsupported true route claim fields in this scaffold', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.rows[4]).toMatchObject({
      rowIndex: 4,
      participationDenominatorField: 'pass_play_participation',
      status: 'blocked_true_route_claim',
    });
    expect(result.issues).toContainEqual({
      rowIndex: 4,
      code: 'unsupported_true_route_claim_fields',
      fields: ['routes_run'],
    });
  });
});
