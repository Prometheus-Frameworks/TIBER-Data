# Forge canonical gold sample artifacts

This directory holds canonical handoff artifacts for `ForgeWeeklyPlayerInput` exports from TIBER-Data.

Current sample artifact:

- `forge_weekly_player_input_2025_w12.sample.json`
  - contract namespace/version: `src/contracts/v1/forgeWeeklyPlayerInput.ts`
  - represented scope: season `2025`, week `12`, asOf `2026-03-18T12:00:00Z`
  - source set id: `forge-weekly-input-fixtures-v1`
  - deterministic fixture-derived sample; **not** a live production weekly feed

Current derived artifact slices:

- `forge_weekly_player_input_2024_w01.qb_offline_fixture.derived.json`
  - represented scope: season `2024`, week `1`, QB-only cohort
  - source inputs (repo-held support artifacts):
    - `data/raw/forge/weekly_player_stats.offline_fixture.json`
    - `data/raw/forge/team_week_context.offline_fixture.json`
  - directly mapped fields: identity, scope, rush/pass usage, team points proxy
  - explicit gaps/defaults for now: spread/opponent matchup context uses neutral placeholders and route participation for QB remains unavailable, with quality flags
  - narrow sanity-check derived slice, **not** full weekly production parity

- repeatable broader skill-position weekly derived artifacts:
  - `forge_weekly_player_input_2024_w01.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w02.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w03.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w04.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w05.skill_offline_fixture.derived.json`
  - `forge_weekly_player_input_2024_w06.skill_offline_fixture.derived.json`
  - represented artifact availability: season `2024`, weeks `W1-W6` from committed repo-held raw support data
  - reproducible fixture support: W1 only from current `src/ingest/public.py::FIXTURE_DATA`
  - provenance note: W2–W6 support rows are committed legacy repo-held artifacts pending full provenance reconstruction; they are not promoted as fixture-reproducible or source-backed support
  - attempted target for this expansion lane remains `W1-W17`, but current offline support sources stop at `W6`; no new upstream sources were introduced in this repo
  - current provenance manifest: `data/forge_weekly_offline_support_provenance_manifest.json`
  - W2–W6 gap audit: `docs/data/forge-weekly-w2-w6-provenance-gap-audit-2026-05-16.md`
  - intended use: backward-compatible weekly artifact factory pattern for FORGE ingestion sanity checks, with W2-W6 labeled legacy for provenance purposes
  - explicit checks per generated week: non-empty artifact, coherent source metadata (`sourceSetId`/season/week), deterministic ordering, expected positions from source support, and schema validation
  - explicit gaps/defaults for now: snaps/snapShare remain opportunity-based approximations, route fields are lightweight target-share approximations for non-QB rows, and spread/matchup remain neutral/defaulted with quality flags
  - still an offline-fixture-backed constrained season-segment export path, **not** full-season production ETL parity


- repeatable upstream-backed scaffold derived skill artifacts (parallel lane, no legacy replacement):
  - `forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.derived.json`
  - `forge_weekly_player_input_2024_w02.skill_upstream_public_w01_w03_8player_scaffold.derived.json`
  - `forge_weekly_player_input_2024_w03.skill_upstream_public_w01_w03_8player_scaffold.derived.json`
  - represented scope: season `2024`, weeks `W1-W3` only, fixed ATL/DET 8-player scaffold cohort
  - source inputs (upstream-backed scaffold support artifacts):
    - `data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.json`
    - `data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.json`
  - transformation path intentionally reuses the same skill derived logic as the legacy lane; only support provenance differs
  - fail-closed behavior: generation errors if upstream scaffold support is missing/incomplete for W1–W3
  - intended use: side-by-side derived-row sanity checks (for example Amon-Ra St. Brown across W1–W3), **not** full migration

- proof/reference snapshot derived artifacts (stable review baseline lane when committed):
  - `forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json`
  - `forge_weekly_player_input_2024_w02.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json`
  - `forge_weekly_player_input_2024_w03.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json`
  - promotion flow is manual via `scripts/promote_forge_weekly_upstream_proof_snapshot.py`
  - if these files are absent, the lane is defined but not yet populated in-repo
  - this snapshot lane preserves a bounded in-repo specimen for audit/review; it does **not** replace legacy, does not cover W4-W6, and does not imply broader coverage
