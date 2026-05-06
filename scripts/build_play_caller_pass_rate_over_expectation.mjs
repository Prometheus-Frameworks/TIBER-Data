#!/usr/bin/env node

const requiredInputFields = [
  'season',
  'week',
  'game_id',
  'posteam',
  'down',
  'ydstogo',
  'yardline_100',
  'pass',
  'xpass',
  'pass_oe',
];

const intendedFutureOutputPath =
  'data/processed/research/play_caller_pass_rate_over_expectation_v0.source_backed.json';

console.log(`Play-caller pass rate over expectation lane scaffold only.

This follow-up intentionally does not generate artifacts, fetch nflfastR/nflverse data, transcribe screenshot/reference values, or fabricate play-caller mappings.

Required future play-by-play input fields:
  ${requiredInputFields.join('\n  ')}

Intended future source-backed output path:
  ${intendedFutureOutputPath}

Research notes and scope boundaries are documented at:
  docs/data/play-caller-pass-rate-over-expectation.md

The lane remains blocked until both prerequisites are available:
  1. sourced play-caller mappings with documented validity windows and provenance;
  2. sourced expected-pass fields such as pass, xpass, and pass_oe from a governed nflverse/nflfastR-style extraction.

No data was fetched. No artifact was generated.`);
