# Operator Signal Note v0 Contract

## Status and scope

`operator_signal_note_v0` is the first lightweight contract for turning operator-entered football notes into structured, inspectable reasoning artifacts for downstream TIBER systems.

This contract is documentation and schema only. It does **not** introduce a runtime parser, UI, ranking engine, inference pipeline, machine-learning component, or autonomous decision system.

## Purpose

Operator notes may contain observations such as EPA on/off splits, route participation changes, red-zone catchable target rates, division strength context, environmental changes, efficiency anomalies, or usage shifts. The purpose of this contract is to preserve those notes as structured signals that can be inspected, challenged, and verified before downstream use.

The artifact records what the operator note appears to claim, what entities and metrics were detected, what hypotheses might be worth checking, and what must **not** happen automatically.

## Stress Lab Philosophy

TIBER is testing reasoning integrity, not just outputs. A freeform football note should become an inspectable structured signal while preserving contact with the original text and with source reality.

Stress Lab and Reasoning Sandbox workflows should increase autonomy only when they also increase auditability. The system may organize observations into hypotheses, follow-ups, uncertainties, and explicit non-application rules; it must not convert a note into hidden truth, silent ranking movement, or fabricated context.

## Reasoning posture

`operator_signal_note_v0` artifacts are hypothesis and signal extraction records. They are not source-of-truth football datasets.

Required posture:

- Operator notes generate hypotheses, not truth.
- Inspectability is preferred over automation.
- No downstream ranking mutation is allowed by default.
- No context may be invented to complete a story.
- Uncertainty must be preserved in the artifact.
- Downstream repositories must verify source truth before applying any ranking, projection, recommendation, or decision change.
- Missing source truth must reduce scope rather than encourage fabricated continuity.

## Canonical schema

Schema file: `schemas/operator_signal_note_v0.schema.json`

The schema describes a single operator signal note artifact. A collection format may be added later, but this contract intentionally starts with one inspectable note at a time.

## Core fields

| Field | Type | Requirement | Meaning |
| --- | --- | --- | --- |
| `note_id` | string | required | Stable identifier for the note artifact. |
| `source_type` | string | required | Origin class of the note, such as `operator_entered_note`. |
| `raw_note` | string | required | Exact freeform note text entered by the operator. |
| `created_at` | string | required | ISO-8601 timestamp for artifact creation. |
| `entities` | array | required | Detected football entities from the raw note. |
| `detected_metrics` | array | required | Metrics detected or normalized from the raw note. |
| `signal_tags` | array | required | Inspectable tags for downstream triage. |
| `reasoning_status` | string | required | Current reasoning posture for the artifact. |
| `required_followups` | array | required | Checks required before downstream application. |
| `do_not_apply` | array | required | Explicit actions downstream systems must not take from this artifact alone. |
| `uncertainty` | array | required | Preserved ambiguity, missing context, or verification gaps. |
| `interpretation_summary` | string | required | Short human-readable summary of the extracted hypothesis. |

## Entity support

The contract supports, at minimum, these entity types:

- `player`
- `team`
- `division`
- `season`

Entities should remain literal and inspectable. If the note says `San Francisco 49ers [2025]`, the artifact may identify a `team` entity and a `season` entity. It must not infer missing opponent, week range, player availability source, or schedule context unless present in the note or verified elsewhere.

## Metric support

Each detected metric supports:

- `metric`
- `value`
- `unit`
- `context`
- `confidence`
- `sample_filter`

Allowed metric names are intentionally generic strings so the contract can represent football notes without prematurely freezing every possible football statistic. Examples include:

- `catchable_target_rate`
- `epa_per_play`
- `route_participation`
- `target_share`
- `pressure_rate`

`confidence` describes extraction confidence, not truth confidence. A clear operator note can have high extraction confidence while still requiring source verification.

## Reasoning statuses

Suggested `reasoning_status` values:

- `hypothesis_only` — extracted as a possible signal; not verified for application.
- `requires_followup` — cannot be interpreted safely without named checks.
- `source_verified_signal` — source truth has been verified outside this contract, but downstream application is still not automatic.
- `rejected_or_out_of_scope` — note cannot be represented honestly or belongs outside this repo.

## Non-application rule

Every artifact must include `do_not_apply`. This field is a safety rail for downstream systems. It should explicitly prevent automatic ranking mutation, projection changes, lineup recommendations, or decision automation from a note alone.

## Example artifacts

The examples below are illustrative contract artifacts for the provided operator notes. They are not promoted source-truth rows and must not be treated as verified football facts without external validation.

### Example 1: 49ers EPA on/off split

Raw note:

```text
San Francisco 49ers [2025]
w/ CMC on the field: 0.157 EPA/Play
w/out CMC: 0.061
Delta: +157%
```

Artifact:

```json
{
  "note_id": "operator-note-example-49ers-cmc-epa-2025",
  "source_type": "operator_entered_note",
  "raw_note": "San Francisco 49ers [2025]\nw/ CMC on the field: 0.157 EPA/Play\nw/out CMC: 0.061\nDelta: +157%",
  "created_at": "2026-05-07T00:00:00Z",
  "entities": [
    {
      "entity_type": "team",
      "name": "San Francisco 49ers",
      "raw_text": "San Francisco 49ers"
    },
    {
      "entity_type": "season",
      "value": 2025,
      "raw_text": "[2025]"
    },
    {
      "entity_type": "player",
      "name": "CMC",
      "raw_text": "CMC"
    }
  ],
  "detected_metrics": [
    {
      "metric": "epa_per_play",
      "value": 0.157,
      "unit": "epa_per_play",
      "context": "San Francisco offense with CMC on the field",
      "confidence": "high_extraction_unverified_source",
      "sample_filter": "with CMC on field"
    },
    {
      "metric": "epa_per_play",
      "value": 0.061,
      "unit": "epa_per_play",
      "context": "San Francisco offense without CMC on the field",
      "confidence": "high_extraction_unverified_source",
      "sample_filter": "without CMC on field"
    },
    {
      "metric": "epa_per_play_delta_percent",
      "value": 157,
      "unit": "percent",
      "context": "Operator-stated EPA/play delta between with-CMC and without-CMC samples",
      "confidence": "high_extraction_unverified_source",
      "sample_filter": "with CMC on field vs without CMC on field"
    }
  ],
  "signal_tags": [
    "epa_on_off_split",
    "player_availability_context",
    "team_efficiency_anomaly_candidate"
  ],
  "reasoning_status": "requires_followup",
  "required_followups": [
    "Verify source calculation for EPA/play splits and delta percentage.",
    "Confirm CMC identity resolution and on-field sample definition.",
    "Check sample size, game state filters, opponent mix, and season/week coverage before applying interpretation."
  ],
  "do_not_apply": [
    "Do not mutate team, player, or matchup rankings from this note alone.",
    "Do not assume causality between CMC presence and EPA/play without verified controls.",
    "Do not extend the 2025 support window beyond verified source coverage."
  ],
  "uncertainty": [
    "The raw note does not provide sample size, source, week range, game state, or opponent context.",
    "The abbreviation CMC requires identity confirmation before use.",
    "The delta is operator-stated and must be recalculated against source data."
  ],
  "interpretation_summary": "The operator note suggests a possible 2025 San Francisco EPA/play on/off efficiency signal tied to CMC presence, but it remains a hypothesis requiring source, sample, and context verification."
}
```

### Example 2: NFC North non-division win percentage

Raw note:

```text
best division in the NFL
(win % in non-division games last 4 years)
58.8% NFC North
```

Artifact:

```json
{
  "note_id": "operator-note-example-nfc-north-nondivision-win-rate",
  "source_type": "operator_entered_note",
  "raw_note": "best division in the NFL\n(win % in non-division games last 4 years)\n58.8% NFC North",
  "created_at": "2026-05-07T00:00:00Z",
  "entities": [
    {
      "entity_type": "division",
      "name": "NFC North",
      "raw_text": "NFC North"
    }
  ],
  "detected_metrics": [
    {
      "metric": "non_division_win_percentage",
      "value": 58.8,
      "unit": "percent",
      "context": "Operator-stated NFC North win percentage in non-division games over the last 4 years",
      "confidence": "high_extraction_unverified_source",
      "sample_filter": "non-division games, last 4 years"
    }
  ],
  "signal_tags": [
    "division_strength_context",
    "schedule_context_candidate",
    "multi_year_sample"
  ],
  "reasoning_status": "requires_followup",
  "required_followups": [
    "Define the exact four-season window represented by 'last 4 years'.",
    "Verify the non-division game set and win percentage source calculation.",
    "Compare against all other divisions before preserving or rejecting the 'best division' label."
  ],
  "do_not_apply": [
    "Do not automatically upgrade NFC North teams or players from this note alone.",
    "Do not treat 'best division in the NFL' as verified until comparative source truth is checked.",
    "Do not infer current-season strength from a multi-year aggregate without recency validation."
  ],
  "uncertainty": [
    "The note does not specify the exact seasons in the four-year window.",
    "The comparative ranking against other divisions is not included.",
    "The source and treatment of ties, playoffs, neutral sites, or schedule changes are not provided."
  ],
  "interpretation_summary": "The operator note suggests an NFC North division-strength context signal based on a 58.8% non-division win rate over an unspecified four-year window, requiring source and comparison checks before use."
}
```

### Example 3: Justin Jefferson red-zone catchable target rate

Raw note:

```text
Lowest Catchable Target Rates in the Red Zone
JUSTIN JEFFERSON [2025] - 50.0%
```

Artifact:

```json
{
  "note_id": "operator-note-example-justin-jefferson-red-zone-catchable-rate-2025",
  "source_type": "operator_entered_note",
  "raw_note": "Lowest Catchable Target Rates in the Red Zone\nJUSTIN JEFFERSON [2025] - 50.0%",
  "created_at": "2026-05-07T00:00:00Z",
  "entities": [
    {
      "entity_type": "player",
      "name": "Justin Jefferson",
      "raw_text": "JUSTIN JEFFERSON"
    },
    {
      "entity_type": "season",
      "value": 2025,
      "raw_text": "[2025]"
    }
  ],
  "detected_metrics": [
    {
      "metric": "catchable_target_rate",
      "value": 50.0,
      "unit": "percent",
      "context": "Operator-stated catchable target rate in the red zone for Justin Jefferson in 2025",
      "confidence": "high_extraction_unverified_source",
      "sample_filter": "red-zone targets"
    }
  ],
  "signal_tags": [
    "red_zone_usage_context",
    "catchable_target_rate_low_candidate",
    "possible_td_positive_regression_candidate"
  ],
  "reasoning_status": "requires_followup",
  "required_followups": [
    "Verify red-zone target sample size and catchable-target charting source.",
    "Check quarterback accuracy, quarterback availability, offensive environment, play caller, and route usage context.",
    "Compare expected touchdown opportunity only after source truth and environment checks are complete."
  ],
  "do_not_apply": [
    "Do not declare automatic positive touchdown regression from this note alone.",
    "Do not mutate player rankings, projections, or recommendations without verified source truth.",
    "Do not assume low catchable target rate is independent of player role, route type, defensive context, quarterback play, or sample size."
  ],
  "uncertainty": [
    "The raw note does not include target count, charting definition, quarterback context, or game/week coverage.",
    "The 'lowest' label implies a comparison set that is not provided in the note.",
    "The signal may indicate quarterback/environment friction, role context, sample noise, or a touchdown opportunity hypothesis; the artifact does not choose among them."
  ],
  "interpretation_summary": "The operator note identifies Justin Jefferson as a possible red-zone catchable-target-rate signal and may be tagged as a possible TD positive regression candidate, but the artifact explicitly preserves uncertainty and requires quarterback/environment follow-up before any application."
}
```

## Boundary for future work

Future work may add parser implementations, validation fixtures, collections, or Stress Lab workflows. Those additions must remain contract-safe: no invented source data, no silent ranking mutations, no unsupported coverage expansion, and no hidden inference pipelines.
