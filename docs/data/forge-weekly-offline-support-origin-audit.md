# FORGE weekly offline support origin audit (2024 W1–W6)

## Scope audited
- `data/raw/forge/weekly_player_stats.offline_fixture.json`
- `data/raw/forge/team_week_context.offline_fixture.json`

## Current origin signals in-repo
Both raw files are tagged as offline fixtures and point to `src/ingest/public.py` fixture origins:

- `weekly_player_stats.offline_fixture.json`
  - `provenance: "offline_fixture"`
  - `source_path: "src/ingest/public.py::FIXTURE_DATA.weekly_player_stats"`
- `team_week_context.offline_fixture.json`
  - `provenance: "offline_fixture"`
  - `source_path: "src/ingest/public.py::FIXTURE_DATA.team_week_context"`

The repo ingestion/export path that writes these raw JSON payloads is `PublicDataClient.write_raw_exports(...)` in `src/ingest/public.py`.

## Important reproducibility finding
Within the current checked-in `FIXTURE_DATA` in `src/ingest/public.py`, only week 1 records are present for `weekly_player_stats` and `team_week_context`.

That means the checked-in W2–W6 support rows in `data/raw/forge/*.offline_fixture.json` are repo-held artifacts, but **are not fully reproducible from the current `FIXTURE_DATA` block alone**.

## Honest-support conclusion for this PR
From currently repo-held support inputs/process, there is no reliable, documented, reproducible in-repo basis to honestly extend support beyond the existing W1–W6 window without introducing new upstream source material/process.

Therefore this PR keeps the supported endpoint fail-closed at W6 and does not treat W7+ as supported.
