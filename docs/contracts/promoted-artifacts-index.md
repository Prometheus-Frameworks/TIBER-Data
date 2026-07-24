# Promoted Artifacts Index

This page inventories the files committed under `exports/promoted/**`. It is a
navigation aid, not an artifact contract, promotion decision, or source of new
support claims.

> `exports/promoted/` is a location, not itself a provenance guarantee.
> Artifact fields, row-level source labels, manifests, schemas, and the linked
> documentation remain the evidence for each file's actual state.

Inventory basis: TIBER-Data `main` at
`85f8a46b924d2e051729b78af25fcfc5b677ba69`, reviewed 2026-07-24.

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
| [`exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json`](../../exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json) | Operator-verified seed mappings; explicitly not full player-universe coverage | `v1` | Not seasonal; 25 mappings for the `sleeper` namespace | TIBER-Data | [Identity crosswalk documentation](../data/tiber-identity-crosswalk-v1.md); [schema](../../schemas/tiber_identity_crosswalk_v1.schema.json) |
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
| [`exports/promoted/player_ownership/player_ownership_latest.json`](../../exports/promoted/player_ownership/player_ownership_latest.json) | Mixed snapshot: source-backed but provisional/stale, with one fixture-backed row | `player_ownership_v0` | 27 players observed from a 2025 week-18 roster snapshot and 2026 draft facts; not current or full-universe truth | TIBER-Data | [Player ownership contracts](player-ownership-v0.md); [availability audit](../audits/player-availability-season-coverage-forecast-readiness-2026-06-30.md) |
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
