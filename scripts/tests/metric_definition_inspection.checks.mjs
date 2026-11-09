import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import {
  catalog, compare, digest, inspectCoverage, inspectionMarkdown, loadInspection,
  lookup, serialize, sha256, validateInspection,
} from '../lib/metric_definition_inspection.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const REGISTRY_PATH = 'data/semantics/projection_input_semantics.json';
const registry = JSON.parse(fs.readFileSync(path.join(ROOT, REGISTRY_PATH), 'utf8'));
const context = loadInspection(registry, ROOT);
const ID = {
  route: 'inspection.route_share.sum_player_routes.v0',
  alias: 'inspection.route_participation.gold_compatibility_alias.v0',
  participation: 'inspection.route_participation.team_dropbacks.proposed.v0',
  goldTargets: 'inspection.target_share.gold_team_targets.v0',
  weeklyTargets: 'inspection.target_share.weekly_passthrough.v0',
  tprr: 'inspection.targets_per_route.actual_routes.v0',
  proxy: 'inspection.pass_play_participation.eligible_pass_plays.v0',
};
const clone = () => structuredClone(registry);
const cli = (...args) => spawnSync(process.execPath,
  ['scripts/inspect_projection_input_semantics.mjs', ...args], { cwd: ROOT, encoding: 'utf8' });

function syntheticRepository(run, records = [{ season: 2000, week: 1,
  source: 'offline_fixture:synthetic_test_only', routes_run: 0, route_participation: null,
  snap_share: 'invalid', target_share: 1.2 }]) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'metric-inspection-'));
  try {
    const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
    git('init');
    git('config', 'user.name', 'Synthetic Test');
    git('config', 'user.email', 'synthetic@example.invalid');
    fs.writeFileSync(path.join(root, 'source.py'), 'def synthetic_only():\n    pass\n');
    fs.writeFileSync(path.join(root, 'fixture.json'), serialize(records));
    git('add', '.');
    git('commit', '-m', 'Synthetic inspection boundary test');
    const commit = git('rev-parse', 'HEAD');
    const pin = (relative, symbol = null) => ({ path: relative, commit, symbol,
      sha256: sha256(fs.readFileSync(path.join(root, relative))) });
    const r = clone();
    r.definition_inspection.definitions.forEach((definition) => {
      definition.source_bindings = [pin('source.py', 'synthetic_only')];
    });
    r.definition_inspection.coverage_artifacts = [{
      ...r.definition_inspection.coverage_artifacts[1], binding: pin('fixture.json'),
    }];
    run({ root, r, pin });
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
}

test('legacy entry semantics are unchanged and field links add no duplicate names', () => {
  const old = JSON.parse(execFileSync('git', ['show',
    '35fc692b67d2e218b3033e7e30688e03c367de58:' + REGISTRY_PATH], { cwd: ROOT, encoding: 'utf8' }));
  const stripped = registry.entries.map(({ definition_ids, ...entry }) => entry);
  assert.deepEqual(stripped, old.entries);
  assert.equal(new Set(registry.entries.map((entry) => entry.field_name)).size, 37);
});

test('legacy viewer retains opportunity filters and validation', () => {
  const result = cli('--group', 'opportunity');
  assert.equal(result.status, 0);
  assert.match(result.stdout, /total entries: 37/);
  assert.match(result.stdout, /matching entries: 8/);
  assert.equal(cli('--status', 'needs_verification').status, 0);
  assert.equal(cli('--consumer', 'Point-prediction-model').status, 0);
});

test('exact lookup returns immutable sources and no player measurement', () => {
  const result = lookup(context, ID.route);
  assert.equal(result.status, 'definition');
  assert.equal(result.consumer_authorized, false);
  assert.equal(result.canonical_approval, 'not_granted');
  assert.equal(result.definition.observation_evidence, 'not_assessed');
  assert.equal(result.definition.denominator, 'sum_player_routes_in_input_team_week');
  assert.equal(Object.hasOwn(result, 'value'), false);
  assert.equal(Object.hasOwn(result.definition, 'value'), false);
  assert.match(result.definition.sources[0].url, /\/blob\/[a-f0-9]{40}\//);
  assert.equal(result.definition.definition_sha256, digest(context.config.definitions[2]));
});

test('families and declared aliases require an exact selection without defaults', () => {
  for (const query of ['route %', 'route_participation', 'target_share', 'TPRR']) {
    const result = lookup(context, query);
    assert.equal(result.status, 'selection_required');
    assert.equal(Object.hasOwn(result, 'definition'), false);
    const command = cli('--definitions', 'get', '--id', query, '--json');
    assert.equal(command.status, 2);
    assert.equal(JSON.parse(command.stdout).consumer_authorized, false);
  }
  assert.equal(lookup(context, 'route_participation').matches.length, 2);
});

test('unknown concepts stay unknown, including object-property names', () => {
  for (const key of ['elusiveness_score', '__proto__', 'constructor']) {
    assert.deepEqual(lookup(context, key).matches, []);
    assert.equal(lookup(context, key).status, 'not_indexed');
  }
  assert.equal(cli('--definitions', 'get', '--id', 'unknown').status, 2);
});

test('compatibility mapping remains explicit and cannot inherit dropbacks', () => {
  const alias = lookup(context, ID.alias).definition;
  assert.equal(alias.alias_of, ID.route);
  assert.equal(alias.denominator, lookup(context, ID.route).definition.denominator);
  assert.equal(compare(context, ID.alias, ID.participation).compatibility, 'incompatible');
  assert.ok(compare(context, ID.route, ID.participation).differing_dimensions.includes('denominator'));
});

test('upstream target share does not inherit the gold formula', () => {
  const definition = lookup(context, ID.weeklyTargets).definition;
  assert.equal(definition.formula, null);
  assert.equal(definition.numerator, null);
  assert.equal(definition.denominator, null);
  assert.equal(compare(context, ID.goldTargets, ID.weeklyTargets).compatibility, 'unresolved');
});

test('same ID proves only definition identity; incomplete aliases do not certify compatibility', () => {
  const result = compare(context, ID.tprr, ID.tprr);
  assert.equal(result.compatibility, 'same_definition');
  assert.equal(result.observation_comparability, 'not_assessed');
  assert.equal(result.consumer_authorized, false);
  assert.equal(compare(context, ID.route, ID.alias).compatibility, 'unresolved');
  assert.equal(compare(context, 'route_share', ID.alias).status, 'not_indexed');
});

test('proxy and TPRR retain separate numerator and denominator identities', () => {
  assert.equal(lookup(context, ID.tprr).definition.denominator, 'actual_player_routes_run');
  assert.equal(lookup(context, ID.proxy).definition.numerator, 'on_field_eligible_pass_plays');
  assert.equal(compare(context, ID.tprr, ID.proxy).compatibility, 'incompatible');
});

test('legacy zero behavior and unselected aggregation remain visible', () => {
  assert.match(lookup(context, ID.goldTargets).definition.missing_behavior, /null, zero or negative/);
  for (const definition of catalog(context).definitions) {
    assert.equal(definition.aggregation.status, 'not_selected');
    assert.equal(definition.event_eligibility.status, 'unresolved');
    assert.equal(definition.canonical_approval, 'not_granted');
  }
});

test('coverage receipt independently reproduces bounded missing routes and unresolved targets', () => {
  const result = inspectCoverage(context, 'weekly_usage_2025.source_backed');
  assert.equal(result.rows, 6326);
  for (const field of ['routes_run', 'route_participation', 'snap_share']) {
    assert.equal(result.columns[field].non_null, 0);
    assert.equal(result.columns[field].missing, 6326);
    assert.equal(result.columns[field].measurement_support, 'unavailable');
  }
  assert.equal(result.columns.target_share.non_null, 6326);
  assert.equal(result.columns.target_share.definition_binding, 'unresolved_formula');
  assert.equal(result.columns.target_share.measurement_support, 'unqualified_values');
  assert.equal(result.source_admission, 'not_assessed');
  assert.equal(result.scope.season_type_coverage, 'unknown_or_partial');
  assert.deepEqual(result.scope.weeks, Array.from({ length: 22 }, (_, i) => i + 1));
  assert.equal(result.clocks.source_snapshot_at, null);
  assert.equal(result.population_completeness, 'unknown');
  assert.equal(result.consumer_authorized, false);
});

test('populated promoted-path rows remain fixtures', () => {
  const result = inspectCoverage(context, 'weekly_usage.offline_fixture');
  assert.equal(result.rows, 6);
  assert.equal(result.columns.routes_run.non_null, 6);
  assert.equal(result.columns.routes_run.measurement_support, 'fixture_only');
  assert.equal(result.source_admission, 'fixture_only');
  assert.ok(result.source_labels.every((label) => label.startsWith('offline_fixture:')));
  assert.equal(inspectCoverage(context, '/arbitrary/input.json').status, 'not_indexed');
});

test('synthetic receipt separates zero, null, invalid numeric and out-of-range values', () => {
  syntheticRepository(({ root, r }) => {
    const result = inspectCoverage(loadInspection(r, root), 'weekly_usage.offline_fixture');
    assert.equal(result.columns.routes_run.zero_value_count, 1);
    assert.equal(result.columns.routes_run.missing, 0);
    assert.equal(result.columns.route_participation.missing, 1);
    assert.equal(result.columns.snap_share.invalid_numeric_or_domain, 1);
    assert.equal(result.columns.target_share.invalid_numeric_or_domain, 1);
    assert.equal(result.source_admission, 'fixture_only');
  });
});

test('fixture-to-source promotion and lost fixture labels are rejected', () => {
  syntheticRepository(({ root, r }) => {
    r.definition_inspection.coverage_artifacts[0].source_kind = 'repository_source_backed';
    assert.throws(() => inspectCoverage(loadInspection(r, root), 'weekly_usage.offline_fixture'),
      /fixture rows cannot be classified as source-backed/);
  });
  syntheticRepository(({ root, r }) => {
    assert.throws(() => inspectCoverage(loadInspection(r, root), 'weekly_usage.offline_fixture'),
      /lost its explicit row-level fixture labels/);
  }, [{ source: 'unproven', season: 2000, week: 1 }]);
});

test('source drift, stale hash, unavailable pin and wrong symbol fail closed', () => {
  syntheticRepository(({ root, r }) => {
    fs.appendFileSync(path.join(root, 'source.py'), '# changed\n');
    assert.throws(() => loadInspection(r, root), /source drift requires review/);
  });
  syntheticRepository(({ root, r }) => {
    r.definition_inspection.definitions[0].source_bindings[0].sha256 = '0'.repeat(64);
    assert.throws(() => loadInspection(r, root), /pinned source digest mismatch/);
  });
  syntheticRepository(({ root, r }) => {
    r.definition_inspection.definitions[0].source_bindings[0].commit = 'a'.repeat(40);
    assert.throws(() => loadInspection(r, root), /unavailable source pin/);
  });
  syntheticRepository(({ root, r }) => {
    r.definition_inspection.definitions[0].source_bindings[0].symbol = 'nonexistent';
    assert.throws(() => loadInspection(r, root), /source symbol is missing/);
  });
});

test('schema rejects semantic self-promotion, missing metadata and conflicting alias components', () => {
  const mutations = [
    (r) => { r.definition_inspection.consumer_authorized = true; },
    (r) => { r.definition_inspection.definitions[0].canonical_approval = 'approved'; },
    (r) => { r.definition_inspection.definitions[0].unit = 'percentage'; },
    (r) => { delete r.definition_inspection.definitions[0].grain; },
    (r) => { r.definition_inspection.definitions[0].denominator = null; },
    (r) => { r.definition_inspection.definitions[1].id = ID.goldTargets; },
    (r) => { r.definition_inspection.definitions[3].denominator = 'eligible_team_dropbacks'; },
    (r) => { r.definition_inspection.definitions[0].source_bindings[0].path = '../outside'; },
    (r) => { r.entries[7].definition_ids = [ID.goldTargets]; },
  ];
  for (const mutate of mutations) {
    const r = clone(); mutate(r);
    assert.throws(() => validateInspection(r));
  }
});

test('generated views reproduce their sole registry source deterministically', () => {
  assert.equal(fs.readFileSync(path.join(ROOT, 'data/semantics/metric_definitions.generated.json'), 'utf8'),
    serialize(catalog(context)));
  assert.equal(fs.readFileSync(path.join(ROOT, 'docs/metric-definitions.generated.md'), 'utf8'),
    inspectionMarkdown(context));
  assert.equal(cli('--definitions', 'list', '--check-generated').status, 0);
});

test('changed descriptors make the retained generated views fail their drift check', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'metric-registry-drift-'));
  try {
    const r = clone();
    r.definition_inspection.definitions[0].caveats.push('Synthetic metadata drift test only.');
    const registryPath = path.join(root, 'registry.json');
    fs.writeFileSync(registryPath, serialize(r));
    const result = cli('--registry', registryPath, '--definitions', 'list', '--check-generated');
    assert.equal(result.status, 1);
    assert.match(JSON.parse(result.stdout).error, /generated inspection view is stale/);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test('CLI invalid combinations produce explicit machine-readable failure', () => {
  for (const args of [
    ['get'], ['compare', '--left', ID.route], ['coverage'],
    ['list', '--status', 'candidate'], ['list', '--write', '--check-generated'],
    ['get', '--id', ID.route, '--write'], ['list', '--artifact', 'extra'],
  ]) {
    const result = cli('--definitions', ...args);
    assert.equal(result.status, 1);
    assert.equal(JSON.parse(result.stdout).consumer_authorized, false);
  }
  assert.equal(cli('--definitions', 'coverage', '--artifact', 'unknown').status, 2);
});
