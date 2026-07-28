# Bounded 2026 Population Census v0

## Status and purpose

`bounded_2026_population_census_v0.1.0` is the TIBER-Data contract for the
candidate artifact at:

```text
exports/candidates/population_census/bounded_2026_population_census_v0.json
```

The artifact is a deterministic, row-preserving declaration of the bounded
population authorized by TIBER-Data issue #227. It is not a current roster, a
complete active-player universe, a forecast, a ranking, or a promotion.

The JSON Schema is:

```text
schemas/bounded_2026_population_census_v0.schema.json
```

## Scope identity

```text
historical_offense_plus_2026_rookies_v0
```

Exactly two cohorts are included:

1. every record whose `season == 2025` in TIBER-Data's promoted
   `player_season_coverage_v0`; and
2. every row in TIBER-Rookies' promoted 2026 rookie-transition profile v0.2.

The source lock is part of the contract:

| Source cohort | Repository commit | Path | SHA-256 | Included rows |
| --- | --- | --- | --- | ---: |
| 2025 player-season coverage | `Prometheus-Frameworks/TIBER-Data@31c0c8e751816d262cf79ffef1a4ae9b6c9b70d5` | `exports/promoted/nfl/player_season_coverage_v0.json` | `d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac` | 610 |
| 2026 rookie transition v0.2 | `Prometheus-Frameworks/TIBER-Rookies@a825431402f89f7ec4fe69e72de073ca4b301ea3` | `exports/promoted/rookie-transition-profile/2026_rookie_transition_profile_v0.json` | `c95b941c7855612daccfc2226fc51e0e34dbb2ebe8a2487596675d2522a22f37` | 48 |

The builder also verifies the promotion/governance manifests at the same
commits:

- TIBER-Data
  `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json`,
  SHA-256
  `5e9a382db0681e7a808a1d5fdf4334653cf2f0b26314c45425b333aa2024d154`;
- TIBER-Rookies
  `exports/promoted/rookie-transition-profile/2026_manifest.json`, SHA-256
  `0acf361c6d2d8cc6f684026481a5aa279e9f7fa718256fad78da0366d5804413`.

No provider fetch, credential, fuzzy lookup, display-name match, or new source
is part of this contract.

## Explicit exclusions

This scope does not represent:

- players absent from both source cohorts;
- a complete current or active NFL/fantasy-player universe;
- IDP full-universe coverage;
- kickers, punters, long snappers, or other undeclared domains;
- 2026 active/inactive, rostered, injury, or availability state inferred from
  absence;
- Forecast cutoff admission, model eligibility, execution, advice, or
  promotion.

The 2025 cohort is production/history evidence. Its team fields remain labeled
as 2025 source context and must not be interpreted as a 2026 team or roster
assertion.

## Row contract

Every source row produces exactly one `population_rows[]` entry.

Required row fields are:

- `population_row_id`: stable deterministic census-row identifier;
- `population_kind`: `historical_offense_2025` or
  `rookie_transition_2026`;
- `source_identity_ref`: source artifact key, source namespace, source player
  ID (nullable), source identity confidence (nullable), source row key,
  original source-row index, and canonicalized source-row SHA-256;
- `canonical_player_id`: source-verified Data identifier or `null`;
- `identity_status`: explicit resolution state;
- source-carried `player_name` and `position`, plus `position_status`;
- `history_status`;
- `team_assignment`: source-backed teams, primary team, source season, and an
  explicit status;
- `availability_evidence`: source artifact timestamp plus losslessly associated
  provenance records. Each record retains its field/ref name, value state,
  source type/name/URL, observed/update/verification timestamp (including
  `null`), confidence/band, and notes together.

Rows do not carry production totals, projected values, scores, ranks, advice,
or activity assertions.

### Stable population row identity

`population_row_id` is the prefix `pop2026v0-` plus the first 32 hexadecimal
characters of SHA-256 over:

```text
scope_id
source_artifact_key
source identity key
duplicate occurrence
```

The source identity key uses the source namespace's own player ID and declared
season/class grain. It does not use display names. Duplicate occurrences are
ordered by canonical source-row hash, then original row index. Consequently,
IDs are byte-stable for the pinned sources and remain stable when distinct
source rows are reordered.

The full canonicalized source-row hash remains in `source_row_sha256`, so the
validator can prove that each exact input row was represented. Availability
provenance is not flattened: a null verification timestamp stays attached to
the same source field, URL, and explanatory notes that supplied it.

`source_row_index` always means the row's zero-based index in the complete,
unfiltered source artifact array. Filtering a cohort must carry that original
index forward; it must never re-enumerate the selected subset.

## Identity policy

The only allowed join policy is:

```text
exact_source_identity_only_no_cross_namespace_join
```

TIBER-Data historical `player_id` values are carried as
`canonical_player_id` with `canonical_id_source_verified` only when the source
row itself declares `identity_confidence: source_verified`. Provisional or low
source identities remain present as source IDs but have null canonical IDs and
an unresolved state.

TIBER-Rookies `player_id` values are retained under the
`tiber_rookies_player_id` source namespace. They are not asserted to be
canonical TIBER-Data IDs. Without an exact governed cross-namespace mapping,
their `canonical_player_id` is `null`, their identity is
`source_id_present_canonical_unresolved`, and their history is
`history_unresolved_no_exact_crosswalk`.

Equal display names never resolve identity. Exact source-ID string reuse across
the two namespaces is reported separately for review, but is not called a
canonical collision and is not treated as a join.

## Team-state policy

The artifact preserves only source-carried team evidence:

- historical rows: 2025 `teams` and `primary_team`;
- rookie rows: the observed 2026 team from
  `official_postdraft_outcome`, distinguished as drafted or UDFA-signed;
- explicit free-agent or unsigned tokens, if present;
- `source_unknown` when the source does not provide a team.

The builder never replaces unknown/free-agent/unsigned state with a plausible
team and never infers current activity.

## Reconciliation ledger

The top-level `reconciliation` object itemizes:

- duplicate source IDs within a source;
- duplicate resolved canonical IDs;
- every unresolved identity row;
- every missing identity row;
- cross-source canonical collision evaluation state;
- exact source-ID strings reused across source namespaces;
- duplicate canonical source-row hashes.

All source rows remain in `population_rows`, including duplicate, missing-ID,
unresolved, rookie, and unknown-team rows. A reconciliation finding is never
permission to drop a row.

Because the two source ID namespaces have no admitted exact crosswalk,
cross-source canonical collision evaluation is explicitly
`unevaluable_no_exact_cross_namespace_contract`; its collision count is
`null`, never a misleading numeric zero. Raw equal-string reuse is itemized in
the separate `cross_source_source_id_reuse` ledger.

Each coverage count map must sum exactly to `population_row_count`.

## Deterministic build and validation

The builder reads immutable git blobs, not mutable working-tree copies:

```bash
python scripts/build_bounded_2026_population_census_v0.py \
  --data-repo-root . \
  --rookie-repo-root /path/to/read-only/TIBER-Rookies
```

Validate the schema, pins, governance manifests, row invariants, canonical
serialization, and a fresh deterministic source reconstruction:

```bash
python scripts/validate_bounded_2026_population_census_v0.py \
  --data-repo-root . \
  --rookie-repo-root /path/to/read-only/TIBER-Rookies \
  --report \
    exports/candidates/population_census/bounded_2026_population_census_v0.validation.json
```

Two builds with the same source pins and `generated_at` must be byte-identical.
The committed candidate's expected SHA-256 is recorded in its validation
report and coverage report.

## Consumer boundary

This candidate may be inspected as a bounded source-population declaration.
Any downstream consumer must separately verify source pins, cutoff semantics,
identity policy, and its own admission contract.

This contract does not authorize TIBER-Forecast consumption, the parked 2026
candidate run, promotion, deployment, or a production binding. Those remain
separate operator-governed gates.
