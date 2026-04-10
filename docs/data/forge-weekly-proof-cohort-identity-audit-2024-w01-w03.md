# FORGE proof cohort identity audit (2024 W1–W3 ATL/DET)

Scope: narrow 8-player proof cohort only, for current support/derived comparison lanes.

## Evidence boundary

- Legacy raw lane rows are present in-repo (`weekly_player_stats.offline_fixture.json`) for W1–W3.
- Legacy derived lane rows are present in-repo (`skill_offline_fixture.derived.json`) for W1–W3.
- Upstream scaffold raw/derived artifacts for W1–W3 are **not committed in this repo snapshot**, so this audit records the known mismatch from current local comparison findings and marks the rest unresolved until upstream row snapshots are checked in/reproduced in-place.

## Cohort identity matrix

| player_name | team | legacy_id | upstream_id | status | note |
|---|---|---|---|---|---|
| Amon-Ra St. Brown | DET | `00-0037834` | `00-0036963` | `mismatch` | Primary observed mismatch from current local comparison runs; legacy id appears stale/local versus upstream lane identity. |
| Bijan Robinson | ATL | `00-0038134` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |
| Drake London | ATL | `00-0039152` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |
| Jahmyr Gibbs | DET | `00-0036976` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |
| Jared Goff | DET | `00-0033901` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |
| Kirk Cousins | ATL | `00-0037183` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |
| Kyle Pitts | ATL | `00-0038122` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |
| Sam LaPorta | DET | `00-0038047` | `unknown` | `unresolved` | Legacy id stable across raw+derived; upstream row snapshot not available in-repo for this audit pass. |

## Derived-lane consistency note

For all 8 cohort players, legacy derived W1–W3 `playerId` matches legacy raw W1–W3 `player_id` in this repo snapshot.
