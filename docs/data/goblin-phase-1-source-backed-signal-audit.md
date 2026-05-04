# GOBLIN Phase 1 Source-Backed Signal Audit (Issue #57)

## 1) Purpose

GOBLIN means **Gross Output But Legitimate Indicator Node**.

In this Phase 1 research lane, GOBLIN is an evidence scanner that looks for players with ugly surface fantasy outcomes but legitimate underlying usage/context signals that warrant human review.

GOBLIN is:
- an **attention-allocation tool** for operator review
- a **source-backed research artifact design** effort in TIBER-Data

GOBLIN is not:
- a ranking model
- a waiver recommendation engine
- a promoted fantasy product output at this stage

## 2) Current source-backed inputs

### A) Identity artifact
- **Path:** `data/processed/evidence/roster_player_team_map_2025.source_backed.json`
- **Source / provenance:** `nflreadpy.load_rosters_weekly([2025])`
- **Contribution to GOBLIN:** Provides stable player identity and team context joins (`player_id`, `player_name`, `team`, `position`) needed to interpret and group weekly outcomes/usage.
- **Limitations:** Does not provide usage intensity or fantasy outcome fields by itself; identity/class details (for rookie-specific logic) may require explicit schema confirmation/extension.

### B) PPR outcomes artifact
- **Path:** `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json`
- **Build rule:** generated from the existing TypeScript PPR builder with `toDeterministicPlayerWeeklyPprOutcomesV1Json({ sourceKind: "source_backed" })` via `npm run export:player-weekly-ppr-source-backed-2025`.
- **Source / provenance:** computed from `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json` raw wrapper records.
- **Artifact shape note:** identity/usage source-backed handoffs are wrapper objects (`provenance`, `source_path`, `records`), while this computed PPR handoff is currently a deterministic computed row array emitted by the TypeScript builder; readiness checks accept this governed computed-array shape without requiring GOBLIN to recompute PPR.
- **Contribution to GOBLIN:** supplies deterministic weekly output evidence including computed `ppr_points`, rolling windows, and season accumulators used by readiness checks and future candidate generation.
- **Limitations:** raw source-backed input remains an input wrapper without computed `ppr_points`; GOBLIN consumers should use this governed computed handoff and must not silently recompute PPR internally.

### C) Usage artifact
- **Path:** `data/processed/evidence/player_weekly_usage_2025.source_backed.json`
- **Source / provenance:** `nflreadpy.load_player_stats([2025])`
- **Contribution to GOBLIN:** Supplies underlying opportunity/context fields for “legitimacy” checks.
- **Current available usage fields:** `targets`, `receptions`, `target_share`, `air_yards`, `air_yards_share`, `rushing_attempts`.
- **Known contract semantics:**
  - `air_yards_share` may be negative and should be preserved as signal.
  - Unsupported fields are currently null: `routes_run`, `route_participation`, `team_rushing_attempts`, `rush_share`, `red_zone_targets`, `red_zone_carries`, `snap_share`.
- **Limitations:** Missing route/snap/red-zone/team-rush context blocks several downstream flag families.

## 3) Core GOBLIN concept

GOBLIN separates two ideas:

- **Grossness**: why the market or casual review may ignore the player from a weak weekly result.
- **Legitimacy**: why source-backed usage/context suggests the player still deserves attention.

### Grossness examples (surface output)
- low PPR points
- no touchdown
- low yardage
- low receptions
- weak total box score

### Legitimacy examples (underlying evidence)
- high targets despite low points
- strong `target_share`
- meaningful `air_yards` (or unusual `air_yards_share`)
- week-over-week usage increase
- carries present despite poor fantasy return
- low/negative outcome week that masks receiving involvement

## 4) Computable flags today

The following flags are computable now from the current identity + PPR + usage source-backed artifacts, unless noted otherwise. Thresholds below are **candidate direction only**, not final tuned cutoffs.

### 4.1 `low_ppr_high_targets`
- **Description:** Flags players with poor weekly PPR outcome but substantial target volume.
- **Required fields:** `ppr_points`, `targets`.
- **Source-backed status:** Computable now.
- **Candidate threshold direction:** Low `ppr_points` for position/week context with elevated `targets` (e.g., 6+ style range).
- **Caveats:** Should be position-aware and week-distribution aware.

### 4.2 `low_ppr_high_target_share`
- **Description:** Low fantasy output despite strong share of team targets.
- **Required fields:** `ppr_points`, `target_share`.
- **Source-backed status:** Computable now.
- **Candidate threshold direction:** Low `ppr_points` with high `target_share` relative to weekly peers.
- **Caveats:** Team pass-volume context matters; share alone can mislead in low-volume offenses.

### 4.3 `air_yards_without_output`
- **Description:** Opportunity depth present but output lagging.
- **Required fields:** `air_yards`, `ppr_points` (optionally `receptions` for interpretation).
- **Source-backed status:** Computable now.
- **Candidate threshold direction:** Elevated `air_yards` with weak `ppr_points` / muted box-score conversion.
- **Caveats:** One-week deep-shot variance is high; may need multi-week smoothing.

### 4.4 `negative_air_yards_share_context`
- **Description:** Preserves unusual negative `air_yards_share` as contextual signal rather than coercing to zero.
- **Required fields:** `air_yards_share`, plus outcome/usage context fields (`ppr_points`, `targets`, `receptions`, `air_yards`).
- **Source-backed status:** Computable now.
- **Candidate threshold direction:** Detect negative or unusually low `air_yards_share` and review alongside involvement/output profile.
- **Caveats:** Negative values can represent real play-level effects; should be interpreted, not auto-penalized.

### 4.5 `carries_without_points`
- **Description:** Rushing involvement exists but fantasy points remain weak.
- **Required fields:** `rushing_attempts`, `ppr_points`.
- **Source-backed status:** Computable now.
- **Candidate threshold direction:** Non-trivial `rushing_attempts` paired with low `ppr_points`.
- **Caveats:** Without `team_rushing_attempts`/`rush_share`, role centrality cannot be confirmed.

### 4.6 `target_share_without_touchdown`
- **Description:** Target role present but no TD-driven output.
- **Required fields:** `target_share`, touchdown indicator from PPR outcomes artifact, `ppr_points`.
- **Source-backed status:** Computable now if weekly touchdown field is present in outcomes contract.
- **Candidate threshold direction:** High `target_share` with zero touchdowns and weak/mediocre PPR return.
- **Caveats:** TDs are noisy; interpretation should avoid overfitting to one week.

### 4.7 `usage_spike_without_box_score`
- **Description:** Week-over-week usage increase not reflected in surface output.
- **Required fields:** Weekly sequence keys (`season`, `week`, `player_id`) + usage fields (`targets`, `target_share`, `air_yards`, `rushing_attempts`) + `ppr_points`.
- **Source-backed status:** Computable now.
- **Candidate threshold direction:** Positive week-over-week deltas in usage with flat/low `ppr_points`.
- **Caveats:** Early-season baseline instability and byes/role resets require handling.

### 4.8 `wopr_without_ppr_output`
- **Description:** Intended to capture weighted opportunity rate behavior with weak fantasy output.
- **Required fields:** `wopr` (or derivable components under approved formula), `ppr_points`.
- **Source-backed status:** **Not yet computable unless `wopr` is added to the usage contract/artifact** (or explicitly derivable in-contract with documented formula).
- **Candidate threshold direction:** High WOPR-style opportunity vs low output.
- **Caveats:** Must avoid undocumented derived metrics.

### 4.9 `rookie_ramp_hidden_by_low_volume`
- **Description:** Detects early-career usage growth masked by low fantasy output.
- **Required fields:** `player_id`, weekly usage/outcomes fields, plus rookie class/tenure identity fields.
- **Source-backed status:** **Partially computable if rookie identity/class data is joined later**.
- **Candidate threshold direction:** Positive usage trend with still-low output among confirmed rookie cohort.
- **Caveats:** Currently blocked on explicit rookie classification in joined identity contract.

## 5) Blocked flags

These flags are currently blocked due to missing source-backed fields/sources and cannot be inferred honestly.

### 5.1 `high_route_participation_low_output`
- **Missing field/source:** `route_participation`, `routes_run`.
- **Why blocked:** Route involvement cannot be inferred from targets alone.
- **Future source requirement:** Source-backed route participation artifact/contract.

### 5.2 `snap_share_jump_without_points`
- **Missing field/source:** `snap_share`.
- **Why blocked:** Snap role changes are not reconstructible from current usage fields.
- **Future source requirement:** Weekly player snap-count/share source-backed feed.

### 5.3 `red_zone_usage_without_td`
- **Missing field/source:** `red_zone_targets`, `red_zone_carries`.
- **Why blocked:** Red-zone role is not inferable from aggregate targets/carries.
- **Future source requirement:** Source-backed red-zone touch artifact.

### 5.4 `end_zone_targets_without_td`
- **Missing field/source:** End-zone target field (not present in current artifacts).
- **Why blocked:** End-zone opportunity is not derivable from current aggregate receiving fields.
- **Future source requirement:** Play-level or summarized end-zone target source.

### 5.5 `goal_line_carries_without_td`
- **Missing field/source:** Goal-line carry detail.
- **Why blocked:** Goal-line usage cannot be inferred from total rushing attempts.
- **Future source requirement:** Play-level location bucketed rushing source.

### 5.6 `backup_role_one_injury_away`
- **Missing field/source:** Depth chart status and injury/deactivation context.
- **Why blocked:** Counterfactual role proximity is not measurable from current evidence layer.
- **Future source requirement:** Source-backed depth chart + injury participation artifacts.

### 5.7 `slot_role_without_box_score`
- **Missing field/source:** Alignment/slot rate data.
- **Why blocked:** Slot role cannot be inferred from aggregate targets/air yards.
- **Future source requirement:** Source-backed alignment/snap-location feed.

### 5.8 `market_lag / usage_spike_without_market_reaction`
- **Missing field/source:** Market/external valuation signal (ADP, roster %, start %, etc.).
- **Why blocked:** “Market reaction” claims require explicit market data source.
- **Future source requirement:** Contracted market dataset joined by player-week.

## 6) Candidate artifact design (not implemented)

Two path options:
- `exports/research/goblin/goblin_signal_candidates_v0.json`
- `data/processed/research/goblin_signal_candidates_2025.source_backed.json`

### Recommendation at this stage
Prefer:
- `data/processed/research/goblin_signal_candidates_2025.source_backed.json`

Rationale:
- Keeps output explicitly inside source-backed/research lane semantics.
- Avoids implying productized export status too early.
- Aligns with deterministic, auditable evidence lineage conventions already used by current artifacts.

### Candidate row shape
- `season`
- `week`
- `player_id`
- `player_name`
- `team`
- `position`
- `gross_output_flags` (array)
- `legitimate_indicator_flags` (array)
- `blocked_or_missing_fields` (array)
- `ppr_points`
- `usage_snapshot` (object)
- `candidate_score_component_notes` (object/string notes)
- `evidence_status`
- `source_artifacts` (array of artifact paths)
- `generated_at`

Important:
- `candidate_score` is **not implemented** in Phase 1.
- Any score-like field, if later added, must be clearly labeled as research-only and formula-versioned.

## 7) Interpretable future formula (research-only, non-final)

Illustrative form:

`GOBLIN_score = GrossnessDiscount × LegitimacySignal × OpportunityChange × EvidenceConfidence - FragilityPenalty`

Potential component inputs:
- **GrossnessDiscount:** low `ppr_points`, no-TD condition, low receptions/yardage profile.
- **LegitimacySignal:** `targets`, `target_share`, `air_yards`, contextual `air_yards_share`, `rushing_attempts`.
- **OpportunityChange:** week-over-week deltas in usage fields.
- **EvidenceConfidence:** proportion of needed fields that are source-backed and non-null for a candidate row.
- **FragilityPenalty:** instability markers (small sample volatility, missing context fields, role ambiguity).

This is a readability scaffold for future research only, not active production scoring.

## 8) Guardrails

- No invented data.
- No fuzzy identity matching.
- No route/snap/red-zone claims without explicit source-backed fields.
- No market-lag claims without a contracted market source.
- `null` means unavailable, not zero.
- Negative `air_yards_share` can be valid signal and must be preserved.
- Source-backed flags must cite source-backed artifacts.
- Candidate scanner, not recommendation engine.
- Operator review required before any decision/action.

## 9) Recommended next PR

Recommended immediate next small PR:

1. Add a **GOBLIN source-readiness check script/test** that:
   - verifies required source-backed artifacts exist,
   - reports row counts,
   - reports required field availability/null coverage,
   - fails closed when required inputs are missing.

Then, after readiness checks are in place:

2. Build `goblin_signal_candidates_v0` from source-backed artifacts under research lane conventions.

This sequencing keeps Phase 1 deterministic, bounded, and honest about available evidence before candidate generation.
