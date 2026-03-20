import { z } from 'zod';

export const positionSchema = z.enum(['QB', 'RB', 'WR', 'TE']);

export const primaryRoleSchema = z.enum([
  'workhorse_rb',
  'committee_rb',
  'pass_down_rb',
  'goal_line_rb',
  'perimeter_wr',
  'slot_wr',
  'flanker_wr',
  'move_te',
  'inline_te',
  'dual_threat_qb',
  'pocket_qb',
  'unknown',
]);

export const confidenceTierSchema = z.enum(['low', 'medium', 'high']);

export type Position = z.infer<typeof positionSchema>;
export type PrimaryRole = z.infer<typeof primaryRoleSchema>;
export type ConfidenceTier = z.infer<typeof confidenceTierSchema>;
