# Point-prediction scenario export v1 contract

`point-prediction-scenario-export.v1` is the pinned TIBER-Data-owned output contract for Point-prediction-model scenario exports consumed by Point Scenario Lab in TIBER-Fantasy.

## Contract authority

- **TIBER-Data owns** the canonical output shape, version literal, field requirements, promoted artifact semantics, fixture, and conformance check.
- **Point-prediction-model emits** scenario output against this pinned contract and must preserve `contract_version: "tiber-data.point-prediction-scenario-export.v1.0.0"` until a governed TIBER-Data contract revision is published.
- **TIBER-Fantasy consumes read-only** through its adapter edge. Fantasy may keep defensive local normalization, but it must not become the canonical schema authority for this dataset.

This repository did not contain an existing Point-prediction-model scenario export contract before this v1 definition was added. The previous nearby projection-input fixture contract remains a bounded adapter rehearsal input shape, not a producer-owned scenario output contract.

## Canonical implementation and fixture

- TypeScript contract: `src/contracts/v1/pointPredictionScenarioExport.ts`
- Promoted-shape contract fixture: `exports/promoted/point_prediction_model/point_prediction_scenario_export_v1.fixture.json`
- Conformance check: `npm run check:point-prediction-scenario-export`

The committed fixture is `artifact_status: "fixture_only"`. It represents the valid promoted artifact shape without claiming real scenario coverage, real player projections, injury truth, roster truth, or production model output.

## Artifact shape

A scenario export is an envelope with scenario-level metadata and one or more player rows in `rows[]`.

### Top-level fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `contract_version` | yes | literal string | Must be `tiber-data.point-prediction-scenario-export.v1.0.0`. |
| `artifact_status` | yes | enum string | `fixture_only` or `promoted_source_backed`. |
| `scenario_id` | yes | non-empty string | Stable scenario identifier from the producer. |
| `scenario_name` | yes | non-empty string | Human-readable scenario label. |
| `scenario_type` | yes | enum string | One of `injury_absence`, `injury_return`, `role_change`, `depth_chart_change`, `team_environment_change`, `weather`, `custom`. |
| `event_type` | yes | enum string | One of `player_out`, `player_limited`, `player_returning`, `starter_change`, `target_share_shift`, `rush_share_shift`, `pace_shift`, `pass_rate_shift`, `weather_adjustment`, `manual_scenario`. |
| `season` | yes | integer | NFL season represented by the scenario output. |
| `week` | yes | integer | NFL week, 1 through 22. |
| `model_version` | yes | non-empty string | Point-prediction-model version or fixture lane identifier that emitted the artifact. |
| `generated_at` | yes | ISO-8601 date-time string with offset | Producer generation timestamp. |
| `provenance` | yes | object | Required provenance envelope, defined below. |
| `rows` | yes | non-empty array | Player-level scenario projection rows. |

### Provenance fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `source_repo` | yes | literal string | Must be `Point-prediction-model`. |
| `source_artifact` | yes | non-empty string | Producer artifact path, name, or fixture lane identifier. |
| `source_run_id` | no | non-empty string | Optional source run identifier. |
| `source_commit` | no | non-empty string | Optional producer commit identifier. |
| `tiber_data_contract_owner` | yes | literal string | Must be `TIBER-Data`. |
| `emitted_by` | yes | non-empty string | Producer or fixture lane that emitted the artifact. |
| `validated_by` | yes | non-empty string | Validator used for conformance. |
| `notes` | yes | array of non-empty strings | Provenance notes and scope boundaries. |

### Row fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `player.player_id` | yes | non-empty string | Canonical player identity used by TIBER consumers. |
| `player.player_name` | yes | non-empty string | Player display name. |
| `player.source_player_id` | no | non-empty string | Optional producer-local player identifier. |
| `team` | yes | uppercase team code string | Two to four uppercase letters. |
| `position` | yes | enum string | `QB`, `RB`, `WR`, or `TE`. |
| `baseline_projection` | yes | finite number | Baseline fantasy projection before scenario adjustment. |
| `adjusted_projection` | yes | finite number | Scenario-adjusted fantasy projection. |
| `delta` | yes | finite number | Must equal `adjusted_projection - baseline_projection`, rounded to four decimals. |
| `confidence_score` | yes | number | Closed range `0..1`. |
| `confidence_tier` | yes | enum string | `low`, `medium`, or `high`. |
| `confidence_notes` | yes | array of non-empty strings | Confidence rationale or caveats. |
| `explanation` | yes | non-empty string | Human-readable explanation of the scenario adjustment. |
| `notes` | yes | array of non-empty strings | Row-level notes and scope boundaries. |

## Fail-closed behavior

The v1 Zod schema is strict. Unknown fields, missing required fields, unsupported enum values, invalid timestamps, unsupported contract versions, malformed player identity, out-of-range confidence scores, and incorrect `delta` values fail validation.

## Downstream adapter expectations

TIBER-Fantasy should validate the upstream `contract_version` at the Point Scenario adapter edge and surface a clear promoted-status mismatch state when the version is missing or unsupported. Consumer-side field aliases can remain defensive normalization, but they should sit behind this TIBER-Data-owned contract check rather than replacing it.

## Follow-up implementation issues

1. **Point-prediction-model:** emit scenario output with `contract_version: "tiber-data.point-prediction-scenario-export.v1.0.0"` and pass `npm run check:point-prediction-scenario-export` against an emitted artifact.
2. **TIBER-Fantasy:** validate `contract_version` at the Point Scenario adapter edge and show a clear promoted-status mismatch state when the upstream version is missing or unsupported.
