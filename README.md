# TIBER-Data

TIBER-Data is a source of truth for canonical football data contracts used by downstream TIBER repositories. This PR adds a small, strict, versioned role-opportunity contract so repos like `Role-and-opportunity-model` and `TIBER-Fantasy` can stop inventing slightly different payload shapes.

## Canonical governance documents

TIBER-Data is both:

- the canonical contract authority for cross-repo integration in the TIBER ecosystem
- the canonical home for TIBER architecture governance documents

Start here:

- [ARCHITECTURE.md](ARCHITECTURE.md)

Canonical architecture governance documents:

- [TIBER Architecture Document v1.0](docs/governance/architecture/tiber-architecture-document-v1.0.md)
- [TIBER Architecture Quick Reference v1.0](docs/governance/architecture/tiber-architecture-quick-reference-v1.0.md)

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
