# Cross-Repo Governance v0

> Status: Documentation-only governance note. Scoped to principles, ownership mapping, and gap flagging. No model logic, no contract changes in this document.
>
> Tracking issue: [#91](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/91)
>
> Canonical source: `TIBER-Data/docs/governance/cross-repo-governance-v0.md`

## Why this document exists

TIBER repos must operate as a coherent football data system, not as disconnected model outputs. This note formalizes the four principles that make the system coherent across repo boundaries, names the repo that owns each principle, points to existing schemas/artifacts that already support them, and flags gaps where new schemas or metadata fields are needed.

This document complements, and does not replace:

- `docs/TIBER_DOCTRINE.md` (contract philosophy, S-tier checklist)
- `docs/governance/architecture/tiber-architecture-document-v1.0.md` (architecture rules)
- `docs/governance/evidence-layer-v0.md` (evidence statuses, promotion gates)
- `docs/governance/tiber-intelligence-evolution-roadmap.md` (phase plan)
- `TRUTH_SOURCES.md` (fail-closed rules)

## Operating loop

The TIBER system is governed as a single loop:

```text
observe → structure → evaluate → explain → compare to outcome → recalibrate
```

Each principle below corresponds to a stage of that loop. The point of governance is to keep the loop coherent across repo boundaries so downstream consumers do not invent missing pieces.

## Principles

### 1. Canonical State

**Principle.** TIBER-Data is the source of truth for player IDs, team IDs, seasons, schema versions, artifact contracts, and promoted output expectations. Downstream repos must not invent duplicate truth when canonical data already exists.

**Owner.** TIBER-Data.

**Existing support.**
- Versioned contracts under `src/contracts/v1/` (entry point: `src/contracts/v1/index.ts`).
- Promoted artifact targets enumerated in `docs/contracts/evidence-layer-v0.md` (e.g. `roster_player_team_map_v1`, `team_offense_summary_v1`, `team_pace_pass_environment_v1`, `player_weekly_ppr_outcomes_v1`, `player_weekly_usage_v1`, `coaching_staff_context_v1`).
- Per-artifact schema docs under `docs/schemas/` (`players.md`, `teams.md`, `weekly_player_stats.md`, `weekly_team_stats.md`, `player_role_inputs_weekly.md`, `team_context_weekly.md`, `team_opportunity_context_compatibility_weekly.md`, `player_role_profile_compatibility_weekly.md`).
- Versioned contract docs under `docs/contracts/` (`evidence-layer-v0.md`, `history-rookie-replay-v0.md`, `operator-signal-note-v0.md`, `roster-snapshot-v0.md`).
- Truth-source rules in `TRUTH_SOURCES.md` and fail-closed posture in `AGENTS.md`.

**Gaps to flag.**
- No single index that lists every promoted artifact, its current schema version, and its declared support window in one place.
- ID stability rules (when a `player_id` may change, how rookies are minted, how alias resolution works across seasons) are not documented as a contract.

### 2. Observability

**Principle.** Promoted outputs must be traceable. For each artifact or endpoint, the system must answer: what source data was used, which repo generated it, which schema version it follows, what assumptions were applied, what season/week/context it represents, and what confidence or uncertainty is attached.

**Owner.** TIBER-Data owns the observability envelope contract. Producing repos populate it.

**Existing support.**
- The S-tier checklist in `docs/TIBER_DOCTRINE.md` already names the required envelope fields: canonical IDs, season/week scope, `source` metadata, `generated_at` timestamp, model/version metadata, normalized confidence, nulls for unknowns.
- `docs/contracts/evidence-layer-v0.md` requires `source` and `generated_at` on every row.
- Evidence statuses in `docs/governance/evidence-layer-v0.md` (`unsupported`, `needs_verification`, `partially_supported`, `supported`, `contradicted`, `stale_or_missing_data`) provide a normalized way to express uncertainty for evaluated claims.

**Gaps to flag.**
- The doctrine checklist is not yet expressed as an enforced envelope contract that every promoted artifact must satisfy. A `promoted_artifact_envelope_v0` contract would lock in: `source`, `producer_repo`, `schema_version`, `assumptions[]`, `season`, `week`, `generated_at`, `confidence` (or evidence status reference).
- Producer-repo identity (`producer_repo`) is not currently a required field on promoted rows. Without it, an inspector cannot deterministically answer "which repo generated this row."
- An `assumptions[]` field (free-form short tags such as `"route_participation_proxy"`, `"missing_snap_counts"`) is not yet standardized.

### 3. Outcome Calibration

**Principle.** TIBER must be able to compare model claims against real outcomes. Examples: breakout flags vs realized usage, role-opportunity signals vs actual route/target changes, FORGE scores vs fantasy outcomes, rookie projections vs year 1–3 production. The goal is not perfect prediction; the goal is to make failure modes visible and improve future weighting.

**Owner.** TIBER-Data owns the calibration record contract and the realized-outcome artifacts. Per-model repos emit claims in the contract shape. Downstream consumers (FORGE, Fantasy) read calibration records but do not own them.

**Existing support.**
- Realized outcome artifacts already targeted: `player_weekly_ppr_outcomes_v1`, `player_weekly_usage_v1` (see `docs/contracts/evidence-layer-v0.md`).
- Historical replay doctrine: `docs/governance/historical-rookie-replay-v0.md` and `docs/contracts/history-rookie-replay-v0.md`.
- Phase 6 of `docs/governance/tiber-intelligence-evolution-roadmap.md` ("Role Outcome Calibration") describes the intent.
- Operator-signal capture: `docs/contracts/operator-signal-note-v0.md`, `schemas/operator_signal_note_v0.schema.json`.
- Evidence-layer status vocabulary already supports the "claim vs evidence" half of the comparison.

**Gaps to flag.**
- No `model_claim_vs_outcome_v0` contract exists. A v0 shape would carry: `claim_id`, `producer_repo`, `claim_type` (e.g. `breakout_flag`, `role_opportunity_score`, `forge_score`, `rookie_projection`), `subject_id` (player or team), `season`, `week_or_window`, `predicted_value`, `realized_value`, `realized_source_artifact`, `delta`, `failure_mode_tag`, `generated_at`.
- No standardized `failure_mode_tag` vocabulary (e.g. `right_for_wrong_reason`, `wrong_for_right_reason`, `role_did_not_materialize`, `environment_changed`, `injury_disrupted`).
- `coaching_staff_context_v1` is referenced in evidence-layer contracts but no per-artifact contract doc exists yet under `docs/contracts/` to match the other versioned contracts.

### 4. World Modeling

**Principle.** TIBER must gradually move from raw stats toward structured football context: offensive identity, coaching tendency, pass/run environment, target-tree concentration, QB stability, protection quality, roster/depth-chart context, and uncertainty tags. Teamstate owns much of this environment layer; TIBER-Data defines the contracts other repos consume.

**Owner.** TIBER-Teamstate owns the environmental interpretation. TIBER-Data owns the contract surface that exposes it to other repos. Role-and-Opportunity-Model and downstream consumers read these contracts, do not redefine them.

**Existing support.**
- Team-context schema docs present: `docs/schemas/team_context_weekly.md`, `docs/schemas/team_opportunity_context_compatibility_weekly.md`, `docs/schemas/teams.md`.
- Promoted artifact targets: `team_pace_pass_environment_v1`, `team_offense_summary_v1`, `coaching_staff_context_v1` (see `docs/contracts/evidence-layer-v0.md`).
- Roster/depth context: `docs/schemas/players.md` and the versioned `docs/contracts/roster-snapshot-v0.md`; planned promoted artifact `roster_player_team_map_v1`.
- `team-state/` directory is wired in at the repo level for environment data handoff.

**Gaps to flag.**
- No contract surface yet for: target-tree concentration (top-1/top-3 target share, tier shape), QB stability (starter continuity, injury status, depth-chart change), protection quality (pressure rate allowed, sack rate, pass-block grade proxy).
- No standardized `uncertainty_tag` vocabulary on world-model rows (e.g. `low_sample_size`, `staff_change_recent`, `injury_uncertainty`, `roster_volatility`).
- "Offensive identity" and "coaching tendency" are referenced in roadmap but not yet expressed as a typed shape downstream repos can consume.

## Ownership matrix

| Principle | Contract owner | Producer(s) | Primary consumers |
| --- | --- | --- | --- |
| Canonical State | TIBER-Data | TIBER-Data | All repos |
| Observability | TIBER-Data | All producing repos | All consuming repos, auditors |
| Outcome Calibration | TIBER-Data | Per-model repos (Point-Prediction, Role-and-Opportunity, Signal-Validation *(planned, not yet created)*, Age-Curve, FORGE) | TIBER-Data (replay), TIBER-Fantasy, FORGE |
| World Modeling | TIBER-Data (contract); TIBER-Teamstate (interpretation) | TIBER-Teamstate | Role-and-Opportunity-Model, FORGE, TIBER-Fantasy |

## Gap summary (follow-up issues recommended)

The following are intentionally not implemented in this document. They should be tracked as separate issues so each can be reviewed against doctrine before contracts are added.

1. `promoted_artifact_envelope_v0` contract — observability envelope every promoted artifact must satisfy (`producer_repo`, `schema_version`, `assumptions[]`, normalized confidence, etc.).
2. `model_claim_vs_outcome_v0` contract — outcome-calibration record shape, plus `failure_mode_tag` vocabulary.
3. `coaching_staff_context_v1` contract doc under `docs/contracts/` to match the artifact already referenced in evidence-layer contracts.
4. World-model contract additions: target-tree concentration, QB stability, protection quality, standardized `uncertainty_tag` vocabulary.
5. Single index of promoted artifacts (file → version → support window → owning producer repo).
6. Player/team ID stability and alias-resolution rules as an explicit contract.

## Posture

This document is a contract map, not a model. It states what is owned, what already exists, and what is missing. It does not extend coverage, does not synthesize fields, and does not promote any artifact. Following the repo's fail-closed rule: where a contract is missing, this note flags the gap rather than inventing the contract.
