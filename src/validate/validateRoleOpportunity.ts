import type { RoleOpportunityArray, RoleOpportunityRecord } from '../contracts/v1/roleOpportunity.js';
import {
  roleOpportunityArraySchema,
  roleOpportunityRecordSchema,
} from '../contracts/v1/roleOpportunity.js';

export function validateRoleOpportunityRecord(input: unknown): RoleOpportunityRecord {
  return roleOpportunityRecordSchema.parse(input);
}

export function validateRoleOpportunityArray(input: unknown): RoleOpportunityArray {
  return roleOpportunityArraySchema.parse(input);
}

export function isRoleOpportunityRecord(input: unknown): input is RoleOpportunityRecord {
  return roleOpportunityRecordSchema.safeParse(input).success;
}
