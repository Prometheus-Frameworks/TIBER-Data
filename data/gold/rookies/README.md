# Rookie gold data (promoted handoff outputs)

This directory stores **promoted rookie artifacts** intended for downstream consumption.

## Scope

- Layer: `gold`
- Ownership: canonical downstream-consumption snapshots for reusable rookie datasets
- Typical content: promoted exports and contract-ready outputs

## Verification requirement

Gold-layer rookie artifacts carry the strictest trust requirement.

**Every file in this directory must have `verified: true` and a valid `sha256` hash in `data/rookies_manifest.csv`.** No exceptions. Downstream consumers are directed to read from this directory as the canonical retrieval point. Unverified data must not appear here.

## Ingestion rules

All files in this directory must comply with the [fail-closed ingestion rules](../../docs/data/rookies-data-centralization.md#ingestion-rules-fail-closed).

- Only place artifacts that were **directly read from TIBER-Rookies** and verified at import time.
- Every artifact must have a corresponding row in `data/rookies_manifest.csv` with `source_path`, `verified: true`, and `sha256`.
- If source access fails during import, do not create data files. Instead, create an `IMPORT_BLOCKED.md` in the target season subdirectory. See blocked import protocol in the centralization doc.

## What does NOT belong here

- Unverified artifacts (use `data/raw/rookies/` until verification is complete)
- Synthetic or placeholder data with realistic-looking values
- UI/prototype assets from TIBER-Rookies
- Model logic or scoring code
- Files without a manifest entry
