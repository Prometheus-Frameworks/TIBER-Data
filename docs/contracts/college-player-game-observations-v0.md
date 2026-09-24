# College player/game observations v0.1.0 — corrected local candidate

Contract and synthetic fixtures for TIBER-Data #265 / TIBER-Rookies #298. This is
an unpromoted football-fact contract. It does not acquire data, admit a source,
resolve the full college identity universe, compare Devy checkpoints, score,
forecast, rank, or mutate a seed watchlist. This pre-merge local repair retains
the version name; no published v0.1.0 consumer exists.

## Contract surfaces

- `schemas/college_player_game_observations_v0.schema.json`: JSON Schema
  2020-12, the closed shape/type vocabulary. Schema validation is necessary,
  but semantic admission additionally requires the Python contract gate.
- `src/contracts/college_player_game_observations_v0.py`: offline semantic
  validator, deterministic sorted findings, read-only CLI and a minimal
  fail-closed corrected-leaf selector. No provider I/O, identity allocator,
  checkpoint engine or data writer.
- `tests/fixtures/college_observations/player_games.synthetic.json`:
  unmistakably synthetic players, source provider, observations and references.
- `tests/test_college_player_game_observations_v0.py` and matching `_repair.py`:
  original focused assertions and repairs, including negative cases.

```sh
python -m src.contracts.college_player_game_observations_v0 \
  tests/fixtures/college_observations/player_games.synthetic.json
python -m pytest -q tests/test_college_player_game_observations_v0.py \
  tests/test_college_player_game_observations_v0_repair.py
```

CLI returns exit 0 for contract-valid, 1 for invalid/failed JSON read and 2 for
bad invocation. The CLI rejects duplicate JSON keys. `validate` never mutates
inputs. Contract-valid does **not** mean source admitted, truthful, licensed,
retained, complete beyond the declared source population or eligible downstream.

## Three histories

| History | Contract coordinates | Does not imply |
|---|---|---|
| Football event | `game.season`, `source_game_id`, nullable source date, event team/opponent/position/status | Retrieval date is kickoff time; NFL week; freshman or participation inference |
| Source assertion | Provider-scoped player/game ID, source revision identity/origin, observed stats, declared snapshot, source time if supplied, `source_relationship` | An opaque token, later retrieval or digest proves correction order |
| TIBER knowledge/attribution | Row `retrieved_at`, evidence `known_at`, append-only `attributions.recorded_at`, artifact `generated_at`, repeat `retrieval_receipts` | A later identity resolution rewrites original football/source facts |

`artifact_type=college_player_game_observations`,
`schema_version=college-player-game-observations-v0.1.0`,
`artifact_position=unpromoted`. One envelope has one provider namespace, a
bounded declared competition and source population, and may contain multiple
seasons. `evidence_mode=synthetic_fixture|source_observation` describes provenance,
not source admission. A synthetic locator cannot be relabeled source evidence.

One immutable source observation is keyed by
`provider × source_player_id × season × source_game_id × source_revision_id`.
`observation_id` uniquely names the retained row, distinct from the provider
player ID and nullable resolved canonical TIBER college-player ID. Names and
school do not resolve identity; provider IDs are provider-scoped. Even when a
later TIBER crosswalk changes, the source row and its event-time source program,
opponent, position and record type stay unchanged. Transfers preserve old teams
and seasons. Source correction of event attribution is a new source revision;
TIBER-side attribution change uses an `attributions` record with independent
time/evidence. No general identity allocator or cross-provider merger exists.

## Source revisions and evidence

Each row's `source_relationship` has a closed status:

| Status | Relationship | Selection |
|---|---|---|
| `initial` | No prior source assertion linked; one initial root per source player/game | Candidate if no conflicting relation |
| `established_supersession` | `supersedes` and `related_observation_id` name the same retained ancestor; reason, basis and evidence required | Later current leaf only when source assertion evidence establishes relationship |
| `unresolved` | A retained related assertion exists without evidenced order; no supersession | Corrected leaf unavailable |
| `older_discovered_later` | A retained related assertion was found later but source order is unresolved; no supersession | Corrected leaf unavailable |

Established bases are `provider_explicit_correction` and
`documented_provider_order`. The new source snapshot must include a structured
`source_order_claim` naming exact older/newer revision IDs and matching assertion.
The claim must be backed by retained source evidence in future provider use; a
self-authored payload cannot prove source authenticity. A source update timestamp
that clearly predates its predecessor blocks an established relationship. Missing
source timestamps do not force a fictional value; an independently documented
provider assertion may establish order without them. Retrieval order is checked
only for **TIBER knowledge** chronology and never establishes source order.

`revision_origin=source_supplied` names a provider token; tokens are opaque unless
source evidence establishes their order. `retained_snapshot_digest` requires
`sha256:<64 lowercase hex>`; it identifies response bytes, not a chronological
provider revision. The validator checks digest syntax and exact declared evidence
identity; actual hash-to-retained-byte verification remains an operational gate.
An identical later fetch belongs in `retrieval_receipts`, referencing the same
immutable observation/snapshot with a later receipt time. It does not append a
second fact or refresh the row's first-known time. Repeated duplicate or
conflicting rows at the same grain are rejected.

Ancestors are retained in the same envelope; forks, missing ancestors, cycles,
parallel unlinked roots, wrong-player/game source links and conflicting duplicate
revisions fail validation. The minimal `corrected_leaf_ids` helper returns source
leaf IDs on a valid fully ordered envelope, or raises if any competing relation
is unresolved. This is a fail-closed demonstration, not a checkpoint engine or
aggregation; downstream must never sum superseded revisions.

## Evidence binding and as-known cutoffs

Evidence entries have identity (`locator`), kind, provider, `known_at`, structured
scope (nullable season/game/player/revision/record type), a description and nullable
source-order/alias assertions. Null scope components mean source-wide support,
not invented player-level knowledge. All refs must exist, have the expected kind,
match provider and non-null scope components, and be known by the state they
support. A row's source snapshot must bind exactly to its revision and source
record type. Source-observed metric values must cite exactly that snapshot;
metric-level missingness citations must also be in scope and known by retrieval.
The source clock and status refs are snapshot-bound. Mapping and identity evidence
can be independently earlier and source-revision-neutral where honest.

An earlier row cannot cite a later correction snapshot. The global scope evidence
and attribution event evidence have own `known_at`; a consumer selecting an as-known
cutoff must include only material known by that cutoff, rather than projecting a
later coverage claim backwards. This contract validates the clock relations but
does not implement the cutoff query. A later recorded attribution state supersedes
the earlier attribution state for the **same immutable source observation**, while
the earlier state remains inspectable. Attribution evidence first-known time must
not exceed its `recorded_at` or artifact generation. TIBER's baseline canonical
identity state lives in the source row as an immutable first-known annotation;
subsequent identity changes are separate records, never source revisions.
Every baseline and retained attribution state is validated independently at its
own first-known/recorded cutoff, including identity status, canonical ID,
aggregation status, representative binding and evidence. Attribution lineage is
strictly sequential in recorded time. An invalid intermediate state is reported
at its own path and remains invalid even if a later state is well formed; a
consumer must quarantine that historical cutoff rather than skip ahead.

As-known example: source row first retrieved September 6 can be unresolved;
new identity evidence first known September 8 supports an attribution record on
September 8 resolving the canonical player ID, without changing source bytes or
the September 6 answer. The corrected synthetic QB observation retains 240 and
245 passing-yard assertions with distinct source snapshots and source-supported
revision relationship. Its football event date stays September 5.

## Alias/canonical aggregation boundary

`identity.status=resolved` requires a non-null canonical ID;
`unresolved|ambiguous` require null and `aggregation_status=blocked_unresolved_identity`.
For a resolved player, canonical aggregation status is `eligible`,
`blocked_alias_conflict`, or `excluded_reconciled_alias`. A latter row names an
`alias_of_observation_id` in the same game and carries scoped identity evidence
with a structured alias claim naming **both exact observation IDs**, both
source player IDs, season/game and canonical player ID. The claim binds one
review decision to a specific source revision pair, not a provider identity in
perpetuity. Two provider IDs resolved to the same canonical player/game
cannot both be eligible: all must be blocked during unresolved reconciliation,
or exactly one representative remains eligible and the others are explicitly
excluded with reviewed evidence. All source rows remain inspectable.
Each excluded alias must point **directly** to the one eligible source-observation
revision in its provider/season/game/canonical group at its effective cutoff.
An alias cannot point to itself, another alias, a blocked representative, a
different provider/game/canonical identity or a source revision not yet known.
Alias chains and cycles have no meaning in this version. The exact alias claim
is necessary but cannot make an ineligible representative eligible. A group
with multiple provider identities may instead remain wholly and explicitly
`blocked_alias_conflict` while reconciliation is unresolved; it cannot mix a
claimed alias with blocked members and call the group reviewed.

The validator checks alias safety at **each retrieval/attribution knowledge
cutoff** and counts multiple revisions under the same provider player ID as one
source identity. A later alias review cannot retroactively sanitize an earlier
period where two aliases were independently eligible. Same names with separate
IDs are not merged; one player across different games or transfers is valid.
Each retained initial and later attribution alias state is checked at its own
knowledge cutoff, and each effective multi-identity group is checked at every
retrieval/attribution cutoff. Later valid links cannot erase an earlier invalid
representative graph.
An old alias decision remains valid at its original as-known cutoff even if its
representative later receives a correction. When either source member is
corrected, the old decision ceases to grant eligibility to the current source
leaf pair. The effective eligibility of an otherwise eligible representative is
blocked if its reviewed alias was corrected, until a later representative review;
the corrected alias must also receive its own new reviewed binding to the
current representative. These effective states do not alter retained historical
states. A later determination that the provider IDs refer to distinct canonical
players is recorded as a separate attribution, without changing older claims.
This is a candidate eligibility boundary, not a canonical aggregation producer.
Alias identity evidence correctness still requires governed review.

## Ordinary facts and missingness

All fields exist; position does not determine availability. Passing: attempts,
completions, yards, touchdowns, interceptions. Rushing: carries, yards, touchdowns.
Receiving: targets, receptions, yards, touchdowns. Counts are nonnegative integers;
net yards may be negative. Observed completions cannot exceed observed attempts.
A QB may catch a pass; an RB/WR/TE may throw one. Provider-specific sack, kneel,
target and team/uncredited-stat conventions need mapping qualification. Only
source-credited game values belong in `observed`; season totals, estimated
receptions/0.70 targets, longest-reception targets, arithmetic shares, fantasy
points and Devy grades do not. A mislabeled integer cannot be detected by a shape
gate; future retained mapping/source review must establish field semantics.

Every cell has `value`, `availability`, `evidence_refs`, `note`, and nullable
`applicability_basis`. The eight availability states are:

| State | Value | Meaning |
|---|---|---|
| `observed_zero` | exactly 0 | Source explicitly credited zero |
| `observed_value` | nonzero integer | Source explicitly credited exact value |
| `unavailable_from_source` | null | Source does not supply field |
| `not_applicable` | null | Structured source-record-type rule demonstrates field does not apply |
| `unresolved_identity` | null | Attribution of a field is unresolved |
| `incomplete_coverage` | null | Missing source segment/field support |
| `source_conflict` | null | Contradictory assertions need reconciliation |
| `excluded_by_contract` | null | Source material cannot meet contract semantics |

`not_applicable` alone requires `applicability_basis`: a bounded
`field_not_defined_for_source_record_type` rule, source record type equal to the
row and declared snapshot, and evidence refs to the same snapshot **and** the
admitted mapping ref. The mapping evidence contains the exact record type and
field path rule. Generic position does not qualify. If that source-record
classification is unavailable or unsupported, represent missingness honestly
instead. The schema rejects an applicability basis on any other status. The
validator checks these structured claims; actual source/mapping authenticity
remains a later qualification obligation.

An absent source row is never an observed zero, inactivity, participation, game
played, freshman or eligibility statement. `row_presence=source_row_observed` is
a source-backed assertion a future adapter must prove. No missing player row is
fabricated by validation.

## Coverage, finality and clocks

`coverage.provider`, `competition_scope`, `declared_population` and scope evidence
bound `population_status=complete|partial|unknown` to an explicit source subset.
No complete-NCAA claim follows. `game_scope.expected_game_ids` is null for unknown
expectations and `[]` for independently established zero games (requiring scoped
evidence). Expected and observed entries are **season × source_game_id**; the
same provider game ID can recur in different seasons without collapsing two games.
Every row belongs to the declared observed game set; complete population cannot
omit a known expected game. `observed_game_ids` measures source coverage, never
player participation. Population completeness remains an independently audited
source assertion; a validator cannot prove a prose-defined player universe.

Per-row category completeness can be complete, partial, unknown, unavailable or
not_applicable independently of game finality. Complete categories require every
core field to be observed. Missing targets cannot become complete receiving
coverage merely because receptions exist. Game status is source-backed scheduled,
in_progress, final, suspended, cancelled or unknown; a partial game may contain
observed interim values without claiming finality.

`game.date` is nullable source-supplied **date only** with explicit origin, not a
kickoff timezone; no NFL-week field is imported. Source timestamp is nullable and
has source origin or explicitly unavailable origin. `retrieved_at` is when TIBER
first knew the retained assertion, and `generated_at` is artifact-generation
time. Non-null source time <= retrieval <= generation; coincident clocks are fine.
All datetimes require timezone offsets. Source timestamps cannot be replaced by
retrieval timestamps. Legitimate delayed retrieval, including historical games,
is fine. A final game with supplied event date must have date no later than the
**UTC calendar date of first retrieval plus one full day**. The one-day margin
conservatively accommodates date-only/timezone uncertainty while rejecting a
2035 final result first retrieved in 2026. Scheduled future games are exempt.
Postseason can cross calendar years; no naive season-year equality is enforced.

## Extensions and gates

Unknown fields are rejected; additions require a new version/consumer opt-in after
this unpromoted candidate is finalized. Future companion contracts can add team
shares, scoring-area and explosive events, air yards, or richer plays without
changing raw game-stat meanings. Any derivation needs numerator, denominator,
formula/rule version, source-game refs and status. The present contract has no
opportunity score or derivations.

Future Rookies checkpoint comparison must retain evidence cutoffs, correction
lineage, uncertainty and the curated seed-watchlist review boundary. Event-time
school, exact identity history, competing source assertions, lifecycle evidence
and development horizon remain distinct when later governed rookie transitions
occur. No Devy interpretation, Rookie Alpha update or experimental ML connection
exists here.

Before first provider qualification, separately establish: lawful access,
automation, retention and redistribution/attribution rights; source endpoint and
season/competition/postseason scope; schedule/player population evidence;
field mappings and zero/null/target/sack/kneel semantics; provider player/team/game
ID stability, transfer and alias behavior; correction chronology, finality,
source timestamps and snapshot authenticity; immutable retention and replay
cutoff policy; and a bounded authorized test sample. No terms/entitlement decision
or real data access occurred in this slice. TIBER-Data `AGENTS.md` requires an
auditor review before merge for contract/identity changes.
