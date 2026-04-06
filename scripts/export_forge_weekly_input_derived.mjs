#!/usr/bin/env node

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  writeForgeWeeklyDerivedArtifact,
} from '../dist/src/export/forgeWeeklyDerivedArtifact.js';

try {
  const output = writeForgeWeeklyDerivedArtifact(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH);
  console.log(`Wrote derived ForgeWeeklyPlayerInput artifact: ${output}`);
} catch (error) {
  console.error('Failed to export derived ForgeWeeklyPlayerInput artifact from raw repo-held sources.');
  console.error(error);
  process.exit(1);
}
