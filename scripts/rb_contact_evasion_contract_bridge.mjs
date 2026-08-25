#!/usr/bin/env node
/**
 * Thin bridge to the canonical rb_contact_evasion_observations_v0 evaluator
 * (TIBER-Data #234, Slice B).
 *
 * This file deliberately contains NO football semantics, no metric knowledge,
 * no reason-code knowledge, and no filesystem traversal. Slice A's compiled
 * public contract is the single semantic authority; this bridge only moves
 * bytes in and the evaluator's own report out, so a Python-facing gate can
 * delegate semantic judgment without re-implementing any rule.
 *
 * Usage:
 *   node scripts/rb_contact_evasion_contract_bridge.mjs constants
 *   node scripts/rb_contact_evasion_contract_bridge.mjs evaluate  < artifact.json
 *
 * `constants` prints the pinned contract identity so a caller can prove its own
 * pins still agree with the contract. `evaluate` reads the artifact bytes from
 * stdin -- never from a path -- so the caller's already-verified bytes are the
 * exact bytes judged, leaving no window between digest verification and
 * semantic evaluation.
 *
 * Requires `npm run build`; the compiled contract under dist/ is imported.
 * Output is always exactly one JSON line on stdout.
 */

import { readFileSync } from 'node:fs';
import process from 'node:process';

function emit(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

function fail(error, detail) {
  emit({ ok: false, error, detail });
  process.exit(3);
}

const mode = process.argv[2];
if (mode !== 'constants' && mode !== 'evaluate') {
  fail('usage', 'expected exactly one mode argument: "constants" or "evaluate"');
}

let contract;
try {
  contract = await import('../dist/src/index.js');
} catch (error) {
  fail(
    'compiled_contract_unavailable',
    `could not import the compiled contract from dist/src/index.js (run "npm run build"): ${error?.message ?? error}`,
  );
}

const {
  RB_CONTACT_EVASION_ARTIFACT_ID,
  RB_CONTACT_EVASION_SCHEMA_VERSION,
  evaluateRbContactEvasionObservationsV0,
} = contract;

if (
  typeof RB_CONTACT_EVASION_ARTIFACT_ID !== 'string' ||
  typeof RB_CONTACT_EVASION_SCHEMA_VERSION !== 'string' ||
  typeof evaluateRbContactEvasionObservationsV0 !== 'function'
) {
  fail('contract_surface_missing', 'the compiled contract does not export the expected public surface');
}

if (mode === 'constants') {
  emit({
    ok: true,
    artifact_id: RB_CONTACT_EVASION_ARTIFACT_ID,
    schema_version: RB_CONTACT_EVASION_SCHEMA_VERSION,
  });
  process.exit(0);
}

let raw;
try {
  raw = readFileSync(0);
} catch (error) {
  fail('stdin_unreadable', `could not read artifact bytes from stdin: ${error?.message ?? error}`);
}

let artifact;
try {
  artifact = JSON.parse(raw.toString('utf8'));
} catch (error) {
  fail('artifact_json_malformed', `the bytes on stdin are not valid JSON: ${error?.message ?? error}`);
}

let report;
try {
  report = evaluateRbContactEvasionObservationsV0(artifact);
} catch (error) {
  fail('evaluator_threw', `the canonical evaluator threw: ${error?.message ?? error}`);
}

emit({ ok: true, report });
