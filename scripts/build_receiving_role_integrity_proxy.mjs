#!/usr/bin/env node

const requiredFutureInputFields = [
  'season',
  'week',
  'game_id',
  'player_id',
  'player_name',
  'team',
  'position',
  'offense_snaps',
  'snap_share',
  'pass_play_participation or a documented equivalent proxy denominator',
  'targets',
  'receptions',
  'receiving_yards',
];

const optionalContextFieldsToInvestigate = [
  'targeted_route_label or route on targeted-player rows only',
  'air_yards if sourced from joinable play-by-play or usage data',
  'team pass-play count denominator for participation-share auditing',
];

const intendedFutureOutputPath =
  'data/processed/research/receiving_role_integrity_proxy_v0.source_backed.json';

console.log(`Receiving Role Integrity / route participation proxy lane scaffold only.

This script intentionally does not fetch nflverse/nflreadpy data, generate artifacts, infer routes, or fabricate pass-play participation values.

Required future input fields:
  ${requiredFutureInputFields.join('\n  ')}

Optional context fields to investigate:
  ${optionalContextFieldsToInvestigate.join('\n  ')}

Intended future source-backed output path:
  ${intendedFutureOutputPath}

Research notes and scope boundaries are documented at:
  docs/data/receiving-role-integrity-route-participation-proxy.md

Contract boundary:
  TIBER-Data must not claim true routes run, true route share, true YPRR, or true TPRR unless the upstream source explicitly provides true route participation coverage for all relevant players.
  Pass-play participation proxies must be named as proxies and must remain distinct from true charted routes.

No data was fetched. No artifact was generated.`);
