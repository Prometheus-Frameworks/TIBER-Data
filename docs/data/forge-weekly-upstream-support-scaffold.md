# FORGE weekly upstream-backed support scaffold (proof-of-path)

## What this path is

This scaffold adds a **new, separate** support-ingestion lane for FORGE weekly support artifacts sourced from upstream public data, not from the legacy offline fixture lane.

It currently exports two required support surfaces:

- `weekly_player_stats`
- `team_week_context`

Outputs:

- `data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.json`
- `data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.json`

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
- weeks: `1, 2, 3`
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

## Commands for W1–W3 visual truth-check workflow

Generate upstream-backed scaffold outputs for the narrow supported slice:

```bash
python scripts/export_forge_weekly_upstream_support_scaffold.py
```

Run side-by-side terminal comparison against legacy fixture support lane:

```bash
python scripts/compare_forge_weekly_support_lanes.py --player-name "Amon-Ra St. Brown"
```

or

```bash
python scripts/compare_forge_weekly_support_lanes.py --player-id 00-0037834
```

This comparison lane is for human visual sanity checks only and is **not** a full migration path.

## What remains before migration

Before replacing legacy support for broader weekly exports, the repo still needs:

1. explicit supported-week expansion policy and fail-closed gating per week
2. broader cohort/season handling without introducing silent fallback behavior
3. downstream validation that derived FORGE exports from this lane meet required operational quality
4. migration plan that preserves compatibility while retiring legacy-only support rows
