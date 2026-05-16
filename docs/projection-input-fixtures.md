# Projection input fixtures

Projection input fixtures are bounded, TIBER-Data-owned rehearsal artifacts for exercising downstream adapter contracts without creating a production ingestion path.

The first v1 bundle lives at:

- `data/projection-input-fixtures/weekly_projection_input_fixture_2026_w01.json`

The versioned v1 Zod contract lives at:

- `src/contracts/v1/projectionInputFixture.ts`

Detailed contract notes live at:

- `docs/contracts/projection-input-fixture-v1.md`

## Boundary

This fixture is intentionally small and non-production:

- It is for Point-prediction-model adapter rehearsal only.
- It does not claim full-season, live-week, or production projection coverage.
- It does not assert 2026 roster continuity; the `2026_w01` label is a rehearsal label, while the included opportunity values are sourced from bounded 2025 week 1 TIBER-Data artifacts.
- Projection metadata such as season/week, scoring format, fixture-only status, and source evidence labels lives under `projection_context`; `league_context` is reserved for the downstream adapter-compatible league shape (`teams`, `starters`, optional `FLEX`, `flex_allocation`, and `replacement_buffer`).
- It omits unavailable optional fields rather than filling them with `null` or synthetic values.
- It does not synthesize high-value usage fields such as touchdown opportunity, goal-line work, end-zone targets, or injury/role interpretations.

## v1 contract shape

`projection-input-fixture.v1` validates the existing bounded fixture bundle shape:

- top-level bundle metadata (`input_contract_version` and `tiber_data_schema_version`);
- `fixture_scope`, including `kind: "bounded_rehearsal_fixture"` and `production_coverage_claim: false`;
- `source_dataset_refs` and `identity_ref` provenance;
- `projection_context` metadata, including separate projection-label season/week and source-evidence season/week;
- `league_context` rehearsal settings;
- `player_opportunities` rows with required identity fields and optional finite numeric opportunity/context fields;
- `missing_fields` evidence-gap records;
- `adapter_warnings` that preserve fixture-only and provenance boundaries.

The contract is a schema and governance boundary only. It does not add live ETL, source fetching, downstream model scoring, production projection coverage, or Point-prediction-model code changes.

## Evidence gaps and severity vocabulary

Missing fields in these bundles are intentional evidence gaps. TIBER-Data keeps `missing_fields[].severity` as the fixture-level literal value `"warning"` in v1. A fixture warning means the gap should remain visible during adapter rehearsal; it is not a downstream scoring severity or a `required | optional` contract.

Downstream adapters that need `required | optional` semantics must map TIBER-Data fixture warnings explicitly before scoring. They must not silently reinterpret fixture warnings as production scoring requirements, and they must keep missing high-value usage fields missing unless a governed TIBER-Data source artifact and semantics entry support them.

## Inspection

Run the fixture inspector from the repository root:

```bash
node scripts/inspect_projection_input_fixture.mjs
```

The inspector validates the bundle against the v1 Zod schema and then preserves fixture-specific semantic checks:

- no unsupported `not_consumed_yet` fields in consumed player rows;
- no `null` substitution for unavailable values;
- finite numeric values for present opportunity/context fields;
- bounded fixture-only and provenance warnings.

To emit a generated markdown summary:

```bash
node scripts/inspect_projection_input_fixture.mjs --write
```
