# TIBER-Data

TIBER-Data is the shared football data foundation for downstream TIBER model repositories. PR1 intentionally focuses on dependable data contracts and a reproducible ETL backbone instead of advanced modeling, serving infrastructure, or historical backfill.

## Why this repo exists

Downstream role, opportunity, projection, and ranking models need one deterministic place to pull curated football tables from. This repository establishes that backbone with three explicit layers:

- **raw**: minimally touched source pulls written to disk for auditability.
- **silver**: normalized canonical tables with stable column contracts.
- **gold**: first-pass model-ready tables derived from silver tables.

That layered split keeps ingestion logic, normalization logic, and model-ready derivations from collapsing into one pile of sludge.

## Project layout

```text
data/
  raw/
  silver/
  gold/
docs/
  schemas/
scripts/
src/
  config/
  ingest/
  transform/
  derive/
  utils/
```

## PR1 scope

Included in this bootstrap:

- Python ETL scaffold using `polars`, `pyarrow`, and `nflreadpy`.
- Canonical schema docs for the first foundational tables.
- Public-data ingest entrypoints for players, teams, and weekly stats.
- Silver tables for players, weekly player stats, and weekly team stats.
- Gold tables for player role inputs and team context.
- Lightweight validation checks for required columns, duplicate keys, and non-negative numeric metrics.
- One command entrypoint to run the pipeline end to end.

Explicitly out of scope for PR1:

- web/API layers
- databases or warehouse infrastructure
- cloud deployment
- auth
- ML/model training
- expansive historical backfill beyond configured seasons
- fabricated tracking-grade metrics where public data is not yet cleanly available

## Installation

Create a Python 3.10+ environment and install the package with dependencies:

```bash
python -m pip install -e .
```

> `nflreadpy` is configured as the first-choice public data access layer. The ingest client also includes an offline fallback path so the repository structure and transforms stay testable in restricted environments.

## Run the pipeline

```bash
python -m src.main
```

Optional flags:

```bash
python -m src.main --season 2024 --overwrite
python -m src.main --seasons 2023 2024
```

The pipeline will:

1. ingest source data into `data/raw/`
2. normalize canonical parquet tables into `data/silver/`
3. derive first-pass gold tables into `data/gold/`
4. validate schema and basic quality constraints before succeeding

## Tables produced

### Silver

- `data/silver/players.parquet`
- `data/silver/teams.parquet`
- `data/silver/weekly_player_stats.parquet`
- `data/silver/weekly_team_stats.parquet`

### Gold

- `data/gold/player_role_inputs_weekly.parquet`
- `data/gold/team_context_weekly.parquet`

## Schema philosophy

The docs and code use three tiers when discussing fields:

- `required_now`
- `derived_now_if_available`
- `future_optional`

That prevents the repo from pretending it already has routes, tracking, air-yards, or participation data if those fields are not cleanly available from the current public ingest path.

## Notes on current public ingest

The ingest module tries to read public data through `nflreadpy` first. If that library is unavailable or the environment cannot reach public endpoints, the client can fall back to deterministic sample fixtures for local development. Those fixtures are deliberately limited and exist to preserve pipeline shape and validation behavior in offline CI; they are **not** a substitute for the intended public ingest path.
