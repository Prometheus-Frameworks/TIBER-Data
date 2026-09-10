# Offline one-game PBP validation and bounded read v0 (Research #22 first PR)

**Status:** implementation for operator review. This PR adds a local, read-only reader
and synthetic tests. It performs no acquisition, database write, schema change,
ingestion, admission, promotion, Research activation, or deployment. Real 2026 game
availability remains **unverified** until a separately authorized source read.

- Home question: [TIBER-Research #22](https://github.com/Prometheus-Frameworks/TIBER-Research/issues/22)
  (re-read at preparation: open, no comments, updated 2026-09-10T17:27:04Z).
- Owning repository for this PR: TIBER-Data. Fantasy's old nflfastR importers and
  `bronze_nflfastr_plays` table are discovery material only; canonical authority is not
  moved into Fantasy.
- Task class (AGENTS.md): provenance / source audit task plus a read-only builder with
  matching tests. No contract under `src/contracts/**`, no `schemas/**`, no
  `data/raw/**` or `exports/promoted/**` change, no support-claim change.

## Pinned revisions and initial working-tree state

| Repository | Pinned commit at start | Working tree at start |
| --- | --- | --- |
| TIBER-Data (owning) | `b0c79de5403864796a5701dc42bcda8eafd788ab` | clean |
| TIBER-Fantasy (reference only) | `080abb53825f6fb4b1a31aa42aec0880806a1d06` | clean |
| TIBER-Research (home question) | `0952e3325fb610f9cdb22c5242397d223c7a6c26` | clean |

## Files

| Path | Role |
| --- | --- |
| `src/pbp_one_game/offline_read.py` | Library: receipt verification, schema inspection, game location, inventory, possession selection, bounded events |
| `scripts/read_pbp_one_game_offline.py` | Thin CLI over the library; exit 0 result, 2 rejected, 3 usage |
| `tests/test_pbp_one_game_offline_read.py` | Synthetic-fixture tests (fictional `SYA`/`SYB`, season 1999) |
| `docs/data/pbp-one-game-offline-read-v0.md` | This document, including the storage/import compatibility plan |

## What the reader does

1. **Hash before parse.** The caller supplies an explicit local path, expected byte
   count, and expected SHA-256. The exact bytes are read and hashed. Missing file,
   byte-count mismatch, digest mismatch, or non-parquet magic bytes stop processing with
   a precise `rejected` result. Nothing is parsed, downloaded, guessed, or written.
2. **One format.** Parquet, read with `polars`, an existing declared dependency in
   `pyproject.toml`. No new dependency was added and no multi-format framework exists.
   `pyarrow` is the parquet backend polars already declares.
3. **Explicit game request.** Season, date (`YYYY-MM-DD`), away team, home team.
   Only game-identity columns are projected across the supplied file to locate the game;
   the requested `LA`→`LAR` canonicalization mirrors existing builders and raw source
   values are preserved verbatim. Zero matches, multiple matching game IDs, or one game
   ID with conflicting identity tuples (for example two `game_date` values) is
   `unresolved`. Swapped home/away on the requested date is reported as a diagnostic count
   only and is never selected. Date timezone is reported as not stated by the source
   unless the source dtype carries one.
4. **Schema inspected before projection.** Every inventoried column is reported as
   `absent` or `present`, and present columns are counted by `null`,
   `explicit_false_or_zero`, and `value` rows over the located game only. Columns outside
   the inventoried families are listed as `uninspected_columns`. Missing game-identity
   columns prevent certification; missing route/protection fields do not prevent the
   narrower event read.
5. **Keys and duplicates.** Row count and distinct `(game_id, play_id)` count are
   reported separately. Repeated keys are classified `identical_duplicate` or
   `conflicting_duplicate` (with differing column names) and all rows are retained.
   Neither count is an official snap denominator; no snap count is derived.
6. **Possession sequence.** Rows are ordered by `play_id`. A possession is a maximal run
   of identical non-null `posteam` and identical provider `drive` value (fallback
   `fixed_drive`, disclosed in `basis.drive_column_used`). A team's N-th possession is
   the N-th such run for that team in play order and is **never** equated with provider
   drive number N. Selection resolves only when the provider drive column exists, the
   run's drive value is non-null, that drive value occurs in exactly one run
   (contiguous), earlier runs do not carry a higher drive number, and no null `play_id`
   breaks ordering. Otherwise the selection is `unresolved` with a typed reason and no
   arbitrary event sample is emitted.
7. **Bounded events.** At most 40 event rows from the selected possession window plus up
   to two boundary rows before and after, each marked with its duplicate status, raw
   `play_type == "no_play"`, raw `penalty`, and raw `play_deleted`. Truncation is
   explicit (`truncated`, `omitted_row_count`). Personnel, `shotgun`/`no_huddle`,
   routes, coverage, and protection are inventoried separately with the limitation that a
   binary shotgun flag does not establish Under/Gun/Pistol.
8. **Receipt.** Provider/dataset reference, retrieval time, and publication time are
   carried only when the operator supplies them and are labeled `operator_supplied`;
   otherwise they are `null` with basis `unknown` / `not_evidenced`. `processing_time` is
   the only value that varies between runs of the same input and reader revision, and it
   is never substituted for retrieval, ingestion, publication, or admission time.
   `lineage.status` is `unknown`, `admission.status` is `not_admitted`,
   `governance_status` is `ungoverned`, `canonical` is `false`. Reader revision is
   recorded as `READER_VERSION` plus the SHA-256 of the reader module bytes.

The module imports no network, database, or application code; a test asserts that.

## Target request (not executed here)

The scope's target request is NE at SEA, 2026-09-09, season 2026, Seattle possession 2.
Invoking it requires an explicitly authorized local input file with its exact byte
count and digest. The upstream release metadata observed during preparation
(`play_by_play_2026.parquet`, 222639 bytes, digest
`149b3a9077cb7891b3a4fcd2c9b926a495e72f66ca2b77dc4418f3f530f0fe50`) is an external
observation, not a TIBER receipt; no bytes were downloaded and game membership is
unknown. A synthetic test confirms that this exact request against a fixture that does
not contain the game returns `unresolved` rather than a substitute.

```bash
python scripts/read_pbp_one_game_offline.py \
  --path <authorized local file> --expected-bytes <n> --expected-sha256 <hex> \
  --season 2026 --date 2026-09-09 --away NE --home SEA \
  --possession-team SEA --possession-ordinal 2 \
  --source-ref nflverse-data:pbp/play_by_play_2026 --retrieved-at <if known>
```

## Tests

`python -m pytest tests/test_pbp_one_game_offline_read.py` covers the scope's required
matrix: wrong digest / missing input rejected before parsing with no side effect;
wrong home/away/date/season and the real target request against a synthetic file are
unresolved with no fallback; ambiguous date inside one game is conflicting metadata;
identical versus conflicting duplicate keys; a team's second possession resolved to
provider drive 4 (not 2), consecutive same-team drives kept separate, and unresolved
cases for null drive, non-contiguous drive, absent drive column, and ordinal beyond
observed possessions; absent/null/false-zero/value states and binary shotgun; nullified
penalty event plus repeated key with no snap counting; 45-row possession truncated to
40 with two boundaries per side; receipt never invents publication, ingestion, or
admission; operator-supplied times carried as supplied; output reproducible apart from
`processing_time`; CLI exit codes and no output file on rejection. Synthetic tests prove
software behavior only.

## Storage/import compatibility plan (requested in scope; not implemented)

### 1. Which existing Data artifact/receipt owns source identity and revisions?

The closest existing Data conventions are the candidate **lineage manifests** under
`data/manifests/*.manifest.json` (per-source `sourceUrlOrDatasetId`, `retrievalMethod`,
`retrievalTimestamp`, `packageVersion`, `checksum.sha256`, `immutableSourceRef: null`,
`mutabilityNote`) produced by `scripts/build_team_week_raw_v0_2024_candidate.py` and
`scripts/build_formation_summary_v0_2024_candidate.py`, and the operator-accepted
**admission receipt** pattern in `exports/promoted/draft_review/evidence_admission_v1.json`
(proposal commit/path/sha256, operator acceptance link, review link, scope). Neither is
a durable per-game or per-row source-revision register: manifests describe one build of
one aggregate artifact and are not keyed by game or play. **Exact contract decision
required before any durable envelope is designed:** whether a per-input "source receipt"
record (digest, byte count, provider/dataset ref, retrieval time, publication time when
evidenced, reader revision) becomes a new small Data artifact family, or whether the
existing manifest shape is generalized with a game-scoped `sources[]` entry. This reader's
`receipt` block is intentionally shaped so either choice can adopt it without loss.

### 2. Can the existing bronze table retain the inspected source without loss?

Reference only, from Fantasy `shared/schema.ts` at the pinned commit:
`bronze_nflfastr_plays` has a unique index on `(game_id, play_id)`, a `raw_data` jsonb
column, a small set of normalized columns (several typed `boolean` where the source is
`0/1` float, and `integer` where the source has nullable floats), and `imported_at` /
`created_at` defaults. `raw_data` can hold the full source row without information loss
if the importer writes every column verbatim, which the pinned bulk importers do not
guarantee (they select columns). The normalized `boolean` columns with `.default(false)`
collapse the source's null / explicit-zero distinction that this reader preserves; they
are lossy and must not be the record of truth. **There is no column that associates a
row with the input digest or source revision.** `imported_at` is processing time and
must not stand in for retrieval or publication time. A loose report beside the database
is not durable linkage: the minimum durable association is a source-receipt row keyed
by digest, with each play row carrying that receipt key (or the digest itself) in a
dedicated column or a dedicated `raw_data` sub-object that the importer is required to
write. That is a schema change and is not preapproved here.

### 3. What database-enforced read-only path would verify deployed schema and rows?

Runtime metadata (Railway service info, an app health endpoint, or the ORM schema file)
is insufficient. The verification must run **SQL against the deployed database under a
role that is read-only at the database level** (a login role with `SELECT` only, no
DDL, no write on `bronze_nflfastr_plays` or any receipt table) and return: the actual
`information_schema.columns` for the table and its unique index; the row count and the
distinct `(game_id, play_id)` count for the one requested game ID; and whether any
digest/receipt linkage column exists and is populated for those rows. Owning executor:
an operator-run or operator-authorized session with that read-only credential, executed
outside the app runtime; no credential is requested, stored, or exposed by this PR. Joe's
empty-result screenshot from preparation is not a verified count and should be
superseded by that query.

### 4. How would a future explicitly selected game import be transactional and idempotent?

Not by reusing the season-wide delete/reload path in the pinned importers. A one-game
import would: (a) run this reader first and refuse to proceed unless the receipt is
`verified` and the game is `matched`; (b) open one transaction; (c) insert or confirm a
source-receipt record keyed by the input digest; (d) insert only the located game's rows
with the receipt key, using `ON CONFLICT (game_id, play_id)` semantics that **compare the
incoming row content to the stored row**: identical content is a no-op, differing content
under a different input digest is a recorded revision/conflict decision (new receipt,
stored diff, explicit operator disposition), and differing content under the same digest
is an integrity error that aborts the transaction; (e) commit only if every row resolved.
Same bytes therefore never create duplicates or a second receipt, and changed upstream
content never silently replaces rows. Conflicting duplicates inside the source file (this
reader's `conflicting_duplicate_keys`) block the import rather than being resolved by
"last write wins".

### 5. What must happen before promoting any records to consumer use?

Import existence and admission are different states. Before any consumer (Team, FORGE,
Forecast, a ledger, the Research #22 comparison) reads these rows: an operator-accepted
admission receipt in the `evidence_admission_v1` pattern naming the game, the input
digest, the reader/importer revisions, and the consumer scope; the read-only database
verification from item 3 recorded against that digest; an independent audit per
AGENTS.md triggers (source/provenance semantics, generated artifacts); and an explicit
row-level provenance label distinguishing these rows from `governed_real_data`. Nothing
routes automatically; `admission.status` in this reader's output stays `not_admitted`.

### Smallest schema proposal if storage cannot meet these requirements

If item 2's linkage is required, the smallest separately reviewable change is one
receipt table (`digest` primary key, `byte_count`, `provider_dataset_ref`,
`retrieved_at` nullable, `published_at` nullable, `reader_revision`, `recorded_at`) and
one nullable `source_digest` column on the play table referencing it, backfilled as
`null` for legacy rows so that unknown lineage stays explicit. Source receipts must not be
squeezed into football fields. This is a proposal for operator review, not a change made
here.

## Exclusions and blockers

This PR does not create a film-observation ledger, populate the signal ledger, produce
Forecast fields, reconcile the personal chart, grade players, compute route/block
percentages, enable season ingestion or scheduling, acquire provider data, connect to a
live database, or deploy. The personal chart and photographs are not committed.

Remaining blockers before the target request can be run: operator authorization of one
pinned input acquisition or a provenance-bearing TIBER export, with its exact byte count
and digest supplied to this reader; the item-3 read-only database verification; and the
item-1 receipt contract decision before any durable import.
