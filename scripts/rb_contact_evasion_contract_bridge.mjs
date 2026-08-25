#!/usr/bin/env node
/**
 * Thin bridge to the canonical rb_contact_evasion_observations_v0 evaluator
 * (TIBER-Data #234, Slice B).
 *
 * This file deliberately contains NO football semantics, no metric knowledge,
 * no reason-code knowledge, and no filesystem traversal beyond reading the one
 * module it is told to load. Slice A's contract is the single semantic
 * authority; this bridge only moves bytes in and the evaluator's own report
 * out, so a Python-facing gate can delegate semantic judgment without
 * re-implementing any rule.
 *
 * Usage:
 *   node scripts/rb_contact_evasion_contract_bridge.mjs constants <module> <sha256>
 *   node scripts/rb_contact_evasion_contract_bridge.mjs evaluate  <module> <sha256> < artifact.json
 *
 * The module path is supplied by the caller and is NEVER `dist/`. The gate
 * compiles the reviewed TypeScript source itself and passes the path of what it
 * just built, together with the sha256 it computed of those exact bytes. This
 * bridge re-hashes the file and refuses to import it on any mismatch, so a
 * module swapped between build and import cannot be executed. Evaluator
 * identity therefore rests on the build, never on what the module says about
 * itself.
 *
 * `constants` returns the contract identity the module reports -- used only as
 * an agreement check against the gate's code pins, never as proof of identity.
 * `evaluate` reads the artifact bytes from stdin -- never from a path -- so the
 * caller's already-verified bytes are the exact bytes judged, leaving no window
 * between digest verification and semantic evaluation.
 *
 * Output is always exactly one JSON line on stdout.
 */

import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

function emit(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

function fail(error, detail) {
  emit({ ok: false, error, detail });
  process.exit(3);
}

const [, , mode, modulePath, expectedDigest] = process.argv;

if (mode !== 'constants' && mode !== 'evaluate') {
  fail('usage', 'first argument must be "constants" or "evaluate"');
}
if (!modulePath || !expectedDigest) {
  fail('usage', 'a compiled module path and its expected sha256 are both required');
}

let moduleBytes;
try {
  moduleBytes = readFileSync(modulePath);
} catch (error) {
  fail('compiled_module_unreadable', `could not read ${modulePath}: ${error?.message ?? error}`);
}

const actualDigest = createHash('sha256').update(moduleBytes).digest('hex');
if (actualDigest !== expectedDigest) {
  fail(
    'compiled_module_tampered',
    `the module to import hashes to ${actualDigest}, not the ${expectedDigest} the gate built; refusing to execute it`,
  );
}

let contract;
try {
  contract = await import(pathToFileURL(modulePath).href);
} catch (error) {
  fail('compiled_module_unloadable', `could not import ${modulePath}: ${error?.message ?? error}`);
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
  fail(
    'contract_surface_missing',
    'the compiled contract does not export the expected public surface',
  );
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
