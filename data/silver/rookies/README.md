# Rookie silver data (processed/support)

This directory stores **processed rookie artifacts** centralized from `Prometheus-Frameworks/TIBER-Rookies`.

## Scope

- Layer: `silver`
- Ownership: durable reusable intermediate rookie datasets
- Typical content: cleaned joins, enriched feature tables, and processing-stage support artifacts

## Ingestion rules

All files in this directory must comply with the [fail-closed ingestion rules](../../docs/data/rookies-data-centralization.md#ingestion-rules-fail-closed).

- Only place artifacts that were **directly read from TIBER-Rookies** at import time.
- Every artifact must have a corresponding row in `data/rookies_manifest.csv` with `source_path`, `verified` status, and `sha256` (if verified).
- If source access fails during import, do not create data files. Instead, create an `IMPORT_BLOCKED.md` in the target season subdirectory. See blocked import protocol in the centralization doc.

## What does NOT belong here

- Synthetic or placeholder data with realistic-looking values
- App presentation or UI files
- Model logic or scoring code
- Files without a manifest entry
