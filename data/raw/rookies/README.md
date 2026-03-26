# Rookie raw data (authoritative inputs)

This directory stores **raw rookie inputs** centralized from `Prometheus-Frameworks/TIBER-Rookies`.

## Scope

- Layer: `raw`
- Ownership in this repo: durable canonical storage of reusable rookie input artifacts
- Typical content: source extracts, provider payload snapshots, and support files used before feature processing

## Artifact requirements

Every artifact placed here must have matching metadata in `data/rookies_manifest.csv` with:

- source repository (`TIBER-Rookies`)
- season
- artifact purpose
- classification (`raw`)
- role (`authoritative_input` or `support_data`)
- import date

Do not place UI/prototype assets in this directory.
