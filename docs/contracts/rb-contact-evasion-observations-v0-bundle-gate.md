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
    ↓  canonical evaluator      (src/contracts/v1/rbContactEvasionObservationsV0.ts,
    ↓                            compiled from source by the gate itself)
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

### Evaluator identity is established by building, not by asking

`dist/` is gitignored, so a stale, substituted or permissive module could sit
there exporting the correct `artifact_id` and `schema_version` while returning
`valid: true` for every payload. Self-reported constants prove nothing about
what code does, so **the gate never reads `dist/` at all.**

Instead it compiles the reviewed contract itself, on demand, with the
**repository-local, lock-pinned** TypeScript compiler
(`node node_modules/typescript/bin/tsc`) and the committed
[`scripts/rb_contact_evasion_evaluator.tsconfig.json`](../../scripts/rb_contact_evasion_evaluator.tsconfig.json).
`npx` is never invoked and `PATH` is never consulted for the compiler, so a
poisoned `npx`/`tsc` earlier on `PATH` can never run and no package acquisition
is ever attempted; if the local compiler is absent or its version differs from
the `package-lock.json` pin, the gate fails closed **before** compiling.

The compile is **race-free by construction**. A discovery pass asks the compiler
which repo-local sources the contract transitively needs; those files, plus the
tsconfigs and package manifests, are copied once into a private *immutable*
snapshot the process owns; the snapshot is what gets compiled, with the snapshot
as the working directory so repo-local resolution cannot reach the working tree;
and the receipt hashes the **snapshot** bytes -- exactly the bytes compiled.
Working-tree drift during compilation therefore cannot produce a module paired
with a receipt describing different source. Discovery is not an authority: it
only decides what to copy, and if it under-reports, the snapshot compile fails
closed rather than reaching outside the snapshot.

Execution is bound to the authenticated bytes with no reopen. The gate hands the
bridge the built module path and the sha256 of its bytes. The bridge reads the
module **once**, hashes it, refuses any mismatch, and then executes those
already-in-memory bytes through a Node module-customization hook -- it never
opens the path a second time. `zod`, the single runtime import, is resolved
against the module's original directory. Because the file is authenticated and
executed from one read, a swap between "hash" and "run" has no window to occupy:
there is no second open to race.

The build is memoized per process but the memo is *re-checked*, never assumed:
the fingerprinted sources and the emitted module are re-hashed on every use, so
a source edit or a swapped module forces a rebuild rather than reusing a verdict
from code that is no longer there.

**Exactly what is hashed**, recorded in the `evaluator` receipt of every result:

| Input | Why |
|---|---|
| every repo-local, non-`node_modules` file `tsc --listFiles` reports it read | the true transitive source surface, taken from the compiler rather than guessed. For the committed tsconfig that is exactly `src/contracts/v1/rbContactEvasionObservationsV0.ts`, because it imports nothing but `zod`. If the contract later imports a sibling module, that module joins the fingerprint automatically |
| `tsconfig.json` and `scripts/rb_contact_evasion_evaluator.tsconfig.json` | they decide how that source is compiled |
| `package.json` and `package-lock.json` | they pin `zod`, the one runtime dependency the evaluator imports |
| the emitted `.js` itself | so a reviewer can rebuild and compare digests |

`node_modules` entries in the compiler's file list are `.d.ts` type
declarations, erased at emit; they are not hashed, and the installed `zod`
version is recorded separately as a dependency pin.

The gate compiles the module that *defines* the evaluator rather than the
`src/index.ts` barrel, which keeps the identity-bound surface to the code that
actually decides. A test asserts the barrel re-exports exactly that function, so
"the canonical public evaluator" means the same thing it did before.

If the build cannot be produced — no `npx`, a type error, a missing tsconfig —
the gate fails closed with `BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE`. It never
falls back to a build lying around.

### The bridge response is admitted only if it is exactly well-formed

The transport is fail-closed at every step. The bridge's answer is trusted only
when it exits `0`, prints **exactly one** line, that line is a single strict JSON
object with no duplicate keys, `ok` is a **real boolean** (never a truthy string
or number), and the object's key set matches the envelope for the mode exactly:
`{ok, artifact_id, schema_version}` for constants, `{ok, report}` for evaluate,
`{ok, error, detail}` for a declared failure. A nonzero exit, no output, extra
lines (a real refusal followed by a success line), trailing bytes, a mixed
success/error shape, or any missing or extra field is refused.

### Every bundle file is read through one descriptor, bounded and typed

The gate never does a pathname `stat()` followed by a separate pathname read: that is a
time-of-check/time-of-use race in which an entry can be swapped between the two operations for an
oversized file (bypassing the cap, unbounded read), a FIFO (a blocking read that hangs), a device, or a
symlink. Instead every bundle file — the manifest and each declared artifact — is read through **one
descriptor**:

- Each path component is opened descriptor-relatively with `O_NOFOLLOW`. Intermediate components are
  opened `O_PATH | O_NOFOLLOW` (which resolves the inode without I/O, so a FIFO or device cannot block)
  and required to be real directories by `fstat`; a symlink at any component — final or intermediate — is
  refused. This is deterministic across kernels rather than relying on `ELOOP`/`ENOTDIR` nuances.
- The leaf is opened `O_NONBLOCK` so a FIFO cannot make the open hang.
- The type is validated by `fstat` **on the opened descriptor**: a regular file is required; a FIFO,
  device, socket, or directory is refused without being read.
- The cap is enforced against that descriptor's `fstat` size, and the read is a bounded read from the
  **same** descriptor that reads at most the cap plus one byte in total. An oversized replacement or
  growth after the size check is detected without allocating unbounded memory.
- The read accumulates into **one** growing buffer — not a list of chunks that is then joined, which would
  hold two payload-sized representations at once. **Within the bounded reader** peak payload ownership is a
  single `bytearray` of at most the cap plus one byte, plus one small reusable read chunk, and the reader
  makes no whole-payload copy. The "no whole-payload copy" claim is scoped to the reader: it is *not* a
  whole-lifecycle claim, because the integrity stage below deliberately makes one copy.
- Once the digest matches, the integrity stage **freezes** the verified bytes into an immutable `bytes`
  object and releases the mutable read buffer. This is a deliberate, one-time, per-artifact second
  payload-sized allocation (the `bytearray` and its `bytes` copy coexist for the duration of that copy,
  then the `bytearray` is dropped), not a whole-payload copy inside the read. It exists so the
  digest-authorized subject cannot be altered in place before evaluation: a mutable `bytearray` aliased
  into the parse and semantic stages (the earlier behaviour) let any holder flip a byte — for example a
  JSON-equivalent whitespace swap — so the evaluator could receive bytes whose SHA-256 no longer matched
  the digest just proved. An immutable `bytes` object cannot be mutated in place by any alias.
- The exact frozen bytes are carried in memory to the parse and semantic stages. The artifact pathname is
  **not** reopened there, and the frozen object cannot be mutated there, so neither a swap after integrity
  nor an in-place edit can change what the evaluator judges.

**No degraded fallback.** These primitives — `O_NOFOLLOW`, `O_PATH`, `O_NONBLOCK`, and `dir_fd` support on
`os.open` — are required to *prove* no-follow, component-relative access. If the platform cannot provide
them, the gate **fails closed before reading any bundle bytes** (`BUNDLE_DESCRIPTOR_UNSUPPORTED`); it never
falls back to a full-path open, which would follow a symlink to bytes outside the bundle. (Manifest reading
happens before path-safety normalization, and a path check followed by a later full-path open would itself
be raceable — so a fallback could not be made safe.) On Linux all four primitives are present.

Size and digest bind to the exact bytes that one descriptor yielded, preserving the digest and
declared-size semantics. All the path-normalization, bijection, manifest, shape, evaluator-identity, and
lifecycle guarantees above are preserved.

### The evaluator's verdict is validated before it is acted on

A verdict is the one thing this gate cannot re-derive, so it is read exactly as
given: no `bool()`, no `list()`, no `or []`. `parse_evaluator_report` requires
the report's key set to be exactly `{valid, shape_valid, violations,
reason_codes}`; `valid` and `shape_valid` to be actual booleans (`0`, `1` and
`"false"` are all refused); `reason_codes` to be a list of unique non-empty
strings; each violation to be an object with exactly `{reason_code, path,
detail}`; and the report to agree with itself — a rejection must name at least
one violation and one reason code, an acceptance must name neither, the reason
codes must equal the violation codes, and a payload that could not be parsed
cannot be `valid`.

Anything malformed or self-contradictory produces
`BUNDLE_SEMANTIC_EVALUATOR_FAILED` and the payload stays unvalidated.

Requiring the exact key set is deliberate: if Slice A's report grows a field,
this gate fails closed and gets re-reviewed rather than quietly ignoring it.

Finally, success is not "the failure list is empty". A bundle passes only when
every declared artifact **completed** the semantic stage, and an artifact that
did not, with no failure explaining why, becomes a failure itself.

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
# human-readable diagnostics; exit 0 pass, 1 fail.
# No build step: the gate compiles the contract itself.
python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root>

# machine-readable result on stdout, for CI
python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json

# or write it to a file (which must be outside the bundle)
python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json-out result.json
```

Or through the package script:

```bash
npm run check:rb-contact-evasion-bundle -- <bundle-root>
```

Both entry points behave identically. Neither trusts an existing build.

Exit codes: `0` the bundle passed every stage, `1` the bundle failed the gate,
`2` the invocation itself was invalid.

The gate performs no network access and opens every **bundle** path read-only.
It never writes into the bundle it is validating. `--json-out` pointing inside
the bundle is refused as a usage error, but that pathname check is only a
usability guard: it cannot see a hard link that shares a bundle file's inode and
it is raceable. The safety is in how the result is published. `--json-out` never
opens, truncates, or follows an existing output inode. The intended output parent
is resolved by a **component-by-component `O_NOFOLLOW` walk** from a trusted
anchor (`/` for an absolute path, the current directory for a relative one), each
component opened relative to the previous one. Because `O_NOFOLLOW` guards only
the final component of any single `open`, walking every level is what refuses a
symlink at *any* component — the parent **or any ancestor**, whether already
present or swapped in after the pathname preflight — so nothing can redirect the
write into the bundle; missing components are created with `mkdir` relative to
the pinned parent, never through a symlink. A **fresh, uniquely named** staging
inode is then created relative to that descriptor with
`O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW`, written, and `fsync`ed; a name
collision is resolved by trying a new random name, so an existing entry is never
unlinked and publication never deletes or mutates an unrelated pre-existing path.
Publication is a single `os.replace` (rename) of the staging entry onto the
destination entry. Because `rename` never follows the destination, a hard-linked
or symlinked output has its directory entry atomically repointed at the new inode
while the old (possibly bundle-shared) inode keeps its bytes — so a successful
`--json-out` can never corrupt the bundle. A refusal or a failed publication
leaves every bundle byte and any pre-existing output byte unchanged, and only the
uniquely named staging inode the gate created is cleaned up.

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
| 7 | `integrity` | byte size and type from `fstat` **on the opened descriptor** (never a pathname `stat`), then SHA-256 of the exact bytes read from that descriptor, then those bytes frozen into an immutable object |
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
| `BUNDLE_CONTRACT_IDENTITY_DRIFT` | the compiled contract reports an identity the gate does not pin |
| `BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE` | the evaluator could not be built from the reviewed source |
| `BUNDLE_SEMANTIC_EVALUATOR_FAILED` | the evaluator returned no verdict, or a malformed or self-contradictory one |

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
- **The semantic stage compiles on demand.** The gate needs `node` and the
  repository-local, lock-pinned TypeScript compiler; the first validation in a
  process spends a few seconds compiling. Without them it fails closed. It never
  uses `npx` and never acquires a package.
- **`node_modules` is not hashed.** The compiled evaluator imports `zod` at run
  time. The gate binds the TypeScript source it compiled and the declared
  dependency pin (`package-lock.json` records `zod`'s integrity hash, and the
  installed version is recorded in the receipt), but it does not hash the
  installed contents of `node_modules`. A tampered dependency tree is outside
  this boundary — it is the same trust boundary every other consumer of the
  contract has.
- **The build trusts the pinned `tsc` and `node`.** Identity means
  "deterministically produced from this source by the repository's lock-pinned
  compiler". The gate verifies the compiler's version against the lockfile, but
  a compromised toolchain binary or a compromised Node is out of scope.
- **Some guards are redundant defence-in-depth.** Mutation testing records that the exact failure-envelope check and the snapshot-compile escape / un-snapshotted checks kill no test individually: an `ok:false` response already fails closed whatever its shape, and confining the compile to the snapshot directory already prevents a repo-local read from outside it. They are kept as belt-and-braces; the escape-detector logic is unit-tested directly.
- **Module execution uses a Node loader hook.** The authenticated bytes are run
  from memory (never reopened), which closes the hash-then-reopen window. This
  relies on Node's built-in `module.register` customization hooks -- no new
  dependency and no bundler -- and on `zod` resolving from the module's original
  directory.
- **Four guards are redundant, and are recorded as such.** Mutation testing
  shows that disabling any one of them individually changes no outcome, because
  another rule already covers every case it would admit: the
  rejection-names-a-violation and acceptance-carries-no-violation rules are
  covered by the reason-code and code-agreement rules; the empty-violation
  backstop is covered by the closing sweep; and the entry-source check is
  covered by the emitted-output check. They are kept as defence-in-depth — with
  all four covering rules removed together, the escapes reappear immediately —
  but no test claims they are individually necessary.
