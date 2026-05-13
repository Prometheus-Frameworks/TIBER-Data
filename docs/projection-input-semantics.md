# Projection Input Semantics Viewer

This document introduces a lightweight semantics inspection surface for candidate fields that may eventually feed `Point-prediction-model`.

This is **not ingestion**. It does not create a runtime feed, scoring rule, model feature contract, or downstream wiring. It exists so humans and agents can inspect field meaning, source readiness, and open questions before any projection-input adapter is designed.

## Files

- Registry: `data/semantics/projection_input_semantics.json`
- Viewer / validator: `scripts/inspect_projection_input_semantics.mjs`
- Optional generated view: `docs/projection-input-semantics.generated.md`

## Boundary rules

- Existing data artifacts are not changed by this viewer.
- Candidate entries are not claims of complete field availability.
- `needs_verification` entries must not be consumed as real model inputs.
- Nulls and unavailable values must remain explicit; the viewer must not invent source continuity or fill missing data.
- Downstream consumers named here (`Point-prediction-model`, `FORGE`, `TIBER-Fantasy`) are inspection labels only, not wiring.

## Registry metadata checked by the viewer

Each semantics entry must include:

- `field_group`
- `field_name`
- `description`
- `owner_source`
- `artifact_source_path_if_known`
- `position_relevance`
- `time_scope`
- `semantic_type`
- `nullability_missing_behavior`
- `provenance_expectations`
- `downstream_consumers`
- `consumption_recommendation`
- `status`
- `notes_open_questions`

The viewer fails closed if required metadata is missing, if field names are duplicated, or if enum-style values are outside the allowed inspection vocabulary.

## Usage

Print a compact terminal summary and validate the registry:

```bash
npm run inspect:projection-input-semantics
```

Write the generated markdown view:

```bash
npm run docs:projection-input-semantics
```

Filter examples:

```bash
node scripts/inspect_projection_input_semantics.mjs --status needs_verification
node scripts/inspect_projection_input_semantics.mjs --group opportunity
node scripts/inspect_projection_input_semantics.mjs --consumer Point-prediction-model
```

## High-value usage ownership

High-value fantasy usage fields are inspection semantics only until a governed projection-input adapter exists. TIBER-Data may own factual or derived evidence fields such as red-zone targets per game, red-zone carries per game, inside-10 carries per game, goal-line rushing attempts per game, end-zone targets per game, and player red-zone target share only when the underlying source path, denominator, sample window, and null policy are governed.

Interpretive composites remain outside this repo. `rush_td_opportunity`, touchdown fragility, touchdown regression modifiers, and ceiling/floor adjustments from high-value usage belong in `Point-prediction-model` or another downstream modeling repo because they combine evidence with model judgment. The semantics registry may name those concepts to mark the boundary, but `needs_verification` entries must stay unavailable and not consumed here.

Denominator policy must be explicit before consumption:

- per-game fields must say whether the denominator is active games, games with source coverage, all team games, or another governed sample;
- red-zone target share must use governed player red-zone targets divided by governed team red-zone targets over the same sample, not all team targets or implied attempts;
- route participation and targets per route must preserve route denominator uncertainty until source coverage and route opportunity definitions are documented;
- unavailable high-value usage remains `null` / unavailable, never zero, unless the source row explicitly says the player had zero opportunities.

## Status vocabulary

| status | meaning |
|---|---|
| `supported` | The semantics registry points to current TIBER-Data contracts or evidence docs for the field concept. This still does not imply full-season production coverage. |
| `candidate` | The field is plausible for projection input inspection, but requires adaptation, a denominator/sample-window policy, or source-lane review before consumption. |
| `needs_verification` | The field should not be consumed yet. Source support, formula ownership, denominator semantics, or repo boundary ownership is unresolved. |

## Consumption recommendation vocabulary

| recommendation | meaning |
|---|---|
| `pass_directly` | The field can be inspected as a direct candidate identity/key value, subject to future adapter contract review. |
| `adapt_before_consumption` | The field needs an explicit adapter decision such as sample window, denominator, naming, or source-lane filtering. |
| `not_consumed_yet` | The field is not ready for downstream consumption and remains an open semantics question. |

## Current candidate groups

The registry currently covers the requested groups:

1. Identity
2. Opportunity
3. Efficiency
4. TD / high-value usage
5. Stability / confidence
6. Context candidates

Use the generated view for the current entry-level table. Keep edits in the JSON registry, then regenerate the markdown view when a committed snapshot is useful.
