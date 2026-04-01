# TIBER Team State v0.1

## Architecture decision (first step)

This module lives in **TIBER-Data** because it is an upstream, reusable football context producer, not a product/UI concern. It generates a stable offensive team-state artifact that downstream systems (including TIBER-Fantasy) should consume through thin adapters/read-only routes.

- Home: `team-state/` docs/contracts/scripts + `src/team_state/` compute module.
- Consumer boundary: downstream systems read `tiber_team_state_v0_1` artifact; they do not re-implement feature math.
- Deferred intentionally: defensive mirror, opponent-adjusted features, player-level layers, scenario simulation, UI surfaces.

## Runbook

Generate full season:

```bash
python team-state/scripts/generate_tiber_team_state_v0_1.py --season 2025
```

Generate through week:

```bash
python team-state/scripts/generate_tiber_team_state_v0_1.py --season 2025 --through-week 9
```

Deterministic local/CI run with fixture file:

```bash
python team-state/scripts/generate_tiber_team_state_v0_1.py \
  --season 2025 \
  --through-week 1 \
  --pbp-path team-state/fixtures/pbp_fixture.json \
  --output team-state/artifacts/tiber_team_state_v0_1.sample.json
```

## Artifact contract

- Name: `tiber_team_state_v0_1`
- Contract file: `team-state/contracts/tiber_team_state_v0_1.schema.json`
- Output path default: `team-state/artifacts/tiber_team_state_v0_1.json`

## Failure behavior

- Missing required PBP columns => hard failure with explicit column list.
- Empty qualifying offense play universe => no crash; emits valid artifact with empty `teams` and explanatory source note.
- Missing pace timing fields => no crash; `paceSecondsPerPlay` is omitted (`null`) and noted in team stability notes.

## Definitions

See `team-state/definitions/metric_definitions.md`.
