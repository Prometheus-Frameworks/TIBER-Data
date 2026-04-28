#!/usr/bin/env node

import {
  ROSTER_PLAYER_TEAM_MAP_V1_ARTIFACT_PATH,
  writeRosterPlayerTeamMapV1Artifact,
} from '../dist/src/export/rosterPlayerTeamMapArtifact.js';

try {
  const output = writeRosterPlayerTeamMapV1Artifact(ROSTER_PLAYER_TEAM_MAP_V1_ARTIFACT_PATH);
  console.log(`Wrote Evidence Layer roster player/team map artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Evidence Layer roster player/team map artifact.');
  console.error(error);
  process.exit(1);
}
