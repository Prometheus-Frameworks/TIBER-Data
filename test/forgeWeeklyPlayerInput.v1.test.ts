import { describe, expect, it } from 'vitest';

import {
  forgeWeeklyPlayerInputArraySchema,
  forgeWeeklyPlayerInputSchema,
  forgeWeeklyQbExample,
  forgeWeeklyRbExample,
  forgeWeeklyWrExample,
  isForgeWeeklyPlayerInput,
  mixedForgeWeeklyExamples,
  validateForgeWeeklyPlayerInput,
  validateForgeWeeklyPlayerInputArray,
} from '../src/index.js';

describe('forge weekly player input contract v1', () => {
  it('valid WR fixture passes schema validation', () => {
    expect(validateForgeWeeklyPlayerInput(forgeWeeklyWrExample)).toEqual(forgeWeeklyWrExample);
  });

  it('valid RB fixture passes schema validation', () => {
    expect(validateForgeWeeklyPlayerInput(forgeWeeklyRbExample)).toEqual(forgeWeeklyRbExample);
  });

  it('valid QB fixture passes schema validation', () => {
    expect(validateForgeWeeklyPlayerInput(forgeWeeklyQbExample)).toEqual(forgeWeeklyQbExample);
  });

  it('mixed array fixture passes array validation', () => {
    expect(validateForgeWeeklyPlayerInputArray(mixedForgeWeeklyExamples)).toEqual(
      mixedForgeWeeklyExamples,
    );
  });

  it('invalid position enum fails', () => {
    expect(() =>
      forgeWeeklyPlayerInputSchema.parse({
        ...forgeWeeklyWrExample,
        position: 'FB',
      }),
    ).toThrow();
  });

  it('invalid share range fails', () => {
    expect(() =>
      forgeWeeklyPlayerInputSchema.parse({
        ...forgeWeeklyRbExample,
        featureCoverage: 1.2,
      }),
    ).toThrow();
  });

  it('negative count fails', () => {
    expect(() =>
      forgeWeeklyPlayerInputSchema.parse({
        ...forgeWeeklyQbExample,
        rushAttempts: -1,
      }),
    ).toThrow();
  });

  it('array and type guard remain directly usable', () => {
    expect(isForgeWeeklyPlayerInput(forgeWeeklyWrExample)).toBe(true);
    expect(forgeWeeklyPlayerInputArraySchema.safeParse(mixedForgeWeeklyExamples).success).toBe(true);
  });
});
