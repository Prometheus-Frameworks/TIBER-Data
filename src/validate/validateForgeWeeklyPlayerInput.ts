import type {
  ForgeWeeklyPlayerInput,
  ForgeWeeklyPlayerInputArray,
} from '../contracts/v1/forgeWeeklyPlayerInput.js';
import {
  forgeWeeklyPlayerInputArraySchema,
  forgeWeeklyPlayerInputSchema,
} from '../contracts/v1/forgeWeeklyPlayerInput.js';

export function validateForgeWeeklyPlayerInput(input: unknown): ForgeWeeklyPlayerInput {
  return forgeWeeklyPlayerInputSchema.parse(input);
}

export function validateForgeWeeklyPlayerInputArray(input: unknown): ForgeWeeklyPlayerInputArray {
  return forgeWeeklyPlayerInputArraySchema.parse(input);
}

export function isForgeWeeklyPlayerInput(input: unknown): input is ForgeWeeklyPlayerInput {
  return forgeWeeklyPlayerInputSchema.safeParse(input).success;
}
