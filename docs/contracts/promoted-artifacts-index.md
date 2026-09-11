# Promoted Artifacts Index

This page inventories the files committed under `exports/promoted/**`. It is a
navigation aid, not an artifact contract, promotion decision, or source of new
support claims.

> `exports/promoted/` is a location, not itself a provenance guarantee.
> Artifact fields, row-level source labels, manifests, schemas, and the linked
> documentation remain the evidence for each file's actual state.

Inventory basis: committed artifacts in this revision, updated 2026-09-10 for
PR #268's three-row Team admission/promotion preparation on the review branch,
following PR #266's four-row Draft Review extension. This is not a production
activation record.

## Reading the index

- **Observed declaration** reports only states explicitly present in the file
  or its linked repository documentation.
- **Observed support window** describes committed rows, not implied support
  beyond them.
- **Producer** names a repository only when existing provenance, ownership
  documentation, or a repository-local generator identifies it. Otherwise it
  is `unknown`.
- `unknown` means the current repository evidence does not prove a value. It
  must not be filled by inference from the directory name or nearby artifacts.
- Several array payloads do not carry an artifact-level version or status
  envelope. For those rows, the version comes from the canonical path and
  linked versioned documentation, while the observed state comes from row-level
  fields and the linked scope statement.

## Committed files

| Committed path | Observed declaration | Version | Observed support window | Producer | Evidence |
| --- | --- | --- | --- | --- | --- |
| [`exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json`](../../exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json) | Frozen operator-verified seed mappings; explicitly not full player-universe coverage; retained as the contract of record for consumers that have not migrated identifier vocabularies | `v1` (frozen; not replaced by `v2`) | Not seasonal; 25 mappings for the `sleeper` namespace | TIBER-Data | [Identity crosswalk documentation](../data/tiber-identity-crosswalk-v1.md); [schema](../../schemas/tiber_identity_crosswalk_v1.schema.json) |
| [`exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json`](../../exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json) | GSIS-vocabulary slice with four previously accepted Draft Review additions and three `name_exact`/medium Team additions prepared on the review branch; explicitly not full player-universe coverage; not interchangeable with the v1 identifier vocabulary | `v2` | Not seasonal; 75 `sleeper` mappings on this branch: 23 `gsis_direct`, 6 `espn_bridge`, 46 `name_exact` | TIBER-Data | Artifact fields/source-artifact digests; promotion PR #244; [four-row admission receipt](../../exports/promoted/draft_review/evidence_admission_v1.json); [three-row branch receipt](../../exports/promoted/draft_review/team_identity_admission_v1.json) |
| [`exports/promoted/draft_review/evidence_admission_v1.json`](../../exports/promoted/draft_review/evidence_admission_v1.json) | `accepted` receipt for four exact `name_exact`/medium identity rows and bounded historical descriptive use by TIBER-Fantasy Draft Review / issue #360; no forecast, refresh, merge or production-deployment grant | `draft_review_evidence_admission_v1` | Authorized descriptive window: 2025 weeks 1–18; recorded-week coverage and missing values remain source-bound, with source acquisition/update clocks `null` and attribution required | TIBER-Data | [Immutable reviewed proposal](https://github.com/Prometheus-Frameworks/TIBER-Data/blob/e08e5cb8f8c3c71441e62755fb87c9514ce1b249/docs/audits/draft-review-evidence-admission-2026-09-07.md); [operator acceptance](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/264#issuecomment-5574349251); receipt's pinned proposal/source hashes |
| [`exports/promoted/draft_review/team_identity_admission_v1.json`](../../exports/promoted/draft_review/team_identity_admission_v1.json) | `accepted_for_branch_preparation` for exactly Parker Washington, Drake London and Chris Rodriguez; unchanged bounded historical scope; no consumer regeneration, merge, deployment or release authority | `team_identity_admission_v1` | 2025 weeks 1–18, observed denominators 16/12/12; medium confidence; excluded week 19 and candidate/historical team distinction retained | TIBER-Data | [Preparation audit](../audits/team-identity-admission-2026-09-10.md); exact proposal/review/authorization and source pins in separate receipt |
| [`exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json`](../../exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json) | Promotion manifest for a `promoted_governed_artifact`; validation declared `passed` | `player_season_coverage_v0_promoted_v1` | 2021-2025, `REG`; manifest reports 3,016 records | TIBER-Data | [Promoted schema](../../schemas/player_season_coverage_v0_promoted.schema.json); [promotion-resume report](../reports/player-season-coverage-v0-2021-2025-promotion-resume.md) |
| [`exports/promoted/nfl/player_season_coverage_v0.json`](../../exports/promoted/nfl/player_season_coverage_v0.json) | `promoted_governed_artifact` | `player_season_coverage_v0_promoted_v1` | 2021-2025, `REG`; 3,016 player-season records | TIBER-Data | [Promoted schema](../../schemas/player_season_coverage_v0_promoted.schema.json); [promotion-resume report](../reports/player-season-coverage-v0-2021-2025-promotion-resume.md) |
| [`exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`](../../exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json) | Offline-fixture scaffold; every row names the offline fixture source | `v1` | 2025 weeks 1-3; 6 rows | TIBER-Data | [Artifact documentation](../data/player-weekly-ppr-outcomes-v1.md) |
| [`exports/promoted/nfl/player_weekly_usage_v1.json`](../../exports/promoted/nfl/player_weekly_usage_v1.json) | Offline-fixture scaffold; every row names the offline fixture source | `v1` | 2025 weeks 1-3; 6 rows | TIBER-Data | [Artifact documentation](../data/player-weekly-usage-v1.md) |
| [`exports/promoted/nfl/roster_player_team_map_v1.json`](../../exports/promoted/nfl/roster_player_team_map_v1.json) | Offline-fixture scaffold; rows declare `source_status: offline_fixture` | `v1` | 2025 week 1; 5-player bounded cohort | TIBER-Data | [Artifact documentation](../data/roster-player-team-map-v1.md) |
| [`exports/promoted/nfl/team_offense_summary_v1.json`](../../exports/promoted/nfl/team_offense_summary_v1.json) | Offline-fixture scaffold; every row names the offline fixture source | `v1` | 2025; 3 teams (`ARI`, `LV`, `TB`) | TIBER-Data | [Artifact documentation](../data/team-offense-summary-v1.md) |
| [`exports/promoted/nfl/team_pace_pass_environment_v1.json`](../../exports/promoted/nfl/team_pace_pass_environment_v1.json) | Offline-fixture scaffold; every row names the offline fixture source | `v1` | 2025; 3 teams (`ARI`, `LV`, `TB`) | TIBER-Data | [Artifact documentation](../data/team-pace-pass-environment-v1.md) |
| [`exports/promoted/nfl_draft_results/nfl_draft_results_2026.json`](../../exports/promoted/nfl_draft_results/nfl_draft_results_2026.json) | Source-backed promoted draft facts; rows declare `source_verified` or `source_verified_player_id_unresolved` | `v1` | 2026 NFL Draft; 257 picks | TIBER-Data | [NFL Draft results documentation](../data/nfl-draft-results-v1.md) |
| [`exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl`](../../exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl) | Fixture scaffold; one provisional event names `fixture_demonstration_only` | `player_ownership_change_event_v0` | One event effective 2026-03-14 | TIBER-Data | [Player ownership contracts](player-ownership-v0.md); [event schema](../../schemas/player_ownership_change_event_v0.schema.json) |
| [`exports/promoted/player_ownership/player_ownership_aliases.json`](../../exports/promoted/player_ownership/player_ownership_aliases.json) | Alias seed; no artifact-level provenance state is declared | `player_ownership_aliases_v0` | Not seasonal; 4 aliases | `unknown` | [Alias schema](../../schemas/player_ownership_aliases_v0.schema.json); [availability audit](../audits/player-availability-season-coverage-forecast-readiness-2026-06-30.md) |
| [`exports/promoted/player_ownership/player_ownership_latest.json`](../../exports/promoted/player_ownership/player_ownership_latest.json) | Mixed snapshot: source-backed but provisional/stale, with one fixture-backed row | `player_ownership_v0` | 27 players: 19 from 2025 roster observations (4 week 18, 8 week 19, 5 week 20, 2 week 22), 7 from 2026 draft facts, and 1 fixture row; not current or full-universe truth | TIBER-Data | [Player ownership contracts](player-ownership-v0.md); [availability audit](../audits/player-availability-season-coverage-forecast-readiness-2026-06-30.md) |
| [`exports/promoted/point_prediction_model/point_prediction_scenario_export_v1.fixture.json`](../../exports/promoted/point_prediction_model/point_prediction_scenario_export_v1.fixture.json) | `fixture_only`; explicitly no production projection or real scenario coverage claim | `tiber-data.point-prediction-scenario-export.v1.0.0` | 2026 week 1; 2 fixture rows | Point-prediction-model fixture lane | [Scenario export contract](point-prediction-scenario-export-v1.md) |
| [`exports/promoted/rookie-replay/historical_rookie_replay_readiness_v0.json`](../../exports/promoted/rookie-replay/historical_rookie_replay_readiness_v0.json) | Offline fixture/scaffold join-readiness audit; not a scoring or projection artifact | `v0` | 2025 replay; 3-player cohort using roster week 1 | TIBER-Data | [Readiness documentation](../data/historical-rookie-replay-readiness-v0.md) |
| [`exports/promoted/rookie-replay/historical_rookie_replay_v0.json`](../../exports/promoted/rookie-replay/historical_rookie_replay_v0.json) | Offline-fixture scaffold; explicitly not full real 2025 replay coverage | `v0` | 2025 replay; 3-player cohort | TIBER-Data | [Artifact documentation](../data/historical-rookie-replay-v0.md); [contract](history-rookie-replay-v0.md) |

## Known uncertainty

`player_ownership_aliases.json` declares its artifact name, four alias rows, and
row-level builder source strings, but it does not declare an artifact-level
provenance state or producer repository. This index therefore records its
producer as `unknown`.

## Maintenance

Keep this index synchronized in any pull request that adds, removes, or renames
a committed file under `exports/promoted/**`. Updating this page does not, by
itself, promote an artifact or change its contract, support window, provenance,
or downstream availability.
