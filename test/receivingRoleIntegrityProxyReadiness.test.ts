import { describe, expect, it } from 'vitest';

import syntheticRows from './fixtures/receiving_role_integrity_proxy.synthetic.json' with { type: 'json' };
import {
  RECEIVING_ROLE_PROXY_BLOCKED_TRUE_ROUTE_FIELDS,
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
      'game_id',
      'player_id',
      'player_name',
      'team',
      'position',
    ]);
    expect(RECEIVING_ROLE_PROXY_SNAP_FIELDS).toEqual(['offense_snaps', 'snap_share']);
    expect(RECEIVING_ROLE_PROXY_REQUIRED_BASE_FIELDS).toEqual([
      'season',
      'week',
      'game_id',
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
      participationDenominatorField: 'pass_play_participation',
      status: 'ready_for_proxy_research',
    });
  });

  it('flags rows without a pass-play participation proxy denominator', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.rows[1]).toMatchObject({
      rowIndex: 1,
      participationDenominatorField: null,
      status: 'blocked_missing_shape',
    });
    expect(result.issues).toContainEqual({
      rowIndex: 1,
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
      rowIndex: 2,
      code: 'missing_joinable_receiving_usage_fields',
      fields: ['receiving_yards'],
    });
  });

  it('blocks unsupported true route claim fields in this scaffold', () => {
    const result = validateReceivingRoleProxyInputRows(syntheticRows);

    expect(result.rows[3]).toMatchObject({
      rowIndex: 3,
      participationDenominatorField: 'pass_play_participation',
      status: 'blocked_true_route_claim',
    });
    expect(result.issues).toContainEqual({
      rowIndex: 3,
      code: 'unsupported_true_route_claim_fields',
      fields: ['routes_run'],
    });
  });
});
