# Rookie data centralization boundary

## Why rookie data lives in TIBER-Data

TIBER-Data is the durable canonical storage layer for reusable rookie data artifacts.

- `TIBER-Rookies` computes rookie model outputs, experiments, and iterates in lab.
- `TIBER-Data` stores and serves reusable rookie datasets for downstream consumers.

This keeps model-lab evolution decoupled from cross-repo data contracts.

## Canonical rookie data area

Rookie artifacts are centralized in the existing raw/silver/gold hierarchy:

- `data/raw/rookies/` for authoritative rookie inputs and raw support payloads
- `data/silver/rookies/` for processed reusable rookie support artifacts
- `data/gold/rookies/` for promoted downstream-consumption rookie outputs
- `data/rookies_manifest.csv` as the provenance and inventory index

## Ownership boundary

### TIBER-Rookies owns

- rookie modeling logic
- experiments and lab notebooks/components
- prototype UX/presentation surfaces
- artifact production workflows

### TIBER-Data owns

- durable storage of reusable rookie data artifacts
- provenance metadata for imported rookie artifacts
- canonical downstream-facing rookie dataset snapshots
- ingestion validation and verification

## Ingestion rules (fail-closed)

These rules govern how rookie artifacts enter TIBER-Data. They are designed to prevent fabricated or unverifiable data from reaching canonical storage.

### Rule 1: Source-verified imports only

Only copy artifacts that are **directly readable from TIBER-Rookies** at import time. Every imported file must have a traceable source path in the source repository.

If source access fails (network error, permissions, repo unavailable), **do not**:
- create mirrored player-level files (CSV, JSON, parquet)
- populate the manifest with rows referencing inaccessible sources
- generate season inventories implying successful import
- synthesize realistic-looking data values as placeholders

Instead, create a single `IMPORT_BLOCKED.md` in the target season directory. See "Blocked import protocol" below.

### Rule 2: No synthetic rookie data

No invented player rows. No inferred season files. No placeholder rookie artifacts with realistic-looking values. No "example" data in canonical storage areas.

If you need test fixtures, place them in `fixtures/rookies/` with obviously synthetic values (e.g., `player_id: "test-fixture-001"`, `forty_yard_dash: 99.99`). Fixture data must never appear in `data/raw/`, `data/silver/`, or `data/gold/`.

### Rule 3: Manifest-before-merge

Every artifact in `data/raw/rookies/`, `data/silver/rookies/`, or `data/gold/rookies/` must have a corresponding row in `data/rookies_manifest.csv` before the PR merges. The `verified` field must be populated. Unverified artifacts must not appear in `data/gold/rookies/`.

### Rule 4: Hash-on-import

Every verified artifact must have a `sha256` hash recorded in the manifest at import time. This enables downstream consumers to confirm file integrity without re-accessing the source.

## Blocked import protocol

When a rookie data import cannot complete because the source is unavailable, create this file instead of fabricating data:

```
data/raw/rookies/{season}/IMPORT_BLOCKED.md
```

Contents:

```markdown
# Import blocked

- **Requested source**: TIBER-Rookies (specific path or artifact list)
- **Failure reason**: [e.g., HTTP 403, repo not accessible, network restricted]
- **Timestamp**: [ISO 8601]
- **Attempted by**: [agent or human identifier]
- **Required follow-up**: Manual import once source access is restored
```

This is the only acceptable output when source access fails. It preserves an honest record of the attempt without polluting canonical storage.

## Manifest schema

The manifest at `data/rookies_manifest.csv` uses these required fields:

| Field | Required | Description |
|---|---|---|
| `artifact_path` | yes | Relative path from repo root to the artifact file |
| `source_repo` | yes | Source repository (e.g., `TIBER-Rookies`) |
| `source_path` | yes | Path within source repo where the artifact was read |
| `season` | yes | NFL season year |
| `purpose` | yes | Brief description of what the artifact contains |
| `classification` | yes | One of: `raw`, `processed`, `promoted` |
| `role` | yes | One of: `authoritative_input`, `support_data`, `downstream_handoff_output` |
| `verified` | yes | `true` if source was directly read and hash recorded; `false` otherwise |
| `sha256` | yes if verified | SHA-256 hash of the artifact file at import time |
| `imported_at_utc` | yes | ISO 8601 timestamp of import |
| `notes` | no | Optional context |

**Downstream consumers should only trust rows where `verified` is `true`.**

Gold-layer artifacts (`data/gold/rookies/`) must have `verified: true`. No exceptions.

## Validation

Run `python scripts/validate_rookie_inventory.py` before merging any rookie-data PR. The validator checks:

- every manifest row points to a real file
- every file in rookie data directories has a matching manifest row
- verified rows have a sha256 hash
- gold-layer artifacts are verified
- no file exists in rookie storage without a manifest entry

## Artifact flow

1. Rookie logic evolves in `TIBER-Rookies`.
2. When reusable artifacts are ready, they are imported into TIBER-Data by directly reading from the source repo.
3. Each imported artifact is registered in `data/rookies_manifest.csv` with full provenance.
4. The validator script confirms integrity.
5. Downstream repositories retrieve from TIBER-Data `data/gold/rookies/` (verified only).

## Current coverage status (honest inventory)

As of **2026-03-26**, the canonical rookie storage zone, ingestion rules, and validation tooling are in place.

No rookie artifacts have been imported yet. The `data/raw/rookies/`, `data/silver/rookies/`, and `data/gold/rookies/` directories are empty. The manifest contains only the header row.

Historic rookie data has not been centralized. When historic artifacts are imported, they will follow the same ingestion rules and manifest requirements as current-season data.
