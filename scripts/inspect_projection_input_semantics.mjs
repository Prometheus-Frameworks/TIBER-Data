#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import {
  catalog, compare, inspectCoverage, inspectionMarkdown, loadInspection, lookup, refusal, serialize,
  validateInspection,
} from './lib/metric_definition_inspection.mjs';

const DEFAULT_REGISTRY = 'data/semantics/projection_input_semantics.json';
const DEFAULT_OUTPUT = 'docs/projection-input-semantics.generated.md';
const ALLOWED_OPTIONS = new Set([
  'registry', 'write', 'output', 'group', 'status', 'consumer',
  'definitions', 'id', 'left', 'right', 'artifact', 'json', 'check-generated',
]);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const GENERATED_JSON = 'data/semantics/metric_definitions.generated.json';
const GENERATED_MARKDOWN = 'docs/metric-definitions.generated.md';
const REQUIRED_ENTRY_FIELDS = [
  'field_group',
  'field_name',
  'description',
  'owner_source',
  'artifact_source_path_if_known',
  'position_relevance',
  'time_scope',
  'semantic_type',
  'nullability_missing_behavior',
  'provenance_expectations',
  'downstream_consumers',
  'consumption_recommendation',
  'status',
  'notes_open_questions',
];
const ALLOWED_POSITIONS = new Set(['QB', 'RB', 'WR', 'TE']);
const ALLOWED_STATUSES = new Set(['supported', 'candidate', 'needs_verification']);
const ALLOWED_RECOMMENDATIONS = new Set([
  'pass_directly',
  'adapt_before_consumption',
  'not_consumed_yet',
]);
const ALLOWED_CONSUMERS = new Set(['Point-prediction-model', 'FORGE', 'TIBER-Fantasy']);
const ALLOWED_SEMANTIC_TYPES = new Set([
  'factual',
  'derived',
  'interpretive',
  'factual_or_derived_source_metric',
]);

function printUsage() {
  console.log('Definition inspection: --definitions <list|get|compare|coverage> [--id <exact-id>] [--left <id> --right <id>] [--artifact <exact-artifact-id>] [--json]');
  console.log('Generation: --definitions list --write | --definitions list --check-generated');
  console.log(`Usage: node scripts/inspect_projection_input_semantics.mjs [options]\n\nOptions:\n  --registry <path>   Semantics registry JSON path (default: ${DEFAULT_REGISTRY})\n  --write             Write generated markdown summary\n  --output <path>     Generated markdown output path (default: ${DEFAULT_OUTPUT})\n  --group <name>      Filter by field_group\n  --status <status>   Filter by status\n  --consumer <name>   Filter by downstream consumer\n  --help, -h          Show this help\n\nExamples:\n  node scripts/inspect_projection_input_semantics.mjs\n  node scripts/inspect_projection_input_semantics.mjs --status needs_verification\n  node scripts/inspect_projection_input_semantics.mjs --write`);
}

function fail(message) {
  console.error(`Error: ${message}`);
  process.exitCode = 1;
}

function parseArgs(argv) {
  const options = { registry: DEFAULT_REGISTRY, output: DEFAULT_OUTPUT };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === '--help' || arg === '-h') {
      options.help = true;
      continue;
    }

    if (['--write', '--json', '--check-generated'].includes(arg)) {
      options[arg.slice(2)] = true;
      continue;
    }

    if (!arg.startsWith('--')) {
      throw new Error(`unexpected positional argument: ${arg}`);
    }

    const key = arg.slice(2);
    if (!ALLOWED_OPTIONS.has(key)) {
      throw new Error(`unknown option: ${arg}`);
    }

    const value = argv[index + 1];
    if (value === undefined || value.startsWith('--')) {
      throw new Error(`missing value for ${arg}`);
    }

    options[key] = value;
    index += 1;
  }

  if (options.status && !ALLOWED_STATUSES.has(options.status)) {
    throw new Error(`--status must be one of: ${[...ALLOWED_STATUSES].join(', ')}`);
  }

  if (options.consumer && !ALLOWED_CONSUMERS.has(options.consumer)) {
    throw new Error(`--consumer must be one of: ${[...ALLOWED_CONSUMERS].join(', ')}`);
  }

  if (options.definitions) {
    const required = { list: [], get: ['id'], compare: ['left', 'right'], coverage: ['artifact'] };
    if (!Object.hasOwn(required, options.definitions)) throw new Error('unknown definition operation');
    for (const key of required[options.definitions]) {
      if (!options[key]) throw new Error(`--${key} is required`);
    }
    for (const key of ['id', 'left', 'right', 'artifact']) {
      if (options[key] && !required[options.definitions].includes(key)) {
        throw new Error(`--${key} is not used by this operation`);
      }
    }
    if (options.group || options.status || options.consumer || argv.includes('--output')) {
      throw new Error('definition operations do not accept legacy filters or --output');
    }
    if ((options.write || options['check-generated']) && options.definitions !== 'list') {
      throw new Error('generation is only available with --definitions list');
    }
    if (options.write && options['check-generated']) throw new Error('choose write or check-generated');
  } else if (['id', 'left', 'right', 'artifact', 'check-generated', 'json'].some((key) => options[key])) {
    throw new Error('definition-specific options require --definitions');
  }

  return options;
}

function loadRegistry(registryPath) {
  const resolvedPath = path.resolve(process.cwd(), registryPath);
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`registry file is missing: ${registryPath}`);
  }

  let registry;
  try {
    registry = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'));
  } catch (error) {
    throw new Error(`registry JSON is invalid: ${registryPath} (${error.message})`);
  }

  validateRegistry(registry);
  return { registry, resolvedPath };
}

function assertNonEmptyString(value, fieldPath, errors) {
  if (typeof value !== 'string' || value.trim() === '') {
    errors.push(`${fieldPath} must be a non-empty string`);
  }
}

function assertStringArray(value, fieldPath, errors, allowedValues) {
  if (!Array.isArray(value) || value.length === 0) {
    errors.push(`${fieldPath} must be a non-empty array`);
    return;
  }

  for (const item of value) {
    if (typeof item !== 'string' || item.trim() === '') {
      errors.push(`${fieldPath} contains a non-string or empty value`);
      continue;
    }

    if (allowedValues && !allowedValues.has(item)) {
      errors.push(`${fieldPath} contains unsupported value: ${item}`);
    }
  }
}

function validateRegistry(registry) {
  const errors = [];

  assertNonEmptyString(registry.registry_name, 'registry_name', errors);
  assertNonEmptyString(registry.version, 'version', errors);
  assertNonEmptyString(registry.purpose, 'purpose', errors);
  assertNonEmptyString(registry.scope_boundary, 'scope_boundary', errors);

  if (!Array.isArray(registry.entries) || registry.entries.length === 0) {
    errors.push('entries must be a non-empty array');
  }

  const seen = new Set();
  for (const [index, entry] of (registry.entries ?? []).entries()) {
    const entryPath = `entries[${index}]`;
    for (const field of REQUIRED_ENTRY_FIELDS) {
      if (!Object.hasOwn(entry, field)) {
        errors.push(`${entryPath}.${field} is required`);
      }
    }

    assertNonEmptyString(entry.field_group, `${entryPath}.field_group`, errors);
    assertNonEmptyString(entry.field_name, `${entryPath}.field_name`, errors);
    assertNonEmptyString(entry.description, `${entryPath}.description`, errors);
    assertNonEmptyString(entry.owner_source, `${entryPath}.owner_source`, errors);
    assertNonEmptyString(entry.time_scope, `${entryPath}.time_scope`, errors);
    assertNonEmptyString(entry.nullability_missing_behavior, `${entryPath}.nullability_missing_behavior`, errors);
    assertNonEmptyString(entry.provenance_expectations, `${entryPath}.provenance_expectations`, errors);

    if (
      entry.artifact_source_path_if_known !== null &&
      (typeof entry.artifact_source_path_if_known !== 'string' ||
        entry.artifact_source_path_if_known.trim() === '')
    ) {
      errors.push(`${entryPath}.artifact_source_path_if_known must be null or a non-empty string`);
    }

    assertStringArray(entry.position_relevance, `${entryPath}.position_relevance`, errors, ALLOWED_POSITIONS);
    assertStringArray(entry.downstream_consumers, `${entryPath}.downstream_consumers`, errors, ALLOWED_CONSUMERS);
    assertStringArray(entry.notes_open_questions, `${entryPath}.notes_open_questions`, errors);

    if (!ALLOWED_SEMANTIC_TYPES.has(entry.semantic_type)) {
      errors.push(`${entryPath}.semantic_type must be one of: ${[...ALLOWED_SEMANTIC_TYPES].join(', ')}`);
    }

    if (!ALLOWED_RECOMMENDATIONS.has(entry.consumption_recommendation)) {
      errors.push(`${entryPath}.consumption_recommendation must be one of: ${[...ALLOWED_RECOMMENDATIONS].join(', ')}`);
    }

    if (!ALLOWED_STATUSES.has(entry.status)) {
      errors.push(`${entryPath}.status must be one of: ${[...ALLOWED_STATUSES].join(', ')}`);
    }

    const key = entry.field_name;
    if (typeof key === 'string' && key.trim() !== '') {
      if (seen.has(key)) {
        errors.push(`${entryPath}.field_name is duplicated: ${key}`);
      }
      seen.add(key);
    }
  }

  if (errors.length > 0) {
    throw new Error(`registry validation failed:\n- ${errors.join('\n- ')}`);
  }
  if (Object.hasOwn(registry, 'definition_inspection')) validateInspection(registry);
}

function applyFilters(entries, options) {
  return entries.filter((entry) => {
    if (options.group && entry.field_group !== options.group) {
      return false;
    }
    if (options.status && entry.status !== options.status) {
      return false;
    }
    if (options.consumer && !entry.downstream_consumers.includes(options.consumer)) {
      return false;
    }
    return true;
  });
}

function escapeMarkdown(value) {
  return String(value ?? '')
    .replaceAll('\\', '\\\\')
    .replaceAll('|', '\\|')
    .replaceAll('\n', '<br>');
}

function summarize(value, maxLength = 96) {
  const text = Array.isArray(value) ? value.join(', ') : String(value ?? '');
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}…`;
}

function markdownTable(entries, { compact = false } = {}) {
  const columns = compact
    ? [
        ['field', (entry) => entry.field_name],
        ['group', (entry) => entry.field_group],
        ['status', (entry) => entry.status],
        ['recommendation', (entry) => entry.consumption_recommendation],
        ['positions', (entry) => entry.position_relevance.join(', ')],
        ['scope', (entry) => entry.time_scope],
        ['type', (entry) => entry.semantic_type],
        ['source/path', (entry) => summarize(entry.artifact_source_path_if_known ?? 'unknown', 72)],
      ]
    : [
        ['field_name', (entry) => entry.field_name],
        ['description', (entry) => entry.description],
        ['owner/source', (entry) => entry.owner_source],
        ['artifact/source path if known', (entry) => entry.artifact_source_path_if_known ?? 'unknown'],
        ['position relevance', (entry) => entry.position_relevance.join(', ')],
        ['scope', (entry) => entry.time_scope],
        ['type', (entry) => entry.semantic_type],
        ['nullability / missing behavior', (entry) => entry.nullability_missing_behavior],
        ['provenance expectations', (entry) => entry.provenance_expectations],
        ['downstream consumers', (entry) => entry.downstream_consumers.join(', ')],
        ['recommendation', (entry) => entry.consumption_recommendation],
        ['status', (entry) => entry.status],
        ['notes/open questions', (entry) => entry.notes_open_questions.join('; ')],
      ];

  const header = `| ${columns.map(([label]) => escapeMarkdown(label)).join(' | ')} |`;
  const divider = `| ${columns.map(() => '---').join(' | ')} |`;
  const rows = entries.map((entry) => {
    const cells = columns.map(([, getter]) => escapeMarkdown(getter(entry)));
    return `| ${cells.join(' | ')} |`;
  });

  return [header, divider, ...rows].join('\n');
}

function statusCounts(entries) {
  return entries.reduce((counts, entry) => {
    counts[entry.status] = (counts[entry.status] ?? 0) + 1;
    return counts;
  }, {});
}

function generatedMarkdown(registry, entries, registryPath) {
  const counts = statusCounts(registry.entries);
  const countText = [...ALLOWED_STATUSES]
    .map((status) => `${status}: ${counts[status] ?? 0}`)
    .join(', ');

  return `# Projection Input Semantics Generated View\n\nGenerated from \`${registryPath}\`.\n\n> Inspection only: this generated document does not create ingestion, scoring, or downstream wiring. Candidate and needs_verification entries are not claims of complete source-backed coverage.\n\n- registry: \`${registry.registry_name}\`\n- version: \`${registry.version}\`\n- total entries: ${registry.entries.length}\n- status counts: ${countText}\n\n${markdownTable(entries)}\n`;
}

function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    if (process.argv.includes('--definitions')) {
      console.log(serialize(refusal('invalid_request', error.message)));
      process.exitCode = 1;
      return;
    }
    fail(error.message);
    printUsage();
    return;
  }

  if (options.help) {
    printUsage();
    return;
  }

  let registry;
  let resolvedPath;
  try {
    ({ registry, resolvedPath } = loadRegistry(options.registry));
  } catch (error) {
    if (options.definitions) {
      console.log(serialize(refusal('invalid_registry', error.message)));
      process.exitCode = 1;
      return;
    }
    fail(error.message);
    return;
  }

  if (options.definitions) {
    try {
      const context = loadInspection(registry, ROOT);
      const result = {
        list: () => catalog(context),
        get: () => lookup(context, options.id),
        compare: () => compare(context, options.left, options.right),
        coverage: () => inspectCoverage(context, options.artifact),
      }[options.definitions]();
      if (options.write || options['check-generated']) {
        for (const [relative, content] of [
          [GENERATED_JSON, serialize(catalog(context))],
          [GENERATED_MARKDOWN, inspectionMarkdown(context)],
        ]) {
          const destination = path.join(ROOT, relative);
          if (options.write) fs.writeFileSync(destination, content);
          else if (!fs.existsSync(destination) || fs.readFileSync(destination, 'utf8') !== content) {
            throw new Error(`generated inspection view is stale: ${relative}`);
          }
        }
      }
      console.log(serialize(result));
      if (['not_indexed', 'selection_required'].includes(result.status)) process.exitCode = 2;
    } catch (error) {
      console.log(serialize(refusal('inspection_blocked', error.message)));
      process.exitCode = 1;
    }
    return;
  }

  const filteredEntries = applyFilters(registry.entries, options);
  const counts = statusCounts(registry.entries);

  console.log(`# ${registry.registry_name} v${registry.version}`);
  console.log(`registry path: ${resolvedPath}`);
  console.log(`scope: ${registry.scope_boundary}`);
  console.log(`total entries: ${registry.entries.length}`);
  console.log(`status counts: ${[...ALLOWED_STATUSES].map((status) => `${status}=${counts[status] ?? 0}`).join(', ')}`);
  console.log(`matching entries: ${filteredEntries.length}`);
  console.log('');
  console.log(markdownTable(filteredEntries, { compact: true }));

  if (options.write) {
    const outputPath = path.resolve(process.cwd(), options.output);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, generatedMarkdown(registry, registry.entries, options.registry));
    console.log('');
    console.log(`wrote generated markdown: ${outputPath}`);
  }
}

main();
