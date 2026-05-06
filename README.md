# TIBER-Data

TIBER-Data is a source of truth for canonical football data contracts used by downstream TIBER repositories. This PR adds a small, strict, versioned role-opportunity contract so repos like `Role-and-opportunity-model` and `TIBER-Fantasy` can stop inventing slightly different payload shapes.

## Canonical governance documents

TIBER-Data is both:

- the canonical contract authority for cross-repo integration in the TIBER ecosystem
- the canonical home for TIBER architecture governance documents

Start here:

- [ARCHITECTURE.md](ARCHITECTURE.md)

### Agent operating files

- [AGENTS.md](AGENTS.md)
- [TRUTH_SOURCES.md](TRUTH_SOURCES.md)
- [HANDOFF.md](HANDOFF.md)

Canonical architecture governance documents:

- [TIBER Architecture Document v1.0](docs/governance/architecture/tiber-architecture-document-v1.0.md)
- [TIBER Architecture Quick Reference v1.0](docs/governance/architecture/tiber-architecture-quick-reference-v1.0.md)
- [TIBER Evidence Layer v0](docs/governance/evidence-layer-v0.md)
- [TIBER Intelligence Evolution Roadmap](docs/governance/tiber-intelligence-evolution-roadmap.md)
- [Evidence Layer v0 Contract Shapes](docs/contracts/evidence-layer-v0.md)
- [Historical Rookie Replay v0 Governance](docs/governance/historical-rookie-replay-v0.md)
- [Historical Rookie Replay v0 Contract](docs/contracts/history-rookie-replay-v0.md)

## What this repo is for

This repository now has two complementary jobs:

- maintain deterministic football data assets for downstream modeling workflows
- publish canonical, versioned contracts that describe how downstream repos should exchange role and opportunity outputs

The new contract in `src/contracts/v1` is intentionally about **schema, fixtures, and validation only**. It does not perform football analysis, projections, or model scoring.

## Canonical role-opportunity contract v1

The `v1` contract defines a single record shape for player role and opportunity outputs with explicit fields for:

- player identity
- season and week scope
- canonical primary role plus free-form role tags
- usage and opportunity metrics
- confidence metadata
- source metadata

### Versioning

The contract lives under a versioned namespace:

```text
src/
  contracts/
    v1/
      enums.ts
      roleOpportunity.ts
      examples.ts
      index.ts
```

That layout makes a future `v2` additive and obvious.

### Raw counts vs share metrics

The contract carries both normalized shares and raw counts.

- **Share metrics** are decimals constrained to `0..1`, such as `targetShare`, `routeParticipation`, or `goalLineCarryShare`.
- **Raw counts** are non-negative integers, such as `targets`, `routesRun`, or `goalLineCarries`.

This split keeps downstream consumers from having to guess whether a field is a rate, a percentage-like decimal, or a volume total.

## Canonical FORGE weekly input contract v1 (groundwork)

TIBER-Data now includes an initial canonical input contract for weekly skill-position records flowing into TIBER-FORGE: `ForgeWeeklyPlayerInput`.

This addition is intentionally narrow and scoped to **schema, deterministic fixtures, and validation helpers** for the first TIBER-Data → TIBER-FORGE ingestion boundary.

What this does:

- defines a versioned weekly input record shape under `src/contracts/v1`
- includes deterministic WR/RB/QB fixtures plus a mixed array fixture
- provides validation helpers for single records and arrays

What this does **not** do:

- add FORGE scoring/math logic
- complete the live weekly export/ETL pipeline
- claim production readiness for downstream ingestion

### Canonical sample handoff artifact (groundwork)

TIBER-Data now ships a deterministic sample handoff artifact that matches `ForgeWeeklyPlayerInput` and gives TIBER-FORGE a concrete upstream file target:

- `data/gold/forge/forge_weekly_player_input_2025_w12.sample.json`

Generate/re-generate it from canonical fixtures with fail-closed validation:

```bash
npm run export:forge-weekly-sample
```

This is groundwork only: fixture-derived canonical shape for ingestion alignment, not the completed live weekly production export pipeline.

### First narrow derived handoff artifact slice

TIBER-Data now ships two **derived** `ForgeWeeklyPlayerInput` export lanes from repo-held support artifacts:

- `data/gold/forge/forge_weekly_player_input_2024_w01.qb_offline_fixture.derived.json`
- repeatable broader skill-position weekly artifacts for a small offline-fixture-backed set:
  - `data/gold/forge/forge_weekly_player_input_2024_w01.skill_offline_fixture.derived.json`
  - through `data/gold/forge/forge_weekly_player_input_2024_w06.skill_offline_fixture.derived.json`

Generate/re-generate with fail-closed validation:

```bash
npm run export:forge-weekly-derived
```

Scope remains intentionally small and honest:

- both artifacts are derived from repo-held support fixtures (`data/raw/forge/weekly_player_stats.offline_fixture.json` and `data/raw/forge/team_week_context.offline_fixture.json`)
- the QB lane remains a narrow sanity-check slice fixed to season `2024`, week `1`
- the skill lane now follows a repeatable weekly factory pattern for season `2024`, weeks `1-6`
- each generated skill artifact is validated fail-closed (non-empty, coherent metadata, deterministic order, expected position coverage, schema validation)
- spread/matchup and route-participation style fields still rely on explicit neutral/default placeholders where source coverage is missing
- this is offline-fixture-backed season-segment coverage groundwork, not full-season production ETL
- support-origin audit for this lane: `docs/data/forge-weekly-offline-support-origin-audit.md`
- provenance status: W1 is reproducible from current `src/ingest/public.py::FIXTURE_DATA`; committed W2–W6 raw support rows remain legacy repo-held artifacts pending fully recoverable provenance

This is still **not** the full live weekly production export pipeline.

### Upstream-backed FORGE weekly support scaffold (proof-of-path)

TIBER-Data now includes a separate scaffold path for **upstream-backed** weekly support ingestion for FORGE, distinct from the legacy offline fixture lane.

- script: `python scripts/export_forge_weekly_upstream_support_scaffold.py`
- outputs:
  - `data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.json`
  - `data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.json`
- current supported scope is intentionally narrow and fail-closed:
  - season `2024`, weeks `1-3`
  - fixed 8-player sanity cohort (ATL/DET) plus ATL/DET team context
- side-by-side visual comparison script:
  - `python scripts/compare_forge_weekly_support_lanes.py --player-name "Amon-Ra St. Brown"`
  - (or `--player-id 00-0037834`)

This is a reproducible source-backed scaffold only and does **not** replace the current W1–W6 offline fixture support lane yet.

Details: `docs/data/forge-weekly-upstream-support-scaffold.md`.

For the committed proof/reference specimen lane and deliberate refresh workflow, see:
`docs/data/forge-weekly-upstream-proof-reference-snapshot.md`.

## Research lane scaffolds

- Play-caller pass rate over expectation is scaffolded as a research-only lane for future TIBER-Teamstate input. It does not generate artifacts, transcribe reference-table values, fabricate play-caller mappings, or change GOBLIN candidates. See `docs/data/play-caller-pass-rate-over-expectation.md`.

## Evidence artifact ownership note

TIBER-Data owns canonical evidence artifacts used for operator-claim verification and promotion gating.

Downstream repositories may consume published evidence artifacts but should not invent or synthesize missing evidence.

## Downstream usage

Downstream repos should import the top-level exports and validate their payloads before persisting or consuming them.

### Example import usage

```ts
import {
  rbExample,
  roleOpportunityRecordSchema,
  validateRoleOpportunityRecord,
} from 'tiber-data-contracts';

const record = validateRoleOpportunityRecord(rbExample);
const parsed = roleOpportunityRecordSchema.parse(record);
```

### Example validation usage

```ts
import {
  isRoleOpportunityRecord,
  validateRoleOpportunityArray,
} from 'tiber-data-contracts';

const records = validateRoleOpportunityArray(input);

for (const record of records) {
  if (!isRoleOpportunityRecord(record)) {
    throw new Error('Invalid role-opportunity record.');
  }
}
```

## Fixtures included

Golden fixtures are available for four realistic player archetypes plus a mixed array:

- `rbExample`
- `wrExample`
- `teExample`
- `qbExample`
- `mixedRoleOpportunityExamples`

These fixtures are intentionally internally consistent and can be reused in downstream tests.

## Validate locally

Install Node dependencies and run the contract checks locally:

```bash
npm install
npm run typecheck
npm run test
npm run build
```

## Command list

- `npm install` — install the lightweight TypeScript validation toolchain
- `npm run typecheck` — verify TypeScript types
- `npm run test` — run the acceptance tests and fixture validation
- `npm run build` — emit the distributable TypeScript build into `dist/`


## Rookie data canonical storage

TIBER-Data is the canonical retrieval point for reusable rookie data artifacts.

- `data/raw/rookies/` — authoritative rookie inputs and raw support artifacts
- `data/silver/rookies/` — reusable processed rookie support artifacts
- `data/gold/rookies/` — promoted canonical rookie outputs (verified only)
- `data/rookies_manifest.csv` — provenance/inventory for every imported artifact

Boundary: `TIBER-Rookies` computes and experiments. `TIBER-Data` stores and serves.

Ingestion is **fail-closed**: artifacts must be directly read from TIBER-Rookies at import time. If source access fails, no data files are created — only an `IMPORT_BLOCKED.md` record. No synthetic or placeholder data is permitted in canonical storage.

- [Ingestion rules, boundary, and manifest schema](docs/data/rookies-data-centralization.md)
- Validate imports: `python scripts/validate_rookie_inventory.py`
- PR template for rookie imports: `.github/PULL_REQUEST_TEMPLATE/rookie-import.md`

## Existing data pipeline

The Python ETL and read-only API remain in this repository for producing deterministic raw, silver, and gold datasets. The contract work introduced here is designed to sit alongside that pipeline and provide a cleaner handoff boundary for downstream consumers.


## Evidence Layer: player weekly PPR outcomes v1 (historical backtest scaffold)

TIBER-Data now includes the first deterministic Evidence Layer builder for:

- `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`

Current bounded scope:

- season `2025`
- mode `historical_backtest` only
- repo-held offline fixture source lane only

Regenerate with:

```bash
npm run export:player-weekly-ppr-outcomes-v1
```

Details: `docs/data/player-weekly-ppr-outcomes-v1.md`.

## Evidence Layer: player weekly usage v1 (historical backtest scaffold)

TIBER-Data now includes a deterministic Evidence Layer usage builder for:

- `exports/promoted/nfl/player_weekly_usage_v1.json`

Current bounded scope:

- season `2025`
- mode `historical_backtest` only
- repo-held offline fixture source lane only

Regenerate with:

```bash
npm run export:player-weekly-usage-v1
```

Details: `docs/data/player-weekly-usage-v1.md`.

## Evidence Layer: team pace/pass environment v1 (historical backtest scaffold)

TIBER-Data now includes a deterministic Evidence Layer team environment builder for:

- `exports/promoted/nfl/team_pace_pass_environment_v1.json`

Current bounded scope:

- season `2025`
- mode `historical_backtest` only
- repo-held offline fixture scaffold lane only

Regenerate with:

```bash
npm run export:team-pace-pass-environment-v1
```

Details: `docs/data/team-pace-pass-environment-v1.md`.

## Evidence Layer: team offense summary v1 (historical backtest scaffold)

TIBER-Data now includes a deterministic Evidence Layer team offense quality builder for:

- `exports/promoted/nfl/team_offense_summary_v1.json`

Current bounded scope:

- season `2025`
- mode `historical_backtest` only
- repo-held offline fixture scaffold lane only

Regenerate with:

```bash
npm run export:team-offense-summary-v1
```

Details: `docs/data/team-offense-summary-v1.md`.


## Evidence Layer: roster player/team map v1 (historical backtest scaffold)

TIBER-Data now includes a deterministic Evidence Layer identity mapping builder for:

- `exports/promoted/nfl/roster_player_team_map_v1.json`

Current bounded scope:

- season `2025`
- mode `historical_backtest` only
- repo-held offline fixture scaffold lane only
- small bounded cohort only (not full real 2025 roster coverage)

Regenerate with:

```bash
npm run export:roster-player-team-map-v1
```

Details: `docs/data/roster-player-team-map-v1.md`.

## Historical Rookie Replay v0 (historical backtest scaffold)

TIBER-Data now includes the first deterministic Historical Rookie Replay scaffold builder for:

- `exports/promoted/rookie-replay/historical_rookie_replay_v0.json`

Current bounded scope:

- replay season `2025`
- roster identity join defaults to week `1`
- mode `historical_backtest` only
- repo-held offline fixture scaffold only
- small bounded cohort only

Regenerate with:

```bash
npm run export:historical-rookie-replay-v0
```

Details: `docs/data/historical-rookie-replay-v0.md`.


## Historical Rookie Replay readiness v0 (historical backtest scaffold)

TIBER-Data now includes the first deterministic replay join-readiness scaffold builder for:

- `exports/promoted/rookie-replay/historical_rookie_replay_readiness_v0.json`

Current bounded scope:

- replay season `2025`
- mode `historical_backtest` only
- local promoted fixture/scaffold inputs only
- readiness audit only (not scoring)
- small bounded cohort only; no claim of full real 2025 replay coverage

Regenerate with:

```bash
npm run export:historical-rookie-replay-readiness-v0
```

Details: `docs/data/historical-rookie-replay-readiness-v0.md`.

- `python scripts/build_roster_player_team_map_source_backed_2025.py` — generate 2025 source-backed weekly roster identity evidence via nflreadpy
