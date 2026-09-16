# Weekly box-score candidate — 2026 Week 1

Status: local candidate prepared for review. No source promotion, Team admission,
consumer activation, scheduler, database write, remote push, PR, merge or deployment.

## Authority and scope

Joe approved the smallest next step proposed in the preceding backend audit:
one current-season weekly artifact from verified box-score inputs and explicit
team denominators, followed by validation. He also asked whether Data #269 had
built the 2026 loading bridge. This records the assistant's interpretation of
that live approval; it is not a separately retrieved operator action receipt.

Task classes: data artifact preparation, source validation and downstream handoff
preparation. This slice uses the existing first-party nflverse source family.
It does not introduce a vendor, scoring policy, model, ranking or production contract.
Candidate/source status remains explicit throughout. No existing governed artifact
or runtime behavior changed. Raw support was committed locally before generation,
as required by TRUTH_SOURCES.md.

## What #269 actually delivered

[Data PR #269](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/269)
merged on 2026-09-12 at merge commit
`e65791d3169c0234b80bdb4bfb00c3ed848d64dd`. It supplied a local receipt verifier,
one-game Parquet reader, CLI and synthetic tests for Research #22. Its reader
verifies supplied bytes and inspects a bounded game/possession. It does not
acquire a season file, ingest a weekly table, write a database, certify real 2026
coverage or activate Team. Its reviewed implementation is reusable for a later
play-by-play inspection, not required for this box-score candidate.

The separate existing `src/ingest/public.py` already has weekly player and team
loaders using `load_player_stats` / `load_team_stats` or nflverse release assets.
Its default configuration permits an explicitly labeled offline-fixture fallback.
This candidate uses exact retained source bytes and an offline builder instead;
there is no fixture fallback. No database connection was available in this session.

Data baseline: `93ac73af22da063f37694939a3494bcdf82ae1d4`.
Local committed source support: `66e4fc0695b26de25d086eabde54dd02f45de0ce`.
There were no open Data PRs in the fresh PR collection read during this check.
That does not establish the absence of unpushed work elsewhere.

## Source snapshot

Source directory: `data/raw/weekly_boxscore/2026_w01_20260914/`.

| Source | Asset update time (UTC) | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| nflverse weekly player CSV, 2026 | 2026-09-14 10:56:06 | 465069 | `7bf9b616d9f86a5357093b5af6bf1fa7138c1d4cb46cab4c2765fef852c30bc4` |
| nflverse weekly team CSV, 2026 | 2026-09-14 10:56:08 | 14021 | `ec35c7154c2a2232676c10ed94a7ca8b6ec7d531671b05a45b59970c12adfc6c` |

Exact source URLs, release asset IDs, separately observed retrieval start/end
clocks, sizes and hashes are in `receipt.json`. Both byte digests match the
published release asset metadata retrieved in this session. Mutable release URLs
may subsequently change; the retained snapshots preserve this particular read.

Attribution: nflverse contributors, CC BY 4.0, no endorsement implied. The
repository's `LICENSE.md` was retrieved and retained with its own hash. This is
a scoped source snapshot, not a blanket rights determination for other nflverse
datasets, participation providers, paid charting or future acquisition.

## Candidate shape and boundaries

Output: `exports/candidates/weekly_boxscore/2026_w01_20260914.v0.json`.
Schema marker: `weekly_boxscore_candidate_v0`; `consumer_admitted: false`.

Grain: one source player/game/team observation within explicit season, week and
season type. Team observations use game/team keys. GSIS-shaped source player IDs
are retained exactly; this does not establish a Sleeper identity edge or create a
new governed TIBER identity. NFL game-team, opponent and source position remain
attached to the observation; no current-roster/name join rewrites them.

The candidate carries 25 numeric source fields: passing attempts/completions,
yards, TDs, interceptions, sacks and sack fumbles lost; carries, rushing yards,
TDs and rushing fumbles lost; targets, receptions, receiving yards, TDs and
receiving fumbles lost; total lost fumbles; three two-point-conversion components;
receiving air yards and YAC; passing/rushing/receiving first downs. It retains
the provider's field names and does not silently replace total lost fumbles with
a sum of selected components.

Derived values are limited to carries plus targets, player targets divided by
explicit credited team targets, and player carries divided by all team carries.
The latter includes QB carries and is not RB-only backfield share. Each share
contains its numerator, denominator, value and availability reason. A missing,
zero or unreconciled denominator withholds the share. Missing columns/values stay
null; they never become observed zeroes.

Routes, route participation, snaps, first-read shares, red-zone/inside-five work,
designed runs, scrambles and injury context are unavailable. There are no scores,
usage buckets, projections, ownership, eligibility or transaction claims here.
Fantasy scoring and descriptive bucket thresholds remain downstream policy.

## Actual validation result

- Source scope is exactly 2026 REG Week 1; no out-of-scope rows were selected.
- 1041 player-source rows: 1040 identified observations plus one unattributed row.
- 30 reciprocal team observations represent 15 distinct game IDs.
- The 1040 identified observations span all source positions, including defense
  and special teams. Of those, 35 are QB, 83 RB, 74 TE and 140 WR. This is not an
  active-roster census, official games-played count or complete participation list.
- The first strict build stopped on player CSV row 1042, which has no player ID
  or display name. It is retained separately under
  `unattributed_source_observations` for SEA in `2026_01_NE_SEA`, with raw ID and
  source-row pointer. No identity was inferred. Its selected numeric fields are
  explicit zeroes. Reconciliation includes that source observation, while the
  player list excludes it. Other missing game/team identities remain fatal.
- All 25 selected fields are present and nonnull in the identified player and
  team rows. Source zeroes retain their source meaning; no independent audit of
  the upstream producer's missing-value policy is claimed.
- 730 of 750 team/metric comparisons match. Targets and carries reconcile for
  all 30 teams, as do the other 22 selected fields apart from receiving air yards.
- The 20 remaining discrepancies are all `receiving_air_yards`. Player sums and
  team values are both retained in the discrepancy ledger. Their cause may be a
  provider-definition difference or source disagreement; it was not settled in
  this slice. Air-yard shares and other air-yard-derived metrics are not produced.
  Air yards should remain audit-only for the proposed first consumer release.
- 18 focused synthetic unit tests pass. They cover byte tampering, duplicates,
  nulls, zero denominators, source disagreement, missing IDs, game/team joins,
  unsupported scope, invalid numeric values and absence of route/score inference.
- A separate implementer check compared all 26775 selected numeric values
  (including the unattributed observation) directly against their source CSV rows.
  Exact reproduction of the complete candidate bytes passed.
- CLI checks rejected both an existing output filename and a promoted-directory
  output. The original candidate hash remained unchanged and no promoted file
  was created.

These are implementer validation results, not an independent review. Reconciliation
between two nflverse tables is not independent box-score corroboration.

## Reproduction

Run from the repository root with Python's standard library; no dependency change:

```sh
python -m unittest discover -s tests -p test_weekly_boxscore_candidate_v0.py -v
python scripts/build_weekly_boxscore_candidate_v0.py --source-dir data/raw/weekly_boxscore/2026_w01_20260914 --source-commit 66e4fc0695b26de25d086eabde54dd02f45de0ce --output exports/candidates/weekly_boxscore/2026_w01_20260914.reproduction.json
```

The CLI requires exact committed source bytes, verifies the receipt hashes and
license snapshot, accepts only a candidate output directory, and refuses to
overwrite an existing artifact. A reproduction at a new filename should have the
same bytes as the candidate. It does not fetch anything or activate a consumer.

## Remaining boundary and handoff

No schedule or game-status source was read. Full-week completeness and game
finality remain unverified, despite the valid season/week keys. Missing games
and players must not be assigned zeroes. Stat corrections may require a new,
separately identified snapshot; the original must remain reproducible.

Audit triggers: new raw support, candidate artifact, identity handling and
source/handoff semantics. Independent review is pending. The existing Evidence
Layer doctrine additionally requires historical replay of the same artifact
family before live promotion; this first candidate does not satisfy that gate.

Next review should inspect identity quarantine, raw source fidelity, population
coverage, denominator semantics, the air-yard discrepancies and the downstream
field allowlist. Before any release: independently review the candidate, complete
the required historical replay and scope/finality checks, obtain the operator's
promotion disposition, then separately wire Team's bounded consumer. No broad
legacy-runtime activation or #269 reader modification is required.

Files created: four raw snapshot/receipt/license files; one offline builder; one
focused synthetic test file; one candidate JSON; this report and its machine-readable
validation companion. Existing governed files are unchanged.
