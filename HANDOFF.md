# TIBER-Data — Working Handoff

## Repo purpose in one sentence

TIBER-Data stores canonical contracts and deterministic football data artifacts for downstream repos.

## Current agent workflow

Typical loop:
1. Lamar defines scope and boundary
2. Codex implements the narrow change
3. Claude audits when needed
4. merge only if the repo remains honest

## When a task arrives

Ask:
1. Is this a contract task, a data artifact task, or a repo-governance task?
2. Does this repo already hold the source truth needed?
3. If not, should scope be reduced or should the task move elsewhere?

## If a mistake or uncertainty appears

First call:
- README
- contracts
- export code
- tests
- committed raw support files

If still unclear:
- Lamar decides whether the task is honest
- Claude audits if a builder may have overreached

## Handoff note format

Every material handoff should state:
- active task
- files touched
- audit-trigger status: not triggered, Claude audit happened, Claude audit pending, or Claude audit skipped with reason
- what is now true
- what is still missing
- what must not be assumed

Example:
- Active task: extend supported weekly artifact generation
- Files touched: raw support fixtures, export validation, tests, README
- Now true: W1–W6 supported and fail-closed
- Missing: honest raw support beyond W6
- Must not assume: W7+ exists unless committed support is present
## Current handoff — NFL Draft results v1 contract foundation

- Active task: implement issue #112 by adding the first-pass canonical NFL Draft results contract, one-year fixture validation path, and documented promoted export boundary.
- Files touched: `src/contracts/v1/nflDraftResults.ts`, `src/contracts/v1/index.ts`, `test/fixtures/nfl_draft_results_2026.contract_fixture.json`, `test/nflDraftResults.v1.test.ts`, `docs/data/nfl-draft-results-v1.md`, `README.md`, `HANDOFF.md`.
- Audit-trigger status: Claude audit pending/required by repo policy because this change adds a contract under `src/contracts/v1/` and documents promoted export semantics.
- What is now true: the v1 row contract validates required draft result fields, positive pick integers, ISO timestamps, nullable source URLs, and explicit unresolved-player-ID provenance states; the future promoted path is documented as `exports/promoted/nfl_draft_results/nfl_draft_results_{year}.json`.
- What is still missing: repo-held official NFL Draft result source files with clear provenance and any promoted official draft result artifacts.
- What must not be assumed: the fixture row is not an official draft fact, no year has full draft coverage, TIBER-Data does not own TIBER-Rookies scoring or prospect interpretation, and FORGE does not consume raw draft facts from this PR.

## Current handoff — #181 governed Teamstate coverage audit for Forecast gate

- Active task: audit/verify complete governed 2024 Teamstate source coverage for the Forecast Run 2 coverage gate (TIBER-Data #181). Upstream coverage only; no Forecast change, no Run 2 rerun, no FORGE, no product output.
- Files touched: `docs/data/team-week-raw-v0-2024-teamstate-coverage-audit.md`, `scripts/audit_team_week_raw_v0_2024_teamstate_coverage.py`, `tests/test_audit_team_week_raw_v0_2024_teamstate_coverage.py`, `exports/candidates/team_week_raw/team_week_raw_v0_2024_teamstate_coverage_audit.json`, `HANDOFF.md`.
- Audit-trigger status: this change *is* a Claude audit (read-only verification + durable report); no artifact rows were produced or mutated.
- What is now true: TIBER-Data already holds a complete governed 2024 `team_week_raw_v0` source — 32/32 teams, 544/544 played team-game rows, explicit governance marker, source/validation/lineage provenance, deterministic ordering, honest deferred (`pressureRateAllowed`) and absent (fantasy split) nulls with no zero-fill. A dependency-free audit + tests re-prove this from the committed artifact.
- What is still missing: nothing on the TIBER-Data side. The Forecast 3-team failure is a downstream handoff gap — TIBER-Teamstate must emit its Forecast-facing artifact from this governed 544-row source (full mode, not `--excerpt`/scaffold).
- What must not be assumed: this does not claim Teamstate or Forecast "works"; it does not run Forecast; it does not source pressure or fantasy splits; deferred/absent fields stay null and must never be zero-filled downstream.

### Current handoff — #220 2015–2020 candidate-build design accepted; implementation inactive

- Active task: TIBER-Data #220 completed the documentation-only design frontier for a bounded 2015–2020 REG `player_season_coverage_v0` candidate. The accepted design is `docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md`, accepted at PR #221 head `17d50febffbf087e7faec31157bc406a561a5fd4`, design blob `27aae171cb7b4138b272af32e42e06bb147900b2`. This is a design result only; candidate implementation remains inactive.
- Files touched: the accepted design document and this `HANDOFF.md` state synchronization. No builder, test, source, schema, validator, data, export, manifest, report, README, promoted artifact, Forecast file, or other repository file changed.
- Audit-trigger status: independent design review completed through five hardening rounds. Findings addressed included multi-file publication and rollback semantics, test-matrix consistency, first-run absence restoration, structural source-fingerprint binding, value-level hashing across both source frames and identity inputs, residue preflight, exact 1.0 identity joins, and removal of the publishable provisional-identity path.
- What is now true: an implementation-ready specification exists for a new bounded historical builder producing exactly 2015–2020 REG candidate rows. It requires nflreadpy `0.1.5`, exact agreement with the accepted #218 structural fingerprint, thirteen deterministic source-content hashes, exact 1.0 identity joins, no provisional published identities, weeks 1–17 independently for every season, `full_season` at 14 or more observed week numbers, games above 16 only through source-backed multi-team evidence and never above 17, unchanged schema and validator reuse, phase-0 residue preflight, journaled set publication, deterministic output, fail-closed drift handling, and the normative test matrix. Its terminal decision is `may_activate_player_season_coverage_2015_2020_candidate_build`.
- What is still missing: a separate explicit G2 operator decision activating implementation. No historical builder, tests, candidate rows, manifest, validation result, or build reports exist. Candidate execution, independent artifact audit, candidate acceptance, promotion proposal, promotion, and Forecast availability each remain separate gates.
- What must not be assumed: G1 acceptance is not implementation authority and does not mean a candidate exists. The promoted player-season window remains 2021–2025 REG only. “2015–2025 is available” remains prohibited. No promotion, Forecast, ADP, rebound research, rankings, projections, advice, or product behavior is authorized.

### Current handoff — #222 G2 candidate-builder implementation accepted; G3 run inactive

- Active task: TIBER-Data #222 completed the implementation-only G2 frontier for the bounded 2015–2020 REG `player_season_coverage_v0` candidate builder. The implementation was accepted at PR #223 head `dff6597ee3bcd9f0255e34c1ad02534c26ea9402`; builder blob `0c7fe1bb5885c75a09d7d461bbb7ce480b1fe3e9`; offline-test blob `9a10deac2f32266a1c73f465b5a5fa0ba115422f`. G3 network-backed candidate execution remains inactive.
- Files touched: the bounded historical builder, its offline test module, and this `HANDOFF.md` state synchronization. No candidate artifact, manifest, validation result, build report, data file, export, schema, validator, accepted audit script, accepted design document, 2021/2022–2025 builder, promotion manifest, README support claim, Forecast file, or other repository file changed.
- Audit-trigger status: independent review completed through three Codex rounds. Six findings were corrected before acceptance: mandatory post-G5 hash locking, partial-temp tracking, backup-cleanup handling, successful-publication exit semantics, damaged-manifest fail-closed behavior, and complete phase-one cleanup accounting. Final Codex review was clean at the accepted implementation head; all six review threads are resolved.
- What is now true: an independently reviewed offline implementation exists for the bounded 2015–2020 candidate build. It encodes the accepted source fingerprint, thirteen source-content hashes, historical 1–17 week rules, the 14-week full-season threshold, source-backed 17-game handling, exact 1.0 identity joins, unchanged schema/validator reuse, deterministic serialization, residue preflight, journaled set publication, rollback/recovery semantics, promoted-path guards, support-claim guards, and the normative test matrix. Focused tests passed 51/51 and the full repository suite passed 471 with 1 skipped.
- What is still missing: G3 operator authorization for the network-backed candidate run. No live nflreadpy candidate-generation calls have occurred and no candidate rows, artifact, manifest, validation result, or build report exist. Candidate execution, independent artifact audit, candidate acceptance, promotion proposal, promotion, and Forecast availability remain separate gates.
- What must not be assumed: accepted implementation is not candidate evidence, promotion, or consumer availability. The promoted player-season window remains 2021–2025 REG only. “2015–2025 is available” remains prohibited. No Forecast, ADP, rebound research, rankings, projections, advice, or product behavior is authorized.
