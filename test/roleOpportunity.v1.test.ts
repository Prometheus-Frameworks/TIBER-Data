import { describe, expect, it } from 'vitest';

import {
  qbExample,
  rbExample,
  roleOpportunityArraySchema,
  roleOpportunityRecordSchema,
  teExample,
  validateRoleOpportunityArray,
  validateRoleOpportunityRecord,
  wrExample,
  mixedRoleOpportunityExamples,
} from '../src/index.js';

describe('role-opportunity contract v1', () => {
  it('valid RB fixture passes schema validation', () => {
    expect(validateRoleOpportunityRecord(rbExample)).toEqual(rbExample);
  });

  it('valid WR fixture passes schema validation', () => {
    expect(validateRoleOpportunityRecord(wrExample)).toEqual(wrExample);
  });

  it('valid TE fixture passes schema validation', () => {
    expect(validateRoleOpportunityRecord(teExample)).toEqual(teExample);
  });

  it('valid QB fixture passes schema validation', () => {
    expect(validateRoleOpportunityRecord(qbExample)).toEqual(qbExample);
  });

  it('mixed array fixture passes array validation', () => {
    expect(validateRoleOpportunityArray(mixedRoleOpportunityExamples)).toEqual(
      mixedRoleOpportunityExamples,
    );
  });

  it('invalid share > 1 fails', () => {
    expect(() =>
      roleOpportunityRecordSchema.parse({
        ...rbExample,
        targetShare: 1.01,
      }),
    ).toThrow();
  });

  it('negative counts fail', () => {
    expect(() =>
      roleOpportunityRecordSchema.parse({
        ...rbExample,
        carries: -1,
      }),
    ).toThrow();
  });

  it('missing required identity field fails', () => {
    const { playerId, ...invalidRecord } = rbExample;
    expect(() => roleOpportunityRecordSchema.parse(invalidRecord)).toThrow();
    expect(playerId).toBeTruthy();
  });

  it('invalid enum value for position fails', () => {
    expect(() =>
      roleOpportunityRecordSchema.parse({
        ...wrExample,
        position: 'FB',
      }),
    ).toThrow();
  });

  it('confidence score outside 0..1 fails', () => {
    expect(() =>
      roleOpportunityRecordSchema.parse({
        ...teExample,
        confidence: {
          ...teExample.confidence,
          score: 1.2,
        },
      }),
    ).toThrow();
  });

  it('record and array schemas remain directly usable', () => {
    expect(roleOpportunityRecordSchema.safeParse(rbExample).success).toBe(true);
    expect(roleOpportunityArraySchema.safeParse(mixedRoleOpportunityExamples).success).toBe(true);
  });
});
