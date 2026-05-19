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
