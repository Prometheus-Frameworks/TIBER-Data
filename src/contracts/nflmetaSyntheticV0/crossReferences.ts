import { z } from 'zod';
import { nflmetaHash, nflmetaInteger, nflmetaSyntheticEvidence, nflmetaText, nflmetaTimestamp } from './common.js';

const sleeperId = z.string().regex(/^\d+$/).max(32);
const mappingSchema = z.object({
  player_key: nflmetaText.nullable(), canonical_player_key: nflmetaText.nullable(),
  sleeper_player_id: sleeperId.nullable(), mapping_id: nflmetaInteger.positive().nullable(),
  verified_at: nflmetaTimestamp.nullable(),
  status: z.enum(['verified', 'unmapped', 'needs_review', 'not_found']),
  alias_keys: z.array(nflmetaText).max(1000),
}).passthrough().superRefine((row, ctx) => {
  const fail = (message: string) => ctx.addIssue({ code: 'custom', message });
  if (row.status === 'verified') {
    if (row.sleeper_player_id === null || row.canonical_player_key === null || row.player_key === null
      || row.mapping_id === null || row.verified_at === null) fail('Verified mapping requires identity and verification fields');
  } else if (row.sleeper_player_id !== null) fail('Only verified mappings may publish a Sleeper ID');
  if (new Set(row.alias_keys).size !== row.alias_keys.length) fail('Duplicate alias');
});

const pageSchema = z.object({
  data: z.array(mappingSchema).max(1000),
  meta: z.object({
    total: nflmetaInteger.max(10_000), limit: nflmetaInteger.positive().max(1000),
    offset: nflmetaInteger, snapshot_id: nflmetaInteger, after_id: nflmetaInteger,
    returned: nflmetaInteger, max_page_size: nflmetaInteger.positive().max(1000),
    next_offset: nflmetaInteger.nullable(), max_result_window: nflmetaInteger.nullable(),
    version_bound: z.boolean(), page_complete: z.boolean(), not_modified: z.boolean(),
    has_more: z.boolean(), complete: z.boolean(), can_complete: z.boolean(), window_blocked: z.boolean(),
    version: nflmetaHash, sync_type: z.enum(['full', 'additions', 'unchanged']),
    scope: z.literal('published_registry'), consistency: z.literal('version_bound_restart_on_change'),
    next_page: z.string().max(2048).nullable(), last_checked_at: nflmetaTimestamp.nullable(),
    refresh_schedule: z.literal('hourly_check_with_24_hour_minimum'), unmapped_meaning: z.string(),
  }).passthrough(),
}).passthrough();

type Page = z.infer<typeof pageSchema>;
type Mapping = z.infer<typeof mappingSchema>;
const bindingSchema = z.object({ nflmetaKey: nflmetaText, sleeperId }).strict();
const baselineSchema = z.object({
  completedVersion: nflmetaHash.nullable(),
  bindings: z.array(bindingSchema).max(10_000),
}).strict().superRefine((baseline, ctx) => {
  if (new Set(baseline.bindings.map(b => b.nflmetaKey)).size !== baseline.bindings.length) {
    ctx.addIssue({ code: 'custom', message: 'Duplicate existing key' });
  }
});
type Binding = z.infer<typeof bindingSchema>;
type Evidence = ReturnType<typeof nflmetaSyntheticEvidence>;
export type NflmetaSyntheticReconciliation = {
  disposition: 'proposed' | 'identity_conflict' | 'unchanged';
  sourceAdmission: 'not_admitted';
  observedVersion: string;
  /** No version advancement on an identity conflict. */
  completedVersion: string | null;
  existingBindings: Binding[];
  proposedBindings: (Binding & { basis: 'provider_verified_relationship' | 'retained_without_current_verification' })[] | null;
  conflicts: { nflmetaKey: string; existingSleeperId: string; reportedSleeperId: string }[];
  registryRows: Mapping[];
  receipts: Evidence[];
  population: 'published_registry_not_all_profiles';
};

/** Only inspect the link; never rebuild it for fetching or issue a request. */
function validateContinuation(page: Page) {
  const m = page.meta;
  if (!m.next_page?.startsWith('/api/v1/players/cross-references?')) throw new Error('Invalid continuation');
  const url = new URL(m.next_page, 'https://nflmeta.org');
  const allowed = ['provider', 'limit', 'offset', 'snapshot_id', 'version', 'after_id'];
  for (const key of url.searchParams.keys()) {
    if (!allowed.includes(key) || url.searchParams.getAll(key).length !== 1) throw new Error('Invalid continuation');
  }
  if (url.hash || url.searchParams.get('version') !== m.version
    || url.searchParams.get('snapshot_id') !== String(m.snapshot_id)
    || url.searchParams.get('offset') !== String(m.next_offset)
    || url.searchParams.get('limit') !== String(m.limit)
    || ![null, 'sleeper'].includes(url.searchParams.get('provider'))
    || ![null, '0'].includes(url.searchParams.get('after_id'))) throw new Error('Unbound continuation');
}

/**
 * Pure in-memory rehearsal. Caller supplies invented HTTP outcomes. No network,
 * persistent store, crosswalk writes, admission or automatic identity replacement.
 * A fresh instance is required after failure; no staged row escapes before completion.
 */
export function createSyntheticNflmetaReconciler(baselineInput: unknown) {
  const baseline = baselineSchema.parse(baselineInput);
  let phase: 'staging' | 'complete' | 'failed' = 'staging';
  let rows: Mapping[] = [];
  let receipts: Evidence[] = [];
  let first: Page['meta'] | undefined;
  let nextOffset = 0;
  let result: NflmetaSyntheticReconciliation | null = null;
  const fail = () => {
    rows = []; receipts = []; first = undefined; result = null; phase = 'failed';
  };
  function propose(meta: Page['meta']): NflmetaSyntheticReconciliation {
    const candidates = new Map<string, string>();
    const canonicalBySleeper = new Map<string, string>();
    const mappingIds = new Set<number>();
    for (const row of rows) {
      // Full-list rows are registered; batch-only missing/not_found results are not a registry.
      if (row.mapping_id === null || row.player_key === null || row.mapping_id > meta.snapshot_id
        || mappingIds.has(row.mapping_id) || !['verified', 'needs_review'].includes(row.status)) {
        throw new Error('Invalid registry identity');
      }
      mappingIds.add(row.mapping_id);
      if (row.status !== 'verified') continue;
      const id = row.sleeper_player_id!;
      const canonical = row.canonical_player_key!;
      const priorCanonical = canonicalBySleeper.get(id);
      if (priorCanonical && priorCanonical !== canonical) throw new Error('Sleeper identity collision');
      canonicalBySleeper.set(id, canonical);
      for (const key of [row.player_key, canonical, ...row.alias_keys]) {
        const priorId = candidates.get(key);
        if (priorId && priorId !== id) throw new Error('Alias identity collision');
        candidates.set(key, id);
      }
    }
    const existing = new Map(baseline.bindings.map(b => [b.nflmetaKey, b.sleeperId]));
    const conflicts: NflmetaSyntheticReconciliation['conflicts'] = [];
    for (const [key, id] of candidates) {
      const priorId = existing.get(key);
      if (priorId && priorId !== id) conflicts.push({ nflmetaKey: key, existingSleeperId: priorId, reportedSleeperId: id });
    }
    const merged = new Map([...existing, ...candidates]);
    return {
      disposition: conflicts.length ? 'identity_conflict' : 'proposed', sourceAdmission: 'not_admitted',
      observedVersion: meta.version, completedVersion: conflicts.length ? baseline.completedVersion : meta.version,
      existingBindings: baseline.bindings,
      proposedBindings: conflicts.length ? null : Array.from(merged, ([nflmetaKey, sleeperId]) => ({
        nflmetaKey, sleeperId, basis: candidates.has(nflmetaKey)
          ? 'provider_verified_relationship' as const : 'retained_without_current_verification' as const,
      })),
      conflicts, registryRows: rows, receipts, population: 'published_registry_not_all_profiles',
    };
  }
  return {
    state: () => ({ phase, stagedRows: rows.length, nextOffset: phase === 'staging' ? nextOffset : null }),
    /** Aborts interrupted bodies, quota failures or caller cancellation without advancing the baseline. */
    abort: () => { if (phase !== 'staging') throw new Error('Reconciler is terminal'); fail(); },
    submit: (httpStatus: number, body: unknown, receipt: unknown): void => {
      if (phase !== 'staging') throw new Error('Reconciler is terminal');
      try {
        if (httpStatus !== 200) throw new Error('HTTP failure');
        const page = structuredClone(pageSchema.parse(body));
        const m = page.meta;
        const evidence = nflmetaSyntheticEvidence(receipt);
        if (m.sync_type === 'unchanged') {
          if (first || baseline.completedVersion === null || m.version !== baseline.completedVersion
            || !m.not_modified || page.data.length !== 0 || m.returned !== 0 || m.complete || m.has_more
            || m.next_page !== null || m.next_offset !== null || m.offset !== 0 || m.after_id !== 0) {
            throw new Error('Invalid unchanged response');
          }
          result = {
            disposition: 'unchanged', sourceAdmission: 'not_admitted', observedVersion: m.version,
            completedVersion: baseline.completedVersion, existingBindings: baseline.bindings,
            proposedBindings: null, conflicts: [], registryRows: [], receipts: [evidence],
            population: 'published_registry_not_all_profiles',
          };
          phase = 'complete'; return;
        }
        if (m.sync_type !== 'full' || m.after_id !== 0 || m.not_modified || !m.page_complete
          || !m.can_complete || m.window_blocked || m.offset !== nextOffset
          || m.returned !== page.data.length || m.returned > m.limit || m.limit > m.max_page_size
          || (m.max_result_window !== null && m.total > m.max_result_window)
          || m.offset + m.returned > m.total) throw new Error('Incomplete full traversal');
        if (first && (!m.version_bound || m.version !== first.version || m.snapshot_id !== first.snapshot_id
          || m.total !== first.total || m.limit !== first.limit)) throw new Error('Traversal changed');
        if (!first) first = m;
        const end = m.offset + m.returned;
        if (m.has_more) {
          if (m.returned === 0 || m.complete || end >= m.total || m.next_offset !== end) throw new Error('Invalid page continuation');
          validateContinuation(page);
        } else if (!m.complete || end !== m.total || m.next_offset !== null || m.next_page !== null) {
          throw new Error('Incomplete terminal page');
        }
        rows.push(...page.data); receipts.push(evidence); nextOffset = end;
        if (!m.has_more) { result = propose(m); phase = 'complete'; }
      } catch {
        fail();
        // Bounded error, never echo untrusted provider content.
        throw new Error('Synthetic reconciliation refused; discard staging and restart');
      }
    },
    result: (): NflmetaSyntheticReconciliation | null => result === null ? null : structuredClone(result),
  };
}
