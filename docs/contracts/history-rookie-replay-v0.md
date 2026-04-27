# Historical Rookie Replay v0 Contract

This document defines the contract-level artifact shape for Historical Rookie Replay v0.

Scope in this PR is documentation-level contract specification only.

## Canonical artifact target

- `exports/promoted/rookie-replay/historical_rookie_replay_v0.json`

## Purpose

Historical Rookie Replay v0 replays a completed rookie season as if evaluation were happening in real time.

For initial validation, the replay season is **2025**. The objective is to compare:

- pre-draft thesis and grade,
- post-draft landing context,
- expected role assumptions,
- completed weekly and season fantasy outcomes,
- and explicit evidence-status resolution.

This replay boundary exists to validate thesis quality before trusting 2026 live rookie tracking.

## Initial replay cohort (v0)

- Tetairoa McMillan → Carnell Tate archetype
- Ashton Jeanty → Jeremiyah Love archetype
- Emeka Egbuka → KC Concepcion archetype
- premium TE translation case
- Day 2 WR landing-spot elevation case

## General contract expectations

- Artifact payload is deterministic and stored at the canonical v0 target path.
- Rows must be source-labeled and inspectable.
- Null is preferred over synthetic imputation when an optional field is unavailable.
- `generated_at` must use ISO-8601 UTC timestamp format.
- Replay scope must be explicit; no inferred season/week coverage beyond available source rows.

## Minimum row fields

Each row in `historical_rookie_replay_v0.json` must include:

- `replay_season`
- `player_id`
- `player_name`
- `position`
- `draft_round`
- `draft_pick`
- `nfl_team`
- `archetype_label`
- `archetype_comp_2026`
- `pre_draft_grade`
- `post_draft_context_tags`
- `expected_role`
- `actual_weekly_ppr`
- `season_ppr`
- `games_played`
- `startable_weeks`
- `spike_weeks`
- `bust_weeks`
- `weekly_volatility`
- `role_materialized`
- `target_share_materialized`
- `environment_supported`
- `model_was_right_for_wrong_reason`
- `model_was_wrong_for_right_reason`
- `evidence_status`
- `notes`
- `source`
- `generated_at`

## Evidence statuses (allowed values)

`evidence_status` must resolve to exactly one of:

- `supported`
- `partially_supported`
- `contradicted`
- `needs_verification`
- `stale_or_missing_data`

## Field semantics (v0 high-level)

- `archetype_label`: replay-side label representing the evaluated rookie archetype in-season.
- `archetype_comp_2026`: forward-looking comp anchor used for 2026 archetype mapping comparison.
- `post_draft_context_tags`: bounded list of context tags that affected expectation quality.
- `actual_weekly_ppr`: ordered weekly PPR series for the replay season, scoped only to supported weeks.
- `weekly_volatility`: deterministic volatility measure derived from `actual_weekly_ppr`.
- `role_materialized`: whether expected role appeared in completed-season usage/outcomes.
- `target_share_materialized`: whether expected target-share thesis appeared in completed-season usage/outcomes.
- `environment_supported`: whether team/offense environment evidence supported the thesis context.
- `model_was_right_for_wrong_reason`: true when outcome aligned but causal thesis failed evidence checks.
- `model_was_wrong_for_right_reason`: true when outcome missed but supporting thesis conditions were directionally correct.

## Non-goals (v0)

Historical Rookie Replay v0 does **not**:

- fetch data,
- scrape sources,
- generate replay artifacts in this PR,
- change scoring definitions,
- modify downstream repositories.
