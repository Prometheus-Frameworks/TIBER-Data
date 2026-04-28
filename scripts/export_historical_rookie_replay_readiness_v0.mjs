#!/usr/bin/env node

import {
  HISTORICAL_ROOKIE_REPLAY_READINESS_V0_ARTIFACT_PATH,
  writeHistoricalRookieReplayReadinessV0Artifact,
} from '../dist/src/export/historicalRookieReplayReadinessArtifact.js';

try {
  const output = writeHistoricalRookieReplayReadinessV0Artifact(HISTORICAL_ROOKIE_REPLAY_READINESS_V0_ARTIFACT_PATH);
  console.log(`Wrote Historical Rookie Replay readiness v0 artifact: ${output}`);
} catch (error) {
  console.error('Failed to export Historical Rookie Replay readiness v0 artifact.');
  console.error(error);
  process.exit(1);
}
