#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

import {
  POINT_PREDICTION_SCENARIO_EXPORT_PROMOTED_FIXTURE_PATH,
  validatePointPredictionScenarioExport,
} from '../src/contracts/v1/pointPredictionScenarioExport.ts';

const targetPath = process.argv[2] ?? POINT_PREDICTION_SCENARIO_EXPORT_PROMOTED_FIXTURE_PATH;
const resolvedPath = path.resolve(process.cwd(), targetPath);

try {
  const artifact = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'));
  const parsed = validatePointPredictionScenarioExport(artifact);

  console.log(
    `Validated ${targetPath} against ${parsed.contract_version} (${parsed.rows.length} row${
      parsed.rows.length === 1 ? '' : 's'
    }).`,
  );
} catch (error) {
  console.error(`Point-prediction scenario export contract conformance failed for ${targetPath}.`);
  console.error(error);
  process.exit(1);
}
