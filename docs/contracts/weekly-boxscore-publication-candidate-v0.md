# Weekly intake and candidate publication v0

Status: implementation candidate, not source admission or production activation.
Authority: Joe approved the recommended weekly intake/publication slice on 2026-09-14.
Task classes: contract, data artifact, provenance audit and downstream handoff.

Data owns raw provider observations, receipts, exact game/team identities and reconciled denominators. Fantasy owns scoring policy, descriptive buckets and presentation. This slice does not change PBP #269, databases, the 2025 historical admission, or canonical identity mappings.

## Source intake

`python scripts/intake_weekly_boxscore_v0.py --season 2026 --week 1`

Explicitly acquires the exact nflverse-data stats_player/stats_team weekly season CSV assets. Both release metadata reads must agree around the download; bytes must match release size and SHA256. No missing-asset fallback exists. The existing audited CC BY 4.0 license bytes must match their fixed digest. Separate source retrievals are not atomic upstream publication.

Snapshots under `data/raw/weekly_boxscore` are content-addressed by season/week, both source digests and license digest. Identical intake preserves the first receipt and returns unchanged. Changed bytes produce a different snapshot. Commit all raw support before offline preparation. Successful intake is not successful validation or admission.

`python scripts/intake_weekly_schedule_v0.py`

Reads the released `nflverse-data/releases/download/schedules/games.csv` under the same checked license, with matching release metadata/digest. It does not mirror the separate nfldata repository. The schedule supplies game membership only: no explicit final-status field was established. Scores, elapsed kickoff and release timestamps do not certify finality.

## Offline publication contract

`python scripts/publish_weekly_boxscore_candidate_v0.py --source-dir SOURCE --source-commit FULL_SHA --schedule-dir SCHEDULE --schedule-commit FULL_SHA`

Schedule arguments are optional as a pair. Support must match exact local Git objects; lazy fetching is disabled. Fixture flags, unsupported receipt/schema/source families, modified license bytes, malformed scope, numeric/identity conflicts and corrupt source hashes fail closed. The pure facts builder is shared with historical replay. Raw source IDs retain their namespace; they are not new Sleeper/canonical identity admissions. Anonymous rows remain quarantined and contribute only to disclosed source-team reconciliation.

Envelope schema: `weekly_boxscore_publication_candidate_v0`.
- `candidate`: existing raw observations, reconciliation and explicit source receipt/support commit.
- `coverage`: observed/scheduled/missing/unexpected game IDs; schedule coverage matched, partial_or_conflicting or unavailable. `game_finality: unknown`, `full_week_final: false` in v0, even when membership matches.
- `schedule_receipt`: independent source, hash, clocks, license and support commit, or null.
- `source_receipt_sha256`, `builder_sha256`, `fact_builder_sha256`: reproducibility aids, not admission authority. Exact reviewed producer code commit also belongs in the handoff.
- `status: candidate_needs_review`, `consumer_admitted: false` always.

Candidate revisions live under `exports/candidates/weekly_boxscore/revisions/SEASON_REG_wWW`. SHA256 filenames contain immutable canonical JSON bytes. A file lock serializes writers. The candidate-only index records ordered revision hashes and predecessor links. Identical latest envelope bytes are a no-op. Corrected sources or changed builder/coverage evidence append a revision; old bytes remain inspectable. Each referenced revision hash is checked before publication. The index is NOT a consumer latest pointer or permission to publish evidence. No automatic scheduler is installed.

## Replay and scope limitations

`python scripts/replay_weekly_boxscore_v0.py --source-dir SOURCE_2025 --source-commit FULL_SHA --season 2025 --schedule-dir SCHEDULE --schedule-commit FULL_SHA --output docs/audits/REPORT.json`

Runs weeks 1–18 through the same preparation function. The original source receipt retains its acquisition scope; requested replay week is explicit in the artifact. Missing weeks fail rather than becoming empty successful weeks. Current corrected historical bytes do not establish pre-kickoff availability; this is not an as-of backtest. This bounded raw weekly replay does not claim completion of scoring, pace or role-baseline doctrine targets.

Air-yard discrepancies are preserved upstream and excluded from the first consumer. Routes, route participation, snaps, first reads, inside-five opportunities, injury/game-script context, QB designed runs and scrambles remain unavailable. Missing players are not zero-usage players. No rankings, forecasts, game availability, ownership, reserve eligibility or transactions follow from these artifacts.

## Release gates remaining

Independent review and local checks do not admit evidence. A later operator decision must accept exact source/artifact scope and limitations, then a separate consumer activation change must pin that receipt and exact bytes. User-facing leaders/weekly UI, current-roster ID joining, scheduling and deployment remain separate work. A final-status source is required before any final-week claim; preliminary publication must retain unknown finality and missing games.
