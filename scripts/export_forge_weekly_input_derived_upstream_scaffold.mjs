#!/usr/bin/env node

import {
  FORGE_WEEKLY_UPSTREAM_SCAFFOLD_DERIVED_SKILL_EXPORT_WEEKS,
  writeForgeWeeklyUpstreamScaffoldSkillDerivedArtifactsForWeeks,
} from '../dist/src/export/forgeWeeklyDerivedArtifact.js';

try {
  const skillOutputs = writeForgeWeeklyUpstreamScaffoldSkillDerivedArtifactsForWeeks();
  console.log(
    `Wrote upstream scaffold skill derived ForgeWeeklyPlayerInput artifacts for weeks ${FORGE_WEEKLY_UPSTREAM_SCAFFOLD_DERIVED_SKILL_EXPORT_WEEKS.join(', ')}:`,
  );
  for (const outputPath of skillOutputs) {
    console.log(` - ${outputPath}`);
  }
} catch (error) {
  console.error('Failed to export upstream scaffold skill-derived ForgeWeeklyPlayerInput artifacts.');
  console.error(error);
  process.exit(1);
}
