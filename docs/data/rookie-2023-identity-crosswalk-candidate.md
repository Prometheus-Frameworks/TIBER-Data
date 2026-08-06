# 2023 skill-class identity crosswalk candidate v0.1.0

## Status and purpose

This document defines the candidate-only identity interface produced for
TIBER-Data #237. It covers all 80 drafted 2023 QB/RB/WR/TE players and binds
three source namespaces where evidence permits:

- GSIS from the pinned TIBER-Rookies draft census;
- the Rookies slug copied from that same census row; and
- TIBER-Data's source-player `player_id`, but only when the exact GSIS appears in
  the promoted Data coverage artifact with `identity_confidence` equal to
  `source_verified`.

The governed TIBER canonical namespace is distinct: identity crosswalk v1 uses
`tiber_player_id` values such as `tiber-data-player-2025-puka-nacua`. That
Sleeper-only artifact has no GSIS field, so there is no admissible non-name
edge from this census to a governed `tiber_player_id`. The candidate therefore
sets `tiber_canonical_player_id` to null for all 80 rows and records the
namespace decision as blocked. It does not invent IDs.

Forecast is a separate, blocked edge. The candidate records exact source-row
assertions and conflicts; it does not resolve, rewrite, or mutate Forecast.
This artifact is not promoted and does not change the governed Sleeper-only
identity crosswalk v1.

## Candidate artifacts

| Artifact | Purpose |
| --- | --- |
| `exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.json` | 80-row census and versioned crosswalk candidate |
| `exports/candidates/identity_crosswalk/rookie_2023_identity_conflicts_v0.1.0.json` | Explicit conflict ledger and impacted-artifact inventory |
| `exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.manifest.json` | Version/hash binding for consumers |
| `exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.validation.json` | Deterministic validation result |

The manifest binds downstream consumers to crosswalk version `0.1.0` and
SHA-256 `db1a08192aacf604d0be7930147b3e0182c28250bda246c65fbca290ed9a11e2`.
Consumers must verify both values before joining. A later rebuild with a
different hash is a different input even if the version string is unchanged.

## Source locks

| Role | Repository / commit | Path | SHA-256 | Status |
| --- | --- | --- | --- | --- |
| Class, GSIS, slug, draft team | `Prometheus-Frameworks/TIBER-Rookies@8c95723ee08de2186ede74163fbb379969764296` | `data/historical/reconstruction_2023/2023_skill_class_census_v0.json` | `90796d23a35547a43555fa9d6a4d519081fa424406ee9d56da59775ef291012f` | Pinned draft-PR census, not promoted |
| Data source-player identity/history | `Prometheus-Frameworks/TIBER-Data@711d6ee158d4e3bd116d1df4d76dea282200454d` | `exports/promoted/nfl/player_season_coverage_v0.json` | `d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac` | Promoted governed artifact keyed by GSIS-like `player_id` |
| Governed TIBER canonical namespace | `Prometheus-Frameworks/TIBER-Data@3df598a43e6af41ccf0bbd9db206bc4504b5a8b2` | `exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json` | `5ce5cd3f5dc8fd27c28c5a5fb283431ac648f764c3f8f2b645f6ad924338f263` | Promoted Sleeper-to-`tiber_player_id` artifact; no GSIS edge |
| Forecast source fixture | `Prometheus-Frameworks/TIBER-Forecast@813eff8de0b4a8d4f29f5c37abe522fe3e792ca3` | `src/datasets/seasonal/fixtures/seasonalPprSeedSnapshot.ts` | `3f9862b7b5d1b92bbb777399617c501328fcc00358e665c74c84cf368856f4f2` | Scaffold fixture, not governed identity evidence |
| Forecast emitted rows | same Forecast commit | `data/backtests/seasonal-ppr/seasonal_ppr_predictions.jsonl` | `0955ffbeb750dff5659fbaa115eba4dcc208223a6b3a2859a7256a989ad34c09` | Existing emitted artifact, read-only here |

The committed assertion snapshot is
`data/candidate/identity/rookie_2023_identity_source_assertions_v0.json`,
SHA-256 `4c60962d5397b86acd13ed333d155ac9278ec04c3cc6e77c1527064bb3e26084`.
It copies the 80 pinned census assertions, eleven exact Forecast source-row
locators, and the explicit Tank Dell name-override lineage. It is an input
fixture, not an authority upgrade for the unmerged Rookies census.

## Identity contract

Permitted player joins are exact `gsis_id`, `crosswalk_row_id`, or an explicit
source-row assertion ID. Display-name, normalized-name, and fuzzy-name joins
are forbidden. Names and positions in the artifact are audit descriptors only.

The exact-GSIS Data source-player edge has three explicit states:

| State | Rows | Meaning |
| --- | ---: | --- |
| `exact_gsis_source_verified_in_2023_reg` | 68 | Exact GSIS appears in the promoted 2023 REG records |
| `exact_gsis_source_verified_in_later_promoted_reg_only` | 8 | Exact GSIS first appears in a later promoted REG season |
| `unresolved_no_governed_data_record` | 4 | No exact GSIS record exists in the promoted Data artifact |

The four unresolved Data source-player rows are Stetson Bennett (`00-0039107`), Zack Kuntz
(`00-0038406`), DeWayne McBride (`00-0039046`), and Max Duggan
(`00-0038637`). Their sourced GSIS and Rookies slug remain present, but
`tiber_data_source_player_id` stays null.

Separately, all 80 `tiber_canonical_player_id` values stay null with
`unresolved_no_admissible_gsis_to_tiber_player_id_edge`. The promoted V1
crosswalk is inventoried, but its display descriptors cannot be used to bridge
GSIS to `tiber_player_id`. This is an operator-owned namespace gap and makes
the full canonical crosswalk terminal state
`rookie_2023_identity_crosswalk_blocked`.

Display-name and position differences under an already exact GSIS are
preserved as non-joining audit context. This includes Marvin Mims / Marvin
Mims Jr., Chris Rodriguez / Chris Rodriguez Jr., Lew Nichols / Lew Nichols
III, Grant Dubose / Grant DuBose, and the draft-WR/current-TE contexts for
Justin Shorter and Elijah Higgins.

### Explicit name override lineage

The Rookies census already emits `Tank Dell`, which could otherwise hide the
upstream `Nathaniel Dell` spelling. The crosswalk therefore carries a
structured override keyed by GSIS `00-0038977`. It records the upstream and
target names, target slug, reason, and immutable refs to the pinned Rookies
census builder and `docs/draft-results-provenance.md`. It is slug lineage only;
it does not permit a display-name join.

## Forecast fail-closed policy

Eight Forecast Run 1 source rows are bound to 2023 census rows through explicit
candidate overrides over a unique exact non-name 2024 fingerprint: position,
canonical team, games played, receptions, and targets. Each override is keyed
by the Forecast row index/raw ID/raw-line hash and the target GSIS, carries both
Forecast and Data source pins, and remains `needs_operator_review`. Display
names are audit-only. Every raw Forecast ID disagrees with the target governed
GSIS, and none resolves:

| Subject descriptor | Forecast raw ID | Governed GSIS |
| --- | --- | --- |
| Bijan Robinson | `00-0036223` | `00-0038542` |
| Jahmyr Gibbs | `00-0037539` | `00-0039139` |
| De'Von Achane | `00-0038120` | `00-0039040` |
| Chase Brown | `00-0035685` | `00-0038597` |
| Puka Nacua | `00-0038543` | `00-0039075` |
| Jaxon Smith-Njigba | `00-0039051` | `00-0038543` |
| Sam LaPorta | `00-0037744` | `00-0039065` |
| Dalton Kincaid | `00-0038996` | `00-0038933` |

Five raw Forecast IDs are also governed GSIS identities for different 2023
census players. Those collision findings affect C.J. Stroud, Bijan Robinson,
Jaxon Smith-Njigba, Tank Dell, and Tucker Kraft. Across the two finding types,
eleven census rows are conflict-exposed and 69 have no known Run 1 subject or
collision. The conflict report contains thirteen findings over eleven unique
Forecast source rows: eight subject mismatches plus five raw-ID collisions,
with two source rows contributing to both categories.

Puka's `00-0038543` Forecast claim is never an alias. In governed Data that ID
belongs to Jaxon Smith-Njigba; Puka's core GSIS is `00-0039075`. Every Forecast
edge has `resolved_forecast_row_identity: null`, `auto_resolution_allowed:
false`, and a conflict-blocked status.

Structural validation succeeds only when every open conflict is explicit,
ledgered, and unresolved. That does not make Forecast consumption ready.

## Canonical team-code policy

`LAR` is the sole canonical Rams output. `LA` is a directed input alias for
`LAR` only when the source namespace is `tiber_data_player_season` and the
season is one of 2023–2025—the years actually observed for this class in the
pinned Data artifact. This is a conservative candidate support boundary, not
a franchise-history claim. `LAC` is always distinct. Reverse emission from `LAR`
to `LA` is forbidden without a separate provider contract.

The 2023 draft-source aliases are separately scoped to
`nflverse_draft_results:2023`: `GNB→GB`, `KAN→KC`, `LVR→LV`, `NOR→NO`,
`NWE→NE`, `SFO→SF`, and `TAM→TB`. Each rule records how many exact-GSIS rows
show the raw census code and matching canonicalized Data draft-team code, plus
both source refs. Every row preserves the raw code and applied rule. Unknown
aliases, missing source namespace, or an invalid season fail closed. Team codes
never participate in player resolution.

## Build and validation

Run from the TIBER-Data repository root:

```bash
python3 scripts/build_rookie_2023_identity_crosswalk_candidate.py
python3 scripts/validate_rookie_2023_identity_crosswalk_candidate.py \
  --report --strict-cross-repo \
  --rookies-repo-root ../TIBER-Rookies \
  --forecast-repo-root ../TIBER-Forecast
python3 -m pytest -q tests/test_rookie_2023_identity_crosswalk_candidate.py
```

The strict validator reads the immutable git blobs from both sibling repos and
checks the Rookies projection, Tank override lineage, all Forecast row/line
hashes, each asserted non-name fingerprint against its exact pinned seed row,
and all 16 bounded Forecast inventory hashes. It also checks local
source hashes, a byte-identical deterministic rebuild,
80-row coverage and uniqueness, exact-GSIS-only Data links, all Forecast
conflicts and collisions, the 0/80 governed TIBER canonical gap, Puka's two-ID
record, non-name override lineage, directional team-alias evidence, artifact
hashes, and the consumer version/hash binding.

## Consumer and authority boundary

Only the exact-GSIS-to-Data-source-player edge is ready for the bounded #236
pilot after that consumer verifies version `0.1.0` and the manifest's
crosswalk SHA-256. The governed `tiber_player_id` edge and every Forecast edge
remain blocked. Disposition of already-emitted Forecast
artifacts requires an operator decision and separate authority. This issue
does not authorize a Forecast rerun, Forecast mutation, artifact
supersession, promotion, or changes to any governed schema or promoted path.
