# nflverse Participation Route-Proxy Audit (nflreadpy, 2025 probe)

## Purpose

Assess whether `nflreadpy.load_participation()` can honestly support **route-adjacent proxy metrics** for TIBER-Data without claiming proprietary route truths (true routes run, true route share, true YPRR, true TPRR, true 1D/RR).

This document is an **audit only**. It does not create source-backed production artifacts and does not add GOBLIN candidate generation.

## Source/provenance

- Intended source: `nflreadpy.load_participation([2025])` from nflverse participation data.
- Local inspection path: `scripts/inspect_participation_columns_2025.py`.
- Environment result at audit time: package import succeeded, but participation download failed due network/proxy rejection to GitHub release assets (HTTP tunnel 403).
- Consequence: exact 2025 live column inventory is **not source-verified in this environment** and must be re-run in a network-permitted environment before any source-backed schema claims.

## License/attribution notes

- `nflreadr::load_participation()` documentation indicates 2023+ participation is FTN Data distributed via nflverse.
- FTN Data via nflverse carries attribution requirements (commonly CC-BY-SA 4.0 terms in nflverse docs).
- Any downstream TIBER source-backed artifact using this participation stream must include explicit attribution text and license reference in docs/contracts and output metadata where applicable.
- This audit does not redistribute raw participation rows.

## Column availability

### Local execution status (2026-05-04 UTC)

- `load_participation` callable: **yes**.
- 2025 data fetch: **failed in current environment** (proxy/network block).
- Row count and concrete columns: **unavailable locally at this time**.

### Requested column probes

Probe targets to verify when script is run with network access:

- `players_on_play`
- `offense_players`
- `defense_players`
- `offense_formation`
- `offense_personnel`
- `defense_personnel`
- `n_offense`
- `n_defense`
- `route`
- `possession_team`
- `season`
- `week`
- `play_id`
- game identifier candidate: `game_id` or `nflverse_game_id`

## Metrics directly supported

Only metrics with explicit source support and verified columns should be treated as directly supported. In this environment, direct support is **not yet confirmed** because the participation table could not be loaded.

## Metrics honestly proxyable

If full offensive participant lists and play identifiers are present, and pass-play status is joined from play-by-play:

- pass-play participation per player (proxy for route opportunity, not true routes)
- pass-play participation share by team/week
- targets per pass-play participation (with usage/pbp join)
- receiving yards per pass-play participation (with stats/pbp join)
- air yards per pass-play participation (with pbp join)

All above remain **conditional pending column verification**.

## Metrics blocked/proprietary

Without true route participation coverage for all eligible receivers on each pass play, the following remain blocked/proprietary:

- true routes run
- true route share
- true YPRR
- true TPRR
- true 1D/RR

Do not alias proxy metrics as these truths.

## Recommended TIBER naming

Use explicit proxy naming and avoid “route” truth labels unless fully source-backed:

- `pass_play_participation`
- `pass_play_participation_share`
- `targets_per_pass_play_participation`
- `receiving_yards_per_pass_play_participation`
- `air_yards_per_pass_play_participation`
- `targeted_route_type` (only if clearly limited to targeted/primary context)

Avoid names such as `routes_run`, `route_share`, `yprr`, `tprr`, `first_downs_per_route_run` unless true route coverage is explicitly proven.

## GOBLIN implications

- GOBLIN can consume pass-play participation proxies once source-backed and contract-documented.
- GOBLIN must not claim route-truth features when only participation proxies exist.
- Null/unavailable values must remain null/unavailable; never coerce to zero.

## Data Lab UI implications

- UI labels should explicitly say “pass-play participation proxy”.
- Tooltip language should distinguish proxy opportunity from true route participation.
- Any route-type display should be marked targeted-player-only unless proven otherwise.

## Audit questions (current answers)

1. **Does nflreadpy participation expose all offensive players on a play?**  
   Unconfirmed locally due blocked download; requires rerun of inspection script with data access.
2. **Can we identify pass plays directly from participation, or do we need to join play-by-play?**  
   Assume play-by-play join required unless participation includes explicit pass flag; unconfirmed locally.
3. **Does `route` describe every eligible receiver, or only targeted/primary receiver?**  
   Unconfirmed locally; treat as targeted-player-only until proven otherwise.
4. **Can we derive pass-play participation per player?**  
   Potentially yes if player-on-play fields exist + pass-play join; pending verification.
5. **Can we derive pass-play participation share by team/week?**  
   Potentially yes with possession team + season/week + pass-play join; pending verification.
6. **Can we derive targets per pass-play participation by joining usage/PPR/pbp data?**  
   Potentially yes; pending join-key and column verification.
7. **Can we derive yards per pass-play participation?**  
   Potentially yes via join; pending verification.
8. **Can we derive air yards per pass-play participation?**  
   Potentially yes via pbp join; pending verification.
9. **Can we derive true YPRR/TPRR/route share?**  
   No, not honestly, unless true route participation coverage for all eligible receivers is source-proven.
10. **What attribution/license language is required for FTN Data via nflverse?**  
    Include explicit FTN via nflverse attribution and applicable CC-BY-SA 4.0 notice/link in downstream source-backed artifacts.

## Metric classification table

| Metric | Classification | Notes |
|---|---|---|
| true routes run | blocked/proprietary | Requires true route participation coverage. |
| true route share | blocked/proprietary | Same dependency as above. |
| true YPRR | blocked/proprietary | Requires true routes run denominator. |
| true TPRR | blocked/proprietary | Requires true routes run denominator. |
| true 1D/RR | blocked/proprietary | Requires true routes run denominator. |
| pass_play_participation | derivable proxy | Needs offensive participant field + pass-play join. |
| pass_play_participation_share | derivable proxy | Needs team/week grouping + pass-play join. |
| targets_per_pass_play_participation | needs play-by-play join | Proxy metric, not TPRR. |
| receiving_yards_per_pass_play_participation | needs play-by-play join | Proxy metric, not YPRR. |
| air_yards_per_pass_play_participation | needs play-by-play join | Proxy metric using air-yards source. |
| targeted_route_type | targeted-player-only | Do not generalize to all eligibles. |
| snap/personnel/formation context | directly source-backed (pending local verification) | Expected participation context fields; verify with script output. |

## Recommended next PR

1. Run `scripts/inspect_participation_columns_2025.py` in a network-permitted environment and commit only a markdown audit update (no raw data).
2. Update this audit with exact detected columns, row counts, and concrete yes/no answers for Questions 1–8.
3. Draft a contract-safe proxy schema proposal (separate PR) only for metrics proven source-backed or derivable with documented joins.
4. Add attribution boilerplate for FTN via nflverse before any source-backed export artifact is introduced.

