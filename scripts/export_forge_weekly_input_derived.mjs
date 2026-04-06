#!/usr/bin/env node

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH,
  writeForgeWeeklyDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifact,
} from '../dist/src/export/forgeWeeklyDerivedArtifact.js';

try {
  const qbOutput = writeForgeWeeklyDerivedArtifact(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH);
  const skillOutput = writeForgeWeeklySkillDerivedArtifact(FORGE_WEEKLY_DERIVED_SKILL_ARTIFACT_PATH);
  console.log(`Wrote QB derived ForgeWeeklyPlayerInput artifact: ${qbOutput}`);
  console.log(`Wrote broader skill derived ForgeWeeklyPlayerInput artifact: ${skillOutput}`);
} catch (error) {
  console.error('Failed to export derived ForgeWeeklyPlayerInput artifacts from raw repo-held sources.');
  console.error(error);
  process.exit(1);
}
