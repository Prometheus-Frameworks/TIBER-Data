# Audit: TIBER_IDENTITY_CROSSWALK_V2 — GSIS vocabulary promotion

- **Date:** 2026-08-09
- **Scope:** promotion of a bounded candidate slice into a **new versioned contract**, `TIBER_IDENTITY_CROSSWALK_V2`, whose `tiber_player_id` is a GSIS player id.
- **Tracking issues:** [TIBER-Data #241](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/241), [TIBER-Fantasy #317](https://github.com/Prometheus-Frameworks/TIBER-Fantasy/issues/317)
- **Audit triggers hit** (AGENTS.md "Audit triggers"): touches `exports/promoted/**`; touches player identity semantics and `exports/promoted/identity_crosswalk/**`; changes source/provenance wording; adds a large generated JSON artifact; adds builder code (matching tests added: `tests/test_identity_crosswalk_v2.py`); adds a contract under `schemas/**`.
- **Operator authorization:** granted 2026-08-09 (H4MMER), on the decision laid out in TIBER-Fantasy#317.

---

## 1. Verdict

**Promote as V2, leaving V1 intact.** The change is a breaking contract change and is versioned rather than applied in place, per AGENTS.md non-negotiable rule 6 ("Contracts change explicitly. Breaking changes are versioned. Never change a contract to fit bad data.").

## 2. Why a new contract was required

TIBER-FORGE #50 promoted a `FORGE_PLAYER_STATIC_V1` artifact keyed by GSIS `player_id`. The promoted V1 crosswalk maps provider ids to `tiber-data-player-2025-*` slugs. Measured overlap against the new FORGE artifact: **0 of 50**. Downstream (`TIBER-Fantasy leagueDashboardService`), a V1-vocabulary crosswalk therefore resolves to zero FORGE rows **while still counting those players as `identity_crosswalk` matched** — a silently misleading diagnostic rather than an honest miss.

The V1 schema (`schemas/tiber_identity_crosswalk_v1.schema.json`) constrains `tiber_player_id` to `^tiber-data-player-2025-...`, pins `coverage` as a `const`, restricts `match_method` to `verified_manual_seed`, `confidence` to `exact|high|provisional`, requires a non-null `team`, and sets `additionalProperties: false`. A GSIS-keyed artifact violates all of these. **An earlier revision of this work overwrote the V1 artifact in place and broke `scripts/build_identity_crosswalk_v1.py --check`; that was caught in PR review (Codex P1, PR #244) and is corrected here** — V1's schema, builder, validator, artifact, and tests are untouched and still pass.

## 3. Findings (per the required audit questions)

- **Source lineage:** rows derive from `exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json` (issue #241), itself built from the promoted coverage universe joined to Sleeper's public players dump (audited 2026-08-09, `external_candidate`, identity-mapping evidence only). No new external source is admitted by this promotion.
- **Slice boundaries:** 68 records = 49 rows backing the pinned FORGE cohort + 19 provider ids already promoted in V1, re-expressed as GSIS. The remaining ~1,038 candidate rows stay candidate-tier. Widening the slice requires a new authorization.
- **Identity risk — the whole subject.** Every one of the 49 FORGE-cohort rows was verified individually rather than accepted on its tier label:
  - 26 `name_exact` rows checked for team/position agreement against the FORGE artifact; 23 agree exactly.
  - `LA` vs `LAR` (Kyren Williams, Puka Nacua) is an nflverse/Sleeper abbreviation difference, not a mismatch.
  - The one genuine divergence, **Travis Etienne** (FORGE `JAX`, Sleeper `NO`), was run down: the dump contains exactly one `Travis Etienne` (RB, sleeper id 7543); `Trevor Etienne` is a distinct player that cannot collide under name normalization. The difference is temporal — FORGE reflects the completed 2025 season, the dump reflects the 2026 roster. Same explanation for the two `gsis_direct` drifts (Mike Evans, Tyreek Hill), where identity is provider-declared and certain.
  - `name_exact` rows carry `confidence: medium`, distinguishing them from provider-declared id agreements in the artifact itself rather than in prose.
- **Reproducibility / provenance:** both source artifacts are pinned by **sha256** in `source_artifacts`. `--forge-sha256` refuses to promote when the supplied FORGE file's bytes do not match the pin, so re-running against a different file at the same path cannot silently promote a different or larger slice. (An earlier revision recorded an ephemeral `/tmp` scratchpad path as provenance; caught in PR review, corrected here, and now guarded by a test asserting no `/tmp/` path appears in promoted provenance.)
- **Fail-closed behavior:** the promoter validates against the committed V2 schema **before** writing, and refuses to write on duplicate `provider_canonical_id` — the exact condition that makes the downstream consumer throw `duplicate_ids`.
- **Leakage risk:** none in scope. Identity facts only; no outcomes, no features, no scores.
- **Downstream recursion (rule 4):** none. FORGE output is used only to *scope which identities to promote*; no FORGE-derived value enters a crosswalk row.

## 4. Known losses, stated plainly

1. **`Frank Gore Jr.` is dropped.** He is the single V1 mapping with no GSIS identity in the promoted coverage universe. Retaining him would reintroduce the second dead vocabulary this contract exists to remove. He has no FORGE row either way. His V1 row remains intact in the untouched V1 artifact, and the promoter reports the drop by name on every run.
2. **`Kenneth Gainwell` has no crosswalk row** — `no_match` in the #241 review CSV — so FORGE-cohort coverage is 49/50.
3. **19 promoted records resolve to no FORGE row.** These are prior-verified players outside the current top-50 cohort. Unlike the V1 dead rows, these are correct identities that are simply uncovered, so "matched but unscored" is now a meaningful state.

## 5. Constraints of the classification

1. GSIS vocabulary only; V1 and V2 must not be merged into one artifact or consumed interchangeably.
2. Slice is bounded as described in §3; widening requires a new operator authorization and a new audit.
3. `name_exact` rows are `medium` confidence by construction — consumers that require provider-declared identity should filter on `match_method`.
4. Re-promotion must pin the upstream FORGE artifact by sha256.
5. V1 remains the contract of record for any consumer not yet migrated; it is frozen, not deleted.
