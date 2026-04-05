#!/usr/bin/env node

import {
  FORGE_WEEKLY_SAMPLE_ARTIFACT_PATH,
  writeForgeWeeklySampleArtifact,
} from '../dist/src/export/forgeWeeklySampleArtifact.js';

try {
  const output = writeForgeWeeklySampleArtifact(FORGE_WEEKLY_SAMPLE_ARTIFACT_PATH);
  console.log(`Wrote canonical ForgeWeeklyPlayerInput sample artifact: ${output}`);
} catch (error) {
  console.error('Failed to export canonical ForgeWeeklyPlayerInput sample artifact.');
  console.error(error);
  process.exit(1);
}
