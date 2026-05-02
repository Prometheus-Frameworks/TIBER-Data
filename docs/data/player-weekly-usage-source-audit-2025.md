# 2025 Player Weekly Usage Source Audit (player_weekly_usage_v1)

## 1. Purpose

This audit determines whether a **source-backed** `player_weekly_usage_v1` input can be derived from committed repo evidence plus the known `nflreadpy.load_player_stats([2025])` column set, **without inventing data**.

Scope is intentionally bounded to QB/RB/WR/TE weekly usage signals that are truly supported by source-backed fields today.

## 2. Current contract summary

Current `player_weekly_usage_v1` export contract expects these row fields:

- identity/context: `season`, `week`, `player_id`, `player_name`, `team`, `position`, `opponent`
- receiving/routing: `targets`, `receptions`, `routes_run`, `route_participation`, `target_share`, `air_yards`, `air_yards_share`
- rushing/opportunity: `rushing_attempts`, `team_rushing_attempts`, `rush_share`, `red_zone_targets`, `red_zone_carries`
- playing time: `snap_share`
- metadata: `source`, `generated_at`

Current lane and paths:

- raw fixture input: `data/raw/evidence/player_weekly_usage_2025.offline_fixture.json`
- promoted artifact: `exports/promoted/nfl/player_weekly_usage_v1.json`
- artifact builder: `src/export/playerWeeklyUsageArtifact.ts`
- contract doc: `docs/data/player-weekly-usage-v1.md`
- export tests: `test/playerWeeklyUsageArtifact.export.test.ts`

Current semantics are fixture-backed scaffold data for 2025 (`historical_backtest` mode), with fail-closed duplicate detection at `season/week/player_id`.

## 3. Available source-backed fields

From the known `nflreadpy.load_player_stats([2025])` columns, these usage-supporting fields are available now:

- identity/week/team context: `player_id`, `player_name`, `player_display_name`, `position`, `season`, `week`, `team`, `opponent_team`
- receiving usage: `targets`, `receptions`, `receiving_air_yards`, `target_share`, `air_yards_share`, `wopr`
- rushing usage: `carries`
- first-down signal: `rushing_first_downs`, `receiving_first_downs`
- efficiency signal: `rushing_epa`, `receiving_epa`
- YAC signal: `receiving_yards_after_catch`
- outcomes cross-check (already source-backed in adjacent lane): `fantasy_points_ppr`

These are valid source-backed candidates for a usage lane because they are direct columns from the stated player stats source.

## 4. Missing or unsupported fields

The following fields are **not available** from current `nflreadpy.load_player_stats([2025])` columns and should remain explicitly unsupported unless another governed source is added:

- `route_participation`
- `routes_run`
- `snap_share`
- `red_zone_targets`
- `end_zone_targets`
- `goal_line_carries`
- slot/wide alignment usage
- personnel grouping usage
- depth chart role
- injury-created opportunity attribution
- team-level denominator required for `team_rushing_attempts` and derived `rush_share` (not present as direct column in the known set)

Boundary: route/snap/red-zone claims must not be inferred from generic box score columns.

## 5. Mapping recommendation

Recommended mapping status against source columns:

| Usage field (current/future) | Source column(s) | Status | Notes |
|---|---|---|---|
| `season` | `season` | available | Direct. |
| `week` | `week` | available | Direct. |
| `player_id` | `player_id` | available | Exact ID only. |
| `player_name` | `player_name` (or `player_display_name`) | available | Prefer stable canonical name policy per lane. |
| `team` | `team` | available | Direct in known set. |
| `position` | `position` | available | Direct. |
| `opponent` | `opponent_team` | available | Contract field rename only. |
| `targets` | `targets` | available | Direct. |
| `receptions` | `receptions` | available | Direct. |
| `rushing_attempts` | `carries` | available | Contract rename only. |
| `air_yards` | `receiving_air_yards` | available | Contract rename only. |
| `target_share` | `target_share` | available | Direct. |
| `air_yards_share` | `air_yards_share` | available | Direct. |
| `wopr` (future) | `wopr` | available but contract extension needed | Useful receiving opportunity composite. |
| `receiving_yards_after_catch` (future) | `receiving_yards_after_catch` | available but contract extension needed | Useful usage/output decomposition. |
| `rushing_first_downs` (future) | `rushing_first_downs` | available but contract extension needed | Opportunity conversion signal. |
| `receiving_first_downs` (future) | `receiving_first_downs` | available but contract extension needed | Opportunity conversion signal. |
| `rushing_epa` (future) | `rushing_epa` | available but contract extension needed | Per-week rushing efficiency context. |
| `receiving_epa` (future) | `receiving_epa` | available but contract extension needed | Per-week receiving efficiency context. |
| `routes_run` | — | not available from this source | Requires route participation source. |
| `route_participation` | — | not available from this source | Requires route/snap source. |
| `snap_share` | — | not available from this source | Requires snap-count source. |
| `red_zone_targets` | — | not available from this source | Requires play-location tagging source. |
| `red_zone_carries` | — | not available from this source | Requires play-location tagging source. |
| `team_rushing_attempts` | — | not available from this source | Could be computed only if team totals are separately sourced/governed. |
| `rush_share` | — | not available from this source | Blocked by missing team rushing denominator. |

## 6. Source-backed lane recommendation

Recommended next implementation lane (separate PR from this audit):

1. Add `sourceKind` support to `player_weekly_usage_v1` consistent with roster/PPR patterns (`offline_fixture` default, explicit `source_backed`).
2. Add `scripts/build_player_weekly_usage_source_backed_2025.py` to create:
   - `data/processed/evidence/player_weekly_usage_2025.source_backed.json`
3. Generate source-backed rows using only supported columns listed as **available** above.
4. Keep current fixture/promoted artifact behavior unchanged unless explicit source-backed export path is invoked.
5. Fail closed when source-backed file is missing.
6. Use exact `player_id` joins only where cross-lane joins are needed (no fuzzy matching on names).
7. Keep unsupported route/snap/red-zone fields documented as unsupported rather than synthesized.

## 7. GOBLIN implications

With identity + source-backed PPR outcomes + available usage columns, these flags become computable now (or with straightforward weekly delta logic):

- `low_ppr_high_target_share`
- `low_ppr_high_targets`
- `air_yards_without_output`
- `carries_without_points`
- `target_share_without_touchdown`
- `wopr_without_ppr_output`
- `rookie_ramp_hidden_by_low_volume` (if position + week trend windows are applied in governed downstream logic)
- `usage_spike_without_box_score` (if prior-week deltas are computed deterministically)

Still blocked from current source column set:

- `high_route_participation_low_output`
- `red_zone_usage_without_td`
- `end_zone_targets_without_td`
- `snap_share_jump_without_points`

These blocked flags require a separate source that contains route, snap, and/or red-zone/end-zone participation fields.

## 8. Guardrails

- No invented usage fields.
- No fuzzy matching.
- No route/snap/red-zone claims from `nflreadpy.load_player_stats([2025])` alone.
- Source-backed fields must be labeled with provenance in produced evidence files.
- Fixture scaffolds remain explicitly labeled fixture-only.
- Missing source support must be documented, not filled.

## 9. Recommended next Codex task

Add source-backed `player_weekly_usage_v1` lane from `nflreadpy` player stats using only supported fields, while documenting unsupported route/snap/red-zone fields.
