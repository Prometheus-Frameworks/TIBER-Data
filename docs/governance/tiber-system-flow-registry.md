# TIBER System Flow Registry (v1)

This document is the human companion to `contracts/tiber-system-flow-registry.v1.json`.

- Registry file: `contracts/tiber-system-flow-registry.v1.json`
- Source governance map: `docs/governance/tiber-system-flow-map.md`
- Scope: contract/registry foundation only (no runtime integrations)

## Notes

- The registry mirrors the current first-pass governance map; it does not expand approved topology.
- The rookie pathway is represented through `Rookies -> TIBER-Data -> TIBER-Fantasy`.
- Review-required and blocked directions are captured explicitly so agents/scripts do not infer unsafe loops.
- Global blocked rules capture provenance bypass and unreviewed upstream authority promotion.

## Repo boundary corrections

These align the registry's human description with actual repo boundaries (see `tiber-system-flow-map.md`):

- **Role & Opportunity is not a peer repository.** It is a module/sub-node inside TIBER-Fantasy (`server/modules/externalModels/roleOpportunity/`). Any role/usage interpretation flow originates from that TIBER-Fantasy sub-node, not from a standalone repo.
- **Age-curve-intelligence-model** is a real sibling repo and is represented as its own node in the flow map.
- The registry contract file (`contracts/tiber-system-flow-registry.v1.json`) still carries the older `producer_repo: "Role & Opportunity"` label. Correcting the contract JSON is a contract change and is intentionally out of scope for this docs-only update; it is flagged here as follow-up.
