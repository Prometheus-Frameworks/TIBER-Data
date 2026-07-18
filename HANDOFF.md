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

## Current handoff — #216 2015-2020 player-season source-availability audit (blocked network run, requires followup)

- Active task: TIBER-Data #216 — bounded, read-only source-availability audit of REG seasons 2015-2020 for the `player_season_coverage_v0` family (approved source family only: `nflreadpy.load_player_stats`, `nflreadpy.load_players`). Provenance/source-audit task class; no candidate build, no promotion, no support-window change.
- Files touched: `scripts/audit_player_season_coverage_2015_2020_source_availability.py`, `tests/test_audit_player_season_coverage_2015_2020_source_availability.py`, `docs/reports/player-season-coverage-v0-2015-2020-source-availability.md`, `docs/reports/player-season-coverage-v0-2015-2020-source-availability.json`, `HANDOFF.md`.
- Audit-trigger status: this change *is* an audit (read-only inspection + durable aggregate report); no artifact rows were produced or mutated. Independent review is still requested because the report expands knowledge about a possible supported season window and could be misread as authorizing 2015-2025 support if its boundaries are imprecise.
- What is now true: a deterministic, fail-closed, offline-testable audit script exists for the six seasons (per-season isolation, aggregate-only reporting, no player names/IDs/rows, terminal-decision enum fixed by #216, and the 2021+ `EXPECTED_REG_WEEKS = set(range(1, 19))` assumption deliberately NOT reused — week spans are taken from evidence). The committed report records the network run attempted from the audit environment: all six seasons `not_observed` because the execution environment's egress policy returned 403 for the approved source endpoints (`github.com/nflverse/nflverse-data/releases/download/...`); terminal decision `player_season_coverage_2015_2020_source_audit_requires_followup`.
- What is still missing: an execution environment that can reach the approved nflreadpy endpoints. The follow-up is to re-run `python scripts/audit_player_season_coverage_2015_2020_source_availability.py` unchanged from such an environment and re-commit the regenerated report; only then can per-season `source_rows_exist` / `builder_compatible` evidence exist.
- What must not be assumed: the 403s are an access failure of this environment, NOT evidence that upstream lacks 2015-2020 (upstream availability remains UNKNOWN); no season 2015-2020 is source-verified, builder-compatible, built, promoted, or available to consumers; 2021-2025 REG remains the only promoted window; no ADP source exists or was investigated; no Forecast behavior is authorized.
