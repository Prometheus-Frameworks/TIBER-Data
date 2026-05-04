#!/usr/bin/env node

import {
  PLAYER_WEEKLY_PPR_OUTCOMES_V1_COMPUTED_SOURCE_BACKED_ARTIFACT_PATH,
  writePlayerWeeklyPprOutcomesV1Artifact,
} from '../dist/src/export/playerWeeklyPprOutcomesArtifact.js';

try {
  const output = writePlayerWeeklyPprOutcomesV1Artifact(
    PLAYER_WEEKLY_PPR_OUTCOMES_V1_COMPUTED_SOURCE_BACKED_ARTIFACT_PATH,
    { sourceKind: 'source_backed' },
  );
  console.log(`Wrote computed source-backed weekly PPR outcomes artifact: ${output}`);
} catch (error) {
  console.error('Failed to export computed source-backed weekly PPR outcomes artifact.');
  console.error(error);
  process.exit(1);
}
