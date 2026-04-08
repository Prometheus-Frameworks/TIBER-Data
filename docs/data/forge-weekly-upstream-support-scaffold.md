# FORGE weekly upstream-backed support scaffold (proof-of-path)

## What this path is

This scaffold adds a **new, separate** support-ingestion lane for FORGE weekly support artifacts sourced from upstream public data, not from the legacy offline fixture lane.

It currently exports two required support surfaces:

- `weekly_player_stats`
- `team_week_context`

Outputs:

- `data/raw/forge/weekly_player_stats.upstream_public_2024_w01_8player_scaffold.json`
- `data/raw/forge/team_week_context.upstream_public_2024_w01_2team_scaffold.json`

## Source used

- `nflreadpy.load_player_stats(..., summary_level="week")`
- `nflreadpy.load_team_stats(..., summary_level="week")`
- fallback source path references in `src/ingest/public.py` for the equivalent nflverse parquet URLs

This scaffold is fail-closed:

- offline fallback is disabled
- export raises if public-source reads fail
- export raises if required cohort records are missing

## Minimal supported slice (current)

The scaffold intentionally supports only one narrow, reproducible slice:

- season: `2024`
- week: `1`
- player cohort: fixed 8-player set (ATL/DET) used for current FORGE weekly sanity coverage
- team cohort: `ATL`, `DET`

No broader season/week support is implied by this scaffold.

## How it differs from the legacy W1–W6 offline fixture lane

Legacy lane (unchanged):

- `data/raw/forge/weekly_player_stats.offline_fixture.json`
- `data/raw/forge/team_week_context.offline_fixture.json`
- includes operational W1–W6 repo-held support artifacts with mixed provenance status

New scaffold lane:

- writes separate `*.upstream_public_*_scaffold.json` raw artifacts
- uses upstream-backed reads with offline fallback disabled
- proves reproducible source-backed generation for a minimal honest slice
- does **not** replace legacy W1–W6 support lane yet

## What remains before migration

Before replacing legacy support for broader weekly exports, the repo still needs:

1. explicit supported-week expansion policy and fail-closed gating per week
2. broader cohort/season handling without introducing silent fallback behavior
3. downstream validation that derived FORGE exports from this lane meet required operational quality
4. migration plan that preserves compatibility while retiring legacy-only support rows
