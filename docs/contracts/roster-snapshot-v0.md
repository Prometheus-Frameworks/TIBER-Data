# Roster Snapshot v0 Contract

`roster_snapshot_v0` defines the canonical scaffold for time-bounded roster identity artifacts owned by TIBER-Data.

Scope in this change is contract, documentation, and JSON Schema only. This contract does not add a full ingestion pipeline, fantasy interpretation, Teamstate scoring, or downstream repository mutation.

Schema file: `schemas/roster_snapshot_v0.schema.json`

## Purpose

TIBER-Data owns roster truth so downstream repositories can stop maintaining independent guesses about player/team membership.

The contract supports source-linked answers to questions such as:

- who is on what team as of a specific date or week
- what canonical player ID represents a rostered player
- what canonical team ID represents the team
- which source observed or reported the roster fact
- when the roster fact was generated, updated, and valid
- whether transaction context exists for a roster entry

## Repository responsibility doctrine

- TIBER-Data knows what is true.
- TIBER-Teamstate explains what roster truth means for the team.
- TIBER-Fantasy explains what roster truth means for fantasy.

This contract must not carry fantasy projections, lineup advice, player value scores, Teamstate impact scores, depth-chart interpretation, role optimism/pessimism, or speculative fit analysis.

## Non-negotiable rules

- Do not invent player IDs.
- Do not invent team IDs.
- Unknown fields should be `null`, not fake defaults.
- Every roster snapshot must be time-bounded with `data_window_start` and `data_window_end`.
- Roster truth must remain separate from Teamstate interpretation.
- Transaction claims must remain source-linked.
- Downstream repositories should consume this contract instead of maintaining independent roster truth.
- If source truth is missing, reduce scope rather than filling the gap.

## Temporal grounding

Reasoning without time is ungrounded reasoning.

Roster artifacts must preserve:

- `generated_at` — when TIBER-Data generated the artifact
- `source_updated_at` — when the underlying source was last updated, if known
- `data_window_start` and `data_window_end` — the bounded validity window for the snapshot
- entry-level `valid_from` and `valid_to`, when a narrower player-level validity window is known
- source-level `observed_at` and `source_updated_at`, when available

A roster fact without a timestamp is unsafe for downstream reasoning. Consumers must not treat untimestamped roster facts as canonical roster state.

## Artifact shape

A `roster_snapshot_v0` artifact is a single team roster snapshot for a bounded season/week/date window.

Top-level fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `artifact_id` | string | yes | Stable artifact identifier. |
| `contract_version` | string | yes | Must be `roster_snapshot_v0`. |
| `generated_at` | date-time string | yes | ISO-8601 UTC generation timestamp. |
| `source_updated_at` | date-time string or null | yes | Latest known source update timestamp for the snapshot. Use `null` if the source does not expose it. |
| `data_window_start` | date-time string | yes | Inclusive lower bound for the snapshot's validity window. |
| `data_window_end` | date-time string | yes | Exclusive or documented upper bound for the snapshot's validity window. |
| `season` | integer | yes | NFL season represented by the snapshot. |
| `week` | integer or null | yes | NFL week represented by the snapshot, or `null` when the snapshot is date-only or season-level. |
| `team_id` | string or null | yes | Canonical TIBER team ID. Use `null` rather than an invented ID. |
| `team_abbr` | string or null | yes | Team abbreviation as represented by the source/canonical team mapping. |
| `team_name` | string or null | yes | Human-readable team name. |
| `roster_entries` | array | yes | Source-linked player roster entries. |

## Roster entry shape

Each roster entry represents a player membership assertion inside the snapshot window.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `player_id` | string or null | yes | Canonical TIBER player ID. Use `null` rather than an invented ID. |
| `player_name` | string or null | yes | Player display name from canonical identity resolution or source. |
| `position` | string or null | yes | Player position if known. |
| `status` | string or null | yes | Roster status if known, such as active, injured reserve, practice squad, released, traded, unsigned, or departed context. |
| `jersey_number` | integer, string, or null | no | Jersey number when source-backed. Use `null` when unknown. |
| `roster_role` | string or null | no | Source-backed roster role only; not a Teamstate or fantasy interpretation. |
| `acquired_via` | string or null | no | Source-backed acquisition mode if known. |
| `transaction_context` | object or null | no | Source-linked transaction context. Must not be speculative. |
| `source_refs` | array | yes | One or more source references supporting the roster entry. |
| `valid_from` | date-time string or null | no | Entry-level validity start when known. |
| `valid_to` | date-time string or null | no | Entry-level validity end when known. |

### Transaction context

`transaction_context` is for source-backed transaction metadata only. It can describe items such as signing, trade, release, waiver claim, injured-reserve placement, or departure context when sources support those claims.

Transaction context must not infer causality, team impact, fantasy impact, depth-chart impact, or replacement hierarchy. If a transaction claim is included, it must be traceable through `source_refs`.

Supported scaffold fields inside `transaction_context`:

| Field | Type | Description |
| --- | --- | --- |
| `transaction_id` | string or null | Stable transaction identifier if known. |
| `transaction_type` | string or null | Source-backed transaction type. |
| `transaction_date` | date string or null | Source-backed transaction date. |
| `source_statement` | string or null | Short source-grounded statement, not analysis. |
| `related_team_id` | string or null | Related canonical team ID if source-backed. |
| `related_team_abbr` | string or null | Related team abbreviation if source-backed. |
| `notes` | string or null | Bounded source/provenance note. |

## Source reference shape

Each `source_refs[]` item supports inspection of the roster claim.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `source_name` | string | yes | Name of the source system, document, feed, or fixture. |
| `source_url` | string or null | no | URL when available. Use `null` when unavailable. |
| `observed_at` | date-time string | yes | When TIBER-Data observed the source. |
| `source_updated_at` | date-time string or null | no | Source's own update timestamp when available. |
| `confidence` | string | yes | Source confidence or verification posture. |
| `notes` | string or null | no | Short bounded source note. |

`confidence` is not a downstream interpretation score. It is a provenance/verification posture for the roster fact.

## Consumer expectations

Downstream consumers must:

- validate against `schemas/roster_snapshot_v0.schema.json`
- preserve timestamps and source references
- treat `null` as unknown, not as negative evidence
- avoid creating independent roster-truth tables when this artifact exists
- avoid promoting docs-only examples as source truth
- request narrower scope from TIBER-Data when roster coverage is missing

## Illustrative Jets example fixture only

The following example is documentation-only. It is intentionally not promoted source truth, not backed by real source references in this repository, and must not be treated as verified New York Jets 2026 roster state.

Names in this example, including Breece Hall, Garrett Wilson, Geno Smith, T'Vondre Sweat, Sauce Gardner, and Quinnen Williams, are included only to demonstrate contract shape, current-roster entries, and departed-context-style entries. Do not infer that any listed membership, departure, acquisition, or transaction is true unless a future promoted artifact supplies real canonical IDs and real source references.

```json
{
  "artifact_id": "docs-example-roster-snapshot-nyj-2026",
  "contract_version": "roster_snapshot_v0",
  "generated_at": "2026-05-08T00:00:00Z",
  "source_updated_at": null,
  "data_window_start": "2026-03-01T00:00:00Z",
  "data_window_end": "2026-09-01T00:00:00Z",
  "season": 2026,
  "week": null,
  "team_id": null,
  "team_abbr": "NYJ",
  "team_name": "New York Jets",
  "roster_entries": [
    {
      "player_id": null,
      "player_name": "Breece Hall",
      "position": "RB",
      "status": "illustrative_unverified_roster_context",
      "jersey_number": null,
      "roster_role": null,
      "acquired_via": null,
      "transaction_context": null,
      "source_refs": [
        {
          "source_name": "docs_only_illustrative_example",
          "source_url": null,
          "observed_at": "2026-05-08T00:00:00Z",
          "source_updated_at": null,
          "confidence": "illustrative_not_verified",
          "notes": "Documentation example only; not promoted roster truth."
        }
      ],
      "valid_from": null,
      "valid_to": null
    },
    {
      "player_id": null,
      "player_name": "Garrett Wilson",
      "position": "WR",
      "status": "illustrative_unverified_roster_context",
      "jersey_number": null,
      "roster_role": null,
      "acquired_via": null,
      "transaction_context": null,
      "source_refs": [
        {
          "source_name": "docs_only_illustrative_example",
          "source_url": null,
          "observed_at": "2026-05-08T00:00:00Z",
          "source_updated_at": null,
          "confidence": "illustrative_not_verified",
          "notes": "Documentation example only; not promoted roster truth."
        }
      ],
      "valid_from": null,
      "valid_to": null
    },
    {
      "player_id": null,
      "player_name": "Geno Smith",
      "position": "QB",
      "status": "illustrative_unverified_roster_context",
      "jersey_number": null,
      "roster_role": null,
      "acquired_via": null,
      "transaction_context": null,
      "source_refs": [
        {
          "source_name": "docs_only_illustrative_example",
          "source_url": null,
          "observed_at": "2026-05-08T00:00:00Z",
          "source_updated_at": null,
          "confidence": "illustrative_not_verified",
          "notes": "Documentation example only; not promoted roster truth."
        }
      ],
      "valid_from": null,
      "valid_to": null
    },
    {
      "player_id": null,
      "player_name": "T'Vondre Sweat",
      "position": "DT",
      "status": "illustrative_unverified_roster_context",
      "jersey_number": null,
      "roster_role": null,
      "acquired_via": null,
      "transaction_context": null,
      "source_refs": [
        {
          "source_name": "docs_only_illustrative_example",
          "source_url": null,
          "observed_at": "2026-05-08T00:00:00Z",
          "source_updated_at": null,
          "confidence": "illustrative_not_verified",
          "notes": "Documentation example only; not promoted roster truth."
        }
      ],
      "valid_from": null,
      "valid_to": null
    },
    {
      "player_id": null,
      "player_name": "Sauce Gardner",
      "position": "CB",
      "status": "illustrative_unverified_departed_context",
      "jersey_number": null,
      "roster_role": null,
      "acquired_via": null,
      "transaction_context": {
        "transaction_id": null,
        "transaction_type": "departed_context_example",
        "transaction_date": null,
        "source_statement": "Illustrates how a departed-context row would remain source-linked if real sources existed.",
        "related_team_id": null,
        "related_team_abbr": null,
        "notes": "Not a verified transaction claim."
      },
      "source_refs": [
        {
          "source_name": "docs_only_illustrative_example",
          "source_url": null,
          "observed_at": "2026-05-08T00:00:00Z",
          "source_updated_at": null,
          "confidence": "illustrative_not_verified",
          "notes": "Documentation example only; not promoted departure truth."
        }
      ],
      "valid_from": null,
      "valid_to": null
    },
    {
      "player_id": null,
      "player_name": "Quinnen Williams",
      "position": "DT",
      "status": "illustrative_unverified_departed_context",
      "jersey_number": null,
      "roster_role": null,
      "acquired_via": null,
      "transaction_context": {
        "transaction_id": null,
        "transaction_type": "departed_context_example",
        "transaction_date": null,
        "source_statement": "Illustrates how a departed-context row would remain source-linked if real sources existed.",
        "related_team_id": null,
        "related_team_abbr": null,
        "notes": "Not a verified transaction claim."
      },
      "source_refs": [
        {
          "source_name": "docs_only_illustrative_example",
          "source_url": null,
          "observed_at": "2026-05-08T00:00:00Z",
          "source_updated_at": null,
          "confidence": "illustrative_not_verified",
          "notes": "Documentation example only; not promoted departure truth."
        }
      ],
      "valid_from": null,
      "valid_to": null
    }
  ]
}
```

## Out of scope for v0

- live ingestion
- source arbitration between competing feeds
- fantasy projections or valuation
- Teamstate scoring or meaning-making
- inferred depth charts
- inferred starter/back-up labels unless directly sourced as roster metadata
- full NFL roster coverage guarantees
- historical roster backfills
- downstream repository changes
