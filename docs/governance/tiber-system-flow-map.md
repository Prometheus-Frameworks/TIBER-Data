# TIBER System Flow Map (v1)

> Status: Governance map only. Documentation scope only; no runtime integrations, no schema promotions, and no cross-repo dependency changes.
>
> Tracking issue: [#116](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/116)
>
> Canonical source: `TIBER-Data/docs/governance/tiber-system-flow-map.md`

## Purpose

TIBER now operates as a multi-repo intelligence network.
This document defines where authority lives, where artifacts may flow, and which flow directions are suspicious or blocked pending explicit review.

This is intentionally a first-pass governance map. If support truth is missing, scope is reduced instead of inferred.

## Repo roles and authority boundaries

### TIBER-Data

- Canonical facts, contracts, provenance policy, and source metadata.
- Owns source-of-truth contract surfaces and promotion gates.
- Does **not** become authoritative from downstream model or display outputs.

### Point Prediction

- Produces weekly/scenario fantasy projection artifacts.
- May consume canonical and context inputs.
- Projection outputs are **not** canonical fact ownership replacements.

### FORGE

- Player grading/ranking layer.
- May consume bounded projection/context signals.
- FORGE outputs are derived artifacts, not upstream truth.

### Role & Opportunity

- Usage and role interpretation layer.
- Emits role/usage interpretation artifacts for model consumers.

### Teamstate

- Team/environment context layer.
- Emits environment/context artifacts for model consumers.

### Rookies

- Prospect evaluation layer.
- Emits rookie evaluation artifacts for downstream consumers.

### TIBER-Fantasy

- Consumer UI/integration surface.
- Displays and integrates downstream artifacts.
- Display/ranking state is **not** canonical source truth.

## Known or intended artifact flows

The following flows are allowed as first-pass intended channels.

- `TIBER-Data -> Point Prediction`
- `TIBER-Data -> FORGE`
- `Role & Opportunity -> Point Prediction`
- `Teamstate -> Point Prediction`
- `Point Prediction -> FORGE` (bounded projection signal only; does not replace grading ownership)
- `FORGE -> TIBER-Fantasy`
- `Rookies -> TIBER-Data -> TIBER-Fantasy` (reusable rookie artifacts pass through TIBER-Data validation, provenance, and manifest gates before downstream display)

## Suspicious or review-required flows

The following directions are not approved as default behavior and require explicit governance review before use.

- `TIBER-Fantasy -> TIBER-Data`
- `FORGE -> TIBER-Data`
- `Point Prediction -> TIBER-Data`
- `FORGE -> Point Prediction`
- Direct `Rookies -> TIBER-Fantasy` bypasses are review-required unless there is an explicitly approved exception.
- Any flow bypassing TIBER-Data source/provenance gates is not approved by default.
- Any downstream display/model output becoming upstream source truth without declared provenance separation and promotion review.

## Loop classification

### Green loop

Artifact returns only for display, QA, or inspection.
No upstream authority transfer.

### Yellow loop

Model output becomes a bounded feature in another model.
Allowed only when provenance, boundaries, and rollback are explicit.

### Red loop

Downstream output becomes upstream input without provenance separation.
Blocked by default; requires governance intervention.

### Black loop

Generated/derived output is later treated as raw source data.
Disallowed under doctrine.

## Breaker principle

Every loop must define where flow can be:

- stopped,
- inspected,
- invalidated, and
- rolled back.

Intelligence may circulate.
Authority may not circulate blindly.

## Explicit warning on upstream authority

Downstream outputs (model, ranking, or display artifacts) must never be treated as upstream canonical facts unless there is a declared promotion/review step with provenance intact.

Missing connections are acceptable.
Unlabeled or authority-circular connections are not.

## Non-goals for this document

- No runtime integration changes.
- No new cross-repo dependency wiring.
- No scoring logic changes.
- No artifact promotion decisions.
- No invented artifacts or fabricated support continuity.
