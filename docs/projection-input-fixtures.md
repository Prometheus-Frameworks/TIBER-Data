# Projection input fixtures

Projection input fixtures are bounded, TIBER-Data-owned rehearsal artifacts for exercising downstream adapter contracts without creating a production ingestion path.

The first bundle lives at:

- `data/projection-input-fixtures/weekly_projection_input_fixture_2026_w01.json`

## Boundary

This fixture is intentionally small and non-production:

- It is for Point-prediction-model adapter rehearsal only.
- It does not claim full-season, live-week, or production projection coverage.
- It does not assert 2026 roster continuity; the `2026_w01` label is a rehearsal label, while the included opportunity values are sourced from bounded 2025 week 1 TIBER-Data artifacts.
- Projection metadata such as season/week, scoring format, fixture-only status, and source evidence labels lives under `projection_context`; `league_context` is reserved for the downstream adapter-compatible league shape (`teams`, `starters`, optional `FLEX`, `flex_allocation`, and `replacement_buffer`).
- It omits unavailable optional fields rather than filling them with `null` or synthetic values.
- It does not synthesize high-value usage fields such as touchdown opportunity, goal-line work, end-zone targets, or injury/role interpretations.

## Evidence gaps

Missing fields in these bundles are intentional evidence gaps. They use the downstream adapter-facing shape (`field`, `severity`, `reason`, optional `player_id`, and optional `impact`) and should be read as provenance and scope signals, not as model defaults. Downstream consumers should keep missing high-value usage fields missing unless a governed TIBER-Data source artifact and semantics entry support them.

## Inspection

Run the fixture inspector from the repository root:

```bash
node scripts/inspect_projection_input_fixture.mjs
```

To emit a generated markdown summary:

```bash
node scripts/inspect_projection_input_fixture.mjs --write
```
