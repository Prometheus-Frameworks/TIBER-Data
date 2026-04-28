#!/usr/bin/env node

import {
  TEAM_PACE_PASS_ENVIRONMENT_V1_ARTIFACT_PATH,
  writeTeamPacePassEnvironmentV1Artifact,
} from '../dist/src/export/teamPacePassEnvironmentArtifact.js';

try {
  const output = writeTeamPacePassEnvironmentV1Artifact(TEAM_PACE_PASS_ENVIRONMENT_V1_ARTIFACT_PATH);
  console.log(`Wrote Evidence Layer team pace/pass environment artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Evidence Layer team pace/pass environment artifact.');
  console.error(error);
  process.exit(1);
}
