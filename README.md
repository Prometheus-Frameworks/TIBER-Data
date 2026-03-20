# TIBER-Data

TIBER-Data is the boring source of truth for canonical football data contracts used by downstream TIBER repositories. This PR adds a small, strict, versioned role-opportunity contract so repos like `Role-and-opportunity-model` and `TIBER-Fantasy` can stop inventing slightly different payload shapes.

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

## Existing data pipeline

The Python ETL and read-only API remain in this repository for producing deterministic raw, silver, and gold datasets. The contract work introduced here is designed to sit alongside that pipeline and provide a cleaner handoff boundary for downstream consumers.
