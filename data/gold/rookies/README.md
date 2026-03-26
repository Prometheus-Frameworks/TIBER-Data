# Rookie gold data (promoted handoff outputs)

This directory stores **promoted rookie artifacts** intended for downstream consumption.

## Scope

- Layer: `gold`
- Ownership in this repo: canonical downstream-consumption snapshots for reusable rookie datasets
- Typical content: promoted exports and contract-ready outputs

## Contract note

Gold rookie artifacts in TIBER-Data are canonical snapshots for downstream consumers. TIBER-Rookies remains the model/lab system that computes and iterates toward those outputs.

## Artifact requirements

Every artifact placed here must be listed in `data/rookies_manifest.csv` and include:

- source repository (`TIBER-Rookies`)
- season
- purpose
- classification (`promoted`)
- role (`consumer_handoff_output`)
- import date

Do not place UI/prototype assets in this directory.
