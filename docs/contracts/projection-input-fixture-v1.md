# Projection input fixture contract v1

`projection-input-fixture.v1` is the narrow TIBER-Data contract for the committed projection-input rehearsal bundle shape. It lives in `src/contracts/v1/projectionInputFixture.ts` and is exported through the public v1 contract index.

## What it is

The contract describes a bounded rehearsal fixture bundle for downstream adapter practice, especially Point-prediction-model rehearsal. It validates:

- top-level bundle metadata and contract version;
- `fixture_scope`, including `kind: "bounded_rehearsal_fixture"` and `production_coverage_claim: false`;
- source dataset references and identity provenance;
- projection-context metadata that carries the rehearsal projection label separately from source-evidence season/week;
- league-context settings used by the downstream adapter rehearsal shape;
- player opportunity rows with required identity fields and optional finite numeric opportunity/context fields;
- visible missing-field records;
- adapter warnings that state fixture-only and provenance boundaries.

## What it is not

This contract is not live ETL, source fetching, projection scoring, roster truth, or production weekly coverage. It does not activate Point-prediction-model scoring behavior and does not claim that the `2026_w01` projection label is a verified 2026 roster or live projection slate.

The contract intentionally allows unavailable optional opportunity fields to be omitted. Consumers must not null-fill, zero-fill, or synthesize unavailable fields such as goal-line rushing attempts, end-zone targets, inside-10 carries, or other high-value usage values unless a governed TIBER-Data source and semantics entry support them.

## Projection label vs. source evidence

`fixture_scope.projection_label` and `projection_context.season/week` are rehearsal labels. `projection_context.source_evidence_season` and `projection_context.source_evidence_week` identify the bounded source-evidence window. The committed golden fixture labels the rehearsal as 2026 week 1 while preserving the source-evidence window as 2025 week 1.

## Missing-field severity vocabulary

TIBER-Data keeps `missing_fields[].severity` as the fixture-level literal value `"warning"` in v1. In this repo, `warning` means an evidence gap that must remain visible during rehearsal. It is not the same as a downstream scoring requirement level.

Downstream adapters that need `required | optional` or another scoring-facing severity vocabulary must map TIBER-Data fixture warnings explicitly before scoring. They must not treat the fixture warning vocabulary as an implicit scoring contract.

## Local validation

Validate the TypeScript contract and tests:

```bash
npm run typecheck
npm run test
```

Validate the semantics registry and fixture inspector:

```bash
npm run inspect:projection-input-semantics
node scripts/inspect_projection_input_fixture.mjs
```

The fixture inspector first validates the JSON bundle against the v1 Zod schema, then preserves the existing semantic checks for unsupported `not_consumed_yet` fields, null substitution, finite numeric values, and fixture-only/provenance warnings.
