# FORGE 2025 PPR cohort artifact

## Output

`data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json` is a source-backed
cohort proof for handing a bounded 2025 weekly PPR player set to TIBER-FORGE.
It scales the one-player Ja'Marr Chase proof without adding fixture, sample,
offline, representative, or invented rows.

## Source input file

The builder reads existing TIBER-Data source-backed evidence:

- Player-week stats: `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json`
- Roster names: `data/processed/evidence/roster_player_team_map_2025.source_backed.json`

The player-week source identifies `nflreadpy.load_player_stats` as provenance and
`nflverse player stats via nflreadpy` as the source path label. The cohort builder
copies provider, file, path, provenance, `asOf`, `sourceUpdatedAt`, and `buildId`
metadata into the artifact and each weekly row.

## Scoring formula

Weekly PPR points are recomputed from source stats with:

```text
receptions
+ receivingYards / 10
+ receivingTDs * 6
+ rushingYards / 10
+ rushingTDs * 6
+ passingYards / 25
+ passingTDs * 4
- interceptions * 2
- fumblesLost * 2
```

Null numeric fields are treated as zero for scoring only. Nullable fields remain
explicitly nullable in the artifact, including `gameId` and `fumblesLost`.
Points are rounded to two decimals with Python `round(..., 2)`.

## Cohort selection logic

The builder first resolves the requested high-signal players by nflverse player
ID from source-backed 2025 regular-season rows:

- Ja'Marr Chase
- Josh Allen
- Bijan Robinson
- Brock Bowers
- Amon-Ra St. Brown
- Christian McCaffrey
- Tyreek Hill
- Jameson Williams
- Mike Evans
- Mark Andrews

If any requested player has no source-backed 2025 regular-season QB/RB/WR/TE row,
the build fails clearly. After requested players resolve, the builder fills the
cohort by descending regular-season PPR points among available QB/RB/WR/TE players
until reaching the maximum cohort size of 50. The minimum valid cohort size is 20.

Only existing weeks are emitted. Bye weeks, injuries, missing games, and non-played
weeks are not fabricated.

## Artifact shape

Top-level fields include:

- `artifactId`, `schemaVersion`, `artifactType`
- `season`, `regularSeasonWeeks`, `playerCount`
- `scoringFormat`, `scoringFormula`
- top-level `source`
- `asOf`, `sourceUpdatedAt`, `buildId`
- `cohortSelection`
- `players[]`

Each player contains identity fields, player-level source metadata, a `seasonTotal`
block, and `weeklyRows[]`. Each weekly row contains week/opponent context, nullable
`gameId`, passing/rushing/receiving/fumble fields, recomputed `pprPoints`, and row-level
source metadata.

## Known limitations

- The artifact is bounded to the existing 2025 regular-season source rows in
  TIBER-Data (`weeks 1-18`).
- `gameId` is currently nullable because the source-backed player-week evidence does
  not always provide a game identifier.
- `fumblesLost` remains nullable where the source evidence does not provide the field.
- Player names come from the roster source when available; otherwise the source-stat
  name is used.
- This artifact is proof/handoff data only. It does not define FORGE model behavior,
  scoring tweaks, UI behavior, or product policy.

## Handoff path to TIBER-FORGE

Use this governed handoff artifact:

```text
data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json
```

Downstream FORGE consumers should treat it as a source-backed cohort proof and should
not infer unsupported weeks, players, game IDs, or fumble values beyond what is present
in the artifact.
