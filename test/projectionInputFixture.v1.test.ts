import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  projectionInputFixtureBundleSchema,
  validateProjectionInputFixtureBundle,
} from '../src/index.js';

const FIXTURE_PATH = 'data/projection-input-fixtures/weekly_projection_input_fixture_2026_w01.json';

function loadFixture(): unknown {
  return JSON.parse(readFileSync(path.resolve(FIXTURE_PATH), 'utf-8'));
}

describe('projection input fixture contract v1', () => {
  it('validates the committed bounded golden fixture', () => {
    const fixture = validateProjectionInputFixtureBundle(loadFixture());

    expect(fixture.input_contract_version).toBe('tiber-data.projection-input-fixture.v1.0.0');
    expect(fixture.fixture_scope.kind).toBe('bounded_rehearsal_fixture');
    expect(fixture.fixture_scope.production_coverage_claim).toBe(false);
    expect(fixture.projection_context.fixture_only).toBe(true);
    expect(fixture.projection_context.production_ingestion).toBe(false);
  });

  it('keeps missing fields visible with fixture-level warning severity', () => {
    const fixture = validateProjectionInputFixtureBundle(loadFixture());

    expect(fixture.missing_fields.length).toBeGreaterThan(0);
    expect(fixture.missing_fields.map((field) => field.severity)).toEqual(
      expect.arrayContaining(['warning']),
    );
    expect(fixture.missing_fields.every((field) => field.severity === 'warning')).toBe(true);
    expect(fixture.missing_fields.map((field) => field.field)).toEqual(
      expect.arrayContaining(['red_zone_targets_pg', 'goal_line_rush_attempts_pg']),
    );
  });

  it('treats projection context as bundle metadata rather than player scoring input', () => {
    const fixture = validateProjectionInputFixtureBundle(loadFixture());
    const player = fixture.player_opportunities[0];

    expect(fixture.projection_context.source_evidence_season).toBe(2025);
    expect(fixture.projection_context.season).toBe(2026);
    expect(player).not.toHaveProperty('projection_context');
    expect(player).not.toHaveProperty('source_evidence_season');
    expect(player).not.toHaveProperty('source_evidence_week');
  });

  it('requires source refs and identity refs', () => {
    const fixture = validateProjectionInputFixtureBundle(loadFixture());
    const withoutSourceRefs = { ...fixture, source_dataset_refs: undefined };
    const withoutIdentityRef = { ...fixture, identity_ref: undefined };

    expect(() => projectionInputFixtureBundleSchema.parse(withoutSourceRefs)).toThrow();
    expect(() => projectionInputFixtureBundleSchema.parse(withoutIdentityRef)).toThrow();
  });

  it('requires the fixture scope to deny production coverage claims', () => {
    const fixture = validateProjectionInputFixtureBundle(loadFixture());

    expect(() =>
      projectionInputFixtureBundleSchema.parse({
        ...fixture,
        fixture_scope: {
          ...fixture.fixture_scope,
          production_coverage_claim: true,
        },
      }),
    ).toThrow();
  });

  it('rejects null-filled unavailable player fields', () => {
    const fixture = validateProjectionInputFixtureBundle(loadFixture());

    expect(() =>
      projectionInputFixtureBundleSchema.parse({
        ...fixture,
        player_opportunities: [
          {
            ...fixture.player_opportunities[0],
            red_zone_targets_pg: null,
          },
          ...fixture.player_opportunities.slice(1),
        ],
      }),
    ).toThrow();
  });
});
