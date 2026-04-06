#!/usr/bin/env node

import {
  FORGE_WEEKLY_DERIVED_ARTIFACT_PATH,
  FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS,
  writeForgeWeeklyDerivedArtifact,
  writeForgeWeeklySkillDerivedArtifactsForWeeks,
} from '../dist/src/export/forgeWeeklyDerivedArtifact.js';

try {
  const qbOutput = writeForgeWeeklyDerivedArtifact(FORGE_WEEKLY_DERIVED_ARTIFACT_PATH);
  const skillOutputs = writeForgeWeeklySkillDerivedArtifactsForWeeks();
  console.log(`Wrote QB derived ForgeWeeklyPlayerInput artifact: ${qbOutput}`);
  console.log(
    `Wrote broader skill derived ForgeWeeklyPlayerInput artifacts for weeks ${FORGE_WEEKLY_DERIVED_SKILL_EXPORT_WEEKS.join(', ')}:`,
  );
  for (const outputPath of skillOutputs) {
    console.log(` - ${outputPath}`);
  }
} catch (error) {
  console.error('Failed to export derived ForgeWeeklyPlayerInput artifacts from raw repo-held sources.');
  console.error(error);
  process.exit(1);
}
