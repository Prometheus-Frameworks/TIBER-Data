# Historical landing-context candidate v0.1.0

## Status and purpose

This is the draft, candidate-only interface produced for TIBER-Data #236. It
tests a time-bounded landing-context shape against the April 2023 BAL, IND, and
LAR rookie pilots without making the cross-repository ownership decision or
either terminal decision requested by the issue. It is not a governed contract,
is not promoted, and authorizes no model or Forecast use.

The draft JSON Schema is stored beside its candidate inputs at
`data/candidate/historical_landing_context/historical_landing_context_candidate_v0.1.0.schema.json`.
Keeping it outside the governed `schemas/**` surface makes the authority
boundary explicit.

## Candidate bundle

| Artifact | Role |
| --- | --- |
| `exports/candidates/historical_landing_context/2023_bal_historical_landing_context_v0.1.0.json` | Zay Flowers / BAL evidence pilot |
| `exports/candidates/historical_landing_context/2023_ind_historical_landing_context_v0.1.0.json` | Josh Downs / IND evidence pilot |
| `exports/candidates/historical_landing_context/2023_lar_historical_landing_context_v0.1.0.json` | Puka Nacua / LAR evidence pilot |
| `exports/candidates/historical_landing_context/2023_historical_landing_context_pilot_bundle_v0.1.0.manifest.json` | Version/hash binding and consumer boundary |
| `exports/candidates/historical_landing_context/2023_historical_landing_context_pilot_bundle_v0.1.0.validation.json` | Deterministic validation result |
| `docs/reports/historical-landing-context-2023-source-availability-2026-08-05.json` | Machine-readable source/gap report |
| `docs/reports/historical-landing-context-2023-source-availability-2026-08-05.md` | Human-readable source/gap report |

## Temporal contract

`context.effective_at` is the configured snapshot instant and must equal
`context.context_cutoff`. The three values are end-of-draft-day UTC proxies
copied from the pinned, frozen Rookies pilots. They are not represented as exact
pick timestamps. Same-day external facts are inadmissible unless their sequence
relative to the selection is explicitly sourced; these candidates admit none.

Every evidence-bearing row has a separate temporal object:

- `effective_at` is the event instant when one is actually sourced; it remains
  null for 2022 season aggregates;
- `effective_period` identifies period facts such as `2022 REG`;
- `source_available_at` is the publication/release time, not the local retrieval
  time;
- `source_updated_at` is the source revision time;
- `known_by_cutoff` is `true`, `false`, or null; null means the lineage cannot
  prove the historical availability claim;
- `knowledge_basis` records why that state was assigned.

The governed player-season artifact was observed in June 2026 and has no
source-update timestamp. Its 2022 rows therefore remain candidate evidence with
`known_by_cutoff: null`, `needs_verification: true`, and
`admitted_to_reconstruction: false`. A later retrieval timestamp is never
rewritten as a historical effective or publication timestamp.

## Identity boundary

The pilots bind to #237 crosswalk candidate version `0.1.0`, SHA-256
`db1a08192aacf604d0be7930147b3e0182c28250bda246c65fbca290ed9a11e2`,
and manifest SHA-256
`ff3eacdd8e8f5c1b5ab59911b3f7fd8601cb2e17aadce1ab1c57c1f06e949c2d`.
Only `gsis_to_tiber_data_source_player_id` is allowed:

| Pilot | Crosswalk row | GSIS / Data source-player ID | Governed TIBER ID |
| --- | --- | --- | --- |
| BAL | `rookie-2023-gsis-00-0039064` | `00-0039064` | null |
| IND | `rookie-2023-gsis-00-0038997` | `00-0038997` | null |
| LAR | `rookie-2023-gsis-00-0039075` | `00-0039075` | null |

Display names, normalized names, later Data team history, and Forecast metadata
are prohibited projections. In particular, Forecast's Puka claim
`00-0038543` never enters these artifacts.

## Team and aggregation boundary

Draft-team identity comes from the 2023 crosswalk. Prior-season source team
codes are preserved independently. BAL and IND match exactly. The Rams source
uses `LA` in 2022, but #237's directed `LA → LAR` candidate rule is scoped to
source seasons 2023–2025. This interface does not silently widen it: the LAR
prior-season binding is blocked, `LA` remains raw, and normalization is false.

`player_season_coverage_v0` is one full-season row per player, not a
player-team split. The pilots therefore preserve only nonzero rows whose raw
`teams` list contains exactly one team as diagnostic candidate evidence.
Multi-team rows are kept in an exclusion ledger. The derived target and share
subtotals are explicitly partial, never renormalized, never complete team
totals, and never admitted to reconstruction.

## Observation, derivation, and missingness

The interface separates:

- `observations`: exact source projections plus explicit unavailable groups;
- `deterministic_derivations`: diagnostic subtotals over the projected rows;
- `interpretations`: structurally empty for this design/evidence PR.

Returning inventory, roster/depth, transactions, vacated targets/routes/snaps,
quarterback state, coaching/play-caller state, 2022 offense quality/personnel,
and injury/availability remain null or empty. Every required gap has a typed
missingness entry. Missing facts are never zero-filled, and prior-season usage
never stands in for roster membership or depth rank.

The draft schema is an interface rather than a null-only snapshot: each source
family has a typed available/unavailable union. Available branches distinguish
WR/TE/RB returning inventory, dated chronology events, cutoff roster members,
quarterback and coaching state, prior-offense metrics, injury records, and
source-complete vacancy components. The three pilots intentionally exercise the
unavailable branches until cutoff-admissible sources exist.

## Reproduction and validation

Run from the TIBER-Data repository root with the #237 candidate present:

```bash
python3 scripts/build_historical_landing_context_2023_pilots.py
python3 scripts/validate_historical_landing_context_2023_pilots.py \
  --report --data-repo-root . --rookies-repo-root ../TIBER-Rookies
python3 -m pytest -q tests/test_historical_landing_context_2023_pilots.py
```

The validator checks the draft schema, deterministic rebuild, exact three
identity/cutoff/pick tuples, #237 version/hash/edge, raw team codes, source-row
reproduction, multi-team exclusions, cutoff admission, complete-total and
vacancy nulls, missingness, no-inference boundary, and candidate authority. The
optional Rookies replay verifies all three frozen cutoff references by commit,
path, Git blob, SHA-256, and cutoff value without editing them.
The strict Data replay independently verifies every asserted `commit:path`, Git
blob, and content hash, including the #237 draft branch and every negative
inventory entry.

## TIBER-Rookies handoff

A Rookies consumer must first verify the bundle manifest, the #237 crosswalk
version/hash, and the exact GSIS-to-Data-source-player edge. It may inspect the
draft assignment and explicit source gaps. It must not treat the 2022 usage
rows or partial subtotals as cutoff-admitted landing-context facts, a returning
roster, depth order, or a complete team distribution. It must not compute
vacated opportunity from this bundle, normalize the 2022 `LA` rows to `LAR`,
consume a governed TIBER canonical ID, or interpret candidate presence as
promotion/model authority.

The frozen Rookies PR #284 artifacts are comparison references only. No file
under `data/historical/reconstruction_2023/**` is copied or modified here. The
Puka comparison's June 2023 Cooper Kupp source is explicitly excluded by the
hindsight firewall.

## Open operator questions

- Which repository owns cutoff-bounded roster, quarterback, coaching, and
  opportunity interpretation?
- Which immutable transaction, roster, coaching, and injury sources are
  admissible?
- Does a later-retrieved prior-season record with no revision timestamp qualify
  as known by the April 2023 cutoff?
- Should a separately evidenced candidate-only 2022 `LA → LAR` rule be admitted?
- What source can allocate full-season usage across teams?
- Is the end-of-draft-day proxy sufficient, or must exact pick timestamps be
  sourced?
- What durable non-name edge will connect GSIS to the governed TIBER canonical
  player-ID namespace?

The ownership split and all terminal decisions remain operator calls.
