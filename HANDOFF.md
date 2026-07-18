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

## Current handoff — #218 2015–2020 player-season source-availability rerun (source observed; candidate-build issue may be proposed)

- Active task: TIBER-Data #218 completed the controlled network-capable rerun of the accepted #216/#217 `player_season_coverage_v0` source-availability audit for REG seasons 2015–2020. The audit script remained byte-identical to accepted blob `529f832b050dba494146f4b133c202072f587c0e`. This remains source-evidence work only: no candidate build, promotion, support-window widening, Forecast action, ADP work, or product behavior.
- Files touched by the #218 rerun: `docs/reports/player-season-coverage-v0-2015-2020-source-availability.md`, `docs/reports/player-season-coverage-v0-2015-2020-source-availability.json`, and this `HANDOFF.md` state update. No script, test, schema, contract, builder, data, export, manifest, README, or other repository file changed.
- Audit-trigger status: this change is a rerun of the previously accepted read-only audit from a qualifying operator-local network environment. The committed reports contain aggregate evidence only and no player names, IDs, or player-level rows. Independent review remains required because the terminal decision could be misread as a support or promotion claim.
- What is now true: the approved `nflreadpy.load_player_stats(...)` and `nflreadpy.load_players()` source calls completed successfully for every REG season 2015–2020. All six seasons passed source existence, required-column, identity-join, schedule-observation, schema-compatibility, validator-compatibility, and builder-path checks. Every season exposed contiguous REG weeks 1–17 with zero gaps, wrong-season rows, or duplicate grains; identity joins were 100%. The evidence-backed builder path requires an explicit 1–17 week-span parameter rather than the 2021+ 1–18 rule. The terminal decision is `may_open_player_season_coverage_2015_2020_candidate_build_issue`.
- What is still missing: a separately drafted, reviewed, and explicitly authorized 2015–2020 candidate-build issue. No candidate rows exist yet. The candidate design must independently define the historical week-span parameter, restate the full-season coverage threshold, and re-derive older-season games/trade allowances. Historical ADP remains a separate unresolved provenance dependency.
- What must not be assumed: the source audit does not mean 2015–2020 is built, promoted, Forecast-ready, or available to consumers. The promoted player-season window remains 2021–2025 REG. No Forecast mirror refresh, ADP ingestion, rebound study, rankings, projections, advice, or product action is authorized.
