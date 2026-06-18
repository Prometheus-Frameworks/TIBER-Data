# TIBER Intelligence Evolution Roadmap

Canonical roadmap for evolving TIBER from rankings/model infrastructure into an evidence-backed intelligence system.

This document is the permanent in-repo roadmap reference. Issue #40 remains the live checklist and PR tracker.

## Core doctrine

- Manual journal = what the operator noticed.
- Automated evidence = what TIBER artifacts can confirm, contradict, or mark unknown.
- Promotion layer = what TIBER is allowed to trust.

Claims are stored because the operator noticed them. Claims are promoted only when evidence artifacts support them.

## Operating rule

No soup, no magic, no invented evidence.

Taste creates hypotheses. Evidence tests hypotheses. Promotion gates trust. ML comes last.

## Phase 0 — Evidence Doctrine

**Status:** PR39 merged.

**Goal:** define evidence governance, evidence statuses, artifact ownership, and historical replay doctrine in TIBER-Data.

**Artifacts/docs:**
- `docs/governance/evidence-layer-v0.md`
- `docs/contracts/evidence-layer-v0.md`

## Phase 1 — Historical Rookie Replay v0

**Status:** Export shape implemented and exported — offline-fixture-backed scaffold, not yet full source-backed 2025 evidence coverage. The exported artifact declares `"source": "offline_fixture:..."`.

**Artifact:**
- `exports/promoted/rookie-replay/historical_rookie_replay_v0.json` (offline-fixture-backed)

**Goal:** pretend it is 2025 and replay completed rookie outcomes as a validation cohort before trusting 2026 live tracking.

**Initial cohort ideas:**
- Tetairoa McMillan → Carnell Tate archetype
- Ashton Jeanty → Jeremiyah Love archetype
- Emeka Egbuka → KC Concepcion archetype
- premium TE translation case
- Day 2 WR landing-spot elevation case

**Derived fields to track:**
- `pre_draft_grade`
- `post_draft_context`
- `weekly_ppr`
- `season_ppr`
- `startable_weeks`
- `spike_weeks`
- `bust_weeks`
- `weekly_volatility`
- `role_materialized`
- `target_share_materialized`
- `model_was_right_for_wrong_reason`
- `model_was_wrong_for_right_reason`

## Phase 2 — Weekly PPR Reality Tracker

**Status:** Export shape implemented and exported — offline-fixture-backed scaffold, not yet full source-backed 2025 evidence coverage. The exported artifact declares `"source": "offline_fixture:..."`.

**Goal:** build `player_weekly_ppr_outcomes_v1` for 2025 historical validation first, then 2026 live weekly refresh.

**Canonical target:**
- `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json` (offline-fixture-backed)

## Phase 3 — Team Environment Evidence

**Status:** Export shape implemented and exported — offline-fixture-backed scaffold, not yet full source-backed 2025 evidence coverage. Both exported artifacts declare `"source": "offline_fixture:..."`.

**Goal:** build team pace/pass and offense summaries from artifact-backed data.

**Canonical targets:**
- `exports/promoted/nfl/team_pace_pass_environment_v1.json` (offline-fixture-backed)
- `exports/promoted/nfl/team_offense_summary_v1.json` (offline-fixture-backed)

**Core checks:**
- pass volume
- neutral pass rate
- dropbacks per game
- red-zone pass rate
- WR/TE/RB target share
- pace
- offensive environment indicators

## Phase 4 — Roster / Staff Context

This phase has two parts with different status.

### Phase 4a — Roster mapping

**Status:** Export shape implemented and exported — offline-fixture-backed scaffold, not yet full source-backed 2025 evidence coverage. The exported artifact declares `"source": "offline_fixture:..."`.

**Artifact:**
- `exports/promoted/nfl/roster_player_team_map_v1.json` (offline-fixture-backed)

### Phase 4b — Coaching staff context

**Status:** Not started. `coaching_staff_context_v1.json` is named as a target below but has no code, fixtures, or exported artifact yet.

**Planned target:**
- `exports/promoted/nfl/coaching_staff_context_v1.json` (not yet produced)

**Goal:** build player-team maps and coaching/play-caller context.

**Used for claims like:**
- Kellen Moore pass-volume environment
- Shough/Tyson fit
- Olave hierarchy
- heavy-personnel target consolidation

## Phase 5 — Evidence Scanner in TIBER-Rookies

**Goal:** compare operator journal candidates against TIBER-Data artifacts.

**Workbench columns to add:**
- Operator Signal
- Automated Evidence
- Evidence Status
- Promotion Eligibility
- Contradictions / Missing Data

## Phase 6 — Role Outcome Calibration

**Goal:** use completed seasons to learn what fantasy roles actually produced.

**Examples:**
- WR2 under specific offensive environments
- TE1 / move TE / blocking TE translation
- premium RB workload insulation
- rookie WR startability decay

## Phase 7 — 2026 Live Weekly Loop

**Goal:** once 2025 backtest passes, run weekly 2026 evidence refreshes.

**Weekly loop:**
- update PPR outcomes
- update role/usage evidence
- update team environment
- re-evaluate journal claims
- flag promoted, contradicted, stale, or needs-verification signals

## Phase 8 — ML-Ready Intelligence Dataset

**Goal:** only after evidence is clean, build ML-facing features from typed claims + typed evidence + completed outcomes.

**Rule:** ML consumes promoted/typed evidence. It does not ingest untyped narrative soup.

## Cross-repo responsibilities

**TIBER-Data:**
- owns evidence contracts and canonical artifacts

**TIBER-Teamstate:**
- interprets team environment

**Role-and-Opportunity:**
- translates team/role context into fantasy role expectations

**TIBER-Rookies:**
- prospect interface, operator journal, Workbench, evidence review

**TIBER-FORGE:**
- grading engine consuming stable promoted evidence later

**TIBER-Fantasy:**
- downstream presentation surface once evidence is promoted

## Phase status summary

"Export shape complete" below means the artifact's contract/export shape is implemented and exported from an **offline fixture** (`"source": "offline_fixture:..."`). It does **not** mean full source-backed 2025 evidence coverage; that source-derived ingestion remains open and these scaffolds must not be treated as promoted real evidence.

- Phase 0 — Evidence Doctrine: done (PR39 merged).
- Phase 1 — Historical Rookie Replay v0: export shape complete, offline-fixture-backed (`historical_rookie_replay_v0.json`); full source-backed coverage still open.
- Phase 2 — Weekly PPR Reality Tracker: export shape complete, offline-fixture-backed (`player_weekly_ppr_outcomes_v1.json`); full source-backed coverage still open.
- Phase 3 — Team Environment Evidence: export shape complete, offline-fixture-backed (`team_pace_pass_environment_v1.json`, `team_offense_summary_v1.json`); full source-backed coverage still open.
- Phase 4a — Roster mapping: export shape complete, offline-fixture-backed (`roster_player_team_map_v1.json`); full source-backed coverage still open.
- Phase 4b — Coaching staff context: not started (no code, fixtures, or artifact for `coaching_staff_context_v1.json`).
- Phases 5–8: not started.

## Current next action

Phases 1–3 and roster mapping (Phase 4a) have their export shapes implemented and exported as offline-fixture-backed scaffolds; replacing those fixtures with full source-backed 2025 evidence coverage remains open work and is not represented by the fixture exports alone. The next entirely unbuilt step in this roadmap is Phase 4b — Coaching staff context (`coaching_staff_context_v1.json`), which currently has no code, fixtures, or artifact support.

Issue #40 remains the live checklist and PR tracker.
