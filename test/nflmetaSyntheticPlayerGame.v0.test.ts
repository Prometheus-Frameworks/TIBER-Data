import { describe, expect, it } from 'vitest';
import { decodeSyntheticNflmetaPlayerGames as decode, NFLMETA_BASE_STATS } from '../src/contracts/nflmetaSyntheticV0/playerGame.js';
import { playerPage, receipt, V1, V2 } from './fixtures/nflmetaSyntheticV0/builders.js';

// Mutations intentionally cross the unknown-input boundary with malformed objects.
function changed(mutate: (page: any) => void) { const page = playerPage(); mutate(page); return page; }
describe('NFLMeta synthetic player-game contract v0', () => {
  it('preserves all 34 fields, source zero, four statuses, negative yards and fractional sacks', () => {
    const output = decode(playerPage(), receipt);
    expect(NFLMETA_BASE_STATS).toHaveLength(34);
    const row = output.rows[0].providerRow;
    expect(row.pass_int).toBe(0);
    expect(row.targets).toBeNull(); expect(row.stat_status.targets).toBe('missing');
    expect(row.rec).toBeNull(); expect(row.stat_status.rec).toBe('partial');
    expect(row.fga).toBeNull(); expect(row.stat_status.fga).toBe('not_reported');
    expect(row.rush_yds).toBe(-2); expect(row.def_sacks).toBe(0.5);
    expect(output.evidence).toMatchObject({ provenance: 'synthetic_only', sourceAdmission: 'not_admitted',
      retentionRights: 'unresolved', independentVerification: 'not_performed', providerPublishedAt: null });
    expect(output.rows[0].factBasis).toBe('provider_reported_unverified');
  });
  it('keeps calendar date, source write and simulated receipt clocks separate', () => {
    const output = decode(playerPage(), receipt);
    expect(output.rows[0].providerRow.game_date).toBe('2030-01-01');
    expect(output.rows[0].kickoffAt).toBeNull();
    expect(output.rows[0].providerWriteAt).toBe('2030-01-02T11:00:00Z');
    expect(output.evidence.receivedAt).toBe(receipt.receivedAt);
    expect(output.rows[0].finality).toBe('unknown');
  });
  it('does not manufacture participation from an empty ranked page', () => {
    const p = playerPage(); p.data = []; p.meta.total = 0; p.meta.returned = 0;
    expect(decode(p, receipt)).toMatchObject({ rows: [], absentPlayerMeaning: 'unknown',
      population: 'filtered_ranked_page_not_participation_census' });
  });
  it('permits null dates and unresolved identities without name joining', () => {
    const p = changed(p => Object.assign(p.data[0], { game_date: null, player_id: null, player_key: null, resolved_player: false }));
    expect(decode(p, receipt).rows[0].providerRow.player_key).toBeNull();
  });
  it('retains opaque fields rather than stripping provider lineage', () => {
    const p = changed(p => { p.data[0].source_note = { upstream: 'synthetic-only' }; });
    const out = decode(p, receipt);
    expect(out.rows[0].providerRow.source_note).toEqual({ upstream: 'synthetic-only' });
    (p.data[0] as any).source_note.upstream = 'mutated';
    expect(out.rows[0].providerRow.source_note).toEqual({ upstream: 'synthetic-only' });
  });
  it('does not treat a write-clock change as a content revision or invent history', () => {
    const a = decode(playerPage(), receipt);
    const b = decode(changed(p => p.data[0].boxscore_updated_at = '2030-01-02T11:30:00Z'), receipt);
    expect(a.rows[0].contentFingerprint).toBe(b.rows[0].contentFingerprint);
    expect(b.correctionHistory).toBe('unavailable');
    for (const v of [V1, V2, V1]) expect(decode(changed(p => p.data[0].stat_version = v), receipt).rows[0].contentFingerprint).toBe(v);
  });
  it('accepts selected fractional rates without converting them to percent points', () => {
    const p = changed(p => { p.meta.stat = 'pass_cmp_pct'; p.data[0].pass_cmp_pct = 0.6; p.data[0].stat_value = 0.6; });
    expect(decode(p, receipt).rows[0].providerRow.pass_cmp_pct).toBe(0.6);
  });
  it.each([
    ['numeric contract version', (p: any) => p.meta.contract_version = 2],
    ['unknown contract version', (p: any) => p.meta.contract_version = '3'],
    ['omitted count', (p: any) => delete p.data[0].fga],
    ['omitted status', (p: any) => delete p.data[0].stat_status.fga],
    ['null reported value', (p: any) => p.data[0].pass_int = null],
    ['zero filled missing', (p: any) => p.data[0].targets = 0],
    ['non-null partial', (p: any) => p.data[0].rec = 2],
    ['numeric string', (p: any) => p.data[0].pass_int = '0'],
    ['NaN', (p: any) => p.data[0].pass_int = NaN],
    ['infinite sack', (p: any) => p.data[0].def_sacks = Infinity],
    ['fractional attempt', (p: any) => p.data[0].pass_att = 1.5],
    ['rolled over date', (p: any) => p.data[0].game_date = '2030-02-30'],
    ['kickoff as date', (p: any) => p.data[0].game_date += 'T12:00:00Z'],
    ['invalid write clock', (p: any) => p.data[0].boxscore_updated_at = 'yesterday'],
    ['missing fingerprint', (p: any) => delete p.data[0].stat_version],
    ['wrong season', (p: any) => p.data[0].season_year = 2029],
    ['wrong season type', (p: any) => p.data[0].season_type = 'POST'],
    ['duplicate player-game', (p: any) => { p.data.push(p.data[0]); p.meta.total = 2; p.meta.returned = 2; }],
    ['blank identity key', (p: any) => p.data[0].player_key = '   '],
    ['false resolved identity', (p: any) => p.data[0].player_key = null],
    ['missing selected value', (p: any) => p.meta.stat = 'targets'],
    ['wrong selected value', (p: any) => p.data[0].stat_value = 3],
    ['wrong page count', (p: any) => p.meta.returned = 2],
    ['false continuation', (p: any) => p.meta.has_more = true],
    ['unknown selected statistic', (p: any) => p.meta.stat = 'invented_metric'],
    ['unavailable derived input', (p: any) => { p.meta.stat = 'catch_pct'; p.data[0].catch_pct = 0; }],
    ['zero derived denominator', (p: any) => { p.meta.stat = 'pass_cmp_pct'; p.data[0].pass_att = 0; p.data[0].pass_cmp_pct = 0; }],
    ['percent points instead of fraction', (p: any) => { p.meta.stat = 'pass_cmp_pct'; p.data[0].pass_cmp_pct = 60; p.data[0].stat_value = 60; }],
    ['rate inconsistent with inputs', (p: any) => { p.meta.stat = 'pass_cmp_pct'; p.data[0].pass_cmp_pct = 0.8; p.data[0].stat_value = 0.8; }],
    ['missing selected derived field', (p: any) => p.meta.stat = 'pass_cmp_pct'],
  ])('refuses %s', (_label, mutate) => expect(() => decode(changed(mutate), receipt)).toThrow());
  it('rejects a receipt claiming real acquisition or admission', () => {
    expect(() => decode(playerPage(), { ...receipt, sourceAdmission: 'admitted' })).toThrow();
    expect(() => decode(playerPage(), { ...receipt, fixtureId: 'real-response' })).toThrow();
  });
  it('does not mutate input rows or filters', () => {
    const p = playerPage(); const before = structuredClone(p);
    const out = decode(p, receipt); out.rows[0].providerRow.pass_int = 100;
    expect(p).toEqual(before);
  });
});
