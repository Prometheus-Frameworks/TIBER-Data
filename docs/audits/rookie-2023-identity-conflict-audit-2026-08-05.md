# 2023 rookie identity conflict audit — 2026-08-05

## Outcome

The 80-player candidate census is complete and deterministic. Exact GSIS joins
resolve 76 TIBER-Data source-player IDs; four remain explicit nulls because
the promoted Data coverage artifact has no matching record. The distinct
governed `tiber_player_id` namespace remains unresolved for all 80 rows because
the Sleeper-only V1 crosswalk exposes no GSIS edge. No display-name join was
used and no TIBER ID was minted.

Forecast Run 1 is not safe as identity evidence. All eight audited 2023-class
subject rows carry a raw ID that conflicts with the governed GSIS, and five
raw IDs collide with a different 2023 census identity. The artifact therefore
reports zero resolved Forecast links, eight blocked subject links, thirteen
explicit findings over eleven unique source rows, and eleven conflict-exposed
census records.

## Defect findings

| Finding | Evidence | Disposition in candidate |
| --- | --- | --- |
| Puka Forecast GSIS | Forecast `00-0038543`; governed Data/Rookies `00-0039075` | Both claims preserved; edge unresolved and blocked; wrong ID is not an alias |
| Additional Forecast subject mismatches | Seven other explicit source rows all disagree with governed GSIS | Explicit unique non-name fingerprint overrides carry row/hash lineage, stay `needs_operator_review`, and have no resolution effect |
| Forecast raw-ID collisions | Five raw IDs point at a different 2023 census identity | Separate collision findings; exact-ID joining from this Forecast fixture is unsafe |
| Data coverage gaps | No exact promoted record for Bennett, Kuntz, McBride, or Duggan | Data source-player ID null; sourced GSIS retained |
| TIBER canonical namespace gap | Promoted V1 has `tiber_player_id` but no GSIS field | All 80 TIBER canonical IDs null; full crosswalk blocked; operator decision required |
| Rookies name transformation | Upstream `Nathaniel Dell` becomes `Tank Dell` / `wr-tank-dell` | Explicit GSIS-keyed override with builder/doc lineage |
| Rams code split | Data history can use `LA`; canonical team vocabulary uses `LAR` | Directed, source/date-scoped `LA→LAR`; raw value retained; `LAC` distinct |

## Source availability and limitations

- The class census is pinned to the frozen head of TIBER-Rookies PR #284, not
  to a promoted Rookies artifact. The candidate labels that limitation and
  pins commit, blob, and content hash.
- The Data edge uses the promoted `player_season_coverage_v0` artifact and
  exact GSIS equality. Sixty-eight rows have 2023 REG evidence, eight first
  appear in a later promoted REG season, and four are absent.
- The governed TIBER identity V1 artifact is Sleeper-only. Its human
  descriptors are not an admissible GSIS join, so zero `tiber_player_id` links
  are asserted.
- Forecast's source is an explicitly bundled scaffold fixture. A broader
  evidence check found systemic raw-ID contamination, so this audit stays
  bounded to limitation records and eleven pinned Run 1 source rows. Subject
  bindings use unique exact non-name fingerprints against the pinned Data 2024
  rows, remain `needs_operator_review`, and do not resolve identity. No
  projection values were copied into the crosswalk.
- Historical display names, positions, and team contexts are retained only as
  dated audit descriptors. They cannot resolve player identity.

## Impacted artifact inventory

The machine-readable conflict report pins a bounded direct/reference inventory
and hashes, not a full transitive dependency graph. Its discovery rule searches
the pinned Forecast commit for the seed path, scaffold dataset version, and
known conflicting raw IDs within seasonal source, backtest fixtures, and
reports. Additional transitive consumers remain `needs_verification`. The
primary impacted Forecast lineage is:

- `src/datasets/seasonal/fixtures/seasonalPprSeedSnapshot.ts`;
- `data/backtests/seasonal-ppr/seasonal_ppr_predictions.jsonl`;
- `data/backtests/seasonal-ppr/seasonal_ppr_prediction_explanations.jsonl`;
- `data/backtests/seasonal-ppr/seasonal_ppr_backtest_report.json`;
- the paired `pre_143` baseline prediction/report fixtures; and
- the production-binding review/implementation/activation reports that pin or
  evaluate this lineage; and
- the two seasonal scaffold consumer modules.

The existing promoted TIBER-Data identity crosswalk v1 is Sleeper-only and has
no GSIS field. It is explicitly inventoried as inadmissible for this join and
was not changed. The pinned Rookies census was read as a source and was not
changed. No Forecast file was changed.

## Recommended remediation sequence

1. Allow the #236 pilot to consume only the exact-GSIS-to-Data-source-player
   edge after
   verifying crosswalk version and SHA-256.
2. Have the operator define or source a non-name GSIS-to-`tiber_player_id`
   edge before treating the full crosswalk as ready.
3. Keep all Forecast edges blocked and surface the limitation record wherever
   the affected Run 1 artifacts are reviewed.
4. Have the operator choose correction, supersession, or limitation-only
   treatment for already-emitted Forecast artifacts.
5. Require a separate Forecast issue and authority before any mutation or
   rerun.

## Terminal states

- Bounded source-player edge: ready for the #236 pilot after version/hash check.
- Full governed TIBER canonical crosswalk: `rookie_2023_identity_crosswalk_blocked`.
- Existing Forecast edges: blocked; zero resolved.
- Emitted Forecast disposition:
  `emitted_artifact_identity_remediation_requires_operator_decision`.

These are separate states. Structural validation of a completely represented
conflict ledger does not resolve a Forecast edge or authorize promotion.
