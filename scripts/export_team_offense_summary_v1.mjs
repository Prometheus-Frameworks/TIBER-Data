#!/usr/bin/env node

import {
  TEAM_OFFENSE_SUMMARY_V1_ARTIFACT_PATH,
  writeTeamOffenseSummaryV1Artifact,
} from '../dist/src/export/teamOffenseSummaryArtifact.js';

try {
  const output = writeTeamOffenseSummaryV1Artifact(TEAM_OFFENSE_SUMMARY_V1_ARTIFACT_PATH);
  console.log(`Wrote Evidence Layer team offense summary artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Evidence Layer team offense summary artifact.');
  console.error(error);
  process.exit(1);
}
