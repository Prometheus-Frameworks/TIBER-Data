# NFLMeta synthetic v0 — builder boundary audit

Date: November 9, 2026. Issue: Data #287.
Base: `35fc692b67d2e218b3033e7e30688e03c367de58`.

This is an implementation self-check, not independent review. Contract and identity
changes trigger independent review before merge under AGENTS.md. That review is
pending; this packet does not authorize merge or source admission. The paired JSON
records SHA-256 pins for the code, tests and documentation inspected (excluding
these audit files to avoid a self-referential digest).

## What was checked

- Allowed surface: versioned contracts, invented tests, contract documentation and
  handoff. Existing package exports, data artifacts, promoted identity bridges,
  dependencies and downstream consumers remain unchanged.
- Runtime imports are Zod and the three local contract files only. There are no
  network, filesystem, environment, credential or application-startup operations.
- Numeric zero, missing, not-reported and partial observations remain distinct.
  Calendar dates are not kickoff times; provider write clocks are not publication
  clocks; synthetic receipts are not actual custody. Fingerprints are not ordered
  revisions or complete correction history.
- Reconciliation exposes no partial registry, refuses additions-only/batch input,
  validates page continuity/version/snapshot/total and explicit completion, aborts
  on failure, and keeps established identities when null, absent or under review.
  Conflicting established IDs withhold the entire proposal; retained IDs carry
  an explicit without-current-verification basis. Nothing applies a
  proposal to the promoted crosswalk.
- All records carry a synthetic-only, not-admitted evidence boundary. Neither
  successful parsing nor complete provider-registry traversal creates a population,
  rights, finality or independently corroborated-fact claim.

No unresolved builder finding was identified. This is not evidence of an independent
clean review or real-provider compatibility.

## Validation

Runtime: Node 24.22.1, Python 3.12.14, Vitest 3.2.4.

- 89 focused synthetic tests passed.
- TypeScript typecheck and build passed.
- 1,055 tests across 20 TypeScript files passed with the existing roster-export
  file excluded.
- `test/rosterPlayerTeamMapArtifact.export.test.ts` did not finish within 90 seconds
  on the candidate or 60 seconds on unchanged base. The original unbounded full
  run was interrupted after stalling there. The full TypeScript suite is therefore
  **not green**; no roster-export code or root export changed in this task.
- Python suite: 1,506 passed, 3 skipped, 1 failed. The existing
  `test_bridge_opens_the_module_exactly_once` strace audit recorded zero module
  opens; the exact same failure reproduced on unchanged base. No Python code
  changed here. The full Python suite is **not green**.
- The first pre-PR invocation stopped at a missing pytest dependency. The declared
  Python development dependencies were then installed in an isolated test environment.

## Remaining boundary

Independent review must verify the actual candidate head. Real response conformance,
coverage, identity quality, clocks, entitlement, billing and retention/replay rights
remain unqualified. No provider contact, purchase, credentials, live call, persistent
cache, promotion, source activation, merge or deployment was performed.
