# FORGE derived_skill semantic cleanup (2024 week 6)

## What was wrong
- `practiceParticipation` and `opponentDefenseTier` used legacy labels (`not_listed`, `average`) that required downstream cleanup.
- `activeProjection` was tied to opportunity share, which made clearly active players look inactive.
- `roleVolatility` was tied to `1 - snapShare`, which overstated volatility for target-driven WR/TE rows.
- `qualityFlags` duplicated provenance entries when both sources shared the same label.
- Skill-slice route fields were hard-zeroed, which was overly lossy when target volume was present.

## What was fixed
- Normalized enum outputs to `practiceParticipation: "none"` and `opponentDefenseTier: "neutral"`.
- Set `activeProjection` to `1` for realized weekly records and defaulted `roleVolatility` to neutral midpoint (`0.5`) with explicit flags.
- De-duplicated `qualityFlags`.
- Added lightweight route approximations for non-QB skill rows using target volume vs team pass attempts.
- Added an explicit cap of `3.0` on `fantasyPointsPerOpportunity`.

## Deferred
- True snap/route participation and matchup/spread context still require richer upstream sources; this cleanup keeps placeholders honest without adding new feeds.
