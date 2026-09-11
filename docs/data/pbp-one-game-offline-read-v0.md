# Offline one-game PBP validation and bounded read v0 (Research #22 first PR)

**Status:** implementation for operator review, revised after the 2026-09-10 independent
branch review (findings F1–F5 plus documentation and error-handling corrections). This PR
adds a local, read-only reader and synthetic tests. It performs no acquisition, database
write, schema change, ingestion, admission, promotion, Research activation, or
deployment. Real 2026 game availability remains **unverified** until a separately
authorized source read.

- Home question: [TIBER-Research #22](https://github.com/Prometheus-Frameworks/TIBER-Research/issues/22)
  (re-read at preparation: open, no comments, updated 2026-09-10T17:27:04Z).
- Owning repository for this PR: TIBER-Data. Fantasy's old nflfastR importers and
  `bronze_nflfastr_plays` table are discovery material only; canonical authority is not
  moved into Fantasy.
- Task class (AGENTS.md): provenance / source audit task plus a read-only builder with
  matching tests. No contract under `src/contracts/**`, no `schemas/**`, no
  `data/raw/**` or `exports/promoted/**` change, no support-claim change.
- **Audit status: pending.** The reader introduces a team alias map (`LA`→`LAR`,
  mirroring existing builders), game-identity matching, and provenance/status wording.
  Under the pinned AGENTS.md those are identity and source/provenance semantics, which
  trigger the auditor function regardless of file path. Independent review is required
  before merge; the first review round is recorded in the commit history of this branch.

## Pinned revisions and initial working-tree state

| Repository | Pinned commit at start | Working tree at start |
| --- | --- | --- |
| TIBER-Data (owning) | `b0c79de5403864796a5701dc42bcda8eafd788ab` | clean |
| TIBER-Fantasy (reference only) | `080abb53825f6fb4b1a31aa42aec0880806a1d06` | clean |
| TIBER-Research (home question) | `0952e3325fb610f9cdb22c5242397d223c7a6c26` | clean |

Review round 1 reviewed head `2da2f604872143bde6eb89fe68c20e4d13edf7cd` against that base.

## Files

| Path | Role |
| --- | --- |
| `src/pbp_one_game/offline_read.py` | Library: receipt verification, schema inspection, lazy game location, inventory, possession selection, bounded events |
| `scripts/read_pbp_one_game_offline.py` | Thin CLI over the library; exit 0 result, 2 rejected, 3 usage, 4 output collision, 5 reader processing failure |
| `tests/test_pbp_one_game_offline_read.py` | Synthetic-fixture tests (fictional `SYA`/`SYB`, season 1999) |
| `docs/data/pbp-one-game-offline-read-v0.md` | This document, including the storage/import compatibility plan |

## What the reader does

1. **Hash before parse.** The caller supplies an explicit local path, expected byte
   count, and expected SHA-256. The exact bytes are read and hashed. Missing file,
   byte-count mismatch, digest mismatch, or non-parquet magic bytes stop processing with
   a precise `rejected` result whose `parsed` field is `not_attempted`. A file that
   passes the magic-byte check but fails inside a parquet engine stage (schema read,
   identity scan, descriptor read, game-row collect) produces a bounded `parse_failure`
   rejection with `parsed: attempted_failed`, the failing `read_stage`, the exception
   class and message, and the verified receipt. Only those four engine stages can
   produce `parse_failure`. A defect in the reader's own post-parse processing
   (matching, inventory, sequencing, selection, assembly) is returned as a distinct
   `processing_failed` result with `failure.kind: reader_processing_failure`, its
   processing `stage`, and `parsed: succeeded`; it is never attributed to the source
   file. Neither path raises out of the reader, and nothing is downloaded, guessed, or
   written in any case.
2. **One format.** Parquet, read with `polars`, an existing declared dependency in
   `pyproject.toml`. No new dependency was added and no multi-format framework exists.
   `pyarrow` is the parquet backend polars already declares.
3. **Explicit game request.** Season, date (`YYYY-MM-DD`, a real zero-padded calendar
   date; `1999-99-99` or `2026-02-30` is a usage error before any file access), away
   team, home team. The expected byte count must be a non-negative integer and the
   expected digest exactly 64 hexadecimal characters matched against the full string, so
   a trailing newline is rejected; a malformed expectation is a usage error (exit 3),
   never a source rejection. The away and home codes must differ after
   canonicalization, so an alias pair such as
   `LA` / `LAR` cannot describe an impossible same-team game; that is rejected before
   any file access.
   **Invariant identity** is exactly `game_id`, `season`, `game_date`, `home_team`,
   `away_team`; only these decide whether a game's metadata is consistent, and only these
   are projected across the file to locate the game. **Game-level descriptors** (`week`,
   `season_type`, `old_game_id`, `nfl_api_id`, `start_time`, `stadium`, `location`) are
   read for the matched game only and reported with their distinct values and a
   `varies_within_game` flag; variation is disclosed, never fatal. Event-level timestamps
   such as `time_of_day` are ordinary event fields (quarter/clock family). The requested
   `LA`→`LAR` canonicalization mirrors existing builders and raw source values are
   preserved verbatim. Zero matches, multiple matching game IDs, one game ID with more
   than one invariant identity tuple, or any matching tuple whose provider `game_id` is
   null or empty (`matching_identity_without_game_id`, counted in diagnostics) is
   `unresolved`; a missing game ID is never certified as a match. Season equality is
   exact with no lossy coercion: an int on equality, a float only when integral and
   equal, a string only when it is exactly the requested season's digits; fractional,
   boolean, padded, or otherwise invalid season values never match. Swapped home/away on the requested
   date is reported as a diagnostic count only and is never selected. Date timezone is
   reported as not stated by the source unless the source dtype carries one.
4. **Lazy, bounded reads.** Both reads are `polars.scan_parquet` over the verified
   in-memory bytes. The identity scan projects identity columns only. The game read
   pushes `game_id == <matched>` into the parquet scan node (the query plan shows the
   selection inside the scan, not as a separate filter) so only the located game's rows
   are materialized, with all columns because full-row content is needed to classify
   duplicate keys. The output discloses this as `inventory.read_strategy`: logical scope
   is one game; physical I/O may still decode row groups that parquet statistics cannot
   exclude. The receipt no longer claims other games were "not read", only that no other
   game's rows were materialized or analyzed.
5. **Schema inspected before projection.** Every inventoried column is reported as
   `absent` or `present`, and present columns are counted by `null`,
   `explicit_false_or_zero`, and `value` rows over the located game only. Columns outside
   the inventoried families are listed as `uninspected_columns`. Missing game-identity
   columns prevent certification; missing route/protection fields do not prevent the
   narrower event read.
6. **Keys and duplicates.** Row count and distinct `(game_id, play_id)` count are
   reported separately. Repeated keys are classified `identical_duplicate` or
   `conflicting_duplicate` (with differing column names and an
   `affects_possession_order` flag when `posteam`, `drive`, or `fixed_drive` disagree),
   and all rows are retained. Neither count is an official snap denominator; no snap
   count is derived.
7. **Possession sequence.** Rows are ordered by `play_id` through one lossless numeric
   representation shared by every ordering stage (sorting, run extension, the
   order-affecting conflict check): integers stay integers, finite floats become exact
   fractions of their binary value, and numeric strings are parsed exactly from their
   decimal spelling under a strict grammar (sign, digits, optional fraction, optional
   exponent; no whitespace, underscores, hex, or inf/nan spellings), so
   `9007199254740993.0` and `9007199254740993e0` are the exact integer, never a rounded
   float. Python compares int and Fraction exactly, so mixed keys sort correctly. Run
   extension, duplicate grouping, and occurrence counting all use the same recursive
   NaN-aware equality and its consistent freeze, so one equivalence relation governs
   every stage; a cross-stage test feeds one shared case set through all of them. A possession is a maximal run
   of identical non-null `posteam` and identical provider `drive` value (fallback
   `fixed_drive`, disclosed in `basis.drive_column_used`). A team's N-th possession is
   the N-th such run for that team in play order and is **never** equated with provider
   drive number N. Because N is a count over every earlier run, selection resolves only
   when the **entire prefix** up to the selected run is evidenced: no conflicting
   duplicate affecting team or drive at or before the selected run's last play; every
   prefix run has a non-null, contiguous (occurs once), non-decreasing provider drive;
   no unattributed (null `posteam`) row before the end of the selection carries a drive
   value that no prefix run accounts for; no null, NaN, non-finite, or non-numeric
   `play_id` breaks ordering (±infinity serializes but is no evidence of a position in
   the game order; an unparseable ID has an unknown position; a parseable numeric string
   orders normally);
   and no prefix run carries a non-finite provider drive (a NaN drive is treated as a
   missing drive number, an infinite one as unresolvable ordering; the raw NaN is kept
   distinct from null through run extension, occurrence counting, and output, so a NaN
   drive and a null drive on consecutive same-team rows are two runs). Neutral
   administrative rows (null `posteam` with a null drive, or a drive already in the
   prefix) do not create possessions and do not block selection. Every unresolved case
   returns a typed reason and the affected runs or play IDs, keeps all runs in the
   output, and emits no arbitrary event sample.
8. **Bounded events.** At most 40 event rows from the selected possession window plus up
   to two boundary rows before and after, each marked with its duplicate status, raw
   `penalty`, raw `play_deleted`, and a derived no-play status with four values:
   `no_play`, `other_play_type`, `unknown_null_play_type`, `unknown_absent_column`. A
   null or absent discriminator is never turned into a negative assertion. Truncation is
   explicit (`truncated`, `omitted_row_count`). Personnel, `shotgun`/`no_huddle`,
   routes, coverage, and protection are inventoried separately with the limitation that a
   binary shotgun flag does not establish Under/Gun/Pistol.
9. **Receipt.** Provider/dataset reference, retrieval time, and publication time are
   carried only when the operator supplies them and are labeled `operator_supplied`;
   otherwise they are `null` with basis `unknown` / `not_evidenced`. `processing_time` is
   the only value that varies between runs of the same input and reader revision, and it
   is never substituted for retrieval, ingestion, publication, or admission time.
   `lineage.status` is `unknown`, `admission.status` is `not_admitted`,
   `governance_status` is `ungoverned`, `canonical` is `false`. Reader revision is
   recorded as `READER_VERSION` plus the SHA-256 of the reader module bytes. Internally,
   rows keep raw source scalars, NaN included, through duplicate classification and
   possession sequencing; duplicate comparison is NaN-aware (two NaNs are equivalent,
   NaN never equals null or a number), so a NaN-versus-null disagreement is a conflict.
   NaN-aware equality applies recursively inside list and struct values. Duplicate
   grouping canonicalizes only the key, with a freeze that is consistent with that
   equality: every NaN shares one sentinel at any depth (distinct from the null-`play_id`
   group, both counted as missing keys), lists become typed tuples of frozen elements so
   value-equal lists such as `[0.0]` and `[-0.0]` share a key while a list and a tuple do
   not, structs become sorted tuples of frozen items, and any residual unhashable value
   is keyed by type and repr. The rows' raw values are untouched, so grouped rows are
   compared by content and reported with their raw play ID. A non-scalar play ID
   therefore reaches the documented unresolved-possession path rather than a processing
   failure. The same freeze keys provider-drive occurrence counting and the prefix drive
   set, so a non-scalar drive still bounds runs and is reported as
   `provider_drive_not_orderable` instead of crashing sequencing.
   Field inventories count `nan_rows` separately from `null_rows`. JSON shaping happens
   once at the output boundary. There, every scalar polars can return is normalized: bytes become an explicit
   `{bytes_hex, byte_length}` envelope, time and timedelta and Decimal values become
   labeled envelopes, NaN becomes an explicit `{float_nan: true}` envelope distinct from
   null, positive and negative infinity become signed `{float_infinity}` envelopes
   distinct from finite, NaN, and null, and an unknown type is reported by name. If
   serialization still fails, the CLI returns a bounded `reader_processing_failure` at
   stage `serialize_result` (exit 5) instead of a traceback.
10. **Source preservation.** The CLI never overwrites. `--out` is refused with exit 4 if
    any path already exists there (a regular file, the input itself, a symlink or
    hardlink alias of it, or a dangling symlink), checked before anything is read; the
    write itself uses exclusive creation (`O_CREAT|O_EXCL`), so a path that appears in
    between fails without truncating anything. Rejections and processing failures never
    write an output file. Malformed invocations (missing required flags, a non-integer
    value, an unknown flag, a possession ordinal below 1) exit 3, so exit 2 means only
    a rejected source input. The possession ordinal is 1-based; a zero or negative
    ordinal is a malformed invocation, never absent source evidence.

The module imports no network, database, or application code; a test asserts that.

## Target request (not executed here)

The scope's target request is NE at SEA, 2026-09-09, season 2026, Seattle possession 2.
Invoking it requires an explicitly supplied local input file with its exact byte count
and digest. The upstream release metadata observed during preparation
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
  --source-ref nflverse-data:pbp/play_by_play_2026 --retrieved-at <if known> \
  --out <new path that does not exist>
```

## Tests

`python -m pytest tests/test_pbp_one_game_offline_read.py` covers the scope's required
matrix and the review regressions: wrong digest / missing input rejected before parsing
with no side effect; a PAR1-wrapped corrupt file rejected as a bounded `parse_failure`
at the schema stage, an engine failure after the schema read reported with its own
stage, and a monkeypatched exception in each pure processing function (and in matching
logic) reported as `reader_processing_failure` with its stage and never as
`parse_failure`, with the CLI exiting 5 and writing nothing; the engine and processing
stage vocabularies are disjoint and enforced; a matching identity tuple with a null,
empty, or blank `game_id`, alone or alongside a real match, is unresolved and never
certified; argparse usage errors and a non-positive possession ordinal exit 3 while
`--help` exits 0; season values of 1999, 1999.0, and "1999" match while 1999.5,
1998.999, "1999.0", " 1999", true, and null do not; bytes in an emitted field serialize
as a hex envelope and a forced serialization failure is a bounded exit-5 processing
failure at stage `serialize_result`; a request whose away and home codes canonicalize to
one team (`LA`/`LAR`) is rejected before reading while a real alias match still
resolves; positive and negative infinity serialize as signed envelopes and stay distinct
from finite, NaN, and null; an infinite `play_id` or `drive` is classified and sequenced
on its raw value and enveloped only in the output, while an infinite `play_id` or an
infinite provider drive in the counting prefix leaves selection unresolved with no event
sample and a NaN drive is treated as missing; identical rows containing NaN are
identical duplicates while a NaN-versus-null disagreement is a conflict, NaN is counted
and emitted distinct from null, and a NaN `play_id` is a null key; two NaN play IDs group
together and compare identical or conflicting by content, NaN and null play IDs are
distinct missing keys, a non-numeric play ID withholds selection while parseable numeric
strings still order and resolve, and list- or struct-typed play IDs group hashably,
classify duplicates by content, and withhold selection instead of failing grouping;
value-equal lists and structs (`[0.0]` versus `[-0.0]`) share one key and are identical
duplicates, nested NaNs compare equal recursively while nested NaN versus null does not,
list- or struct-typed drives still bound runs and count occurrences and are reported as
not orderable, and Int64 play IDs above 2**53 (as integers, integer strings, or
decimal- and exponent-spelled integral strings) keep exact ascending order including in
the order-affecting conflict check; equivalent nested-NaN drives extend one run; and a
cross-stage test asserts that freeze equality, recursive value equality, order-class
membership, sort order, run extension, grouping, and occurrence counts agree over one
shared case set, for scalar drive pairs as well as nested ones; a scalar NaN drive
followed by a null drive forms two runs with the raw NaN kept and enveloped only in the
output, a NaN drive in the selected run or earlier in the prefix withholds selection as
a missing drive number, and an unattributed row with a NaN drive stays neutral; a digest
with a trailing or leading newline is a usage
error before file access; negative byte counts and non-64-hex digests exit 3
before file access while a well-formed wrong digest still exits 2; non-calendar dates
exit 3 while a leap day validates;
wrong home/away/date/season and the real target request against a synthetic file are
unresolved with no fallback; conflicting `game_date` or `home_team` inside one game is
conflicting metadata while varying `time_of_day` or `week` is not; identical versus
conflicting duplicate keys; a team's second possession resolved to provider drive 4 (not
2), consecutive same-team drives kept separate; unresolved for a null drive in the
selected run or earlier in the prefix (the reviewed `(SYA,null),(SYA,1),(SYB,2),(SYA,3)`
sequence), non-contiguous or non-monotone earlier drives, a conflicting duplicate that
changes an earlier team, an unattributed row carrying an unaccounted drive, absent drive
column, and ordinal beyond observed possessions; a neutral timeout row and a
non-order conflict still resolve; absent/null/false-zero/value states and binary
shotgun; null and absent `play_type` reported as unknown; nullified penalty event plus
repeated key with no snap counting; 45-row possession truncated to 40 with two
boundaries per side; the game read's plan pushes the selection into the scan and eager
`read_parquet` is never called after verification; receipt never invents publication,
ingestion, or admission; operator-supplied times carried as supplied; output
reproducible apart from `processing_time`; CLI exit codes, refusal of `--out` that is
the input, a symlink or hardlink alias, a dangling symlink, or an unrelated existing
file with both files left byte-identical. Synthetic tests prove software behavior only.

## Prerequisites, separated

**For an offline read of a real file (this reader, no persistence):** an explicitly
authorized local input with its exact byte count and digest, supplied by the operator.
Nothing else. The result is external evidence about that file, not verified stored TIBER
evidence.

**For claiming verified stored TIBER evidence and for durable import/admission:** the
database-enforced read-only verification (plan item 3), the receipt-contract decision
(plan item 1), the transactional import design (item 4), and the admission gates (item
5). These are not prerequisites for the offline read above.

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

What the pinned Fantasy code actually does (reference only, `shared/schema.ts` and
`server/scripts/import_nflfastr_2025_bulk.py` at the pinned commit):

- `bronze_nflfastr_plays` has a unique index on `(game_id, play_id)`, a `raw_data`
  jsonb column, normalized columns, and `imported_at` / `created_at` defaults.
- The 2025 bulk importer writes the **entire source row** into `raw_data`
  (`row.to_dict()` with NaN coerced to null) alongside the selected normalized columns.
  Selecting normalized columns therefore does not by itself lose the source row.
- Normalized handling is mixed: `complete_pass`, `incomplete_pass`, `interception`,
  `touchdown`, `first_down_pass`, and `first_down_rush` map a null source value to
  `False`, which collapses null and explicit zero for those six columns only; `sack`,
  `qb_hit`, `shotgun`, `no_huddle`, and `qb_scramble` go through a helper that keeps
  null as null. A boolean column default in the schema does not by itself collapse
  null; only a caller that writes `False` for null does.
- The importer deletes the whole season before inserting and records no input digest.

What is **unknown** and must not be claimed: whether the deployed database was populated
by this importer or an earlier variant; whether the deployed `raw_data` rows are complete;
and whether the pandas-to-JSON path preserves every parquet type (integers stored as
floats, timestamps, nested values) faithfully. JSONB retention must be validated against
the source before it is described as lossless.

Consequence: `raw_data` is the plausible lossless carrier, subject to that validation, and
the normalized boolean columns with null-to-`False` coercion must not be the record of
truth for null/zero distinctions. **There is no column associating a row with the input
digest or source revision.** `imported_at` is processing time and must not stand in for
retrieval or publication time. A loose report beside the database is not durable
linkage: the minimum durable association is a source-receipt row keyed by digest, with
each play row carrying that receipt key (or the digest itself) in a dedicated column or a
dedicated `raw_data` sub-object the importer is required to write. That is a schema
change and is not preapproved here.

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

## Exclusions and remaining blockers

This PR does not create a film-observation ledger, populate the signal ledger, produce
Forecast fields, reconcile the personal chart, grade players, compute route/block
percentages, enable season ingestion or scheduling, acquire provider data, connect to a
live database, or deploy. The personal chart and photographs are not committed.

Blockers before the target request can be run offline: operator authorization of one
pinned input acquisition or a provenance-bearing TIBER export, with its exact byte count
and digest supplied to this reader. Blockers before any durable import or any claim of
verified stored TIBER evidence: the item-3 read-only database verification and the
item-1 receipt contract decision.

**Push boundary.** The first commit on this branch was pushed after repository-level
checks only (no CI workflows, no branch-scoped deploy trigger in `railpack.json` or
`.replit`); account-level branch deployment binding was not verified at that time, which
the review recorded as an unresolved execution-boundary deviation. The F1–F5 repair was
returned as a local patch. On 2026-09-10 the operator's read-only Railway inspection of
project TIBER-data, production environment, service TIBER-Data recorded: source branch
`main`; all twenty returned recent deployments from `main`, the latest being
`b0c79de5` created 2026-09-09T17:42:13Z; no deployment for `2da2f604` or this branch;
zero staged changes. Pushing this feature branch is therefore not configured to deploy
that Railway production service. That receipt covers Railway only; no Replit
account-level inspection occurred, and repository evidence remains the only evidence
about Replit. The R1 repair commit was pushed on that basis.
