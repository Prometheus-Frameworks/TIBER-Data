#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const DEFAULT_ARTIFACT = 'data/processed/research/goblin_signal_candidates_2025.source_backed.json';
const ALLOWED_FILTERS = new Set(['artifact', 'team', 'position', 'player', 'flag', 'week', 'limit']);

function printUsage() {
  console.log(`Usage: node scripts/inspect_goblin_room.mjs [filters]\n\nFilters:\n  --artifact <path>   Artifact JSON path (default: ${DEFAULT_ARTIFACT})\n  --team <abbr>       Team exact match after uppercasing\n  --position <pos>    Position exact match after uppercasing\n  --player <name>     Case-insensitive player-name substring match\n  --flag <flag>       Match legitimate_indicator_flags or gross_output_flags\n  --week <number>     Week exact numeric match\n  --limit <number>    Maximum matching rows to print\n\nExamples:\n  node scripts/inspect_goblin_room.mjs --team KC --position WR\n  node scripts/inspect_goblin_room.mjs --player "Ladd McConkey"\n  node scripts/inspect_goblin_room.mjs --flag air_yards_without_output --limit 5`);
}

function fail(message) {
  console.error(`Error: ${message}`);
  process.exitCode = 1;
}

function parseArgs(argv) {
  const options = { artifact: DEFAULT_ARTIFACT };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === '--help' || arg === '-h') {
      options.help = true;
      continue;
    }

    if (!arg.startsWith('--')) {
      throw new Error(`unexpected positional argument: ${arg}`);
    }

    const key = arg.slice(2);
    if (!ALLOWED_FILTERS.has(key)) {
      throw new Error(`unknown option: ${arg}`);
    }

    const value = argv[index + 1];
    if (value === undefined || value.startsWith('--')) {
      throw new Error(`missing value for ${arg}`);
    }

    options[key] = value;
    index += 1;
  }

  if (options.team) {
    options.team = options.team.toUpperCase();
  }

  if (options.position) {
    options.position = options.position.toUpperCase();
  }

  if (options.player) {
    options.player = options.player.toLowerCase();
  }

  if (options.week !== undefined) {
    const week = Number(options.week);
    if (!Number.isInteger(week)) {
      throw new Error('--week must be an integer');
    }
    options.week = week;
  }

  if (options.limit !== undefined) {
    const limit = Number(options.limit);
    if (!Number.isInteger(limit) || limit < 0) {
      throw new Error('--limit must be a non-negative integer');
    }
    options.limit = limit;
  }

  return options;
}

function loadArtifact(artifactPath) {
  const resolvedPath = path.resolve(process.cwd(), artifactPath);

  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`artifact file is missing: ${artifactPath}`);
  }

  let payload;
  try {
    payload = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'));
  } catch (error) {
    throw new Error(`artifact JSON is invalid: ${artifactPath} (${error.message})`);
  }

  if (!Array.isArray(payload.records)) {
    throw new Error('artifact payload does not contain a records array');
  }

  return { payload, resolvedPath };
}

function hasFlag(record, flag) {
  const legitimateFlags = Array.isArray(record.legitimate_indicator_flags)
    ? record.legitimate_indicator_flags
    : [];
  const grossFlags = Array.isArray(record.gross_output_flags) ? record.gross_output_flags : [];

  return legitimateFlags.includes(flag) || grossFlags.includes(flag);
}

function matchesFilters(record, options) {
  if (options.team && String(record.team ?? '').toUpperCase() !== options.team) {
    return false;
  }

  if (options.position && String(record.position ?? '').toUpperCase() !== options.position) {
    return false;
  }

  if (options.player && !String(record.player_name ?? '').toLowerCase().includes(options.player)) {
    return false;
  }

  if (options.flag && !hasFlag(record, options.flag)) {
    return false;
  }

  if (options.week !== undefined && Number(record.week) !== options.week) {
    return false;
  }

  return true;
}

function formatFilters(options) {
  const filters = [];
  for (const key of ['team', 'position', 'player', 'flag', 'week', 'limit']) {
    if (options[key] !== undefined) {
      filters.push(`${key}=${options[key]}`);
    }
  }

  return filters.length > 0 ? filters.join(', ') : 'none';
}

function formatRows(records) {
  return records.map((record) => {
    const usage = record.usage_snapshot ?? {};

    return {
      week: record.week,
      player: record.player_name,
      team: record.team,
      pos: record.position,
      ppr: record.ppr_points,
      flags: Array.isArray(record.legitimate_indicator_flags)
        ? record.legitimate_indicator_flags.join(', ')
        : '',
      gross: Array.isArray(record.gross_output_flags) ? record.gross_output_flags.join(', ') : '',
      targets: usage.targets,
      target_share: usage.target_share,
      air_yards: usage.air_yards,
      air_yards_share: usage.air_yards_share,
      rush: usage.rushing_attempts,
    };
  });
}

function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    fail(error.message);
    printUsage();
    return;
  }

  if (options.help) {
    printUsage();
    return;
  }

  let payload;
  let resolvedPath;
  try {
    ({ payload, resolvedPath } = loadArtifact(options.artifact));
  } catch (error) {
    fail(error.message);
    return;
  }

  const matchingRecords = payload.records.filter((record) => matchesFilters(record, options));
  const limitedRecords = options.limit === undefined ? matchingRecords : matchingRecords.slice(0, options.limit);

  console.log(`artifact path: ${resolvedPath}`);
  console.log(`total records: ${payload.records.length}`);
  console.log(`matching records: ${matchingRecords.length}`);
  console.log(`filters applied: ${formatFilters(options)}`);

  if (matchingRecords.length === 0) {
    console.log('No matching GOBLIN candidate rows found.');
    return;
  }

  console.table(formatRows(limitedRecords));
}

main();
