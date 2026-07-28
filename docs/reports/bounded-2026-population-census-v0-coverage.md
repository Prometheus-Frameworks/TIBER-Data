# Bounded 2026 Population Census v0 Coverage Report

## Decision

```text
bounded_2026_census_v0_ready
```

This decision means the bounded candidate artifact required by TIBER-Data #227
is reproducible and validation-ready for operator/auditor review. It does not
promote the artifact, claim full-universe coverage, authorize downstream
consumption, or authorize a Forecast run.

## Review lock

- TIBER-Data implementation base:
  `31c0c8e751816d262cf79ffef1a4ae9b6c9b70d5`
- Candidate path:
  `exports/candidates/population_census/bounded_2026_population_census_v0.json`
- Candidate SHA-256:
  `6057031bfc6dfedac1a5b2957ec194e738df5fbdb12dfec80d1e8ad773f0d1ea`
- Schema:
  `schemas/bounded_2026_population_census_v0.schema.json`
- Validation report:
  `exports/candidates/population_census/bounded_2026_population_census_v0.validation.json`
- Scope:
  `historical_offense_plus_2026_rookies_v0`
- Status:
  `candidate_governed_artifact_not_promoted`

## Source reproduction

| Source | Commit | Artifact SHA-256 | Governance evidence SHA-256 | Source rows | Included rows |
| --- | --- | --- | --- | ---: | ---: |
| TIBER-Data promoted `player_season_coverage_v0` | `31c0c8e751816d262cf79ffef1a4ae9b6c9b70d5` | `d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac` | `5e9a382db0681e7a808a1d5fdf4334653cf2f0b26314c45425b333aa2024d154` | 3,016 | 610 (`season == 2025`) |
| TIBER-Rookies promoted transition profile v0.2 | `a825431402f89f7ec4fe69e72de073ca4b301ea3` | `c95b941c7855612daccfc2226fc51e0e34dbb2ebe8a2487596675d2522a22f37` | `0acf361c6d2d8cc6f684026481a5aa279e9f7fa718256fad78da0366d5804413` | 48 | 48 (every row) |
| **Total** |  |  |  | 3,064 source rows inspected | **658 census rows** |

Both artifacts and their governance manifests were read from the exact pinned
git commits. No source download, provider request, credential, paid/licensed
source, or cross-repository write occurred.

The 610 selected historical rows retain original source-array indices
`2406..3015`; the 48 rookie rows retain original indices `0..47`. These are
indices in the complete pinned source arrays, not indices assigned after cohort
filtering.

## Population coverage

| Population kind | QB | RB | TE | WR | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2025 historical offense rows | 81 | 151 | 138 | 240 | 610 |
| 2026 rookie-transition rows | 5 | 9 | 11 | 23 | 48 |
| **Total** | **86** | **160** | **149** | **263** | **658** |

Every row is in the declared QB/RB/WR/TE offense domain. This is a property of
the two pinned cohorts, not a claim that those positions are complete across
the NFL or fantasy universe.

## Identity coverage

| Identity state | Rows |
| --- | ---: |
| TIBER-Data canonical/source-verified | 610 |
| TIBER-Rookies source ID present; canonical cross-namespace ID unresolved | 48 |
| Missing source ID | 0 |
| **Total** | **658** |

The 48 rookie IDs remain unresolved by design. No exact governed
TIBER-Rookies-to-TIBER-Data identity contract was admitted under this issue.
Names were not compared or normalized. Preserving these rows is preferable to
inventing canonical continuity.

## Team evidence

| Team state | Rows |
| --- | ---: |
| Source-backed 2025 historical team | 610 |
| Source-backed 2026 drafted team | 47 |
| Source-backed 2026 UDFA-signed team | 1 |
| Explicit free agent | 0 |
| Explicit unsigned | 0 |
| Unknown in source | 0 |
| **Total** | **658** |

The absence of free-agent/unsigned/unknown rows is an observed property of the
pinned inputs. Builder fixtures prove those states remain explicit when
present. Historical teams are labeled 2025 and are not reinterpreted as 2026
roster truth.

## Reconciliation

| Ledger | Groups/rows |
| --- | ---: |
| Duplicate source-ID groups | 0 |
| Duplicate resolved canonical-ID groups | 0 |
| Cross-source canonical identity collision groups | Unevaluable (`null`) |
| Exact cross-source source-ID string reuse groups | 0 |
| Duplicate source-row-hash groups | 0 |
| Unresolved identity rows | 48 |
| Missing identity rows | 0 |

All 48 unresolved rows are itemized in the artifact's reconciliation ledger.
All 658 source rows have unique `population_row_id` values and exact canonical
source-row hashes.

The canonical collision count is not zero. It is unevaluable because the
TIBER-Data and TIBER-Rookies identifiers occupy distinct namespaces and this
issue admits no exact cross-namespace identity contract. A separate ledger
shows raw source-ID string reuse without interpreting it as identity.

## Determinism and validation evidence

The following checks pass:

- JSON Schema validation;
- exact source artifact and governance-manifest hash verification;
- source-envelope and included-row-count checks;
- original source-array index preservation and range checks, including a
  filtered-cohort regression fixture;
- per-field/per-source-ref provenance association checks, including preserved
  null verification timestamps and their source notes;
- stable `population_row_id` fixtures;
- duplicate/collision preservation and tamper-negative fixtures;
- unresolved/missing identity preservation;
- rookie/history-unresolved preservation;
- explicit free-agent/unsigned/unknown team fixtures;
- count-map and reconciliation invariants;
- recursive ban on forecast, ranking, advice, and activity assertion fields;
- deterministic reconstruction against both pinned git blobs;
- canonical serialization check;
- two-build byte comparison.

The generated validation report records:

```text
validation_status=passed
population_row_count=658
source_pins_verified=true
deterministic_source_rebuild_equal=true
forecast_run_authorized=false
promotion_authorized=false
```

## Who is not represented

The artifact does not establish coverage for:

- any player absent from both pinned source cohorts;
- roster-only players who produced no 2025 row and are not in the 48-row rookie
  profile;
- the complete 2026 rookie class;
- IDP;
- kickers, punters, long snappers, or other undeclared positions;
- a complete active/current NFL or fantasy-player universe.

No active/inactive or availability state is inferred from absence.

## Required next gate

The candidate requires independent artifact/contract audit and operator
acceptance before any merge or downstream-use decision. TIBER-Data #227 does
not authorize Forecast consumption, cutoff admission, production publication,
promotion, or execution of the parked 2026 candidate.
