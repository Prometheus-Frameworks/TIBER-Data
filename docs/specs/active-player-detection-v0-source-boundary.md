# Spec: `active_player_detection_v0` — Contract and Source Boundary

- **Status:** Pre-contract specification. **Spec-only. Not implementation-ready. Not a promoted contract. Not a dataset.**
- **Date:** 2026-06-30
- **Tracking issue:** [TIBER-Data #186](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/186)
- **Predecessor:** [TIBER-Data #184](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/184) / [PR #185](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/185) — audit `docs/audits/player-availability-season-coverage-forecast-readiness-2026-06-30.md`.

> **Why this document exists.** The goal is not to know who is active today. The goal is to prevent TIBER from *pretending* it knows. This document defines the contract shape, enum boundary, and source boundary for a future active-player detector **before** any detector is built, any roster is scraped, any data is ingested or promoted, or any availability signal is bound into Forecast. A spec is not a dataset; placing this under `docs/specs/` (not `docs/contracts/`) is deliberate — it signals that no implementation-ready contract is being asserted.

---

## 1. Purpose and non-goals

### Purpose

Define the smallest safe contract/spec boundary for active-player detection so that, **if and only if** a legitimate source and as-of policy are later approved, an implementer can build `active_player_detection_v0` without re-deriving the boundary or drifting from governed vocabulary.

### Non-goals (hard blocks)

This document does **not**, and any PR carrying it must **not**:

- build the detector or any code that emits active status;
- scrape or fetch live/current rosters;
- ingest new roster, injury, or transaction data;
- promote or create any dataset;
- modify Forecast or Teamstate;
- start FORGE work or bind anything into Forecast;
- create a Forecast gate;
- claim current active-player truth;
- infer active/inactive from missing rows;
- treat the stale `player_ownership_latest.json` snapshot as current truth;
- treat fixtures or smoke-test subsets as current truth;
- make fantasy advice, rankings, start/sit, trade, draft, or product claims.

This is a boundary document. Where a source is missing, it flags the gap rather than inventing the source (per `TRUTH_SOURCES.md` and `AGENTS.md` fail-closed posture).

---

## 2. Relationship to `player_ownership_v0`

`player_ownership_v0` (`schemas/player_ownership_v0.schema.json`, `docs/contracts/player-ownership-v0.md`) already provides:

- a governed **ownership/roster-membership** status vocabulary (`ownership_status`);
- a provenance shape (`source_refs[]` with `source_name`, `observed_at`, `source_updated_at`, `confidence`, `notes`);
- an explicit **staleness posture** (e.g., the `source_snapshot_stale_for_current_roster` note in `player_ownership_latest.json`);
- fail-closed `unknown` semantics.

It does **not** provide:

- full-universe **current** active-player truth;
- current roster truth for all players;
- **gameday-inactive** state;
- transaction truth beyond fixture/candidate events (`player_ownership_events_2026.jsonl` is a single `fixture_demonstration_only` event today).

**`active_player_detection_v0` is a different axis from `player_ownership_v0`.** Ownership answers *"what roster-membership category is this player in?"* Detection answers *"is this player available/active for a given scope, and on what source basis?"* The two must coexist as **separate fields**, never as one masquerading as the other (see §3).

---

## 3. Enum decision: **Option B (distinct detection enum) — with disciplined reuse of `ownership_status`**

**Decision: adopt Option B.** Define a distinct `active_status` enum for the gameday/availability/detection axis, **and** carry the governed `ownership_status` (reused verbatim from `player_ownership_v0`) as a *separate* field for the ownership-membership axis. Document the mapping (below) as an explicit, non-silent boundary.

### Why Option B over Option A

Option A (reuse `ownership_status` alone) was considered and rejected as the *sole* mechanism because the governed enum cannot honestly express the detection axis:

- there is **no first-class gameday `inactive` value** in `ownership_status` (a player can be `active_roster` and still be a gameday inactive);
- **`traded`** is not an ownership status — it is a transaction event (`player_ownership_change_event_v0.event_type = team_change`/`trade`);
- **`released`** maps only approximately to `free_agent` (release is a transaction; free-agent is the resulting ownership state).

Collapsing these into `ownership_status` would either drop real distinctions or silently overload governed values — both forbidden by the repo's "no enum drift / no contract drift" rules.

### Why not a *free-floating* new enum

A new enum that re-encodes ownership states (e.g., re-inventing `practice_squad`, `free_agent`) would create drift. The disciplined form keeps **two narrow axes**:

- `ownership_status` — **reused verbatim** from `player_ownership_v0` (no drift);
- `active_status` — **new**, scoped only to availability/detection semantics ownership cannot express.

### Required enum mapping (Option B boundary)

The `active_status` enum is: `active | inactive | ir | practice_squad | released | traded | unknown`.

| detection `active_status` | governed `ownership_status` | boundary note |
|---|---|---|
| `active` | `active_roster` | direct |
| `inactive` | *(none)* | no governed value for gameday-inactive; carried only in `active_status`; needs separate roster-status field or ownership-contract extension before it can round-trip |
| `ir` | `injured_reserve` | direct |
| `practice_squad` | `practice_squad` | direct (same label, distinct field) |
| `released` | `free_agent` | **approximate** — release is a transaction; `free_agent` is the resulting ownership state; do not collapse without a `source_ref` |
| `traded` | *(none)* | **not** an ownership status; model as `player_ownership_change_event_v0.event_type = team_change`/`trade` |
| `unknown` | `unknown` | direct |

**Hard rule:** the contract **must not** silently emit `active`, `inactive`, `ir`, `released`, or `traded` as if they were valid `player_ownership_v0.ownership_status` values, and **must not** emit `unsigned_draft_pick`, `college`, `devy`, `retired`, or `suspended` as `active_status` values. The two enums are validated independently. Where a value has no counterpart, the mapping is `none` and the cross-field value is `unknown` / omitted — never invented.

---

## 4. Required field shape

Proposed shape for a future `active_player_detection_v0` artifact. **Illustrative, not a validator.** No record below asserts any real player's current status.

### Artifact envelope

| field | type | required | notes |
|---|---|---|---|
| `contract_version` | const `"active_player_detection_v0"` | yes | only when a new contract is actually created |
| `generated_at` | ISO-8601 UTC datetime | yes | when the artifact was produced |
| `as_of` | ISO-8601 UTC datetime | yes | the instant the active-status claim is asserted valid *for* (the detection as-of boundary) |
| `season` | integer | yes | NFL season scope |
| `week` | integer \| null | yes | null when date-scoped or season-level |
| `date_scope` | string \| null | conditional | required when `week` is null |
| `source_name` | string | yes | e.g., `nflreadpy.load_rosters_weekly` |
| `source_path` | string | yes | e.g., `data/processed/evidence/roster_player_team_map_2025.source_backed.json` |
| `source_updated_at` | ISO-8601 \| null | yes | source's own update time; null when unavailable |
| `observed_at` | ISO-8601 UTC datetime | yes | when TIBER-Data observed the source |
| `staleness_status` | enum `current \| stale \| unknown` | yes | artifact-level honesty about whether `as_of` reflects current truth |
| `staleness_reason` | string \| null | conditional | required when `staleness_status` ≠ `current` |
| `coverage` | string | yes | e.g., `not_full_player_universe`, `2025_weekly_membership_only` |
| `records` | array of player records | yes | see below |

### Per-player record

| field | type | required | notes |
|---|---|---|---|
| `player_id` | string \| null | yes | canonical TIBER/nflverse id; null only if genuinely unknown (do not invent) |
| `player_name` | string \| null | yes | |
| `team` | string \| null | yes | |
| `position` | string \| null | yes | |
| `ownership_status` | `player_ownership_v0.ownership_status` enum \| null | yes | reused verbatim; the ownership-membership axis |
| `active_status` | `active_status` enum | conditional | **only when Option B detection is in scope**; the availability/detection axis; default `unknown` |
| `status_basis` | enum `source_truth \| derived_classification \| unavailable_unknown` | yes | whether status is asserted by source, derived by TIBER, or unavailable |
| `confidence` | string | yes | provenance posture (e.g., `source_verified`, `provisional`, `low`) — not a downstream score |
| `source_refs` | array | yes (min 1) | each: `source_name`, `source_url?`, `observed_at`, `source_updated_at?`, `confidence`, `notes?` |
| `staleness_flag` | enum `current \| stale \| unknown` | yes | row-level staleness when it differs from the envelope |
| `fail_closed_reason` | string \| null | conditional | **required** whenever `active_status = unknown` or `status_basis = unavailable_unknown` — states *why* status is not known |
| `notes` | string \| null | no | bounded source/provenance note |

---

## 5. Source boundary

A future implementation may draw **only** from the conservative inputs below until a new source passes a separate source/provenance review.

### 5.1 Known partial source — `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

Provider: `nflreadpy.load_rosters_weekly([2025])`, `source_status: source_verified`, 14,348 rows / 971 players, weeks 1–22.

**Can provide:** player identity, team, position, season/week roster **membership**, source-backed roster presence.

**Cannot provide:** active vs inactive; IR vs active roster; practice squad; released/traded current state; current 2026 active state; gameday-inactive status. (Every row carries `active_roster_status: "unknown"`.)

→ From this source, `status_basis` is at best `derived_classification` for *membership presence*, and `active_status` must be `unknown` (with `fail_closed_reason`). Membership is **not** availability.

### 5.2 Existing status-shaped contract — `player_ownership_v0`

Artifact today: `exports/promoted/player_ownership/player_ownership_latest.json` (27 players, provisional, `source_snapshot_stale_for_current_roster`).

**Can provide:** ownership/status vocabulary; provenance shape; explicit staleness posture; fail-closed `unknown` semantics.

**Cannot provide:** full-universe current active-player truth; current roster truth for all players; gameday-inactive state; transaction truth beyond fixture/candidate events.

→ Usable for the `ownership_status` axis and provenance shape **only**, and only as a `stale` snapshot — never as current truth, never universe-complete.

### 5.3 Out of boundary (requires separate approval)

Live roster scraping; gameday inactives feeds; injury reports; transaction feeds; any 2026 "current" roster source; any new ingestion. None of these are authorized by this spec.

---

## 6. Staleness / as-of rules

- Every artifact **must** carry an explicit `as_of` and `staleness_status`.
- `staleness_status = current` is permitted **only** when a source whose `source_updated_at`/`observed_at` is at or after `as_of` exists and has passed a source/provenance review. The two in-boundary sources today are 2025-bounded and therefore cannot back a `current` claim about any later `as_of` → they are `stale` for present-day questions.
- A stale snapshot **cannot** be relabeled current by re-`generated_at`-ing it. Staleness is a property of the source observation, not of artifact generation time.
- Row-level `staleness_flag` overrides the envelope when a specific row's source is older/newer than the artifact default.

---

## 7. Fail-closed rules

1. Missing status becomes `unknown` — **never** `active`.
2. A missing row is **not** proof of inactivity. Absence ≠ inactive.
3. A stale snapshot **cannot** be treated as current truth.
4. Source-backed **membership** is **not** the same thing as **active status**.
5. Transaction terms (`traded`, `released`) **must not** be collapsed into current availability without `source_refs`.
6. Fixtures and smoke-test subsets **cannot** authorize current active status.
7. Current active status **requires** an explicit as-of source boundary that has passed provenance review.
8. Whenever `active_status = unknown` or `status_basis = unavailable_unknown`, `fail_closed_reason` is **required**.
9. `active_status` and `ownership_status` are validated independently; a value valid in one enum is **invalid** in the other.

---

## 8. Examples of allowed and disallowed interpretations

### Allowed

- *"For 2025 week 5, `roster_player_team_map_2025.source_backed.json` shows player X on team Y's weekly roster (membership). `active_status = unknown`, `status_basis = derived_classification` (membership presence only), `fail_closed_reason = "source provides roster membership but not active/inactive status"`."*
- *"`player_ownership_latest.json` reports player Z `ownership_status = active_roster` as observed 2025-wk18; `staleness_status = stale`, `staleness_reason = "snapshot from 2025 week 18; not confirmed current"`. No `active_status` is asserted."*

### Disallowed

- ❌ Treating presence in the 2025 weekly roster map as `active_status = active`.
- ❌ Treating a player's absence from a roster row as `active_status = inactive`.
- ❌ Emitting `active_status = active_roster` (cross-enum leakage) or `ownership_status = inactive`.
- ❌ Reporting `staleness_status = current` for a 2026 `as_of` using only 2025-bounded sources.
- ❌ Using the 27-player `player_ownership_latest.json` subset to claim universe-wide active status.
- ❌ Deriving `traded`/`released` availability without a `source_ref` to a transaction event.

---

## 9. Consumer guidance for Forecast

- **Forecast must not consume `active_player_detection_v0` until a real artifact exists and passes a separate coverage/provenance gate.** This spec authorizes no binding.
- **A spec is not a dataset.** Nothing here is loadable.
- **A roster-membership row is not an availability feature.** Do not feed membership presence as if it were active status.
- **`unknown` must remain unknown** — never coerced to `0`, `false`, or `inactive`.
- **Keep semantics separate:** gameday-inactive, IR, traded, released, and free-agent must remain distinct unless the contract explicitly maps them (per §3). Forecast must not flatten them.
- Until a gate exists, Forecast should treat active-player availability as **out of scope**, exactly as the audit recommended.

---

## 10. Recommended implementation issue (separate, not started here)

A future, separately-approved issue — only if a legitimate source and as-of policy are accepted — would be:

**`feat: implement active_player_detection_v0 (gated, source-bounded)`**, with required gates:

1. an approved source with `source_updated_at`/`observed_at` ≥ the target `as_of`, passing source/provenance review;
2. a schema + validator proving: valid examples pass; missing source/as-of metadata fails; missing status is represented as `unknown`; invalid enum values fail; `active_status` cannot be emitted as `ownership_status` (and vice versa); staleness fields are explicit;
3. fail-closed `unknown` behavior end-to-end;
4. **no** Forecast binding until a separate coverage/provenance gate passes.

Implementation must remain blocked until those gates are explicitly approved. This document does not authorize it.

---

## Appendix — Referenced governed vocabulary (for implementers)

- `player_ownership_v0.ownership_status`: `active_roster | practice_squad | unsigned_draft_pick | college | devy | free_agent | retired | injured_reserve | suspended | unknown`.
- `player_ownership_change_event_v0.event_type`: `team_change | status_change | signing | release | trade | draft_selection | practice_squad_change | injured_reserve_change | free_agent_status_change | college_program_change`.
- Proposed **new** `active_status` (this spec, Option B): `active | inactive | ir | practice_squad | released | traded | unknown`.
- Proposed **new** `status_basis` (this spec): `source_truth | derived_classification | unavailable_unknown`.
