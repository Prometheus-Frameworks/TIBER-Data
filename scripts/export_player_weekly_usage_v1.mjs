#!/usr/bin/env node

import {
  PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH,
  writePlayerWeeklyUsageV1Artifact,
} from '../dist/src/export/playerWeeklyUsageArtifact.js';

try {
  const output = writePlayerWeeklyUsageV1Artifact(PLAYER_WEEKLY_USAGE_V1_ARTIFACT_PATH);
  console.log(`Wrote Evidence Layer player weekly usage artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Evidence Layer player weekly usage artifact.');
  console.error(error);
  process.exit(1);
}
