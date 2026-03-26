## Rookie data import checklist

Use this template for any PR that adds, updates, or removes rookie data artifacts in `data/raw/rookies/`, `data/silver/rookies/`, or `data/gold/rookies/`.

### Source verification

- [ ] All imported artifacts were **directly read** from TIBER-Rookies (not synthesized, inferred, or approximated)
- [ ] Source repository was accessible at import time
- [ ] If source access failed: created `IMPORT_BLOCKED.md` instead of data files

### Provenance

- [ ] Every imported file has a row in `data/rookies_manifest.csv`
- [ ] Each manifest row includes: `artifact_path`, `source_repo`, `source_path`, `season`, `purpose`, `classification`, `role`, `verified`, `imported_at_utc`
- [ ] Verified artifacts have `sha256` hashes recorded
- [ ] Gold-layer artifacts have `verified: true`

### Validation

- [ ] Ran `python scripts/validate_rookie_inventory.py` and it passed

### Coverage honesty

- [ ] Which seasons were actually imported? <!-- list them -->
- [ ] Which seasons or artifacts were NOT imported? <!-- list them or say "none expected" -->
- [ ] Does the PR description honestly state what was and was not imported?

### Boundary check

- [ ] No model logic, scoring code, or UI/prototype files were copied
- [ ] No synthetic or placeholder data with realistic-looking values was created
- [ ] PR scope is limited to data import (no unrelated changes)
