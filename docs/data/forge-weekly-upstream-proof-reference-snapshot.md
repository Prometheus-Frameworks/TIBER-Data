# FORGE upstream proof/reference snapshot lane (2024 W1–W3 ATL/DET)

This document defines the **proof/reference specimen lane** for the existing upstream-backed FORGE proof slice.

## Scope (strict)

- season: `2024`
- weeks: `1,2,3`
- teams: `ATL`, `DET`
- player cohort: fixed 8-player ATL/DET proof cohort already used by the upstream scaffold lane

This lane is intentionally narrow and does **not** imply:

- full-season support
- production ETL readiness
- replacement of the legacy W2–W6 offline fixture rows or any W4–W6 upstream-backed support

## Lane separation

- Legacy offline lane (unchanged; W1 fixture-reproducible, W2–W6 repo-held legacy):
  - `data/raw/forge/*.offline_fixture.json`
  - `data/gold/forge/*.skill_offline_fixture.derived.json`
- Live upstream scaffold generation lane (unchanged):
  - `data/raw/forge/*.upstream_public_2024_w01_w03_*_scaffold.json`
  - `data/gold/forge/*.skill_upstream_public_w01_w03_8player_scaffold.derived.json`
- Committed proof/reference snapshot lane (target baseline location):
  - `data/raw/forge/*.proof_reference_snapshot.json`
  - `data/gold/forge/*.proof_reference_snapshot.derived.json`
  - `data/forge_weekly_upstream_w01_w03_atl_det_proof_reference_snapshot_manifest.json`

## Deliberate refresh workflow (manual only)

1. Generate/refresh the current upstream scaffold outputs intentionally:
   - `python scripts/export_forge_weekly_upstream_support_scaffold.py`
   - `npm run export:forge-weekly-derived-upstream-scaffold`
2. Promote those generated outputs into the committed proof snapshot lane:

```bash
python scripts/promote_forge_weekly_upstream_proof_snapshot.py --captured-at "2026-04-10T00:00:00Z"
```

3. Review resulting snapshot + manifest diffs before commit.

The current W1–W3 proof/reference files are committed. Future refreshes remain manual by design (no auto-refresh in CI), and any refreshed output should be reviewed before commit.

## Review baseline guidance

- Use the committed proof snapshot lane when reviewers need a stable in-repo baseline.
- Use the live upstream scaffold lane when intentionally re-checking source behavior before a deliberate re-baseline.
- Keep truth-arbitration claims bounded to this proof slice unless a broader audited scope is explicitly added.
