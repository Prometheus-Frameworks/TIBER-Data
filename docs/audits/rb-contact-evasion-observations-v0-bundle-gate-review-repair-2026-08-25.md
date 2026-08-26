# RB contact-evasion bundle gate — independent-review repair record — 2026-08-25

> Status: review-and-repair record for the Slice B bundle gate; not a contract, ingest, artifact, or promotion
> Tracking issue: TIBER-Data #234
> Pull request: TIBER-Data #260
> Reviewed head (findings produced): `4f9591af3ebbcabea965b689e7b95ab8b821d4c1`
> Authorized base: `4498d5efd053e6bbc87f5f28214b0509550ad653`
> Evidence cutoff: 2026-08-26 (this record spans multiple review rounds; the latest evidence is dated 2026-08-26)

## Answer first

An independent Codex review, triggered when PR #260 was marked ready for review at head
`4f9591af3ebbcabea965b689e7b95ab8b821d4c1`, produced **three findings**: two P1 governance gaps
(a missing committed auditor artifact and a missing handoff record) and one P2 correctness/security
defect (a stat-then-reopen time-of-check/time-of-use race in the gate's file reads). All three are
accepted. This record and its JSON companion satisfy the first P1; `HANDOFF.md` satisfies the second;
the P2 code repair is committed to PR #260 with reproduction, negative controls, and mutation evidence.

This record does **not** constitute an independent audit of the repaired head. It records who produced
the findings (the Codex independent review), the repair disposition, and the residual boundaries. Final
exact-head audit status remains **pending fresh Codex review of the repaired head**.

## Task class and boundary

This is a repo-governance and contract-adjacent record under AGENTS.md, paired with a bounded
correctness/security repair to `scripts/validate_rb_contact_evasion_bundle.py`. It admits no source,
builds no artifact, and authorizes no promotion. Slice A's contract, schema, dictionary, reason codes,
minimum-sample rule, allowed combinations, and fixtures are unchanged (a committed test diffs the Slice A
surface against the authorized base and requires it empty).

## Pinned evidence

| Repository | Exact ref | Inspected purpose |
| --- | --- | --- |
| Prometheus-Frameworks/TIBER-Data | `4f9591af3ebbcabea965b689e7b95ab8b821d4c1` | reviewed Slice B gate, bridge, tests, docs |
| Prometheus-Frameworks/TIBER-Data | `4498d5efd053e6bbc87f5f28214b0509550ad653` | authorized base (Slice A squash) |

Review evidence: PR #260 review threads by `chatgpt-codex-connector`, created 2026-08-25T18:31:26Z —
review-comment ids r3856050625 (P1 auditor artifact), r3856050632 (P1 handoff), r3856050637 (P2 read race).

## Findings and repair disposition

### P1 — commit the required auditor review artifact (r3856050625)

AGENTS.md requires the auditor function for changes adding contract surfaces under `schemas/**` and
`docs/contracts/**`, and specifies audit outputs are committed artifacts. The reviewed head added a
manifest schema and a contract-doc but committed no audit artifact.

**Disposition:** repaired by committing this paired `.md` / `.json` record under `docs/audits/`, following
the repository's dated-paired convention. It does not fabricate an independent auditor identity: it records
that the Codex independent review produced the findings, and leaves final exact-head audit status pending
fresh Codex review of the repaired head.

### P1 — record the material handoff (r3856050632)

AGENTS.md/HANDOFF.md require a material handoff stating the active task, files touched, what is now true,
what remains missing, what must not be assumed, and audit-trigger status. The reviewed head updated
neither `HANDOFF.md` nor an equivalent record.

**Disposition:** repaired by adding a `## Current handoff — #234 Slice B` section to `HANDOFF.md` in the
existing format.

### P2 — bind size/type checks to the exact bytes read (r3856050637)

The gate performed a pathname `stat()` to check size/type, then a separate pathname `read_bytes()` — a
time-of-check/time-of-use race. Between the two, another process could replace the entry with an oversized
file (bypassing the 64 MiB cap, unbounded read), a FIFO (blocking read/hang), a device, or a symlink.

**Reproduced** at the reviewed head against the real gate (temporary files only): after the size check
sampled the original inode, the pathname was reopened and an oversized replacement (72 MiB) was read in
full — 8 MiB past the 64 MiB cap, unbounded.

**Disposition:** repaired as one gate-wide descriptor-bound file-read invariant, applied to every bundle
read (the manifest and each artifact) and to the semantic stage:

- Each path component is opened descriptor-relatively with `O_NOFOLLOW`; intermediate components are
  opened `O_PATH|O_NOFOLLOW` and required to be real directories by `fstat` (a symlink at any component,
  final or intermediate, is refused; deterministic across kernels).
- The leaf is opened `O_NONBLOCK` so a FIFO cannot make the open hang.
- Type is validated by `fstat` on the opened descriptor — a regular file is required; FIFOs, devices,
  sockets, and directories are refused without reading.
- The cap is enforced against that descriptor's `fstat` size, and the read is a bounded read from the
  **same** descriptor that reads at most the cap plus one byte in total, accumulating into one growing
  buffer (see the 2026-08-26 correction below), so an oversized file or growth after the size check is
  detected without unbounded memory.
- The exact verified bytes are carried in memory to the semantic stage; the artifact pathname is **not**
  reopened there, so a post-integrity swap cannot change what the evaluator judges.

Exact digest and declared-size semantics are preserved: size and digest now bind to the exact bytes the
one descriptor yielded. All prior fail-closed path-normalization, bijection, manifest, shape,
evaluator-identity, and lifecycle guarantees are preserved.

## Verification summary (repaired head)

- Focused Slice B suite: 263 passed (248 prior + 15 new descriptor-read controls). [Corrected 2026-08-26:
  this line originally read "262 passed (248 prior + 14 new)" — the round's 15 additions were undercounted
  as 14. `pytest --collect-only` in an isolated worktree at `96c33214` reports 263 node IDs.]
- Full Python suite, Slice A contract (748) and schema (81) suites: unchanged and passing.
- TypeScript typecheck, Ruff, syntax checks: clean. No TypeScript source changed.
- Vitest: unchanged versus the authorized baseline (this repair changes no TypeScript source); the single
  pre-existing `rosterPlayerTeamMapArtifact` failure is reproduced at the authorized base.
- Mutation testing: the descriptor-bound read guards were mutated against the real implementation; every
  security-relevant guard is killed by a named test; any zero-kill guard is characterized honestly.
- No file under `exports/**` changed; the reference bundle is byte-identical; no committed fixture,
  contract file, or canonical artifact was mutated by any test.

## Residual boundaries

- The gate proves bytes and file identity, not football truth. Slice A's own residual limits are unchanged.
- `node_modules`, the pinned toolchain binary, and Node itself remain trusted (out of scope), as recorded
  in the contract doc.
- The admitted-source registry stays unimplemented: no source is admitted, so there is nothing to pin
  against, and a registry would invent provenance.
- This record is not an independent audit of the repaired head. Fresh Codex exact-head review of the
  repaired head is still required before the audit trigger can be marked complete.

## Authorization boundary

This record authorizes no source access, collection, ingestion, candidate row, artifact, promotion, or
consumer activation. #234 remains open; PR #260 remains draft and unmerged.

---

## Second review round — 2026-08-26

A follow-up Codex exact-head review at head `96c332149e6411c51ecd6839afbe922a5a1ca499` produced **two
findings**, both accepted and repaired. Final exact-head audit status remains **pending fresh Codex review
of the repaired head**.

**Review provenance (corrected).** This round's findings were produced by a Codex exact-head review
performed in the operator session and relayed by the operator; they were relayed into PR #260 as a
follow-up comment on the existing first-round thread (`r3856050637`, comment `r3859172198`). There is **no
GitHub connector review object or thread** for this round, and the connector is **not** its author. (An
earlier version of the JSON companion recorded this round's `reviewer_identity` as
`chatgpt-codex-connector`; that was incorrect and is corrected here and in the JSON. The only genuine
`chatgpt-codex-connector` review threads on PR #260 are the three **first-round** threads created
2026-08-25T18:31:26Z.)

### P1 — required descriptor capabilities failed open

`read_bundle_file` had a fallback branch (used when `O_PATH`, `O_NOFOLLOW`, or `os.open(dir_fd=...)`
support was unavailable) that opened the full path. **Reproduced**: with those capabilities disabled and
`manifest.json` made a symlink to a file outside the bundle, the helper returned OK and read the external
bytes. The fallback's stated rationale was invalid — manifest reading occurs before `check_path_safety`,
and an artifact path-check followed by a later full-path open is itself raceable.

**Disposition:** the fallback is removed. `descriptor_primitives_available()` gates the read: if
`O_NOFOLLOW`, `O_PATH`, `O_NONBLOCK`, or `dir_fd` support is missing, `read_bundle_file` returns
`UNSUPPORTED` and `validate_bundle` fails the whole gate closed with `BUNDLE_DESCRIPTOR_UNSUPPORTED`
**before reading any bundle bytes**. No pathname-check-then-open substitute is introduced. A capability
matrix (drop `O_PATH`, `O_NOFOLLOW`, `dir_fd`, `O_NONBLOCK`, and combinations, against manifest,
final-component, and intermediate-component external symlinks) proves external/symlinked bytes are never
read. The earlier document/audit claim that "per-component symlink safety is still enforced by
`check_path_safety` upstream" was wrong and is corrected here and in the contract doc.

### P2 — cap-plus-one memory claim was false

`_read_fd_capped` accumulated a list of byte chunks and then `join`ed them; both representations coexisted
during the join, peaking at roughly twice the payload. **Reproduced**: a 4 MiB read peaked at ~8 MiB, so
the 64 MiB cap could require ~128 MiB of payload storage.

**Disposition:** the reader now accumulates into **one** growing `bytearray` and returns it directly (a
bytes-like object the caller hashes, decodes, and sends to the bridge), with no chunk list and no
whole-payload `join`. Peak payload ownership is a single buffer of at most the cap plus one byte, plus one
small reusable read chunk — measured with `tracemalloc` at ~1.25× the payload (payload plus one read
chunk), versus ~2× before. Post-`fstat` growth (trips the cap+1 bound) and short reads (fewer bytes for
the caller's size/digest checks) are both preserved. Every "never buffers more than the cap plus one byte"
statement in the code comments, the contract document, this audit, the JSON audit, and `HANDOFF.md` is
corrected to the accurate single-buffer / peak-ownership claim. [Corrected 2026-08-26, fourth round: that
"every statement" claim was itself incomplete — two occurrences survived it (the gate's descriptor-reads
module comment and the `check_integrity` docstring) and were corrected in the fourth round below.]

### Second-round verification

Focused Slice B suite: 284 passed (verified with `pytest --collect-only`), a +21 delta over the first
round's 263: 15 parametrized capability-matrix cases plus 6 standalone tests (`tracemalloc`
peak-ownership, single-buffer structural, growth/short-read, and companions). [Corrected 2026-08-26: an
earlier version of this section said the first round's count was 262 and re-derived the delta as +22; both
were wrong. The first round had undercounted its 15 additions as 14, so its true count was 263, and this
round's "+21" was correct all along — the error was in the base, not the delta. Verified by
`pytest --collect-only` in isolated worktrees: `4f9591af` 248, `96c33214` 263, `8d2b9cad` 284.]
Full Python suite and Slice A suites unchanged. Mutation testing: 6 mutations
against the real gate (reinstating the fallback, disabling the preflight, weakening the capability check,
reinstating the chunk-join, unbounded read, dropping growth detection), all killed, no degenerate, gate
restored byte-for-byte. No Slice A change; nothing under `exports/**`; reference bundle byte-identical.
Repaired head recorded on PR #260.

---

## Third review round — 2026-08-26

A further Codex exact-head review at head `8d2b9cad0488d649657b43d6b1339a6c92bcc0c7` produced **four
findings** (two P1, two P2), all accepted and repaired. Final exact-head audit status remains **pending
fresh Codex review of the repaired head**.

**Review provenance.** As with the second round, these findings were produced by a Codex exact-head review
performed in the operator session and relayed by the operator. There is **no GitHub connector review
object or thread** for this round; the connector is not claimed as its author.

### P1 — mutable verified-byte identity

`_read_fd_capped` returned a `bytearray`; `check_integrity` hashed it and then aliased the **same mutable
object** into both `verified_bytes` and `raw_bytes`; `evaluate_semantics` sent that object to the evaluator
without re-proving the digest. **Reproduced** through the real gate on a copy of the reference bundle: a
hook on the stage immediately before semantic evaluation flipped one JSON-insignificant space (`0x20`) to a
tab (`0x09`) in `verified_bytes` in place; the gate returned `ok=True` and the bridge received bytes whose
SHA-256 (`8f99…`, `cc71…`) differed from both the observed digest and the manifest digests (`f16a…`,
`ffab…`). The digest proof no longer bound the evaluated subject.

**Disposition — freeze at the boundary where the promise is made.** When the digest matches in
`check_integrity`, the verified bytes are frozen into an immutable `bytes` object (`frozen = bytes(raw);
del raw`), and both `verified_bytes` and `raw_bytes` reference that single immutable object. An immutable
`bytes` object cannot be mutated in place by any alias, so the bytes parsed, schema-checked, and evaluated
are byte-for-byte the ones integrity bound. Re-running the reproduction: `verified_bytes` is now `bytes`,
the in-place flip is refused (`'bytes' object does not support item assignment`), and the evaluator
receives bytes whose SHA-256 equals the manifest digests.

**Memory reconciliation (honest).** The old chunk-list/`join` double representation is gone **from the
reader**: the bounded read owns one growing buffer and makes no whole-payload copy. The integrity freeze,
by contrast, **deliberately and transiently owns two payload-sized representations together** — the
`bytearray` and its immutable `bytes` copy coexist for the duration of the copy, then the `bytearray` is
released. So there *is* a momentary double-payload peak, per artifact, at the freeze; what is repaired is
that it is a disclosed, bounded, deliberate copy at the integrity boundary rather than an undisclosed
structural double held by the reader. The "no whole-payload copy" property is scoped explicitly to the
bounded reader (in the reader docstring and the contract doc), not claimed for the whole lifecycle.

**Regression + mutation evidence.** Public-gate regressions added:
`test_verified_bytes_are_frozen_immutable_after_integrity` (both fields are the same immutable `bytes`
object; in-place assignment raises), `test_evaluator_receives_bytes_matching_the_manifest_digest` (the
bridge boundary is instrumented; every payload sent hashes to a declared manifest digest), and
`test_pre_semantic_mutation_cannot_alter_the_evaluated_subject` (the reproduction, as a regression). A
mutation removing the freeze (restoring the `bytearray` alias) is killed by these tests.

### P1 — incorrect reviewer identity (second-round audit)

The second-round audit block attributed operator-relayed Codex findings to the
`chatgpt-codex-connector` connector, though no GitHub connector review or thread exists for that round.
**Disposition:** both audit artifacts now record the actual provenance (Codex exact-head review in the
operator session, relayed by the operator, no GitHub review object or comment id, connector not the
author). The first-round attribution is unchanged because those three threads are genuine connector
reviews.

### P2 — capability matrix did not prove no read

The capability-matrix tests only asserted the external secret text was absent from `GateResult`, and one
term (`secret[:0]`) checked zero secret bytes — vacuous. Absence from the rendered result does not prove
the external bytes were never opened or read. **Disposition:** the 15-case matrix (manifest, final-, and
intermediate-component external symlink × each dropped primitive and the combined case) now instruments the
gate's real `os.open`/`os.read` boundary and asserts **zero opens and zero reads** after the capability
preflight fails. A control test proves the spies leave `descriptor_primitives_available()` intact when the
primitives are present and actually observe a real open and read — so a zero count is a genuine no-access,
not a broken detector. The instrumentation preserves the `dir_fd` view (registering the spy in
`supports_dir_fd` when `dir_fd` is meant to be supported), so the preflight fails only because of the
dropped `O_*` flag, never because `os.open` was replaced.

### P2 — reconcile all evidence text and counts

Stale wording reconciled across changed files: the contract stage table row 7 now reads "byte size and
type from `fstat` on the opened descriptor (never a pathname `stat`), then SHA-256 of the exact bytes, then
those bytes frozen into an immutable object"; the `check_integrity` and `_read_fd_capped` docstrings are
corrected; the "no whole-payload copy" claim is scoped to the bounded reader with the freeze copy
disclosed. The evidence cutoff is corrected to include 2026-08-26.

**Focused test count.** `pytest --collect-only` reports **288** node IDs at the repaired head. That is 284
(the actual collected count at `8d2b9ca`, verified with `--collect-only`) + 4 new tests this round (1
open/read instrumentation control + 3 P1 identity regressions). The count lineage, all via
`--collect-only` in isolated worktrees at each historical head:
`4f9591af` 248 → `96c33214` 263 (+15) → `8d2b9cad` 284 (+21: 15 parametrized matrix cases + 6 standalone)
→ `8c484931` 288 (+4). [Corrected in the fourth round, 2026-08-26: this paragraph originally gave the
lineage as "262 → 284 (+22) → 288 (+4)". That was false: the first repair round had undercounted its 15
additions as 14 (reporting 262 instead of 263), and this round's attempted reconciliation compounded the
error by trusting the recorded 262 and re-deriving the second-round delta as +22 instead of re-counting
the base. The second round's original "+21" was correct.]

### Third-round verification

Focused Slice B suite: **288 passed** (collect-only 288). Full Python suite: **1009 passed, 3 skipped**
(1005 at the prior head + the 4 new focused tests this round).
Slice A contract (748) and schema (81) suites unchanged. No TypeScript source changed, so vitest is
identical to baseline by construction. Mutation testing: 4 mutations against the real gate (remove the
freeze / bytearray alias; leave `raw_bytes` a distinct mutable bytearray; reinstate the full-path fallback;
disable the gate preflight), all killed, no degenerate, gate restored byte-for-byte. No Slice A change;
nothing under `exports/**`; reference bundle byte-identical. Repaired head recorded on PR #260.

---

## Fourth review round — 2026-08-26 (evidence reconciliation only)

A Codex exact-head review at head `8c484931255ea5edb4de7923a30b2d8434b8ebfa` **accepted the functional
repairs** (the mutable-alias freeze, the capability no-access instrumentation, the corrected reviewer
provenance) and found **one P2 evidence-reconciliation defect**. This round changes comments and
governance text only — no gate behavior — so no mutation evidence is manufactured for it. As with the
second and third rounds, the review was performed in the operator session and relayed by the operator; no
GitHub connector review object or thread exists for it.

### P2 — false test-count lineage and remaining stale wording

**The lineage was false.** `pytest --collect-only` in isolated git worktrees at each historical head
establishes: `4f9591af` **248** → `96c33214` **263** (+15) → `8d2b9cad` **284** (+21: 15 parametrized
capability-matrix cases + 6 standalone tests) → `8c484931` **288** (+4). The audit trail instead recorded
262 for the first repair round — that round undercounted its 15 additions as 14 — and the third round's
attempted reconciliation **compounded** the error by trusting the recorded 262 and re-deriving the
second-round delta as +22 instead of re-counting the base. The second round's original "+21" was correct
all along. Every occurrence (PR body, `HANDOFF.md`, this audit pair) is corrected, with the propagation
error annotated in place; historical commits are untouched.

**Remaining stale wording**, which the second round's "every statement corrected" claim had missed, is
corrected: the gate's descriptor-reads module comment and the `check_integrity` docstring still said the
bounded read "never buffers more than the cap plus one byte" — the accurate statement is that it *reads*
at most `cap + 1` bytes in total, while peak reader ownership is one growing buffer plus one bounded read
chunk and allocation headroom. The test module docstring still said semantic judgment is delegated to "the
compiled contract under `dist/`" — the gate compiles reviewed source into its private temporary build and
never trusts an ambient `dist/`. This record's top-level evidence cutoff (previously 2026-08-25) is
corrected to 2026-08-26. The freeze-memory wording in the PR body, `HANDOFF.md`, and the third-round
section above is made precise: the chunk-list/`join` double representation is gone **from the reader**,
while the integrity freeze **deliberately and transiently owns the `bytearray` and immutable `bytes` copy
together** — a disclosed, momentary, per-artifact double-payload peak at the freeze.

### Fourth-round verification

Comments and governance text only; gate behavior unchanged. Focused Slice B suite: 288 collected, 288
passed. Full Python suite: 1009 passed, 3 skipped. `py_compile`, Ruff, JSON validation, `git diff --check`
clean. Slice A untouched; nothing under `exports/**`; reference bundle byte-identical. Final exact-head
audit status remains **pending fresh Codex review of the repaired head**.

---

## Fifth review round — 2026-08-26 (`--json-out` output-publication safety)

An **independent GitHub Codex review** at head `e68fc176304699ed5ed815f22836f6b9bb56aea6` produced **one
P2 finding** (thread `r3864788150`). Unlike the second through fourth rounds, this is a genuine
`chatgpt-codex-connector` review thread on PR #260 — the first connector thread since the three
first-round threads.

### P2 — `--json-out` could follow an existing output inode and truncate a validated bundle file

The `--json-out` writer used `Path.write_text()`, guarded only by a pathname `realpath` check. **Reproduced**
against the real gate on temporary reference-bundle copies — three windows, each ending with exit 0 and a
corrupted bundle:

- **(A) hard link.** `--json-out` an external hard link sharing `manifest.json`'s inode. The `realpath`
  preflight accepted it — the link's own name is outside the bundle, and `realpath` does not resolve a hard
  link elsewhere — and `write_text()` followed the shared inode, truncating `manifest.json` from 1086 to
  2913 bytes.
- **(B) leaf symlink swap.** `--json-out` swapped to a symlink into the bundle after the preflight but
  before publication; `write_text` followed it.
- **(C) parent symlink swap.** `--json-out`'s parent directory swapped to a symlink into the bundle's
  `observations/` dir before publication; `write_text` wrote onto the artifact
  `p2_raw_count_without_denominator.json` (4144 → 2913 bytes).

**Repair — one output-publication invariant (`publish_json_out`).** The gate never opens, truncates, or
follows an existing output inode:

- The intended output **parent** is opened once with `O_NOFOLLOW | O_DIRECTORY` and every step is done
  **relative to that descriptor**. A parent that is (or is swapped to) a symlink is refused / pinned, so it
  cannot redirect the write into the bundle.
- A **fresh staging inode** is created relative to that `dir_fd` with
  `O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW` — never opening an existing inode, refusing a symlink planted
  at the staging name — then the data is written and `fsync`ed.
- Publication is a single `os.replace` (rename) of the staging entry onto the destination **entry**.
  `rename` never follows the destination: a hard-linked or symlinked destination has its directory entry
  atomically repointed at the new inode while the old (possibly bundle-shared) inode keeps its bytes.
- On any failure the staging inode is unlinked relative to the pinned `dir_fd` only, so cleanup never
  touches an unrelated path and no partial or truncated output is left behind.

The `realpath` "points inside the bundle" refusal is kept but demoted to a usability guard (it cannot see a
hard link and is raceable); the publication mechanism is the safety. Output bytes and exit codes are
unchanged. Re-running all three windows leaves every bundle file byte-identical: **A** and **B** publish the
result to the intended name, **C** is refused.

**Negative controls** (committed; each snapshots SHA-256 and size of every bundle file before and after, on
temporary copies): hard link to `manifest.json`; hard link to the artifact class; symlink to a bundle file
(caught by the `realpath` guard or safely republished, target byte-identical either way); leaf swapped to a
symlink after preflight (rename replaces the symlink entry); reachable parent-directory symlink swap
(`O_NOFOLLOW` parent open refuses); publication (`os.replace`) failure (staging cleaned up, bundle and prior
output byte-for-byte unchanged); ordinary new output and replacement of an unrelated prior output (both
succeed with a fresh inode); and a symlink planted at the staging name pointing into the bundle (not
followed). Plus a structural test pinning the invariant (`O_EXCL`/`O_NOFOLLOW` create, `os.replace`
publish, no `.write_text(`, no `O_TRUNC`).

### Fifth-round verification

Focused Slice B suite: **297 collected, 297 passed** (288 + 9 new: 8 `--json-out` controls + 1 structural).
Full Python suite: **1018 passed, 3 skipped**. `py_compile`, Ruff, JSON validation, `git diff --check`
clean. Mutation testing: **5 mutations** against the real publication (reinstate `write_text`; truncate the
leaf pathname; drop the parent `O_NOFOLLOW`; make the staging create non-exclusive; skip staging cleanup),
**all killed, no degenerate, gate restored byte-for-byte**. No Slice A change; nothing under `exports/**`;
reference bundle byte-identical. Final exact-head audit status remains **pending fresh Codex review of the
repaired head**.

---

## Sixth review round — 2026-08-26 (`--json-out` ancestor-symlink and collision-cleanup hardening)

A Codex exact-head review at head `58c69f62728e0c6cf99e5840816a747f0b37d3e6` found that the round-5
`--json-out` publication repair was **incomplete in two ways**. The finding was **relayed by the operator
in condensed form** because elaborating it tripped a content filter on the operator's Codex account (the
operator is separately contacting support); there is no GitHub connector review object or thread for this
round, and the connector is not claimed as its author. The relayed handoff named: commit `58c69f6`, P2,
`scripts/validate_rb_contact_evasion_bundle.py`, unmet requirement *"Output publication can still be
redirected through an ancestor symlink, and collision cleanup can delete an unrelated pre-existing entry."*
Both sub-findings were reproduced against the real gate before editing (temporary bundle copies only). This
round changes no TypeScript source.

### P2(a) — publication redirectable through an ancestor symlink

The round-5 publisher opened only the **immediate** parent with `O_NOFOLLOW | O_DIRECTORY`, but `O_NOFOLLOW`
guards only the *final* component of a single `open` — an ancestor above the parent is still followed.
**Reproduced:** with `out = gp/observations/<artifact>` where `gp` and `observations` are real directories
at the realpath preflight (so the preflight passed, seeing a path outside the bundle), then `gp` swapped to
a symlink to the bundle root before publication, `os.open('gp/observations', O_NOFOLLOW)` followed the `gp`
symlink and opened `bundle/observations`; publication overwrote
`observations/p2_raw_count_without_denominator.json` (4144 → 2913 bytes).

**Repair:** `_open_output_parent_nofollow` walks the output parent **one component at a time** from a
trusted anchor (`/` for an absolute path, the current directory for a relative one), each component opened
`O_NOFOLLOW | O_DIRECTORY` relative to the previous. A symlink at *any* level — parent or ancestor, present
or swapped in after the preflight — is refused; missing components are created with `mkdir` relative to the
pinned parent, never through a symlink.

### P2(b) — collision cleanup deletes an unrelated entry

The staging name was deterministic (`.{leaf}.rbce-stage.{pid}`), and a `FileExistsError` at that name was
resolved by `os.unlink(staging)` then retry — so an unrelated pre-existing file that happened to sit at that
name was **deleted**. **Reproduced:** a pre-created unrelated file at the deterministic staging name was
removed by a successful `--json-out` run.

**Repair:** the staging name now carries an unpredictable random token
(`.{leaf}.rbce-stage.{os.urandom(8).hex()}`), created `O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW`; a name
collision is resolved by trying a **new** random name — an existing entry is never unlinked, so publication
never deletes or mutates an unrelated pre-existing path, and the failure cleanup only removes the uniquely
named inode the gate itself created.

`os.replace` publication, the hard-link / symlink-destination safety, refusal / failed-publish
preservation, deterministic output, and exit codes are all unchanged. Re-running both windows: the ancestor
swap is refused (`GateUsageError`) with the bundle byte-identical; the collision leaves the unrelated file
byte-identical and still publishes the result.

### Sixth-round verification

Focused Slice B suite: **299 collected, 299 passed** (297 − 1 deterministic-staging-name control removed,
superseded by the collision control, + 3 new: ancestor-swap, static-ancestor, collision). Full Python
suite: **1020 passed, 3 skipped**. `py_compile`, Ruff, JSON validation, `git diff --check` clean. Mutation
testing: **5 mutations** against the real publication (reinstate the single-parent ancestor-following open;
reinstate blind unlink on collision; reinstate `write_text`; truncate the leaf pathname; skip staging
cleanup), **all killed, no degenerate, gate restored byte-for-byte** — `single_parent_open_follows_ancestor`
and `blind_unlink_on_collision` each have a dedicated behavioural kill. No Slice A change; nothing under
`exports/**`; reference bundle byte-identical. Final exact-head audit status remains **pending fresh Codex
review of the repaired head**.

### Sixth-round addendum — full handoff posted as a PR comment (same date)

After the condensed relay, the **full sixth-round handoff** was durably recorded on GitHub as
operator-authorized PR comment
[`issuecomment-5431528233`](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/260#issuecomment-5431528233)
(2026-08-26T21:49:53Z). The comment states its own provenance — a Codex exact-head review of `58c69f6`
performed in the operator session, relayed through that operator-authorized comment — and instructs that
the findings **not** be attributed to the connector. The earlier statement in this round's record that no
GitHub object existed for the round is superseded by that comment and corrected in the JSON companion
without rewriting the round's history.

Diffing the completed repair against the full handoff showed the core invariants already satisfied
(component-by-component no-follow parent binding with `makedirs` removed and dir_fd-relative `mkdir`;
collision-resistant `O_CREAT | O_EXCL | O_NOFOLLOW` staging with no unlink-on-collision; staging,
replacement, and cleanup only relative to the final pinned descriptor; `os.replace` publication and all
prior guarantees preserved) and **two required controls missing**, both added in a completion pass:

- **Symlink collider at the staging name:** a pre-existing symlink at the first staging candidate (forced
  via `os.urandom`) keeps its name and its target, the target's bytes are intact, and the result still
  publishes — the publisher moves to a new candidate, never unlinking or following the collider.
- **Ordinary nested-parent creation/replacement:** two missing parent levels are created by the walk's
  dir_fd-relative `mkdir` (no full-path `makedirs` exists), publication succeeds, and a second run
  atomically replaces the first output; the bundle stays byte-identical and no staging litter remains.

Re-run mutation matrix (real publication, byte-for-byte restore, no degenerate):
`single_parent_open_follows_ancestor` 4 kills (now including the nested-parent control),
`blind_unlink_on_collision` 2 kills (regular-file **and** symlink collision controls — a behavioural kill
of the unlink-on-collision reinstatement), `reinstate_write_text_publication` 8,
`publish_truncates_leaf_pathname` 7, `no_staging_cleanup_on_failure` 1.

Completion-pass verification: focused Slice B suite **301 collected, 301 passed** (299 + 2); full Python
suite **1022 passed, 3 skipped**; `py_compile`, Ruff, JSON validation, `git diff --check` clean; no Slice A
change; nothing under `exports/**`; reference bundle byte-identical. Final exact-head audit status remains
**pending fresh Codex review of the repaired head**.
