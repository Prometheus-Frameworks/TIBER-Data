import { describe, expect, it } from 'vitest';
import { createSyntheticNflmetaReconciler as create } from '../src/contracts/nflmetaSyntheticV0/crossReferences.js';
import { mappingPage, receipt, V1, V2 } from './fixtures/nflmetaSyntheticV0/builders.js';
const prior = { completedVersion: V2, bindings: [
  { nflmetaKey: 'synthetic-player-1', sleeperId: '900001' },
  { nflmetaKey: 'synthetic-retained-missing', sleeperId: '990001' },
] };
function changed(mutate: (page: any) => void, offset = 0) { const p = mappingPage(offset); mutate(p); return p; }

describe('NFLMeta synthetic full-registry reconciliation v0', () => {
  it('stages privately and proposes only after complete contiguous same-version pages', () => {
    const r = create(prior);
    r.submit(200, mappingPage(), receipt);
    expect(r.state()).toEqual({ phase: 'staging', stagedRows: 1, nextOffset: 1 });
    expect(r.result()).toBeNull();
    r.submit(200, mappingPage(1), receipt);
    expect(r.result()).toMatchObject({ disposition: 'proposed', completedVersion: V1,
      sourceAdmission: 'not_admitted', population: 'published_registry_not_all_profiles' });
    expect(r.result()!.proposedBindings).toEqual(expect.arrayContaining([
      ...prior.bindings.map(b => expect.objectContaining(b)),
      { nflmetaKey: 'synthetic-player-2', sleeperId: '900002', basis: 'provider_verified_relationship' },
      { nflmetaKey: 'synthetic-alias-2', sleeperId: '900002', basis: 'provider_verified_relationship' },
    ]));
    expect(r.result()!.proposedBindings!.find(b => b.nflmetaKey === 'synthetic-retained-missing')!.basis).toBe('retained_without_current_verification');
    expect(r.result()!.receipts).toHaveLength(2);
    expect(r.result()!.receipts[0].provenance).toBe('synthetic_only');
    expect(prior.completedVersion).toBe(V2);
  });
  it('uses the returned limit when a requested page size would be larger', () => {
    const r = create({ completedVersion: null, bindings: [] });
    r.submit(200, mappingPage(0, 3, 2), receipt);
    r.submit(200, mappingPage(2, 3, 2), receipt);
    expect(r.result()!.registryRows).toHaveLength(3);
  });
  it('retains prior identities for needs_review, absent and null mappings', () => {
    const r = create(prior);
    r.submit(200, changed(p => Object.assign(p.data[0], {
      status: 'needs_review', sleeper_player_id: null, verified_at: null, canonical_player_key: null,
    })), receipt);
    r.submit(200, mappingPage(1), receipt);
    expect(r.result()!.proposedBindings).toEqual(expect.arrayContaining(prior.bindings.map(b => ({ ...b, basis: 'retained_without_current_verification' }))));
  });
  it('blocks the entire proposal when an established identity conflicts', () => {
    const r = create({ ...prior, bindings: [{ nflmetaKey: 'synthetic-player-1', sleeperId: '999999' }] });
    r.submit(200, mappingPage(), receipt); r.submit(200, mappingPage(1), receipt);
    expect(r.result()).toMatchObject({ disposition: 'identity_conflict', proposedBindings: null,
      completedVersion: V2, conflicts: [{ nflmetaKey: 'synthetic-player-1', existingSleeperId: '999999', reportedSleeperId: '900001' }] });
  });
  it('permits canonical aliases with a shared Sleeper identity', () => {
    const r = create(prior);
    r.submit(200, mappingPage(), receipt);
    r.submit(200, changed(p => Object.assign(p.data[0], {
      canonical_player_key: 'synthetic-player-1', sleeper_player_id: '900001',
    }), 1), receipt);
    expect(r.result()!.disposition).toBe('proposed');
  });
  it('accepts a complete empty registry without deleting existing bindings', () => {
    const r = create(prior); r.submit(200, mappingPage(0, 0), receipt);
    expect(r.result()!.proposedBindings).toEqual(prior.bindings.map(b => ({ ...b, basis: 'retained_without_current_verification' })));
  });
  it('treats a conditional unchanged response as reuse, not an empty new baseline', () => {
    const r = create({ ...prior, completedVersion: V1 });
    const p = mappingPage(0, 0);
    Object.assign(p.meta, { sync_type: 'unchanged', not_modified: true, complete: false });
    r.submit(200, p, receipt);
    expect(r.result()).toMatchObject({ disposition: 'unchanged', completedVersion: V1,
      existingBindings: prior.bindings, proposedBindings: null });
  });
  it.each([409, 429, 401, 500])('discards every staged row on HTTP %s', status => {
    const r = create(prior); r.submit(200, mappingPage(), receipt);
    expect(() => r.submit(status, { error: 'untrusted-secret' }, receipt)).toThrow('discard staging and restart');
    expect(r.state()).toEqual({ phase: 'failed', stagedRows: 0, nextOffset: null });
    expect(r.result()).toBeNull();
    expect(() => r.submit(200, mappingPage(), receipt)).toThrow('terminal');
  });
  it('discards malformed/interrupted bodies and explicit cancellations', () => {
    const r = create(prior); r.submit(200, mappingPage(), receipt);
    expect(() => r.submit(200, '{interrupted', receipt)).toThrow(); expect(r.state().stagedRows).toBe(0);
    const canceled = create(prior); canceled.submit(200, mappingPage(), receipt); canceled.abort();
    expect(canceled.result()).toBeNull(); expect(canceled.state().phase).toBe('failed');
  });
  it.each([
    ['offset gap', (p: any) => p.meta.offset = 2],
    ['wrong content version', (p: any) => p.meta.version = V2],
    ['wrong snapshot boundary', (p: any) => p.meta.snapshot_id = 3],
    ['wrong total', (p: any) => p.meta.total = 3],
    ['unbound subsequent page', (p: any) => p.meta.version_bound = false],
    ['limit drift', (p: any) => p.meta.limit = 2],
    ['premature final page', (p: any) => p.meta.total = 4],
    ['false final flag', (p: any) => p.meta.complete = false],
    ['duplicate mapping ID', (p: any) => p.data[0].mapping_id = 1],
    ['mapping beyond snapshot', (p: any) => p.data[0].mapping_id = 100],
    ['alias collision', (p: any) => p.data[0].alias_keys = ['synthetic-alias-1']],
    ['canonical collision', (p: any) => p.data[0].canonical_player_key = 'synthetic-player-1'],
    ['Sleeper collision across canonical identities', (p: any) => p.data[0].sleeper_player_id = '900001'],
    ['unmapped batch row', (p: any) => Object.assign(p.data[0], { status: 'unmapped', sleeper_player_id: null })],
    ['duplicate alias', (p: any) => p.data[0].alias_keys.push(p.data[0].alias_keys[0])],
    ['review row leaking ID', (p: any) => p.data[0].status = 'needs_review'],
    ['verified row missing clock', (p: any) => p.data[0].verified_at = null],
    ['blank canonical identity', (p: any) => p.data[0].canonical_player_key = '   '],
    ['unsafe numeric mapping', (p: any) => p.data[0].mapping_id = 2 ** 53],
  ])('discards traversal on %s', (_label, mutate) => {
    const r = create(prior); r.submit(200, mappingPage(), receipt);
    expect(() => r.submit(200, changed(mutate, 1), receipt)).toThrow();
    expect(r.state().stagedRows).toBe(0); expect(r.result()).toBeNull();
  });
  it.each([
    ['additions-only cursor', (p: any) => p.meta.sync_type = 'additions'],
    ['hidden additions boundary', (p: any) => p.meta.after_id = 1],
    ['plan cannot complete', (p: any) => p.meta.can_complete = false],
    ['window blocked', (p: any) => p.meta.window_blocked = true],
    ['total exceeds window', (p: any) => p.meta.max_result_window = 1],
    ['incomplete page', (p: any) => p.meta.page_complete = false],
    ['starts at final page', (p: any) => p.meta.offset = 1],
    ['wrong returned count', (p: any) => p.meta.returned = 0],
    ['empty nonterminal page', (p: any) => { p.data = []; p.meta.returned = 0; }],
    ['wrong next offset', (p: any) => p.meta.next_offset = 2],
    ['unbound link', (p: any) => p.meta.next_page = '/api/v1/players/cross-references?offset=1'],
    ['foreign continuation', (p: any) => p.meta.next_page = 'https://evil.example/'],
    ['duplicate query parameter', (p: any) => p.meta.next_page += '&offset=1'],
    ['batch continuation', (p: any) => p.meta.next_page += '&player_keys=synthetic-player-1'],
    ['fragment continuation', (p: any) => p.meta.next_page += '#untrusted'],
    ['premature complete', (p: any) => p.meta.complete = true],
    ['excessive registry for this bounded rehearsal', (p: any) => p.meta.total = 10001],
  ])('refuses %s', (_label, mutate) => {
    const r = create(prior);
    expect(() => r.submit(200, changed(mutate), receipt)).toThrow(); expect(r.result()).toBeNull();
  });
  it('rejects unchanged without a matching completed baseline', () => {
    const p = mappingPage(0, 0); Object.assign(p.meta, { sync_type: 'unchanged', not_modified: true, complete: false });
    for (const version of [null, V2]) {
      const r = create({ ...prior, completedVersion: version }); expect(() => r.submit(200, p, receipt)).toThrow();
    }
  });
  it('isolates baseline/input/output mutations and refuses terminal reuse', () => {
    const b = structuredClone(prior); const r = create(b); b.bindings[0].sleeperId = '777';
    const p = mappingPage(); r.submit(200, p, receipt); p.data[0].sleeper_player_id = '888';
    r.submit(200, mappingPage(1), receipt);
    const out = r.result()!; out.proposedBindings![0].sleeperId = '999';
    expect(r.result()!.existingBindings[0].sleeperId).toBe('900001');
    expect(r.result()!.registryRows[0].sleeper_player_id).toBe('900001');
    expect(() => r.submit(200, mappingPage(1), receipt)).toThrow('terminal');
    expect(() => r.abort()).toThrow('terminal');
  });
});
