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

---

## Follow-up (less fake-flat stability/confidence inputs)
- Previously flat in committed skill artifacts: `roleVolatility` (`0.5`), `featureCoverage` (`0.71`), and mostly identical row `qualityFlags`.
- Now derived per row from existing repo fixture support only:
  - `roleVolatility`: week-to-week opportunity-share + role-mix deltas when history exists; neutral `0.5` only when history is unavailable.
  - `featureCoverage`: conservative weighted coverage based on direct support vs approximation/default usage in each row.
  - `qualityFlags`: row-specific route semantics (QB unavailable vs non-QB approximated) and volatility derivation vs fallback.
- Still deferred (unchanged): neutral default matchup/spread context and realized-week `activeProjection = 1` until richer upstream context exists.
