#!/usr/bin/env node
/**
 * Thin bridge to the canonical rb_contact_evasion_observations_v0 evaluator
 * (TIBER-Data #234, Slice B).
 *
 * This file contains NO football semantics, no metric knowledge, no reason-code
 * knowledge. Slice A's contract is the single semantic authority; this bridge
 * only authenticates the compiled module, executes it, and passes the
 * evaluator's own report out.
 *
 * Usage:
 *   node scripts/rb_contact_evasion_contract_bridge.mjs constants <module> <sha256>
 *   node scripts/rb_contact_evasion_contract_bridge.mjs evaluate  <module> <sha256> < artifact.json
 *
 * Lifecycle binding. The gate compiles the reviewed source into a private
 * module and passes this bridge the module path and the sha256 it computed of
 * those exact bytes. This bridge reads the module **once**, hashes it, and
 * refuses to run on any mismatch. It then executes those already-read,
 * in-memory bytes through a module-customization hook -- it does NOT reopen the
 * path -- so the bytes executed are provably the bytes authenticated. There is
 * no window in which the file could be swapped between authentication and
 * execution, because the file is never opened a second time. `zod`, the one
 * runtime dependency, is resolved against the module's original directory.
 *
 * Output contract. On success the bridge prints EXACTLY ONE JSON object on
 * stdout and exits 0. Every failure prints exactly one `{ok:false,error,detail}`
 * object and exits non-zero. All diagnostics go to stderr. The envelopes are
 * mutually exclusive and exact:
 *   constants success: {ok:true, artifact_id, schema_version}
 *   evaluate  success: {ok:true, report}
 *   failure          : {ok:false, error, detail}
 */

import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire, register } from 'node:module';
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
if (!/^[0-9a-f]{64}$/.test(expectedDigest)) {
  fail('usage', 'the expected digest must be 64 lowercase hex characters');
}

// --- Authenticate the module: read once, hash, compare. -----------------------
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
    `the module hashes to ${actualDigest}, not the ${expectedDigest} the gate built; refusing to execute it`,
  );
}

// The exact authenticated bytes, kept in memory. Execution uses THESE, never a
// re-read of the path.
const authenticatedSource = moduleBytes.toString('utf8');

// Resolve `zod` against the module's original directory (its node_modules).
let zodUrl;
try {
  const require = createRequire(pathToFileURL(modulePath));
  zodUrl = pathToFileURL(require.resolve('zod')).href;
} catch (error) {
  fail('zod_unresolvable', `could not resolve the zod runtime dependency: ${error?.message ?? error}`);
}

// --- Execute the authenticated bytes in-memory via a loader hook. -------------
// The hook returns the in-memory authenticated source for the sentinel URL, and
// maps the module's single bare import (`zod`) to its resolved location. The
// entry module is never opened from the filesystem, so there is no reopen to
// race against.
const HOOKS = `
let SOURCE = null, ZOD_URL = null;
export async function initialize(data) { SOURCE = data.source; ZOD_URL = data.zodUrl; }
export async function resolve(specifier, context, next) {
  if (specifier === 'rbce-authenticated:evaluator') {
    return { url: 'rbce-authenticated:evaluator', shortCircuit: true };
  }
  if (specifier === 'zod') return { url: ZOD_URL, shortCircuit: true };
  return next(specifier, context);
}
export async function load(url, context, next) {
  if (url === 'rbce-authenticated:evaluator') {
    return { format: 'module', source: SOURCE, shortCircuit: true };
  }
  return next(url, context);
}`;

let contract;
try {
  register(`data:text/javascript,${encodeURIComponent(HOOKS)}`, import.meta.url, {
    data: { source: authenticatedSource, zodUrl },
  });
  contract = await import('rbce-authenticated:evaluator');
} catch (error) {
  fail('compiled_module_unloadable', `could not execute the authenticated module: ${error?.message ?? error}`);
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
process.exit(0);
