# Metric-definition inspection follow-up (PR #290): audit and validation record

Prepared 10 November 2026. Draft follow-up; unmerged, undeployed, unactivated.

This record covers PR #290 only. The #289 record under
`docs/audits/metric-definition-inspection-2026-11-09/` is historical and is left
unchanged; its file hashes describe the #289 candidate.

## Scope

Task classes: repo documentation and provenance/source-audit record, plus the
viewer change already made at the code head below. Base: `main` at
`7a13fda31356ec0fcb11e100157a3ff95156ecb4`.

- Code head: `66030294f5595d0ba23c8e3d9dc28457796ddc5c`. Definition-operation
  failure responses carry `consumer_authorized=false` and
  `canonical_approval="not_granted"`; documentation separates three
  route-participation meanings and separates `definition_ids` references from
  coverage `definition_bindings`; three regression checks were added.
- Closeout commit (the commit that adds this record): corrects one lookup
  sentence in `docs/metric-definition-inspection.md` and adds this paired record.
  It changes no code, test, registry or generated view. A file cannot contain its
  own commit SHA; the closeout head is stated in the PR body.

Unchanged: registry semantics, generated views, producers, formulas, observation
artifacts, promoted exports, source admission, consumer wiring, ROP and rankings.

## Review status by head

| Head | Status |
| --- | --- |
| `66030294f5595d0ba23c8e3d9dc28457796ddc5c` | Reviewed by Codex with isolated checks (see below). Not a full-suite or source-pin qualification. |
| Closeout head | **Not independently reviewed.** The earlier review does not carry over. |

## Lookup behavior recorded during closeout

Run at the closeout working tree; code identical to the reviewed head.

| Query | Status, exit | Returned IDs |
| --- | --- | --- |
| `route_participation` | `selection_required`, 2 | `inspection.route_participation.gold_compatibility_alias.v0`; `inspection.route_participation.team_dropbacks.proposed.v0` |
| `route %` | `selection_required`, 2 | `inspection.route_share.sum_player_routes.v0`; `inspection.route_participation.gold_compatibility_alias.v0`; `inspection.route_participation.team_dropbacks.proposed.v0` |

Both responses carry `consumer_authorized=false` and
`canonical_approval="not_granted"`. The code head's documentation said both
lookups list two variants. That was a documentation error; the documentation was
corrected to match this behavior and the implementation was not changed.

## Evidence, by who ran it

### 1. Builder-reported checks at the code head

Run by the builder in one cloud container (Node, Polars 2.1.0). Not independent.

| Check | Builder-reported result |
| --- | --- |
| Reproduction before the fix | `canonical_approval` absent on `invalid_request` and `invalid_registry` |
| `npm run test:metric-definition-inspection` | 22 passed, 0 failed, 0 skipped |
| `--definitions list --check-generated` | Passed |
| Legacy `--group`, `--status`, `--consumer` filters | Exit 0 |
| `node --check` (viewer, helper); `git diff --check` | Passed |
| `npm run typecheck`; `npm run build` | Passed |
| `npm run test` (full Vitest) | 1066 passed, 1 failed |
| Three bounded Python files (parity, usage builder, API) | 27 passed |
| `python -m ruff check tests/test_metric_definition_source_parity.py` | Passed |
| `python -m pytest` (full) | 1518 passed, 1 failed, 3 skipped |

`scripts/pre_pr.sh` was not run as one unrestricted run.

### 2. Codex independently executed checks at the code head

As relayed by the operator in the closeout request. No Codex review comment or
artifact is attached to PR #290, so the builder did not verify this section
against a primary record.

Confirmed by Codex, as isolated checks against exact fetched files:

- the three error statuses retain both denial flags;
- refusal payloads cannot override the flags;
- descriptor-generated views match the committed views;
- legacy filters work;
- both registry coverage artifacts omit route bindings.

Not done by Codex: rerunning the full focused suite, validating all pinned Git
sources, rerunning the full TypeScript or Python suites, or independently
reproducing their baseline failures.

### 3. Checks rerun during this closeout

Run by the builder at the closeout tree. Not independent.

| Check | Result |
| --- | --- |
| `npm run test:metric-definition-inspection` | 22 passed, 0 failed, 0 skipped |
| `--definitions list --check-generated` | Passed (exit 0) |
| Legacy `--group opportunity`, `--status needs_verification`, `--consumer Point-prediction-model` | Exit 0 |
| `node --check` (viewer, helper, focused checks) | Passed |
| `git diff --check`; `audit.json` parses | Passed |
| Both lookups | As recorded above |

Not rerun during closeout: typecheck, build, full Vitest, any Python test, Ruff.

### 4. GitHub CI

Read at the code head before the closeout push: 0 check runs and 0 commit
statuses. The repository has no `.github/workflows` directory. CI results are
absent, not passing.

## Unresolved test dispositions

Neither failure is waived, repaired or excluded by this PR. No full-suite pass is
claimed.

| Failure | Evidence | Disposition |
| --- | --- | --- |
| Vitest `test/rosterPlayerTeamMapArtifact.export.test.ts` > "supports source_backed lane when source artifact exists and fails closed otherwise" | Builder-reported: failed in the full run and reproduced on unmodified `main`; ran about 248 s and the full run also raised a Vitest worker `onTaskUpdate` timeout. Not independently reproduced. | The #289 record lists this case as a known exclusion for its bounded runs and attributes it to an array-versus-wrapper comparison. The builder did not verify that cause here. That exclusion is #289's; disposition for #290 is pending operator review. |
| Pytest `tests/test_historical_landing_context_2023_pilots.py::test_asserted_data_commit_path_blob_and_hash_pins_replay` | Builder-reported: failed in the full run and reproduced on unmodified `main`. It cannot read pinned paths at commit `9a58e6ed4b748783869277bb430c60ae33f1d05a`. The checkout was shallow; fetching that commit did not resolve it, and Git then reported one pinned path as not present in that commit. Not independently reproduced. | Cause undetermined. No existing exclusion found. Pending operator review. |

## Remaining uncertainties and approvals required

- Independent review of the closeout head.
- Operator disposition of both failures above.
- No CI evidence exists for any head of this PR.
- Pinned Git sources were validated only through the builder's focused suite.
- The FORGE proxy description has no source pin and is not drift-checked.
- Canonical definition approval, admitted route observations, any binding for
  `route_participation` coverage, and consumer activation remain outstanding and
  are outside this PR.

## Handoff

- Active task: documentation and validation closeout of PR #290.
- Files touched in the closeout: `docs/metric-definition-inspection.md`, this
  `README.md`, `audit.json`.
- Now true: the lookup documentation matches observed behavior; this record
  separates builder, Codex and closeout evidence.
- Still missing: everything under "Remaining uncertainties and approvals
  required".
- Must not be assumed: that the closeout head is independently reviewed; that
  either suite passes in full; that the Python failure is only a shallow-clone
  effect; that `consumer_authorized=false` or `canonical_approval="not_granted"`
  permits use of any metric; that the proposed dropback ratio is approved; that
  fixture rows are evidence.
- Audit-trigger status: triggered (documentation and support-claim wording);
  audit pending for the closeout head.

Machine record: [audit.json](audit.json).
Interface documentation: [metric-definition inspection](../../metric-definition-inspection.md).
