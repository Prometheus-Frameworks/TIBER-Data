# Candidate-Build Report: `player_season_coverage_v0` — 2021 Extension

- **Generated at:** 2026-07-06T03:13:21.402017+00:00
- **Tracking issue:** TIBER-Data#200
- **Status:** `candidate_build_evidence_report_not_an_artifact`
- **Candidate path:** `data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json`
- **Scope:** this report is evidence only. It is not a promoted artifact and authorizes no Forecast behavior; the only positive outcome it can authorize is a follow-up promotion-review issue.

## Candidate summary

- sha256: `55618590d4a1f6affa8228d32d61b9baa0d66552448811c06136ca6139a7eef4`
- artifact_id: `player_season_coverage_2021_candidate.source_backed`
- status field: `candidate_evidence_artifact_not_promoted`
- seasons: [2021]
- season_type_scope: ['REG']
- included_positions: ['QB', 'RB', 'TE', 'WR']
- total records: 633
- identity join rate: 1.0

### Row counts by position

| position | count |
|---|---|
| QB | 81 |
| RB | 165 |
| WR | 256 |
| TE | 131 |

### Coverage status distribution

- `full_season`: 162
- `single_week`: 68
- `partial_season`: 403

## Reconciliation against #198 source-availability finding

| position | #198 source-availability count | candidate count | match |
|---|---|---|---|
| QB | 81 | 81 | yes |
| RB | 165 | 165 | yes |
| WR | 256 | 256 | yes |
| TE | 131 | 131 | yes |

- Overall match: **True**

## Validation

PASSED: schema + business-rule validation (`scripts/validate_player_season_coverage_v0.py`).

- No promoted path written: **True**

## Decision

```text
may_open_player_season_coverage_2021_promotion_review_issue
```

- Basis: Candidate passed schema/business-rule validation and row counts reconcile exactly with the #198 source-availability finding for all four positions.

### Explicitly NOT emitted / NOT authorized by this report

- player_season_coverage_2021_candidate_build_failed_source_or_schema_check
- player_season_coverage_2021_candidate_build_requires_source_boundary_redesign
- player_season_coverage_2021_candidate_build_inconclusive_requires_followup
- promotion of any artifact
- Forecast mirror refresh
- Forecast controlled rerun
- player-history threshold acceptance
- leakage audit
- model wiring / seasonalPprModel.ts changes

This report is evidence under `docs/reports/`. It does not modify or promote any artifact and does not authorize Forecast behavior; a follow-up TIBER-Data promotion-review issue must explicitly authorize promotion.
