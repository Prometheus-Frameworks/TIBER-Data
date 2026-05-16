# FORGE weekly W2-W6 provenance gap audit (2026-05-16)

## What was checked

This audit checked the current FORGE weekly support lanes that can affect the 2024 weekly derived artifacts:

- `src/ingest/public.py::FIXTURE_DATA`
- `scripts/export_forge_weekly_upstream_support_scaffold.py`
- `src/ingest/forge_weekly_upstream_support_scaffold.py`
- `data/raw/forge/weekly_player_stats.offline_fixture.json`
- `data/raw/forge/team_week_context.offline_fixture.json`
- `data/raw/forge/*.proof_reference_snapshot.json`
- `data/gold/forge/*.skill_offline_fixture.derived.json`
- `data/gold/forge/*.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json`
- `data/forge_weekly_upstream_w01_w03_atl_det_proof_reference_snapshot_manifest.json`
- `data/forge_weekly_offline_support_provenance_manifest.json`

## Result

The W2-W6 offline fixture lane cannot honestly be regenerated from current repo-held fixture truth or current committed upstream-backed support artifacts.

What is reproducible now:

- **Offline fixture lane:** 2024 W1 only is reproducible from `src/ingest/public.py::FIXTURE_DATA`.
- **Separate upstream proof/reference lane:** 2024 W1-W3 for the fixed ATL/DET 8-player proof cohort are committed as upstream-backed proof/reference snapshots.

What remains legacy or blocked:

- **Offline fixture W2-W6:** committed repo-held support artifacts only; not fixture-reproducible from the current `FIXTURE_DATA` block.
- **Upstream-backed W4-W6:** blocked in this repo because no committed upstream-backed W4-W6 support artifacts or proof/reference snapshots exist.
- **Migration/replacement:** blocked until a deliberate upstream-backed W4-W6 support slice is added and validated without offline fallback or fabricated rows.

## Boundary now documented

The repo may continue to use committed W2-W6 offline fixture artifacts for backward-compatible engine sanity checks, but those weeks are labeled legacy/repo-held/non-promoted for provenance purposes. They are not promoted as fully reproducible source-backed support.

The upstream proof/reference W1-W3 lane remains a separate audit specimen. It narrows the proof-of-path but does not close the full W2-W6 offline provenance gap.

## Validation commands

Use these checks to validate the current state:

```bash
pytest tests/test_forge_offline_support_provenance.py tests/test_forge_weekly_upstream_support_scaffold.py
```

```bash
npm run test -- --run test/forgeWeeklyDerivedArtifact.export.test.ts
```

The live upstream scaffold command remains fail-closed and requires public-source reads with offline fallback disabled:

```bash
python scripts/export_forge_weekly_upstream_support_scaffold.py
```

In an environment where public reads are unavailable, that command should fail rather than silently falling back to offline fixtures.
