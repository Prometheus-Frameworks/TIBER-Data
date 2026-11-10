// Data-only inspection. This module never evaluates player metrics or authorizes consumers.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const REPO = 'Prometheus-Frameworks/TIBER-Data';
const STATUSES = new Set([
  'existing_code_inspection', 'existing_mapping_inspection',
  'proposed_ratio', 'existing_scaffold_inspection',
]);
const DIMENSIONS = [
  'numerator', 'denominator', 'formula', 'unit', 'grain',
  'event_eligibility', 'aggregation', 'missing_behavior',
];

export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const stable = (value) => Array.isArray(value)
  ? value.map(stable)
  : value && typeof value === 'object'
    ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]))
    : value;
export const digest = (value) => sha256(JSON.stringify(stable(value)));
export const serialize = (value) => `${JSON.stringify(value, null, 2)}\n`;

function requireThat(condition, message) {
  if (!condition) throw new Error(`definition inspection: ${message}`);
}

const nonempty = (value) => typeof value === 'string' && value.trim().length > 0;
const strings = (value) => Array.isArray(value) && value.length > 0 && value.every(nonempty);

function validateBinding(binding) {
  requireThat(binding && nonempty(binding.path), 'source path is required');
  requireThat(!path.isAbsolute(binding.path) && !binding.path.split('/').includes('..'),
    'source path must remain repository-relative');
  requireThat(/^[a-f0-9]{40}$/.test(binding.commit), 'source commit must be an exact SHA');
  requireThat(/^[a-f0-9]{64}$/.test(binding.sha256), 'source sha256 is required');
  requireThat(binding.symbol === null || nonempty(binding.symbol), 'source symbol must be explicit');
}

export function validateInspection(registry) {
  const config = registry.definition_inspection;
  requireThat(config && config.version === '0.1.0', 'unsupported or missing inspection version');
  requireThat(config.status === 'implementation_candidate' && config.consumer_authorized === false,
    'this inspection version cannot authorize canonical metrics or downstream consumption');
  requireThat(nonempty(config.authority), 'authority is required');
  requireThat(Array.isArray(config.definitions) && config.definitions.length > 0,
    'definitions must be a non-empty array');
  const ids = new Set();
  for (const definition of config.definitions) {
    requireThat(/^inspection\.[a-z0-9_.]+\.v[0-9]+$/.test(definition.id), 'invalid inspection ID');
    requireThat(!ids.has(definition.id), `duplicate ID ${definition.id}`);
    ids.add(definition.id);
    requireThat(nonempty(definition.family) && strings(definition.field_names), 'family/fields required');
    requireThat(STATUSES.has(definition.definition_status), 'unknown definition status');
    requireThat(definition.canonical_approval === 'not_granted', 'canonical approval is outside this layer');
    for (const key of ['numerator', 'denominator', 'formula']) {
      requireThat(definition[key] === null || nonempty(definition[key]), `${key} must be explicit`);
    }
    const components = ['numerator', 'denominator', 'formula'].map((key) => definition[key]);
    requireThat(components.every((v) => v === null) || components.every(nonempty),
      'formula and components must be complete together or unresolved together');
    requireThat(definition.unit === 'fraction' && strings(definition.grain), 'unit/grain required');
    requireThat(definition.event_eligibility?.status === 'unresolved'
      && nonempty(definition.event_eligibility.rule), 'event qualification remains unresolved in v0');
    requireThat(definition.aggregation?.status === 'not_selected'
      && nonempty(definition.aggregation.rule), 'aggregation must remain unselected in v0');
    requireThat(nonempty(definition.missing_behavior) && strings(definition.caveats), 'caveats/null policy required');
    requireThat(Array.isArray(definition.source_bindings) && definition.source_bindings.length > 0,
      'source bindings required');
    definition.source_bindings.forEach(validateBinding);
  }
  const byId = new Map(config.definitions.map((definition) => [definition.id, definition]));
  for (const definition of config.definitions) {
    requireThat(definition.alias_of === null || ids.has(definition.alias_of), 'unknown alias target');
    if (definition.alias_of !== null) {
      const target = byId.get(definition.alias_of);
      requireThat(target.alias_of === null && DIMENSIONS.slice(0, 6).every(
        (key) => digest(definition[key]) === digest(target[key])),
      'compatibility alias must preserve target components, formula, unit, grain and eligibility');
    }
  }
  requireThat(config.query_aliases && typeof config.query_aliases === 'object'
    && !Array.isArray(config.query_aliases), 'query aliases must be explicit');
  const families = new Set(config.definitions.map((definition) => definition.family));
  for (const [alias, targets] of Object.entries(config.query_aliases)) {
    requireThat(nonempty(alias) && strings(targets) && targets.every((family) => families.has(family)),
      'query alias refers to an unknown family');
  }
  for (const entry of registry.entries) {
    if (Object.hasOwn(entry, 'definition_ids')) {
      requireThat(strings(entry.definition_ids) && entry.definition_ids.every((id) => ids.has(id)
        && byId.get(id).field_names.includes(entry.field_name)), 'field references unknown/unrelated definition');
    }
  }
  requireThat(Array.isArray(config.coverage_artifacts), 'coverage artifacts must be explicit');
  const artifacts = new Set();
  for (const artifact of config.coverage_artifacts) {
    requireThat(nonempty(artifact.id) && !artifacts.has(artifact.id), 'duplicate/invalid artifact ID');
    artifacts.add(artifact.id);
    requireThat(['repository_source_backed', 'fixture'].includes(artifact.source_kind), 'unknown source kind');
    validateBinding(artifact.binding);
    requireThat(artifact.records_key === null || nonempty(artifact.records_key), 'records key must be explicit');
    requireThat(strings(artifact.fields), 'coverage fields required');
    requireThat(artifact.definition_bindings && typeof artifact.definition_bindings === 'object'
      && !Array.isArray(artifact.definition_bindings), 'coverage definition bindings required');
    for (const [field, id] of Object.entries(artifact.definition_bindings)) {
      requireThat(artifact.fields.includes(field) && ids.has(id)
        && byId.get(id).field_names.includes(field), 'artifact definition binding is unknown/unrelated');
    }
  }
  return config;
}

function readPinned(root, binding) {
  validateBinding(binding);
  let bytes;
  try {
    bytes = execFileSync('git', ['show', `${binding.commit}:${binding.path}`], {
      cwd: root, maxBuffer: 32 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch {
    throw new Error(`definition inspection: unavailable source pin ${binding.commit}:${binding.path}`);
  }
  requireThat(sha256(bytes) === binding.sha256, `pinned source digest mismatch: ${binding.path}`);
  if (binding.symbol !== null && binding.path.endsWith('.py')) {
    requireThat(bytes.toString('utf8').includes(`def ${binding.symbol}(`),
      `source symbol is missing: ${binding.path}:${binding.symbol}`);
  }
  let working;
  try { working = fs.readFileSync(path.join(root, binding.path)); } catch {
    throw new Error(`definition inspection: working source missing: ${binding.path}`);
  }
  requireThat(sha256(working) === binding.sha256, `source drift requires review: ${binding.path}`);
  return bytes;
}

export function loadInspection(registry, root) {
  const config = validateInspection(registry);
  const checked = new Set();
  for (const definition of config.definitions) {
    for (const binding of definition.source_bindings) {
      const key = digest(binding);
      if (!checked.has(key)) readPinned(root, binding);
      checked.add(key);
    }
  }
  return { config, root, catalogDigest: digest(config) };
}

// The denial flags are re-applied after any payload so that no payload can override them.
const DENIAL = Object.freeze({ consumer_authorized: false, canonical_approval: 'not_granted' });

function envelope(context, status, payload = {}) {
  return {
    inspection_version: context.config.version,
    status,
    inspection_scope: 'definition_and_coverage_inspection_only',
    ...DENIAL,
    catalog_sha256: context.catalogDigest,
    ...payload,
    ...DENIAL,
  };
}

// Failure response for requests that never reach a validated catalog (invalid request,
// invalid registry, blocked inspection). A failure is never an approval or an authorization.
export function refusal(status, error, payload = {}) {
  return { ...payload, status, ...DENIAL, error: String(error) };
}

function definitionView(definition) {
  return {
    ...definition,
    definition_sha256: digest(definition),
    sources: definition.source_bindings.map((binding) => ({
      ...binding, url: `https://github.com/${REPO}/blob/${binding.commit}/${binding.path}`,
    })),
    observation_evidence: 'not_assessed',
  };
}

export function catalog(context) {
  return envelope(context, 'inspection_catalog', {
    definitions: context.config.definitions.map(definitionView),
    coverage_artifact_ids: context.config.coverage_artifacts.map((artifact) => artifact.id),
  });
}

export function lookup(context, query) {
  const key = query.trim().toLowerCase();
  const exact = context.config.definitions.find((definition) => definition.id === key);
  if (exact) return envelope(context, 'definition', { definition: definitionView(exact) });
  const families = Object.hasOwn(context.config.query_aliases, key)
    ? context.config.query_aliases[key] : [key];
  const matches = context.config.definitions.filter((definition) => families.includes(definition.family)
    || definition.field_names.includes(key));
  if (matches.length === 0) return envelope(context, 'not_indexed', { query, matches: [] });
  // Family/name queries always require an exact-ID selection, even if there is currently one variant.
  return envelope(context, 'selection_required', {
    query, matches: matches.map(definitionView),
    reason: 'Choose an exact definition ID; family/name lookup never selects a variant.',
  });
}

export function compare(context, leftId, rightId) {
  const left = context.config.definitions.find((definition) => definition.id === leftId);
  const right = context.config.definitions.find((definition) => definition.id === rightId);
  if (!left || !right) return envelope(context, 'not_indexed', { reason: 'compare requires two exact IDs' });
  const differences = DIMENSIONS.filter((key) => digest(left[key]) !== digest(right[key]));
  const concreteConflict = ['numerator', 'denominator', 'unit', 'grain'].some((key) =>
    left[key] !== null && right[key] !== null && digest(left[key]) !== digest(right[key]));
  return envelope(context, 'definition_comparison', {
    left: leftId, right: rightId,
    compatibility: leftId === rightId ? 'same_definition' : concreteConflict ? 'incompatible' : 'unresolved',
    differing_dimensions: differences,
    observation_comparability: 'not_assessed',
    reason: 'A matching definition does not qualify sources, event populations, coverage or consumer use.',
  });
}

export function inspectCoverage(context, artifactId) {
  const artifact = context.config.coverage_artifacts.find((item) => item.id === artifactId);
  if (!artifact) return envelope(context, 'not_indexed', { reason: 'coverage requires an exact artifact ID' });
  const bytes = readPinned(context.root, artifact.binding);
  const payload = JSON.parse(bytes.toString('utf8'));
  const rows = artifact.records_key === null ? payload : payload[artifact.records_key];
  requireThat(Array.isArray(rows) && rows.every((row) => row && typeof row === 'object'
    && !Array.isArray(row)), 'artifact must contain object records');
  const labels = [...new Set(rows.map((row) => row.source).filter(nonempty))].sort();
  const fixtureRows = rows.filter((row) => typeof row.source === 'string'
    && row.source.startsWith('offline_fixture:')).length;
  requireThat(artifact.source_kind !== 'fixture' || fixtureRows === rows.length,
    'fixture artifact lost its explicit row-level fixture labels');
  requireThat(artifact.source_kind !== 'repository_source_backed' || fixtureRows === 0,
    'fixture rows cannot be classified as source-backed');
  const columns = Object.fromEntries(artifact.fields.map((field) => {
    const values = rows.map((row) => row[field]).filter((value) => value !== null && value !== undefined);
    const numeric = values.filter((value) => typeof value === 'number' && Number.isFinite(value));
    const definitionId = artifact.definition_bindings[field] ?? null;
    const definition = context.config.definitions.find((item) => item.id === definitionId);
    return [field, {
      missing: rows.length - values.length,
      non_null: values.length,
      numeric_non_null: numeric.length,
      invalid_numeric_or_domain: values.length - numeric.filter((value) => value >= 0
        && (field === 'routes_run' ? Number.isInteger(value) : value <= 1)).length,
      zero_value_count: numeric.filter((value) => value === 0).length,
      measurement_support: artifact.source_kind === 'fixture' ? 'fixture_only'
        : values.length === 0 ? 'unavailable' : 'unqualified_values',
      definition_id: definitionId,
      definition_binding: definition?.formula ? 'inspection_only' : definition ? 'unresolved_formula' : 'unbound',
    }];
  }));
  const values = (field) => [...new Set(rows.map((row) => row[field])
    .filter((value) => value !== undefined && value !== null))].sort((a, b) =>
    typeof a === 'number' && typeof b === 'number' ? a - b : String(a).localeCompare(String(b)));
  return envelope(context, 'coverage_receipt', {
    artifact_id: artifactId,
    source: { ...artifact.binding,
      url: `https://github.com/${REPO}/blob/${artifact.binding.commit}/${artifact.binding.path}` },
    source_kind: artifact.source_kind,
    source_labels: labels,
    source_admission: artifact.source_kind === 'fixture' ? 'fixture_only' : 'not_assessed',
    rows: rows.length,
    columns,
    scope: { seasons: values('season'), weeks: values('week'), season_types: values('season_type'),
      season_type_coverage: rows.every((row) => nonempty(row.season_type)) ? 'present' : 'unknown_or_partial' },
    clocks: { artifact_generated_at: payload.generated_at ?? null, source_snapshot_at: null },
    population_completeness: 'unknown',
    identity_resolution: 'not_assessed',
    caveat: 'Counts inspect only this pinned artifact. Non-null and zero values do not establish valid measurements, source admission or current coverage.',
  });
}

export function inspectionMarkdown(context) {
  const rows = context.config.definitions.map((definition) =>
    `| ${definition.id} | ${definition.definition_status} | ${definition.denominator ?? 'unresolved'} |`);
  return `# Metric Definition Inspection Generated View\n\n`
    + `Inspection candidate; canonical approval and downstream consumption are not granted.\n\n`
    + `Generated from projection_input_semantics.json; catalog SHA-256: \`${context.catalogDigest}\`.\n\n`
    + `| Exact inspection ID | Status | Denominator |\n| --- | --- | --- |\n${rows.join('\n')}\n\n`
    + `Exact formulas, source pins, null policies and caveats are in the JSON output. `
    + `Coverage receipts are separate; this table contains no player observations.\n`;
}
