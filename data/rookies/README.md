# Rookie data (canonical storage)

This directory is the canonical retrieval location for reusable rookie data artifacts in the TIBER ecosystem.

## Ownership boundary

- **TIBER-Rookies owns** rookie model logic, lab experimentation, and product/UI surfaces.
- **TIBER-Data owns** reusable rookie artifacts that should be retrieved by downstream repos.

If a downstream repo needs promoted rookie outputs or reusable rookie support/processed inputs, it should prefer this directory over pulling ad hoc snapshots from the rookie lab repository.

## Provenance rule

Every imported artifact in this tree must include:

- source repository (TIBER-Rookies)
- season
- artifact type (raw, processed, support, or promoted)
- artifact purpose
- role in pipeline (`authoritative_input`, `support_data`, or `downstream_handoff_output`)

See `data/rookies/artifact-index.json` for the machine-readable inventory.
