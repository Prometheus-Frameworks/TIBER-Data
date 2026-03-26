# Rookie silver data (processed/support)

This directory stores **processed rookie artifacts** centralized from `Prometheus-Frameworks/TIBER-Rookies`.

## Scope

- Layer: `silver`
- Ownership in this repo: durable reusable intermediate rookie datasets
- Typical content: cleaned joins, enriched feature tables, and processing-stage support artifacts

## Artifact requirements

Every artifact placed here must be listed in `data/rookies_manifest.csv` and include provenance fields:

- source repository (`TIBER-Rookies`)
- season
- purpose
- classification (`processed`)
- role (`support_data`)
- import date

Do not place app presentation files in this directory.
