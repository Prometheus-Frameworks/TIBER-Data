# Contract Change: Generalize `promotion_review` in the Promoted Schema

- **Generated at:** 2026-07-06
- **Tracking issue:** TIBER-Data#204
- **Prior context:** TIBER-Data#202 / PR#203 found the 2021-2025 merged candidate fully sound but blocked promotion on a schema defect: `promotion_review` was hardcoded to `const: "TIBER-Data#192"`.
- **Status:** contract-task report. Scoped to the schema fix only. Does **not** authorize promotion, candidate rebuilds, Forecast work, threshold decisions, model wiring, or product behavior.

## Change made

`schemas/player_season_coverage_v0_promoted.schema.json`, field `promotion_review`:

```diff
-"promotion_review": { "type": "string", "const": "TIBER-Data#192" }
+"promotion_review": { "type": "string", "pattern": "^TIBER-Data#[0-9]+\Z" }
```

Also updated the schema's top-level `description` to stop describing the contract as scoped to a single promotion event (it referenced "TIBER-Data #192" as if the whole contract were that one-time-only; now it credits both #192 as the originating event and #204 as the generalization).

## Other fields checked for accidental first-promotion-specificity

A full scan of the schema for `const` constraints found exactly three: `status`, `row_grain`, and `promotion_review`. Only `promotion_review` was first-promotion-specific.

| field | const value | first-promotion-specific? | action |
|---|---|---|---|
| `status` | `promoted_governed_artifact` | No — this is the correct, permanent invariant marking any promoted artifact | unchanged |
| `row_grain` | `player_id + season + season_type` | No — this is the correct, permanent grain invariant for this artifact family | unchanged |
| `promotion_review` | `TIBER-Data#192` | **Yes** | generalized (see above) |

No other field (`seasons`, `season_type_scope`, `source_candidate`, `approved_source_allowlist`, `consumer_safety`, per-record `$defs`) carries a first-promotion-specific constraint. No unrelated field was broadened.

## Tests added

`tests/test_player_season_coverage_v0_promoted_schema.py` (26 tests):

- Both `TIBER-Data#192` and `TIBER-Data#202` (plus `#204`, `#1`) validate as `promotion_review`.
- Malformed/non-TIBER-Data references fail closed: bare numbers, missing `#`, lowercase, wrong casing, trailing/leading whitespace, non-numeric suffix, empty string, a same-shape-but-wrong-repo reference (`TIBER-Forecast#134`), and (added after a Codex review finding) trailing/leading newline variants (`"TIBER-Data#192\n"`, `"\n\n"`, `"\r\n"`, leading `"\n"`) all correctly fail. A dedicated schema-inspection test also asserts the pattern ends with `\Z` rather than a bare `$`, since Python's `re` treats `$` as matching before a single trailing newline rather than strict end-of-string -- the original pattern would have let a newline-tainted review reference through.
- `status` and `row_grain` remain `const` in the schema and still reject any deviation (invariant protection verified both by schema inspection and by validating a deviating payload).
- **Regression:** the currently-committed, live promoted artifact (`exports/promoted/nfl/player_season_coverage_v0.json`, from TIBER-Data#192) still validates cleanly against the generalized schema — zero errors.
- **Unblock confirmation:** calling PR#203's `build_promoted_payload` directly (pure function, no disk writes, no `main()` call, nothing under `exports/promoted/**` touched) against the real, committed 2021-2025 merged candidate now produces a payload that validates cleanly against the generalized schema — zero errors, `promotion_review: "TIBER-Data#202"`.

Full repo suite: 350 passed (up from 324 before this change; 345 immediately after the initial generalization, 350 after the newline-anchor fix added 5 more tests). Typecheck: passed.

## Audit

This change modifies a contract under `schemas/**`, which fires `AGENTS.md`'s audit trigger explicitly ("adds or changes a contract under `src/contracts/**`, `schemas/**`, or `docs/contracts/**`"). Audit artifact: `docs/audits/player-season-coverage-v0-promoted-schema-generalization-2026-07-06.{md,json}`.

## Decision

```text
may_resume_player_season_coverage_2021_2025_promotion_attempt
```

- **Basis:** the schema change is narrow, keeps `exports/promoted/**` untouched, preserves both true invariants, adds tests for old and new review references plus invariant protection, and directly confirms (via the pure `build_promoted_payload` function, no writes) that the PR#203 promotion payload now passes schema validation.
- This decision authorizes only a **follow-up TIBER-Data promotion-resume issue or PR**. It does not itself promote anything and does not authorize Forecast work.

### Explicitly NOT emitted / NOT authorized by this report

- `player_season_coverage_promoted_schema_generalization_blocked`
- `player_season_coverage_promoted_schema_generalization_requires_followup`
- promotion of any artifact
- modification of `exports/promoted/nfl/player_season_coverage_v0.json` or its manifest (confirmed untouched)
- candidate rebuilds
- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- threshold decisions, model wiring, or production claims
- ranking/advice/UI/export/product behavior
