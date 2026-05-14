#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const DEFAULT_FIXTURE = 'data/projection-input-fixtures/weekly_projection_input_fixture_2026_w01.json';
const DEFAULT_OUTPUT = 'docs/projection-input-fixtures.generated.md';
const DEFAULT_REGISTRY = 'data/semantics/projection_input_semantics.json';
const ALLOWED_OPTIONS = new Set(['fixture', 'registry', 'write', 'output']);
const TOP_LEVEL_REQUIRED_FIELDS = [
  'input_contract_version',
  'tiber_data_schema_version',
  'source_dataset_refs',
  'identity_ref',
  'league_context',
  'player_opportunities',
  'missing_fields',
  'adapter_warnings',
];
const PLAYER_REQUIRED_FIELDS = ['player_id', 'player_name', 'team', 'position', 'season', 'week'];
const REQUIRED_STRING_PLAYER_FIELDS = ['player_id', 'player_name', 'team', 'position'];
const ALLOWED_POSITIONS = new Set(['QB', 'RB', 'WR', 'TE']);
const IDENTITY_FIELD_NAMES = new Set(PLAYER_REQUIRED_FIELDS);
const ALLOWED_EXTRA_TOP_LEVEL_FIELDS = new Set(['fixture_scope', 'projection_context']);
const MISSING_FIELD_SEVERITIES = new Set(['info', 'warning', 'error']);

function printUsage() {
  console.log(`Usage: node scripts/inspect_projection_input_fixture.mjs [options]\n\nOptions:\n  --fixture <path>   Projection input fixture JSON path (default: ${DEFAULT_FIXTURE})\n  --registry <path>  Projection input semantics registry path (default: ${DEFAULT_REGISTRY})\n  --write            Write generated markdown summary\n  --output <path>    Generated markdown output path (default: ${DEFAULT_OUTPUT})\n  --help, -h         Show this help\n\nExamples:\n  node scripts/inspect_projection_input_fixture.mjs\n  node scripts/inspect_projection_input_fixture.mjs --write`);
}

function parseArgs(argv) {
  const options = { fixture: DEFAULT_FIXTURE, registry: DEFAULT_REGISTRY, output: DEFAULT_OUTPUT };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--help' || arg === '-h') {
      options.help = true;
      continue;
    }
    if (arg === '--write') {
      options.write = true;
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

  return options;
}

function loadJson(filePath, label) {
  const resolvedPath = path.resolve(process.cwd(), filePath);
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`${label} file is missing: ${filePath}`);
  }

  try {
    return { value: JSON.parse(fs.readFileSync(resolvedPath, 'utf8')), resolvedPath };
  } catch (error) {
    throw new Error(`${label} JSON is invalid: ${filePath} (${error.message})`);
  }
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function assertNonEmptyString(value, fieldPath, errors) {
  if (typeof value !== 'string' || value.trim() === '') {
    errors.push(`${fieldPath} must be a non-empty string`);
  }
}

function findNulls(value, fieldPath, errors) {
  if (value === null) {
    errors.push(`${fieldPath} must be omitted instead of null`);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => findNulls(item, `${fieldPath}[${index}]`, errors));
    return;
  }
  if (typeof value === 'object' && value !== null) {
    for (const [key, child] of Object.entries(value)) {
      findNulls(child, `${fieldPath}.${key}`, errors);
    }
  }
}

function assertPositiveNumber(value, fieldPath, errors) {
  if (!isFiniteNumber(value) || value <= 0) {
    errors.push(`${fieldPath} must be a positive finite number`);
  }
}

function assertNonNegativeNumber(value, fieldPath, errors) {
  if (!isFiniteNumber(value) || value < 0) {
    errors.push(`${fieldPath} must be a non-negative finite number`);
  }
}

function validateNumberRecord(value, fieldPath, errors, requiredKeys) {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    errors.push(`${fieldPath} must be an object`);
    return;
  }

  for (const key of requiredKeys) {
    if (!Object.hasOwn(value, key)) {
      errors.push(`${fieldPath}.${key} is required`);
      continue;
    }
    assertNonNegativeNumber(value[key], `${fieldPath}.${key}`, errors);
  }
}

function validateLeagueContext(leagueContext, fieldPath, errors) {
  assertPositiveNumber(leagueContext.teams, `${fieldPath}.teams`, errors);
  validateNumberRecord(leagueContext.starters, `${fieldPath}.starters`, errors, ['QB', 'RB', 'WR', 'TE']);

  if (leagueContext.starters && Object.hasOwn(leagueContext.starters, 'FLEX')) {
    assertNonNegativeNumber(leagueContext.starters.FLEX, `${fieldPath}.starters.FLEX`, errors);
  }
  if (Object.hasOwn(leagueContext, 'flex_allocation')) {
    validateNumberRecord(leagueContext.flex_allocation, `${fieldPath}.flex_allocation`, errors, ['RB', 'WR', 'TE']);
  }
  if (Object.hasOwn(leagueContext, 'replacement_buffer')) {
    validateNumberRecord(leagueContext.replacement_buffer, `${fieldPath}.replacement_buffer`, errors, ['QB', 'RB', 'WR', 'TE']);
  }
}

function registryFieldMap(registry) {
  if (!Array.isArray(registry.entries)) {
    throw new Error('registry.entries must be an array');
  }

  const fields = new Map();
  for (const entry of registry.entries) {
    if (typeof entry.field_name === 'string') {
      fields.set(entry.field_name, entry);
    }
  }
  return fields;
}

function validateFixture(fixture, registry) {
  const errors = [];
  const registryFields = registryFieldMap(registry);
  const allowedPlayerFields = new Set([...IDENTITY_FIELD_NAMES]);
  for (const [fieldName, entry] of registryFields.entries()) {
    if (entry.consumption_recommendation !== 'not_consumed_yet') {
      allowedPlayerFields.add(fieldName);
    }
  }

  for (const field of TOP_LEVEL_REQUIRED_FIELDS) {
    if (!Object.hasOwn(fixture, field)) {
      errors.push(`${field} is required`);
    }
  }

  for (const field of ['input_contract_version', 'tiber_data_schema_version']) {
    assertNonEmptyString(fixture[field], field, errors);
  }

  for (const key of Object.keys(fixture)) {
    if (!TOP_LEVEL_REQUIRED_FIELDS.includes(key) && !ALLOWED_EXTRA_TOP_LEVEL_FIELDS.has(key)) {
      errors.push(`${key} is not a governed top-level fixture field`);
    }
  }

  if (!Array.isArray(fixture.source_dataset_refs) || fixture.source_dataset_refs.length === 0) {
    errors.push('source_dataset_refs must be a non-empty array');
  }
  if (typeof fixture.identity_ref !== 'object' || fixture.identity_ref === null || Array.isArray(fixture.identity_ref)) {
    errors.push('identity_ref must be an object');
  }
  if (typeof fixture.league_context !== 'object' || fixture.league_context === null || Array.isArray(fixture.league_context)) {
    errors.push('league_context must be an object');
  } else {
    validateLeagueContext(fixture.league_context, 'league_context', errors);
  }
  if (!Array.isArray(fixture.player_opportunities) || fixture.player_opportunities.length === 0) {
    errors.push('player_opportunities must be a non-empty array');
  }
  if (!Array.isArray(fixture.missing_fields)) {
    errors.push('missing_fields must be an array');
  }
  if (!Array.isArray(fixture.adapter_warnings)) {
    errors.push('adapter_warnings must be an array');
  }

  findNulls(fixture, 'fixture', errors);

  for (const [index, player] of (fixture.player_opportunities ?? []).entries()) {
    const playerPath = `player_opportunities[${index}]`;
    if (typeof player !== 'object' || player === null || Array.isArray(player)) {
      errors.push(`${playerPath} must be an object`);
      continue;
    }

    for (const field of PLAYER_REQUIRED_FIELDS) {
      if (!Object.hasOwn(player, field)) {
        errors.push(`${playerPath}.${field} is required`);
      }
    }
    for (const field of REQUIRED_STRING_PLAYER_FIELDS) {
      assertNonEmptyString(player[field], `${playerPath}.${field}`, errors);
    }
    if (!ALLOWED_POSITIONS.has(player.position)) {
      errors.push(`${playerPath}.position must be one of: ${[...ALLOWED_POSITIONS].join(', ')}`);
    }
    for (const field of ['season', 'week']) {
      if (!Number.isInteger(player[field]) || player[field] <= 0) {
        errors.push(`${playerPath}.${field} must be a positive integer`);
      }
    }

    for (const [field, value] of Object.entries(player)) {
      const semanticEntry = registryFields.get(field);
      if (!allowedPlayerFields.has(field)) {
        errors.push(`${playerPath}.${field} is not supported for player_opportunities by the semantics registry`);
        continue;
      }
      if (!IDENTITY_FIELD_NAMES.has(field) && !isFiniteNumber(value)) {
        errors.push(`${playerPath}.${field} must be a finite number when present`);
      }
      if (semanticEntry?.consumption_recommendation === 'not_consumed_yet') {
        errors.push(`${playerPath}.${field} must not be included because it is marked not_consumed_yet`);
      }
    }
  }

  for (const [index, missing] of (fixture.missing_fields ?? []).entries()) {
    const missingPath = `missing_fields[${index}]`;
    if (typeof missing !== 'object' || missing === null || Array.isArray(missing)) {
      errors.push(`${missingPath} must be an object`);
      continue;
    }
    assertNonEmptyString(missing.field, `${missingPath}.field`, errors);
    assertNonEmptyString(missing.severity, `${missingPath}.severity`, errors);
    assertNonEmptyString(missing.reason, `${missingPath}.reason`, errors);
    if (Object.hasOwn(missing, 'player_id')) {
      assertNonEmptyString(missing.player_id, `${missingPath}.player_id`, errors);
    }
    if (Object.hasOwn(missing, 'impact')) {
      assertNonEmptyString(missing.impact, `${missingPath}.impact`, errors);
    }
    if (typeof missing.severity === 'string' && !MISSING_FIELD_SEVERITIES.has(missing.severity)) {
      errors.push(`${missingPath}.severity must be one of: ${[...MISSING_FIELD_SEVERITIES].join(', ')}`);
    }
    if (typeof missing.field === 'string' && !registryFields.has(missing.field)) {
      errors.push(`${missingPath}.field is not present in the semantics registry: ${missing.field}`);
    }
    if (Object.hasOwn(missing, 'field_name')) {
      errors.push(`${missingPath}.field_name is not adapter-compatible; use field`);
    }
    if (Object.hasOwn(missing, 'applies_to')) {
      errors.push(`${missingPath}.applies_to is not adapter-compatible; use player_id or impact`);
    }
  }

  if (errors.length > 0) {
    throw new Error(`fixture validation failed:\n- ${errors.join('\n- ')}`);
  }
}

function groupByPosition(players) {
  const counts = new Map();
  for (const player of players) {
    counts.set(player.position, (counts.get(player.position) ?? 0) + 1);
  }
  return [...counts.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function missingFieldCounts(missingFields) {
  const counts = new Map();
  for (const missing of missingFields) {
    const key = missing.field;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function playerNumericFields(player) {
  return Object.entries(player)
    .filter(([field, value]) => !IDENTITY_FIELD_NAMES.has(field) && isFiniteNumber(value))
    .map(([field]) => field)
    .sort();
}

function renderMarkdown(fixture, fixturePath) {
  const players = fixture.player_opportunities;
  const positionRows = groupByPosition(players)
    .map(([position, count]) => `| ${position} | ${count} |`)
    .join('\n');
  const playerRows = players
    .map((player) => `| ${player.player_name} | ${player.position} | ${player.team} | ${playerNumericFields(player).join(', ')} |`)
    .join('\n');
  const missingRows = missingFieldCounts(fixture.missing_fields)
    .map(([field, count]) => `| ${field} | ${count} |`)
    .join('\n');

  return `# Projection input fixture inspection\n\nGenerated from \`${fixturePath}\`.\n\n## Bundle\n\n- Contract: \`${fixture.input_contract_version}\`\n- TIBER-Data schema: \`${fixture.tiber_data_schema_version}\`\n- Player rows: ${players.length}\n- Fixture only: ${fixture.projection_context?.fixture_only === true ? 'yes' : 'no'}\n\n## Position counts\n\n| Position | Count |\n| --- | ---: |\n${positionRows}\n\n## Players\n\n| Player | Position | Team | Numeric opportunity/context fields present |\n| --- | --- | --- | --- |\n${playerRows}\n\n## Missing-field counts\n\n| Field | Count |\n| --- | ---: |\n${missingRows}\n`;
}

function printSummary(fixture, fixturePath) {
  console.log(`Projection input fixture: ${fixturePath}`);
  console.log(`Contract: ${fixture.input_contract_version}`);
  console.log(`TIBER-Data schema: ${fixture.tiber_data_schema_version}`);
  const projectionContext = fixture.projection_context;
  if (projectionContext) {
    console.log(`Projection context: ${projectionContext.league} ${projectionContext.season} W${projectionContext.week}`);
  }
  console.log(`League context: ${fixture.league_context.teams} teams, starters ${JSON.stringify(fixture.league_context.starters)}`);
  console.log(`Player rows: ${fixture.player_opportunities.length}`);
  console.log('\nPlayers:');
  for (const player of fixture.player_opportunities) {
    console.log(`- ${player.player_name} (${player.position}, ${player.team}): ${playerNumericFields(player).join(', ')}`);
  }
  console.log('\nPosition counts:');
  for (const [position, count] of groupByPosition(fixture.player_opportunities)) {
    console.log(`- ${position}: ${count}`);
  }
  console.log('\nMissing-field counts:');
  for (const [field, count] of missingFieldCounts(fixture.missing_fields)) {
    console.log(`- ${field}: ${count}`);
  }
  console.log(`\nAdapter warnings: ${fixture.adapter_warnings.length}`);
}

function main() {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (options.help) {
      printUsage();
      return;
    }

    const { value: fixture } = loadJson(options.fixture, 'fixture');
    const { value: registry } = loadJson(options.registry, 'registry');
    validateFixture(fixture, registry);
    printSummary(fixture, options.fixture);

    if (options.write) {
      const outputPath = path.resolve(process.cwd(), options.output);
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, renderMarkdown(fixture, options.fixture));
      console.log(`\nWrote ${options.output}`);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  }
}

main();
