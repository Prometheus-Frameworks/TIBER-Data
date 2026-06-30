"""Validator for the player_season_coverage_v0 candidate artifact.

Combines JSON Schema structural validation (schemas/player_season_coverage_v0.schema.json)
with business-rule checks required by TIBER-Data #190 / the spec in #188-#189:

- one row per approved grain (player_id + season + season_type), no duplicates,
- season_type explicit and valid on every row,
- zero and null/unavailable are distinct (a field present with value 0 is not the
  same as a field that is null/absent because the source did not report it),
- multi-team rows (teams with more than one entry) carry an explicit primary_team_rule,
- no row asserts active/inactive/IR/practice-squad availability status,
- source_refs exist and are machine-readable,
- fixture/scaffold sources are rejected if present in source_refs/source_name fields,
- missing age/career data remains unavailable (null), never fabricated as 0.

Usage: python scripts/validate_player_season_coverage_v0.py <path-to-artifact.json>
Exits non-zero (fail closed) on any violation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path("schemas/player_season_coverage_v0.schema.json")
FIXTURE_MARKERS = ("offline_fixture", "fixture_", "scaffold", "fixture_demonstration_only")
ACTIVE_STATUS_FORBIDDEN_KEYS = {"active_status", "ownership_status", "roster_status", "active_roster_status"}


class ValidationFailure(Exception):
    pass


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_schema(payload: dict) -> list[str]:
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in err.path)}: {err.message}" for err in validator.iter_errors(payload)]


def check_duplicate_grain(records: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[tuple] = set()
    for idx, row in enumerate(records):
        key = (row.get("player_id"), row.get("season"), row.get("season_type"))
        if None in key:
            errors.append(f"record[{idx}]: incomplete grain key {key}")
            continue
        if key in seen:
            errors.append(f"record[{idx}]: duplicate grain {key}")
        seen.add(key)
    return errors


def check_season_type_explicit(records: list[dict]) -> list[str]:
    errors: list[str] = []
    valid = {"REG", "POST", "REG+POST"}
    for idx, row in enumerate(records):
        season_type = row.get("season_type")
        if season_type not in valid:
            errors.append(f"record[{idx}]: invalid or missing season_type {season_type!r}")
    return errors


def check_multi_team_rule(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(records):
        teams = row.get("teams") or []
        if len(teams) > 1 and not row.get("primary_team_rule"):
            errors.append(f"record[{idx}]: multi-team row missing explicit primary_team_rule")
    return errors


def check_no_availability_assertion(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(records):
        present = ACTIVE_STATUS_FORBIDDEN_KEYS & set(row.keys())
        if present:
            errors.append(f"record[{idx}]: forbidden availability/status field(s) present: {sorted(present)}")
    return errors


def check_source_refs(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(records):
        refs = row.get("source_refs") or []
        if not refs:
            errors.append(f"record[{idx}]: missing source_refs")
            continue
        for ref in refs:
            name = str(ref.get("source_name", ""))
            if any(marker in name for marker in FIXTURE_MARKERS):
                errors.append(f"record[{idx}]: fixture/scaffold source presented as source-backed: {name}")
            if not ref.get("observed_at"):
                errors.append(f"record[{idx}]: source_ref missing observed_at")
    return errors


def check_age_career_not_fabricated(records: list[dict]) -> list[str]:
    """If birth_date is null, season_age/career fields tied to it must also be null, not guessed."""
    errors: list[str] = []
    for idx, row in enumerate(records):
        if row.get("birth_date") is None and row.get("season_age") is not None:
            errors.append(f"record[{idx}]: season_age populated despite null birth_date (possible fabrication)")
        if row.get("rookie_year") is None and row.get("career_year") is not None:
            errors.append(f"record[{idx}]: career_year populated despite null rookie_year (possible fabrication)")
    return errors


def check_zero_vs_null_distinct(records: list[dict]) -> list[str]:
    """Spot-check that unavailable usage fields are null, not coerced to 0."""
    errors: list[str] = []
    always_unavailable = ("snap_share", "routes_run", "route_participation", "red_zone_targets", "red_zone_carries")
    for idx, row in enumerate(records):
        usage = row.get("usage_summary") or {}
        for field in always_unavailable:
            if field in usage and usage[field] == 0:
                errors.append(
                    f"record[{idx}]: usage_summary.{field} is 0 but this field is not source-backed; "
                    "must be null/unavailable, not zero"
                )
    return errors


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_schema(payload))

    if payload.get("status") != "candidate_evidence_artifact_not_promoted":
        errors.append("artifact status must explicitly be 'candidate_evidence_artifact_not_promoted'")

    records = payload.get("records") or []
    if not records:
        errors.append("no records present")

    errors.extend(check_duplicate_grain(records))
    errors.extend(check_season_type_explicit(records))
    errors.extend(check_multi_team_rule(records))
    errors.extend(check_no_availability_assertion(records))
    errors.extend(check_source_refs(records))
    errors.extend(check_age_career_not_fabricated(records))
    errors.extend(check_zero_vs_null_distinct(records))
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/validate_player_season_coverage_v0.py <path-to-artifact.json>", file=sys.stderr)
        return 2

    artifact_path = Path(argv[1])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    errors = validate_payload(payload)

    if errors:
        print(f"FAILED: {len(errors)} validation error(s) in {artifact_path}", file=sys.stderr)
        for err in errors[:200]:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: {artifact_path} passed all validation checks ({len(payload.get('records', []))} records).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
