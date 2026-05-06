# Receiving Role Integrity / route participation proxy scaffold

## Purpose

This document scopes a future **Receiving Role Integrity** evidence lane for route participation or a legal/public proxy for route participation. It is research and provenance infrastructure only: no source-backed artifact is introduced here, no external data is fetched, and no true route participation values are fabricated.

The near-term question is what TIBER-Data can safely support from nflverse/nflreadpy-style public data. The answer today is bounded: TIBER-Data may investigate snap participation, pass-play participation proxies, targeted-route labels, and joinable receiving usage, but it must not claim true charted routes unless an upstream source explicitly provides true route participation coverage.

## Current status

- Source-backed GOBLIN evidence lanes remain unchanged.
- The play-caller PROE lane remains parked behind provenance requirements.
- This lane is **not** a GOBLIN scoring change, candidate-generation change, FORGE change, Teamstate change, Role-and-opportunity change, or TIBER-Fantasy change.
- Existing nflverse participation probing is documented separately in `docs/data/nflverse-participation-route-proxy-audit.md`; that audit found the local environment could import `nflreadpy`, but could not source-verify 2025 participation columns because the data download was blocked.

## Metric distinctions

| Term | Meaning | Safe current TIBER-Data treatment |
|---|---|---|
| True route participation | Charted count/share of routes run by a player on actual pass concepts, typically requiring full eligible-player route charting. | Blocked unless the source explicitly supports true route coverage. Do not infer from targets, snaps, or participant lists. |
| Pass-play participation proxy | Count/share of offensive pass plays on which a player is listed as participating, when public participation data and play-by-play pass-play joins support that denominator. | Potentially derivable proxy after source columns and joins are verified. Must be labeled as a proxy, not routes. |
| Targeted route labels | Route label attached to a targeted receiver or primary receiving event, if present in public play/participation data. | Targeted-player context only unless source documentation proves all eligible-player route labels are present. |
| Snap share | Offensive snaps or share of team offensive snaps for a player in a game/week. | Useful role context, but not route participation and not a pass-play-specific denominator. |
| Target share | Player targets divided by team targets or team pass attempts for a selected window. | Usage metric only; it does not reveal whether non-targeted pass-play participation stayed stable. |
| Targets per route | Targets divided by true routes run. | Blocked unless true routes run are source-backed. |
| Targets per pass-play participation proxy | Targets divided by pass-play participation proxy count. | Potentially derivable proxy after denominator and target joins are verified. Must not be shortened to TPRR. |

## Why route/pass-play participation matters

Receiving output can be misleading without a denominator describing how often the player was actually available in the passing structure.

- **Bad output + stable route/pass-play participation** can indicate hidden role signal. The player may still be earning field time and route opportunity even if box-score production lagged.
- **Bad output + participation collapse** can indicate injury, game script, disciplinary benching, personnel change, or genuine role loss. The box score alone cannot separate those cases.
- **Good output + low participation** can indicate a spike-week trap. Efficiency may be unsustainably high if the player did not own a stable pass-game role.

The future lane should help downstream systems distinguish role integrity from production noise, but only with source-backed participation denominators.

## Expected public-source fields to investigate

The following fields describe the desired public-source shape. They are not a claim that every field exists today in every nflverse/nflreadpy extract.

### Identity and grouping fields

- `season`
- `week`
- `game_id` or a documented game-id equivalent such as `nflverse_game_id`
- `player_id`
- `player_name`
- `team`
- `position`

### Snap participation fields

- `offense_snaps`
- `snap_share`

### Pass-play participation proxy fields

Potential denominator fields must be source-verified before artifact generation. Candidate names used by this scaffold are:

- `pass_play_participation`
- `pass_play_participation_proxy`
- `pass_play_participation_count`
- `offense_pass_play_participation`

If the public source instead exposes play-level offensive participant lists, a future builder may derive a pass-play participation proxy only after documenting:

1. the play identifier join between participation rows and play-by-play;
2. the exact pass-play inclusion rule;
3. how team offensive pass-play denominators are counted;
4. how players are exploded from participant-list fields;
5. how nulls and missing plays fail closed rather than becoming zero participation.

### Joinable receiving usage fields

The proxy lane becomes useful only if receiving usage can be joined or aggregated on the same player/week/team keys:

- `targets`
- `receptions`
- `receiving_yards`

Future follow-ups may investigate `air_yards`, first downs, or touchdown context if those fields are source-backed and joinable, but they are not required by this scaffold.

## Classification of support today

| Candidate output | Current classification | Notes |
|---|---|---|
| `offense_snaps` | expected public role context | Still requires source/version provenance in any artifact. |
| `snap_share` | expected public role context | Useful for total role, not pass-game-specific route opportunity. |
| `pass_play_participation` | conditional proxy | Requires verified participant/play-level source fields or an explicitly supplied public proxy denominator. |
| `pass_play_participation_share` | conditional proxy | Requires team/week pass-play denominator and documented inclusion rules. |
| `targets_per_pass_play_participation_proxy` | conditional proxy | Requires source-backed targets plus source-backed proxy denominator. |
| `targeted_route_label` | targeted-player-only | Do not generalize to non-targeted players unless source coverage proves it. |
| `routes_run` | blocked/proprietary | Do not claim unless true route coverage is explicitly sourced. |
| `route_share` | blocked/proprietary | Same dependency as true routes run. |
| `targets_per_route` / `tprr` | blocked/proprietary | Requires true routes run denominator. |
| `yards_per_route_run` / `yprr` | blocked/proprietary | Requires true routes run denominator. |

## Test-only scaffold

The synthetic fixture at `test/fixtures/receiving_role_integrity_proxy.synthetic.json` validates expected row shape and readiness classification only. It is not source-backed football history and must not be promoted into evidence artifacts.

The helper at `src/research/receivingRoleIntegrityProxyReadiness.ts` classifies rows as:

- `ready_for_proxy_research` when identity fields, snap fields, a pass-play participation proxy denominator, and basic receiving usage fields are present;
- `blocked_missing_shape` when the row lacks required proxy-research shape;
- `blocked_true_route_claim` when unsupported true-route claim fields appear in this scaffold.

This helper does not calculate route participation, pass-play participation, target share, or efficiency metrics.

## No-op scaffold script

Run the scaffold message with:

```bash
node scripts/build_receiving_role_integrity_proxy.mjs
```

The script prints required future inputs and an intended future output path, then exits without fetching data or generating artifacts.

## Required future provenance gates

Before TIBER-Data can produce a source-backed Receiving Role Integrity artifact, a future PR must document:

1. exact upstream package/source, version, license, and attribution requirements;
2. exact detected columns and row counts from a network-permitted source audit;
3. whether any `route`-like field is true full-player route coverage or targeted-player-only context;
4. deterministic pass-play inclusion rules;
5. join keys between participation, play-by-play, roster identity, and receiving usage;
6. null handling that distinguishes unavailable data from zero participation;
7. output schema and downstream contract names that preserve the proxy/true-route distinction.

Until those gates are satisfied, this lane remains documentation plus validation scaffolding only.
