# TIBER Team State v0.1 metric definitions

- Scope: offense only, regular season only, one season per artifact.
- Play universe: offensive snaps where `posteam` is non-null and play is identified as rush/pass (`rush == 1` or `pass == 1` or play_type in `{run, pass}`).

## Metrics

1. **neutralPassRate**: pass plays / plays in neutral situation.
   - Neutral situation: quarter 1-3 and absolute score differential <= 8.
2. **earlyDownPassRate**: pass plays / early-down non-garbage plays.
   - Early down: down in {1,2}.
   - Garbage exclusion: quarter 4 and absolute score differential > 16 excluded.
3. **earlyDownSuccessRate**: successful early-down non-garbage plays / early-down non-garbage plays.
   - Success rule: >=40% yards-to-go on 1st down, >=60% on 2nd down, >=100% on 3rd/4th.
4. **redZonePassRate**: pass plays on snaps with `yardline_100 <= 20` / red-zone plays.
5. **redZoneTdEfficiency**: red-zone drives with offensive touchdown / drives that reached red zone.
6. **explosivePlayRate**: offensive plays with `yards_gained >= 16` / offensive plays.
7. **driveSustainRate**: drives with at least one first down / offensive drives.
8. **paceSecondsPerPlay**: median positive snap-to-snap delta seconds <= 45. Omitted if timing fields are unavailable.

## Stability metadata

- `sample.games`, `sample.plays`, `sample.drives`, and per-situation play counts are included.
- `sampleFlag=thin` if offense has <250 plays in sample; otherwise `ok`.
