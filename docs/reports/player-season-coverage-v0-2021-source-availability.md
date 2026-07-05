# Source-Availability Report: `player_season_coverage_v0` — 2021 REG

- **Status:** `blocked_pending_source_access` — **not** a completed source-availability finding.
- **Tracking issue:** TIBER-Data #198
- **Forecast context (not source authority):** Prometheus-Frameworks/TIBER-Forecast#133, #134 (merged `2517270`)
- **Scope:** season 2021, season_type REG, positions QB/RB/WR/TE, approved source family only
  (`nflreadpy.load_player_stats`, `nflreadpy.load_players`).

## What this report is and is not

This report is evidence only. It is **not** a candidate artifact, **not** a promoted
artifact, and does not authorize any Forecast behavior. It also does **not** claim
2021 source availability was assessed — the inspection could not run. See below.

## Inspection tooling (written and tested, not yet run against real data)

- `scripts/inspect_player_season_coverage_2021_source_availability.py` — a
  non-promotional inspection script targeting `nflreadpy.load_player_stats`
  (`week` and `reg` summary levels) and `nflreadpy.load_players()` for season 2021,
  `REG`, QB/RB/WR/TE. It writes exactly the two report files at this path pair and
  emits one decision from the allowed set in #198.
- `tests/test_inspect_player_season_coverage_2021_source_availability.py` — 8 unit
  tests exercising the assessment/decision logic against synthetic fake frames
  (no network). All 8 pass. **These tests validate the logic only; they are not a
  substitute for running the script against real 2021 source data**, and this
  report does not treat them as one.

## Why this report is blocked

The approved source family for `player_season_coverage_v0` is `nflreadpy`, which
downloads season data from GitHub release assets under
`github.com/nflverse/nflverse-data`. This session's GitHub access is currently
scoped to `Prometheus-Frameworks/TIBER-Data` and `Prometheus-Frameworks/TIBER-Forecast`
only. Every attempt to reach the nflverse-data source returns HTTP 403:

```text
GitHub access to this repository is not enabled for this session. Use add_repo to request access.
```

Repeated `add_repo(owner="nflverse", repo="nflverse-data")` calls from inside this
session fail with `MCP tool call requires approval` / `Tool permission stream closed
before response received` and never complete — the approval step cannot be resolved
from within the session itself.

### Required external source access

| field | value |
|---|---|
| Required repo/source | `nflverse/nflverse-data` |
| Purpose | public release parquet assets (e.g. `stats_player_week_2021.parquet`) that `nflreadpy` downloads from GitHub releases |
| Reason | needed only for this 2021 source-availability inspection — same approved source family already used for the promoted 2022-2025 artifact, for one additional season |
| Current blocker | MCP `add_repo` approval cannot complete from this session |

### What was explicitly NOT done to work around this

- No vendoring or hand-copying of `nflverse-data` parquet/CSV files into this repo.
- No substitution of a different, non-approved source for 2021 data.
- No change to the `player_season_coverage_v0` source boundary to route around the block.
- No fabricated or estimated 2021 counts.
- The synthetic-fake-frame unit tests are not presented as a completed source check.

## Decision

```text
player_season_coverage_2021_source_feasibility_inconclusive_requires_followup
```

- **Basis:** the inspection could not run because the approved source family is
  blocked at the environment/session level, not because of any TIBER-Data source
  or governance finding. No conclusion about 2021 feasibility can be drawn yet.

### Explicitly NOT emitted / NOT authorized by this report

- `may_open_player_season_coverage_2021_candidate_build_issue`
- `player_season_coverage_2021_source_unavailable_blocks_additional_validation`
- `player_season_coverage_2021_requires_source_boundary_redesign`
- promotion of any artifact
- Forecast mirror refresh, Forecast controlled rerun
- player-history threshold acceptance, leakage audit, model wiring / `seasonalPprModel.ts` changes

## Next step

Once `nflverse/nflverse-data` access is granted to a session with write access to
this branch, run:

```bash
python3 scripts/inspect_player_season_coverage_2021_source_availability.py
```

This overwrites this report with real 2021 REG row/player counts by position,
schema-compatibility findings against the 2022-2025 builder, identity/age/draft
join rates from `load_players()`, and one of the three substantive decisions
(candidate-build-authorized / source-unavailable / requires-redesign) in place of
this inconclusive placeholder.
