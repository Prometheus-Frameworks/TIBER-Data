# Rookie data inventory

This document tracks reusable rookie artifacts centralized in `TIBER-Data` from `TIBER-Rookies`.

## Centralized seasons

- **2026**: Present
- **Historic seasons**: Not currently centralized in this repository

Historic coverage is intentionally honest: no reusable historic rookie datasets have been imported yet.

## Artifact inventory

| Season | Artifact | Type | Purpose | Pipeline role | Source repo | Path |
|---|---|---|---|---|---|---|
| 2026 | `rookie_2026_promoted_board_v1` | promoted | Current promoted rookie board handoff for downstream repos | downstream_handoff_output | TIBER-Rookies | `data/rookies/2026/promoted/rookie_2026_promoted_board_v1.json` |
| 2026 | `rookie_2026_combine_support_v1` | support | Processed combine support inputs used by rookie pipeline | support_data | TIBER-Rookies | `data/rookies/2026/support/rookie_2026_combine_support_v1.csv` |
| 2026 | `rookie_2026_draft_capital_proxy_v1` | processed | Draft-capital proxy scores for rookie pipeline features | authoritative_input | TIBER-Rookies | `data/rookies/2026/processed/rookie_2026_draft_capital_proxy_v1.csv` |
| 2026 | `rookie_2026_college_production_processed_v1` | processed | Processed college production features for rookie candidates | authoritative_input | TIBER-Rookies | `data/rookies/2026/processed/rookie_2026_college_production_processed_v1.csv` |

## Retrieval guidance for future repos

Consumers that need reusable rookie artifacts should retrieve from `TIBER-Data` first.

- Use `data/rookies/artifact-index.json` for machine-readable discovery.
- Use this inventory for human-readable audit and provenance.

## What remains in TIBER-Rookies

The following remain outside this repository by design:

- rookie model logic
- UI and prototype surfaces
- queue/browser-local state
- lab-only presentation and component code

`TIBER-Data` intentionally stores durable rookie artifacts only.
