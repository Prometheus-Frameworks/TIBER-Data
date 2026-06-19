# Player interpretability UI audit — issue 160

## Summary

TIBER-Data already contains a small standalone Node HTTP UI in `web/server.mjs`. It is not a full application framework; it is a read-only evidence viewer served by `npm start` and backed by committed repository artifacts loaded at server start.

## Existing standalone UI surface

- Surface: `web/server.mjs`.
- Runtime: Node built-in `http` server, no React/Next/Vite UI app.
- Existing routes before this audit: `/`, `/health`, `/artifacts`, `/roster`, `/ppr`, `/goblin`, `/docs`, and `/system-flow`.
- Existing purpose: inspect committed evidence artifacts, source details, contracts, and research rows without mutating data.

## Best home for a minimal player interpretability page

The safest first home is the existing read-only evidence viewer as a narrow route, `/player-lab`, because it already:

- loads source-backed roster, box-score, usage, and research artifacts;
- exposes read-only artifact provenance;
- has a clear non-recommendation posture;
- keeps raw source rows visible; and
- avoids introducing a second UI stack before the product boundary is settled.

A later production UI can move to a separate TIBER app if this surface grows beyond evidence inspection and deterministic translation.

## Available local player data sources

The locally available 2025 player data sources are:

- `data/processed/evidence/roster_player_team_map_2025.source_backed.json` — player/team/position/week roster assignments.
- `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json` — weekly box-score receiving/rushing/passing fields.
- `data/processed/evidence/player_weekly_usage_2025.source_backed.json` — weekly targets, receptions, target share, air yards/share, and explicit nullable placeholders for unsupported usage fields such as routes, route participation, red-zone fields, and snap share.
- `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json` — computed PPR totals and rolling context.
- `data/processed/research/goblin_signal_candidates_2025.source_backed.json` — source-backed research candidate rows with deterministic flags, caveats, source artifacts, and no candidate score implementation.

## Boundary findings

- Receiver-friendly fields exist for targets, receptions, receiving yards, touchdowns, target share, air yards, and air-yards share.
- Route participation, snaps, and red-zone usage appear in usage/research artifacts as missing/null support fields; the UI must show them as missing rather than infer values.
- Existing GOBLIN candidate rows are research review signals, not fantasy advice, rankings, start/sit guidance, or lineup management.
- No new contract should be promoted for this MVP; the current evidence artifacts are sufficient for a read-only prototype.

## Scaffold added

A minimal `/player-lab` route was added to the existing evidence viewer. It provides:

- a player-name search biased to WR rows but not hardcoded to invented fixtures;
- a season stat card aggregated only from matched source-backed rows;
- one or more deterministic interpretation tags with visible trigger text;
- explicit missing-data tags when unsupported fields are absent;
- a raw/source-data JSON preview for the selected source rows.

## Follow-up implementation steps

1. Add focused tests around deterministic tag thresholds before expanding tag vocabulary.
2. Decide whether `/player-lab` remains an evidence-viewer route or graduates to a separate app surface.
3. If adding route, snap, or red-zone interpretation, first add source-backed artifacts for those fields instead of inferring them.
4. Gather user feedback on tag wording using the read-only page before adding any scoring or prediction layer.
