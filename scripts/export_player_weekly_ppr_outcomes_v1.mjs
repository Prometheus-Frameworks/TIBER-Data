#!/usr/bin/env node

import {
  PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH,
  writePlayerWeeklyPprOutcomesV1Artifact,
} from '../dist/src/export/playerWeeklyPprOutcomesArtifact.js';

try {
  const output = writePlayerWeeklyPprOutcomesV1Artifact(PLAYER_WEEKLY_PPR_OUTCOMES_V1_ARTIFACT_PATH);
  console.log(`Wrote Evidence Layer player weekly PPR outcomes artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Evidence Layer player weekly PPR outcomes artifact.');
  console.error(error);
  process.exit(1);
}
