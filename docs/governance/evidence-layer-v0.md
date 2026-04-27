# TIBER Evidence Layer v0 (Deterministic Artifact Doctrine)

## 1) Purpose

TIBER Evidence Layer v0 defines the first canonical, deterministic boundary between:

- **manual operator journal claims** (what a human scout observed), and
- **artifact-backed evidence** (what TIBER data can currently confirm, contradict, or leave unknown).

This layer exists so downstream promotion decisions are governed by inspectable artifacts rather than plausibility or narrative continuity.

## 2) Doctrine

Evidence Layer v0 follows these rules:

1. **Manual journal != truth by default.**
   Operator claims are hypotheses until artifact-backed evidence status is assigned.
2. **Evidence must be deterministic and inspectable.**
   Every evaluation must be reproducible from versioned artifacts in TIBER-Data.
3. **Unknown is allowed.**
   If required source support is missing, claims remain unpromoted with explicit status.
4. **No silent continuity extension.**
   Week/range support cannot be inferred beyond available artifact rows.
5. **Promotion is gated by evidence status, not confidence tone.**

## 3) Data ownership

- **TIBER-Data owns Evidence Layer artifacts and contracts** for canonical evidence evaluation inputs.
- Downstream repositories may consume these artifacts for evaluation and display.
- Downstream repositories must **not invent missing evidence**, synthetic support rows, or inferred coverage windows.
- Evidence authority for promotion boundaries remains in TIBER-Data governance and contract documents.

## 4) Artifact list (v0 proposed promoted evidence inputs)

Evidence Layer v0 defines these canonical artifact targets:

- `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json`
- `exports/promoted/nfl/player_weekly_usage_v1.json`
- `exports/promoted/nfl/team_offense_summary_v1.json`
- `exports/promoted/nfl/team_pace_pass_environment_v1.json`
- `exports/promoted/nfl/roster_player_team_map_v1.json`
- `exports/promoted/nfl/coaching_staff_context_v1.json`

v0 in this PR defines **contract and documentation only**. It does not add external fetch, scrape, or live export generation.

## 5) Evidence statuses

Each claim evaluation must resolve to exactly one status:

- `unsupported`
  - No relevant artifact-backed signal currently available for the claim.
- `needs_verification`
  - Some support exists but is insufficiently reliable or complete for promotion.
- `partially_supported`
  - Evidence supports a bounded subset of the claim but not full scope.
- `supported`
  - Artifact-backed evidence supports the claim within declared scope.
- `contradicted`
  - Artifact-backed evidence conflicts with the claim.
- `stale_or_missing_data`
  - Required evidence artifacts are missing, stale, or outside declared support window.

## 6) Claim-to-evidence matching flow

1. **Ingest claim metadata**
   - Claim text, player/team scope, season/week scope, and claim type.
2. **Resolve required artifact set**
   - Map claim type to required promoted evidence artifacts.
3. **Check support window and artifact freshness**
   - If required coverage is absent or stale, assign `stale_or_missing_data`.
4. **Extract deterministic evidence rows**
   - Pull only rows matching explicit claim scope and contract keys.
5. **Apply status mapping rules**
   - Assign one of the six statuses using explicit rule criteria.
6. **Emit inspectable evaluation record**
   - Include status, artifact references, source labels, and generated timestamp.

## 7) Promotion rules

A claim is eligible for promotion only when:

- status is `supported` or clearly bounded `partially_supported` (with explicit scope limits), and
- the supporting artifacts are present in canonical promoted locations, and
- evidence rows are source-labeled and reproducible.

A claim is **not** promotable when status is:

- `unsupported`
- `needs_verification`
- `contradicted`
- `stale_or_missing_data`

No claim is promoted solely because it appears plausible to an operator.


## 8) Historical validation / replay doctrine

Before Evidence Layer artifacts are trusted for live weekly tracking, the same builders should support historical replay against the most recent completed NFL season.

For 2026 development, **2025** is the initial validation season.

Backtest goals:

- reproduce weekly player PPR totals,
- reproduce season-long player PPR totals,
- generate team pace/pass/target-share summaries,
- validate role-to-fantasy baselines against completed outcomes,
- compare operator claim statuses against known completed outcomes.

Supported modes:

- `historical_backtest`
- `live_weekly_refresh`

Rule:

No live evidence artifact should be promoted until the same artifact family can produce valid historical outputs for the most recent completed season.

This keeps the Evidence Layer honest: **2025 proves the pipeline, 2026 uses the pipeline**.

## 9) Non-goals (v0)

Evidence Layer v0 does **not**:

- implement external data fetching or scraping,
- redefine scoring systems,
- modify existing artifact generation pipelines,
- introduce downstream repo-specific logic,
- claim support for weeks/seasons not present in canonical artifacts.
