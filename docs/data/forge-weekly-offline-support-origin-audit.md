# FORGE weekly offline support provenance audit (2024 W1–W6)

## Scope
- `data/raw/forge/weekly_player_stats.offline_fixture.json`
- `data/raw/forge/team_week_context.offline_fixture.json`

## Provenance result
**State B — provenance still incomplete.**

The repo contains enough evidence to explain *where* W2–W6 were committed (specific commits), but not enough to fully reconstruct a deterministic in-repo generation process that reproduces those W2–W6 rows from current fixture source alone.

## What is known (direct evidence)
- Both raw support files declare `provenance: "offline_fixture"` and point at `src/ingest/public.py::FIXTURE_DATA...` via `source_path`.  
- `PublicDataClient.write_raw_exports(...)` is the only in-repo writer for this payload shape (`provenance`, `source_path`, `records`).
- Current checked-in `FIXTURE_DATA` in `src/ingest/public.py` contains only season 2024 week 1 rows for:
  - `weekly_player_stats`
  - `team_week_context`
- W2–W6 rows in raw support files were committed in two history steps:
  - `00a43ee` added W2–W3 support rows
  - `c0fcbea` added W4–W6 support rows

## What is inferred (reasonable, but not proven)
- W2–W6 were likely assembled as repo-held offline support expansions to unblock skill weekly derived artifact exports for W2–W6.
- The raw support rows were likely authored/updated directly in committed JSON (or from an external local process not captured in this repo), then consumed by `src/export/forgeWeeklyDerivedArtifact.ts`.

## What is not proven
- A complete in-repo recipe that regenerates the committed W2–W6 raw support rows from current `FIXTURE_DATA` in `src/ingest/public.py`.
- Any checked-in fixture builder, script, or documented source path that deterministically reconstructs W2–W6 support records from source truth currently present in this repo.

## Reproducibility status today
- **Fixture-reproducible now:** W1 raw support rows from `src/ingest/public.py::FIXTURE_DATA`.
- **Not reproducible from current fixture block alone:** W2–W6 raw support rows.
- **Operationally available but legacy:** W2–W6 remain usable as committed repo-held support artifacts for backward-compatible downstream derived export checks, but are not promoted as fully reproducible or source-backed support.
- **Current machine-readable manifest:** `data/forge_weekly_offline_support_provenance_manifest.json`.
- **Current gap audit:** `docs/data/forge-weekly-w2-w6-provenance-gap-audit-2026-05-16.md`.

## Files/history inspected for this audit
- `src/ingest/public.py`
- `src/main.py`
- `src/export/forgeWeeklyDerivedArtifact.ts`
- `test/forgeWeeklyDerivedArtifact.export.test.ts`
- `README.md`
- `data/gold/forge/README.md`
- `data/raw/forge/weekly_player_stats.offline_fixture.json`
- `data/raw/forge/team_week_context.offline_fixture.json`
- git history for those paths, including commits:
  - `d36e7c0` (deterministic public ingest path)
  - `0de9054` (first derived weekly slice)
  - `00a43ee` (weekly factory; W2–W3 raw support additions)
  - `c0fcbea` (coverage through W6; W4–W6 raw support additions)
