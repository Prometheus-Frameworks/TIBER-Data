#!/usr/bin/env node

import {
  HISTORICAL_ROOKIE_REPLAY_V0_ARTIFACT_PATH,
  writeHistoricalRookieReplayV0Artifact,
} from '../dist/src/export/historicalRookieReplayArtifact.js';

try {
  const output = writeHistoricalRookieReplayV0Artifact(HISTORICAL_ROOKIE_REPLAY_V0_ARTIFACT_PATH);
  console.log(`Wrote Historical Rookie Replay v0 artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Historical Rookie Replay v0 artifact.');
  console.error(error);
  process.exit(1);
}
