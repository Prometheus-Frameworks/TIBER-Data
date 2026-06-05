import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  POINT_PREDICTION_SCENARIO_EXPORT_CONTRACT_VERSION,
  POINT_PREDICTION_SCENARIO_EXPORT_PROMOTED_FIXTURE_PATH,
  pointPredictionScenarioExportSchema,
  pointPredictionScenarioRowSchema,
  validatePointPredictionScenarioExport,
} from '../src/index.js';

function loadFixture(): unknown {
  return JSON.parse(
    readFileSync(path.resolve(POINT_PREDICTION_SCENARIO_EXPORT_PROMOTED_FIXTURE_PATH), 'utf-8'),
  );
}

describe('point-prediction scenario export contract v1', () => {
  it('validates the committed promoted-shape fixture', () => {
    const artifact = validatePointPredictionScenarioExport(loadFixture());

    expect(artifact.contract_version).toBe(POINT_PREDICTION_SCENARIO_EXPORT_CONTRACT_VERSION);
    expect(artifact.artifact_status).toBe('fixture_only');
    expect(artifact.provenance.tiber_data_contract_owner).toBe('TIBER-Data');
    expect(artifact.provenance.source_repo).toBe('Point-prediction-model');
    expect(artifact.rows).toHaveLength(2);
  });

  it('requires the pinned contract version', () => {
    const artifact = validatePointPredictionScenarioExport(loadFixture());

    expect(() =>
      pointPredictionScenarioExportSchema.parse({
        ...artifact,
        contract_version: 'point-prediction-model.local-shape.v1',
      }),
    ).toThrow();
  });

  it('fails loudly when producer drift adds or renames fields', () => {
    const artifact = validatePointPredictionScenarioExport(loadFixture());
    const { scenario_id: _scenarioId, ...missingScenarioId } = artifact;

    expect(() => pointPredictionScenarioExportSchema.parse(missingScenarioId)).toThrow();
    expect(() =>
      pointPredictionScenarioExportSchema.parse({
        ...artifact,
        scenarioLabel: artifact.scenario_name,
      }),
    ).toThrow();
  });

  it('requires core player identity, projection, confidence, and explanation fields', () => {
    const artifact = validatePointPredictionScenarioExport(loadFixture());
    const [row] = artifact.rows;

    expect(() => pointPredictionScenarioRowSchema.parse({ ...row, baseline_projection: undefined })).toThrow();
    expect(() => pointPredictionScenarioRowSchema.parse({ ...row, adjusted_projection: undefined })).toThrow();
    expect(() => pointPredictionScenarioRowSchema.parse({ ...row, confidence_score: undefined })).toThrow();
    expect(() => pointPredictionScenarioRowSchema.parse({ ...row, explanation: '' })).toThrow();
    expect(() =>
      pointPredictionScenarioRowSchema.parse({
        ...row,
        player: { player_name: row.player.player_name },
      }),
    ).toThrow();
  });

  it('keeps delta tied to adjusted_projection minus baseline_projection', () => {
    const artifact = validatePointPredictionScenarioExport(loadFixture());
    const [row] = artifact.rows;

    expect(() =>
      pointPredictionScenarioRowSchema.parse({
        ...row,
        delta: row.delta + 0.01,
      }),
    ).toThrow();
  });

  it('bounds confidence score to the 0..1 range', () => {
    const artifact = validatePointPredictionScenarioExport(loadFixture());
    const [row] = artifact.rows;

    expect(() => pointPredictionScenarioRowSchema.parse({ ...row, confidence_score: -0.01 })).toThrow();
    expect(() => pointPredictionScenarioRowSchema.parse({ ...row, confidence_score: 1.01 })).toThrow();
  });
});
