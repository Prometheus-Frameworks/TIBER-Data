# RB contact-evasion bundle gate — independent-review repair record — 2026-08-25

> Status: review-and-repair record for the Slice B bundle gate; not a contract, ingest, artifact, or promotion
> Tracking issue: TIBER-Data #234
> Pull request: TIBER-Data #260
> Reviewed head (findings produced): `4f9591af3ebbcabea965b689e7b95ab8b821d4c1`
> Authorized base: `4498d5efd053e6bbc87f5f28214b0509550ad653`
> Evidence cutoff: 2026-08-25

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
  **same** descriptor that never buffers more than the cap plus one byte, so an oversized file or growth
  after the size check is detected without unbounded memory.
- The exact verified bytes are carried in memory to the semantic stage; the artifact pathname is **not**
  reopened there, so a post-integrity swap cannot change what the evaluator judges.

Exact digest and declared-size semantics are preserved: size and digest now bind to the exact bytes the
one descriptor yielded. All prior fail-closed path-normalization, bijection, manifest, shape,
evaluator-identity, and lifecycle guarantees are preserved.

## Verification summary (repaired head)

- Focused Slice B suite: 262 passed (248 prior + 14 new descriptor-read controls).
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
