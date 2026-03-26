# Rookie data centralization boundary

## Why rookie data now lives in TIBER-Data

TIBER-Data is the durable canonical storage layer for reusable rookie data artifacts.

- `TIBER-Rookies` computes rookie model outputs, experiments, and lab iteration.
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

### TIBER-Data owns

- durable storage of reusable rookie data artifacts
- provenance metadata for imported rookie artifacts
- canonical downstream-facing rookie dataset snapshots

## Artifact flow / sync note

Going forward:

1. Rookie logic evolves in `TIBER-Rookies`.
2. Approved reusable rookie artifacts are published into TIBER-Data raw/silver/gold rookie directories.
3. Every imported artifact is registered in `data/rookies_manifest.csv`.
4. Downstream repositories should prefer TIBER-Data for canonical reusable rookie datasets.

## Current coverage status (honest inventory)

As of **2026-03-26**, this PR establishes the canonical rookie storage zone and provenance manifest.

Historic/current rookie artifacts from `TIBER-Rookies` were not copied in this environment snapshot because the source repository contents were not available from this workspace at PR time. The manifest and directory structure are in place for immediate artifact ingestion once source access is available.
