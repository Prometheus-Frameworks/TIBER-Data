# rb_contact_evasion_observations_v0 — candidate bundle gate (Slice B)

TIBER-Data #234, Slice B. This document describes the deterministic, offline
validation entry point for **future** `rb_contact_evasion_observations_v0`
candidate artifacts, and how to run it.

It does not describe the contract. The contract, the metric dictionary, the
reason codes, the minimum-sample rule, the allowed combinations and the fixture
corpus are Slice A's, documented in
[`rb-contact-evasion-observations-v0.md`](./rb-contact-evasion-observations-v0.md).
Slice B changes none of them.

## Status

No admitted source exists for this lane, so **no candidate artifact exists**.
Nothing lives under `exports/candidates/rb_contact_evasion/` or
`exports/promoted/rb_contact_evasion/`, and this slice creates nothing there.
What exists is the boundary such an artifact would have to cross.

## Single semantic authority

Slice A's compiled TypeScript public evaluator is the only thing in this
repository allowed to judge whether an observation row is contract-valid.

```text
bundle bytes
    ↓  manifest gate            (Python, scripts/validate_rb_contact_evasion_bundle.py)
    ↓  committed JSON Schema    (schemas/rb_contact_evasion_observations_v0.schema.json)
    ↓  canonical evaluator      (src/contracts/v1/rbContactEvasionObservationsV0.ts, compiled)
verdict
```

The gate contains no football semantics: no mechanism, metric, denominator,
clock, cohort, rights or missingness rule appears in it, and a test asserts the
absence directly over the source text rather than in prose. Semantic judgment is
delegated over a deliberately thin bridge,
`scripts/rb_contact_evasion_contract_bridge.mjs`, which imports the compiled
contract and does nothing but pass bytes in and the evaluator's own report out.
The evaluator's machine-readable reason codes are reproduced **verbatim**: they
are not renamed, filtered, grouped or ranked, so a code seen in CI is the same
code Slice A's own tests pin.

The gate holds the bytes it verified and sends *those* to the evaluator on
stdin, never a path and never a re-serialisation. There is therefore no window
between digest verification and semantic evaluation in which the file could
change, and no opportunity for this gate's JSON writer to decide what the
evaluator sees.

### Why the gate is Python and the evaluator is not

The shape gate is the committed JSON Schema, applied with `jsonschema`, which is
already a declared dependency of this repository. The semantic gate is the
compiled TypeScript contract. Writing the gate in Python therefore adds no new
dependency to either side, and matches the repository's existing
`scripts/validate_*.py` precedent. Writing it in TypeScript instead would have
required adding a JSON Schema library to the npm dependency set purely to apply
a schema this repository already knows how to apply — a larger change to a
governance repository than the design saves.

The cost is one process boundary. It is deliberate: it is what keeps Slice A's
rules in exactly one place.

## Running it

```bash
# once, so the compiled contract exists
npm run build

# human-readable diagnostics; exit 0 pass, 1 fail
python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root>

# machine-readable result on stdout, for CI
python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json

# or write it to a file (which must be outside the bundle)
python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json-out result.json
```

Or, building and validating in one step:

```bash
npm run check:rb-contact-evasion-bundle -- <bundle-root>
```

Exit codes: `0` the bundle passed every stage, `1` the bundle failed the gate,
`2` the invocation itself was invalid.

The gate performs no network access and opens every path read-only. It never
writes into the bundle it is validating — `--json-out` pointing inside the
bundle is refused as a usage error.

## Bundle layout and manifest contract

A bundle is a plain directory containing `manifest.json` at its root and the
artifact files it declares:

```text
<bundle-root>/
  manifest.json
  observations/<something>.json
```

The manifest name is pinned in code and is not configurable: a caller able to
point the gate at a different manifest could point it at a friendlier one.

```json
{
  "manifest_version": "rb_contact_evasion_observations_bundle_manifest_v0.1.0",
  "artifact_id": "rb_contact_evasion_observations_v0",
  "schema_version": "rb_contact_evasion_observations_v0.4.0",
  "artifact_position": "candidate",
  "digest_algorithm": "sha256",
  "generated_at": "2026-08-25T00:00:00+00:00",
  "artifacts": [
    {
      "path": "observations/example.json",
      "size_bytes": 4144,
      "digest": "<64 lowercase hex characters>"
    }
  ]
}
```

Its shape gate is
[`schemas/rb_contact_evasion_observations_bundle_manifest_v0.schema.json`](../../schemas/rb_contact_evasion_observations_bundle_manifest_v0.schema.json).

### The manifest is integrity metadata, never authority

This is the property the whole design turns on, so it is enforced three ways
rather than asserted once.

- **`artifact_id`, `schema_version`, `manifest_version` and `digest_algorithm`
  are pinned in code**, in `scripts/validate_rb_contact_evasion_bundle.py`, not
  taken from the manifest. The manifest restates them for inspectability; a
  manifest that disagrees fails closed rather than redefining what is admitted.
  Those pins are themselves cross-checked against the canonical contract at run
  time, so Slice B cannot drift into validating against a version Slice A no
  longer defines.
- **The manifest schema is closed and carries no contract-semantic field.** It
  has no permissions, provenance, missingness, metric, cohort, rights, waiver,
  override, exemption, skip, score, ranking or validity field. A test asserts
  the admitted key set exactly, and separately asserts that a long list of
  weakening keys is refused — so widening the schema to admit one is caught
  here rather than becoming a way for a manifest to speak for a payload.
- **`artifact_position` must equal the payload's own, exactly.** A manifest
  cannot describe a candidate as a fixture to duck the rules a candidate faces,
  nor describe a fixture as a candidate to look governed. The payload's own
  declaration is what the contract layer judges, and promoted position still
  fails closed under Slice A's `PROMOTED_POSITION_REQUIRES_PROMOTION_GATE`.

## Stages

Every stage is fail-closed. A stage that *cannot* run is a failure, never a
skip: if the compiled contract is missing, the bundle does not pass, it fails
with `BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE`.

| # | Stage | What must hold |
|---|---|---|
| 1 | `manifest_read` | `manifest.json` exists at the root, is a regular file, is not a symlink, is within the size cap |
| 2 | `manifest_parse` | strict JSON: no duplicate keys, no `NaN`/`Infinity`, valid UTF-8 |
| 3 | `manifest_shape` | matches the committed manifest schema; carries no weakening field |
| 4 | `contract_identity` | declared identity equals the code pins, and the code pins equal the canonical contract's |
| 5 | `path_safety` | each declared path is relative, POSIX, normalized, contained, and a real regular file |
| 6 | `bundle_bijection` | declared files and present regular files are the same set, each declared once |
| 7 | `integrity` | byte size (from `stat`, before reading) then SHA-256 of the exact bytes |
| 8 | `payload_parse` | strict JSON — a matching digest never excuses malformed bytes |
| 9 | `payload_shape` | matches the committed `rb_contact_evasion_observations_v0` JSON Schema |
| 10 | `manifest_payload_agreement` | manifest and payload agree on `artifact_id`, `schema_version`, `artifact_position` |
| 11 | `semantic` | the canonical Slice A evaluator returns `valid: true` |

The order is part of the contract. Integrity is established before anything is
parsed, and parsing before any semantic claim, so a corrupted file is never
handed to a parser and a misshapen payload is never handed to the evaluator.

### Path safety, specifically

Rejected: absolute paths; drive-qualified paths; backslashes; `.`, `..` and
empty segments; trailing slashes; NUL bytes; anything resolving outside the
bundle root; and symlinks at **any** path component, not only the leaf — a
symlinked parent directory is as good an escape as a symlinked file, and a
digest computed through one describes bytes that do not live in the bundle.
Non-regular files (directories, FIFOs, devices) are rejected whether or not the
manifest declares them.

## Gate reason codes

Gate-owned codes are prefixed `BUNDLE_` so they can never collide with a Slice A
contract code. Anything without that prefix in a result came verbatim from the
canonical evaluator.

| Code | Meaning |
|---|---|
| `BUNDLE_ROOT_INVALID` | the bundle root is not a real directory |
| `BUNDLE_MANIFEST_UNREADABLE` | no manifest, not a regular file, a symlink, or oversized |
| `BUNDLE_MANIFEST_JSON_MALFORMED` | the manifest is not strict JSON |
| `BUNDLE_MANIFEST_DUPLICATE_KEY` | the manifest repeats an object key |
| `BUNDLE_MANIFEST_SHAPE_INVALID` | the manifest fails the committed manifest schema, or declares a weakening field |
| `BUNDLE_CONTRACT_IDENTITY_MISMATCH` | the manifest declares an identity other than the pinned one |
| `BUNDLE_CONTRACT_IDENTITY_DRIFT` | the gate's pins no longer match the canonical contract |
| `BUNDLE_DIGEST_ALGORITHM_UNSUPPORTED` | the declared algorithm is not admitted |
| `BUNDLE_DIGEST_VALUE_MALFORMED` | the declared digest is the wrong length for the algorithm |
| `BUNDLE_PATH_NOT_RELATIVE` | absolute or drive-qualified path |
| `BUNDLE_PATH_TRAVERSAL` | the path contains a `..` segment |
| `BUNDLE_PATH_NOT_NORMALIZED` | `.`, empty segment, backslash, trailing slash or NUL |
| `BUNDLE_PATH_ESCAPES_ROOT` | the path resolves outside the bundle root |
| `BUNDLE_PATH_NOT_REGULAR_FILE` | a symlink or non-regular entry, declared or merely present |
| `BUNDLE_ARTIFACT_MISSING` | declared but absent |
| `BUNDLE_UNDECLARED_FILE` | present but not declared |
| `BUNDLE_DUPLICATE_MANIFEST_ENTRY` | the same path is declared more than once |
| `BUNDLE_MANIFEST_DECLARES_ITSELF` | the manifest lists itself as bundle content |
| `BUNDLE_SIZE_MISMATCH` | the file's byte length is not what was declared |
| `BUNDLE_DIGEST_MISMATCH` | the file's bytes do not hash to the declared digest |
| `BUNDLE_ARTIFACT_TOO_LARGE` | the declared size is above the read cap |
| `BUNDLE_ARTIFACT_JSON_MALFORMED` | verified bytes that are not strict JSON |
| `BUNDLE_ARTIFACT_DUPLICATE_KEY` | the payload repeats an object key |
| `BUNDLE_ARTIFACT_SCHEMA_INVALID` | the payload fails the committed contract schema |
| `BUNDLE_MANIFEST_PAYLOAD_DISAGREEMENT` | manifest and payload disagree on identity or position |
| `BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE` | the canonical evaluator could not be reached |
| `BUNDLE_SEMANTIC_EVALUATOR_FAILED` | the canonical evaluator returned no readable verdict |

## Determinism

The machine-readable result contains no clock and no absolute path: entries are
sorted by bundle-relative path and failures by `(stage, path, reason_code,
detail)`. Two runs over the same bytes produce byte-identical JSON, and so do
two machines. This is asserted by test.

## What this slice does not do

It builds nothing, collects nothing, and admits no source. It creates no
candidate or promoted artifact, writes nothing under `exports/**`, implements no
Bucky assembler, adds no normalization, percentile, cohort, threshold, score or
"elite" authority, and changes no Data/FORGE ownership. `promoted` position
remains fail-closed under Slice A: this gate is not the #224 promotion gate and
does not claim to be one.

## Residual limits

- **The gate proves bytes, not truth.** A digest proves a file is the file the
  manifest names. It says nothing about whether the observation in it is real,
  and Slice A's own residual limits — producer declarations are consistency-
  checked but not verifiable, a declared clock origin can still be a lie,
  attribution presence is not correctness — are unchanged by this slice.
- **No admitted-source registry.** Slice A recorded that pinning source
  declarations against a registry of admitted sources was Slice B work. It is
  not implemented here: no source is admitted, so there is nothing to pin
  against, and inventing a registry would invent provenance. It remains open.
- **The manifest is not signed.** Anyone who can rewrite a bundle can rewrite
  its manifest to match. The gate detects tampering with *one* side, not a
  coordinated rewrite of both — which is exactly why the semantic evaluator runs
  on every payload regardless of how consistent its metadata looks.
- **`generated_at` is diagnostic only.** It is never compared against, nor
  allowed to substitute for, any contract clock.
- **The semantic stage needs a build.** `dist/` is gitignored, so a fresh
  checkout must run `npm run build` before the gate can reach the canonical
  evaluator. Without it the gate fails closed rather than passing.
